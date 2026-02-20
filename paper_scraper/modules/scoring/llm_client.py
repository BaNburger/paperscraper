"""Provider-agnostic LLM client abstraction with Langfuse observability."""

import asyncio
import json
import logging
import re
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import httpx
from langfuse import Langfuse
from langfuse.decorators import observe

from paper_scraper.core.config import settings
from paper_scraper.core.exceptions import ExternalAPIError

logger = logging.getLogger(__name__)

# Initialize Langfuse client (disabled if no public key configured)
langfuse = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY.get_secret_value()
    if settings.LANGFUSE_SECRET_KEY
    else None,
    host=settings.LANGFUSE_HOST,
    enabled=bool(settings.LANGFUSE_PUBLIC_KEY),
)


# =============================================================================
# Token Usage Tracking
# =============================================================================


@dataclass
class TokenUsage:
    """Token usage statistics from LLM response."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str

    @property
    def estimated_cost_usd(self) -> float:
        """Estimate cost in USD based on model pricing (approximate)."""
        # Pricing per 1M tokens (approximate, as of 2026)
        pricing = {
            "gpt-5-mini": {"input": 0.15, "output": 0.60},
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
            "claude-3-haiku": {"input": 0.25, "output": 1.25},
            "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
            "gemini-2.0-pro": {"input": 1.25, "output": 5.00},
            # AWS Bedrock models
            "amazon.nova-micro-v1:0": {"input": 0.035, "output": 0.14},
            "amazon.nova-lite-v1:0": {"input": 0.06, "output": 0.24},
            "amazon.nova-pro-v1:0": {"input": 0.80, "output": 3.20},
            "anthropic.claude-3-5-haiku-20241022-v1:0": {"input": 0.80, "output": 4.00},
            "anthropic.claude-3-5-sonnet-20241022-v2:0": {"input": 3.00, "output": 15.00},
        }
        model_pricing = pricing.get(self.model, {"input": 1.0, "output": 3.0})
        return (
            self.prompt_tokens * model_pricing["input"] / 1_000_000
            + self.completion_tokens * model_pricing["output"] / 1_000_000
        )


@dataclass
class LLMResponse:
    """LLM response with content and metadata."""

    content: str
    usage: TokenUsage | None = None


# =============================================================================
# Retry Configuration
# =============================================================================

# HTTP status codes that are retryable
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# Maximum retries for transient failures
MAX_RETRIES = 3

# Base delay for exponential backoff (seconds)
BASE_RETRY_DELAY = 1.0

# Maximum delay between retries (seconds)
MAX_RETRY_DELAY = 30.0


async def retry_with_backoff(
    func,
    max_retries: int = MAX_RETRIES,
    base_delay: float = BASE_RETRY_DELAY,
    max_delay: float = MAX_RETRY_DELAY,
    retryable_errors: tuple = (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException),
):
    """
    Execute a function with exponential backoff retry logic.

    Args:
        func: Async function to execute
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        retryable_errors: Tuple of exception types to retry

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func()
        except retryable_errors as e:
            last_exception = e

            # Check if it's an HTTP error with retryable status
            if isinstance(e, httpx.HTTPStatusError):
                if e.response.status_code not in RETRYABLE_STATUS_CODES:
                    raise  # Non-retryable HTTP error

            if attempt < max_retries:
                # Calculate delay with exponential backoff and jitter
                delay = min(base_delay * (2**attempt), max_delay)
                jitter = delay * 0.1 * (0.5 - asyncio.get_event_loop().time() % 1)
                actual_delay = delay + jitter

                logger.warning(
                    f"LLM request failed (attempt {attempt + 1}/{max_retries + 1}), "
                    f"retrying in {actual_delay:.2f}s: {type(e).__name__}: {e}"
                )
                await asyncio.sleep(actual_delay)
            else:
                logger.error(f"LLM request failed after {max_retries + 1} attempts: {e}")

    raise last_exception  # type: ignore


# =============================================================================
# Prompt Sanitization
# =============================================================================


def sanitize_text_for_prompt(text: str | None, max_length: int = 2000) -> str:
    """
    Sanitize text for safe inclusion in LLM prompts.

    Prevents prompt injection by:
    - Escaping special control sequences
    - Removing potential instruction overrides
    - Truncating to max length

    Args:
        text: Text to sanitize
        max_length: Maximum character length

    Returns:
        Sanitized text safe for prompt inclusion
    """
    if not text:
        return ""

    # Remove potential prompt injection patterns
    dangerous_patterns = [
        r"(?i)ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|context)",
        r"(?i)disregard\s+(all\s+)?(previous|above|prior)",
        r"(?i)new\s+instructions?:",
        r"(?i)system\s*prompt\s*override",
        r"(?i)you\s+are\s+now\s+a",
        r"(?i)forget\s+(everything|all)",
        r"(?i)<\s*/?system\s*>",
        r"(?i)\[INST\]",
        r"(?i)\[/INST\]",
        r"```.*?system.*?```",
    ]

    sanitized = text
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, "[REDACTED]", sanitized)

    # Escape any remaining special characters that might be interpreted
    # Remove null bytes and other control characters (except newlines/tabs)
    sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", sanitized)

    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."

    return sanitized


# =============================================================================
# Shared HTTP Client Manager
# =============================================================================


class HTTPClientManager:
    """Manages shared HTTP clients for connection pooling."""

    _clients: dict[str, httpx.AsyncClient] = {}

    @classmethod
    @asynccontextmanager
    async def get_client(cls, base_url: str, timeout: float = 120.0):
        """
        Get or create a shared HTTP client for the given base URL.

        Args:
            base_url: Base URL for the API
            timeout: Request timeout in seconds

        Yields:
            Shared AsyncClient instance
        """
        if base_url not in cls._clients:
            cls._clients[base_url] = httpx.AsyncClient(
                timeout=timeout,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        yield cls._clients[base_url]

    @classmethod
    async def close_all(cls):
        """Close all HTTP clients."""
        for client in cls._clients.values():
            await client.aclose()
        cls._clients.clear()


# =============================================================================
# Base LLM Client
# =============================================================================


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
    async def complete_with_usage(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """
        Generate a completion with token usage tracking.

        Args:
            prompt: The user prompt/query
            system: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            json_mode: If True, request JSON output

        Returns:
            LLMResponse with content and usage statistics
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


# =============================================================================
# OpenAI Client
# =============================================================================


class OpenAIClient(BaseLLMClient):
    """OpenAI API client with Langfuse observability and retry logic."""

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
        response = await self.complete_with_usage(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )
        return response.content

    async def complete_with_usage(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Generate completion with token usage tracking."""
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
            "temperature": temperature if temperature is not None else settings.LLM_TEMPERATURE,
            "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        async def make_request():
            async with HTTPClientManager.get_client(self.base_url) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                return response.json()

        try:
            data = await retry_with_backoff(make_request)
        except httpx.HTTPStatusError as e:
            raise ExternalAPIError(
                service="OpenAI",
                message=e.response.text,
                status_code=e.response.status_code,
            ) from e

        # Extract content and usage
        content = data["choices"][0]["message"]["content"]
        usage = None
        if "usage" in data:
            usage = TokenUsage(
                prompt_tokens=data["usage"]["prompt_tokens"],
                completion_tokens=data["usage"]["completion_tokens"],
                total_tokens=data["usage"]["total_tokens"],
                model=self.model,
            )
            logger.info(
                f"OpenAI request completed: {usage.total_tokens} tokens, "
                f"~${usage.estimated_cost_usd:.6f}"
            )

        return LLMResponse(content=content, usage=usage)

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
            ) from e


# =============================================================================
# Anthropic Client
# =============================================================================


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client with Langfuse observability and retry logic."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or (
            settings.ANTHROPIC_API_KEY.get_secret_value() if settings.ANTHROPIC_API_KEY else ""
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
        response = await self.complete_with_usage(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )
        return response.content

    async def complete_with_usage(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Generate completion with token usage tracking."""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        actual_system = system
        if json_mode:
            actual_system = (
                system or ""
            ) + "\n\nYou MUST respond with valid JSON only. No other text."

        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }

        if actual_system:
            payload["system"] = actual_system
        if temperature is not None:
            payload["temperature"] = temperature

        async def make_request():
            async with HTTPClientManager.get_client(self.base_url) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                return response.json()

        try:
            data = await retry_with_backoff(make_request)
        except httpx.HTTPStatusError as e:
            raise ExternalAPIError(
                service="Anthropic",
                message=e.response.text,
                status_code=e.response.status_code,
            ) from e

        content = data["content"][0]["text"]
        usage = None
        if "usage" in data:
            usage = TokenUsage(
                prompt_tokens=data["usage"]["input_tokens"],
                completion_tokens=data["usage"]["output_tokens"],
                total_tokens=data["usage"]["input_tokens"] + data["usage"]["output_tokens"],
                model=self.model,
            )
            logger.info(
                f"Anthropic request completed: {usage.total_tokens} tokens, "
                f"~${usage.estimated_cost_usd:.6f}"
            )

        return LLMResponse(content=content, usage=usage)

    async def complete_json(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Generate JSON completion using Anthropic API."""
        response = await self.complete(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
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
            ) from e


# =============================================================================
# Azure OpenAI Client
# =============================================================================


class AzureOpenAIClient(BaseLLMClient):
    """Azure OpenAI API client with Langfuse observability and retry logic."""

    def __init__(
        self,
        api_key: str | None = None,
        deployment: str | None = None,
        endpoint: str | None = None,
        api_version: str | None = None,
    ):
        self.api_key = api_key or (
            settings.AZURE_OPENAI_API_KEY.get_secret_value()
            if settings.AZURE_OPENAI_API_KEY
            else ""
        )
        self.deployment = deployment or settings.AZURE_OPENAI_DEPLOYMENT or settings.LLM_MODEL
        self.endpoint = endpoint or settings.AZURE_OPENAI_ENDPOINT or ""
        self.api_version = api_version or settings.AZURE_OPENAI_API_VERSION
        self.base_url = f"{self.endpoint.rstrip('/')}/openai/deployments/{self.deployment}"

    @observe(as_type="generation", name="azure-openai-completion")
    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> str:
        """Generate completion using Azure OpenAI API, tracked by Langfuse."""
        response = await self.complete_with_usage(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )
        return response.content

    async def complete_with_usage(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Generate completion with token usage tracking."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "messages": messages,
            "temperature": temperature if temperature is not None else settings.LLM_TEMPERATURE,
            "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        async def make_request():
            async with HTTPClientManager.get_client(self.endpoint) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions?api-version={self.api_version}",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                return response.json()

        try:
            data = await retry_with_backoff(make_request)
        except httpx.HTTPStatusError as e:
            raise ExternalAPIError(
                service="Azure OpenAI",
                message=e.response.text,
                status_code=e.response.status_code,
            ) from e

        content = data["choices"][0]["message"]["content"]
        usage = None
        if "usage" in data:
            usage = TokenUsage(
                prompt_tokens=data["usage"]["prompt_tokens"],
                completion_tokens=data["usage"]["completion_tokens"],
                total_tokens=data["usage"]["total_tokens"],
                model=self.deployment,
            )
            logger.info(
                f"Azure OpenAI request completed: {usage.total_tokens} tokens, "
                f"~${usage.estimated_cost_usd:.6f}"
            )

        return LLMResponse(content=content, usage=usage)

    async def complete_json(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Generate JSON completion using Azure OpenAI API."""
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
                service="Azure OpenAI",
                message=f"Failed to parse JSON response: {e}",
                details={"response": response},
            ) from e


# =============================================================================
# Ollama Client
# =============================================================================


class OllamaClient(BaseLLMClient):
    """Ollama local LLM client with Langfuse observability and retry logic."""

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
        response = await self.complete_with_usage(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )
        return response.content

    async def complete_with_usage(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Generate completion with token usage tracking."""
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

        async def make_request():
            async with HTTPClientManager.get_client(self.base_url, timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                return response.json()

        try:
            data = await retry_with_backoff(make_request)
        except httpx.HTTPStatusError as e:
            raise ExternalAPIError(
                service="Ollama",
                message=e.response.text,
                status_code=e.response.status_code,
            ) from e

        content = data["response"]
        usage = None
        # Ollama provides token counts in different fields
        if "prompt_eval_count" in data or "eval_count" in data:
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)
            usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                model=self.model,
            )
            logger.info(f"Ollama request completed: {usage.total_tokens} tokens")

        return LLMResponse(content=content, usage=usage)

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
            ) from e


# =============================================================================
# Google Gemini Client
# =============================================================================


class GeminiClient(BaseLLMClient):
    """Google Gemini API client with Langfuse observability and retry logic."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or (
            settings.GOOGLE_API_KEY.get_secret_value() if settings.GOOGLE_API_KEY else ""
        )
        self.model = model or "gemini-2.0-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    @observe(as_type="generation", name="gemini-completion")
    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> str:
        """Generate completion using Gemini API, tracked by Langfuse."""
        response = await self.complete_with_usage(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )
        return response.content

    async def complete_with_usage(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Generate completion with token usage tracking."""
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {},
        }

        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        gen_config = payload["generationConfig"]
        if temperature is not None:
            gen_config["temperature"] = temperature
        else:
            gen_config["temperature"] = settings.LLM_TEMPERATURE
        if max_tokens:
            gen_config["maxOutputTokens"] = max_tokens
        else:
            gen_config["maxOutputTokens"] = settings.LLM_MAX_TOKENS

        if json_mode:
            gen_config["responseMimeType"] = "application/json"

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        async def make_request():
            async with HTTPClientManager.get_client(self.base_url) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                return response.json()

        try:
            data = await retry_with_backoff(make_request)
        except httpx.HTTPStatusError as e:
            raise ExternalAPIError(
                service="Google Gemini",
                message=e.response.text,
                status_code=e.response.status_code,
            ) from e

        # Extract content from response
        candidates = data.get("candidates", [])
        if not candidates:
            raise ExternalAPIError(
                service="Google Gemini",
                message="No candidates in response",
                details=data,
            )
        content = candidates[0]["content"]["parts"][0]["text"]

        # Extract usage metadata
        usage = None
        usage_meta = data.get("usageMetadata", {})
        if usage_meta:
            prompt_tokens = usage_meta.get("promptTokenCount", 0)
            completion_tokens = usage_meta.get("candidatesTokenCount", 0)
            usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                model=self.model,
            )
            logger.info(
                f"Gemini request completed: {usage.total_tokens} tokens, "
                f"~${usage.estimated_cost_usd:.6f}"
            )

        return LLMResponse(content=content, usage=usage)

    async def complete_json(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Generate JSON completion using Gemini API."""
        response = await self.complete(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )

        # Clean up response if needed
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
                service="Google Gemini",
                message=f"Failed to parse JSON response: {e}",
                details={"response": response},
            ) from e


# =============================================================================
# Factory Function
# =============================================================================


# Lazy import to avoid boto3 import at module level when not needed
def _get_bedrock_class() -> type[BaseLLMClient]:
    from paper_scraper.modules.scoring.bedrock_client import BedrockClient

    return BedrockClient


# Registry of available LLM providers
_LLM_PROVIDERS: dict[str, type[BaseLLMClient] | str] = {
    "openai": OpenAIClient,
    "anthropic": AnthropicClient,
    "ollama": OllamaClient,
    "azure": AzureOpenAIClient,
    "google": GeminiClient,
    "bedrock": "bedrock",  # Sentinel — resolved in factory
}


def get_llm_client(
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    org_id: str | None = None,
    base_url: str | None = None,
) -> BaseLLMClient:
    """
    Factory function to get LLM client based on provider setting.

    Args:
        provider: Override provider (openai, anthropic, ollama, azure)
        model: Optional provider-specific model name/deployment.
        api_key: Optional provider API key override.
        org_id: Optional OpenAI organization id.
        base_url: Optional base URL override (ollama).

    Returns:
        Configured LLM client instance
    """
    provider = provider or settings.LLM_PROVIDER

    if provider not in _LLM_PROVIDERS:
        raise ValueError(f"Unknown LLM provider: {provider}")

    if provider == "openai":
        return OpenAIClient(api_key=api_key, model=model, org_id=org_id)
    if provider == "anthropic":
        return AnthropicClient(api_key=api_key, model=model)
    if provider == "ollama":
        return OllamaClient(base_url=base_url, model=model)
    if provider == "azure":
        return AzureOpenAIClient(
            api_key=api_key,
            deployment=model,
        )
    if provider == "google":
        return GeminiClient(api_key=api_key, model=model)
    if provider == "bedrock":
        bedrock_cls = _get_bedrock_class()
        return bedrock_cls(model=model)

    # Defensive fallback for static analyzers.
    raise ValueError(f"Unknown LLM provider: {provider}")
