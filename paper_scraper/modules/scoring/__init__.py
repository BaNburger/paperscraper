"""Scoring module - AI-powered paper scoring.

This module provides:
- Multi-dimensional paper scoring (novelty, IP potential, marketability, feasibility, commercialization)
- Provider-agnostic LLM client for scoring operations
- Embedding generation for semantic similarity search
- Batch scoring via background job queue
"""

from paper_scraper.modules.scoring.dimensions import (
    BaseDimension,
    CommercializationDimension,
    DimensionResult,
    FeasibilityDimension,
    IPPotentialDimension,
    MarketabilityDimension,
    NoveltyDimension,
)
from paper_scraper.modules.scoring.embeddings import EmbeddingClient, generate_paper_embedding
from paper_scraper.modules.scoring.llm_client import (
    AnthropicClient,
    BaseLLMClient,
    OllamaClient,
    OpenAIClient,
    get_llm_client,
)
from paper_scraper.modules.scoring.context_assembler import DefaultScoreContextAssembler
from paper_scraper.modules.scoring.models import PaperScore, ScoringJob, ScoringPolicy
from paper_scraper.modules.scoring.orchestrator import (
    AggregatedScore,
    ScoringOrchestrator,
    ScoringWeights,
)
from paper_scraper.modules.scoring.service import ScoringService

__all__ = [
    # LLM Clients
    "BaseLLMClient",
    "OpenAIClient",
    "AnthropicClient",
    "OllamaClient",
    "get_llm_client",
    "DefaultScoreContextAssembler",
    # Embeddings
    "EmbeddingClient",
    "generate_paper_embedding",
    # Dimensions
    "BaseDimension",
    "DimensionResult",
    "NoveltyDimension",
    "IPPotentialDimension",
    "MarketabilityDimension",
    "FeasibilityDimension",
    "CommercializationDimension",
    # Orchestrator
    "ScoringOrchestrator",
    "ScoringWeights",
    "AggregatedScore",
    # Models
    "PaperScore",
    "ScoringJob",
    "ScoringPolicy",
    # Service
    "ScoringService",
]
