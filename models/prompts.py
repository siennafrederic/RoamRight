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
    return (
        f"Destination: {trip.destination_city}, {trip.destination_country}\n"
        f"Dates: {trip.start_date.isoformat()} to {trip.end_date.isoformat()} ({days} days)\n"
        f"Budget: {trip.budget_amount:.0f} {trip.budget_currency}\n"
        f"Travel style: {p.travel_style.value}\n"
        f"Interests: {p.interest_summary()}\n"
        f"Tourist vs local preference (0 local -> 1 touristy): {p.tourist_vs_local:.2f}\n"
        f"Walking tolerance (0 low -> 1 high): {p.walking_tolerance:.2f}\n"
        f"Group type: {trip.group_type.value}"
    )


def build_messages(variant: str, trip: TripRequest, ranked_context: str) -> list[dict[str, str]]:
    if variant not in PROMPT_VARIANTS:
        raise ValueError(f"Unknown prompt variant {variant!r}; expected one of {PROMPT_VARIANTS}")

    constraints = _trip_constraints(trip)

    if variant == "constraint_first":
        system = (
            "You are a travel planning assistant. Strictly follow constraints and ground every suggestion "
            "in provided candidate activities. Avoid hallucinating venues."
        )
        user = (
            "Create a day-by-day itinerary with sections for Morning, Afternoon, Evening.\n"
            "Prioritize budget fit, local/tourist preference, and feasible pacing.\n"
            "For each slot include: activity name and 1 sentence rationale.\n\n"
            "Trip constraints:\n"
            f"{constraints}\n\n"
            "Candidate activities (ranked):\n"
            f"{ranked_context}\n"
        )
    elif variant == "narrative_planner":
        system = (
            "You are an expert concierge who writes practical but engaging plans. "
            "Use provided activities and explain tradeoffs briefly."
        )
        user = (
            "Draft a coherent itinerary narrative for the whole trip, split each day into "
            "Morning/Afternoon/Evening bullets. Keep walking realistic and mention budget-aware choices.\n\n"
            "Constraints:\n"
            f"{constraints}\n\n"
            "Ranked activity options:\n"
            f"{ranked_context}\n"
        )
    else:  # json_then_explain
        system = (
            "You output a compact machine-readable plan first, then a short explanation section."
        )
        user = (
            "First output JSON with schema:\n"
            "{days: [{day: int, morning: str, afternoon: str, evening: str}], notes: [str]}\n"
            "Then output a short 'Explanation' section (max 6 bullets).\n"
            "Use only candidate activities.\n\n"
            "Constraints:\n"
            f"{constraints}\n\n"
            "Ranked candidate activities:\n"
            f"{ranked_context}\n"
        )

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
