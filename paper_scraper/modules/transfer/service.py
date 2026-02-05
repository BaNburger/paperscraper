"""Service layer for technology transfer conversations."""

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.exceptions import NotFoundError, ValidationError
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
            base_query = base_query.where(
                TransferConversation.title.ilike(f"%{search}%")
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

        query = (
            select(TransferConversation, msg_count_sq, res_count_sq)
            .where(TransferConversation.organization_id == organization_id)
        )

        if stage:
            query = query.where(TransferConversation.stage == stage)
        if search:
            query = query.where(
                TransferConversation.title.ilike(f"%{search}%")
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
        resources = [
            ResourceResponse.model_validate(r)
            for r in resources_result.scalars().all()
        ]

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
                changed_by_name=(
                    sc.changed_by_user.full_name if sc.changed_by_user else None
                ),
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
        await self.db.commit()
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
            raise ValidationError(
                f"Conversation is already in stage '{data.stage.value}'"
            )

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
        await self.db.commit()
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
        await self.db.commit()
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
        await self.db.commit()
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
        await self.db.commit()
        await self.db.refresh(resource)
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
        query = select(MessageTemplate).where(
            MessageTemplate.organization_id == organization_id
        )
        if stage:
            query = query.where(MessageTemplate.stage == stage)

        query = query.order_by(MessageTemplate.name)
        result = await self.db.execute(query)
        return [
            TemplateResponse.model_validate(t) for t in result.scalars().all()
        ]

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
        await self.db.commit()
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

        await self.db.commit()
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
        await self.db.commit()

    # =========================================================================
    # AI Next Steps
    # =========================================================================

    async def get_next_steps(
        self,
        conversation_id: UUID,
        organization_id: UUID,
    ) -> NextStepsResponse:
        """Get AI-suggested next steps for a conversation."""
        detail = await self.get_conversation_detail(conversation_id, organization_id)
        if not detail:
            raise NotFoundError("TransferConversation", conversation_id)

        try:
            from paper_scraper.modules.scoring.llm_client import (
                get_llm_client,
                sanitize_text_for_prompt,
            )

            llm = get_llm_client()

            # Build context for the LLM
            messages_text = "\n".join(
                f"[{m.sender_name or 'Unknown'}]: {sanitize_text_for_prompt(m.content, max_length=500)}"
                for m in detail.messages[-10:]  # Last 10 messages
            )

            stage_history_text = "\n".join(
                f"- {sc.from_stage.value} -> {sc.to_stage.value}"
                + (f" (Note: {sc.notes})" if sc.notes else "")
                for sc in detail.stage_history[:5]
            )

            prompt = f"""Analyze this technology transfer conversation and suggest next steps.

Conversation: {sanitize_text_for_prompt(detail.title, max_length=200)}
Type: {detail.type.value}
Current Stage: {detail.stage.value}
Paper: {sanitize_text_for_prompt(detail.paper_title, max_length=200) if detail.paper_title else 'N/A'}
Researcher: {sanitize_text_for_prompt(detail.researcher_name, max_length=200) if detail.researcher_name else 'N/A'}

Recent Messages:
{messages_text or 'No messages yet.'}

Stage History:
{stage_history_text or 'No stage transitions yet.'}

Respond with a JSON object containing:
- "summary": brief status summary (1-2 sentences)
- "steps": array of 3-5 next steps, each with:
  - "action": what to do
  - "priority": "high", "medium", or "low"
  - "rationale": why this step matters
"""

            system_prompt = (
                "You are an expert technology transfer advisor helping TTO staff "
                "manage conversations with researchers and industry partners. "
                "Provide practical, actionable next steps based on the conversation context."
            )

            result = await llm.complete_json(
                prompt=prompt,
                system=system_prompt,
                temperature=0.3,
                max_tokens=1000,
            )

            steps = [
                NextStep(
                    action=s.get("action", ""),
                    priority=s.get("priority", "medium"),
                    rationale=s.get("rationale", ""),
                )
                for s in result.get("steps", [])
            ]

            return NextStepsResponse(
                conversation_id=conversation_id,
                steps=steps,
                summary=result.get("summary", "Unable to generate summary."),
            )

        except (ImportError, ConnectionError, TimeoutError, ValueError, KeyError) as e:
            logger.warning(f"AI next-steps generation failed: {e}")
            # Return fallback based on current stage
            return self._get_fallback_next_steps(detail)
        except Exception as e:
            logger.exception(f"Unexpected error in AI next-steps: {e}")
            return self._get_fallback_next_steps(detail)

    # =========================================================================
    # Private Methods
    # =========================================================================

    async def count_messages(self, conversation_id: UUID) -> int:
        """Count messages in a conversation."""
        result = await self.db.execute(
            select(func.count()).where(
                ConversationMessage.conversation_id == conversation_id
            )
        )
        return result.scalar() or 0

    async def count_resources(self, conversation_id: UUID) -> int:
        """Count resources in a conversation."""
        result = await self.db.execute(
            select(func.count()).where(
                ConversationResource.conversation_id == conversation_id
            )
        )
        return result.scalar() or 0

    def _get_fallback_next_steps(
        self, detail: ConversationDetailResponse
    ) -> NextStepsResponse:
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
