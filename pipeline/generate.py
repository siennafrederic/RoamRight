"""
Itinerary generation from ranked retrieval results.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from models.llm_client import chat_completion
from models.prompts import PROMPT_VARIANTS, build_messages
from models.user_input import TripRequest
from ranking.scorer import RankedHit


@dataclass(frozen=True)
class GeneratedItinerary:
    prompt_variant: str
    itinerary_text: str
    latency_ms: float
    slot_coverage: float
    activity_coverage: float


def ranked_hits_to_context(ranked_hits: list[RankedHit]) -> str:
    if not ranked_hits:
        return "No ranked activities available."
    lines: list[str] = []
    for i, rh in enumerate(ranked_hits, start=1):
        a = rh.hit.activity
        lines.append(
            (
                f"{i}. {a.name} [{a.category}] in {a.neighborhood}, {a.city} "
                f"(price={a.price_level}, final_score={rh.final_score:.3f})\n"
                f"   tags={', '.join(a.tags)}\n"
                f"   desc={a.description}"
            )
        )
    return "\n".join(lines)


def _slot_coverage(text: str) -> float:
    t = text.lower()
    needed = ("morning", "afternoon", "evening")
    present = sum(1 for x in needed if x in t)
    return present / len(needed)


def _activity_coverage(text: str, ranked_hits: list[RankedHit], top_n: int = 8) -> float:
    t = text.lower()
    names = [rh.hit.activity.name.lower() for rh in ranked_hits[:top_n]]
    if not names:
        return 0.0
    present = sum(1 for n in names if n in t)
    return present / len(names)


def generate_itinerary(
    trip: TripRequest,
    ranked_hits: list[RankedHit],
    prompt_variant: str = "constraint_first",
    temperature: float = 0.25,
    max_tokens: int = 850,
) -> GeneratedItinerary:
    context = ranked_hits_to_context(ranked_hits)
    messages = build_messages(prompt_variant, trip=trip, ranked_context=context)
    t0 = perf_counter()
    text = chat_completion(messages, temperature=temperature, max_tokens=max_tokens)
    elapsed_ms = (perf_counter() - t0) * 1000.0
    return GeneratedItinerary(
        prompt_variant=prompt_variant,
        itinerary_text=text,
        latency_ms=elapsed_ms,
        slot_coverage=_slot_coverage(text),
        activity_coverage=_activity_coverage(text, ranked_hits),
    )


def generate_prompt_variants(
    trip: TripRequest,
    ranked_hits: list[RankedHit],
    variants: tuple[str, ...] = PROMPT_VARIANTS,
) -> list[GeneratedItinerary]:
    outputs: list[GeneratedItinerary] = []
    for variant in variants:
        outputs.append(generate_itinerary(trip=trip, ranked_hits=ranked_hits, prompt_variant=variant))
    return outputs
