"""Token-aware budget management for scoring context assembly."""

import logging
from dataclasses import dataclass

import tiktoken

logger = logging.getLogger(__name__)

# cl100k_base is used by GPT-4, GPT-4o, GPT-5 mini — the default models
ENCODING_NAME = "cl100k_base"

_encoding: tiktoken.Encoding | None = None


def get_encoding() -> tiktoken.Encoding:
    """Get cached tiktoken encoding instance."""
    global _encoding
    if _encoding is None:
        _encoding = tiktoken.get_encoding(ENCODING_NAME)
    return _encoding


def count_tokens(text: str) -> int:
    """Count tokens in a text string.

    Args:
        text: Text to count tokens for.

    Returns:
        Token count.
    """
    if not text:
        return 0
    try:
        return len(get_encoding().encode(text))
    except Exception:
        return len(text) // 4


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text to fit within a token budget.

    Args:
        text: Text to truncate.
        max_tokens: Maximum number of tokens.

    Returns:
        Truncated text that fits within the token budget.
    """
    if not text or max_tokens <= 0:
        return ""
    try:
        enc = get_encoding()
        tokens = enc.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return enc.decode(tokens[:max_tokens])
    except Exception:
        char_limit = max_tokens * 4
        return text[:char_limit]


@dataclass
class DimensionTokenBudget:
    """Token budget allocation for a single dimension's context."""

    total: int = 2400
    similar_papers: int = 800
    citation_graph: int = 600
    enrichment: int = 400
    knowledge: int = 200
    jstor: int = 400


# Per-dimension budget allocations — different dimensions prioritize
# different context types based on their scoring criteria.
DIMENSION_BUDGETS: dict[str, DimensionTokenBudget] = {
    "novelty": DimensionTokenBudget(
        total=2500,
        similar_papers=800,
        citation_graph=700,
        enrichment=200,
        knowledge=300,
        jstor=500,
    ),
    "ip_potential": DimensionTokenBudget(
        total=2400,
        similar_papers=400,
        citation_graph=500,
        enrichment=800,
        knowledge=300,
        jstor=400,
    ),
    "marketability": DimensionTokenBudget(
        total=2300,
        similar_papers=200,
        citation_graph=300,
        enrichment=1100,
        knowledge=400,
        jstor=300,
    ),
    "feasibility": DimensionTokenBudget(
        total=2400,
        similar_papers=700,
        citation_graph=400,
        enrichment=500,
        knowledge=400,
        jstor=400,
    ),
    "commercialization": DimensionTokenBudget(
        total=2200,
        similar_papers=200,
        citation_graph=300,
        enrichment=1100,
        knowledge=400,
        jstor=200,
    ),
    "team_readiness": DimensionTokenBudget(
        total=2200,
        similar_papers=400,
        citation_graph=300,
        enrichment=400,
        knowledge=900,
        jstor=200,
    ),
}
