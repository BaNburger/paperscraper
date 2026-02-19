"""Service layer for technology transfer conversations."""

import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.exceptions import NotFoundError, ValidationError
from paper_scraper.core.sql_utils import escape_like
from paper_scraper.modules.auth.models import User
from paper_scraper.modules.papers.models import Author, Paper
from paper_scraper.modules.transfer.models import (
    ConversationMessage,
    ConversationResource,
    MessageTemplate,
    StageChange,
    TransferConversation,
    TransferStage,
)
from paper_scraper.modules.transfer.schemas import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
    NextStep,
    NextStepsResponse,
    ResourceCreate,
    ResourceResponse,
    StageChangeResponse,
    TemplateCreate,
    TemplateResponse,
    TemplateUpdate,
)

logger = logging.getLogger(__name__)

# Load Jinja2 environment for prompt templates
_PROMPTS_DIR = Path(__file__).parent.parent / "scoring" / "prompts"
_jinja_env = Environment(
    loader=FileSystemLoader(_PROMPTS_DIR),
    autoescape=False,
)


class TransferService:
    """Service for technology transfer conversation management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Conversations
    # =========================================================================

    async def list_conversations(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        stage: TransferStage | None = None,
        search: str | None = None,
    ) -> ConversationListResponse:
        """List transfer conversations with filtering and pagination."""
        base_query = select(TransferConversation).where(
            TransferConversation.organization_id == organization_id
        )

        if stage:
            base_query = base_query.where(TransferConversation.stage == stage)

        if search:
            # Escape SQL LIKE special characters to prevent unexpected matching
            escaped_search = escape_like(search)
            base_query = base_query.where(
                TransferConversation.title.ilike(f"%{escaped_search}%", escape="\\")
            )

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Build query with message/resource counts via subqueries to avoid N+1
        msg_count_sq = (
            select(func.count())
            .where(ConversationMessage.conversation_id == TransferConversation.id)
            .correlate(TransferConversation)
            .scalar_subquery()
            .label("msg_count")
        )
        res_count_sq = (
            select(func.count())
            .where(ConversationResource.conversation_id == TransferConversation.id)
            .correlate(TransferConversation)
            .scalar_subquery()
            .label("res_count")
        )

        query = select(TransferConversation, msg_count_sq, res_count_sq).where(
            TransferConversation.organization_id == organization_id
        )

        if stage:
            query = query.where(TransferConversation.stage == stage)
        if search:
            # Use the same escaped search variable to prevent SQL LIKE injection
            query = query.where(
                TransferConversation.title.ilike(f"%{escaped_search}%", escape="\\")
            )

        query = query.order_by(TransferConversation.updated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        rows = result.all()

        items = []
        for conv, msg_count, res_count in rows:
            items.append(
                ConversationResponse(
                    id=conv.id,
                    organization_id=conv.organization_id,
                    paper_id=conv.paper_id,
                    researcher_id=conv.researcher_id,
                    type=conv.type,
                    stage=conv.stage,
                    title=conv.title,
                    created_by=conv.created_by,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                    message_count=msg_count or 0,
                    resource_count=res_count or 0,
                )
            )

        return ConversationListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size if total > 0 else 0,
        )

    async def get_conversation(
        self,
        conversation_id: UUID,
        organization_id: UUID,
    ) -> TransferConversation | None:
        """Get a conversation by ID with tenant isolation."""
        result = await self.db.execute(
            select(TransferConversation).where(
                TransferConversation.id == conversation_id,
                TransferConversation.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_conversation_detail(
        self,
        conversation_id: UUID,
        organization_id: UUID,
    ) -> ConversationDetailResponse | None:
        """Get full conversation detail with messages, resources, and stage history."""
        conv = await self.get_conversation(conversation_id, organization_id)
        if not conv:
            return None

        # Load messages with sender info
        messages_result = await self.db.execute(
            select(ConversationMessage)
            .options(selectinload(ConversationMessage.sender))
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.asc())
        )
        messages_data = messages_result.scalars().all()

        messages = [
            MessageResponse(
                id=m.id,
                conversation_id=m.conversation_id,
                sender_id=m.sender_id,
                content=m.content,
                mentions=m.mentions or [],
                created_at=m.created_at,
                sender_name=m.sender.full_name if m.sender else None,
            )
            for m in messages_data
        ]

        # Load resources
        resources_result = await self.db.execute(
            select(ConversationResource)
            .where(ConversationResource.conversation_id == conversation_id)
            .order_by(ConversationResource.created_at.desc())
        )
        resources = [ResourceResponse.model_validate(r) for r in resources_result.scalars().all()]

        # Load stage history with user info
        history_result = await self.db.execute(
            select(StageChange)
            .options(selectinload(StageChange.changed_by_user))
            .where(StageChange.conversation_id == conversation_id)
            .order_by(StageChange.changed_at.desc())
        )
        stage_history = [
            StageChangeResponse(
                id=sc.id,
                conversation_id=sc.conversation_id,
                from_stage=sc.from_stage,
                to_stage=sc.to_stage,
                changed_by=sc.changed_by,
                notes=sc.notes,
                changed_at=sc.changed_at,
                changed_by_name=(sc.changed_by_user.full_name if sc.changed_by_user else None),
            )
            for sc in history_result.scalars().all()
        ]

        # Resolve related names
        creator_name = None
        creator_result = await self.db.execute(
            select(User.full_name).where(User.id == conv.created_by)
        )
        creator_name = creator_result.scalar()

        paper_title = None
        if conv.paper_id:
            paper_result = await self.db.execute(
                select(Paper.title).where(Paper.id == conv.paper_id)
            )
            paper_title = paper_result.scalar()

        researcher_name = None
        if conv.researcher_id:
            researcher_result = await self.db.execute(
                select(Author.name).where(Author.id == conv.researcher_id)
            )
            researcher_name = researcher_result.scalar()

        return ConversationDetailResponse(
            id=conv.id,
            organization_id=conv.organization_id,
            paper_id=conv.paper_id,
            researcher_id=conv.researcher_id,
            type=conv.type,
            stage=conv.stage,
            title=conv.title,
            created_by=conv.created_by,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=len(messages),
            resource_count=len(resources),
            messages=messages,
            resources=resources,
            stage_history=stage_history,
            creator_name=creator_name,
            paper_title=paper_title,
            researcher_name=researcher_name,
        )

    async def create_conversation(
        self,
        organization_id: UUID,
        user_id: UUID,
        data: ConversationCreate,
    ) -> TransferConversation:
        """Create a new transfer conversation."""
        conversation = TransferConversation(
            organization_id=organization_id,
            paper_id=data.paper_id,
            researcher_id=data.researcher_id,
            type=data.type,
            stage=TransferStage.INITIAL_CONTACT,
            title=data.title,
            created_by=user_id,
        )
        self.db.add(conversation)
        await self.db.flush()
        await self.db.refresh(conversation)
        return conversation

    async def update_conversation_stage(
        self,
        conversation_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        data: ConversationUpdate,
    ) -> TransferConversation:
        """Update the stage of a conversation and record history."""
        conv = await self.get_conversation(conversation_id, organization_id)
        if not conv:
            raise NotFoundError("TransferConversation", conversation_id)

        old_stage = conv.stage
        if old_stage == data.stage:
            raise ValidationError(f"Conversation is already in stage '{data.stage.value}'")

        # Record stage change
        stage_change = StageChange(
            conversation_id=conv.id,
            from_stage=old_stage,
            to_stage=data.stage,
            changed_by=user_id,
            notes=data.notes,
        )
        self.db.add(stage_change)

        # Update the conversation
        conv.stage = data.stage
        await self.db.flush()
        await self.db.refresh(conv)
        return conv

    # =========================================================================
    # Messages
    # =========================================================================

    async def add_message(
        self,
        conversation_id: UUID,
        organization_id: UUID,
        sender_id: UUID,
        data: MessageCreate,
    ) -> ConversationMessage:
        """Add a message to a conversation."""
        conv = await self.get_conversation(conversation_id, organization_id)
        if not conv:
            raise NotFoundError("TransferConversation", conversation_id)

        message = ConversationMessage(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=data.content,
            mentions=[str(uid) for uid in data.mentions],
        )
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def add_message_from_template(
        self,
        conversation_id: UUID,
        organization_id: UUID,
        sender_id: UUID,
        template_id: UUID,
        mentions: list[UUID] | None = None,
    ) -> ConversationMessage:
        """Add a message to a conversation using a template."""
        conv = await self.get_conversation(conversation_id, organization_id)
        if not conv:
            raise NotFoundError("TransferConversation", conversation_id)

        template = await self.get_template(template_id, organization_id)
        if not template:
            raise NotFoundError("MessageTemplate", template_id)

        message = ConversationMessage(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=template.content,
            mentions=[str(uid) for uid in (mentions or [])],
        )
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message

    # =========================================================================
    # Resources
    # =========================================================================

    async def add_resource(
        self,
        conversation_id: UUID,
        organization_id: UUID,
        data: ResourceCreate,
    ) -> ConversationResource:
        """Attach a resource to a conversation."""
        conv = await self.get_conversation(conversation_id, organization_id)
        if not conv:
            raise NotFoundError("TransferConversation", conversation_id)

        resource = ConversationResource(
            conversation_id=conversation_id,
            name=data.name,
            url=data.url,
            file_path=data.file_path,
            resource_type=data.resource_type,
        )
        self.db.add(resource)
        await self.db.flush()
        await self.db.refresh(resource)
        return resource

    async def get_resource(
        self,
        conversation_id: UUID,
        resource_id: UUID,
        organization_id: UUID,
    ) -> ConversationResource:
        """Get a resource by ID with tenant isolation.

        Args:
            conversation_id: Conversation UUID.
            resource_id: Resource UUID.
            organization_id: Organization UUID for tenant isolation.

        Returns:
            ConversationResource.

        Raises:
            NotFoundError: If conversation or resource not found.
        """
        conv = await self.get_conversation(conversation_id, organization_id)
        if not conv:
            raise NotFoundError("TransferConversation", conversation_id)

        result = await self.db.execute(
            select(ConversationResource).where(
                ConversationResource.id == resource_id,
                ConversationResource.conversation_id == conversation_id,
            )
        )
        resource = result.scalar_one_or_none()
        if not resource:
            raise NotFoundError("ConversationResource", resource_id)
        return resource

    # =========================================================================
    # Templates
    # =========================================================================

    async def list_templates(
        self,
        organization_id: UUID,
        stage: TransferStage | None = None,
    ) -> list[TemplateResponse]:
        """List message templates for an organization."""
        query = select(MessageTemplate).where(MessageTemplate.organization_id == organization_id)
        if stage:
            query = query.where(MessageTemplate.stage == stage)

        query = query.order_by(MessageTemplate.name)
        result = await self.db.execute(query)
        return [TemplateResponse.model_validate(t) for t in result.scalars().all()]

    async def get_template(
        self,
        template_id: UUID,
        organization_id: UUID,
    ) -> MessageTemplate | None:
        """Get a template by ID with tenant isolation."""
        result = await self.db.execute(
            select(MessageTemplate).where(
                MessageTemplate.id == template_id,
                MessageTemplate.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_template(
        self,
        organization_id: UUID,
        data: TemplateCreate,
    ) -> MessageTemplate:
        """Create a new message template."""
        template = MessageTemplate(
            organization_id=organization_id,
            name=data.name,
            subject=data.subject,
            content=data.content,
            stage=data.stage,
        )
        self.db.add(template)
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def update_template(
        self,
        template_id: UUID,
        organization_id: UUID,
        data: TemplateUpdate,
    ) -> MessageTemplate:
        """Update an existing template."""
        template = await self.get_template(template_id, organization_id)
        if not template:
            raise NotFoundError("MessageTemplate", template_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(template, key, value)

        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def delete_template(
        self,
        template_id: UUID,
        organization_id: UUID,
    ) -> None:
        """Delete a message template."""
        template = await self.get_template(template_id, organization_id)
        if not template:
            raise NotFoundError("MessageTemplate", template_id)

        await self.db.delete(template)
        await self.db.flush()

    # =========================================================================
    # AI Next Steps
    # =========================================================================

    async def get_next_steps(
        self,
        conversation_id: UUID,
        organization_id: UUID,
    ) -> NextStepsResponse:
        """Get AI-suggested next steps for a conversation.

        Enhanced version that includes:
        - Full conversation history (last 15 messages)
        - Stage-specific suggestion templates
        - Message template recommendations
        - Researcher profile and paper context
        """
        detail = await self.get_conversation_detail(conversation_id, organization_id)
        if not detail:
            raise NotFoundError("TransferConversation", conversation_id)

        try:
            from paper_scraper.modules.scoring.llm_client import (
                get_llm_client,
                sanitize_text_for_prompt,
            )

            llm = get_llm_client()

            # Get available message templates for current stage
            templates = await self.list_templates(organization_id, stage=detail.stage)

            # Get additional context: paper abstract and researcher details
            paper_context = await self._get_paper_context(detail.paper_id)
            researcher_context = await self._get_researcher_context(detail.researcher_id)

            # Calculate days in current stage
            days_in_stage = 0
            if detail.stage_history:
                latest_change = detail.stage_history[0]  # Most recent
                days_in_stage = (datetime.now(UTC) - latest_change.changed_at).days
            else:
                days_in_stage = (datetime.now(UTC) - detail.created_at).days

            # Build message data for prompt (sanitize all user-controllable fields)
            messages_data = [
                {
                    "timestamp": m.created_at.strftime("%Y-%m-%d %H:%M"),
                    "sender": sanitize_text_for_prompt(m.sender_name or "Unknown", max_length=100),
                    "content": sanitize_text_for_prompt(m.content, max_length=500),
                }
                for m in detail.messages[-15:]  # Last 15 messages
            ]

            # Build stage history for prompt
            stage_history_data = [
                {
                    "from_stage": sc.from_stage.value,
                    "to_stage": sc.to_stage.value,
                    "notes": sc.notes,
                }
                for sc in detail.stage_history[:5]
            ]

            # Build template data for prompt
            template_data = [{"name": t.name, "subject": t.subject} for t in templates]

            # Render enhanced prompt
            template = _jinja_env.get_template("transfer_next_steps.jinja2")
            prompt = template.render(
                title=sanitize_text_for_prompt(detail.title, max_length=200),
                type=detail.type.value,
                stage=detail.stage.value,
                days_in_stage=days_in_stage,
                paper_title=sanitize_text_for_prompt(paper_context.get("title"), max_length=200)
                if paper_context
                else None,
                paper_abstract=sanitize_text_for_prompt(
                    paper_context.get("abstract"), max_length=500
                )
                if paper_context
                else None,
                researcher_name=sanitize_text_for_prompt(
                    researcher_context.get("name"), max_length=100
                )
                if researcher_context
                else None,
                researcher_affiliations=researcher_context.get("affiliations")
                if researcher_context
                else None,
                researcher_h_index=researcher_context.get("h_index")
                if researcher_context
                else None,
                messages=messages_data,
                stage_history=stage_history_data,
                available_templates=template_data,
            )

            system_prompt = (
                "You are an expert technology transfer advisor helping TTO staff "
                "manage conversations with researchers and industry partners. "
                "Provide practical, actionable next steps based on the full conversation context. "
                "Consider the stage-specific priorities and recommend specific message templates when appropriate."
            )

            result = await llm.complete_json(
                prompt=prompt,
                system=system_prompt,
                temperature=0.3,
                max_tokens=1500,
            )

            steps = [
                NextStep(
                    action=s.get("action", ""),
                    priority=s.get("priority", "medium"),
                    rationale=s.get("rationale", ""),
                    suggested_template=s.get("suggested_template"),
                )
                for s in result.get("steps", [])
            ]

            return NextStepsResponse(
                conversation_id=conversation_id,
                steps=steps,
                summary=result.get("summary", "Unable to generate summary."),
                stage_recommendation=result.get("stage_recommendation"),
            )

        except (ImportError, ConnectionError, TimeoutError, ValueError, KeyError) as e:
            logger.warning(f"AI next-steps generation failed: {e}")
            return self._get_fallback_next_steps(detail)
        except Exception as e:
            logger.exception(f"Unexpected error in AI next-steps: {e}")
            return self._get_fallback_next_steps(detail)

    async def _get_paper_context(self, paper_id: UUID | None) -> dict | None:
        """Get paper context for next-steps prompt."""
        if not paper_id:
            return None

        result = await self.db.execute(
            select(Paper.title, Paper.abstract).where(Paper.id == paper_id)
        )
        row = result.first()
        if row:
            return {"title": row.title, "abstract": row.abstract}
        return None

    async def _get_researcher_context(self, researcher_id: UUID | None) -> dict | None:
        """Get researcher context for next-steps prompt."""
        if not researcher_id:
            return None

        result = await self.db.execute(
            select(Author.name, Author.affiliations, Author.h_index).where(
                Author.id == researcher_id
            )
        )
        row = result.first()
        if row:
            return {
                "name": row.name,
                "affiliations": row.affiliations,
                "h_index": row.h_index,
            }
        return None

    # =========================================================================
    # Private Methods
    # =========================================================================

    async def count_messages(self, conversation_id: UUID) -> int:
        """Count messages in a conversation."""
        result = await self.db.execute(
            select(func.count()).where(ConversationMessage.conversation_id == conversation_id)
        )
        return result.scalar() or 0

    async def count_resources(self, conversation_id: UUID) -> int:
        """Count resources in a conversation."""
        result = await self.db.execute(
            select(func.count()).where(ConversationResource.conversation_id == conversation_id)
        )
        return result.scalar() or 0

    def _get_fallback_next_steps(self, detail: ConversationDetailResponse) -> NextStepsResponse:
        """Generate fallback next steps when AI is unavailable."""
        stage = detail.stage
        steps: list[NextStep] = []

        stage_steps = {
            TransferStage.INITIAL_CONTACT: [
                NextStep(
                    action="Schedule introductory meeting with researcher",
                    priority="high",
                    rationale="Personal contact accelerates transfer discussions",
                ),
                NextStep(
                    action="Review the paper and prepare talking points",
                    priority="high",
                    rationale="Understanding the research is essential for productive conversations",
                ),
                NextStep(
                    action="Identify potential industry partners",
                    priority="medium",
                    rationale="Early partner identification speeds up the process",
                ),
            ],
            TransferStage.DISCOVERY: [
                NextStep(
                    action="Conduct prior art search",
                    priority="high",
                    rationale="Understanding the IP landscape is critical before proceeding",
                ),
                NextStep(
                    action="Assess market potential and target industries",
                    priority="high",
                    rationale="Market validation informs the transfer strategy",
                ),
                NextStep(
                    action="Document researcher's commercialization interest",
                    priority="medium",
                    rationale="Researcher alignment is key to successful transfer",
                ),
            ],
            TransferStage.EVALUATION: [
                NextStep(
                    action="Complete IP evaluation and freedom-to-operate analysis",
                    priority="high",
                    rationale="IP clarity is prerequisite for negotiation",
                ),
                NextStep(
                    action="Prepare term sheet or licensing framework",
                    priority="medium",
                    rationale="Having a framework ready accelerates negotiations",
                ),
            ],
            TransferStage.NEGOTIATION: [
                NextStep(
                    action="Review and finalize deal terms",
                    priority="high",
                    rationale="Clear terms prevent disputes and delays",
                ),
                NextStep(
                    action="Coordinate legal review of agreements",
                    priority="high",
                    rationale="Legal sign-off is required before closing",
                ),
            ],
            TransferStage.CLOSED_WON: [
                NextStep(
                    action="Set up monitoring for milestone compliance",
                    priority="medium",
                    rationale="Ongoing oversight ensures deal success",
                ),
            ],
            TransferStage.CLOSED_LOST: [
                NextStep(
                    action="Document lessons learned",
                    priority="medium",
                    rationale="Learning from this case improves future outcomes",
                ),
            ],
        }

        steps = stage_steps.get(stage, [])

        return NextStepsResponse(
            conversation_id=detail.id,
            steps=steps,
            summary=f"Conversation is in {stage.value} stage. AI suggestions are currently unavailable; showing default recommendations.",
        )
