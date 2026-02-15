import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time

st.set_page_config(layout="wide")

OPENF1_BASE = "https://api.openf1.org/v1"

# -------------------------
# Styling (Broadcast Dark)
# -------------------------

st.markdown("""
<style>
body {background-color: #0E1117;}
.metric-label {font-size: 14px;}
</style>
""", unsafe_allow_html=True)

# -------------------------
# Utilities
# -------------------------

def get_json(endpoint):
    response = requests.get(f"{OPENF1_BASE}/{endpoint}")
    if response.status_code != 200:
        return []
    return response.json()

def format_lap_time(seconds):
    if seconds is None:
        return "--"
    total_seconds = float(seconds)
    hours = int(total_seconds // 3600)
    remaining = total_seconds % 3600
    minutes = int(remaining // 60)
    secs = remaining % 60
    return f"{hours:02d}H.{minutes:02d}M.{secs:06.3f}S"

def tire_color(compound):
    colors = {
        "SOFT": "red",
        "MEDIUM": "yellow",
        "HARD": "white",
        "INTERMEDIATE": "green",
        "WET": "blue"
    }
    return colors.get(compound, "gray")

# -------------------------
# Header
# -------------------------

st.title("🏎 LIVE F1 DRIVER ANALYTICS")

session_key = st.number_input("Session Key", value=9222)

drivers_data = get_json(f"drivers?session_key={session_key}")

driver_map = {
    f"{d['name_acronym']} ({d['driver_number']})": d["driver_number"]
    for d in drivers_data
}

selected_driver_label = st.selectbox(
    "Select Driver",
    list(driver_map.keys())
)

driver_number = driver_map[selected_driver_label]

auto_refresh = st.checkbox("🔄 Auto Refresh (5s)", value=True)

# -------------------------
# Data Loading
# -------------------------

laps_data = get_json(
    f"laps?session_key={session_key}&driver_number={driver_number}"
)

if not laps_data:
    st.warning("No data found.")
    st.stop()

laps = pd.DataFrame(laps_data).sort_values("lap_number")

stints = pd.DataFrame(
    get_json(f"stints?session_key={session_key}&driver_number={driver_number}")
)

positions = pd.DataFrame(
    get_json(f"positions?session_key={session_key}")
)

drivers_full = pd.DataFrame(drivers_data)

session_data = get_json(f"sessions?session_key={session_key}")

# -------------------------
# Core Metrics
# -------------------------

current_lap = laps.iloc[-1]
previous_lap = laps.iloc[-2] if len(laps) > 1 else None
best_lap = laps.loc[laps["lap_duration"].idxmin()]

current_lap_number = int(current_lap["lap_number"])
best_lap_number = int(best_lap["lap_number"])

# Tire info
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

    best_stint = stints[
        (stints.lap_start <= best_lap_number) &
        (stints.lap_end >= best_lap_number)
    ]

    if not best_stint.empty:
        best_lap_tire = best_stint.iloc[0]["compound"]

# -------------------------
# Position Logic
# -------------------------

driver_ahead = "-"
driver_behind = "-"
gap_ahead = "-"
gap_behind = "-"
gap_to_leader = "-"

if not positions.empty and "driver_number" in positions.columns:

    latest_positions = positions.iloc[-20:]  # last batch

    if "position" in latest_positions.columns:

        latest_positions = latest_positions.sort_values("position")

        driver_row = latest_positions[
            latest_positions["driver_number"] == driver_number
        ]

        if not driver_row.empty:

            pos_index = driver_row.index[0]
            driver_position = driver_row.iloc[0]["position"]

            if driver_position > 1:
                ahead_row = latest_positions[
                    latest_positions["position"] == driver_position - 1
                ]
                if not ahead_row.empty:
                    driver_ahead = drivers_full[
                        drivers_full["driver_number"] ==
                        ahead_row.iloc[0]["driver_number"]
                    ]["name_acronym"].values[0]
                    gap_ahead = ahead_row.iloc[0].get("interval", "-")

            behind_row = latest_positions[
                latest_positions["position"] == driver_position + 1
            ]
            if not behind_row.empty:
                driver_behind = drivers_full[
                    drivers_full["driver_number"] ==
                    behind_row.iloc[0]["driver_number"]
                ]["name_acronym"].values[0]
                gap_behind = behind_row.iloc[0].get("interval", "-")

            gap_to_leader = driver_row.iloc[0].get("gap_to_leader", "-")

# -------------------------
# Dashboard Layout
# -------------------------

st.subheader("⏱ LAP TIMES")

col1, col2 = st.columns(2)

col1.metric("Current Lap", format_lap_time(current_lap["lap_duration"]))
col1.metric("Previous Lap",
            format_lap_time(previous_lap["lap_duration"]) if previous_lap is not None else "--")

col2.metric("Best Lap",
            f"{format_lap_time(best_lap['lap_duration'])} (Lap {best_lap_number})")
col2.metric("Best Lap Tire", best_lap_tire)

st.subheader("🛞 TIRES")

st.markdown(
    f"Current: <span style='color:{tire_color(current_tire)}'>{current_tire}</span> | "
    f"Previous: {previous_tire}",
    unsafe_allow_html=True
)

st.subheader("📏 GAPS")

gap_col1, gap_col2, gap_col3 = st.columns(3)

gap_col1.metric("To Leader", gap_to_leader)
gap_col2.metric(f"⬆ {driver_ahead}", gap_ahead)
gap_col3.metric(f"⬇ {driver_behind}", gap_behind)

# -------------------------
# Lap Trend Chart
# -------------------------

st.subheader("📊 Lap Time Trend")

fig = px.line(
    laps,
    x="lap_number",
    y="lap_duration",
    template="plotly_dark"
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------
# Tire Stint Timeline
# -------------------------

if not stints.empty:
    st.subheader("🛞 Tire Stints")

    stint_fig = px.timeline(
        stints,
        x_start="lap_start",
        x_end="lap_end",
        y=["Stint"] * len(stints),
        color="compound",
        template="plotly_dark"
    )
    st.plotly_chart(stint_fig, use_container_width=True)

# -------------------------
# Race Progress
# -------------------------

if session_data:
    total_laps = session_data[0].get("total_laps", 0)
    if total_laps:
        st.subheader("🏁 Race Progress")
        st.progress(current_lap_number / total_laps)
        st.write(f"Lap {current_lap_number} / {total_laps}")

# -------------------------
# Auto Refresh
# -------------------------

if auto_refresh:
    time.sleep(5)
    st.rerun()
