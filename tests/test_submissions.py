"""Tests for research submissions module."""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.security import create_access_token, get_password_hash
from paper_scraper.modules.auth.models import Organization, User, UserRole
from paper_scraper.modules.submissions.models import (
    ResearchSubmission,
    SubmissionAttachment,
    SubmissionScore,
    SubmissionStatus,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def test_member_user(
    db_session: AsyncSession,
    test_organization: Organization,
) -> User:
    """Create a test user with MEMBER role."""
    user = User(
        email="member@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test Member",
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
async def test_submission(
    db_session: AsyncSession,
    test_member_user: User,
    test_organization: Organization,
) -> ResearchSubmission:
    """Create a test submission in draft status."""
    submission = ResearchSubmission(
        organization_id=test_organization.id,
        submitted_by_id=test_member_user.id,
        title="Novel CRISPR Gene Editing Technique",
        abstract="We present a novel approach to CRISPR-based gene editing...",
        research_field="Biotechnology",
        keywords=["CRISPR", "gene editing", "biotechnology"],
        status=SubmissionStatus.DRAFT,
    )
    db_session.add(submission)
    await db_session.flush()
    await db_session.refresh(submission)
    return submission


@pytest_asyncio.fixture
async def submitted_submission(
    db_session: AsyncSession,
    test_member_user: User,
    test_organization: Organization,
) -> ResearchSubmission:
    """Create a test submission in submitted status."""
    submission = ResearchSubmission(
        organization_id=test_organization.id,
        submitted_by_id=test_member_user.id,
        title="AI-Powered Drug Discovery",
        abstract="We demonstrate a new AI framework for drug discovery...",
        research_field="AI/Healthcare",
        keywords=["AI", "drug discovery"],
        status=SubmissionStatus.SUBMITTED,
    )
    db_session.add(submission)
    await db_session.flush()
    await db_session.refresh(submission)
    return submission


# =============================================================================
# Researcher Endpoint Tests
# =============================================================================


class TestCreateSubmission:
    """Test submission creation."""

    @pytest.mark.asyncio
    async def test_create_submission(
        self,
        client: AsyncClient,
        member_auth_headers: dict,
        test_member_user: User,
    ):
        """Test creating a new submission."""
        response = await client.post(
            "/api/v1/submissions/",
            json={
                "title": "My Research Paper",
                "abstract": "This paper presents...",
                "research_field": "Computer Science",
                "keywords": ["AI", "machine learning"],
                "commercial_potential": "Could be used in healthcare",
            },
            headers=member_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "My Research Paper"
        assert data["abstract"] == "This paper presents..."
        assert data["status"] == "draft"
        assert data["research_field"] == "Computer Science"
        assert data["keywords"] == ["AI", "machine learning"]
        assert data["submitted_by"]["id"] == str(test_member_user.id)

    @pytest.mark.asyncio
    async def test_create_submission_minimal(
        self,
        client: AsyncClient,
        member_auth_headers: dict,
    ):
        """Test creating a submission with minimal data."""
        response = await client.post(
            "/api/v1/submissions/",
            json={"title": "Minimal Submission"},
            headers=member_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Submission"
        assert data["status"] == "draft"
        assert data["abstract"] is None

    @pytest.mark.asyncio
    async def test_create_submission_unauthenticated(
        self,
        client: AsyncClient,
    ):
        """Test that unauthenticated users cannot create submissions."""
        response = await client.post(
            "/api/v1/submissions/",
            json={"title": "Test"},
        )
        assert response.status_code == 401


class TestListMySubmissions:
    """Test listing own submissions."""

    @pytest.mark.asyncio
    async def test_list_empty(
        self,
        client: AsyncClient,
        member_auth_headers: dict,
    ):
        """Test listing submissions when none exist."""
        response = await client.get(
            "/api/v1/submissions/my",
            headers=member_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_own_submissions(
        self,
        client: AsyncClient,
        member_auth_headers: dict,
        test_submission: ResearchSubmission,
    ):
        """Test listing own submissions."""
        response = await client.get(
            "/api/v1/submissions/my",
            headers=member_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Novel CRISPR Gene Editing Technique"

    @pytest.mark.asyncio
    async def test_list_filter_by_status(
        self,
        client: AsyncClient,
        member_auth_headers: dict,
        test_submission: ResearchSubmission,
        submitted_submission: ResearchSubmission,
    ):
        """Test filtering submissions by status."""
        response = await client.get(
            "/api/v1/submissions/my?status=draft",
            headers=member_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "draft"


class TestGetSubmission:
    """Test getting a single submission."""

    @pytest.mark.asyncio
    async def test_get_submission(
        self,
        client: AsyncClient,
        member_auth_headers: dict,
        test_submission: ResearchSubmission,
    ):
        """Test getting a submission by ID."""
        response = await client.get(
            f"/api/v1/submissions/{test_submission.id}",
            headers=member_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Novel CRISPR Gene Editing Technique"
        assert "attachments" in data
        assert "scores" in data

    @pytest.mark.asyncio
    async def test_get_submission_not_found(
        self,
        client: AsyncClient,
        member_auth_headers: dict,
    ):
        """Test getting a non-existent submission."""
        response = await client.get(
            f"/api/v1/submissions/{uuid.uuid4()}",
            headers=member_auth_headers,
        )
        assert response.status_code == 404


class TestUpdateSubmission:
    """Test updating draft submissions."""

    @pytest.mark.asyncio
    async def test_update_draft(
        self,
        client: AsyncClient,
        member_auth_headers: dict,
        test_submission: ResearchSubmission,
    ):
        """Test updating a draft submission."""
        response = await client.patch(
            f"/api/v1/submissions/{test_submission.id}",
            json={
                "title": "Updated Title",
                "abstract": "Updated abstract text",
            },
            headers=member_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["abstract"] == "Updated abstract text"

    @pytest.mark.asyncio
    async def test_cannot_update_submitted(
        self,
        client: AsyncClient,
        member_auth_headers: dict,
        submitted_submission: ResearchSubmission,
    ):
        """Test that submitted submissions cannot be updated."""
        response = await client.patch(
            f"/api/v1/submissions/{submitted_submission.id}",
            json={"title": "Should Fail"},
            headers=member_auth_headers,
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_cannot_update_others_submission(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_submission: ResearchSubmission,
    ):
        """Test that users cannot update other people's submissions."""
        response = await client.patch(
            f"/api/v1/submissions/{test_submission.id}",
            json={"title": "Hijack Attempt"},
            headers=auth_headers,  # admin user, not the submitter
        )
        assert response.status_code == 403


class TestSubmitForReview:
    """Test submitting for review."""

    @pytest.mark.asyncio
    async def test_submit_for_review(
        self,
        client: AsyncClient,
        member_auth_headers: dict,
        test_submission: ResearchSubmission,
    ):
        """Test submitting a draft for review."""
        response = await client.post(
            f"/api/v1/submissions/{test_submission.id}/submit",
            headers=member_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "submitted"
        assert data["submitted_at"] is not None

    @pytest.mark.asyncio
    async def test_cannot_submit_without_abstract(
        self,
        client: AsyncClient,
        member_auth_headers: dict,
        db_session: AsyncSession,
        test_member_user: User,
        test_organization: Organization,
    ):
        """Test that submission requires an abstract."""
        submission = ResearchSubmission(
            organization_id=test_organization.id,
            submitted_by_id=test_member_user.id,
            title="No Abstract Paper",
            status=SubmissionStatus.DRAFT,
        )
        db_session.add(submission)
        await db_session.flush()

        response = await client.post(
            f"/api/v1/submissions/{submission.id}/submit",
            headers=member_auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_cannot_resubmit(
        self,
        client: AsyncClient,
        member_auth_headers: dict,
        submitted_submission: ResearchSubmission,
    ):
        """Test that already submitted submissions cannot be resubmitted."""
        response = await client.post(
            f"/api/v1/submissions/{submitted_submission.id}/submit",
            headers=member_auth_headers,
        )
        assert response.status_code == 422


# =============================================================================
# TTO Review Endpoint Tests
# =============================================================================


class TestListAllSubmissions:
    """Test listing all submissions (TTO view)."""

    @pytest.mark.asyncio
    async def test_list_all_requires_manager(
        self,
        client: AsyncClient,
        member_auth_headers: dict,
    ):
        """Test that listing all submissions requires manager/admin role."""
        response = await client.get(
            "/api/v1/submissions/",
            headers=member_auth_headers,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_all_as_admin(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_submission: ResearchSubmission,
        submitted_submission: ResearchSubmission,
    ):
        """Test listing all submissions as admin."""
        response = await client.get(
            "/api/v1/submissions/",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2


class TestReviewSubmission:
    """Test submission review."""

    @pytest.mark.asyncio
    async def test_approve_submission(
        self,
        client: AsyncClient,
        auth_headers: dict,
        submitted_submission: ResearchSubmission,
    ):
        """Test approving a submission."""
        response = await client.patch(
            f"/api/v1/submissions/{submitted_submission.id}/review",
            json={
                "decision": "approved",
                "notes": "Excellent commercial potential",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["review_notes"] == "Excellent commercial potential"
        assert data["reviewed_at"] is not None

    @pytest.mark.asyncio
    async def test_reject_submission(
        self,
        client: AsyncClient,
        auth_headers: dict,
        submitted_submission: ResearchSubmission,
    ):
        """Test rejecting a submission."""
        response = await client.patch(
            f"/api/v1/submissions/{submitted_submission.id}/review",
            json={
                "decision": "rejected",
                "notes": "Not commercially viable",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_cannot_review_draft(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_submission: ResearchSubmission,
    ):
        """Test that draft submissions cannot be reviewed."""
        response = await client.patch(
            f"/api/v1/submissions/{test_submission.id}/review",
            json={"decision": "approved"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_review_requires_manager(
        self,
        client: AsyncClient,
        member_auth_headers: dict,
        submitted_submission: ResearchSubmission,
    ):
        """Test that reviewing requires manager/admin role."""
        response = await client.patch(
            f"/api/v1/submissions/{submitted_submission.id}/review",
            json={"decision": "approved"},
            headers=member_auth_headers,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_invalid_decision(
        self,
        client: AsyncClient,
        auth_headers: dict,
        submitted_submission: ResearchSubmission,
    ):
        """Test that invalid review decisions are rejected."""
        response = await client.patch(
            f"/api/v1/submissions/{submitted_submission.id}/review",
            json={"decision": "invalid_status"},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestConvertToPaper:
    """Test converting submissions to papers."""

    @pytest.mark.asyncio
    async def test_convert_approved_submission(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_member_user: User,
        test_organization: Organization,
    ):
        """Test converting an approved submission to a paper."""
        submission = ResearchSubmission(
            organization_id=test_organization.id,
            submitted_by_id=test_member_user.id,
            title="Approved Research",
            abstract="Approved submission abstract...",
            research_field="Physics",
            keywords=["quantum", "computing"],
            status=SubmissionStatus.APPROVED,
            doi="10.1234/test",
        )
        db_session.add(submission)
        await db_session.flush()

        response = await client.post(
            f"/api/v1/submissions/{submission.id}/convert",
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Approved Research"
        assert data["doi"] == "10.1234/test"
        assert data["source"] == "manual"

    @pytest.mark.asyncio
    async def test_cannot_convert_draft(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_submission: ResearchSubmission,
    ):
        """Test that draft submissions cannot be converted."""
        response = await client.post(
            f"/api/v1/submissions/{test_submission.id}/convert",
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_cannot_convert_submitted(
        self,
        client: AsyncClient,
        auth_headers: dict,
        submitted_submission: ResearchSubmission,
    ):
        """Test that submitted (non-approved) submissions cannot be converted."""
        response = await client.post(
            f"/api/v1/submissions/{submitted_submission.id}/convert",
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_cannot_convert_twice(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_member_user: User,
        test_organization: Organization,
    ):
        """Test that a submission cannot be converted twice."""
        submission = ResearchSubmission(
            organization_id=test_organization.id,
            submitted_by_id=test_member_user.id,
            title="Already Converted",
            abstract="Already converted...",
            status=SubmissionStatus.APPROVED,
        )
        db_session.add(submission)
        await db_session.flush()

        # First conversion
        response = await client.post(
            f"/api/v1/submissions/{submission.id}/convert",
            headers=auth_headers,
        )
        assert response.status_code == 201

        # Second conversion should fail
        response = await client.post(
            f"/api/v1/submissions/{submission.id}/convert",
            headers=auth_headers,
        )
        assert response.status_code == 422


# =============================================================================
# Tenant Isolation Tests
# =============================================================================


class TestSubmissionTenantIsolation:
    """Test tenant isolation for submissions."""

    @pytest.mark.asyncio
    async def test_cannot_see_other_org_submissions(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_member_user: User,
        test_organization: Organization,
    ):
        """Test that users cannot see submissions from other organizations."""
        # Create submission in current org
        my_submission = ResearchSubmission(
            organization_id=test_organization.id,
            submitted_by_id=test_member_user.id,
            title="My Submission",
            status=SubmissionStatus.SUBMITTED,
        )
        db_session.add(my_submission)
        await db_session.flush()

        response = await client.get(
            "/api/v1/submissions/",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # All items should belong to the user's org
        for item in data["items"]:
            assert item["organization_id"] == str(test_organization.id)

    @pytest.mark.asyncio
    async def test_cannot_access_other_org_submission(
        self,
        client: AsyncClient,
        member_auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test that users cannot access submissions from other orgs by ID."""
        # Create a submission in a different org
        other_org = Organization(name="Other Org", type="university")
        db_session.add(other_org)
        await db_session.flush()

        other_user = User(
            email="other@example.com",
            hashed_password=get_password_hash("password"),
            organization_id=other_org.id,
            role=UserRole.MEMBER,
        )
        db_session.add(other_user)
        await db_session.flush()

        other_submission = ResearchSubmission(
            organization_id=other_org.id,
            submitted_by_id=other_user.id,
            title="Other Org Submission",
            status=SubmissionStatus.DRAFT,
        )
        db_session.add(other_submission)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/submissions/{other_submission.id}",
            headers=member_auth_headers,
        )
        assert response.status_code == 404


# =============================================================================
# Model Tests
# =============================================================================


class TestSubmissionModel:
    """Test submission model directly."""

    @pytest.mark.asyncio
    async def test_default_status(
        self,
        db_session: AsyncSession,
        test_member_user: User,
        test_organization: Organization,
    ):
        """Test that submissions default to draft status."""
        submission = ResearchSubmission(
            organization_id=test_organization.id,
            submitted_by_id=test_member_user.id,
            title="Default Status Test",
        )
        db_session.add(submission)
        await db_session.flush()
        assert submission.status == SubmissionStatus.DRAFT

    @pytest.mark.asyncio
    async def test_submission_with_attachments(
        self,
        db_session: AsyncSession,
        test_member_user: User,
        test_organization: Organization,
    ):
        """Test creating a submission with attachments."""
        submission = ResearchSubmission(
            organization_id=test_organization.id,
            submitted_by_id=test_member_user.id,
            title="With Attachments",
        )
        db_session.add(submission)
        await db_session.flush()

        attachment = SubmissionAttachment(
            submission_id=submission.id,
            filename="paper.pdf",
            file_path="submissions/test/paper.pdf",
            file_size=1024,
            mime_type="application/pdf",
        )
        db_session.add(attachment)
        await db_session.flush()
        await db_session.refresh(attachment)

        assert attachment.submission_id == submission.id
        assert attachment.filename == "paper.pdf"

    @pytest.mark.asyncio
    async def test_submission_with_score(
        self,
        db_session: AsyncSession,
        test_member_user: User,
        test_organization: Organization,
    ):
        """Test creating a submission with scores."""
        submission = ResearchSubmission(
            organization_id=test_organization.id,
            submitted_by_id=test_member_user.id,
            title="With Score",
        )
        db_session.add(submission)
        await db_session.flush()

        score = SubmissionScore(
            submission_id=submission.id,
            novelty=8.5,
            ip_potential=7.0,
            marketability=6.5,
            feasibility=8.0,
            commercialization=7.5,
            overall_score=7.5,
            overall_confidence=0.85,
            model_version="gpt-5-mini-20260101",
        )
        db_session.add(score)
        await db_session.flush()
        await db_session.refresh(score)

        assert score.overall_score == 7.5
        assert score.model_version == "gpt-5-mini-20260101"
