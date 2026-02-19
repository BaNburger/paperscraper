"""Author profile enrichment via GitHub and ORCID APIs.

Fetches public profile data for paper authors to provide richer context
for the Team Readiness scoring dimension.  Results are injected into the
LLM prompt alongside existing signals (h-index, affiliations, etc.).

GitHub: search by author name → top repos, languages, followers.
ORCID:  fetch by ORCID ID   → employment, education, funding, peer reviews.
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any

import httpx

from paper_scraper.core.config import settings

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15.0
GITHUB_NAME_SIMILARITY_THRESHOLD = 0.6
GITHUB_RATE_LIMIT_FLOOR = 10  # skip if remaining requests < this

# Validation patterns
_ORCID_PATTERN = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
_GITHUB_LOGIN_PATTERN = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,37}[a-zA-Z0-9])?$")


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class GitHubProfile:
    """Public GitHub profile data for an author."""

    username: str
    bio: str | None = None
    company: str | None = None
    public_repos: int = 0
    followers: int = 0
    top_languages: list[str] = field(default_factory=list)
    popular_repos: list[str] = field(default_factory=list)


@dataclass
class OrcidProfile:
    """Public ORCID profile data for an author."""

    orcid_id: str
    current_employment: str | None = None
    past_affiliations: list[str] = field(default_factory=list)
    education: list[str] = field(default_factory=list)
    funding_count: int = 0
    peer_review_count: int = 0
    works_count: int = 0


@dataclass
class AuthorProfile:
    """Combined profile for a single author."""

    name: str
    orcid: str | None = None
    github: GitHubProfile | None = None
    orcid_data: OrcidProfile | None = None

    def to_schema_dict(self) -> dict:
        """Serialize to a dict matching AuthorProfileSchema fields."""
        return {
            "name": self.name,
            "orcid": self.orcid,
            "github_username": self.github.username if self.github else None,
            "github_public_repos": self.github.public_repos if self.github else None,
            "github_followers": self.github.followers if self.github else None,
            "github_top_languages": self.github.top_languages if self.github else [],
            "github_popular_repos": self.github.popular_repos if self.github else [],
            "orcid_current_employment": (
                self.orcid_data.current_employment if self.orcid_data else None
            ),
            "orcid_past_affiliations": (
                self.orcid_data.past_affiliations[:3] if self.orcid_data else []
            ),
            "orcid_funding_count": (self.orcid_data.funding_count if self.orcid_data else None),
            "orcid_peer_review_count": (
                self.orcid_data.peer_review_count if self.orcid_data else None
            ),
        }


@dataclass
class AuthorProfileResult:
    """Container for author profile enrichment results."""

    profiles: list[AuthorProfile] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.profiles


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def fetch_author_profiles(
    authors: list[Any],
    max_authors: int = 5,
) -> AuthorProfileResult:
    """Fetch GitHub and ORCID profiles for paper authors.

    Args:
        authors: Author ORM objects with ``name``, ``orcid``, ``affiliations``.
        max_authors: Maximum number of authors to enrich (by position order).

    Returns:
        AuthorProfileResult with enriched profiles.
    """
    if not authors:
        return AuthorProfileResult()

    limited = authors[:max_authors]
    errors: list[str] = []

    async def _enrich_one(author: Any, idx: int) -> AuthorProfile | None:
        name = getattr(author, "name", None)
        if not name:
            return None

        orcid_id = getattr(author, "orcid", None)
        affiliations = getattr(author, "affiliations", []) or []

        github_profile = None
        orcid_profile = None

        # Fire GitHub + ORCID fetches concurrently
        tasks = [_search_github_user(name, affiliations)]
        if orcid_id:
            tasks.append(_fetch_orcid_profile(orcid_id))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        if isinstance(results[0], Exception):
            errors.append(f"GitHub error for author at position {idx}")
        else:
            github_profile = results[0]

        if orcid_id and len(results) > 1:
            if isinstance(results[1], Exception):
                errors.append(f"ORCID error for author at position {idx}")
            else:
                orcid_profile = results[1]

        if github_profile or orcid_profile:
            return AuthorProfile(
                name=name,
                orcid=orcid_id,
                github=github_profile,
                orcid_data=orcid_profile,
            )
        return None

    # Enrich all authors concurrently
    enrich_results = await asyncio.gather(
        *[_enrich_one(a, i) for i, a in enumerate(limited)],
        return_exceptions=True,
    )

    profiles: list[AuthorProfile] = []
    for r in enrich_results:
        if isinstance(r, Exception):
            errors.append(str(r))
        elif r is not None:
            profiles.append(r)

    return AuthorProfileResult(profiles=profiles, errors=errors)


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------


def _github_headers() -> dict[str, str]:
    """Build GitHub API request headers."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = settings.GITHUB_API_TOKEN
    if token:
        headers["Authorization"] = f"Bearer {token.get_secret_value()}"
    return headers


async def _search_github_user(
    name: str,
    affiliations: list[str] | None = None,
) -> GitHubProfile | None:
    """Search GitHub for a user matching the author name.

    Uses the GitHub Search Users API and applies name similarity filtering
    to avoid false positives for common names.
    """
    if not name or not name.strip():
        return None

    clean_name = name.strip()[:100]
    query = f"{clean_name} type:user"
    url = f"{settings.GITHUB_API_BASE_URL}/search/users"

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(
                url,
                params={"q": query, "per_page": 3},
                headers=_github_headers(),
            )

            # Check rate limit (safe int conversion)
            remaining = resp.headers.get("X-RateLimit-Remaining")
            if remaining:
                try:
                    remaining_int = int(remaining)
                except (TypeError, ValueError):
                    remaining_int = 0
                if remaining_int < GITHUB_RATE_LIMIT_FLOOR:
                    logger.warning("GitHub rate limit low (%s remaining), skipping", remaining)
                    return None

            resp.raise_for_status()
            data = resp.json()

            items = data.get("items", [])
            if not items:
                return None

            # Find best match by name similarity
            best_match = _pick_best_github_match(clean_name, items, affiliations)
            if not best_match:
                return None

            username = best_match.get("login", "")
            if not _GITHUB_LOGIN_PATTERN.match(username):
                logger.warning("GitHub returned unexpected login format, discarding")
                return None

            # Fetch full profile + repos
            profile_resp = await client.get(
                f"{settings.GITHUB_API_BASE_URL}/users/{username}",
                headers=_github_headers(),
            )
            profile_resp.raise_for_status()
            profile_data = profile_resp.json()

            repos_resp = await client.get(
                f"{settings.GITHUB_API_BASE_URL}/users/{username}/repos",
                params={"sort": "stars", "direction": "desc", "per_page": 5},
                headers=_github_headers(),
            )
            repos_resp.raise_for_status()
            repos_data = repos_resp.json()

            top_languages = _extract_top_languages(repos_data)
            popular_repos = _format_popular_repos(repos_data)

            return GitHubProfile(
                username=username,
                bio=_safe_str(profile_data.get("bio"), 200),
                company=_safe_str(profile_data.get("company"), 100),
                public_repos=min(int(profile_data.get("public_repos", 0)), 500_000),
                followers=min(int(profile_data.get("followers", 0)), 10_000_000),
                top_languages=top_languages,
                popular_repos=popular_repos,
            )

    except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as e:
        logger.warning("GitHub search failed for '%s': %s", clean_name, e)
        return None
    except (ValueError, KeyError) as e:
        logger.warning("GitHub response parsing error for '%s': %s", clean_name, e)
        return None


def _pick_best_github_match(
    author_name: str,
    items: list[dict],
    affiliations: list[str] | None = None,
) -> dict | None:
    """Pick the best GitHub user match based on name similarity."""
    best: dict | None = None
    best_score = 0.0

    author_lower = author_name.lower()

    for item in items[:3]:
        login = (item.get("login") or "").lower()
        # GitHub name field from search is not always present
        # We'll check against login
        name_score = _name_similarity(author_lower, login)

        # Also check the display name if available via html_url heuristic
        # The search API doesn't return 'name', so login is our best signal
        if name_score > best_score and name_score >= GITHUB_NAME_SIMILARITY_THRESHOLD:
            best = item
            best_score = name_score

    # If no login matched well enough, try a relaxed match:
    # Author "John Smith" might have login "jsmith" — check first initial + last name
    if not best and len(items) > 0:
        parts = author_lower.split()
        if len(parts) >= 2:
            first_initial = parts[0][0] if parts[0] else ""
            last_name = parts[-1]
            for item in items[:3]:
                login = (item.get("login") or "").lower()
                # Check patterns like "jsmith", "johnsmith", "smith_j"
                if (
                    login
                    and last_name in login
                    and (first_initial == login[0] or author_lower.replace(" ", "") in login)
                ):
                    best = item
                    break

    return best


def _extract_top_languages(repos: list[dict]) -> list[str]:
    """Extract unique languages from top repos."""
    langs: list[str] = []
    seen: set[str] = set()
    for repo in repos:
        lang = repo.get("language")
        if lang and lang not in seen:
            seen.add(lang)
            langs.append(lang)
        if len(langs) >= 5:
            break
    return langs


def _format_popular_repos(repos: list[dict]) -> list[str]:
    """Format top repos as 'name (stars)' strings."""
    formatted: list[str] = []
    for repo in repos[:3]:
        name = repo.get("name", "unknown")[:50]
        stars = repo.get("stargazers_count", 0)
        formatted.append(f"{name} ({stars} stars)")
    return formatted


# ---------------------------------------------------------------------------
# ORCID
# ---------------------------------------------------------------------------


async def _fetch_orcid_profile(orcid: str) -> OrcidProfile | None:
    """Fetch public ORCID profile data.

    Args:
        orcid: ORCID identifier (e.g., "0000-0001-2345-6789").
              May include the URL prefix which will be stripped.
    """
    if not orcid:
        return None

    # Strip URL prefix if present (e.g., "https://orcid.org/0000-...")
    clean_orcid = orcid.strip()
    if "/" in clean_orcid:
        clean_orcid = clean_orcid.rstrip("/").rsplit("/", 1)[-1]

    # Validate ORCID format to prevent SSRF/path traversal
    if not _ORCID_PATTERN.match(clean_orcid):
        logger.warning("Invalid ORCID format, skipping: %s", clean_orcid[:20])
        return None

    url = f"{settings.ORCID_API_BASE_URL}/{clean_orcid}/record"

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(url, headers={"Accept": "application/json"})
            resp.raise_for_status()
            data = resp.json()

    except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as e:
        logger.warning("ORCID fetch failed for '%s': %s", clean_orcid, e)
        return None
    except ValueError as e:
        logger.warning("ORCID returned invalid JSON for '%s': %s", clean_orcid, e)
        return None

    return _parse_orcid_record(clean_orcid, data)


def _parse_orcid_record(orcid_id: str, data: dict) -> OrcidProfile:
    """Parse an ORCID API response into an OrcidProfile."""
    activities = data.get("activities-summary", {})

    # Employment
    employments = _extract_orcid_affiliations(
        activities.get("employments", {}).get("affiliation-group", [])
    )
    current_employment = employments[0] if employments else None
    past_affiliations = employments[1:4] if len(employments) > 1 else []

    # Education
    education = _extract_orcid_affiliations(
        activities.get("educations", {}).get("affiliation-group", [])
    )

    # Funding count
    funding_groups = activities.get("fundings", {}).get("group", [])
    funding_count = len(funding_groups)

    # Peer review count
    peer_review_groups = activities.get("peer-reviews", {}).get("group", [])
    peer_review_count = len(peer_review_groups)

    # Works count
    works_groups = activities.get("works", {}).get("group", [])
    works_count = len(works_groups)

    return OrcidProfile(
        orcid_id=orcid_id,
        current_employment=current_employment,
        past_affiliations=past_affiliations,
        education=education[:3],
        funding_count=funding_count,
        peer_review_count=peer_review_count,
        works_count=works_count,
    )


def _extract_orcid_affiliations(affiliation_groups: list[dict]) -> list[str]:
    """Extract affiliation names from ORCID affiliation groups.

    Returns a list of 'Organization (Role, Start-End)' strings,
    most recent first.
    """
    affiliations: list[str] = []
    for group in affiliation_groups:
        summaries = group.get("summaries", [])
        for summary_wrapper in summaries:
            # Keys vary: "employment-summary", "education-summary", etc.
            for _key, summary in summary_wrapper.items():
                if not isinstance(summary, dict):
                    continue
                org = summary.get("organization", {})
                org_name = org.get("name", "")
                if not org_name:
                    continue

                role = summary.get("role-title", "")
                start = _orcid_date_str(summary.get("start-date"))
                end = _orcid_date_str(summary.get("end-date")) or "present"

                parts = [org_name[:150]]
                if role:
                    if start:
                        parts.append(f"({role[:100]}, {start}-{end})")
                    else:
                        parts.append(f"({role[:100]})")
                elif start:
                    parts.append(f"({start}-{end})")

                affiliations.append(" ".join(parts))
                break  # one per group
    return affiliations


def _orcid_date_str(date_obj: dict | None) -> str | None:
    """Convert ORCID date object to year string."""
    if not date_obj:
        return None
    year = date_obj.get("year", {})
    if isinstance(year, dict):
        return year.get("value")
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _name_similarity(a: str, b: str) -> float:
    """Compute name similarity using SequenceMatcher.

    Also checks last-name match as a fallback for cases like
    "John Smith" vs "johnsmith".
    """
    # Direct sequence match
    ratio = SequenceMatcher(None, a, b).ratio()

    # Also try without spaces (for "johnsmith" matching "john smith")
    a_collapsed = a.replace(" ", "").replace("-", "")
    b_collapsed = b.replace(" ", "").replace("-", "")
    collapsed_ratio = SequenceMatcher(None, a_collapsed, b_collapsed).ratio()

    return max(ratio, collapsed_ratio)


def _safe_str(value: Any, max_length: int = 200) -> str | None:
    """Safely convert a value to a truncated string."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:max_length]
