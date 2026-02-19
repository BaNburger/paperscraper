"""Dimension-specific context builder for the scoring pipeline.

Replaces the monolithic DefaultScoreContextAssembler with per-dimension
context strings, each tailored to the dimension's scoring criteria and
truncated within a token budget.
"""

import logging
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.knowledge.models import KnowledgeType
from paper_scraper.modules.knowledge.service import KnowledgeService
from paper_scraper.modules.papers.context_service import PaperContextService
from paper_scraper.modules.papers.models import Paper, PaperSource
from paper_scraper.modules.scoring.author_profile_client import (
    AuthorProfileResult,
    fetch_author_profiles,
)
from paper_scraper.modules.scoring.citation_graph import (
    CitationGraph,
    fetch_citation_graph,
)
from paper_scraper.modules.scoring.jstor_client import (
    JstorSearchResult,
    build_jstor_query,
    search_jstor,
)
from paper_scraper.modules.scoring.llm_client import sanitize_text_for_prompt
from paper_scraper.modules.scoring.token_budget import (
    DIMENSION_BUDGETS,
    DimensionTokenBudget,
    count_tokens,
    truncate_to_tokens,
)

logger = logging.getLogger(__name__)

DIMENSION_KNOWLEDGE_MAP: dict[str, list[KnowledgeType]] = {
    "novelty": [KnowledgeType.RESEARCH_FOCUS, KnowledgeType.DOMAIN_EXPERTISE],
    "ip_potential": [KnowledgeType.EVALUATION_CRITERIA, KnowledgeType.INDUSTRY_CONTEXT],
    "marketability": [KnowledgeType.INDUSTRY_CONTEXT, KnowledgeType.EVALUATION_CRITERIA],
    "feasibility": [KnowledgeType.DOMAIN_EXPERTISE, KnowledgeType.RESEARCH_FOCUS],
    "commercialization": [KnowledgeType.INDUSTRY_CONTEXT, KnowledgeType.EVALUATION_CRITERIA],
    "team_readiness": [KnowledgeType.EVALUATION_CRITERIA, KnowledgeType.DOMAIN_EXPERTISE],
}

USES_SIMILAR_PAPERS = {"novelty", "ip_potential", "feasibility", "team_readiness"}
USES_CITATION_GRAPH = {
    "novelty",
    "ip_potential",
    "marketability",
    "feasibility",
    "commercialization",
}
USES_PATENTS = {"ip_potential", "novelty"}
USES_MARKET_SIGNALS = {"marketability", "commercialization"}
USES_JSTOR_CONTEXT = {
    "novelty",
    "ip_potential",
    "marketability",
    "feasibility",
    "commercialization",
}
USES_AUTHOR_PROFILES = {"team_readiness", "ip_potential", "feasibility"}


@dataclass
class DimensionContexts:
    """Container for per-dimension context strings."""

    contexts: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, dict] = field(default_factory=dict)
    has_knowledge_context: bool = False

    def get(self, dimension: str) -> str:
        return self.contexts.get(dimension, "")


class DimensionContextBuilder:
    """Builds per-dimension context strings with token-aware budgeting."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.knowledge_service = KnowledgeService(db)
        self.paper_context_service = PaperContextService(db)

    async def build_all(
        self,
        paper: Paper,
        organization_id: UUID,
        user_id: UUID | None = None,
        similar_papers: list[Paper] | None = None,
        dimensions: list[str] | None = None,
    ) -> DimensionContexts:
        """Build context strings for all (or specified) dimensions.

        Args:
            paper: The paper being scored (ORM model).
            organization_id: Tenant ID.
            user_id: Optional user ID for personal knowledge.
            similar_papers: Similar papers from pgvector search.
            dimensions: Optional subset of dimensions to build for.

        Returns:
            DimensionContexts with per-dimension context strings.
        """
        target_dims = dimensions or list(DIMENSION_BUDGETS.keys())
        result = DimensionContexts()

        # Fetch shared data sources once
        snapshot_data = await self._get_snapshot_data(paper.id, organization_id)
        knowledge_sources = await self._get_knowledge_sources(
            organization_id, user_id, paper.keywords or []
        )
        citation_graph = await self._get_citation_graph(paper)
        jstor_result = await self._get_jstor_references(paper)
        author_profile_result = await self._get_author_profiles(paper)

        if knowledge_sources:
            result.has_knowledge_context = True

        # Store JSTOR references in metadata for later extraction by the service
        if jstor_result.papers:
            result.metadata["_jstor_references"] = [
                {
                    "title": p.title,
                    "authors": p.authors,
                    "year": p.year,
                    "doi": p.doi,
                    "journal": p.journal,
                    "jstor_url": p.jstor_url,
                }
                for p in jstor_result.papers[:8]
            ]

        # Store author profiles in metadata for later extraction by the service
        if author_profile_result.profiles:
            result.metadata["_author_profiles"] = [
                p.to_schema_dict() for p in author_profile_result.profiles
            ]

        # Build context for each dimension
        for dim_name in target_dims:
            budget = DIMENSION_BUDGETS.get(dim_name, DimensionTokenBudget())
            context_str = self._build_dimension_context(
                dimension=dim_name,
                budget=budget,
                similar_papers=similar_papers,
                citation_graph=citation_graph,
                jstor_result=jstor_result,
                author_profile_result=author_profile_result,
                snapshot_data=snapshot_data,
                knowledge_sources=knowledge_sources,
            )
            result.contexts[dim_name] = context_str
            result.metadata[dim_name] = {
                "token_count": count_tokens(context_str),
                "budget": budget.total,
                "has_citations": not citation_graph.is_empty,
                "has_jstor": not jstor_result.is_empty,
                "has_author_profiles": not author_profile_result.is_empty,
                "has_patents": bool(snapshot_data.get("patents", {}).get("data")),
                "has_market": bool(snapshot_data.get("market", {}).get("data")),
                "knowledge_sources": len(knowledge_sources),
            }

        return result

    def _build_dimension_context(
        self,
        dimension: str,
        budget: DimensionTokenBudget,
        similar_papers: list[Paper] | None,
        citation_graph: CitationGraph,
        jstor_result: JstorSearchResult,
        author_profile_result: AuthorProfileResult,
        snapshot_data: dict,
        knowledge_sources: list,
    ) -> str:
        """Build a single dimension's context string within its token budget."""
        sections: list[str] = []

        if dimension in USES_SIMILAR_PAPERS and similar_papers:
            section = self._format_similar_papers(similar_papers, dimension)
            section = truncate_to_tokens(section, budget.similar_papers)
            if section:
                sections.append(section)

        if dimension in USES_CITATION_GRAPH and not citation_graph.is_empty:
            section = self._format_citation_graph(citation_graph, dimension)
            section = truncate_to_tokens(section, budget.citation_graph)
            if section:
                sections.append(section)

        if dimension in USES_JSTOR_CONTEXT and not jstor_result.is_empty:
            section = self._format_jstor_references(jstor_result, dimension)
            section = truncate_to_tokens(section, budget.jstor)
            if section:
                sections.append(section)

        if dimension in USES_AUTHOR_PROFILES and not author_profile_result.is_empty:
            section = self._format_author_profiles(author_profile_result, dimension)
            section = truncate_to_tokens(section, budget.author_profiles)
            if section:
                sections.append(section)

        enrichment_section = self._format_enrichment(dimension, snapshot_data, budget.enrichment)
        if enrichment_section:
            sections.append(enrichment_section)

        if knowledge_sources:
            section = self._format_knowledge(dimension, knowledge_sources, budget.knowledge)
            if section:
                sections.append(section)

        combined = "\n\n".join(sections)
        if count_tokens(combined) > budget.total:
            combined = truncate_to_tokens(combined, budget.total)

        return combined

    def _format_similar_papers(
        self,
        similar_papers: list[Paper],
        dimension: str,
    ) -> str:
        if not similar_papers:
            return ""

        headers = {
            "novelty": "## Similar Papers (Novelty Comparison)",
            "ip_potential": "## Related Prior Art (Similar Papers)",
            "feasibility": "## Similar Papers (Methodology Reference)",
            "team_readiness": "## Similar Papers (Field Context)",
        }
        header = headers.get(dimension, "## Similar Papers")

        lines = [header]
        for i, p in enumerate(similar_papers[:5], 1):
            safe_title = sanitize_text_for_prompt(p.title, max_length=200)
            safe_abstract = (
                sanitize_text_for_prompt(p.abstract, max_length=200) if p.abstract else ""
            )

            entry = f"{i}. **{safe_title}**"
            if p.doi and dimension == "ip_potential":
                entry += f" [DOI: {p.doi}]"
            if safe_abstract:
                entry += f"\n   {safe_abstract}"
            if p.publication_date:
                entry += f"\n   Published: {p.publication_date}"
            lines.append(entry)

        return "\n".join(lines)

    def _format_citation_graph(
        self,
        graph: CitationGraph,
        dimension: str,
    ) -> str:
        lines: list[str] = []

        if dimension in ("novelty", "ip_potential"):
            if graph.references:
                lines.append(f"## Referenced Works ({graph.total_references} total)")
                for ref in graph.references[:8]:
                    lines.append(ref.to_context_line())

            if graph.citing_papers:
                lines.append(f"\n## Citing Papers ({graph.total_citing} total)")
                for cit in graph.citing_papers[:5]:
                    lines.append(cit.to_context_line())

        elif dimension in ("marketability", "commercialization"):
            if graph.total_citing > 0:
                lines.append("## Citation Impact")
                lines.append(f"This paper has been cited {graph.total_citing} times.")
                if graph.citing_papers:
                    lines.append("Top citing papers:")
                    for cit in graph.citing_papers[:5]:
                        lines.append(cit.to_context_line())

        elif dimension == "feasibility":
            if graph.references:
                lines.append(f"## Foundation Works Referenced ({graph.total_references} total)")
                for ref in graph.references[:5]:
                    lines.append(ref.to_context_line())

        return "\n".join(lines) if lines else ""

    def _format_jstor_references(
        self,
        jstor_result: JstorSearchResult,
        dimension: str,
    ) -> str:
        """Format JSTOR references as a context string for a dimension."""
        if not jstor_result.papers:
            return ""

        headers = {
            "novelty": "## JSTOR Library References (Novelty Comparison)",
            "ip_potential": "## JSTOR Prior Art References",
            "marketability": "## JSTOR Market & Industry References",
            "feasibility": "## JSTOR Methodology References",
            "commercialization": "## JSTOR Commercialization References",
        }
        header = headers.get(dimension, "## JSTOR Library References")

        lines = [header]
        for i, paper in enumerate(jstor_result.papers[:8], 1):
            safe_title = sanitize_text_for_prompt(paper.title, max_length=200)
            entry = f"{i}. **{safe_title}**"
            if paper.year:
                entry += f" ({paper.year})"
            if paper.journal:
                safe_journal = sanitize_text_for_prompt(paper.journal, max_length=100)
                entry += f"\n   Journal: {safe_journal}"
            if paper.abstract and dimension in ("novelty", "ip_potential", "feasibility"):
                safe_abstract = sanitize_text_for_prompt(paper.abstract, max_length=150)
                entry += f"\n   {safe_abstract}"
            if paper.doi:
                entry += f"\n   DOI: {paper.doi[:100]}"
            if paper.citation_count is not None:
                entry += f" [{paper.citation_count} citations]"
            lines.append(entry)

        return "\n".join(lines)

    def _format_enrichment(
        self,
        dimension: str,
        snapshot_data: dict,
        budget_tokens: int,
    ) -> str:
        sections = []

        if dimension in USES_PATENTS:
            patents = snapshot_data.get("patents", {}).get("data", [])
            if patents:
                patent_lines = ["## Patent Landscape"]
                for p in patents[:5]:
                    title = p.get("title", "Untitled patent")
                    pub_date = p.get("publication_date", "")
                    applicant = p.get("applicant", "")
                    line = f"- {title}"
                    if applicant:
                        line += f" (Applicant: {applicant})"
                    if pub_date:
                        line += f" [{pub_date}]"
                    patent_lines.append(line)
                sections.append("\n".join(patent_lines))

        if dimension in USES_MARKET_SIGNALS:
            market = snapshot_data.get("market", {}).get("data", [])
            if market:
                market_lines = ["## Market Signals"]
                for signal in market[:10]:
                    title = signal.get("title", signal.get("headline", ""))
                    source_name = signal.get("source", "")
                    if title:
                        line = f"- {title}"
                        if source_name:
                            line += f" (Source: {source_name})"
                        market_lines.append(line)
                sections.append("\n".join(market_lines))

        combined = "\n\n".join(sections)
        return truncate_to_tokens(combined, budget_tokens) if combined else ""

    def _format_knowledge(
        self,
        dimension: str,
        knowledge_sources: list,
        budget_tokens: int,
    ) -> str:
        relevant_types = DIMENSION_KNOWLEDGE_MAP.get(dimension, [])

        filtered = [s for s in knowledge_sources if s.type in relevant_types]
        if not filtered:
            filtered = knowledge_sources[:2]

        formatted = self.knowledge_service.format_knowledge_for_prompt(
            filtered[:3], dimension=dimension
        )

        return truncate_to_tokens(formatted, budget_tokens) if formatted else ""

    async def _get_snapshot_data(
        self,
        paper_id: UUID,
        organization_id: UUID,
    ) -> dict:
        try:
            snapshot = await self.paper_context_service.get_snapshot(
                paper_id=paper_id,
                organization_id=organization_id,
            )
            if snapshot is None:
                snapshot = await self.paper_context_service.refresh_snapshot(
                    paper_id=paper_id,
                    organization_id=organization_id,
                )
            return snapshot.context_json
        except Exception as e:
            logger.warning("Failed to get snapshot for paper %s: %s", paper_id, e)
            return {}

    async def _get_knowledge_sources(
        self,
        organization_id: UUID,
        user_id: UUID | None,
        keywords: list[str],
    ) -> list:
        try:
            return await self.knowledge_service.get_relevant_sources_for_scoring(
                organization_id=organization_id,
                user_id=user_id,
                keywords=keywords,
                limit=10,
            )
        except Exception as e:
            logger.warning("Failed to get knowledge sources: %s", e)
            return []

    async def _get_citation_graph(self, paper: Paper) -> CitationGraph:
        try:
            openalex_id = None
            if paper.source == PaperSource.OPENALEX and paper.source_id:
                openalex_id = paper.source_id
            return await fetch_citation_graph(
                paper_doi=paper.doi,
                paper_openalex_id=openalex_id,
                raw_metadata=paper.raw_metadata,
            )
        except Exception as e:
            logger.warning("Failed to fetch citation graph for paper %s: %s", paper.id, e)
            return CitationGraph(errors=[str(e)])

    async def _get_jstor_references(self, paper: Paper) -> JstorSearchResult:
        """Search JSTOR for papers related to the paper being scored."""
        try:
            query = build_jstor_query(paper.title, paper.keywords)
            return await search_jstor(query, max_results=10)
        except Exception as e:
            logger.warning("Failed to fetch JSTOR references for paper %s: %s", paper.id, e)
            return JstorSearchResult(errors=[str(e)])

    async def _get_author_profiles(self, paper: Paper) -> AuthorProfileResult:
        """Fetch GitHub and ORCID profiles for paper authors."""
        try:
            # Extract Author ORM objects from loaded PaperAuthor relationships
            paper_authors = getattr(paper, "authors", None) or []
            sorted_pas = sorted(paper_authors, key=lambda pa: pa.position)
            authors = [pa.author for pa in sorted_pas if pa.author]
            if not authors:
                return AuthorProfileResult()
            return await fetch_author_profiles(authors, max_authors=5)
        except Exception as e:
            logger.warning("Failed to fetch author profiles for paper %s: %s", paper.id, e)
            return AuthorProfileResult(errors=[str(e)])

    def _format_author_profiles(
        self,
        result: AuthorProfileResult,
        dimension: str,
    ) -> str:
        """Format author profiles as a context string for a dimension."""
        if not result.profiles:
            return ""

        headers = {
            "team_readiness": "## Author Profile Enrichment (GitHub & ORCID)",
            "ip_potential": "## Author Background (Industry & Research Experience)",
            "feasibility": "## Author Technical Depth",
        }
        header = headers.get(dimension, "## Author Profiles")

        lines = [header]
        for profile in result.profiles:
            safe_name = sanitize_text_for_prompt(profile.name, max_length=100)
            lines.append(f"\n### {safe_name}")

            if profile.orcid_data:
                o = profile.orcid_data
                if o.current_employment:
                    safe_emp = sanitize_text_for_prompt(o.current_employment, max_length=150)
                    lines.append(f"Current affiliation: {safe_emp}")
                if o.past_affiliations:
                    safe_past = [
                        sanitize_text_for_prompt(a, max_length=100) for a in o.past_affiliations[:3]
                    ]
                    lines.append(f"Past affiliations: {', '.join(safe_past)}")
                if o.education:
                    safe_edu = [
                        sanitize_text_for_prompt(e, max_length=100) for e in o.education[:2]
                    ]
                    lines.append(f"Education: {', '.join(safe_edu)}")
                if o.funding_count:
                    lines.append(f"Research grants: {o.funding_count}")
                if o.peer_review_count:
                    lines.append(f"Peer reviews: {o.peer_review_count}")
                if o.works_count:
                    lines.append(f"ORCID works: {o.works_count}")

            if profile.github:
                g = profile.github
                gh_line = f"GitHub: @{g.username}"
                gh_line += f" ({g.public_repos} repos, {g.followers} followers)"
                lines.append(gh_line)
                if g.top_languages:
                    lines.append(f"Primary languages: {', '.join(g.top_languages[:5])}")
                if g.company:
                    safe_company = sanitize_text_for_prompt(g.company, max_length=100)
                    lines.append(f"Company: {safe_company}")
                if dimension == "team_readiness" and g.popular_repos:
                    safe_repos = [
                        sanitize_text_for_prompt(r, max_length=50) for r in g.popular_repos[:3]
                    ]
                    lines.append(f"Notable repos: {', '.join(safe_repos)}")

        return "\n".join(lines)
