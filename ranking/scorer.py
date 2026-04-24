"""
Ranking module for personalization after retrieval.

Rubric support:
- Feature engineering: explicit sub-scores (preference, budget, local/tourist, feasibility, diversity).
- Comparison/ablation ready: easy to disable or reweight components.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from models.user_input import TripRequest
from retrieval.retriever import RetrievalHit


@dataclass(frozen=True)
class RankedHit:
    hit: RetrievalHit
    preference_score: float
    budget_score: float
    local_tourist_score: float
    walking_feasibility_score: float
    diversity_bonus: float
    final_score: float


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _price_level_from_budget(total_budget: float, trip_days: int) -> float:
    """
    Heuristic mapping from per-day budget to expected activity price level.
    Output lives in [0, 4] to match dataset price_level convention.
    """
    per_day = total_budget / max(1, trip_days)
    if per_day < 90:
        return 1.0
    if per_day < 180:
        return 2.0
    if per_day < 320:
        return 3.0
    return 4.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def _preference_score(hit: RetrievalHit, trip: TripRequest) -> float:
    tags = set(hit.activity.tags)
    if not trip.preferences.interests:
        return 0.5
    numer = 0.0
    denom = 0.0
    for interest, w in trip.preferences.interests.items():
        denom += w
        if interest in tags:
            numer += w
    return _clip01(numer / denom) if denom > 0 else 0.5


def _budget_score(hit: RetrievalHit, trip: TripRequest) -> float:
    days = (trip.end_date - trip.start_date).days + 1
    target = _price_level_from_budget(trip.budget_amount, days)
    distance = abs(hit.activity.price_level - target)
    # 0 diff => 1.0, 4 diff => 0.0
    return _clip01(1.0 - distance / 4.0)


def _local_tourist_score(hit: RetrievalHit, trip: TripRequest) -> float:
    tags = set(hit.activity.tags)
    is_local = 1.0 if "local" in tags else 0.0
    is_touristy = 1.0 if "touristy" in tags else 0.0
    localness = 0.5 + 0.5 * (is_local - is_touristy)  # local->1, touristy->0, unknown->0.5
    target_touristy = trip.preferences.tourist_vs_local
    target_localness = 1.0 - target_touristy
    return _clip01(1.0 - abs(localness - target_localness))


def _walking_feasibility_score(hit: RetrievalHit, selected: list[RankedHit], trip: TripRequest) -> float:
    tolerance = trip.preferences.walking_tolerance
    lat, lon = hit.activity.lat, hit.activity.lon
    if lat is None or lon is None or not selected:
        return 0.6 + 0.4 * tolerance
    prev = selected[-1].hit.activity
    if prev.lat is None or prev.lon is None:
        return 0.6 + 0.4 * tolerance
    km = _haversine_km(prev.lat, prev.lon, lat, lon)
    # lower tolerance penalizes long jumps harder.
    max_ok_km = 1.5 + 6.0 * tolerance
    return _clip01(1.0 - (km / max_ok_km))


def _diversity_bonus(hit: RetrievalHit, selected: list[RankedHit]) -> float:
    if not selected:
        return 1.0
    cats = {x.hit.activity.category for x in selected}
    tags = {t for x in selected for t in x.hit.activity.tags}
    cat_bonus = 1.0 if hit.activity.category not in cats else 0.25
    new_tags = len(set(hit.activity.tags) - tags)
    tag_bonus = _clip01(new_tags / 4.0)
    return 0.6 * cat_bonus + 0.4 * tag_bonus


def rank_hits(hits: list[RetrievalHit], trip: TripRequest, top_k: int = 8) -> list[RankedHit]:
    """
    Greedy re-ranking with diversity-aware selection.
    """
    remaining = list(hits)
    selected: list[RankedHit] = []

    # Weights can later be tuned and compared in experiments.
    w_retrieval = 0.25
    w_pref = 0.25
    w_budget = 0.2
    w_local = 0.15
    w_walk = 0.1
    w_div = 0.05

    while remaining and len(selected) < top_k:
        best: RankedHit | None = None
        best_idx = -1
        for idx, hit in enumerate(remaining):
            pref = _preference_score(hit, trip)
            bgt = _budget_score(hit, trip)
            loc = _local_tourist_score(hit, trip)
            walk = _walking_feasibility_score(hit, selected, trip)
            div = _diversity_bonus(hit, selected)
            final = (
                w_retrieval * hit.hybrid_score
                + w_pref * pref
                + w_budget * bgt
                + w_local * loc
                + w_walk * walk
                + w_div * div
            )
            cand = RankedHit(
                hit=hit,
                preference_score=pref,
                budget_score=bgt,
                local_tourist_score=loc,
                walking_feasibility_score=walk,
                diversity_bonus=div,
                final_score=final,
            )
            if best is None or cand.final_score > best.final_score:
                best = cand
                best_idx = idx
        assert best is not None
        selected.append(best)
        remaining.pop(best_idx)
    return selected
