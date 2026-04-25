"""
Prompt variants for itinerary generation experiments.

Rubric support:
- Prompt engineering with evaluation of at least three prompt designs.
"""

from __future__ import annotations

from models.user_input import TripRequest


PROMPT_VARIANTS = (
    "constraint_first",
    "narrative_planner",
    "json_then_explain",
)


def _trip_constraints(trip: TripRequest) -> str:
    p = trip.preferences
    days = (trip.end_date - trip.start_date).days + 1
    arrival = trip.arrival_datetime.isoformat() if trip.arrival_datetime else "unspecified"
    departure = trip.departure_datetime.isoformat() if trip.departure_datetime else "unspecified"
    include = ", ".join(trip.must_include) if trip.must_include else "none"
    avoid = ", ".join(trip.must_avoid) if trip.must_avoid else "none"
    notes = trip.free_text_notes if trip.free_text_notes else "none"
    return (
        f"Destination: {trip.destination_city}, {trip.destination_country}\n"
        f"Dates: {trip.start_date.isoformat()} to {trip.end_date.isoformat()} ({days} days)\n"
        f"Arrival datetime: {arrival}\n"
        f"Departure datetime: {departure}\n"
        f"Travel style: {p.travel_style.value}\n"
        f"Interests: {p.interest_summary()}\n"
        f"Tourist vs local preference (0 local -> 1 touristy): {p.tourist_vs_local:.2f}\n"
        f"Walking tolerance (0 low -> 1 high): {p.walking_tolerance:.2f}\n"
        f"Group type: {trip.group_type.value}\n"
        f"Must include: {include}\n"
        f"Must avoid: {avoid}\n"
        f"Additional notes: {notes}"
    )


def build_messages(
    variant: str,
    trip: TripRequest,
    ranked_context: str,
    required_days: int | None = None,
    correction_note: str | None = None,
) -> list[dict[str, str]]:
    if variant not in PROMPT_VARIANTS:
        raise ValueError(f"Unknown prompt variant {variant!r}; expected one of {PROMPT_VARIANTS}")

    constraints = _trip_constraints(trip)
    n_days = required_days or trip.trip_length_days()
    correction = f"\nCorrection requirement: {correction_note}\n" if correction_note else ""

    if variant == "constraint_first":
        system = (
            "You are a travel planning assistant. Strictly follow constraints and ground every suggestion "
            "in provided candidate activities. Avoid hallucinating venues."
        )
        user = (
            "Create a day-by-day itinerary with sections for Morning, Afternoon, Evening.\n"
            f"Output exactly {n_days} days labeled Day 1 through Day {n_days}.\n"
            "Every day must have non-empty Morning, Afternoon, Evening suggestions.\n"
            "Prioritize local/tourist preference and feasible pacing.\n"
            "For each slot include: activity name and 1 sentence rationale.\n\n"
            "Trip constraints:\n"
            f"{constraints}\n\n"
            "Candidate activities (ranked):\n"
            f"{ranked_context}\n"
            f"{correction}"
        )
    elif variant == "narrative_planner":
        system = (
            "You are an expert concierge who writes practical but engaging plans. "
            "Use provided activities and explain tradeoffs briefly."
        )
        user = (
            "Draft a coherent itinerary narrative for the whole trip, split each day into "
            "Morning/Afternoon/Evening bullets. Keep walking realistic and avoid overpacking each day.\n\n"
            f"Include exactly {n_days} days, each with all three slots present.\n\n"
            "Constraints:\n"
            f"{constraints}\n\n"
            "Ranked activity options:\n"
            f"{ranked_context}\n"
            f"{correction}"
        )
    else:  # json_then_explain
        system = (
            "You output a compact machine-readable plan first, then a short explanation section."
        )
        user = (
            "First output JSON with schema:\n"
            "{days: [{day: int, morning: str, afternoon: str, evening: str}], notes: [str]}\n"
            f"The JSON must include exactly {n_days} entries in `days` with day values 1..{n_days}.\n"
            "Use arrival/departure times to decide valid slots. If arrival is late on day 1, leave earlier slots empty. "
            "If departure is early on the last day, leave later slots empty.\n"
            "For all other valid slots, provide non-empty strings.\n"
            "Time-of-day alignment is mandatory: morning items must be morning-friendly; "
            "evening items must be dinner/nightlife/event-friendly.\n"
            "Do not place dinner-only items in morning slots.\n"
            "Then output a short 'Explanation' section (max 6 bullets).\n"
            "Use only candidate activities.\n\n"
            "Constraints:\n"
            f"{constraints}\n\n"
            "Ranked candidate activities:\n"
            f"{ranked_context}\n"
            f"{correction}"
        )

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
