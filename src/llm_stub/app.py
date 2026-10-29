"""Tiny OpenAI-compatible stub service for deterministic integration demos."""
from __future__ import annotations

import os
import time
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Offline LLM stub", version="0.1.0")


class CompletionRequest(BaseModel):
    model: str = "stub"
    messages: list[dict[str, Any]]


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.post("/v1/chat/completions")
def chat_completions(request: CompletionRequest) -> dict[str, Any]:
    """Mimic the common chat completion envelope with fixed safe output."""
    delay = max(0, min(int(os.getenv("STUB_DELAY_MS", "0")), 30000)) / 1000
    time.sleep(delay)
    content = '{"route":"specialist-classification-review","proposed_hs_code":null,"reason":"offline stub; evidence required"}'
    prompt_chars = sum(len(str(message.get("content", ""))) for message in request.messages)
    return {"id": "stub-completion", "object": "chat.completion", "created": int(time.time()), "model": request.model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": max(1, prompt_chars // 4), "completion_tokens": max(1, len(content) // 4),
        "total_tokens": max(2, prompt_chars // 4 + len(content) // 4)}}
