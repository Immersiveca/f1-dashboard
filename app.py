import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
import math

st.set_page_config(layout="wide")

OPENF1_BASE = "https://api.openf1.org/v1"

# -----------------------------
# TV Broadcast Styling (Mobile-first, High Contrast)
# -----------------------------
st.markdown("""
<style>
:root{
  --bg: #0B0F14;
  --panel: rgba(255,255,255,0.06);
  --panel-strong: rgba(255,255,255,0.10);
  --border: rgba(255,255,255,0.14);
  --text: #F5F7FA;
  --muted: #B6C0CC;
  --muted2: #8E9AA8;
  --shadow: 0 14px 28px rgba(0,0,0,0.45);
}

html, body, [class*="css"] {
  background-color: var(--bg) !important;
  color: var(--text) !important;
}

/* Clean “broadcast” look */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.container { width: 100%; max-width: 980px; margin: 0 auto; }

.topbar {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 12px;
  padding: 12px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(24,30,38,0.96), rgba(12,16,22,0.96));
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
}

.leftBlock { display: grid; grid-template-columns: 92px 1fr; gap: 12px; align-items: center; }

.driverBadge {
  width: 92px; height: 92px; border-radius: 16px;
  background: rgba(255,255,255,0.08);
  border: 1px solid var(--border);
  display:flex; flex-direction:column; justify-content:center; align-items:center;
  position: relative; overflow: hidden;
}

.teamStripe { position:absolute; top:0; left:0; right:0; height: 10px; opacity: 1; }

.acr {
  font-size: 26px; font-weight: 900; letter-spacing: 1px;
  color: var(--text); text-shadow: 0 2px 10px rgba(0,0,0,0.55);
}
.num {
  margin-top: 2px; font-size: 14px; color: var(--muted); font-weight: 800;
  text-shadow: 0 2px 10px rgba(0,0,0,0.55);
}

.driverMeta { display:flex; flex-direction:column; gap: 8px; }

.raceLine { display:flex; flex-wrap: wrap; gap: 10px; align-items: center; font-size: 12px; color: var(--muted); }

.pill {
  padding: 7px 11px; border-radius: 999px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.14);
  color: var(--text); font-size: 12px; line-height: 1; white-space: nowrap;
  text-shadow: 0 2px 10px rgba(0,0,0,0.55);
}

.pillStrong {
  background: rgba(225,6,0,0.24);
  border: 1px solid rgba(225,6,0,0.44);
  color: var(--text);
  font-weight: 900;
}

.rightBlock { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.kpi {
  padding: 12px; border-radius: 16px;
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.14);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
}

.kpiLabel {
  font-size: 11px; letter-spacing: 0.6px; color: var(--muted2);
  margin-bottom: 6px; font-weight: 800; text-transform: uppercase;
}

.kpiValue {
  font-size: 18px; font-weight: 900; letter-spacing: 0.35px;
  color: var(--text); text-shadow: 0 2px 10px rgba(0,0,0,0.55);
}

.small-note { color: var(--muted); font-size: 12px; margin-top: 4px; }

.card {
  padding: 12px; border-radius: 16px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
}

.sectionTitle {
  font-weight: 900; letter-spacing: 0.4px;
  margin: 8px 0 10px 0; color: var(--text);
  text-shadow: 0 2px 10px rgba(0,0,0,0.55);
}

.tireDot {
  display:inline-block; width: 10px; height: 10px; border-radius: 999px;
  margin-right: 6px; transform: translateY(1px);
  box-shadow: 0 0 0 2px rgba(0,0,0,0.35);
}

.gapGrid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }

.gapCell {
  padding: 12px; border-radius: 16px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
}

.gapDir { font-size: 12px; color: var(--muted); margin-bottom: 6px; font-weight: 800; }
.gapVal { font-size: 16px; font-weight: 900; color: var(--text); text-shadow: 0 2px 10px rgba(0,0,0,0.55); }

@media (max-width: 720px) {
  .topbar { grid-template-columns: 1fr; }
  .rightBlock { grid-template-columns: 1fr 1fr; }
  .gapGrid { grid-template-columns: 1fr; }
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
    """00H.00M.00.000S; '--' for invalid"""
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
        return f"{minutes:02d}m.{sec:06.3f}s"
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

def safe_str(x, default="-"):
    if x is None:
        return default
    if isinstance(x, float) and math.isnan(x):
        return default
    s = str(x).strip()
    return s if s else default

def normalize_hex_color(c):
    c = safe_str(c, "")
    if not c:
        return "#888888"
    c = c.replace("#", "").strip()
    if len(c) == 6 and all(ch in "0123456789ABCDEFabcdef" for ch in c):
        return "#" + c.upper()
    return "#888888"

def plotly_force_dark(fig):
    """Force dark chart even if Streamlit theme is light."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0B0F14",
        plot_bgcolor="#0B0F14",
        font=dict(color="#F5F7FA"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.10)", zerolinecolor="rgba(255,255,255,0.10)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.10)", zerolinecolor="rgba(255,255,255,0.10)"),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig

# -----------------------------
# Header + Controls
# -----------------------------
st.title("🏎 F1 LIVE ANALYTICS BY MPH")

session_key = st.number_input("Session Key", value=9222)

session_data = get_json(f"sessions?session_key={session_key}")
session_name = safe_str(session_data[0].get("session_name")) if session_data else "-"
location = safe_str(session_data[0].get("location")) if session_data else "-"
total_laps = session_data[0].get("total_laps", 0) if session_data else 0

drivers_data = get_json(f"drivers?session_key={session_key}")
if not drivers_data:
    st.error("No drivers found for this session key. Try another session key.")
    st.stop()

driver_map = {}
for d in drivers_data:
    dn = d.get("driver_number")
    acr = d.get("name_acronym", "?")
    if dn is not None:
        driver_map[f"{acr} ({dn})"] = int(dn)

selected_driver = st.selectbox("Select Driver", list(driver_map.keys()))
driver_number = driver_map[selected_driver]

auto_refresh = st.toggle("Auto Refresh (5s)", value=True)

drivers_full = pd.DataFrame(drivers_data)

# -----------------------------
# Load Laps + Stints
# -----------------------------
laps = pd.DataFrame(get_json(f"laps?session_key={session_key}&driver_number={driver_number}"))
if laps.empty or "lap_number" not in laps.columns:
    st.warning("No lap data available for this driver/session.")
    st.stop()

laps = laps.sort_values("lap_number")

# Bulletproof numeric duration
if "lap_duration" in laps.columns:
    laps["lap_duration_num"] = pd.to_numeric(laps["lap_duration"], errors="coerce")
elif "lap_time" in laps.columns:
    laps["lap_duration_num"] = pd.to_numeric(laps["lap_time"], errors="coerce")
else:
    laps["lap_duration_num"] = pd.NA

stints = pd.DataFrame(get_json(f"stints?session_key={session_key}&driver_number={driver_number}"))

# Core lap metrics
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

# Tires
current_tire = "-"
best_lap_tire = "-"
if not stints.empty and all(c in stints.columns for c in ["lap_start", "lap_end", "compound"]):
    cur = stints[(stints.lap_start <= current_lap_number) & (stints.lap_end >= current_lap_number)]
    if not cur.empty:
        current_tire = safe_str(cur.iloc[0].get("compound"))
    if best_lap_number is not None:
        bl = stints[(stints.lap_start <= best_lap_number) & (stints.lap_end >= best_lap_number)]
        if not bl.empty:
            best_lap_tire = safe_str(bl.iloc[0].get("compound"))

# -----------------------------
# Driver identity (team colors if available)
# -----------------------------
me_driver = drivers_full[drivers_full["driver_number"] == driver_number]
acr = safe_str(me_driver.iloc[0].get("name_acronym")) if not me_driver.empty else "DRV"
team = safe_str(me_driver.iloc[0].get("team_name")) if (not me_driver.empty and "team_name" in me_driver.columns) else "-"
team_colour = normalize_hex_color(me_driver.iloc[0].get("team_colour")) if (not me_driver.empty and "team_colour" in me_driver.columns) else "#888888"
full_name = safe_str(me_driver.iloc[0].get("full_name")) if (not me_driver.empty and "full_name" in me_driver.columns) else acr

# -----------------------------
# GAPS (FIXED) – use /intervals (purpose-built)
# -----------------------------
# intervals provides:
# - gap_to_leader (selected driver to leader)
# - interval (selected driver to car ahead)
# For gap to behind: use the behind driver's interval to its ahead (which is our driver).
intervals = pd.DataFrame(get_json(f"intervals?session_key={session_key}"))

driver_ahead = "-"
driver_behind = "-"
gap_ahead = "--"
gap_behind = "--"
gap_leader = "--"
my_pos = None

def acronym_for(num):
    row = drivers_full[drivers_full["driver_number"] == num]
    if not row.empty:
        return safe_str(row.iloc[0].get("name_acronym"), str(num))
    return str(num)

if not intervals.empty and "driver_number" in intervals.columns:
    # Use the latest snapshot per driver (most recent 'date' if present)
    if "date" in intervals.columns:
        snap = intervals.sort_values("date").groupby("driver_number").tail(1)
    else:
        snap = intervals.groupby("driver_number").tail(1)

    # We still need position ordering to know who is ahead/behind.
    # We'll combine with positions snapshot for ordering.
    positions = pd.DataFrame(get_json(f"positions?session_key={session_key}"))

    if not positions.empty and "driver_number" in positions.columns and "position" in positions.columns:
        if "date" in positions.columns:
            pos_snap = positions.sort_values("date").groupby("driver_number").tail(1)
        else:
            pos_snap = positions.groupby("driver_number").tail(1)

        # Merge to get (driver_number, position, gap_to_leader, interval)
        merged = pos_snap[["driver_number", "position"]].merge(
            snap[[c for c in snap.columns if c in ["driver_number", "gap_to_leader", "interval"]]],
            on="driver_number",
            how="left"
        ).sort_values("position")

        me = merged[merged["driver_number"] == driver_number]
        if not me.empty:
            my_pos = int(me.iloc[0]["position"]) if pd.notna(me.iloc[0]["position"]) else None
            gap_leader = safe_str(me.iloc[0].get("gap_to_leader"), "--")
            gap_ahead = safe_str(me.iloc[0].get("interval"), "--")

            if my_pos is not None:
                ahead = merged[merged["position"] == my_pos - 1]
                behind = merged[merged["position"] == my_pos + 1]

                if not ahead.empty:
                    ahead_num = int(ahead.iloc[0]["driver_number"])
                    driver_ahead = acronym_for(ahead_num)

                if not behind.empty:
                    behind_num = int(behind.iloc[0]["driver_number"])
                    driver_behind = acronym_for(behind_num)
                    # Behind gap to us = behind driver's interval (to car ahead i.e. us)
                    gap_behind = safe_str(behind.iloc[0].get("interval"), "--")

# -----------------------------
# TV-style Header (Broadcast Lower Third)
# -----------------------------
cur_time_str = format_lap_time(current_lap.get("lap_duration_num"))
prev_time_str = format_lap_time(previous_lap.get("lap_duration_num")) if previous_lap is not None else "--"
best_time_str = format_lap_time(best_lap.get("lap_duration_num")) if best_lap is not None else "--"

pos_pill = f"P{my_pos}" if my_pos is not None else "P-"
lap_pill = f"LAP {current_lap_number}/{total_laps}" if total_laps else f"LAP {current_lap_number}"

current_tire_dot = tire_color(current_tire)
best_tire_dot = tire_color(best_lap_tire)

st.markdown("<div class='container'>", unsafe_allow_html=True)

st.markdown(f"""
<div class="topbar">
  <div class="leftBlock">
    <div class="driverBadge">
      <div class="teamStripe" style="background:{team_colour};"></div>
      <div class="acr">{acr}</div>
      <div class="num">#{driver_number}</div>
    </div>
    <div class="driverMeta">
      <div class="raceLine">
        <span class="pill pillStrong">{pos_pill}</span>
        <span class="pill">{lap_pill}</span>
        <span class="pill">{safe_str(location)} • {safe_str(session_name)}</span>
      </div>
      <div class="raceLine">
        <span class="pill">Team: <b>{safe_str(team)}</b></span>
        <span class="pill">
          <span class="tireDot" style="background:{current_tire_dot};"></span>
          Tire: <b>{safe_str(current_tire)}</b>
        </span>
        <span class="pill">
          <span class="tireDot" style="background:{best_tire_dot};"></span>
          Best tire: <b>{safe_str(best_lap_tire)}</b>
        </span>
      </div>
      <div class="raceLine">
        <span class="pill">Leader: <b>{safe_str(gap_leader, "--")}</b></span>
        <span class="pill">⬆ {safe_str(driver_ahead, "-")}: <b>{safe_str(gap_ahead, "--")}</b></span>
        <span class="pill">⬇ {safe_str(driver_behind, "-")}: <b>{safe_str(gap_behind, "--")}</b></span>
      </div>
    </div>
  </div>

  <div class="rightBlock">
    <div class="kpi">
      <div class="kpiLabel">Current Lap</div>
      <div class="kpiValue">{cur_time_str}</div>
    </div>
    <div class="kpi">
      <div class="kpiLabel">Previous Lap</div>
      <div class="kpiValue">{prev_time_str}</div>
    </div>
    <div class="kpi">
      <div class="kpiLabel">Best Lap</div>
      <div class="kpiValue">{best_time_str}</div>
      <div class="small-note">Lap {best_lap_number if best_lap_number is not None else "--"}</div>
    </div>
    <div class="kpi">
      <div class="kpiLabel">Driver</div>
      <div class="kpiValue">{safe_str(full_name, acr)}</div>
      <div class="small-note">{safe_str(team)}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Gaps Card (now correct)
# -----------------------------
st.markdown(f"""
<div class="card" style="margin-top:12px;">
  <div class="sectionTitle">📏 Gaps</div>
  <div class="gapGrid">
    <div class="gapCell">
      <div class="gapDir">To Leader</div>
      <div class="gapVal">{safe_str(gap_leader, "--")}</div>
    </div>
    <div class="gapCell">
      <div class="gapDir">⬆ {safe_str(driver_ahead, "-")}</div>
      <div class="gapVal">{safe_str(gap_ahead, "--")}</div>
    </div>
    <div class="gapCell">
      <div class="gapDir">⬇ {safe_str(driver_behind, "-")}</div>
      <div class="gapVal">{safe_str(gap_behind, "--")}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Lap Trend Chart (FORCED DARK)
# -----------------------------
st.markdown("<div class='card' style='margin-top:12px;'>", unsafe_allow_html=True)
st.markdown("<div class='sectionTitle'>📊 Lap Time Evolution</div>", unsafe_allow_html=True)

chart_data = laps.dropna(subset=["lap_duration_num"])
if not chart_data.empty:
    fig = px.line(chart_data, x="lap_number", y="lap_duration_num")
    fig = plotly_force_dark(fig)
    fig.update_layout(height=360)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No valid lap durations available to chart.")
st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Race Progress
# -----------------------------
if total_laps:
    st.markdown(f"<div class='card' style='margin-top:12px;'><div class='sectionTitle'>🏁 Race Progress</div></div>",
                unsafe_allow_html=True)
    st.progress(min(current_lap_number / total_laps, 1.0))
    st.caption(f"Lap {current_lap_number} / {total_laps}")

st.markdown("</div>", unsafe_allow_html=True)  # end container

# -----------------------------
# Auto Refresh
# -----------------------------
if auto_refresh:
    time.sleep(5)
    st.rerun()
