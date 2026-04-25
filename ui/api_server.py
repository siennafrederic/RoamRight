"""
FastAPI bridge for the React frontend.

This maps frontend payloads directly into the existing RoamRight pipeline:
TripRequest -> retrieval/ranking/events/schedule -> LLM itinerary generation.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, time
from functools import lru_cache
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from models.llm_client import chat_completion
from models.user_input import GroupType, TimePreference, TravelPreferences, TravelStyle, TripRequest
from pipeline.generate import generate_itinerary
from pipeline.run import RoamRightPipeline


class PlanRequest(BaseModel):
    destinationCity: str
    destinationCountry: str
    startDate: date
    endDate: date
    travelStyle: Literal["relaxed", "balanced", "packed"] = "balanced"
    touristVsLocal: int = Field(ge=0, le=100, default=50)
    walkingTolerance: int = Field(ge=0, le=100, default=50)
    groupType: Literal["solo", "friends", "family", "couple"] = "solo"
    arrivalTime: str = "10:00"
    departureTime: str = "20:00"
    interests: list[str] = Field(default_factory=list)
    notes: str = ""


class TopActivity(BaseModel):
    name: str
    category: str
    neighborhood: str | None = None


class PlanResponse(BaseModel):
    days: list[dict[str, str | int]]
    explanationBullets: list[str]
    itineraryText: str
    topActivities: list[TopActivity]
    latencyMs: float
    slotCoverage: float
    activityCoverage: float


@lru_cache(maxsize=1)
def _pipeline() -> RoamRightPipeline:
    # Build once so embeddings/index are reused across requests.
    return RoamRightPipeline()


def _build_trip_request(req: PlanRequest) -> TripRequest:
    interests: dict[str, float] = {}
    for interest in req.interests:
        key = interest.strip().lower()
        if key:
            interests[key] = 0.75
    if req.touristVsLocal < 40:
        interests["local"] = max(interests.get("local", 0.0), 0.7)
    if req.touristVsLocal > 60:
        interests["touristy"] = max(interests.get("touristy", 0.0), 0.7)

    prefs = TravelPreferences(
        interests=interests,
        travel_style=TravelStyle(req.travelStyle),
        tourist_vs_local=req.touristVsLocal / 100.0,
        time_preference=TimePreference.FLEXIBLE,
        walking_tolerance=req.walkingTolerance / 100.0,
    )

    try:
        arrival_time = time.fromisoformat(req.arrivalTime)
        departure_time = time.fromisoformat(req.departureTime)
    except ValueError as exc:
        raise ValueError("arrivalTime and departureTime must be valid HH:MM values.") from exc

    return TripRequest(
        destination_city=req.destinationCity.strip(),
        destination_country=req.destinationCountry.strip(),
        start_date=req.startDate,
        end_date=req.endDate,
        arrival_datetime=datetime.combine(req.startDate, arrival_time),
        departure_datetime=datetime.combine(req.endDate, departure_time),
        preferences=prefs,
        group_type=GroupType(req.groupType),
        must_include=[],
        must_avoid=[],
        free_text_notes=req.notes.strip(),
    )


def _extract_json_block(text: str) -> dict | None:
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
    return obj if isinstance(obj, dict) else None


def _parse_explanations(text: str) -> list[str]:
    parts = re.split(r"(?i)\bexplanation\b", text, maxsplit=1)
    if len(parts) < 2:
        return []
    expl = parts[1]
    bullets: list[str] = []
    for line in expl.splitlines():
        stripped = line.strip().lstrip("*-").strip()
        if stripped:
            bullets.append(stripped)
    return bullets[:6]


def _required_slots_for_day(trip: TripRequest, day_index: int) -> dict[str, bool]:
    required = {"morning": True, "afternoon": True, "evening": True}
    total = trip.trip_length_days()
    if day_index == 1 and trip.arrival_datetime:
        hour = trip.arrival_datetime.hour
        if hour >= 12:
            required["morning"] = False
        if hour >= 17:
            required["afternoon"] = False
    if day_index == total and trip.departure_datetime:
        hour = trip.departure_datetime.hour
        if hour <= 16:
            required["evening"] = False
        if hour <= 12:
            required["afternoon"] = False
    return required


def _looks_misaligned(slot: str, text: str) -> bool:
    t = text.lower()
    if slot == "morning":
        return any(x in t for x in ("dinner", "nightclub", "late-night", "cocktail bar"))
    if slot == "evening":
        return any(x in t for x in ("breakfast", "coffee run", "morning market"))
    return False


def _valid_days_structure(trip: TripRequest, parsed: dict | None) -> bool:
    parsed_days = (parsed or {}).get("days")
    if not isinstance(parsed_days, list) or len(parsed_days) != trip.trip_length_days():
        return False
    for idx, row in enumerate(parsed_days, start=1):
        if not isinstance(row, dict):
            return False
        req = _required_slots_for_day(trip, idx)
        for slot in ("morning", "afternoon", "evening"):
            value = str(row.get(slot, "")).strip()
            if req[slot] and not value:
                return False
            if value and _looks_misaligned(slot, value):
                return False
    return True


def _repair_days_with_model(
    trip: TripRequest, itinerary_text: str, top_activities: list[TopActivity]
) -> list[dict[str, str | int]]:
    names = [f"{a.name} ({a.category})" for a in top_activities]
    prompt = (
        "Rewrite this itinerary into strict JSON only with schema:\n"
        "{days:[{day:int,morning:str,afternoon:str,evening:str}],notes:[str]}\n"
        f"Need exactly {trip.trip_length_days()} days.\n"
        f"Arrival datetime: {trip.arrival_datetime.isoformat() if trip.arrival_datetime else 'unspecified'}\n"
        f"Departure datetime: {trip.departure_datetime.isoformat() if trip.departure_datetime else 'unspecified'}\n"
        "If day-1 has late arrival, morning/afternoon can be empty.\n"
        "If last day has early departure, afternoon/evening can be empty.\n"
        "For all other slots, provide concise natural language text.\n"
        "Do not put dinner/nightlife in morning slots.\n"
        f"Candidate activities: {', '.join(names)}\n\n"
        f"Original output:\n{itinerary_text}"
    )
    fixed = chat_completion(
        [
            {"role": "system", "content": "You are a strict JSON reformatter for itinerary plans."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=700,
    )
    parsed = _extract_json_block(fixed)
    if not _valid_days_structure(trip, parsed):
        raise ValueError("Could not produce a valid day-by-day plan from model output.")
    return parsed["days"]


def _normalize_days(
    trip: TripRequest, parsed: dict | None, raw_itinerary_text: str, top_activities: list[TopActivity]
) -> list[dict[str, str | int]]:
    if _valid_days_structure(trip, parsed):
        return parsed["days"]
    return _repair_days_with_model(trip, raw_itinerary_text, top_activities)


app = FastAPI(title="RoamRight API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/plan", response_model=PlanResponse)
def plan(req: PlanRequest) -> PlanResponse:
    try:
        trip = _build_trip_request(req)
        trip_days = trip.trip_length_days()
        top_k_retrieval = max(16, trip_days * 8)
        top_k_ranked = max(8, trip_days * 4)

        out = _pipeline().run(trip, top_k_retrieval=top_k_retrieval, top_k_ranked=top_k_ranked)
        gen = generate_itinerary(
            trip=trip,
            ranked_hits=out.ranked_hits,
            events=out.events,
            resolved_must_includes=out.resolved_must_includes,
            scheduled_items=out.scheduled_items,
            prompt_variant="json_then_explain",
        )

        top_activities = [
            TopActivity(
                name=rh.hit.activity.name,
                category=rh.hit.activity.category,
                neighborhood=rh.hit.activity.neighborhood,
            )
            for rh in out.ranked_hits[:12]
        ]
        parsed = _extract_json_block(gen.itinerary_text)
        normalized_days = _normalize_days(trip, parsed, gen.itinerary_text, top_activities)
        explanation = _parse_explanations(gen.itinerary_text)
        if not explanation:
            explanation = [
                "The plan balances iconic landmarks with local atmosphere while keeping pacing realistic.",
                "Time windows are adapted to your arrival and departure schedule.",
                "Each day is structured to keep transitions practical and coherent."
            ]
        return PlanResponse(
            days=normalized_days,
            explanationBullets=explanation,
            itineraryText=gen.itinerary_text,
            topActivities=top_activities,
            latencyMs=gen.latency_ms,
            slotCoverage=gen.slot_coverage,
            activityCoverage=gen.activity_coverage,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - runtime guard for UI
        raise HTTPException(status_code=500, detail=f"Planner failed: {exc}") from exc
