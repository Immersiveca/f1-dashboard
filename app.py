import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(layout="wide")

OPENF1_BASE = "https://api.openf1.org/v1"

def get_json(endpoint):
    return requests.get(f"{OPENF1_BASE}/{endpoint}").json()

st.title("🏎 F1 Live Driver Dashboard")

session_key = st.number_input("Enter Session Key", value=9150)

driver_number = st.number_input("Enter Driver Number (e.g., 1, 16, 44)", value=1)

if st.button("Load Data"):

    with st.spinner("Fetching data..."):

        laps = pd.DataFrame(get_json(
            f"laps?session_key={session_key}&driver_number={driver_number}"
        ))

        stints = pd.DataFrame(get_json(
            f"stints?session_key={session_key}&driver_number={driver_number}"
        ))

        positions = pd.DataFrame(get_json(
            f"positions?session_key={session_key}"
        ))

        session = get_json(f"sessions?session_key={session_key}")[0]

        laps = laps.sort_values("lap_number")

        current_lap = laps.iloc[-1]
        previous_lap = laps.iloc[-2] if len(laps) > 1 else None
        best_lap = laps.loc[laps["lap_duration"].idxmin()]

        current_lap_number = int(current_lap["lap_number"])

        current_stint = stints[
            (stints.lap_start <= current_lap_number) &
            (stints.lap_end >= current_lap_number)
        ].iloc[0]

        previous_stint = stints.sort_values("lap_start").iloc[-2] \
            if len(stints) > 1 else None

        best_lap_number = int(best_lap["lap_number"])
        best_lap_stint = stints[
            (stints.lap_start <= best_lap_number) &
            (stints.lap_end >= best_lap_number)
        ].iloc[0]

        latest_positions = positions[
            positions["lap_number"] == current_lap_number
        ].sort_values("position")

        driver_row = latest_positions[
            latest_positions["driver_number"] == driver_number
        ].iloc[0]

        col1, col2, col3 = st.columns(3)

        col1.metric("Current Lap", round(current_lap["lap_duration"], 3))
        col1.metric("Previous Lap", 
                    round(previous_lap["lap_duration"], 3) if previous_lap is not None else "--")

        col2.metric("Best Lap",
                    f"{round(best_lap['lap_duration'],3)} (Lap {best_lap_number})")

        col2.metric("Best Lap Tire", best_lap_stint["compound"])

        col3.metric("Current Tire", current_stint["compound"])
        col3.metric("Previous Tire", 
                    previous_stint["compound"] if previous_stint is not None else "--")

        st.subheader("Gap Information")

        st.write("Gap to Leader:", driver_row["gap_to_leader"])
        st.write("Gap to Car Ahead:", driver_row["interval"])

        st.subheader("Race Progress")

        st.progress(current_lap_number / session["total_laps"])
        st.write(f"Lap {current_lap_number} / {session['total_laps']}")

