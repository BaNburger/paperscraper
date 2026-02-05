"""Tests for technology transfer module."""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.security import create_access_token, get_password_hash
from paper_scraper.modules.auth.models import Organization, User, UserRole
from paper_scraper.modules.papers.models import Author, Paper
from paper_scraper.modules.transfer.models import (
    ConversationMessage,
    ConversationResource,
    MessageTemplate,
    StageChange,
    TransferConversation,
    TransferStage,
    TransferType,
)
from paper_scraper.modules.transfer.schemas import (
    ConversationCreate,
    ConversationUpdate,
    MessageCreate,
    ResourceCreate,
    TemplateCreate,
    TemplateUpdate,
)
from paper_scraper.modules.transfer.service import TransferService


# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def transfer_service(db_session: AsyncSession) -> TransferService:
    """Create a transfer service instance for testing."""
    return TransferService(db_session)


@pytest_asyncio.fixture
async def second_organization(db_session: AsyncSession) -> Organization:
    """Create a second organization for tenant isolation tests."""
    organization = Organization(
        name="Second Organization",
        type="corporate",
    )
    db_session.add(organization)
    await db_session.flush()
    await db_session.refresh(organization)
    return organization


@pytest_asyncio.fixture
async def test_author(
    db_session: AsyncSession,
    test_organization: Organization,
) -> Author:
    """Create a test author."""
    author = Author(
        name="Dr. Jane Smith",
        orcid="0000-0001-2345-6789",
        organization_id=test_organization.id,
    )
    db_session.add(author)
    await db_session.flush()
    await db_session.refresh(author)
    return author


@pytest_asyncio.fixture
async def test_paper(
    db_session: AsyncSession,
    test_organization: Organization,
) -> Paper:
    """Create a test paper."""
    paper = Paper(
        doi="10.1234/test.transfer.001",
        title="Novel Nanomaterial for Energy Storage",
        abstract="A breakthrough in energy storage technology.",
        source="openalex",
        organization_id=test_organization.id,
    )
    db_session.add(paper)
    await db_session.flush()
    await db_session.refresh(paper)
    return paper


@pytest_asyncio.fixture
async def test_conversation(
    db_session: AsyncSession,
    test_organization: Organization,
    test_user: User,
    test_paper: Paper,
    test_author: Author,
) -> TransferConversation:
    """Create a test transfer conversation."""
    conv = TransferConversation(
        organization_id=test_organization.id,
        paper_id=test_paper.id,
        researcher_id=test_author.id,
        type=TransferType.PATENT,
        stage=TransferStage.INITIAL_CONTACT,
        title="Patent Discussion - Nanomaterial",
        created_by=test_user.id,
    )
    db_session.add(conv)
    await db_session.flush()
    await db_session.refresh(conv)
    return conv


@pytest_asyncio.fixture
async def test_message(
    db_session: AsyncSession,
    test_conversation: TransferConversation,
    test_user: User,
) -> ConversationMessage:
    """Create a test message."""
    message = ConversationMessage(
        conversation_id=test_conversation.id,
        sender_id=test_user.id,
        content="Initial outreach email sent to researcher.",
        mentions=[],
    )
    db_session.add(message)
    await db_session.flush()
    await db_session.refresh(message)
    return message


@pytest_asyncio.fixture
async def test_resource(
    db_session: AsyncSession,
    test_conversation: TransferConversation,
) -> ConversationResource:
    """Create a test resource."""
    resource = ConversationResource(
        conversation_id=test_conversation.id,
        name="Patent Draft",
        url="https://example.com/patent-draft.pdf",
        resource_type="link",
    )
    db_session.add(resource)
    await db_session.flush()
    await db_session.refresh(resource)
    return resource


@pytest_asyncio.fixture
async def test_template(
    db_session: AsyncSession,
    test_organization: Organization,
) -> MessageTemplate:
    """Create a test message template."""
    template = MessageTemplate(
        organization_id=test_organization.id,
        name="Initial Contact",
        subject="Technology Transfer Opportunity",
        content="Dear Dr. {name}, we are interested in discussing...",
        stage=TransferStage.INITIAL_CONTACT,
    )
    db_session.add(template)
    await db_session.flush()
    await db_session.refresh(template)
    return template


# =============================================================================
# Service Tests - Conversations
# =============================================================================


class TestTransferServiceConversations:
    """Tests for TransferService conversation operations."""

    async def test_create_conversation(
        self,
        transfer_service: TransferService,
        test_organization: Organization,
        test_user: User,
        test_paper: Paper,
        test_author: Author,
    ):
        """Test creating a new conversation."""
        data = ConversationCreate(
            title="Licensing Discussion",
            type=TransferType.LICENSING,
            paper_id=test_paper.id,
            researcher_id=test_author.id,
        )
        conv = await transfer_service.create_conversation(
            organization_id=test_organization.id,
            user_id=test_user.id,
            data=data,
        )

        assert conv.id is not None
        assert conv.title == "Licensing Discussion"
        assert conv.type == TransferType.LICENSING
        assert conv.stage == TransferStage.INITIAL_CONTACT
        assert conv.paper_id == test_paper.id
        assert conv.researcher_id == test_author.id
        assert conv.created_by == test_user.id

    async def test_get_conversation(
        self,
        transfer_service: TransferService,
        test_conversation: TransferConversation,
        test_organization: Organization,
    ):
        """Test retrieving a conversation."""
        conv = await transfer_service.get_conversation(
            conversation_id=test_conversation.id,
            organization_id=test_organization.id,
        )
        assert conv is not None
        assert conv.id == test_conversation.id
        assert conv.title == "Patent Discussion - Nanomaterial"

    async def test_get_conversation_not_found(
        self,
        transfer_service: TransferService,
        test_organization: Organization,
    ):
        """Test that getting a non-existent conversation returns None."""
        conv = await transfer_service.get_conversation(
            conversation_id=uuid4(),
            organization_id=test_organization.id,
        )
        assert conv is None

    async def test_get_conversation_tenant_isolation(
        self,
        transfer_service: TransferService,
        test_conversation: TransferConversation,
        second_organization: Organization,
    ):
        """Test that conversation retrieval respects tenant boundaries."""
        conv = await transfer_service.get_conversation(
            conversation_id=test_conversation.id,
            organization_id=second_organization.id,
        )
        assert conv is None

    async def test_list_conversations(
        self,
        transfer_service: TransferService,
        test_conversation: TransferConversation,
        test_organization: Organization,
    ):
        """Test listing conversations with pagination."""
        result = await transfer_service.list_conversations(
            organization_id=test_organization.id,
        )
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].title == "Patent Discussion - Nanomaterial"

    async def test_list_conversations_with_stage_filter(
        self,
        transfer_service: TransferService,
        test_conversation: TransferConversation,
        test_organization: Organization,
    ):
        """Test filtering conversations by stage."""
        result = await transfer_service.list_conversations(
            organization_id=test_organization.id,
            stage=TransferStage.INITIAL_CONTACT,
        )
        assert result.total == 1

        result = await transfer_service.list_conversations(
            organization_id=test_organization.id,
            stage=TransferStage.NEGOTIATION,
        )
        assert result.total == 0

    async def test_list_conversations_with_search(
        self,
        transfer_service: TransferService,
        test_conversation: TransferConversation,
        test_organization: Organization,
    ):
        """Test searching conversations by title."""
        result = await transfer_service.list_conversations(
            organization_id=test_organization.id,
            search="Nanomaterial",
        )
        assert result.total == 1

        result = await transfer_service.list_conversations(
            organization_id=test_organization.id,
            search="Nonexistent",
        )
        assert result.total == 0

    async def test_update_conversation_stage(
        self,
        transfer_service: TransferService,
        test_conversation: TransferConversation,
        test_organization: Organization,
        test_user: User,
    ):
        """Test updating conversation stage with history."""
        data = ConversationUpdate(
            stage=TransferStage.DISCOVERY,
            notes="Moving to discovery after initial contact.",
        )
        conv = await transfer_service.update_conversation_stage(
            conversation_id=test_conversation.id,
            organization_id=test_organization.id,
            user_id=test_user.id,
            data=data,
        )

        assert conv.stage == TransferStage.DISCOVERY

    async def test_update_conversation_stage_same_stage_raises(
        self,
        transfer_service: TransferService,
        test_conversation: TransferConversation,
        test_organization: Organization,
        test_user: User,
    ):
        """Test that updating to the same stage raises an error."""
        from paper_scraper.core.exceptions import ValidationError

        data = ConversationUpdate(stage=TransferStage.INITIAL_CONTACT)
        with pytest.raises(ValidationError):
            await transfer_service.update_conversation_stage(
                conversation_id=test_conversation.id,
                organization_id=test_organization.id,
                user_id=test_user.id,
                data=data,
            )

    async def test_get_conversation_detail(
        self,
        transfer_service: TransferService,
        test_conversation: TransferConversation,
        test_organization: Organization,
        test_message: ConversationMessage,
        test_resource: ConversationResource,
    ):
        """Test getting full conversation detail."""
        detail = await transfer_service.get_conversation_detail(
            conversation_id=test_conversation.id,
            organization_id=test_organization.id,
        )

        assert detail is not None
        assert detail.id == test_conversation.id
        assert detail.title == "Patent Discussion - Nanomaterial"
        assert len(detail.messages) == 1
        assert len(detail.resources) == 1
        assert detail.paper_title == "Novel Nanomaterial for Energy Storage"
        assert detail.researcher_name == "Dr. Jane Smith"
        assert detail.creator_name == "Test User"


# =============================================================================
# Service Tests - Messages
# =============================================================================


class TestTransferServiceMessages:
    """Tests for TransferService message operations."""

    async def test_add_message(
        self,
        transfer_service: TransferService,
        test_conversation: TransferConversation,
        test_organization: Organization,
        test_user: User,
    ):
        """Test adding a message to a conversation."""
        data = MessageCreate(
            content="Follow-up meeting scheduled for next week.",
        )
        message = await transfer_service.add_message(
            conversation_id=test_conversation.id,
            organization_id=test_organization.id,
            sender_id=test_user.id,
            data=data,
        )

        assert message.id is not None
        assert message.content == "Follow-up meeting scheduled for next week."
        assert message.sender_id == test_user.id

    async def test_add_message_with_mentions(
        self,
        transfer_service: TransferService,
        test_conversation: TransferConversation,
        test_organization: Organization,
        test_user: User,
    ):
        """Test adding a message with mentions."""
        mention_id = uuid4()
        data = MessageCreate(
            content=f"@colleague Please review this.",
            mentions=[mention_id],
        )
        message = await transfer_service.add_message(
            conversation_id=test_conversation.id,
            organization_id=test_organization.id,
            sender_id=test_user.id,
            data=data,
        )

        assert len(message.mentions) == 1

    async def test_add_message_to_nonexistent_conversation(
        self,
        transfer_service: TransferService,
        test_organization: Organization,
        test_user: User,
    ):
        """Test that adding a message to a nonexistent conversation raises error."""
        from paper_scraper.core.exceptions import NotFoundError

        data = MessageCreate(content="Test")
        with pytest.raises(NotFoundError):
            await transfer_service.add_message(
                conversation_id=uuid4(),
                organization_id=test_organization.id,
                sender_id=test_user.id,
                data=data,
            )

    async def test_add_message_from_template(
        self,
        transfer_service: TransferService,
        test_conversation: TransferConversation,
        test_organization: Organization,
        test_user: User,
        test_template: MessageTemplate,
    ):
        """Test adding a message from a template."""
        message = await transfer_service.add_message_from_template(
            conversation_id=test_conversation.id,
            organization_id=test_organization.id,
            sender_id=test_user.id,
            template_id=test_template.id,
        )

        assert message.content == test_template.content
        assert message.sender_id == test_user.id


# =============================================================================
# Service Tests - Resources
# =============================================================================


class TestTransferServiceResources:
    """Tests for TransferService resource operations."""

    async def test_add_resource(
        self,
        transfer_service: TransferService,
        test_conversation: TransferConversation,
        test_organization: Organization,
    ):
        """Test attaching a resource to a conversation."""
        data = ResourceCreate(
            name="Research Paper PDF",
            url="https://example.com/paper.pdf",
            resource_type="link",
        )
        resource = await transfer_service.add_resource(
            conversation_id=test_conversation.id,
            organization_id=test_organization.id,
            data=data,
        )

        assert resource.id is not None
        assert resource.name == "Research Paper PDF"
        assert resource.resource_type == "link"

    async def test_add_resource_to_nonexistent_conversation(
        self,
        transfer_service: TransferService,
        test_organization: Organization,
    ):
        """Test that adding a resource to a nonexistent conversation raises error."""
        from paper_scraper.core.exceptions import NotFoundError

        data = ResourceCreate(name="Test", resource_type="link")
        with pytest.raises(NotFoundError):
            await transfer_service.add_resource(
                conversation_id=uuid4(),
                organization_id=test_organization.id,
                data=data,
            )


# =============================================================================
# Service Tests - Templates
# =============================================================================


class TestTransferServiceTemplates:
    """Tests for TransferService template operations."""

    async def test_create_template(
        self,
        transfer_service: TransferService,
        test_organization: Organization,
    ):
        """Test creating a message template."""
        data = TemplateCreate(
            name="Follow-up Email",
            subject="Re: Technology Transfer Discussion",
            content="Dear Dr. {name}, following up on our conversation...",
            stage=TransferStage.DISCOVERY,
        )
        template = await transfer_service.create_template(
            organization_id=test_organization.id,
            data=data,
        )

        assert template.id is not None
        assert template.name == "Follow-up Email"
        assert template.stage == TransferStage.DISCOVERY

    async def test_list_templates(
        self,
        transfer_service: TransferService,
        test_organization: Organization,
        test_template: MessageTemplate,
    ):
        """Test listing templates."""
        templates = await transfer_service.list_templates(
            organization_id=test_organization.id,
        )
        assert len(templates) == 1
        assert templates[0].name == "Initial Contact"

    async def test_list_templates_with_stage_filter(
        self,
        transfer_service: TransferService,
        test_organization: Organization,
        test_template: MessageTemplate,
    ):
        """Test filtering templates by stage."""
        templates = await transfer_service.list_templates(
            organization_id=test_organization.id,
            stage=TransferStage.INITIAL_CONTACT,
        )
        assert len(templates) == 1

        templates = await transfer_service.list_templates(
            organization_id=test_organization.id,
            stage=TransferStage.NEGOTIATION,
        )
        assert len(templates) == 0

    async def test_update_template(
        self,
        transfer_service: TransferService,
        test_template: MessageTemplate,
        test_organization: Organization,
    ):
        """Test updating a template."""
        data = TemplateUpdate(name="Updated Initial Contact")
        template = await transfer_service.update_template(
            template_id=test_template.id,
            organization_id=test_organization.id,
            data=data,
        )
        assert template.name == "Updated Initial Contact"

    async def test_delete_template(
        self,
        transfer_service: TransferService,
        test_template: MessageTemplate,
        test_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test deleting a template."""
        await transfer_service.delete_template(
            template_id=test_template.id,
            organization_id=test_organization.id,
        )

        result = await db_session.execute(
            select(MessageTemplate).where(MessageTemplate.id == test_template.id)
        )
        assert result.scalar_one_or_none() is None

    async def test_template_tenant_isolation(
        self,
        transfer_service: TransferService,
        test_template: MessageTemplate,
        second_organization: Organization,
    ):
        """Test that template operations respect tenant boundaries."""
        from paper_scraper.core.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await transfer_service.update_template(
                template_id=test_template.id,
                organization_id=second_organization.id,
                data=TemplateUpdate(name="Hacked!"),
            )


# =============================================================================
# Service Tests - AI Next Steps
# =============================================================================


class TestTransferServiceNextSteps:
    """Tests for TransferService AI next-steps (fallback mode)."""

    async def test_get_next_steps_fallback(
        self,
        transfer_service: TransferService,
        test_conversation: TransferConversation,
        test_organization: Organization,
    ):
        """Test that fallback next steps are returned when AI is unavailable."""
        # The AI call will fail in test environment, triggering fallback
        result = await transfer_service.get_next_steps(
            conversation_id=test_conversation.id,
            organization_id=test_organization.id,
        )

        assert result.conversation_id == test_conversation.id
        assert len(result.steps) > 0
        assert result.summary  # Should have a summary

    async def test_get_next_steps_not_found(
        self,
        transfer_service: TransferService,
        test_organization: Organization,
    ):
        """Test that requesting next steps for nonexistent conversation raises error."""
        from paper_scraper.core.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await transfer_service.get_next_steps(
                conversation_id=uuid4(),
                organization_id=test_organization.id,
            )


# =============================================================================
# API Router Tests
# =============================================================================


class TestTransferRouter:
    """Tests for transfer API endpoints."""

    async def test_list_conversations(
        self,
        authenticated_client: AsyncClient,
        test_conversation: TransferConversation,
    ):
        """Test listing conversations via API."""
        response = await authenticated_client.get("/api/v1/transfer/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 1

    async def test_list_conversations_with_filters(
        self,
        authenticated_client: AsyncClient,
        test_conversation: TransferConversation,
    ):
        """Test filtering conversations via API."""
        response = await authenticated_client.get(
            "/api/v1/transfer/",
            params={"stage": "initial_contact", "search": "Nano"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    async def test_create_conversation(
        self,
        authenticated_client: AsyncClient,
        test_paper: Paper,
        test_author: Author,
    ):
        """Test creating a conversation via API."""
        response = await authenticated_client.post(
            "/api/v1/transfer/",
            json={
                "title": "Startup Discussion",
                "type": "startup",
                "paper_id": str(test_paper.id),
                "researcher_id": str(test_author.id),
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Startup Discussion"
        assert data["type"] == "startup"
        assert data["stage"] == "initial_contact"

    async def test_get_conversation_detail(
        self,
        authenticated_client: AsyncClient,
        test_conversation: TransferConversation,
        test_message: ConversationMessage,
    ):
        """Test getting conversation detail via API."""
        response = await authenticated_client.get(
            f"/api/v1/transfer/{test_conversation.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_conversation.id)
        assert "messages" in data
        assert "resources" in data
        assert "stage_history" in data

    async def test_get_conversation_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test getting nonexistent conversation returns 404."""
        response = await authenticated_client.get(
            f"/api/v1/transfer/{uuid4()}"
        )
        assert response.status_code == 404

    async def test_update_conversation_stage(
        self,
        authenticated_client: AsyncClient,
        test_conversation: TransferConversation,
    ):
        """Test updating conversation stage via API."""
        response = await authenticated_client.patch(
            f"/api/v1/transfer/{test_conversation.id}",
            json={
                "stage": "discovery",
                "notes": "Moving forward with discovery.",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stage"] == "discovery"

    async def test_add_message(
        self,
        authenticated_client: AsyncClient,
        test_conversation: TransferConversation,
    ):
        """Test adding a message via API."""
        response = await authenticated_client.post(
            f"/api/v1/transfer/{test_conversation.id}/messages",
            json={
                "content": "Meeting scheduled for Friday.",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Meeting scheduled for Friday."

    async def test_add_message_from_template(
        self,
        authenticated_client: AsyncClient,
        test_conversation: TransferConversation,
        test_template: MessageTemplate,
    ):
        """Test adding a message from template via API."""
        response = await authenticated_client.post(
            f"/api/v1/transfer/{test_conversation.id}/messages/from-template",
            json={
                "template_id": str(test_template.id),
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == test_template.content

    async def test_add_resource(
        self,
        authenticated_client: AsyncClient,
        test_conversation: TransferConversation,
    ):
        """Test attaching a resource via API."""
        response = await authenticated_client.post(
            f"/api/v1/transfer/{test_conversation.id}/resources",
            json={
                "name": "Term Sheet",
                "url": "https://example.com/term-sheet.pdf",
                "resource_type": "document",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Term Sheet"
        assert data["resource_type"] == "document"

    async def test_get_next_steps(
        self,
        authenticated_client: AsyncClient,
        test_conversation: TransferConversation,
    ):
        """Test getting AI next steps via API."""
        response = await authenticated_client.get(
            f"/api/v1/transfer/{test_conversation.id}/next-steps"
        )
        assert response.status_code == 200
        data = response.json()
        assert "steps" in data
        assert "summary" in data

    async def test_list_templates(
        self,
        authenticated_client: AsyncClient,
        test_template: MessageTemplate,
    ):
        """Test listing templates via API."""
        response = await authenticated_client.get("/api/v1/transfer/templates/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Initial Contact"

    async def test_create_template(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test creating a template via API."""
        response = await authenticated_client.post(
            "/api/v1/transfer/templates/",
            json={
                "name": "Discovery Follow-up",
                "subject": "Re: Technology Transfer Discussion",
                "content": "Thank you for the productive conversation...",
                "stage": "discovery",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Discovery Follow-up"
        assert data["stage"] == "discovery"

    async def test_update_template(
        self,
        authenticated_client: AsyncClient,
        test_template: MessageTemplate,
    ):
        """Test updating a template via API."""
        response = await authenticated_client.patch(
            f"/api/v1/transfer/templates/{test_template.id}",
            json={"name": "Updated Template"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Template"

    async def test_delete_template(
        self,
        authenticated_client: AsyncClient,
        test_template: MessageTemplate,
    ):
        """Test deleting a template via API."""
        response = await authenticated_client.delete(
            f"/api/v1/transfer/templates/{test_template.id}"
        )
        assert response.status_code == 204

    async def test_unauthorized_access(
        self,
        client: AsyncClient,
        test_conversation: TransferConversation,
    ):
        """Test that unauthenticated requests are rejected."""
        response = await client.get("/api/v1/transfer/")
        assert response.status_code == 401

    async def test_conversation_response_structure(
        self,
        authenticated_client: AsyncClient,
        test_conversation: TransferConversation,
    ):
        """Test that conversation response has correct structure."""
        response = await authenticated_client.get(
            f"/api/v1/transfer/{test_conversation.id}"
        )
        assert response.status_code == 200
        data = response.json()

        # Verify all expected fields are present
        assert "id" in data
        assert "organization_id" in data
        assert "paper_id" in data
        assert "researcher_id" in data
        assert "type" in data
        assert "stage" in data
        assert "title" in data
        assert "created_by" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "messages" in data
        assert "resources" in data
        assert "stage_history" in data
        assert "creator_name" in data
        assert "paper_title" in data
        assert "researcher_name" in data
