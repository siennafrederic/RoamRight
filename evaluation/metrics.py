"""
Evaluation metrics for itinerary candidate sets.

Rubric support:
- At least three quantitative metrics.
- Reusable for baseline comparisons and ablations.
"""

from __future__ import annotations

from dataclasses import dataclass

from data.preprocess import Activity
from models.user_input import TripRequest


@dataclass(frozen=True)
class MetricBundle:
    relevance: float
    diversity: float

    def as_dict(self) -> dict[str, float]:
        return {
            "relevance": round(self.relevance, 4),
            "diversity": round(self.diversity, 4),
        }


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def relevance_score(activities: list[Activity], trip: TripRequest) -> float:
    """
    Weighted overlap between user interests and activity tags.
    """
    if not activities:
        return 0.0
    interests = trip.preferences.interests
    if not interests:
        return 0.5
    denom = sum(interests.values()) or 1.0
    total = 0.0
    for a in activities:
        tags = set(a.tags)
        match = sum(w for name, w in interests.items() if name in tags)
        total += match / denom
    return _clip01(total / len(activities))


def diversity_score(activities: list[Activity]) -> float:
    """
    Simple set diversity combining category coverage and tag uniqueness.
    """
    if not activities:
        return 0.0
    categories = {a.category for a in activities}
    all_tags = [t for a in activities for t in a.tags]
    unique_tags = set(all_tags)
    cat_component = _clip01(len(categories) / max(1, len(activities)))
    tag_component = _clip01(len(unique_tags) / max(1, len(all_tags))) if all_tags else 0.0
    return _clip01(0.6 * cat_component + 0.4 * tag_component)


def evaluate_activity_set(activities: list[Activity], trip: TripRequest) -> MetricBundle:
    return MetricBundle(
        relevance=relevance_score(activities, trip),
        diversity=diversity_score(activities),
    )
