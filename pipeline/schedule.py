"""
Time-aware scheduling from ranked activities + optional events.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from data.events import Event
from models.user_input import TripRequest, TravelStyle
from ranking.scorer import RankedHit


@dataclass(frozen=True)
class ScheduledItem:
    day_index: int
    start_time: str
    end_time: str
    title: str
    item_type: str  # activity | event | buffer
    notes: str


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


def _transit_minutes(prev: RankedHit, curr: RankedHit) -> int:
    p, c = prev.hit.activity, curr.hit.activity
    if p.lat is None or p.lon is None or c.lat is None or c.lon is None:
        return 25
    km = _haversine_km(p.lat, p.lon, c.lat, c.lon)
    # walking + city transit blended speed ~18km/h
    return max(10, int((km / 18.0) * 60))


def _activity_minutes(rh: RankedHit) -> int:
    return rh.hit.activity.duration_minutes or 90


def _buffer_minutes(style: TravelStyle) -> int:
    if style == TravelStyle.RELAXED:
        return 75
    if style == TravelStyle.PACKED:
        return 25
    return 45


def _day_start(trip: TripRequest, day_date: date) -> datetime:
    if day_date == trip.start_date and trip.arrival_datetime:
        return trip.arrival_datetime
    return datetime.combine(day_date, datetime.strptime("09:30", "%H:%M").time())


def _day_end(trip: TripRequest, day_date: date) -> datetime:
    if day_date == trip.end_date and trip.departure_datetime:
        return trip.departure_datetime
    return datetime.combine(day_date, datetime.strptime("21:30", "%H:%M").time())


def build_timed_schedule(trip: TripRequest, ranked_hits: list[RankedHit], events: list[Event]) -> list[ScheduledItem]:
    """
    Build a pragmatic timestamped plan with buffers and transit estimates.
    """
    items: list[ScheduledItem] = []
    days = trip.trip_length_days()
    if not ranked_hits and not events:
        return items
    event_by_day: dict[date, list[Event]] = {}
    for e in events:
        event_by_day.setdefault(e.start_datetime.date(), []).append(e)
    idx = 0
    for day_idx in range(1, days + 1):
        d = trip.start_date + timedelta(days=day_idx - 1)
        day_start = _day_start(trip, d)
        day_end = _day_end(trip, d)
        t = day_start
        prev_rh: RankedHit | None = None
        # 2-3 activities/day depending style
        target_acts = 2 if trip.preferences.travel_style == TravelStyle.RELAXED else 3
        for _ in range(target_acts):
            if idx >= len(ranked_hits):
                break
            rh = ranked_hits[idx]
            idx += 1
            transit = _transit_minutes(prev_rh, rh) if prev_rh else 0
            if transit:
                t += timedelta(minutes=transit)
            start = t
            dur = _activity_minutes(rh)
            end = start + timedelta(minutes=dur)
            if end > day_end:
                break
            items.append(
                ScheduledItem(
                    day_index=day_idx,
                    start_time=start.strftime("%H:%M"),
                    end_time=end.strftime("%H:%M"),
                    title=rh.hit.activity.name,
                    item_type="activity",
                    notes=f"{rh.hit.activity.category}; transit {transit}m",
                )
            )
            t = end + timedelta(minutes=_buffer_minutes(trip.preferences.travel_style))
            prev_rh = rh

        for e in event_by_day.get(d, []):
            e_end = e.end_datetime or (e.start_datetime + timedelta(minutes=120))
            items.append(
                ScheduledItem(
                    day_index=day_idx,
                    start_time=e.start_datetime.strftime("%H:%M"),
                    end_time=e_end.strftime("%H:%M"),
                    title=e.name,
                    item_type="event",
                    notes=f"{e.venue or 'venue TBA'}",
                )
            )
    return items
