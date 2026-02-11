"""Baseline market feed connector (API/CSV/static config)."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class MarketFeedConnector:
    """Connector for loading market signals from lightweight feeds."""

    async def fetch_signals(
        self,
        config: dict[str, Any],
        keywords: list[str],
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Fetch and rank market signals from configured source."""
        signals = await self._load_raw_signals(config)
        if not signals:
            return []

        keyword_set = {k.lower() for k in keywords if k}
        scored: list[tuple[int, dict[str, Any]]] = []
        for signal in signals:
            haystack = " ".join(
                [
                    str(signal.get("title", "")),
                    str(signal.get("summary", "")),
                    " ".join(str(t) for t in signal.get("tags", [])),
                ]
            ).lower()
            score = sum(1 for keyword in keyword_set if keyword in haystack)
            scored.append((score, signal))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [signal for _, signal in scored[:limit]]

    async def _load_raw_signals(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        """Load raw signals from static config, CSV, or JSON API."""
        if isinstance(config.get("signals"), list):
            return [s for s in config["signals"] if isinstance(s, dict)]

        csv_path = config.get("csv_path")
        if csv_path:
            return self._load_csv(Path(csv_path))

        api_url = config.get("api_url")
        if api_url:
            return await self._load_api(api_url)

        return []

    def _load_csv(self, path: Path) -> list[dict[str, Any]]:
        """Load signals from CSV path."""
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))
        return rows

    async def _load_api(self, url: str) -> list[dict[str, Any]]:
        """Load signals from a JSON API endpoint."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                response.raise_for_status()
        except Exception as e:
            logger.warning("Failed to load market signals from %s: %s", url, e)
            return []

        payload = response.json()
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
        if isinstance(payload, dict) and isinstance(payload.get("items"), list):
            return [row for row in payload["items"] if isinstance(row, dict)]
        return []
