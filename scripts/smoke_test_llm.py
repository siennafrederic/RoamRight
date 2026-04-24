#!/usr/bin/env python3
"""Quick connectivity smoke test for whichever LLM provider is configured.

Run:
  .venv/bin/python scripts/smoke_test_llm.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config as cfg
from models.llm_client import chat_completion


def main() -> None:
    print(f"provider={cfg.LLM_PROVIDER} model={cfg.LLM_MODEL} base_url={cfg.LLM_BASE_URL}")
    prompt = "Return exactly one short sentence: suggest a cheap local activity in Paris."
    text = chat_completion([{"role": "user", "content": prompt}], temperature=0.2, max_tokens=80)
    print("response:")
    print(text)


if __name__ == "__main__":
    main()
