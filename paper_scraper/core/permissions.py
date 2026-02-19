"""Role-based access control system.

Provides granular permission checks using a Permission enum mapped to
user roles.  Use ``require_permission`` as a FastAPI dependency to guard
endpoints.
"""

from enum import Enum

from paper_scraper.core.exceptions import ForbiddenError


class Permission(str, Enum):
    """Granular permissions for RBAC."""

    PAPERS_READ = "papers:read"
    PAPERS_WRITE = "papers:write"
    PAPERS_DELETE = "papers:delete"
    SCORING_TRIGGER = "scoring:trigger"
    GROUPS_READ = "groups:read"
    GROUPS_MANAGE = "groups:manage"
    TRANSFER_READ = "transfer:read"
    TRANSFER_MANAGE = "transfer:manage"
    SUBMISSIONS_READ = "submissions:read"
    SUBMISSIONS_REVIEW = "submissions:review"
    BADGES_MANAGE = "badges:manage"
    KNOWLEDGE_MANAGE = "knowledge:manage"
    SETTINGS_ADMIN = "settings:admin"
    COMPLIANCE_VIEW = "compliance:view"
    DEVELOPER_MANAGE = "developer:manage"


ROLE_PERMISSIONS: dict[str, list[Permission]] = {
    "admin": list(Permission),
    "manager": [
        Permission.PAPERS_READ,
        Permission.PAPERS_WRITE,
        Permission.SCORING_TRIGGER,
        Permission.GROUPS_READ,
        Permission.GROUPS_MANAGE,
        Permission.TRANSFER_READ,
        Permission.TRANSFER_MANAGE,
        Permission.SUBMISSIONS_READ,
        Permission.SUBMISSIONS_REVIEW,
        Permission.KNOWLEDGE_MANAGE,
        Permission.COMPLIANCE_VIEW,
    ],
    "member": [
        Permission.PAPERS_READ,
        Permission.PAPERS_WRITE,
        Permission.SCORING_TRIGGER,
        Permission.GROUPS_READ,
        Permission.TRANSFER_READ,
        Permission.SUBMISSIONS_READ,
    ],
    "viewer": [
        Permission.PAPERS_READ,
        Permission.GROUPS_READ,
    ],
}


def get_permissions_for_role(role: str) -> list[Permission]:
    """Return the permissions for a given role.

    Args:
        role: Role name (e.g. "admin", "member").

    Returns:
        List of Permission values.  Empty list for unknown roles.
    """
    return ROLE_PERMISSIONS.get(role, [])


def check_permission(role: str, *permissions: Permission) -> None:
    """Raise ForbiddenError if *role* lacks any of *permissions*.

    Args:
        role: The user's role value string.
        *permissions: Permissions to check.

    Raises:
        ForbiddenError: When one or more permissions are missing.
    """
    role_perms = get_permissions_for_role(role)
    missing = [p for p in permissions if p not in role_perms]
    if missing:
        raise ForbiddenError("You don't have permission to perform this action")
