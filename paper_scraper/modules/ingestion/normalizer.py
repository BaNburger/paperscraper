"""Default normalization implementation for ingestion records."""

from __future__ import annotations

from typing import Any

from paper_scraper.modules.ingestion.interfaces import (
    NormalizedAuthor,
    NormalizedPaperBundle,
    Normalizer,
)


class DefaultPaperNormalizer(Normalizer):
    """Normalize connector payloads into canonical paper bundles."""

    def normalize(self, record: dict[str, Any]) -> NormalizedPaperBundle:
        source = str(record.get("source") or "unknown")
        source_record_id = str(
            record.get("source_id")
            or record.get("id")
            or record.get("doi")
            or record.get("title")
            or ""
        ).strip()
        if not source_record_id:
            raise ValueError("source_record_id could not be derived from record")

        authors: list[NormalizedAuthor] = []
        for author in record.get("authors", []):
            if not isinstance(author, dict):
                continue
            source_ids: dict[str, str] = {}
            for key in ("openalex_id", "semantic_scholar_id", "orcid"):
                value = author.get(key)
                if value:
                    source_ids[key] = str(value)

            affiliations = author.get("affiliations")
            if not isinstance(affiliations, list):
                affiliations = []

            authors.append(
                NormalizedAuthor(
                    name=str(author.get("name") or "Unknown"),
                    orcid=author.get("orcid"),
                    source_ids=source_ids,
                    affiliations=[str(item) for item in affiliations if item],
                )
            )

        metadata = {
            "source_id": record.get("source_id"),
            "raw_metadata": record.get("raw_metadata", {}),
            "journal": record.get("journal"),
            "volume": record.get("volume"),
            "issue": record.get("issue"),
            "pages": record.get("pages"),
            "keywords": record.get("keywords", []),
            "mesh_terms": record.get("mesh_terms", []),
            "references_count": record.get("references_count"),
            "citations_count": record.get("citations_count"),
        }

        return NormalizedPaperBundle(
            source=source,
            source_record_id=source_record_id,
            title=str(record.get("title") or "Untitled"),
            abstract=record.get("abstract"),
            publication_date=record.get("publication_date"),
            doi=record.get("doi"),
            metadata=metadata,
            authors=authors,
        )
