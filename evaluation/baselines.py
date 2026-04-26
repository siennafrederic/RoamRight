"""
Baseline and approach comparison utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from data.preprocess import Activity
from evaluation.metrics import MetricBundle, evaluate_activity_set
from models.user_input import GroupType, TravelPreferences, TravelStyle, TripRequest
from pipeline.generate import GeneratedItinerary, generate_prompt_variants
from pipeline.run import RoamRightPipeline


@dataclass(frozen=True)
class ApproachResult:
    approach: str
    activities: list[Activity]
    metrics: MetricBundle


@dataclass(frozen=True)
class PromptVariantResult:
    variant: str
    latency_ms: float
    slot_coverage: float
    activity_coverage: float
    text_preview: str


def naive_city_baseline(activities: list[Activity], city: str, k: int = 8) -> list[Activity]:
    city_rows = [a for a in activities if a.city.lower() == city.lower()]
    # Deterministic baseline: alphabetical by name, no personalization.
    city_rows.sort(key=lambda a: a.name.lower())
    return city_rows[:k]


def retrieval_only_activities(pipeline: RoamRightPipeline, trip: TripRequest, k: int = 8) -> list[Activity]:
    rag = pipeline.run(trip, top_k_retrieval=k, top_k_ranked=k).rag
    return [h.activity for h in rag.hits[:k]]


def retrieval_plus_ranking_activities(
    pipeline: RoamRightPipeline, trip: TripRequest, k_retrieval: int = 16, k_ranked: int = 8
) -> list[Activity]:
    out = pipeline.run(trip, top_k_retrieval=k_retrieval, top_k_ranked=k_ranked)
    return [rh.hit.activity for rh in out.ranked_hits]


def compare_core_approaches(pipeline: RoamRightPipeline, trip: TripRequest) -> list[ApproachResult]:
    naive = naive_city_baseline(pipeline.activities, city=trip.destination_city, k=8)
    retrieval = retrieval_only_activities(pipeline, trip=trip, k=8)
    ranked = retrieval_plus_ranking_activities(pipeline, trip=trip, k_retrieval=16, k_ranked=8)
    return [
        ApproachResult("baseline_naive_city", naive, evaluate_activity_set(naive, trip)),
        ApproachResult("retrieval_only", retrieval, evaluate_activity_set(retrieval, trip)),
        ApproachResult("retrieval_plus_ranking", ranked, evaluate_activity_set(ranked, trip)),
    ]


def compare_prompt_variants(pipeline: RoamRightPipeline, trip: TripRequest) -> list[PromptVariantResult]:
    out = pipeline.run(trip, top_k_retrieval=16, top_k_ranked=8)
    generated: list[GeneratedItinerary] = generate_prompt_variants(
        trip,
        out.ranked_hits,
        resolved_must_includes=out.resolved_must_includes,
        scheduled_items=out.scheduled_items,
    )
    results: list[PromptVariantResult] = []
    for g in generated:
        preview = g.itinerary_text.replace("\n", " ").strip()
        if len(preview) > 140:
            preview = preview[:137] + "..."
        results.append(
            PromptVariantResult(
                variant=g.prompt_variant,
                latency_ms=g.latency_ms,
                slot_coverage=g.slot_coverage,
                activity_coverage=g.activity_coverage,
                text_preview=preview,
            )
        )
    return results


def demo_trip_request() -> TripRequest:
    return TripRequest(
        destination_city="Paris",
        destination_country="France",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 5),
        preferences=TravelPreferences(
            interests={"food": 0.9, "nature": 0.7, "local": 0.8, "nightlife": 0.4},
            travel_style=TravelStyle.BALANCED,
            tourist_vs_local=0.25,
            walking_tolerance=0.35,
        ),
        group_type=GroupType.FRIENDS,
    )
