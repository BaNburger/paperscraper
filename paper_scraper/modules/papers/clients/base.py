"""Base class for external API clients."""

from abc import ABC, abstractmethod

import httpx


class BaseAPIClient(ABC):
    """Abstract base class for external API clients."""

    def __init__(self, timeout: float = 30.0):
        """Initialize client with configurable timeout.

        Args:
            timeout: Request timeout in seconds.
        """
        self.client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close client."""
        await self.client.aclose()

    @abstractmethod
    async def search(self, query: str, max_results: int = 100) -> list[dict]:
        """Search for papers.

        Args:
            query: Search query string.
            max_results: Maximum number of results to return.

        Returns:
            List of normalized paper dictionaries.
        """
        pass

    @abstractmethod
    async def get_by_id(self, identifier: str) -> dict | None:
        """Get paper by identifier.

        Args:
            identifier: Paper identifier (DOI, ID, etc.).

        Returns:
            Normalized paper dict or None if not found.
        """
        pass

    @abstractmethod
    def normalize(self, raw_data: dict) -> dict:
        """Normalize API response to standard paper format.

        Args:
            raw_data: Raw API response data.

        Returns:
            Normalized paper dictionary with standard fields.
        """
        pass
