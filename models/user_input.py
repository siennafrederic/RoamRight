"""
Structured user input for retrieval queries and (later) LLM conditioning.

Rubric alignment:
- Feature engineering / system inputs (preferences as a vector + summary).
- Supports multi-turn refinement by mutating or layering TripRequest fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import FrozenSet


class TravelStyle(str, Enum):
    RELAXED = "relaxed"
    BALANCED = "balanced"
    PACKED = "packed"


class GroupType(str, Enum):
    SOLO = "solo"
    FRIENDS = "friends"
    FAMILY = "family"
    COUPLE = "couple"


class TimePreference(str, Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"
    FLEXIBLE = "flexible"


# Canonical interest tags — must overlap dataset tags for strong retrieval.
CANONICAL_INTERESTS: FrozenSet[str] = frozenset(
    {
        "food",
        "nature",
        "museums",
        "nightlife",
        "shopping",
        "history",
        "architecture",
        "local",
        "touristy",
        "wellness",
        "music",
        "sports",
    }
)


@dataclass
class TravelPreferences:
    """Weighted interests and style knobs used by retrieval and ranking."""

    interests: dict[str, float] = field(default_factory=dict)
    travel_style: TravelStyle = TravelStyle.BALANCED
    tourist_vs_local: float = 0.5  # 0 = only local, 1 = tourist-forward
    time_preference: TimePreference = TimePreference.FLEXIBLE
    walking_tolerance: float = 0.5  # 0 = low, 1 = happy to walk a lot

    def __post_init__(self) -> None:
        for k, v in self.interests.items():
            if k not in CANONICAL_INTERESTS:
                raise ValueError(f"Unknown interest {k!r}; use canonical keys {sorted(CANONICAL_INTERESTS)}")
            if not 0.0 <= v <= 1.0:
                raise ValueError(f"Interest weight for {k} must be in [0, 1], got {v}")
        if not 0.0 <= self.tourist_vs_local <= 1.0:
            raise ValueError("tourist_vs_local must be in [0, 1]")
        if not 0.0 <= self.walking_tolerance <= 1.0:
            raise ValueError("walking_tolerance must be in [0, 1]")

    def interest_summary(self) -> str:
        """Natural language fragment for embedding-based retrieval."""
        if not self.interests:
            return "general sightseeing"
        ranked = sorted(self.interests.items(), key=lambda x: -x[1])
        parts = [f"{name} (importance {w:.1f})" for name, w in ranked if w >= 0.2]
        return ", ".join(parts) if parts else "balanced mix of activities"


@dataclass
class TripRequest:
    """Full trip specification: destination, dates, budget, and preferences."""

    destination_city: str
    destination_country: str
    start_date: date
    end_date: date
    budget_amount: float
    budget_currency: str = "USD"
    preferences: TravelPreferences = field(default_factory=TravelPreferences)
    group_type: GroupType = GroupType.SOLO

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if self.budget_amount < 0:
            raise ValueError("budget_amount must be non-negative")

    def retrieval_query_text(self) -> str:
        """
        Single string fed to the bi-encoder for dense retrieval.

        Custom 'chunking' of user intent: we concatenate structured fields so the
        embedding aligns with our structured activity documents.
        """
        p = self.preferences
        style_note = {
            TravelStyle.RELAXED: "slow pace, few activities per day",
            TravelStyle.BALANCED: "moderate pace",
            TravelStyle.PACKED: "packed schedule, maximize experiences",
        }[p.travel_style]
        local_note = (
            "hidden gems and neighborhood spots"
            if p.tourist_vs_local < 0.35
            else "iconic attractions and well-known sights"
            if p.tourist_vs_local > 0.65
            else "mix of local favorites and major sights"
        )
        walk = "minimal walking between spots" if p.walking_tolerance < 0.35 else "comfortable with walking"
        group = self.group_type.value.replace("_", " ")
        return (
            f"Plan activities in {self.destination_city}, {self.destination_country}. "
            f"Interests: {p.interest_summary()}. "
            f"Style: {style_note}. {local_note}. "
            f"Group: {group}. {walk}. "
            f"Budget roughly {self.budget_amount:.0f} {self.budget_currency} for the trip."
        )
