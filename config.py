"""Central configuration: paths, retrieval defaults, and LLM provider settings.

Rubric: modular design; future experiments can override via env or CLI.

Secrets and provider settings should live in `.env` at the project root
(gitignored). Copy `.env.example` -> `.env` and edit locally.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
load_dotenv(PROJECT_ROOT / ".env")


def _resolve_activities_path() -> Path:
    """
    Resolve which activity dataset powers retrieval/ranking.

    Priority:
    1) ROAMRIGHT_ACTIVITIES_PATH env var (absolute or relative)
    2) repo default data/EuropeAttractions.json
    """
    env_path = os.getenv("ROAMRIGHT_ACTIVITIES_PATH")
    if env_path:
        p = Path(env_path).expanduser()
        if not p.is_absolute():
            p = (PROJECT_ROOT / p).resolve()
        return p

    return DATA_DIR / "EuropeAttractions.json"


ACTIVITIES_PATH = _resolve_activities_path()
EVENTS_PATH = DATA_DIR / "events.json"

# --- LLM config (provider-agnostic) ---
# Default is local Ollama to avoid API spend.
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
LLM_MODEL: str = os.getenv("LLM_MODEL", "mistral:7b-instruct").strip()
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1").strip().rstrip("/")
LLM_API_KEY: str | None = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or None

# Back-compat aliases (older config references).
OPENAI_API_KEY: str | None = LLM_API_KEY
OPENAI_MODEL: str = LLM_MODEL
OPENAI_BASE_URL: str | None = LLM_BASE_URL

# Dense retrieval — small, fast baseline; compare to larger models in experiments/.
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Hybrid scoring: convex combination of dense similarity and sparse keyword overlap.
HYBRID_DENSE_WEIGHT = 0.72
HYBRID_KEYWORD_WEIGHT = 0.28

DEFAULT_TOP_K = 8


def llm_key_configured() -> bool:
    if LLM_PROVIDER == "ollama":
        return True
    return bool(LLM_API_KEY and LLM_API_KEY.strip())


def llm_client() -> OpenAI:
    """OpenAI-compatible client for Ollama, LiteLLM, or API providers.

    Providers:
    - ollama: local server at `http://localhost:11434/v1` (default key placeholder)
    - openai_compatible: any OpenAI-style endpoint requiring a bearer token
    """
    provider = LLM_PROVIDER
    if provider == "ollama":
        # Ollama's OpenAI-compatible endpoint accepts placeholder auth values.
        api_key = (LLM_API_KEY or "ollama").strip() or "ollama"
    elif provider == "openai_compatible":
        if not llm_key_configured():
            raise RuntimeError(
                "LLM_API_KEY (or OPENAI_API_KEY) is required for openai_compatible provider."
            )
        api_key = LLM_API_KEY.strip()  # type: ignore[union-attr]
    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER={provider!r}. Use 'ollama' or 'openai_compatible'."
        )

    return OpenAI(api_key=api_key, base_url=LLM_BASE_URL)
