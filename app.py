import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
import math

st.set_page_config(layout="wide")

OPENF1_BASE = "https://api.openf1.org/v1"

# -----------------------------
# TV Broadcast Styling (Mobile-first)
# -----------------------------
st.markdown("""
<style>
html, body, [class*="css"] {
  background-color: #0B0F14;
  color: #EAECEF;
}

/* Hide Streamlit default menu/footer for a cleaner “broadcast” feel */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Layout helpers */
.container {
  width: 100%;
  max-width: 980px;
  margin: 0 auto;
}

.topbar {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 10px;
  padding: 10px;
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(20,26,33,0.95), rgba(14,18,24,0.95));
  border: 1px solid rgba(255,255,255,0.07);
  box-shadow: 0 12px 24px rgba(0,0,0,0.35);
}

.leftBlock {
  display: grid;
  grid-template-columns: 86px 1fr;
  gap: 10px;
  align-items: center;
}

.driverBadge {
  width: 86px;
  height: 86px;
  border-radius: 16px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.09);
  display:flex;
  flex-direction:column;
  justify-content:center;
  align-items:center;
  position: relative;
  overflow: hidden;
}

.teamStripe {
  position:absolute;
  top:0; left:0; right:0;
  height: 9px;
  opacity: 0.95;
}

.acr {
  font-size: 26px;
  font-weight: 800;
  letter-spacing: 1px;
  line-height: 1.0;
}
.num {
  margin-top: 2px;
  font-size: 14px;
  opacity: 0.9;
  font-weight: 700;
}

.driverMeta {
  display:flex;
  flex-direction:column;
  gap: 4px;
}

.raceLine {
  display:flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  font-size: 12px;
  opacity: 0.92;
}

.pill {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  font-size: 12px;
  line-height: 1;
  white-space: nowrap;
}

.pillStrong {
  background: rgba(225,6,0,0.16);
  border: 1px solid rgba(225,6,0,0.28);
  font-weight: 800;
}

.rightBlock {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.kpi {
  padding: 10px;
  border-radius: 14px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
}

.kpiLabel {
  font-size: 11px;
  opacity: 0.78;
  letter-spacing: 0.4px;
  margin-bottom: 4px;
}

.kpiValue {
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0.3px;
}

.subRow {
  margin-top: 10px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

.card {
  padding: 12px;
  border-radius: 14px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
}

.sectionTitle {
  font-weight: 800;
  letter-spacing: 0.4px;
  margin: 8px 0 10px 0;
}

.tireDot {
  display:inline-block;
  width: 10px;
  height: 10px;
  border-radius: 999px;
  margin-right: 6px;
  transform: translateY(1px);
}

.gapGrid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
}

.gapCell {
  padding: 10px;
  border-radius: 14px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
}

.gapDir {
  font-size: 12px;
  opacity: 0.85;
  margin-bottom: 4px;
  font-weight: 700;
}

.gapVal {
  font-size: 16px;
  font-weight: 900;
}

/* Mobile: stack topbar into single column */
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

def safe_str(x, default="-"):
    if x is None:
        return default
    if isinstance(x, float) and math.isnan(x):
        return default
    s = str(x).strip()
    return s if s else default

# Convert team colour (if given like "3671C6") -> "#3671C6"
def normalize_hex_color(c):
    c = safe_str(c, "")
    if not c:
        return "#888888"
    c = c.replace("#", "").strip()
    if len(c) == 6 and all(ch in "0123456789ABCDEFabcdef" for ch in c):
        return "#" + c.upper()
    return "#888888"

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

# -----------------------------
# Load Data
# -----------------------------
laps = pd.DataFrame(get_json(f"laps?session_key={session_key}&driver_number={driver_number}"))
if laps.empty:
    st.warning("No lap data available for this driver/session.")
    st.stop()

if "lap_number" not in laps.columns:
    st.error("Lap data does not contain lap_number. Can't build dashboard.")
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
positions = pd.DataFrame(get_json(f"positions?session_key={session_key}"))
drivers_full = pd.DataFrame(drivers_data)

# -----------------------------
# Driver identity (team colors)
# -----------------------------
me_driver = drivers_full[drivers_full["driver_number"] == driver_number]
acr = safe_str(me_driver.iloc[0].get("name_acronym")) if not me_driver.empty else "DRV"
team = safe_str(me_driver.iloc[0].get("team_name")) if (not me_driver.empty and "team_name" in me_driver.columns) else "-"
team_colour = normalize_hex_color(me_driver.iloc[0].get("team_colour")) if (not me_driver.empty and "team_colour" in me_driver.columns) else "#888888"
full_name = safe_str(me_driver.iloc[0].get("full_name")) if (not me_driver.empty and "full_name" in me_driver.columns) else acr

# -----------------------------
# Core Metrics
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
# Position & gaps + ahead/behind names (robust)
# -----------------------------
driver_ahead = "-"
driver_behind = "-"
gap_ahead = "-"
gap_behind = "-"
gap_leader = "-"
my_pos = None

if not positions.empty and "driver_number" in positions.columns:
    # Snapshot: most recent per driver
    if "date" in positions.columns:
        pos_latest = positions.sort_values("date").tail(80)
        pos_latest = pos_latest.sort_values("date").groupby("driver_number").tail(1)
    else:
        pos_latest = positions.tail(80).groupby("driver_number").tail(1)

    if "position" in pos_latest.columns:
        pos_latest = pos_latest.sort_values("position")
        me = pos_latest[pos_latest["driver_number"] == driver_number]
        if not me.empty:
            my_pos = int(me.iloc[0].get("position")) if pd.notna(me.iloc[0].get("position")) else None
            gap_leader = safe_str(me.iloc[0].get("gap_to_leader"), "-")
            # interval meaning varies by feed; show it as “Ahead gap” from my row if present
            gap_ahead = safe_str(me.iloc[0].get("interval"), "-")

            def acronym_for(num):
                row = drivers_full[drivers_full["driver_number"] == num]
                if not row.empty:
                    return safe_str(row.iloc[0].get("name_acronym"), str(num))
                return str(num)

            if my_pos is not None:
                ahead = pos_latest[pos_latest["position"] == my_pos - 1]
                behind = pos_latest[pos_latest["position"] == my_pos + 1]

                if not ahead.empty:
                    ahead_num = int(ahead.iloc[0]["driver_number"])
                    driver_ahead = acronym_for(ahead_num)

                if not behind.empty:
                    behind_num = int(behind.iloc[0]["driver_number"])
                    driver_behind = acronym_for(behind_num)
                    # behind interval is sometimes only present on behind row
                    gap_behind = safe_str(behind.iloc[0].get("interval"), "-")

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
      <div class="kpiLabel">CURRENT LAP</div>
      <div class="kpiValue">{cur_time_str}</div>
    </div>
    <div class="kpi">
      <div class="kpiLabel">PREVIOUS LAP</div>
      <div class="kpiValue">{prev_time_str}</div>
    </div>
    <div class="kpi">
      <div class="kpiLabel">BEST LAP</div>
      <div class="kpiValue">{best_time_str}</div>
      <div class="small-note">Lap {best_lap_number if best_lap_number is not None else "--"}</div>
    </div>
    <div class="kpi">
      <div class="kpiLabel">DRIVER</div>
      <div class="kpiValue">{safe_str(full_name, acr)}</div>
      <div class="small-note">{safe_str(team)}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Compact “TV Cards” below header
# -----------------------------
st.markdown("<div class='subRow'>", unsafe_allow_html=True)

st.markdown(f"""
<div class="card">
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

# Race progress
if total_laps:
    st.markdown(f"""
    <div class="card">
      <div class="sectionTitle">🏁 Race Progress</div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(min(current_lap_number / total_laps, 1.0))
    st.caption(f"Lap {current_lap_number} / {total_laps}")

st.markdown("</div>", unsafe_allow_html=True)  # end subRow

# -----------------------------
# Lap trend chart (broadcast dark)
# -----------------------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("<div class='sectionTitle'>📊 Lap Time Evolution</div>", unsafe_allow_html=True)

chart_data = laps.dropna(subset=["lap_duration_num"])
if not chart_data.empty:
    fig = px.line(chart_data, x="lap_number", y="lap_duration_num", template="plotly_dark")
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=360
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No valid lap durations available to chart.")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # end container

# -----------------------------
# Auto Refresh
# -----------------------------
if auto_refresh:
    time.sleep(5)
    st.rerun()
