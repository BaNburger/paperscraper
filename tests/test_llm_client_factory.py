"""Unit tests for LLM client factory overrides."""

from paper_scraper.modules.scoring.llm_client import AnthropicClient, OpenAIClient, get_llm_client


def test_get_llm_client_openai_override_model() -> None:
    """Factory should honor explicit provider/model for OpenAI."""
    client = get_llm_client(provider="openai", model="gpt-5-mini")
    assert isinstance(client, OpenAIClient)
    assert client.model == "gpt-5-mini"


def test_get_llm_client_anthropic_override_model() -> None:
    """Factory should honor explicit provider/model for Anthropic."""
    client = get_llm_client(provider="anthropic", model="claude-sonnet-4-20250514")
    assert isinstance(client, AnthropicClient)
    assert client.model == "claude-sonnet-4-20250514"
