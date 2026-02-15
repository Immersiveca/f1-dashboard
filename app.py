import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time

st.set_page_config(layout="wide")

OPENF1_BASE = "https://api.openf1.org/v1"

# -----------------------------
# Styling – Broadcast Dark Mode
# -----------------------------

st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #0E1117;
    color: white;
}
.metric-label {
    font-size: 12px !important;
}
.big-font {
    font-size:22px !important;
    font-weight:600;
}
.banner {
    padding:10px;
    border-radius:8px;
    background: linear-gradient(90deg, #E10600, #8B0000);
    color:white;
    text-align:center;
    font-weight:bold;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Utilities
# -----------------------------

def get_json(endpoint):
    try:
        response = requests.get(f"{OPENF1_BASE}/{endpoint}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

import math

def format_lap_time(value):
    """
    Format seconds into: 00H.00M.00.000S
    Returns "--" for None/NaN/invalid.
    """
    try:
        if value is None:
            return "--"
        sec = float(value)
        if math.isnan(sec) or sec <= 0:
            return "--"
        hours = int(sec // 3600)
        sec = sec - (hours * 3600)
        minutes = int(sec // 60)
        sec = sec - (minutes * 60)
        return f"{hours:02d}H.{minutes:02d}M.{sec:06.3f}S"
    except:
        return "--"
        
def tire_color(compound):
    colors = {
        "SOFT": "#ff2e2e",
        "MEDIUM": "#ffd800",
        "HARD": "#ffffff",
        "INTERMEDIATE": "#00ff66",
        "WET": "#0099ff"
    }
    return colors.get(compound, "#aaaaaa")

# -----------------------------
# Header
# -----------------------------

st.title("🏎 F1 LIVE ANALYTICS BY MPH")

session_key = st.number_input("Session Key", value=9222)

session_data = get_json(f"sessions?session_key={session_key}")
if session_data:
    session_name = session_data[0].get("session_name", "")
    location = session_data[0].get("location", "")
    st.markdown(
        f"<div class='banner'>{location} – {session_name}</div>",
        unsafe_allow_html=True
    )

# -----------------------------
# Driver Selection
# -----------------------------

drivers_data = get_json(f"drivers?session_key={session_key}")

driver_map = {
    f"{d['name_acronym']} ({d['driver_number']})": d["driver_number"]
    for d in drivers_data
}

selected_driver = st.selectbox("Select Driver", list(driver_map.keys()))
driver_number = driver_map[selected_driver]

auto_refresh = st.toggle("Auto Refresh (5s)", value=True)

# -----------------------------
# Load Core Data
# -----------------------------

laps = pd.DataFrame(get_json(
    f"laps?session_key={session_key}&driver_number={driver_number}"
))

if laps.empty:
    st.warning("No lap data available.")
    st.stop()

laps = laps.sort_values("lap_number")

stints = pd.DataFrame(get_json(
    f"stints?session_key={session_key}&driver_number={driver_number}"
))

positions = pd.DataFrame(get_json(
    f"positions?session_key={session_key}"
))

drivers_full = pd.DataFrame(drivers_data)

# -----------------------------
# Core Metrics
# -----------------------------

# Current / previous lap (keep the last row for lap number progress)
current_lap = laps.iloc[-1]
previous_lap = laps.iloc[-2] if len(laps) > 1 else None

# Best lap: ignore NaN / missing lap_duration
valid_laps = laps.dropna(subset=["lap_duration_num"])
if valid_laps.empty:
    best_lap = None
    best_lap_number = None
else:
    best_lap = valid_laps.loc[valid_laps["lap_duration_num"].idxmin()]
    best_lap_number = int(best_lap["lap_number"])
current_lap_number = int(current_lap["lap_number"])

# Tire logic
current_tire = "-"
best_lap_tire = "-"

if not stints.empty:
    current_stint = stints[
        (stints.lap_start <= current_lap_number) &
        (stints.lap_end >= current_lap_number)
    ]
    if not current_stint.empty:
        current_tire = current_stint.iloc[0]["compound"]

    best_stint = stints[
        (stints.lap_start <= best_lap_number) &
        (stints.lap_end >= best_lap_number)
    ]
    if not best_stint.empty:
        best_lap_tire = best_stint.iloc[0]["compound"]

#------------------------------
# Make lap durations numeric + safe
#-------------------------------

laps["lap_duration_num"] = pd.to_numeric(laps.get("lap_duration"), errors="coerce")

# -----------------------------
# Position & Gaps
# -----------------------------

driver_ahead = "-"
driver_behind = "-"
gap_ahead = "-"
gap_behind = "-"
gap_leader = "-"

if not positions.empty and "position" in positions.columns:
    latest_positions = positions.sort_values("date").iloc[-20:]
    latest_positions = latest_positions.sort_values("position")

    driver_row = latest_positions[
        latest_positions["driver_number"] == driver_number
    ]

    if not driver_row.empty:
        pos = int(driver_row.iloc[0]["position"])
        gap_leader = driver_row.iloc[0].get("gap_to_leader", "-")

        ahead = latest_positions[latest_positions["position"] == pos - 1]
        behind = latest_positions[latest_positions["position"] == pos + 1]

        if not ahead.empty:
            ahead_number = ahead.iloc[0]["driver_number"]
            gap_ahead = ahead.iloc[0].get("interval", "-")
            driver_ahead = drivers_full[
                drivers_full["driver_number"] == ahead_number
            ]["name_acronym"].values[0]

        if not behind.empty:
            behind_number = behind.iloc[0]["driver_number"]
            gap_behind = behind.iloc[0].get("interval", "-")
            driver_behind = drivers_full[
                drivers_full["driver_number"] == behind_number
            ]["name_acronym"].values[0]

# -----------------------------
# Layout – Mobile Optimized
# -----------------------------

st.subheader("⏱ Lap Times")

st.metric("Current Lap", format_lap_time(current_lap["lap_duration_num"]))
if previous_lap is not None:
    st.metric("Previous Lap", format_lap_time(previous_lap["lap_duration_num"]))
else:
    st.metric("Previous Lap", "--")

if best_lap is not None:
    st.metric("Best Lap", f"{format_lap_time(best_lap['lap_duration_num'])} (Lap {best_lap_number})")
else:
    st.metric("Best Lap", "--")
    
st.markdown(
    f"🛞 Current Tire: <span style='color:{tire_color(current_tire)}'>{current_tire}</span>",
    unsafe_allow_html=True
)

st.subheader("📏 Gaps")

st.metric("To Leader", gap_leader)
st.metric(f"⬆ {driver_ahead}", gap_ahead)
st.metric(f"⬇ {driver_behind}", gap_behind)

# -----------------------------
# Lap Trend Chart
# -----------------------------

st.subheader("📊 Lap Time Evolution")

fig = px.line(
    laps.dropna(subset=["lap_duration_num"]),
    x="lap_number",
    y="lap_duration_num",
    template="plotly_dark"
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Race Progress
# -----------------------------

if session_data:
    total_laps = session_data[0].get("total_laps", 0)
    if total_laps:
        st.subheader("🏁 Race Progress")
        st.progress(current_lap_number / total_laps)
        st.write(f"Lap {current_lap_number} / {total_laps}")

# -----------------------------
# Auto Refresh
# -----------------------------

if auto_refresh:
    time.sleep(5)
    st.rerun()
