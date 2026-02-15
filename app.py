import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide")

OPENF1_BASE = "https://api.openf1.org/v1"

def get_json(endpoint):
    response = requests.get(f"{OPENF1_BASE}/{endpoint}")
    if response.status_code != 200:
        return []
    return response.json()

st.title("🏎 F1 Driver Dashboard")

session_key = st.number_input("Session Key", value=9222)
driver_number = st.number_input("Driver Number (e.g. 1, 16, 44)", value=1)

if st.button("Load Data"):

    with st.spinner("Fetching data..."):

        laps_data = get_json(
            f"laps?session_key={session_key}&driver_number={driver_number}"
        )

        stints_data = get_json(
            f"stints?session_key={session_key}&driver_number={driver_number}"
        )

        positions_data = get_json(
            f"positions?session_key={session_key}"
        )

        session_data = get_json(
            f"sessions?session_key={session_key}"
        )

        if not laps_data:
            st.error("No lap data found.")
            st.stop()

        laps = pd.DataFrame(laps_data).sort_values("lap_number")
        stints = pd.DataFrame(stints_data)
        positions = pd.DataFrame(positions_data)

        current_lap = laps.iloc[-1]
        previous_lap = laps.iloc[-2] if len(laps) > 1 else None
        best_lap = laps.loc[laps["lap_duration"].idxmin()]
        current_lap_number = int(current_lap["lap_number"])
        best_lap_number = int(best_lap["lap_number"])

        # Tire logic
        current_tire = "-"
        previous_tire = "-"
        best_lap_tire = "-"

        if not stints.empty:
            current_stint = stints[
                (stints.lap_start <= current_lap_number) &
                (stints.lap_end >= current_lap_number)
            ]
            if not current_stint.empty:
                current_tire = current_stint.iloc[0]["compound"]

            if len(stints) > 1:
                previous_tire = stints.sort_values("lap_start").iloc[-2]["compound"]

            best_lap_stint = stints[
                (stints.lap_start <= best_lap_number) &
                (stints.lap_end >= best_lap_number)
            ]
            if not best_lap_stint.empty:
                best_lap_tire = best_lap_stint.iloc[0]["compound"]

        col1, col2, col3 = st.columns(3)

        col1.metric("Current Lap", round(current_lap["lap_duration"], 3))
        col1.metric(
            "Previous Lap",
            round(previous_lap["lap_duration"], 3) if previous_lap is not None else "--"
        )

        col2.metric(
            "Best Lap",
            f"{round(best_lap['lap_duration'], 3)} (Lap {best_lap_number})"
        )

        col2.metric("Best Lap Tire", best_lap_tire)

        col3.metric("Current Tire", current_tire)
        col3.metric("Previous Tire", previous_tire)

        st.subheader("Gap Information")

        gap_to_leader = "-"
        gap_ahead = "-"

        if not positions.empty:
            if "driver_number" in positions.columns:
                driver_positions = positions[
                    positions["driver_number"] == driver_number
                ]
                if not driver_positions.empty:
                    latest_position = driver_positions.iloc[-1]

                    if "gap_to_leader" in latest_position:
                        gap_to_leader = latest_position["gap_to_leader"]

                    if "interval" in latest_position:
                        gap_ahead = latest_position["interval"]

        st.write("Gap to Leader:", gap_to_leader)
        st.write("Gap to Car Ahead:", gap_ahead)

        if session_data:
            total_laps = session_data[0].get("total_laps", 0)
            if total_laps:
                st.subheader("Race Progress")
                st.progress(current_lap_number / total_laps)
                st.write(f"Lap {current_lap_number} / {total_laps}")
