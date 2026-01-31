"""Provider-agnostic LLM client abstraction with Langfuse observability."""

import json
from abc import ABC, abstractmethod
from typing import Any

import httpx
from langfuse import Langfuse
from langfuse.decorators import observe

from paper_scraper.core.config import settings
from paper_scraper.core.exceptions import ExternalAPIError

# Initialize Langfuse client (disabled if no public key configured)
langfuse = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY.get_secret_value()
    if settings.LANGFUSE_SECRET_KEY
    else None,
    host=settings.LANGFUSE_HOST,
    enabled=bool(settings.LANGFUSE_PUBLIC_KEY),
)


class BaseLLMClient(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> str:
        """
        Generate a completion from the LLM.

        Args:
            prompt: The user prompt/query
            system: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            json_mode: If True, request JSON output

        Returns:
            The LLM response text
        """
        pass

    @abstractmethod
    async def complete_json(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """
        Generate a JSON completion from the LLM.

        Args:
            prompt: The user prompt/query
            system: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response

        Returns:
            Parsed JSON response as dict
        """
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI API client with Langfuse observability."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        org_id: str | None = None,
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY.get_secret_value()
        self.model = model or settings.LLM_MODEL
        self.org_id = org_id or settings.OPENAI_ORG_ID
        self.base_url = "https://api.openai.com/v1"

    @observe(as_type="generation", name="openai-completion")
    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> str:
        """Generate completion using OpenAI API, tracked by Langfuse."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.org_id:
            headers["OpenAI-Organization"] = self.org_id

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or settings.LLM_TEMPERATURE,
            "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                raise ExternalAPIError(
                    service="OpenAI",
                    message=response.text,
                    status_code=response.status_code,
                )

            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def complete_json(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Generate JSON completion using OpenAI API."""
        response = await self.complete(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise ExternalAPIError(
                service="OpenAI",
                message=f"Failed to parse JSON response: {e}",
                details={"response": response},
            )


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client with Langfuse observability."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or (
            settings.ANTHROPIC_API_KEY.get_secret_value()
            if settings.ANTHROPIC_API_KEY
            else ""
        )
        self.model = model or "claude-sonnet-4-20250514"
        self.base_url = "https://api.anthropic.com/v1"

    @observe(as_type="generation", name="anthropic-completion")
    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> str:
        """Generate completion using Anthropic API, tracked by Langfuse."""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system:
            payload["system"] = system
        if temperature is not None:
            payload["temperature"] = temperature

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                raise ExternalAPIError(
                    service="Anthropic",
                    message=response.text,
                    status_code=response.status_code,
                )

            data = response.json()
            return data["content"][0]["text"]

    async def complete_json(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Generate JSON completion using Anthropic API."""
        # Anthropic doesn't have native JSON mode, so we instruct via prompt
        json_system = system or ""
        json_system += "\n\nYou MUST respond with valid JSON only. No other text."

        response = await self.complete(
            prompt=prompt,
            system=json_system,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Try to extract JSON from response
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise ExternalAPIError(
                service="Anthropic",
                message=f"Failed to parse JSON response: {e}",
                details={"response": response},
            )


class OllamaClient(BaseLLMClient):
    """Ollama local LLM client with Langfuse observability."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.LLM_MODEL

    @observe(as_type="generation", name="ollama-completion")
    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> str:
        """Generate completion using Ollama API, tracked by Langfuse."""
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        if system:
            payload["system"] = system
        if temperature is not None:
            payload["options"] = payload.get("options", {})
            payload["options"]["temperature"] = temperature
        if max_tokens:
            payload["options"] = payload.get("options", {})
            payload["options"]["num_predict"] = max_tokens
        if json_mode:
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )

            if response.status_code != 200:
                raise ExternalAPIError(
                    service="Ollama",
                    message=response.text,
                    status_code=response.status_code,
                )

            data = response.json()
            return data["response"]

    async def complete_json(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Generate JSON completion using Ollama API."""
        response = await self.complete(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise ExternalAPIError(
                service="Ollama",
                message=f"Failed to parse JSON response: {e}",
                details={"response": response},
            )


def get_llm_client(provider: str | None = None) -> BaseLLMClient:
    """
    Factory function to get LLM client based on provider setting.

    Args:
        provider: Override provider (openai, anthropic, ollama, azure)

    Returns:
        Configured LLM client instance
    """
    provider = provider or settings.LLM_PROVIDER

    if provider == "openai":
        return OpenAIClient()
    elif provider == "anthropic":
        return AnthropicClient()
    elif provider == "ollama":
        return OllamaClient()
    elif provider == "azure":
        # Azure uses OpenAI-compatible API with different endpoint
        return OpenAIClient(
            api_key=settings.AZURE_OPENAI_API_KEY.get_secret_value()
            if settings.AZURE_OPENAI_API_KEY
            else "",
            model=settings.AZURE_OPENAI_DEPLOYMENT or settings.LLM_MODEL,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
