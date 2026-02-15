import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
import math
import os
import textwrap

st.set_page_config(layout="wide")

OPENF1_BASE = "https://api.openf1.org/v1"

# -----------------------------
# TV Broadcast Styling (Mobile-first, True Black + less padding)
# -----------------------------
st.markdown("""
<style>
:root{
  --bg: #000000;                 /* TRUE BLACK */
  --panel: rgba(255,255,255,0.07);
  --panel2: rgba(255,255,255,0.10);
  --border: rgba(255,255,255,0.16);
  --text: #F8FAFC;
  --muted: #C7D0DB;
  --muted2: #95A3B5;
  --shadow: 0 14px 28px rgba(0,0,0,0.65);
  --red: #E10600;
}

/* Force the whole Streamlit app to be black (fixes white/blank areas) */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stToolbar"]{
  background: var(--bg) !important;
}

/* Reduce Streamlit default top padding (fixes large top whitespace) */
.block-container{
  padding-top: 0.75rem !important;
  padding-bottom: 1.25rem !important;
}

html, body, [class*="css"] {
  background-color: var(--bg) !important;
  color: var(--text) !important;
}

/* Hide Streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.container { width: 100%; max-width: 1100px; margin: 0 auto; }

/* Header */
.appTitleText {
  font-size: 30px;
  font-weight: 900;
  letter-spacing: 0.6px;
  color: var(--text);
  text-shadow: 0 2px 10px rgba(0,0,0,0.65);
  line-height: 1.05;
}
.appSubtitle {
  font-size: 13px;
  color: var(--muted2);
  margin-top: 4px;
}

/* Broadcast bar */
.topbar {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 12px;
  padding: 12px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(18,22,28,0.96), rgba(5,7,10,0.96));
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
}

.leftBlock { display: grid; grid-template-columns: 92px 1fr; gap: 12px; align-items: center; }

.driverBadge {
  width: 92px; height: 92px; border-radius: 16px;
  background: rgba(255,255,255,0.10);
  border: 1px solid var(--border);
  display:flex; flex-direction:column; justify-content:center; align-items:center;
  position: relative; overflow: hidden;
}

.teamStripe { position:absolute; top:0; left:0; right:0; height: 10px; opacity: 1; }

.acr {
  font-size: 26px; font-weight: 900; letter-spacing: 1px;
  color: var(--text); text-shadow: 0 2px 10px rgba(0,0,0,0.65);
}
.num {
  margin-top: 2px; font-size: 14px; color: var(--muted); font-weight: 800;
  text-shadow: 0 2px 10px rgba(0,0,0,0.65);
}

.driverMeta { display:flex; flex-direction:column; gap: 8px; }
.raceLine { display:flex; flex-wrap: wrap; gap: 10px; align-items: center; font-size: 12px; color: var(--muted); }

.pill {
  padding: 7px 11px; border-radius: 999px;
  background: rgba(255,255,255,0.10);
  border: 1px solid rgba(255,255,255,0.16);
  color: var(--text); font-size: 12px; line-height: 1; white-space: nowrap;
  text-shadow: 0 2px 10px rgba(0,0,0,0.65);
}

.pillStrong {
  background: rgba(225,6,0,0.26);
  border: 1px solid rgba(225,6,0,0.50);
  color: var(--text);
  font-weight: 900;
}

.rightBlock { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.kpi {
  padding: 12px; border-radius: 16px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.16);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
}

.kpiLabel {
  font-size: 11px; letter-spacing: 0.6px; color: var(--muted2);
  margin-bottom: 6px; font-weight: 800; text-transform: uppercase;
}

.kpiValue {
  font-size: 18px; font-weight: 900; letter-spacing: 0.35px;
  color: var(--text); text-shadow: 0 2px 10px rgba(0,0,0,0.65);
}

.small-note { color: var(--muted); font-size: 12px; margin-top: 4px; }

.card {
  padding: 12px; border-radius: 16px;
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.14);
}

.sectionTitle {
  font-weight: 900; letter-spacing: 0.4px;
  margin: 6px 0 10px 0; color: var(--text);
  text-shadow: 0 2px 10px rgba(0,0,0,0.65);
}

.tireDot {
  display:inline-block; width: 10px; height: 10px; border-radius: 999px;
  margin-right: 6px; transform: translateY(1px);
  box-shadow: 0 0 0 2px rgba(0,0,0,0.45);
}

/* Gaps */
.gapGrid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
.gapCell {
  padding: 12px; border-radius: 16px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
}
.gapDir { font-size: 12px; color: var(--muted); margin-bottom: 6px; font-weight: 800; }
.gapVal { font-size: 16px; font-weight: 900; color: var(--text); text-shadow: 0 2px 10px rgba(0,0,0,0.65); }

/* Top-10 ticker */
.tickerHeader{
  display:grid;
  grid-template-columns: 56px 70px 1fr 120px 110px;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 12px;
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.12);
  color: var(--muted2);
  font-size: 11px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.6px;
}
.tickerRow{
  display:grid;
  grid-template-columns: 56px 70px 1fr 120px 110px;
  gap: 8px;
  padding: 10px 10px;
  border-radius: 12px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.10);
  align-items:center;
}
.tickerRowHighlight{
  outline: 2px solid rgba(225,6,0,0.60);
  box-shadow: 0 0 0 3px rgba(225,6,0,0.15);
}
.posBox{
  display:flex; align-items:center; justify-content:center;
  font-weight: 900;
  border-radius: 10px;
  padding: 6px 8px;
  background: rgba(225,6,0,0.18);
  border: 1px solid rgba(225,6,0,0.35);
}
.acrBox{
  font-weight: 900;
  letter-spacing: 0.8px;
}
.teamBar{
  width: 100%;
  height: 10px;
  border-radius: 999px;
  background: rgba(255,255,255,0.10);
  overflow:hidden;
  border: 1px solid rgba(255,255,255,0.12);
}
.teamFill{ height: 100%; width: 100%; }
.mono{
  font-variant-numeric: tabular-nums;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-weight: 800;
}
.rightAlign{ text-align:right; }

/* Stint timeline */
.timelineWrap{
  width:100%;
  border-radius: 14px;
  padding: 10px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.10);
}
.timelineBar{
  width:100%;
  height: 18px;
  border-radius: 999px;
  overflow:hidden;
  display:flex;
  border: 1px solid rgba(255,255,255,0.14);
  background: rgba(255,255,255,0.06);
}
.stintSeg{
  height: 100%;
  display:flex;
  align-items:center;
  justify-content:center;
  font-size: 11px;
  font-weight: 900;
}
.timelineMeta{
  display:flex;
  justify-content:space-between;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 8px;
  color: var(--muted);
  font-size: 12px;
}

@media (max-width: 920px) {
  .topbar { grid-template-columns: 1fr; }
  .rightBlock { grid-template-columns: 1fr 1fr; }
  .gapGrid { grid-template-columns: 1fr; }
  .tickerHeader, .tickerRow { grid-template-columns: 56px 66px 1fr 110px 90px; }
}
@media (max-width: 520px) {
  .appTitleText { font-size: 26px; }
  .tickerHeader, .tickerRow { grid-template-columns: 52px 60px 1fr 92px 72px; }
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
    """mm.ss.sss (preferred)"""
    try:
        if value is None:
            return "--"
        sec = float(value)
        if math.isnan(sec) or sec <= 0:
            return "--"
        minutes = int(sec // 60)
        sec -= minutes * 60
        return f"{minutes:02d}m.{sec:06.3f}s"
    except:
        return "--"

def tire_color(compound: str):
    colors = {
        "SOFT":"#ff2e2e",
        "MEDIUM":"#ffd800",
        "HARD":"#ffffff",
        "INTERMEDIATE":"#00ff66",
        "WET":"#0099ff"
    }
    return colors.get((compound or "").upper(), "#aaaaaa")

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
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font=dict(color="#F8FAFC"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.10)", zerolinecolor="rgba(255,255,255,0.10)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.10)", zerolinecolor="rgba(255,255,255,0.10)"),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig

# -----------------------------
# App Header (logo bigger + tighter)
# -----------------------------
st.markdown("<div class='container'>", unsafe_allow_html=True)

logo_path_candidates = [
    "2026 F1 logo.png",
    "assets/2026 F1 logo.png",
    "images/2026 F1 logo.png",
]
logo_path = next((p for p in logo_path_candidates if os.path.exists(p)), None)

col_logo, col_title = st.columns([1.3, 8], vertical_alignment="center")
with col_logo:
    if logo_path:
        st.image(logo_path, width=130)   # bigger logo
    else:
        st.markdown(
            "<div style='width:130px;height:62px;border:1px solid rgba(255,255,255,0.14);"
            "border-radius:12px;display:flex;align-items:center;justify-content:center;"
            "color:#F8FAFC;font-weight:900;'>F1</div>",
            unsafe_allow_html=True,
        )

with col_title:
    st.markdown("""
    <div class="appTitleText">
        F1 LIVE ANALYTICS <span style="color:#E10600;">BY MPH</span>
    </div>
    <div class="appSubtitle">
        Season → Race → Session • Broadcast Style Dashboard
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# 1) Season → 2) Race Weekend → 3) Session selector
# -----------------------------
@st.cache_data(ttl=6*60*60)
def load_meetings():
    return pd.DataFrame(get_json("meetings"))

@st.cache_data(ttl=6*60*60)
def load_sessions_for_meeting(meeting_key: int):
    return pd.DataFrame(get_json(f"sessions?meeting_key={meeting_key}"))

meetings = load_meetings()
if meetings.empty or "year" not in meetings.columns:
    st.error("Could not load meetings from OpenF1.")
    st.stop()

years = sorted(meetings["year"].dropna().unique().tolist(), reverse=True)
sel_year = st.selectbox("Season (Year)", years, index=0)

meetings_y = meetings[meetings["year"] == sel_year].copy()
if "date_start" in meetings_y.columns:
    meetings_y = meetings_y.sort_values("date_start")

def meeting_label(row):
    name = row.get("meeting_official_name") or row.get("meeting_name") or "Unknown"
    loc = row.get("location") or ""
    return f"{name} — {loc}".strip(" —")

meeting_options = {
    meeting_label(r): int(r["meeting_key"])
    for _, r in meetings_y.iterrows()
    if pd.notna(r.get("meeting_key"))
}

sel_meeting_label = st.selectbox("Race Weekend (Meeting)", list(meeting_options.keys()))
sel_meeting_key = meeting_options[sel_meeting_label]

sessions_df = load_sessions_for_meeting(sel_meeting_key)
if sessions_df.empty:
    st.error("No sessions returned for that meeting.")
    st.stop()

if "date_start" in sessions_df.columns:
    sessions_df = sessions_df.sort_values("date_start")

def session_label(row):
    name = row.get("session_name") or "Session"
    dt = row.get("date_start")
    dt_short = dt[:16].replace("T", " ") if isinstance(dt, str) else ""
    return f"{name} ({dt_short} UTC)" if dt_short else name

session_options = {
    session_label(r): int(r["session_key"])
    for _, r in sessions_df.iterrows()
    if pd.notna(r.get("session_key"))
}

sel_session_label = st.selectbox("Session", list(session_options.keys()))
session_key = session_options[sel_session_label]

auto_refresh = st.toggle("Auto Refresh (5s)", value=True)

# -----------------------------
# Pull selected session info
# -----------------------------
session_data = get_json(f"sessions?session_key={session_key}")
session_name = safe_str(session_data[0].get("session_name")) if session_data else safe_str(sel_session_label)
location = safe_str(session_data[0].get("location")) if session_data else safe_str(sel_meeting_label)
total_laps = session_data[0].get("total_laps", 0) if session_data else 0

# -----------------------------
# Driver Selection (for this session)
# -----------------------------
drivers_data = get_json(f"drivers?session_key={session_key}")
if not drivers_data:
    st.error("No drivers found for this session.")
    st.stop()

drivers_full = pd.DataFrame(drivers_data)

driver_map = {}
for d in drivers_data:
    dn = d.get("driver_number")
    acr = d.get("name_acronym", "?")
    if dn is not None:
        driver_map[f"{acr} ({dn})"] = int(dn)

selected_driver = st.selectbox("Driver", list(driver_map.keys()))
driver_number = driver_map[selected_driver]

# -----------------------------
# Load Laps + Stints
# -----------------------------
laps = pd.DataFrame(get_json(f"laps?session_key={session_key}&driver_number={driver_number}"))
if laps.empty or "lap_number" not in laps.columns:
    st.warning("No lap data available for this driver/session.")
    st.stop()

laps = laps.sort_values("lap_number")

if "lap_duration" in laps.columns:
    laps["lap_duration_num"] = pd.to_numeric(laps["lap_duration"], errors="coerce")
elif "lap_time" in laps.columns:
    laps["lap_duration_num"] = pd.to_numeric(laps["lap_time"], errors="coerce")
else:
    laps["lap_duration_num"] = pd.NA

stints = pd.DataFrame(get_json(f"stints?session_key={session_key}&driver_number={driver_number}"))

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

# Tires (current + best lap tire)
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

# Driver identity / team color
me_driver = drivers_full[drivers_full["driver_number"] == driver_number]
acr = safe_str(me_driver.iloc[0].get("name_acronym")) if not me_driver.empty else "DRV"
team = safe_str(me_driver.iloc[0].get("team_name")) if (not me_driver.empty and "team_name" in me_driver.columns) else "-"
team_colour = normalize_hex_color(me_driver.iloc[0].get("team_colour")) if (not me_driver.empty and "team_colour" in me_driver.columns) else "#888888"
full_name = safe_str(me_driver.iloc[0].get("full_name")) if (not me_driver.empty and "full_name" in me_driver.columns) else acr

# -----------------------------
# GAPS via /intervals (leader/ahead/behind)
# -----------------------------
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
    if "date" in intervals.columns:
        snap = intervals.sort_values("date").groupby("driver_number").tail(1)
    else:
        snap = intervals.groupby("driver_number").tail(1)

    positions = pd.DataFrame(get_json(f"positions?session_key={session_key}"))
    if not positions.empty and "driver_number" in positions.columns and "position" in positions.columns:
        if "date" in positions.columns:
            pos_snap = positions.sort_values("date").groupby("driver_number").tail(1)
        else:
            pos_snap = positions.groupby("driver_number").tail(1)

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
                    driver_ahead = acronym_for(int(ahead.iloc[0]["driver_number"]))

                if not behind.empty:
                    driver_behind = acronym_for(int(behind.iloc[0]["driver_number"]))
                    gap_behind = safe_str(behind.iloc[0].get("interval"), "--")

# -----------------------------
# Stint timeline (FIX: no indentation -> no code block)
# -----------------------------
def stint_timeline_html(stints_df: pd.DataFrame, total_laps_hint: int):
    if stints_df.empty or not all(c in stints_df.columns for c in ["lap_start", "lap_end", "compound"]):
        return "<div class='timelineWrap'><div class='timelineMeta'>No stint data available.</div></div>"

    df = stints_df.sort_values("lap_start").copy()

    if total_laps_hint and isinstance(total_laps_hint, (int, float)) and total_laps_hint > 0:
        total = int(total_laps_hint)
    else:
        total = int(max(df["lap_end"].max(), current_lap_number))

    segs = []
    meta_bits = []

    for _, r in df.iterrows():
        ls = int(r["lap_start"])
        le = int(r["lap_end"])
        comp = safe_str(r["compound"], "-").upper()
        color = tire_color(comp)

        length = max(le - ls + 1, 1)
        w = (length / total) * 100.0

        short = comp[:1]
        if comp == "INTERMEDIATE":
            short = "I"
        if comp == "WET":
            short = "W"

        # Text color for legibility
        text_color = "#000000"
        if comp in ["SOFT", "WET"]:
            text_color = "#FFFFFF"

        segs.append(
            f"<div class='stintSeg' style='width:{w:.2f}%; background:{color}; color:{text_color};'>{short}</div>"
        )
        meta_bits.append(f"{comp} L{ls}–L{le}")

    left = " • ".join(meta_bits[:3])
    right = " • ".join(meta_bits[3:])

    html = f"""
<div class="timelineWrap">
  <div class="timelineBar">{''.join(segs)}</div>
  <div class="timelineMeta">
    <div>{left}</div>
    <div>{right}</div>
  </div>
</div>
"""
    return textwrap.dedent(html).strip()

# -----------------------------
# Top-10 ticker
# -----------------------------
def build_latest_snapshots_for_ticker():
    positions = pd.DataFrame(get_json(f"positions?session_key={session_key}"))
    intervals2 = pd.DataFrame(get_json(f"intervals?session_key={session_key}"))

    if positions.empty or "driver_number" not in positions.columns or "position" not in positions.columns:
        return pd.DataFrame()

    if "date" in positions.columns:
        pos_snap = positions.sort_values("date").groupby("driver_number").tail(1)
    else:
        pos_snap = positions.groupby("driver_number").tail(1)

    if not intervals2.empty and "driver_number" in intervals2.columns:
        if "date" in intervals2.columns:
            int_snap = intervals2.sort_values("date").groupby("driver_number").tail(1)
        else:
            int_snap = intervals2.groupby("driver_number").tail(1)
        keep_cols = [c for c in ["driver_number", "gap_to_leader", "interval"] if c in int_snap.columns]
        merged = pos_snap.merge(int_snap[keep_cols], on="driver_number", how="left")
    else:
        merged = pos_snap.copy()
        merged["gap_to_leader"] = pd.NA
        merged["interval"] = pd.NA

    cols_needed = ["driver_number", "name_acronym", "team_colour", "team_name"]
    if all(c in drivers_full.columns for c in cols_needed):
        merged = merged.merge(drivers_full[cols_needed], on="driver_number", how="left")
    else:
        merged = merged.merge(drivers_full, on="driver_number", how="left")

    return merged

ticker_df = build_latest_snapshots_for_ticker()
top10 = ticker_df.sort_values("position").head(10).copy() if not ticker_df.empty else pd.DataFrame()

# -----------------------------
# Render broadcast header
# -----------------------------
cur_time_str = format_lap_time(current_lap.get("lap_duration_num"))
prev_time_str = format_lap_time(previous_lap.get("lap_duration_num")) if previous_lap is not None else "--"
best_time_str = format_lap_time(best_lap.get("lap_duration_num")) if best_lap is not None else "--"

pos_pill = f"P{my_pos}" if my_pos is not None else "P-"
lap_pill = f"LAP {current_lap_number}/{total_laps}" if total_laps else f"LAP {current_lap_number}"

current_tire_dot = tire_color(current_tire)
best_tire_dot = tire_color(best_lap_tire)

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
        <span class="pill"><span class="tireDot" style="background:{current_tire_dot};"></span>Current Tire: <b>{safe_str(current_tire)}</b></span>
        <span class="pill"><span class="tireDot" style="background:{best_tire_dot};"></span>Best Lap Tire: <b>{safe_str(best_lap_tire)}</b></span>
      </div>
      <div class="raceLine">
        <span class="pill">Leader: <b>{safe_str(gap_leader, "--")}</b></span>
        <span class="pill">⬆ {safe_str(driver_ahead, "-")}: <b>{safe_str(gap_ahead, "--")}</b></span>
        <span class="pill">⬇ {safe_str(driver_behind, "-")}: <b>{safe_str(gap_behind, "--")}</b></span>
      </div>
    </div>
  </div>

  <div class="rightBlock">
    <div class="kpi"><div class="kpiLabel">Current Lap</div><div class="kpiValue">{cur_time_str}</div></div>
    <div class="kpi"><div class="kpiLabel">Previous Lap</div><div class="kpiValue">{prev_time_str}</div></div>
    <div class="kpi"><div class="kpiLabel">Best Lap</div><div class="kpiValue">{best_time_str}</div><div class="small-note">Lap {best_lap_number if best_lap_number is not None else "--"}</div></div>
    <div class="kpi"><div class="kpiLabel">Driver</div><div class="kpiValue">{safe_str(full_name, acr)}</div><div class="small-note">{safe_str(team)}</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

# Gaps
st.markdown(f"""
<div class="card" style="margin-top:12px;">
  <div class="sectionTitle">📏 Gaps</div>
  <div class="gapGrid">
    <div class="gapCell"><div class="gapDir">To Leader</div><div class="gapVal">{safe_str(gap_leader, "--")}</div></div>
    <div class="gapCell"><div class="gapDir">⬆ {safe_str(driver_ahead, "-")}</div><div class="gapVal">{safe_str(gap_ahead, "--")}</div></div>
    <div class="gapCell"><div class="gapDir">⬇ {safe_str(driver_behind, "-")}</div><div class="gapVal">{safe_str(gap_behind, "--")}</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

# Stint timeline (FIXED)
timeline_html = stint_timeline_html(stints, int(total_laps) if total_laps else 0)
st.markdown(f"""
<div class="card" style="margin-top:12px;">
  <div class="sectionTitle">🛞 Stint Timeline</div>
  {timeline_html}
</div>
""", unsafe_allow_html=True)

# Top-10 leaderboard
st.markdown("<div class='card' style='margin-top:12px;'>", unsafe_allow_html=True)
st.markdown("<div class='sectionTitle'>🏁 Top 10 Leaderboard</div>", unsafe_allow_html=True)

if top10.empty:
    st.info("Top-10 data not available for this session (positions snapshot missing).")
else:
    st.markdown("""
    <div class="tickerHeader">
      <div class="rightAlign">POS</div>
      <div>DRIVER</div>
      <div>TEAM</div>
      <div class="rightAlign">GAP</div>
      <div class="rightAlign">INT</div>
    </div>
    """, unsafe_allow_html=True)

    for _, r in top10.iterrows():
        pos = int(r.get("position")) if pd.notna(r.get("position")) else "-"
        dnum = r.get("driver_number")
        acr2 = safe_str(r.get("name_acronym"), str(dnum))
        team_name2 = safe_str(r.get("team_name"), "-")
        team_col2 = normalize_hex_color(r.get("team_colour"))
        gap2 = safe_str(r.get("gap_to_leader"), "--")
        itv2 = safe_str(r.get("interval"), "--")

        highlight_class = "tickerRow tickerRowHighlight" if int(dnum) == int(driver_number) else "tickerRow"

        st.markdown(f"""
        <div class="{highlight_class}">
          <div class="posBox">{pos}</div>
          <div class="acrBox">{acr2}</div>
          <div>
            <div class="teamBar"><div class="teamFill" style="background:{team_col2};"></div></div>
            <div style="margin-top:6px; color: var(--muted); font-size:12px;">{team_name2}</div>
          </div>
          <div class="mono rightAlign">{gap2}</div>
          <div class="mono rightAlign">{itv2}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Lap trend chart
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

# Race progress
if total_laps:
    st.markdown("<div class='card' style='margin-top:12px;'><div class='sectionTitle'>🏁 Race Progress</div></div>",
                unsafe_allow_html=True)
    st.progress(min(current_lap_number / total_laps, 1.0))
    st.caption(f"Lap {current_lap_number} / {total_laps}")

st.markdown("</div>", unsafe_allow_html=True)  # end container

# Auto refresh
if auto_refresh:
    time.sleep(5)
    st.rerun()
