"""
Event ingestion and filtering.

Supports:
- Local curated events cache (`data/events.json`)
- Optional live Ticketmaster pull when API key is configured.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import httpx

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


def fetch_ticketmaster_events(city: str, start_date: date, end_date: date, country_code: str = "") -> list[Event]:
    if not cfg.TICKETMASTER_API_KEY:
        return []
    params = {
        "apikey": cfg.TICKETMASTER_API_KEY,
        "city": city,
        "startDateTime": f"{start_date.isoformat()}T00:00:00Z",
        "endDateTime": f"{end_date.isoformat()}T23:59:59Z",
        "size": 30,
    }
    if country_code:
        params["countryCode"] = country_code[:2].upper()
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    try:
        resp = httpx.get(url, params=params, timeout=20.0)
        resp.raise_for_status()
    except Exception:
        return []
    data = resp.json()
    rows = data.get("_embedded", {}).get("events", [])
    out: list[Event] = []
    for r in rows:
        dates = r.get("dates", {}).get("start", {})
        local_date = dates.get("localDate")
        local_time = dates.get("localTime") or "19:00:00"
        start = _parse_dt(f"{local_date}T{local_time}") if local_date else None
        if not start:
            continue
        venue = None
        embeds = r.get("_embedded", {})
        if embeds.get("venues"):
            venue = embeds["venues"][0].get("name")
        out.append(
            Event(
                id=str(r.get("id") or ""),
                city=city,
                country=country_code or "",
                name=str(r.get("name") or "Event"),
                description=str(r.get("info") or r.get("pleaseNote") or ""),
                start_datetime=start,
                end_datetime=None,
                venue=venue,
                category=(r.get("classifications") or [{}])[0].get("segment", {}).get("name"),
                source_url=r.get("url"),
            )
        )
    return out


def events_for_trip(city: str, country: str, start_date: date, end_date: date) -> list[Event]:
    events = [e for e in load_local_events(cfg.EVENTS_PATH) if e.city.lower() == city.lower()]
    if cfg.USE_LIVE_EVENTS:
        events.extend(fetch_ticketmaster_events(city=city, start_date=start_date, end_date=end_date, country_code=country))
    return [e for e in events if start_date <= e.start_datetime.date() <= end_date]
