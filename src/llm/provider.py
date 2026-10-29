"""Provider interface with offline stub and environment-configured OpenAI-compatible backend."""
from __future__ import annotations

import abc
import os
import time
from typing import Any

import httpx


class LLMProvider(abc.ABC):
    """Provider interface used by future model-selected agent loops."""

    @abc.abstractmethod
    def complete(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """Return a completion payload with response text and usage metadata."""


class StubProvider(LLMProvider):
    """Predictable offline provider that never contacts external services."""

    def complete(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """Return a deterministic result and approximate token counts."""
        delay = max(0, int(os.getenv("STUB_DELAY_MS", "0"))) / 1000
        time.sleep(delay)
        content = '{"route":"specialist-classification-review","proposed_hs_code":null}'
        text_len = sum(len(x.get("content", "")) for x in messages)
        return {"content": content, "usage": {"prompt_tokens": max(1, text_len // 4), "completion_tokens": max(1, len(content) // 4)}}


class OpenAICompatProvider(LLMProvider):
    """Configurable OpenAI-compatible backend; endpoint/model/keys come only from env."""

    def complete(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """Call a compatible chat-completion API with a bounded timeout."""
        base_url = os.getenv("LLM_BASE_URL", "").strip().rstrip("/")
        api_key = os.getenv("LLM_API_KEY", "")
        model = os.getenv("LLM_MODEL_PRIMARY", "")
        if not base_url or not model:
            raise RuntimeError("LLM_BASE_URL and LLM_MODEL_PRIMARY must be configured")
        if os.getenv("CHAOS_PROVIDER_DOWN", "false").lower() == "true":
            raise RuntimeError("provider disabled by chaos flag")
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        response = httpx.post(f"{base_url}/chat/completions", json={"model": model, "messages": messages},
            headers=headers, timeout=float(os.getenv("LLM_TIMEOUT_S", "15")))
        response.raise_for_status()
        payload = response.json()
        choice = payload.get("choices", [{}])[0]
        return {"content": choice.get("message", {}).get("content", ""), "usage": payload.get("usage", {})}


def make_provider() -> LLMProvider:
    """Build a provider using the LLM_PROVIDER environment variable."""
    name = os.getenv("LLM_PROVIDER", "stub").lower()
    if name == "stub" or os.getenv("LLM_DRY_RUN", "true").lower() == "true":
        return StubProvider()
    if name == "openai_compatible":
        return OpenAICompatProvider()
    raise ValueError("LLM_PROVIDER must be stub or openai_compatible")
