"""AWS Bedrock LLM client for scoring dimensions.

Uses the Bedrock Runtime Converse API for a unified interface across
Amazon Nova, Anthropic Claude, and other Bedrock-hosted models.

Authentication uses the standard AWS credential chain (environment vars,
~/.aws/credentials, IAM role, etc.) — no API key needed.

Uses boto3 (already a project dependency) with asyncio.to_thread()
for non-blocking calls.
"""

import asyncio
import json
import logging
from typing import Any

from langfuse.decorators import observe

from paper_scraper.core.config import settings
from paper_scraper.core.exceptions import ExternalAPIError
from paper_scraper.modules.scoring.llm_client import (
    BaseLLMClient,
    LLMResponse,
    TokenUsage,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Model Aliases & Pricing
# ============================================================================

# Short aliases → full Bedrock model IDs
BEDROCK_MODEL_ALIASES: dict[str, str] = {
    "nova-micro": "amazon.nova-micro-v1:0",
    "nova-lite": "amazon.nova-lite-v1:0",
    "nova-pro": "amazon.nova-pro-v1:0",
    "claude-3.5-haiku": "anthropic.claude-3-5-haiku-20241022-v1:0",
    "claude-3.5-sonnet": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "claude-3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
}

# Pricing per 1M tokens (on-demand, as of early 2026)
BEDROCK_PRICING: dict[str, dict[str, float]] = {
    "amazon.nova-micro-v1:0": {"input": 0.035, "output": 0.14},
    "amazon.nova-lite-v1:0": {"input": 0.06, "output": 0.24},
    "amazon.nova-pro-v1:0": {"input": 0.80, "output": 3.20},
    "anthropic.claude-3-5-haiku-20241022-v1:0": {"input": 0.80, "output": 4.00},
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {"input": 3.00, "output": 15.00},
    "anthropic.claude-3-haiku-20240307-v1:0": {"input": 0.25, "output": 1.25},
}

# Bedrock error codes that are safe to retry
RETRYABLE_ERROR_CODES = {
    "ThrottlingException",
    "ServiceUnavailableException",
    "InternalServerException",
    "ModelTimeoutException",
}

MAX_RETRIES = 3
BASE_RETRY_DELAY = 1.0
MAX_RETRY_DELAY = 30.0


def _resolve_model_id(model: str) -> str:
    """Resolve a model alias to a full Bedrock model ID."""
    return BEDROCK_MODEL_ALIASES.get(model, model)


class BedrockClient(BaseLLMClient):
    """AWS Bedrock LLM client using the Converse API.

    Supports all Bedrock-hosted models through the unified Converse API.
    Uses boto3 with asyncio.to_thread() for non-blocking AWS API calls.

    Authentication follows the standard AWS credential chain:
    1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    2. Shared credentials file (~/.aws/credentials)
    3. IAM instance/task role (ECS, EC2, Lambda)
    """

    def __init__(
        self,
        model: str | None = None,
        region: str | None = None,
    ):
        raw_model = model or settings.AWS_BEDROCK_MODEL
        self.model = _resolve_model_id(raw_model)
        self.region = region or settings.AWS_REGION
        self._boto_client = None

    def _get_boto_client(self):
        """Get or create a boto3 Bedrock Runtime client (lazy, cached)."""
        if self._boto_client is None:
            import boto3

            self._boto_client = boto3.client(
                "bedrock-runtime",
                region_name=self.region,
            )
        return self._boto_client

    async def _converse(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> dict[str, Any]:
        """Call the Bedrock Converse API with retry logic."""
        messages = [
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ]

        inference_config: dict[str, Any] = {
            "temperature": temperature if temperature is not None else settings.LLM_TEMPERATURE,
            "maxTokens": max_tokens or settings.LLM_MAX_TOKENS,
        }

        kwargs: dict[str, Any] = {
            "modelId": self.model,
            "messages": messages,
            "inferenceConfig": inference_config,
        }

        # Build system prompt (append JSON instruction if needed)
        if system or json_mode:
            sys_text = system or ""
            if json_mode:
                sys_text = (
                    f"{sys_text}\n\nYou MUST respond with valid JSON only. "
                    "No markdown, no explanation, no other text."
                ).strip()
            kwargs["system"] = [{"text": sys_text}]

        last_exception: Exception | None = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                client = self._get_boto_client()
                response = await asyncio.to_thread(client.converse, **kwargs)
                return response
            except Exception as e:
                error_code = ""
                if hasattr(e, "response") and isinstance(e.response, dict):
                    error_code = e.response.get("Error", {}).get("Code", "")

                if error_code in RETRYABLE_ERROR_CODES and attempt < MAX_RETRIES:
                    last_exception = e
                    delay = min(BASE_RETRY_DELAY * (2**attempt), MAX_RETRY_DELAY)
                    logger.warning(
                        "Bedrock request failed (attempt %d/%d), retrying in %.2fs: %s: %s",
                        attempt + 1,
                        MAX_RETRIES + 1,
                        delay,
                        error_code,
                        e,
                    )
                    await asyncio.sleep(delay)
                else:
                    raise ExternalAPIError(
                        service="AWS Bedrock",
                        message=str(e),
                        details={"model": self.model, "error_code": error_code},
                    ) from e

        raise ExternalAPIError(
            service="AWS Bedrock",
            message=f"Request failed after {MAX_RETRIES + 1} attempts",
            details={"last_error": str(last_exception)},
        )

    def _parse_response(self, response: dict[str, Any]) -> LLMResponse:
        """Parse Converse API response into LLMResponse."""
        output = response.get("output", {})
        message = output.get("message", {})
        content_blocks = message.get("content", [])

        # Concatenate all text blocks
        content = ""
        for block in content_blocks:
            if "text" in block:
                content += block["text"]

        # Parse token usage
        usage = None
        usage_data = response.get("usage", {})
        if usage_data:
            input_tokens = usage_data.get("inputTokens", 0)
            output_tokens = usage_data.get("outputTokens", 0)
            usage = TokenUsage(
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                model=self.model,
            )

            # Log with Bedrock-specific pricing
            pricing = BEDROCK_PRICING.get(self.model, {"input": 1.0, "output": 3.0})
            cost = (
                input_tokens * pricing["input"] / 1_000_000
                + output_tokens * pricing["output"] / 1_000_000
            )
            logger.info(
                "Bedrock request completed: %d tokens, ~$%.6f (%s)",
                usage.total_tokens,
                cost,
                self.model,
            )

        return LLMResponse(content=content, usage=usage)

    # ========================================================================
    # BaseLLMClient interface
    # ========================================================================

    @observe(as_type="generation", name="bedrock-completion")
    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> str:
        """Generate completion using Bedrock Converse API, tracked by Langfuse."""
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
        response = await self._converse(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )
        return self._parse_response(response)

    async def complete_json(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Generate JSON completion using Bedrock Converse API."""
        response = await self.complete(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )

        # Clean up markdown-wrapped JSON
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
                service="AWS Bedrock",
                message=f"Failed to parse JSON response: {e}",
                details={"response": response, "model": self.model},
            ) from e
