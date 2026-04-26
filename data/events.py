"""
Event ingestion and filtering.

Supports local curated events cache (`data/EuropeAttractions.json`).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import config as cfg


@dataclass(frozen=True)
class Event:
    id: str
    city: str
    country: str
    name: str
    description: str
    start_datetime: datetime
    end_datetime: datetime | None
    venue: str | None
    category: str | None
    source_url: str | None


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_local_events(path: Path) -> list[Event]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        payload = json.load(f)
    rows = payload.get("events", [])
    out: list[Event] = []
    for r in rows:
        start = _parse_dt(r.get("start_datetime"))
        if not start:
            continue
        out.append(
            Event(
                id=str(r.get("id") or ""),
                city=str(r.get("city") or ""),
                country=str(r.get("country") or ""),
                name=str(r.get("name") or ""),
                description=str(r.get("description") or ""),
                start_datetime=start,
                end_datetime=_parse_dt(r.get("end_datetime")),
                venue=r.get("venue"),
                category=r.get("category"),
                source_url=r.get("source_url"),
            )
        )
    return out


def events_for_trip(city: str, country: str, start_date: date, end_date: date) -> list[Event]:
    events = [e for e in load_local_events(cfg.EVENTS_PATH) if e.city.lower() == city.lower()]
    return [e for e in events if start_date <= e.start_datetime.date() <= end_date]
