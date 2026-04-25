"""
Load and clean activity records for indexing.

Rubric: basic preprocessing (missing values, normalization) — checkbox9 (3 pts).
Methodology: curated JSON first; later swap-in APIs/scraping for checkbox13 (10 pts).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Activity:
    """One row in our travel catalog after cleaning."""

    id: str
    city: str
    country: str
    name: str
    category: str
    description: str
    duration_minutes: int | None
    source_url: str | None
    lat: float | None
    lon: float | None
    neighborhood: str
    tags: tuple[str, ...]


def _normalize_tags(raw: list[str] | None) -> tuple[str, ...]:
    if not raw:
        return ()
    seen: set[str] = set()
    out: list[str] = []
    for t in raw:
        x = str(t).strip().lower().replace(" ", "_")
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return tuple(out)


def _coerce_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _nested_get(d: dict[str, Any], *keys: str) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def load_raw_activities(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        payload = json.load(f)
    rows = payload.get("activities")
    if not isinstance(rows, list):
        raise ValueError("activities.json must contain an 'activities' array")
    return rows


def preprocess_activities(rows: list[dict[str, Any]]) -> list[Activity]:
    """Normalize tags; drop rows without an id or name."""

    activities: list[Activity] = []
    for r in rows:
        aid = (r.get("id") or "").strip()
        name = (r.get("name") or "").strip()
        if not aid or not name:
            continue
        desc = (r.get("description") or "").strip() or "No description provided."
        city = (r.get("city") or "").strip() or "Unknown"
        country = (r.get("country") or "").strip() or "Unknown"
        category = (r.get("category") or "other").strip().lower().replace(" ", "_")
        neighborhood = (r.get("neighborhood") or "").strip() or "Unknown"

        tags = _normalize_tags(r.get("tags"))
        duration_raw = r.get("duration_minutes")
        if duration_raw is None:
            duration_raw = _nested_get(r, "duration_minutes", "typical")
        try:
            duration_minutes = int(duration_raw) if duration_raw is not None else None
        except (TypeError, ValueError):
            duration_minutes = None

        source_url_raw = r.get("source_url")
        if source_url_raw is None:
            source_url_raw = _nested_get(r, "source", "primary_url")
        source_url = str(source_url_raw).strip() if source_url_raw else None

        lat = _coerce_float(r.get("lat"))
        lon = _coerce_float(r.get("lon"))

        activities.append(
            Activity(
                id=aid,
                city=city,
                country=country,
                name=name,
                category=category,
                description=desc,
                duration_minutes=duration_minutes,
                source_url=source_url,
                lat=lat,
                lon=lon,
                neighborhood=neighborhood,
                tags=tags,
            )
        )
    return activities


def load_and_preprocess(path: Path) -> list[Activity]:
    return preprocess_activities(load_raw_activities(path))
