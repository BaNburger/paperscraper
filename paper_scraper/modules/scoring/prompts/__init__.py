"""Jinja2 prompt templates for scoring dimensions with sanitization."""

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from paper_scraper.modules.scoring.llm_client import sanitize_text_for_prompt

# Set up Jinja2 environment with prompts directory
PROMPTS_DIR = Path(__file__).parent
jinja_env = Environment(
    loader=FileSystemLoader(PROMPTS_DIR),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)


# =============================================================================
# Prompt Length Constants
# =============================================================================

# Maximum characters for main abstract (roughly 500 tokens)
MAX_ABSTRACT_LENGTH = 2000

# Maximum characters for similar paper abstracts
MAX_SIMILAR_ABSTRACT_LENGTH = 300

# Maximum number of similar papers to include
MAX_SIMILAR_PAPERS = 5


# =============================================================================
# Sanitized Paper Context for Prompts
# =============================================================================


@dataclass
class SanitizedPaperContext:
    """Sanitized paper context safe for prompt inclusion."""

    id: str
    title: str
    abstract: str
    keywords: list[str]
    journal: str
    publication_date: str
    doi: str
    citations_count: int | None
    references_count: int | None

    @classmethod
    def from_paper_context(cls, paper, max_abstract_length: int = MAX_ABSTRACT_LENGTH):
        """Create sanitized context from PaperContext."""
        return cls(
            id=str(paper.id),
            title=sanitize_text_for_prompt(paper.title, max_length=500),
            abstract=sanitize_text_for_prompt(paper.abstract, max_length=max_abstract_length),
            keywords=[sanitize_text_for_prompt(k, max_length=100) for k in (paper.keywords or [])[:10]],
            journal=sanitize_text_for_prompt(paper.journal, max_length=200) if paper.journal else "",
            publication_date=str(paper.publication_date) if paper.publication_date else "",
            doi=str(paper.doi) if paper.doi else "",
            citations_count=paper.citations_count,
            references_count=paper.references_count,
        )


def render_prompt(template_name: str, **kwargs) -> str:
    """
    Render a prompt template with given variables.

    Automatically sanitizes paper content to prevent prompt injection.

    Args:
        template_name: Name of the template file (e.g., "novelty.jinja2")
        **kwargs: Variables to pass to the template

    Returns:
        Rendered prompt string
    """
    # Sanitize paper context if provided
    if "paper" in kwargs and kwargs["paper"] is not None:
        kwargs["paper"] = SanitizedPaperContext.from_paper_context(kwargs["paper"])

    # Sanitize similar papers if provided
    if "similar_papers" in kwargs and kwargs["similar_papers"]:
        sanitized_similar = []
        for p in kwargs["similar_papers"][:MAX_SIMILAR_PAPERS]:
            sanitized_similar.append(
                SanitizedPaperContext.from_paper_context(
                    p, max_abstract_length=MAX_SIMILAR_ABSTRACT_LENGTH
                )
            )
        kwargs["similar_papers"] = sanitized_similar

    template = jinja_env.get_template(template_name)
    return template.render(**kwargs)
