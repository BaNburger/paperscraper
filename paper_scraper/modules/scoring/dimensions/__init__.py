"""Scoring dimension implementations."""

from paper_scraper.modules.scoring.dimensions.base import BaseDimension, DimensionResult
from paper_scraper.modules.scoring.dimensions.commercialization import (
    CommercializationDimension,
)
from paper_scraper.modules.scoring.dimensions.feasibility import FeasibilityDimension
from paper_scraper.modules.scoring.dimensions.ip_potential import IPPotentialDimension
from paper_scraper.modules.scoring.dimensions.marketability import MarketabilityDimension
from paper_scraper.modules.scoring.dimensions.novelty import NoveltyDimension

__all__ = [
    "BaseDimension",
    "DimensionResult",
    "NoveltyDimension",
    "IPPotentialDimension",
    "MarketabilityDimension",
    "FeasibilityDimension",
    "CommercializationDimension",
]
