"""
Itinerary generation from ranked retrieval results.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from time import perf_counter

from models.llm_client import chat_completion
from models.prompts import PROMPT_VARIANTS, build_messages
from models.user_input import TripRequest
from pipeline.resolve import ResolvedMustInclude
from pipeline.schedule import ScheduledItem
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
                f"(final_score={rh.final_score:.3f})\n"
                f"   tags={', '.join(a.tags)}\n"
                f"   desc={a.description}"
            )
        )
    return "\n".join(lines)


def schedule_to_context(items: list[ScheduledItem]) -> str:
    if not items:
        return "No timed schedule was generated."
    rows = [
        f"Day {i.day_index} {i.start_time}-{i.end_time} | {i.item_type} | {i.title} | {i.notes}" for i in items
    ]
    return "\n".join(rows)


def must_include_resolution_context(resolved: list[ResolvedMustInclude]) -> str:
    if not resolved:
        return "No explicit must-include constraints were provided."
    rows: list[str] = []
    for r in resolved:
        rows.append(
            f"- requested='{r.query}' -> title='{r.title}' | source={r.source_type} | status={r.verification_status} | {r.details}"
        )
    rows.append(
        "Instruction: include all requested items; if status=unverified, label clearly as unverified and avoid exact claims."
    )
    return "\n".join(rows)


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


def _extract_days_json_count(text: str) -> int | None:
    """
    Try to parse the first JSON object in text and return len(days) when available.
    """
    # Prefer fenced json block if present.
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.S | re.I)
    candidate = m.group(1) if m else None
    if candidate is None:
        m2 = re.search(r"(\{.*\})", text, flags=re.S)
        candidate = m2.group(1) if m2 else None
    if not candidate:
        return None
    try:
        obj = json.loads(candidate)
    except Exception:
        return None
    days = obj.get("days")
    if isinstance(days, list):
        return len(days)
    return None


def _required_slots_for_day(trip: TripRequest, day_index: int) -> dict[str, bool]:
    required = {"morning": True, "afternoon": True, "evening": True}
    total = trip.trip_length_days()
    if day_index == 1 and trip.arrival_datetime:
        h = trip.arrival_datetime.hour
        if h >= 12:
            required["morning"] = False
        if h >= 17:
            required["afternoon"] = False
    if day_index == total and trip.departure_datetime:
        h = trip.departure_datetime.hour
        if h <= 16:
            required["evening"] = False
        if h <= 12:
            required["afternoon"] = False
    return required


def _has_invalid_slots(text: str, trip: TripRequest) -> bool:
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.S | re.I)
    candidate = m.group(1) if m else None
    if candidate is None:
        m2 = re.search(r"(\{.*\})", text, flags=re.S)
        candidate = m2.group(1) if m2 else None
    if not candidate:
        return False
    try:
        obj = json.loads(candidate)
    except Exception:
        return False
    days = obj.get("days")
    if not isinstance(days, list):
        return False
    expected_days = trip.trip_length_days()
    if len(days) != expected_days:
        return True
    for idx, row in enumerate(days, start=1):
        if not isinstance(row, dict):
            return True
        req = _required_slots_for_day(trip, idx)
        for slot in ("morning", "afternoon", "evening"):
            value = str(row.get(slot, "")).strip()
            if req[slot] and not value:
                return True
    return False


def generate_itinerary(
    trip: TripRequest,
    ranked_hits: list[RankedHit],
    resolved_must_includes: list[ResolvedMustInclude] | None = None,
    scheduled_items: list[ScheduledItem] | None = None,
    prompt_variant: str = "json_then_explain",
    temperature: float = 0.25,
    max_tokens: int = 700,
) -> GeneratedItinerary:
    activities_context = ranked_hits_to_context(ranked_hits)
    full_context = (
        "Ranked activities:\n"
        + activities_context
        + "\n\nDraft timed schedule:\n"
        + schedule_to_context(scheduled_items or [])
        + "\n\nMust-include resolution:\n"
        + must_include_resolution_context(resolved_must_includes or [])
    )
    n_days = trip.trip_length_days()
    messages = build_messages(prompt_variant, trip=trip, ranked_context=full_context, required_days=n_days)
    t0 = perf_counter()
    text = chat_completion(messages, temperature=temperature, max_tokens=max_tokens)
    parsed_count = _extract_days_json_count(text)
    needs_retry = False
    if parsed_count is not None and parsed_count != n_days:
        needs_retry = True
    if _has_invalid_slots(text, trip):
        needs_retry = True
    if needs_retry:
        correction = (
            f"Your previous output did not satisfy format constraints. "
            f"Return exactly {n_days} days. For slots allowed by arrival/departure windows, do not leave them empty."
        )
        retry_messages = build_messages(
            prompt_variant,
            trip=trip,
            ranked_context=full_context,
            required_days=n_days,
            correction_note=correction,
        )
        text = chat_completion(retry_messages, temperature=temperature, max_tokens=max_tokens)
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
    resolved_must_includes: list[ResolvedMustInclude] | None = None,
    scheduled_items: list[ScheduledItem] | None = None,
    variants: tuple[str, ...] = PROMPT_VARIANTS,
) -> list[GeneratedItinerary]:
    outputs: list[GeneratedItinerary] = []
    for variant in variants:
        outputs.append(
            generate_itinerary(
                trip=trip,
                ranked_hits=ranked_hits,
                resolved_must_includes=resolved_must_includes,
                scheduled_items=scheduled_items,
                prompt_variant=variant,
            )
        )
    return outputs
