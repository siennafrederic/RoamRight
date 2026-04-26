#!/usr/bin/env python3
"""
Run benchmark-scale approach comparisons and ablations.

Outputs:
- experiments/ablation_eval_results.json
- experiments/ablation_eval_summary.md
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.baselines import naive_city_baseline  # noqa: E402
from evaluation.benchmark_requests import benchmark_requests  # noqa: E402
from evaluation.metrics import MetricBundle, evaluate_activity_set  # noqa: E402
from models.user_input import TravelPreferences, TravelStyle, TripRequest  # noqa: E402
from pipeline.generate import generate_itinerary  # noqa: E402
from pipeline.run import RoamRightPipeline  # noqa: E402


@dataclass(frozen=True)
class GenMetrics:
    latency_ms: float
    slot_coverage: float
    activity_coverage: float


@dataclass(frozen=True)
class ApproachEval:
    approach: str
    metrics: MetricBundle
    generation: GenMetrics | None


def _trip_key(trip: TripRequest) -> str:
    return f"{trip.destination_city}_{trip.start_date.isoformat()}_{trip.end_date.isoformat()}"


def _clone_without_personality(trip: TripRequest) -> TripRequest:
    return TripRequest(
        destination_city=trip.destination_city,
        destination_country=trip.destination_country,
        start_date=trip.start_date,
        end_date=trip.end_date,
        arrival_datetime=trip.arrival_datetime,
        departure_datetime=trip.departure_datetime,
        preferences=TravelPreferences(
            interests={},
            travel_style=TravelStyle.BALANCED,
            tourist_vs_local=0.5,
            walking_tolerance=0.5,
        ),
        group_type=trip.group_type,
        must_include=[],
        must_avoid=[],
        free_text_notes="",
    )


def _avg(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def _as_dict(eval_row: ApproachEval) -> dict:
    out = {
        "approach": eval_row.approach,
        "relevance": round(eval_row.metrics.relevance, 4),
        "diversity": round(eval_row.metrics.diversity, 4),
    }
    if eval_row.generation is None:
        out.update({"latency_ms": None, "slot_coverage": None, "activity_coverage": None})
    else:
        out.update(
            {
                "latency_ms": round(eval_row.generation.latency_ms, 2),
                "slot_coverage": round(eval_row.generation.slot_coverage, 4),
                "activity_coverage": round(eval_row.generation.activity_coverage, 4),
            }
        )
    return out


def evaluate_trip(pipeline: RoamRightPipeline, trip: TripRequest, skip_generation: bool) -> list[ApproachEval]:
    out_full = pipeline.run(trip, top_k_retrieval=24, top_k_ranked=12)
    full_acts = [rh.hit.activity for rh in out_full.ranked_hits]

    retrieval_only_acts = [h.activity for h in out_full.rag.hits[:12]]
    no_ranking_acts = retrieval_only_acts
    no_rag_acts = naive_city_baseline(pipeline.activities, city=trip.destination_city, k=12)

    trip_no_personality = _clone_without_personality(trip)
    out_no_personality = pipeline.run(trip_no_personality, top_k_retrieval=24, top_k_ranked=12)
    no_personality_acts = [rh.hit.activity for rh in out_no_personality.ranked_hits]

    def gen_for(trip_for_gen: TripRequest, ranked_hits, resolved, schedule) -> GenMetrics | None:
        if skip_generation:
            return None
        g = generate_itinerary(
            trip=trip_for_gen,
            ranked_hits=ranked_hits,
            resolved_must_includes=resolved,
            scheduled_items=schedule,
            prompt_variant="json_then_explain",
        )
        return GenMetrics(
            latency_ms=g.latency_ms,
            slot_coverage=g.slot_coverage,
            activity_coverage=g.activity_coverage,
        )

    full_gen = gen_for(
        trip,
        out_full.ranked_hits,
        out_full.resolved_must_includes,
        out_full.scheduled_items,
    )

    no_personality_gen = gen_for(
        trip_no_personality,
        out_no_personality.ranked_hits,
        out_no_personality.resolved_must_includes,
        out_no_personality.scheduled_items,
    )

    return [
        ApproachEval("full_pipeline", evaluate_activity_set(full_acts, trip), full_gen),
        ApproachEval("no_personality", evaluate_activity_set(no_personality_acts, trip), no_personality_gen),
        ApproachEval("no_ranking", evaluate_activity_set(no_ranking_acts, trip), None),
        ApproachEval("no_rag", evaluate_activity_set(no_rag_acts, trip), None),
    ]


def summarize(per_trip: dict[str, list[ApproachEval]]) -> dict[str, dict[str, float | None]]:
    by_approach: dict[str, list[ApproachEval]] = {}
    for rows in per_trip.values():
        for r in rows:
            by_approach.setdefault(r.approach, []).append(r)

    summary: dict[str, dict[str, float | None]] = {}
    for approach, rows in by_approach.items():
        rel = _avg([x.metrics.relevance for x in rows])
        div = _avg([x.metrics.diversity for x in rows])
        gens = [x.generation for x in rows if x.generation is not None]
        if gens:
            latency = _avg([g.latency_ms for g in gens])
            slot_cov = _avg([g.slot_coverage for g in gens])
            act_cov = _avg([g.activity_coverage for g in gens])
        else:
            latency = None
            slot_cov = None
            act_cov = None
        summary[approach] = {
            "relevance": round(rel, 4),
            "diversity": round(div, 4),
            "latency_ms": round(latency, 2) if latency is not None else None,
            "slot_coverage": round(slot_cov, 4) if slot_cov is not None else None,
            "activity_coverage": round(act_cov, 4) if act_cov is not None else None,
        }
    return summary


def write_markdown(
    path: Path, summary: dict[str, dict[str, float | None]], num_requests: int, skip_generation: bool
) -> None:
    headers = ["Approach", "Relevance", "Diversity", "Latency (ms)", "Slot Coverage", "Activity Coverage"]
    order = ["full_pipeline", "no_personality", "no_ranking", "no_rag"]
    lines = [
        "# Ablation Evaluation Summary",
        "",
        f"- Requests evaluated: **{num_requests}**",
        f"- Generation metrics included: **{'No' if skip_generation else 'Yes'}**",
        "",
        "| " + " | ".join(headers) + " |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for k in order:
        if k not in summary:
            continue
        s = summary[k]
        lines.append(
            f"| {k} | {s['relevance']} | {s['diversity']} | "
            f"{s['latency_ms'] if s['latency_ms'] is not None else '-'} | "
            f"{s['slot_coverage'] if s['slot_coverage'] is not None else '-'} | "
            f"{s['activity_coverage'] if s['activity_coverage'] is not None else '-'} |"
        )
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run benchmark-scale ablation evaluation.")
    parser.add_argument("--max-trips", type=int, default=0, help="Limit number of benchmark trips (0 = all).")
    parser.add_argument(
        "--skip-generation",
        action="store_true",
        help="Skip LLM generation calls and compute retrieval/ranking metrics only.",
    )
    args = parser.parse_args()

    trips = benchmark_requests()
    if args.max_trips and args.max_trips > 0:
        trips = trips[: args.max_trips]

    pipeline = RoamRightPipeline()
    per_trip_rows: dict[str, list[ApproachEval]] = {}
    for i, trip in enumerate(trips, start=1):
        key = _trip_key(trip)
        print(f"[{i}/{len(trips)}] Evaluating {key}")
        per_trip_rows[key] = evaluate_trip(pipeline, trip, skip_generation=args.skip_generation)

    summary = summarize(per_trip_rows)

    experiments_dir = ROOT / "experiments"
    experiments_dir.mkdir(parents=True, exist_ok=True)
    out_json = experiments_dir / "ablation_eval_results.json"
    out_md = experiments_dir / "ablation_eval_summary.md"

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "num_requests": len(trips),
        "skip_generation": args.skip_generation,
        "summary": summary,
        "per_trip": {k: [_as_dict(x) for x in v] for k, v in per_trip_rows.items()},
    }
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n")
    write_markdown(out_md, summary, num_requests=len(trips), skip_generation=args.skip_generation)

    print(f"\nWrote: {out_json}")
    print(f"Wrote: {out_md}")
    print("\nAverages:")
    for k, s in summary.items():
        print(
            f"{k:14} relevance={s['relevance']:.3f} diversity={s['diversity']:.3f} "
            f"slot_cov={s['slot_coverage'] if s['slot_coverage'] is not None else '-'}"
        )


if __name__ == "__main__":
    main()
