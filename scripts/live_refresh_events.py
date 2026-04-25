#!/usr/bin/env python3
"""
Refresh local event cache from Ticketmaster.

Run:
  .venv/bin/python scripts/live_refresh_events.py
  .venv/bin/python scripts/live_refresh_events.py --days 120
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config as cfg
from data.events import Event, fetch_ticketmaster_events, load_local_events
from data.preprocess import load_and_preprocess


COUNTRY_TO_CODE = {
    "france": "FR",
    "spain": "ES",
    "japan": "JP",
    "united_states": "US",
    "usa": "US",
}


def _event_key(e: Event) -> tuple[str, str, str]:
    return (e.city.lower(), e.name.lower(), e.start_datetime.isoformat())


def _to_json_row(e: Event) -> dict:
    row = asdict(e)
    row["start_datetime"] = e.start_datetime.isoformat()
    row["end_datetime"] = e.end_datetime.isoformat() if e.end_datetime else None
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=90, help="Lookahead window in days")
    args = parser.parse_args()

    if not cfg.TICKETMASTER_API_KEY:
        raise RuntimeError(
            "TICKETMASTER_API_KEY missing in .env. Add it and rerun this script."
        )

    activities = load_and_preprocess(cfg.ACTIVITIES_PATH)
    city_country_pairs = sorted({(a.city, a.country) for a in activities})
    start = date.today()
    end = start + timedelta(days=max(1, args.days))

    existing = load_local_events(cfg.EVENTS_PATH)
    merged: dict[tuple[str, str, str], Event] = {_event_key(e): e for e in existing}

    fetched_total = 0
    for city, country in city_country_pairs:
        cc = COUNTRY_TO_CODE.get(country.strip().lower().replace(" ", "_"), "")
        events = fetch_ticketmaster_events(
            city=city,
            start_date=start,
            end_date=end,
            country_code=cc,
        )
        fetched_total += len(events)
        for e in events:
            merged[_event_key(e)] = e
        print(f"{city}: fetched {len(events)} live events")

    rows = [_to_json_row(e) for e in sorted(merged.values(), key=lambda x: (x.city, x.start_datetime))]
    payload = {"events": rows}
    with cfg.EVENTS_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(rows)} total events to {cfg.EVENTS_PATH}")
    print(f"Live events fetched this run: {fetched_total}")


if __name__ == "__main__":
    main()
