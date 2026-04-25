#!/usr/bin/env python3
"""
Minimal Streamlit UI for RoamRight.

Run:
  .venv/bin/streamlit run ui/app.py
"""

from __future__ import annotations

import sys
from datetime import date, time, timedelta
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.generate import generate_itinerary
from pipeline.run import RoamRightPipeline
from ui.form_mapper import build_trip_request_from_form


@st.cache_resource(show_spinner=False)
def get_pipeline() -> RoamRightPipeline:
    return RoamRightPipeline()


def main() -> None:
    st.set_page_config(page_title="RoamRight", layout="wide")
    st.title("RoamRight")
    st.caption("Personality-aware travel itinerary planner (RAG + ranking + local LLM).")

    with st.form("trip_form"):
        c1, c2 = st.columns(2)
        with c1:
            destination_city = st.text_input("Destination City", value="Paris")
            destination_country = st.text_input("Destination Country", value="France")
            arrival_date = st.date_input("Arrival Date", value=date.today() + timedelta(days=14))
            arrival_time = st.time_input("Arrival Time", value=time(10, 0))
            departure_date = st.date_input("Departure Date", value=date.today() + timedelta(days=18))
            departure_time = st.time_input("Departure Time", value=time(18, 0))
            total_budget = st.number_input("Total Budget", min_value=0.0, value=1200.0, step=50.0)
            budget_currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "JPY"], index=0)
        with c2:
            travel_style = st.selectbox("Vacation Pace", ["relaxed", "balanced", "packed"], index=1)
            tourist_vs_local = st.slider("Touristy vs Local (0=local, 100=touristy)", 0, 100, 30)
            walking_tolerance = st.slider("Walking Tolerance (0=low, 100=high)", 0, 100, 40)
            group_type = st.selectbox("Group Type", ["solo", "friends", "family", "couple"], index=1)
            time_preference = st.selectbox(
                "Time Preference",
                ["flexible", "morning", "afternoon", "evening", "night"],
                index=0,
            )
            selected_interests = st.multiselect(
                "Interests",
                ["Food", "Nature", "Museums", "Nightlife", "Shopping", "History", "Architecture", "Wellness", "Music"],
                default=["Food", "Nature"],
            )

        st.markdown("### Constraints and Notes")
        explicit_must_include = st.text_input("Must Include (comma-separated)", value="")
        explicit_must_avoid = st.text_input("Must Avoid (comma-separated)", value="")
        extra_comments = st.text_area(
            "Other Comments",
            value=(
                "Use + at line start for additional must-include items.\n"
                "Use - at line start for must-avoid items.\n"
                "Example: + Eiffel Tower at night"
            ),
            height=120,
        )
        submitted = st.form_submit_button("Generate Itinerary")

    if not submitted:
        return

    with st.spinner("Building trip request and running RAG + ranking + generation..."):
        trip = build_trip_request_from_form(
            destination_city=destination_city,
            destination_country=destination_country,
            arrival_date=arrival_date,
            arrival_time=arrival_time,
            departure_date=departure_date,
            departure_time=departure_time,
            total_budget=total_budget,
            budget_currency=budget_currency,
            travel_style=travel_style,
            tourist_vs_local=tourist_vs_local,
            walking_tolerance=walking_tolerance,
            group_type=group_type,
            time_preference=time_preference,
            selected_interests=selected_interests,
            extra_comments=extra_comments,
            explicit_must_include=explicit_must_include,
            explicit_must_avoid=explicit_must_avoid,
        )
        pipeline = get_pipeline()
        known_cities = {a.city.lower() for a in pipeline.activities}
        if trip.destination_city.lower() not in known_cities:
            st.error(
                f"We do not have dataset entries for '{trip.destination_city}' yet. "
                f"Try one of: {', '.join(sorted({a.city for a in pipeline.activities}))}."
            )
            st.stop()
        n_days = trip.trip_length_days()
        top_k_ranked = max(8, min(3 * n_days, 24))
        top_k_retrieval = max(20, min(5 * n_days, 40))
        out = pipeline.run(trip=trip, top_k_retrieval=top_k_retrieval, top_k_ranked=top_k_ranked)
        gen = generate_itinerary(
            trip=trip,
            ranked_hits=out.ranked_hits,
            events=out.events,
            scheduled_items=out.scheduled_items,
            prompt_variant="json_then_explain",
        )

    st.subheader("Generated Itinerary")
    st.write(gen.itinerary_text)
    st.caption(
        f"Prompt=json_then_explain | latency={gen.latency_ms:.1f} ms | "
        f"slot_coverage={gen.slot_coverage:.2f} | activity_coverage={gen.activity_coverage:.2f}"
    )

    st.subheader("Top Ranked Activities (Debug View)")
    for i, rh in enumerate(out.ranked_hits, start=1):
        a = rh.hit.activity
        if a.price_min is not None or a.price_max is not None:
            price_txt = f"{a.price_currency or ''} {a.price_min or '?'}-{a.price_max or '?'}"
        else:
            price_txt = f"price level {a.price_level}"
        st.markdown(
            f"**{i}. {a.name}** ({a.category}, price={price_txt})  \n"
            f"`final={rh.final_score:.3f} pref={rh.preference_score:.3f} budget={rh.budget_score:.3f} "
            f"local={rh.local_tourist_score:.3f} walk={rh.walking_feasibility_score:.3f} "
            f"div={rh.diversity_bonus:.3f} constraints={rh.include_exclude_score:.3f}`  \n"
            f"{a.description}"
        )

    st.subheader("Date-Specific Events")
    if not out.events:
        st.write("No events found for these dates in current sources.")
    else:
        for e in sorted(out.events, key=lambda x: x.start_datetime):
            price = f"{e.price_currency or ''} {e.price_min or '?'}-{e.price_max or '?'}"
            st.markdown(
                f"- **{e.name}** ({e.start_datetime.strftime('%Y-%m-%d %H:%M')}) at {e.venue or 'TBA'} | {price}"
            )

    st.subheader("Timed Plan Draft")
    if not out.scheduled_items:
        st.write("No schedule items available.")
    else:
        for s in out.scheduled_items:
            st.markdown(f"- Day {s.day_index} {s.start_time}-{s.end_time}: **{s.title}** ({s.item_type}) — {s.notes}")


if __name__ == "__main__":
    main()
