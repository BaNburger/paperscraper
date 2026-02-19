"""Embedding generation for papers and semantic search."""

from typing import Any

import httpx

from paper_scraper.core.config import settings
from paper_scraper.core.exceptions import ExternalAPIError


class EmbeddingClient:
    """Client for generating text embeddings via OpenAI API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY.get_secret_value()
        self.model = model or settings.LLM_EMBEDDING_MODEL
        self.base_url = "https://api.openai.com/v1"

    async def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding vector for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (1536 dimensions for text-embedding-3-small)
        """
        embeddings = await self.embed_texts([text])
        return embeddings[0]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embedding vectors for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Truncate texts to max token limit (approximately)
        # text-embedding-3-small has 8191 token limit
        max_chars = 30000  # Rough estimate, safe limit
        truncated_texts = [text[:max_chars] if len(text) > max_chars else text for text in texts]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "input": truncated_texts,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                raise ExternalAPIError(
                    service="OpenAI Embeddings",
                    message=response.text,
                    status_code=response.status_code,
                )

            data = response.json()
            # Sort by index to ensure correct order
            sorted_data = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in sorted_data]


async def generate_paper_embedding(
    title: str,
    abstract: str | None = None,
    keywords: list[str] | None = None,
) -> list[float]:
    """
    Generate embedding for a paper based on its metadata.

    Combines title, abstract, and keywords into a single text for embedding.

    Args:
        title: Paper title
        abstract: Paper abstract (optional)
        keywords: Paper keywords (optional)

    Returns:
        Embedding vector (1536 dimensions)
    """
    parts = [f"Title: {title}"]

    if abstract:
        parts.append(f"Abstract: {abstract}")

    if keywords:
        parts.append(f"Keywords: {', '.join(keywords)}")

    text = "\n\n".join(parts)

    client = EmbeddingClient()
    return await client.embed_text(text)
