"""Shared filter builders for ingestion pipeline orchestrators."""

from __future__ import annotations

from typing import Any


def extract_openalex_short_id(value: str) -> str:
    """Extract compact OpenAlex ID from URL-like values."""
    normalized = value.strip()
    if "/" in normalized:
        return normalized.rsplit("/", 1)[-1]
    return normalized


def build_openalex_entity_filters(
    *,
    institution_id: str | None,
    author_id: str | None,
) -> dict[str, str]:
    """Build OpenAlex filter map for institution/author scoped sync."""
    filters: dict[str, str] = {}
    if institution_id:
        short_id = extract_openalex_short_id(institution_id)
        if short_id:
            filters["institutions.id"] = short_id
            return filters
    if author_id:
        short_id = extract_openalex_short_id(author_id)
        if short_id:
            filters["authorships.author.id"] = short_id
    return filters


def build_repository_pipeline_filters(
    *,
    provider: str,
    config: dict[str, Any] | Any,
    query: str,
) -> dict[str, Any]:
    """Map repository source config into canonical ingestion connector filters."""
    filters: dict[str, Any] = {"query": query}
    source_filters = config.get("filters") if isinstance(config, dict) else None

    if provider in {"openalex", "crossref"}:
        if isinstance(source_filters, dict) and source_filters:
            filters["filters"] = source_filters

    if provider == "arxiv":
        category = source_filters.get("category") if isinstance(source_filters, dict) else None
        if category:
            filters["category"] = category

    if provider == "semantic_scholar" and isinstance(source_filters, dict):
        year = source_filters.get("year")
        if year is not None:
            filters["year"] = year
        fields_of_study = source_filters.get("fields_of_study")
        if fields_of_study is not None:
            filters["fields_of_study"] = fields_of_study

    return filters
