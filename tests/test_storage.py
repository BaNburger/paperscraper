"""Tests for the StorageService and file upload/download integration."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.security import create_access_token, get_password_hash
from paper_scraper.core.storage import StorageService
from paper_scraper.modules.auth.models import Organization, User, UserRole
from paper_scraper.modules.submissions.models import (
    ResearchSubmission,
    SubmissionAttachment,
    SubmissionStatus,
)
from paper_scraper.modules.transfer.models import (
    ConversationResource,
    TransferConversation,
    TransferStage,
    TransferType,
)

# =============================================================================
# StorageService Unit Tests
# =============================================================================


class TestStorageService:
    """Tests for StorageService core operations."""

    def test_upload_file(self):
        """Test that upload_file calls put_object correctly."""
        mock_client = MagicMock()
        service = StorageService.__new__(StorageService)
        service._client = mock_client
        service.bucket = "test-bucket"

        key = service.upload_file(
            file_content=b"test content",
            key="test/file.pdf",
            content_type="application/pdf",
        )

        assert key == "test/file.pdf"
        mock_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test/file.pdf",
            Body=b"test content",
            ContentType="application/pdf",
        )

    def test_get_download_url(self):
        """Test that get_download_url generates a presigned URL."""
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://example.com/signed"
        service = StorageService.__new__(StorageService)
        service._client = mock_client
        service.bucket = "test-bucket"

        url = service.get_download_url("test/file.pdf", expires_in=1800)

        assert url == "https://example.com/signed"
        mock_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "test/file.pdf"},
            ExpiresIn=1800,
        )

    def test_delete_file(self):
        """Test that delete_file calls delete_object."""
        mock_client = MagicMock()
        service = StorageService.__new__(StorageService)
        service._client = mock_client
        service.bucket = "test-bucket"

        service.delete_file("test/file.pdf")

        mock_client.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test/file.pdf",
        )

    def test_file_exists_true(self):
        """Test file_exists returns True for existing file."""
        mock_client = MagicMock()
        service = StorageService.__new__(StorageService)
        service._client = mock_client
        service.bucket = "test-bucket"

        assert service.file_exists("test/file.pdf") is True
        mock_client.head_object.assert_called_once()

    def test_file_exists_false(self):
        """Test file_exists returns False for missing file."""
        from botocore.exceptions import ClientError

        mock_client = MagicMock()
        mock_client.head_object.side_effect = ClientError({"Error": {"Code": "404"}}, "HeadObject")
        service = StorageService.__new__(StorageService)
        service._client = mock_client
        service.bucket = "test-bucket"

        assert service.file_exists("missing.pdf") is False

    def test_ensure_bucket_creates_when_missing(self):
        """Test ensure_bucket creates bucket when it doesn't exist."""
        from botocore.exceptions import ClientError

        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = ClientError({"Error": {"Code": "404"}}, "HeadBucket")
        service = StorageService.__new__(StorageService)
        service._client = mock_client
        service.bucket = "test-bucket"

        service.ensure_bucket()

        mock_client.create_bucket.assert_called_once_with(Bucket="test-bucket")

    def test_ensure_bucket_skips_when_exists(self):
        """Test ensure_bucket does nothing when bucket exists."""
        mock_client = MagicMock()
        service = StorageService.__new__(StorageService)
        service._client = mock_client
        service.bucket = "test-bucket"

        service.ensure_bucket()

        mock_client.create_bucket.assert_not_called()

    def test_validate_key_rejects_path_traversal(self):
        """Test that keys with '..' are rejected."""
        mock_client = MagicMock()
        service = StorageService.__new__(StorageService)
        service._client = mock_client
        service.bucket = "test-bucket"

        with pytest.raises(ValueError, match="Invalid storage key"):
            service.upload_file(b"content", "../etc/passwd", "text/plain")

    def test_validate_key_rejects_leading_slash(self):
        """Test that keys starting with '/' are rejected."""
        mock_client = MagicMock()
        service = StorageService.__new__(StorageService)
        service._client = mock_client
        service.bucket = "test-bucket"

        with pytest.raises(ValueError, match="Invalid storage key"):
            service.upload_file(b"content", "/absolute/path.pdf", "application/pdf")

    def test_validate_key_rejects_null_bytes(self):
        """Test that keys with null bytes are rejected."""
        mock_client = MagicMock()
        service = StorageService.__new__(StorageService)
        service._client = mock_client
        service.bucket = "test-bucket"

        with pytest.raises(ValueError, match="Invalid storage key"):
            service.upload_file(b"content", "file\x00.pdf", "application/pdf")

    def test_download_url_caps_expiry(self):
        """Test that download URL expiry is capped at 24 hours."""
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://example.com/signed"
        service = StorageService.__new__(StorageService)
        service._client = mock_client
        service.bucket = "test-bucket"

        service.get_download_url("test/file.pdf", expires_in=999999)

        call_args = mock_client.generate_presigned_url.call_args
        assert call_args.kwargs.get("ExpiresIn", call_args[1].get("ExpiresIn")) == 86400


# =============================================================================
# Submission Attachment Upload Integration Tests
# =============================================================================


@pytest_asyncio.fixture
async def test_member_user(
    db_session: AsyncSession,
    test_organization: Organization,
) -> User:
    """Create a test user with MEMBER role."""
    user = User(
        email="storage-member@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Storage Member",
        organization_id=test_organization.id,
        role=UserRole.MEMBER,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
def member_auth_headers(test_member_user: User) -> dict[str, str]:
    """Create auth headers for member user."""
    token = create_access_token(
        subject=str(test_member_user.id),
        extra_claims={
            "org_id": str(test_member_user.organization_id),
            "role": test_member_user.role.value,
        },
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def draft_submission(
    db_session: AsyncSession,
    test_member_user: User,
    test_organization: Organization,
) -> ResearchSubmission:
    """Create a draft submission for file upload tests."""
    submission = ResearchSubmission(
        organization_id=test_organization.id,
        submitted_by_id=test_member_user.id,
        title="File Upload Test Submission",
        abstract="Testing file uploads",
        status=SubmissionStatus.DRAFT,
    )
    db_session.add(submission)
    await db_session.flush()
    await db_session.refresh(submission)
    return submission


@pytest_asyncio.fixture
async def test_attachment(
    db_session: AsyncSession,
    draft_submission: ResearchSubmission,
) -> SubmissionAttachment:
    """Create a test attachment record."""
    attachment = SubmissionAttachment(
        submission_id=draft_submission.id,
        filename="test.pdf",
        file_path=f"submissions/{draft_submission.id}/abc123_test.pdf",
        file_size=1024,
        mime_type="application/pdf",
    )
    db_session.add(attachment)
    await db_session.flush()
    await db_session.refresh(attachment)
    return attachment


class TestSubmissionFileUpload:
    """Test submission file upload with storage integration."""

    @pytest.mark.asyncio
    @patch("paper_scraper.modules.submissions.router.get_storage_service")
    async def test_upload_persists_to_storage(
        self,
        mock_get_storage,
        client: AsyncClient,
        member_auth_headers: dict,
        draft_submission: ResearchSubmission,
    ):
        """Test that file upload persists to MinIO storage."""
        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage

        pdf_content = b"%PDF-1.4 fake pdf content"
        response = await client.post(
            f"/api/v1/submissions/{draft_submission.id}/attachments",
            files={"file": ("paper.pdf", pdf_content, "application/pdf")},
            headers=member_auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "paper.pdf"

        # Verify storage was called
        mock_storage.upload_file.assert_called_once()
        call_args = mock_storage.upload_file.call_args
        assert call_args.kwargs["content_type"] == "application/pdf"
        assert call_args.kwargs["file_content"] == pdf_content
        assert f"submissions/{draft_submission.id}/" in call_args.kwargs["key"]

    @pytest.mark.asyncio
    @patch("paper_scraper.modules.submissions.router.get_storage_service")
    async def test_upload_storage_failure_returns_502(
        self,
        mock_get_storage,
        client: AsyncClient,
        member_auth_headers: dict,
        draft_submission: ResearchSubmission,
    ):
        """Test that storage failures return 502."""
        mock_storage = MagicMock()
        mock_storage.upload_file.side_effect = Exception("Connection refused")
        mock_get_storage.return_value = mock_storage

        pdf_content = b"%PDF-1.4 fake pdf content"
        response = await client.post(
            f"/api/v1/submissions/{draft_submission.id}/attachments",
            files={"file": ("paper.pdf", pdf_content, "application/pdf")},
            headers=member_auth_headers,
        )

        assert response.status_code == 502

    @pytest.mark.asyncio
    async def test_upload_rejects_unsupported_mime(
        self,
        client: AsyncClient,
        member_auth_headers: dict,
        draft_submission: ResearchSubmission,
    ):
        """Test that unsupported MIME types are rejected."""
        response = await client.post(
            f"/api/v1/submissions/{draft_submission.id}/attachments",
            files={"file": ("script.sh", b"#!/bin/bash", "text/x-shellscript")},
            headers=member_auth_headers,
        )

        assert response.status_code == 400


class TestSubmissionFileDownload:
    """Test submission file download."""

    @pytest.mark.asyncio
    @patch("paper_scraper.modules.submissions.router.get_storage_service")
    async def test_download_redirects_to_presigned_url(
        self,
        mock_get_storage,
        client: AsyncClient,
        member_auth_headers: dict,
        draft_submission: ResearchSubmission,
        test_attachment: SubmissionAttachment,
    ):
        """Test that download redirects to a pre-signed URL."""
        mock_storage = MagicMock()
        mock_storage.get_download_url.return_value = "https://minio.local/signed-url"
        mock_get_storage.return_value = mock_storage

        response = await client.get(
            f"/api/v1/submissions/{draft_submission.id}"
            f"/attachments/{test_attachment.id}/download",
            headers=member_auth_headers,
            follow_redirects=False,
        )

        assert response.status_code == 307
        assert "minio.local" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_download_nonexistent_attachment_returns_404(
        self,
        client: AsyncClient,
        member_auth_headers: dict,
        draft_submission: ResearchSubmission,
    ):
        """Test that downloading a non-existent attachment returns 404."""
        response = await client.get(
            f"/api/v1/submissions/{draft_submission.id}" f"/attachments/{uuid4()}/download",
            headers=member_auth_headers,
            follow_redirects=False,
        )

        assert response.status_code == 404


# =============================================================================
# Transfer Resource Upload Integration Tests
# =============================================================================


@pytest_asyncio.fixture
async def test_conversation(
    db_session: AsyncSession,
    test_organization: Organization,
    test_user: User,
) -> TransferConversation:
    """Create a test transfer conversation for file upload tests."""
    conv = TransferConversation(
        organization_id=test_organization.id,
        type=TransferType.PATENT,
        stage=TransferStage.INITIAL_CONTACT,
        title="Storage Test Conversation",
        created_by=test_user.id,
    )
    db_session.add(conv)
    await db_session.flush()
    await db_session.refresh(conv)
    return conv


@pytest_asyncio.fixture
async def test_resource_with_file(
    db_session: AsyncSession,
    test_conversation: TransferConversation,
) -> ConversationResource:
    """Create a resource with a file path."""
    resource = ConversationResource(
        conversation_id=test_conversation.id,
        name="test_doc.pdf",
        file_path=f"transfer/{test_conversation.id}/abc123_test_doc.pdf",
        resource_type="file",
    )
    db_session.add(resource)
    await db_session.flush()
    await db_session.refresh(resource)
    return resource


@pytest_asyncio.fixture
async def test_resource_url_only(
    db_session: AsyncSession,
    test_conversation: TransferConversation,
) -> ConversationResource:
    """Create a URL-only resource (no file)."""
    resource = ConversationResource(
        conversation_id=test_conversation.id,
        name="External Link",
        url="https://example.com/doc.pdf",
        resource_type="link",
    )
    db_session.add(resource)
    await db_session.flush()
    await db_session.refresh(resource)
    return resource


class TestTransferResourceUpload:
    """Test transfer resource file upload."""

    @pytest.mark.asyncio
    @patch("paper_scraper.modules.transfer.router.get_storage_service")
    async def test_upload_resource_file(
        self,
        mock_get_storage,
        authenticated_client: AsyncClient,
        test_conversation: TransferConversation,
    ):
        """Test uploading a file as a transfer resource."""
        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage

        pdf_content = b"%PDF-1.4 fake pdf content"
        response = await authenticated_client.post(
            f"/api/v1/transfer/{test_conversation.id}/resources/upload",
            files={"file": ("contract.pdf", pdf_content, "application/pdf")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "contract.pdf"
        assert data["resource_type"] == "file"
        assert data["file_path"] is not None

        # Verify storage was called
        mock_storage.upload_file.assert_called_once()

    @pytest.mark.asyncio
    @patch("paper_scraper.modules.transfer.router.get_storage_service")
    async def test_upload_storage_failure_returns_502(
        self,
        mock_get_storage,
        authenticated_client: AsyncClient,
        test_conversation: TransferConversation,
    ):
        """Test that storage failures return 502."""
        mock_storage = MagicMock()
        mock_storage.upload_file.side_effect = Exception("Storage down")
        mock_get_storage.return_value = mock_storage

        pdf_content = b"%PDF-1.4 fake"
        response = await authenticated_client.post(
            f"/api/v1/transfer/{test_conversation.id}/resources/upload",
            files={"file": ("doc.pdf", pdf_content, "application/pdf")},
        )

        assert response.status_code == 502

    @pytest.mark.asyncio
    async def test_upload_rejects_unsupported_mime(
        self,
        authenticated_client: AsyncClient,
        test_conversation: TransferConversation,
    ):
        """Test that unsupported MIME types are rejected."""
        response = await authenticated_client.post(
            f"/api/v1/transfer/{test_conversation.id}/resources/upload",
            files={"file": ("virus.exe", b"\x00\x00", "application/x-executable")},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_rejects_mismatched_magic_bytes(
        self,
        authenticated_client: AsyncClient,
        test_conversation: TransferConversation,
    ):
        """Test that files with wrong magic bytes are rejected."""
        # Send "application/pdf" but content starts with PNG magic bytes
        png_content = b"\x89PNG fake content"
        response = await authenticated_client.post(
            f"/api/v1/transfer/{test_conversation.id}/resources/upload",
            files={"file": ("fake.pdf", png_content, "application/pdf")},
        )

        assert response.status_code == 400
        assert "does not match" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_unauthenticated(
        self,
        client: AsyncClient,
        test_conversation: TransferConversation,
    ):
        """Test that unauthenticated uploads are rejected."""
        response = await client.post(
            f"/api/v1/transfer/{test_conversation.id}/resources/upload",
            files={"file": ("doc.pdf", b"%PDF", "application/pdf")},
        )

        assert response.status_code == 401


class TestTransferResourceDownload:
    """Test transfer resource file download."""

    @pytest.mark.asyncio
    @patch("paper_scraper.modules.transfer.router.get_storage_service")
    async def test_download_resource_redirects(
        self,
        mock_get_storage,
        authenticated_client: AsyncClient,
        test_conversation: TransferConversation,
        test_resource_with_file: ConversationResource,
    ):
        """Test that download redirects to a pre-signed URL."""
        mock_storage = MagicMock()
        mock_storage.get_download_url.return_value = "https://minio.local/signed"
        mock_get_storage.return_value = mock_storage

        response = await authenticated_client.get(
            f"/api/v1/transfer/{test_conversation.id}"
            f"/resources/{test_resource_with_file.id}/download",
            follow_redirects=False,
        )

        assert response.status_code == 307
        assert "minio.local" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_download_url_only_resource_returns_400(
        self,
        authenticated_client: AsyncClient,
        test_conversation: TransferConversation,
        test_resource_url_only: ConversationResource,
    ):
        """Test that downloading a URL-only resource returns 400."""
        response = await authenticated_client.get(
            f"/api/v1/transfer/{test_conversation.id}"
            f"/resources/{test_resource_url_only.id}/download",
            follow_redirects=False,
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_download_nonexistent_resource_returns_404(
        self,
        authenticated_client: AsyncClient,
        test_conversation: TransferConversation,
    ):
        """Test that downloading a non-existent resource returns 404."""
        response = await authenticated_client.get(
            f"/api/v1/transfer/{test_conversation.id}" f"/resources/{uuid4()}/download",
            follow_redirects=False,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_unauthenticated(
        self,
        client: AsyncClient,
        test_conversation: TransferConversation,
        test_resource_with_file: ConversationResource,
    ):
        """Test that unauthenticated downloads are rejected."""
        response = await client.get(
            f"/api/v1/transfer/{test_conversation.id}"
            f"/resources/{test_resource_with_file.id}/download",
        )

        assert response.status_code == 401
