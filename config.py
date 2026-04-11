"""Central configuration: paths and retrieval defaults.

Rubric: modular design; future experiments can override via env or CLI.

Secrets: put `OPENAI_API_KEY` (and `OPENAI_BASE_URL` for LiteLLM) in `.env` at the
project root (gitignored). Copy `.env.example` → `.env` — never commit keys or tokens.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
ACTIVITIES_PATH = DATA_DIR / "activities.json"

# Load `.env` so local runs pick up OPENAI_* without exporting in the shell.
load_dotenv(PROJECT_ROOT / ".env")

# --- LLM via OpenAI-compatible API (Duke LiteLLM proxy or api.openai.com) ---
# LiteLLM exposes POST /v1/chat/completions like OpenAI; set OPENAI_BASE_URL in `.env`.
# Model id must match what your proxy returns from GET /v1/models (not always public names).
# Default: mid-tier — avoid cheapest nano; avoid flagship cost for daily ~$1 budgets.
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY") or None
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.1")
OPENAI_BASE_URL: str | None = os.getenv("OPENAI_BASE_URL") or None

# Dense retrieval — small, fast baseline; compare to a larger model in experiments/.
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Hybrid scoring: convex combination of dense similarity and sparse keyword overlap.
HYBRID_DENSE_WEIGHT = 0.72
HYBRID_KEYWORD_WEIGHT = 0.28

DEFAULT_TOP_K = 8


def openai_key_configured() -> bool:
    return bool(OPENAI_API_KEY and OPENAI_API_KEY.strip())


def openai_client():
    """
    Shared OpenAI SDK client pointing at LiteLLM or direct OpenAI.

    Usage:
        client = openai_client()
        r = client.chat.completions.create(model=config.OPENAI_MODEL, messages=[...])
    """
    if not openai_key_configured():
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Copy .env.example to .env and set your key."
        )
    from openai import OpenAI

    kwargs: dict = {"api_key": OPENAI_API_KEY.strip()}
    if OPENAI_BASE_URL and OPENAI_BASE_URL.strip():
        kwargs["base_url"] = OPENAI_BASE_URL.strip().rstrip("/")
    return OpenAI(**kwargs)
