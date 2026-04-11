#!/usr/bin/env python3
"""
RoamRight entrypoint — smoke test for retrieval (v0).

Run from repo root:
  python main.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config as cfg
from data.preprocess import load_and_preprocess
from models.user_input import GroupType, TravelPreferences, TravelStyle, TripRequest
from retrieval.embedder import Embedder
from retrieval.retriever import ActivityRetriever


def main() -> None:
    activities = load_and_preprocess(cfg.ACTIVITIES_PATH)
    print(f"Loaded {len(activities)} activities after preprocessing.\n")

    embedder = Embedder(cfg.EMBEDDING_MODEL_NAME)
    retriever = ActivityRetriever(activities, embedder)

    prefs = TravelPreferences(
        interests={"museums": 0.9, "food": 0.7, "history": 0.5},
        travel_style=TravelStyle.BALANCED,
        tourist_vs_local=0.55,
        walking_tolerance=0.6,
    )
    trip = TripRequest(
        destination_city="Paris",
        destination_country="France",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 5),
        budget_amount=1800.0,
        budget_currency="USD",
        preferences=prefs,
        group_type=GroupType.COUPLE,
    )

    q = trip.retrieval_query_text()
    print("--- Retrieval query (structured user intent chunk) ---")
    print(q)
    print("\n--- Top-k hybrid hits (Paris only) ---\n")

    for i, hit in enumerate(retriever.retrieve(q, top_k=5, city_filter="Paris"), start=1):
        a = hit.activity
        print(f"{i}. {a.name} [{a.category}]")
        print(f"   hybrid={hit.hybrid_score:.3f}  dense={hit.dense_score:.3f}  kw={hit.keyword_score:.3f}")
        print(f"   tags: {list(a.tags)}")
        print()


if __name__ == "__main__":
    main()
