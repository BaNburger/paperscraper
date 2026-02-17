"""Zotero connector adapter for outbound and inbound synchronization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx


@dataclass
class ZoteroCredentials:
    """Connection credentials for Zotero API."""

    user_id: str
    api_key: str
    base_url: str = "https://api.zotero.org"
    library_type: str = "users"


class ZoteroConnector:
    """HTTP adapter for Zotero API."""

    API_VERSION = "3"

    async def verify_connection(self, creds: ZoteroCredentials) -> None:
        """Validate API credentials by listing one collection."""
        endpoint = f"{creds.base_url.rstrip('/')}/{creds.library_type}/{creds.user_id}/collections"
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.get(endpoint, headers=self._headers(creds), params={"limit": 1})
            response.raise_for_status()

    async def upsert_item(
        self,
        creds: ZoteroCredentials,
        item_payload: dict[str, Any],
        zotero_item_key: str | None = None,
    ) -> dict[str, Any]:
        """Create or update a Zotero item."""
        base = f"{creds.base_url.rstrip('/')}/{creds.library_type}/{creds.user_id}/items"
        async with httpx.AsyncClient(timeout=20.0) as client:
            if zotero_item_key:
                endpoint = f"{base}/{zotero_item_key}"
                response = await client.patch(
                    endpoint,
                    headers=self._headers(creds),
                    json=item_payload,
                )
                response.raise_for_status()
                return {"item_key": zotero_item_key}

            response = await client.post(
                base,
                headers=self._headers(creds),
                json=[item_payload],
            )
            response.raise_for_status()
            payload = response.json() if response.content else {}
            successful = payload.get("successful", {}) if isinstance(payload, dict) else {}
            key = None
            if isinstance(successful, dict):
                first = successful.get("0") or successful.get(0)
                if isinstance(first, dict):
                    key = first.get("key")
            return {"item_key": key}

    async def list_items(
        self,
        creds: ZoteroCredentials,
        *,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch recent items from Zotero library."""
        endpoint = f"{creds.base_url.rstrip('/')}/{creds.library_type}/{creds.user_id}/items"
        params: dict[str, Any] = {
            "limit": max(1, min(limit, 100)),
            "sort": "dateModified",
            "direction": "desc",
            "format": "json",
        }
        if since:
            params["since"] = int(since.timestamp())

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(endpoint, headers=self._headers(creds), params=params)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
            return []

    async def get_item(
        self,
        creds: ZoteroCredentials,
        item_key: str,
    ) -> dict[str, Any] | None:
        """Fetch a single Zotero item by key."""
        endpoint = (
            f"{creds.base_url.rstrip('/')}/{creds.library_type}/{creds.user_id}/items/{item_key}"
        )
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(endpoint, headers=self._headers(creds))
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, dict) else None

    def build_item_payload(
        self,
        *,
        title: str,
        abstract: str | None,
        doi: str | None,
        journal: str | None,
        publication_date: datetime | None,
        authors: list[str],
        tags: list[str],
        url: str | None = None,
    ) -> dict[str, Any]:
        """Build a Zotero journalArticle payload from local paper data."""
        creators = []
        for author_name in authors:
            parts = author_name.split()
            first_name = " ".join(parts[:-1]) if len(parts) > 1 else ""
            last_name = parts[-1] if parts else author_name
            creators.append(
                {
                    "creatorType": "author",
                    "firstName": first_name,
                    "lastName": last_name,
                }
            )

        return {
            "itemType": "journalArticle",
            "title": title,
            "abstractNote": abstract or "",
            "DOI": doi or "",
            "publicationTitle": journal or "",
            "date": publication_date.date().isoformat() if publication_date else "",
            "url": url or (f"https://doi.org/{doi}" if doi else ""),
            "creators": creators,
            "tags": [{"tag": tag} for tag in tags],
        }

    def _headers(self, creds: ZoteroCredentials) -> dict[str, str]:
        """Construct Zotero API headers."""
        return {
            "Zotero-API-Key": creds.api_key,
            "Zotero-API-Version": self.API_VERSION,
            "Content-Type": "application/json",
        }
