"""
Map Streamlit form answers to TripRequest.
"""

from __future__ import annotations

from datetime import date, datetime, time

from models.user_input import GroupType, TimePreference, TravelPreferences, TravelStyle, TripRequest


_INTEREST_MAP = {
    "Food": "food",
    "Nature": "nature",
    "Museums": "museums",
    "Nightlife": "nightlife",
    "Shopping": "shopping",
    "History": "history",
    "Architecture": "architecture",
    "Wellness": "wellness",
    "Music": "music",
}


def build_trip_request_from_form(
    destination_city: str,
    destination_country: str,
    arrival_date: date,
    arrival_time: time,
    departure_date: date,
    departure_time: time,
    travel_style: str,
    tourist_vs_local: int,
    walking_tolerance: int,
    group_type: str,
    time_preference: str,
    selected_interests: list[str],
    extra_comments: str,
) -> TripRequest:
    free_notes = extra_comments.strip()

    interests: dict[str, float] = {}
    for label in selected_interests:
        key = _INTEREST_MAP.get(label)
        if key:
            interests[key] = 0.75
    if tourist_vs_local < 40:
        interests["local"] = max(interests.get("local", 0.0), 0.7)
    if tourist_vs_local > 60:
        interests["touristy"] = max(interests.get("touristy", 0.0), 0.7)

    pref = TravelPreferences(
        interests=interests,
        travel_style=TravelStyle(travel_style),
        tourist_vs_local=tourist_vs_local / 100.0,
        time_preference=TimePreference(time_preference),
        walking_tolerance=walking_tolerance / 100.0,
    )

    return TripRequest(
        destination_city=destination_city.strip(),
        destination_country=destination_country.strip(),
        start_date=arrival_date,
        end_date=departure_date,
        arrival_datetime=datetime.combine(arrival_date, arrival_time),
        departure_datetime=datetime.combine(departure_date, departure_time),
        preferences=pref,
        group_type=GroupType(group_type),
        must_include=[],
        must_avoid=[],
        free_text_notes=free_notes,
    )
