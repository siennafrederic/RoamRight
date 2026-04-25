"""
FastAPI bridge for the React frontend.

This maps frontend payloads directly into the existing RoamRight pipeline:
TripRequest -> retrieval/ranking/events/schedule -> LLM itinerary generation.
"""

from __future__ import annotations

from datetime import date, datetime, time
from functools import lru_cache
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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
    interests: list[str] = Field(default_factory=list)
    notes: str = ""


class TopActivity(BaseModel):
    name: str
    category: str
    neighborhood: str | None = None


class PlanResponse(BaseModel):
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

    return TripRequest(
        destination_city=req.destinationCity.strip(),
        destination_country=req.destinationCountry.strip(),
        start_date=req.startDate,
        end_date=req.endDate,
        arrival_datetime=datetime.combine(req.startDate, time(hour=10, minute=0)),
        departure_datetime=datetime.combine(req.endDate, time(hour=20, minute=0)),
        preferences=prefs,
        group_type=GroupType(req.groupType),
        must_include=[],
        must_avoid=[],
        free_text_notes=req.notes.strip(),
    )


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
        return PlanResponse(
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
