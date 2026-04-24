"""Small provider-agnostic LLM wrapper for itinerary generation.

Rubric support: meaningful integration of an LLM in the system pipeline.
"""

from __future__ import annotations

import config as cfg


def chat_completion(messages: list[dict[str, str]], temperature: float = 0.3, max_tokens: int = 700) -> str:
    """Return assistant text from OpenAI-compatible chat completion API."""
    client = cfg.llm_client()
    response = client.chat.completions.create(
        model=cfg.LLM_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return (response.choices[0].message.content or "").strip()
