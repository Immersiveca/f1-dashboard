import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
import math

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
.banner {
    padding:10px;
    border-radius:10px;
    background: linear-gradient(90deg, #E10600, #8B0000);
    color:white;
    text-align:center;
    font-weight:700;
    letter-spacing:0.5px;
}
.small-note {
    opacity: 0.8;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Utilities
# -----------------------------
def get_json(endpoint: str):
    try:
        r = requests.get(f"{OPENF1_BASE}/{endpoint}", timeout=12)
        if r.status_code == 200:
            return r.json()
        return []
    except:
        return []

def format_lap_time(value):
    """
    Format seconds into: 00H.00M.00.000S
    Returns '--' for None/NaN/invalid.
    """
    try:
        if value is None:
            return "--"
        sec = float(value)
        if math.isnan(sec) or sec <= 0:
            return "--"
        hours = int(sec // 3600)
        sec -= hours * 3600
        minutes = int(sec // 60)
        sec -= minutes * 60
        return f"{hours:02d}H.{minutes:02d}M.{sec:06.3f}S"
    except:
        return "--"

def tire_color(compound: str):
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

# Session banner (safe)
session_data = get_json(f"sessions?session_key={session_key}")
if session_data:
    session_name = session_data[0].get("session_name", "")
    location = session_data[0].get("location", "")
    st.markdown(f"<div class='banner'>{location} – {session_name}</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='small-note'>Session info not available for this key.</div>", unsafe_allow_html=True)

# -----------------------------
# Driver Selection
# -----------------------------
drivers_data = get_json(f"drivers?session_key={session_key}")
if not drivers_data:
    st.error("No drivers found for this session key. Try another session key.")
    st.stop()

driver_map = {f"{d.get('name_acronym','?')} ({d.get('driver_number','?')})": d.get("driver_number")
              for d in drivers_data if d.get("driver_number") is not None}

if not driver_map:
    st.error("Driver list returned but could not be parsed. Try another session key.")
    st.stop()

selected_driver = st.selectbox("Select Driver", list(driver_map.keys()))
driver_number = int(driver_map[selected_driver])

auto_refresh = st.toggle("Auto Refresh (5s)", value=True)

# -----------------------------
# Load Core Data
# -----------------------------
laps = pd.DataFrame(get_json(f"laps?session_key={session_key}&driver_number={driver_number}"))
if laps.empty:
    st.warning("No lap data available for this driver/session.")
    st.stop()

# Sort laps
if "lap_number" in laps.columns:
    laps = laps.sort_values("lap_number")
else:
    st.error("Lap data does not contain lap_number. Can't build dashboard.")
    st.stop()

# --- Ensure we have a numeric lap duration column (bulletproof) ---
# Some sessions use lap_duration; if missing, create lap_duration_num anyway to avoid KeyError.
if "lap_duration" in laps.columns:
    laps["lap_duration_num"] = pd.to_numeric(laps["lap_duration"], errors="coerce")
elif "lap_time" in laps.columns:
    laps["lap_duration_num"] = pd.to_numeric(laps["lap_time"], errors="coerce")
else:
    laps["lap_duration_num"] = pd.NA

stints = pd.DataFrame(get_json(f"stints?session_key={session_key}&driver_number={driver_number}"))
positions = pd.DataFrame(get_json(f"positions?session_key={session_key}"))
drivers_full = pd.DataFrame(drivers_data)

# -----------------------------
# Core Metrics (safe)
# -----------------------------
current_lap = laps.iloc[-1]
previous_lap = laps.iloc[-2] if len(laps) > 1 else None
current_lap_number = int(current_lap["lap_number"])

valid_laps = laps[laps["lap_duration_num"].notna()].copy()
if valid_laps.empty:
    best_lap = None
    best_lap_number = None
else:
    best_lap = valid_laps.loc[valid_laps["lap_duration_num"].idxmin()]
    best_lap_number = int(best_lap["lap_number"])

# -----------------------------
# Tire Logic (safe)
# -----------------------------
current_tire = "-"
best_lap_tire = "-"

if not stints.empty and all(c in stints.columns for c in ["lap_start", "lap_end", "compound"]):
    current_stint = stints[(stints.lap_start <= current_lap_number) & (stints.lap_end >= current_lap_number)]
    if not current_stint.empty:
        current_tire = current_stint.iloc[0].get("compound", "-")

    if best_lap_number is not None:
        best_stint = stints[(stints.lap_start <= best_lap_number) & (stints.lap_end >= best_lap_number)]
        if not best_stint.empty:
            best_lap_tire = best_stint.iloc[0].get("compound", "-")

# -----------------------------
# Position & Gaps (safe + ahead/behind names)
# -----------------------------
driver_ahead = "-"
driver_behind = "-"
gap_ahead = "-"
gap_behind = "-"
gap_leader = "-"

# Positions can vary by session; handle missing columns gracefully.
if not positions.empty and "driver_number" in positions.columns:
    # Use 'date' if present, otherwise just last rows
    if "date" in positions.columns:
        pos_latest = positions.sort_values("date").tail(40)
    else:
        pos_latest = positions.tail(40)

    if "position" in pos_latest.columns:
        # pick the most recent snapshot per driver (so duplicates don't confuse)
        if "date" in pos_latest.columns:
            pos_latest = pos_latest.sort_values("date")
            pos_latest = pos_latest.groupby("driver_number").tail(1)
        else:
            pos_latest = pos_latest.groupby("driver_number").tail(1)

        pos_latest = pos_latest.sort_values("position")

        me = pos_latest[pos_latest["driver_number"] == driver_number]
        if not me.empty:
            my_pos = int(me.iloc[0].get("position", 0))
            gap_leader = me.iloc[0].get("gap_to_leader", "-")

            ahead = pos_latest[pos_latest["position"] == my_pos - 1]
            behind = pos_latest[pos_latest["position"] == my_pos + 1]

            def acronym_for(num):
                try:
                    row = drivers_full[drivers_full["driver_number"] == num]
                    if not row.empty:
                        return row.iloc[0].get("name_acronym", str(num))
                except:
                    pass
                return str(num)

            if not ahead.empty:
                ahead_num = int(ahead.iloc[0]["driver_number"])
                driver_ahead = acronym_for(ahead_num)
                # interval meaning varies; still display if present
                gap_ahead = me.iloc[0].get("interval", "-")

            if not behind.empty:
                behind_num = int(behind.iloc[0]["driver_number"])
                driver_behind = acronym_for(behind_num)
                # behind interval sometimes not available; show if present on behind row
                gap_behind = behind.iloc[0].get("interval", "-")

# -----------------------------
# Layout – Mobile-first stacked
# -----------------------------
st.subheader("⏱ Lap Times")
st.metric("Current Lap", format_lap_time(current_lap.get("lap_duration_num")))
st.metric("Previous Lap", format_lap_time(previous_lap.get("lap_duration_num")) if previous_lap is not None else "--")

if best_lap is not None:
    st.metric("Best Lap", f"{format_lap_time(best_lap.get('lap_duration_num'))} (Lap {best_lap_number})")
    st.markdown(
        f"🏁 Best Lap Tire: <span style='color:{tire_color(best_lap_tire)}'>{best_lap_tire}</span>",
        unsafe_allow_html=True
    )
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

chart_data = laps.dropna(subset=["lap_duration_num"])
if not chart_data.empty:
    fig = px.line(chart_data, x="lap_number", y="lap_duration_num", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No valid lap durations available to chart.")

# -----------------------------
# Race Progress
# -----------------------------
if session_data:
    total_laps = session_data[0].get("total_laps", 0)
    if total_laps:
        st.subheader("🏁 Race Progress")
        st.progress(min(current_lap_number / total_laps, 1.0))
        st.write(f"Lap {current_lap_number} / {total_laps}")

# -----------------------------
# Auto Refresh
# -----------------------------
if auto_refresh:
    time.sleep(5)
    st.rerun()
