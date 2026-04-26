"""
Resolve must-include requests against dataset activities.

No extra APIs required in this first version:
- exact/fuzzy match against curated activity catalog
- fallback placeholder when unresolved
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from data.preprocess import Activity
from models.user_input import TripRequest


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text.lower())).strip()


def _token_set(text: str) -> set[str]:
    return {t for t in _norm(text).split() if len(t) >= 2}


def _overlap_score(query: str, candidate: str) -> float:
    q = _token_set(query)
    c = _token_set(candidate)
    if not q or not c:
        return 0.0
    inter = len(q & c)
    return inter / len(q)


@dataclass(frozen=True)
class ResolvedMustInclude:
    query: str
    title: str
    source_type: str  # activity_dataset | general_knowledge_placeholder
    verification_status: str  # verified | unverified
    details: str


def _activity_match(query: str, activities: list[Activity]) -> Activity | None:
    qn = _norm(query)
    best: tuple[float, Activity] | None = None
    for a in activities:
        fields = [
            a.name,
            a.category,
            a.description,
            " ".join(a.tags),
            a.neighborhood,
        ]
        cand = " | ".join(fields)
        score = _overlap_score(qn, cand)
        if qn in _norm(a.name):
            score = max(score, 0.99)
        if score >= 0.55 and (best is None or score > best[0]):
            best = (score, a)
    return best[1] if best else None


def resolve_must_includes(
    trip: TripRequest,
    activities: list[Activity],
) -> list[ResolvedMustInclude]:
    resolved: list[ResolvedMustInclude] = []
    for raw in trip.must_include:
        query = raw.strip()
        if not query:
            continue
        a = _activity_match(query, activities)
        if a:
            resolved.append(
                ResolvedMustInclude(
                    query=query,
                    title=a.name,
                    source_type="activity_dataset",
                    verification_status="verified",
                    details=f"{a.city} | {a.category} | {a.source_url or 'source unknown'}",
                )
            )
            continue
        resolved.append(
            ResolvedMustInclude(
                query=query,
                title=query,
                source_type="general_knowledge_placeholder",
                verification_status="unverified",
                details="Not found in activity dataset. Keep as placeholder and verify manually.",
            )
        )
    return resolved
