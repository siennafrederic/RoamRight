#!/usr/bin/env python3
"""
Run a quick quantitative comparison:
- baseline_naive_city
- retrieval_only
- retrieval_plus_ranking
Then run 3 itinerary prompt variants on the ranked output.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.baselines import compare_core_approaches, compare_prompt_variants, demo_trip_request
from pipeline.run import RoamRightPipeline


def main() -> None:
    pipeline = RoamRightPipeline()
    trip = demo_trip_request()
    results = compare_core_approaches(pipeline, trip)

    print(f"Trip: {trip.destination_city}")
    print("Approach                     relevance   diversity")
    print("-" * 70)
    for r in results:
        m = r.metrics
        print(f"{r.approach:28} {m.relevance:9.3f} {m.diversity:10.3f}")

    print("\nPrompt variant comparison (generation from ranked results)")
    print("Variant                    latency_ms   slot_cov   activity_cov   preview")
    print("-" * 95)
    for p in compare_prompt_variants(pipeline, trip):
        print(
            f"{p.variant:25} {p.latency_ms:10.1f} {p.slot_coverage:10.3f} "
            f"{p.activity_coverage:13.3f}   {p.text_preview}"
        )


if __name__ == "__main__":
    main()
