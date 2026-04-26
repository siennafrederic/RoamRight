"""
Fixed benchmark trip requests for quantitative evaluation.
"""

from __future__ import annotations

from datetime import date

from models.user_input import GroupType, TravelPreferences, TravelStyle, TripRequest


def benchmark_requests() -> list[TripRequest]:
    """
    12 diverse requests across supported cities for stable comparisons.
    """
    return [
        TripRequest(
            destination_city="Barcelona",
            destination_country="Spain",
            start_date=date(2026, 6, 10),
            end_date=date(2026, 6, 14),
            preferences=TravelPreferences(
                interests={"food": 0.9, "architecture": 0.8, "nightlife": 0.7},
                travel_style=TravelStyle.BALANCED,
                tourist_vs_local=0.45,
                walking_tolerance=0.6,
            ),
            group_type=GroupType.FRIENDS,
            free_text_notes="Artsy local energy and one iconic highlight each day.",
        ),
        TripRequest(
            destination_city="Madrid",
            destination_country="Spain",
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 5),
            preferences=TravelPreferences(
                interests={"history": 0.9, "food": 0.7, "architecture": 0.8},
                travel_style=TravelStyle.PACKED,
                tourist_vs_local=0.65,
                walking_tolerance=0.7,
            ),
            group_type=GroupType.COUPLE,
            free_text_notes="Packed but coherent days with great evening atmosphere.",
        ),
        TripRequest(
            destination_city="Sevilla",
            destination_country="Spain",
            start_date=date(2026, 6, 18),
            end_date=date(2026, 6, 22),
            preferences=TravelPreferences(
                interests={"history": 0.8, "music": 0.7, "food": 0.8},
                travel_style=TravelStyle.RELAXED,
                tourist_vs_local=0.35,
                walking_tolerance=0.45,
            ),
            group_type=GroupType.COUPLE,
            free_text_notes="Flamenco, old-town charm, and slower pacing.",
        ),
        TripRequest(
            destination_city="Valencia",
            destination_country="Spain",
            start_date=date(2026, 7, 3),
            end_date=date(2026, 7, 7),
            preferences=TravelPreferences(
                interests={"nature": 0.8, "food": 0.8, "architecture": 0.7},
                travel_style=TravelStyle.BALANCED,
                tourist_vs_local=0.4,
                walking_tolerance=0.55,
            ),
            group_type=GroupType.FAMILY,
            free_text_notes="Include parks and family-friendly daytime blocks.",
        ),
        TripRequest(
            destination_city="Paris",
            destination_country="France",
            start_date=date(2026, 7, 10),
            end_date=date(2026, 7, 15),
            preferences=TravelPreferences(
                interests={"food": 0.85, "architecture": 0.8, "shopping": 0.6},
                travel_style=TravelStyle.BALANCED,
                tourist_vs_local=0.5,
                walking_tolerance=0.55,
            ),
            group_type=GroupType.COUPLE,
            free_text_notes="Blend signature landmarks with neighborhood spots.",
        ),
        TripRequest(
            destination_city="London",
            destination_country="United Kingdom",
            start_date=date(2026, 8, 2),
            end_date=date(2026, 8, 6),
            preferences=TravelPreferences(
                interests={"history": 0.8, "museums": 0.65, "music": 0.75},
                travel_style=TravelStyle.PACKED,
                tourist_vs_local=0.55,
                walking_tolerance=0.65,
            ),
            group_type=GroupType.SOLO,
            free_text_notes="High-energy city sampling with a strong evening plan.",
        ),
        TripRequest(
            destination_city="Rome",
            destination_country="Italy",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 5),
            preferences=TravelPreferences(
                interests={"history": 0.95, "food": 0.85, "architecture": 0.9},
                travel_style=TravelStyle.BALANCED,
                tourist_vs_local=0.6,
                walking_tolerance=0.6,
            ),
            group_type=GroupType.FRIENDS,
            free_text_notes="Must feel iconic but not rushed.",
        ),
        TripRequest(
            destination_city="Florence",
            destination_country="Italy",
            start_date=date(2026, 9, 12),
            end_date=date(2026, 9, 16),
            preferences=TravelPreferences(
                interests={"museums": 0.25, "history": 0.7, "architecture": 0.85, "food": 0.7},
                travel_style=TravelStyle.RELAXED,
                tourist_vs_local=0.4,
                walking_tolerance=0.5,
            ),
            group_type=GroupType.COUPLE,
            free_text_notes="Avoid museum-heavy overload, prioritize streetscape and food.",
        ),
        TripRequest(
            destination_city="Barcelona",
            destination_country="Spain",
            start_date=date(2026, 10, 4),
            end_date=date(2026, 10, 8),
            preferences=TravelPreferences(
                interests={"nightlife": 0.9, "food": 0.8, "music": 0.75},
                travel_style=TravelStyle.PACKED,
                tourist_vs_local=0.35,
                walking_tolerance=0.6,
            ),
            group_type=GroupType.FRIENDS,
            free_text_notes="Late-night friendly plan with strong local vibe.",
        ),
        TripRequest(
            destination_city="Madrid",
            destination_country="Spain",
            start_date=date(2026, 11, 1),
            end_date=date(2026, 11, 3),
            preferences=TravelPreferences(
                interests={"food": 0.8, "shopping": 0.7, "wellness": 0.6},
                travel_style=TravelStyle.RELAXED,
                tourist_vs_local=0.3,
                walking_tolerance=0.35,
            ),
            group_type=GroupType.FAMILY,
            free_text_notes="Keep transitions short and avoid overpacked blocks.",
        ),
        TripRequest(
            destination_city="Paris",
            destination_country="France",
            start_date=date(2026, 11, 14),
            end_date=date(2026, 11, 18),
            preferences=TravelPreferences(
                interests={"nature": 0.7, "food": 0.8, "local": 0.8},
                travel_style=TravelStyle.BALANCED,
                tourist_vs_local=0.25,
                walking_tolerance=0.5,
            ),
            group_type=GroupType.SOLO,
            free_text_notes="Neighborhood feel, parks, and local food scenes.",
        ),
        TripRequest(
            destination_city="Rome",
            destination_country="Italy",
            start_date=date(2026, 12, 3),
            end_date=date(2026, 12, 7),
            preferences=TravelPreferences(
                interests={"history": 0.9, "architecture": 0.85, "nightlife": 0.5},
                travel_style=TravelStyle.BALANCED,
                tourist_vs_local=0.55,
                walking_tolerance=0.58,
            ),
            group_type=GroupType.COUPLE,
            free_text_notes="Mix famous sites with authentic evening streets.",
        ),
    ]
