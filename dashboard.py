import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title="Carrybee Intelligence",
    page_icon="🐝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════════
#  DESIGN TOKENS — White background, Golden Yellow accent system
# ═══════════════════════════════════════════════════════════════════
# Background   #FFFFFF  pure white page
# Surface/card #F0EDE5  warm white cards
# Navy         #1C2B3A  primary text, headers
# Gold         #F5C200  primary accent
# Teal         #2E7D6B  positive / data-series-2
# Coral        #E05C3A  negative / alert
# Slate        #6B7E91  muted / secondary text
# HiYellow     #FDF3BF  highlight backgrounds
# Active       #C99B00  pressed/active state
# DarkGold     #8A6A00  text on yellow surfaces

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700;800&family=DM+Mono:wght@400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; }
* { font-family: 'DM Sans', sans-serif; }

/* ── BASE ── */
[data-testid="stAppViewContainer"] { background: #FFFFFF !important; }
[data-testid="stHeader"]           { background: transparent !important; }
[data-testid="stToolbar"]          { display: none; }
[data-testid="stDecoration"]       { display: none; }
.block-container {
    padding-top: 1.1rem !important;
    padding-bottom: 2rem !important;
    max-width: 100% !important;
}

/* ── HEADER ── */
.dash-header {
    background: #1C2B3A;
    border-radius: 16px;
    padding: 22px 32px;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    gap: 18px;
    box-shadow: 0 4px 20px rgba(28,43,58,0.18);
    border-bottom: 3px solid #F5C200;
}
.dash-bee   { font-size: 38px; line-height: 1; }
.dash-title {
    color: #FFFFFF !important;
    font-size: 24px; font-weight: 800;
    margin: 0; letter-spacing: -0.4px;
}
.dash-subtitle {
    color: rgba(245,194,0,0.85) !important;
    font-size: 13px; margin-top: 4px; font-weight: 400;
}
.dash-live {
    margin-left: auto;
    display: flex; align-items: center; gap: 7px;
    font-size: 12px; font-weight: 700;
    color: #F5C200;
    background: rgba(245,194,0,0.12);
    border: 1px solid rgba(245,194,0,0.35);
    border-radius: 20px; padding: 5px 14px;
}
.live-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #2E7D6B;
    box-shadow: 0 0 6px rgba(46,125,107,0.9);
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:0.45; transform:scale(0.8); }
}

/* ── FILTER BAR ── */
.filter-bar {
    background: #F0EDE5;
    border: 1px solid rgba(245,194,0,0.30);
    border-radius: 14px;
    padding: 14px 22px;
    margin-bottom: 18px;
    box-shadow: 0 2px 10px rgba(28,43,58,0.07);
}

/* ── KPI CARDS (large sparkline cards) ── */
.kpi-spark {
    background: #F0EDE5;
    border-radius: 16px;
    padding: 22px 22px 16px;
    border: 1px solid rgba(245,194,0,0.22);
    box-shadow: 0 2px 14px rgba(28,43,58,0.09);
    min-height: 165px;
    position: relative; overflow: hidden;
    transition: box-shadow 0.2s, border-color 0.2s;
}
.kpi-spark:hover {
    box-shadow: 0 6px 24px rgba(28,43,58,0.14);
    border-color: #F5C200;
}
.kpi-spark::after {
    content: '';
    position: absolute; bottom: -24px; right: -24px;
    width: 100px; height: 100px; border-radius: 50%;
    background: rgba(245,194,0,0.06);
}
.kpi-spark-label {
    font-size: 14px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.9px; color: #6B7E91 !important; margin-bottom: 10px;
}
.kpi-spark-value {
    font-size: 48px; font-weight: 800; line-height: 1;
    font-family: 'DM Mono', monospace; margin-bottom: 10px;
}
.kpi-spark-value.navy  { color: #1C2B3A !important; }
.kpi-spark-value.green { color: #2E7D6B !important; }
.kpi-spark-value.red   { color: #E05C3A !important; }
.kpi-spark-value.gold  { color: #C99B00 !important; }

/* ── SMALL KPI (percentage cards) ── */
.kpi-small {
    background: #F0EDE5;
    border-radius: 16px;
    padding: 20px 22px 16px;
    border: 1px solid rgba(245,194,0,0.22);
    box-shadow: 0 2px 14px rgba(28,43,58,0.09);
    min-height: 125px;
}

/* ── DELTA BADGES ── */
.kpi-delta-row { font-size: 15px; font-weight: 700; }
.delta-good { color: #2E7D6B !important; }
.delta-bad  { color: #E05C3A !important; }
.delta-flat { color: #6B7E91 !important; }

/* ── CHART CARDS ── */
.cc {
    background: #F0EDE5;
    border-radius: 16px;
    padding: 20px 22px 14px;
    border: 1px solid rgba(245,194,0,0.20);
    box-shadow: 0 2px 14px rgba(28,43,58,0.08);
    margin-bottom: 18px;
}

/* native st.container(border=True) override to match .cc */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #F0EDE5 !important;
    border-radius: 16px !important;
    border: 1px solid rgba(245,194,0,0.22) !important;
    box-shadow: 0 2px 14px rgba(28,43,58,0.08) !important;
    padding: 20px 22px 14px !important;
}

/* ── SECTION HEADERS ── */
.sec-hdr {
    font-size: 15px; font-weight: 700; color: #1C2B3A !important;
    text-transform: uppercase; letter-spacing: 1px;
    border-left: 4px solid #F5C200;
    padding-left: 10px; margin-bottom: 14px;
}

/* ── AGING BADGE ── */
.aging-badge {
    background: #FDF3BF;
    border: 1px solid #F5C200;
    border-radius: 6px; padding: 5px 14px;
    font-size: 13px; color: #8A6A00 !important;
    font-weight: 700; display: inline-block; margin-bottom: 10px;
}

/* ── CHIP (recent dates) ── */
.date-chip {
    background: #FFFFFF;
    border: 1px solid rgba(245,194,0,0.40);
    border-radius: 8px; padding: 4px 12px;
    font-size: 12px; font-weight: 600;
    color: #8A6A00 !important;
    font-family: 'DM Mono', monospace;
    display: inline-block; margin: 2px;
}
.date-chip.active {
    background: #F5C200;
    border-color: #C99B00;
    color: #1C2B3A !important;
}

/* ── TABLE ── */
.styled-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.styled-table thead tr { background: #1C2B3A; }
.styled-table th {
    padding: 11px 14px; text-align: center;
    font-weight: 700; font-size: 13px;
    color: #F5C200 !important;
    text-transform: uppercase; letter-spacing: 0.6px;
    border-bottom: 2px solid #F5C200;
}
.styled-table tbody tr { background: #FFFFFF; }
.styled-table tbody tr:nth-child(even) { background: #FAF8F5; }
.styled-table tbody tr:hover { background: #FDF3BF; }
.styled-table tbody tr:last-child { background: #FDF3BF; font-weight: 700; }
.styled-table td {
    padding: 10px 14px; text-align: center;
    border-bottom: 1px solid #EAE6DC;
    color: #1C2B3A !important;
}
.styled-table .col-date { text-align: left; font-weight: 600; color: #1C2B3A !important; }
.styled-table .col-high { color: #E05C3A !important; font-weight: 700; }

/* ── APPENDIX ── */
.app-card {
    background: #F0EDE5;
    border-radius: 14px; padding: 24px 28px;
    border: 1px solid rgba(245,194,0,0.22);
}
.app-title  { font-size: 14px; font-weight: 700; color: #1C2B3A !important; margin-bottom: 14px; }
.app-row    { display: flex; gap: 12px; margin-bottom: 11px; align-items: flex-start; }
.app-key    { font-size: 12px; font-weight: 700; color: #1C2B3A !important; min-width: 230px; }
.app-val    { font-size: 12px; color: #6B7E91 !important; line-height: 1.55; }
.app-form   {
    font-family: 'DM Mono', monospace; font-size: 11px;
    background: #FDF3BF; border: 1px solid #F5C200;
    border-radius: 5px; padding: 2px 9px;
    color: #8A6A00 !important; display: inline-block; margin-top: 3px;
}

/* ── STREAMLIT WIDGET OVERRIDES ── */
label,
.stSelectbox label,
.stMultiSelect label,
[data-testid="stWidgetLabel"] p {
    color: #1C2B3A !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.7px !important;
}
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
    background: #FFFFFF !important;
    border: 1px solid rgba(245,194,0,0.45) !important;
    border-radius: 10px !important;
    color: #1C2B3A !important;
}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1n9GW1UksZ-jhCQ-zmCqwx4EH20fa-Zm5wA5BiMmdZAE/edit?gid=713116247#gid=713116247"
)

# Colour tokens
C_NAVY   = "#1C2B3A"
C_GOLD   = "#F5C200"
C_TEAL   = "#2E7D6B"
C_CORAL  = "#E05C3A"
C_SLATE  = "#6B7E91"
C_CREAM  = "#F0EDE5"
C_HI     = "#FDF3BF"
C_ACTIVE = "#C99B00"
C_DARK   = "#8A6A00"

# Chart colour aliases
C_ISD = C_NAVY
C_OSD = C_CORAL
C_SUB = C_TEAL

# Plotly axis style (light bg)
_AX = dict(
    gridcolor="rgba(28,43,58,0.07)",
    linecolor="rgba(28,43,58,0.12)",
    tickcolor="rgba(28,43,58,0.20)",
    showgrid=True,
    tickfont=dict(color="#6B7E91", size=14, family="DM Mono"),
    title_font=dict(color="#6B7E91", size=14),
)
_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#1C2B3A", family="DM Sans, sans-serif", size=14),
    legend=dict(
        bgcolor="rgba(240,237,229,0.97)",
        bordercolor="rgba(245,194,0,0.35)",
        borderwidth=1,
        font=dict(size=14, color="#1C2B3A"),
    ),
    hoverlabel=dict(
        bgcolor="#1C2B3A", bordercolor="#F5C200",
        font_color="#F0EDE5", font_size=14,
    ),
    margin=dict(l=10, r=10, t=36, b=10),
    xaxis=_AX, yaxis=_AX,
)

def _layout(fig, height=None, extra=None):
    kw = dict(**_BASE)
    if height: kw["height"] = height
    if extra:  kw.update(extra)
    fig.update_layout(**kw)
    return fig

# ── UTILITIES ─────────────────────────────────────────────────────────────────
def _safe(row, col, default=0.0):
    if row is None: return default
    try:
        v = row[col] if col in row.index else default
        if v is None or (isinstance(v, float) and pd.isna(v)): return default
        return float(v)
    except Exception: return default

def _safe_multi(row, *cols, default=0.0):
    for col in cols:
        try:
            v = _safe(row, col, default=None)
            if v is not None and v != 0.0: return float(v)
        except Exception: pass
    return default

def _smart_date(col):
    """Parse ISO dates (dayfirst=False) and normalise to midnight."""
    s = col.astype(str).str.strip()
    parsed = pd.to_datetime(s, errors="coerce", dayfirst=False)
    cy = pd.Timestamp.now().year
    bad = parsed.notna() & (parsed.dt.year < 2000)
    if bad.any():
        parsed = parsed.copy()
        parsed[bad] = parsed[bad].apply(lambda t: t.replace(year=cy))
    return pd.to_datetime(parsed.dt.date)

def _nums(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(
                df[c].astype(str).str.replace(",","").str.replace("%",""),
                errors="coerce").fillna(0)
    return df

# ── DATA LOADING ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)

    # Dashboard_Card — 2-row header (row 0 = title, row 1 = col names)
    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Dashboard_Card", header=False)
        raw.columns = [str(c).strip() for c in raw.iloc[1]]
        raw = raw.iloc[2:].reset_index(drop=True)
        raw = raw[~raw["Date"].astype(str).str.contains(
            r"Grand Total|^Date$|^nan$|Backlog Threshold|ISD Backlog|OSD Backlog",
            case=False, na=True, regex=True)]
        raw["Date"] = _smart_date(raw["Date"])
        raw = raw.dropna(subset=["Date"])
        raw = _nums(raw, [c for c in raw.columns if c != "Date"])
        raw["Date_Label"] = raw["Date"].dt.strftime("%d %b")
        dc = raw
    except Exception as e:
        st.warning(f"Dashboard_Card: {e}"); dc = pd.DataFrame()

    # FID_Tracking
    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="FID_Tracking")
        raw.columns = [str(c).strip() for c in raw.columns]
        raw = raw[~raw.iloc[:,0].astype(str).str.contains(
            r"Grand Total|Report Date|^nan$", case=False, na=True, regex=True)]
        raw.rename(columns={raw.columns[0]: "Date"}, inplace=True)
        raw["Date"] = _smart_date(raw["Date"])
        raw = raw.dropna(subset=["Date"])
        raw = _nums(raw, list(raw.columns[1:]))
        raw["Date_Label"] = raw["Date"].dt.strftime("%d %b")
        ft = raw
    except Exception as e:
        st.warning(f"FID_Tracking: {e}"); ft = pd.DataFrame()

    # FID_RID_Backlog_Details
    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="FID_RID_Backlog_Details")
        raw.columns = [str(c).strip() for c in raw.columns]
        raw = raw[~raw.iloc[:,0].astype(str).str.contains(
            r"Grand Total|^Date$|^nan$", case=False, na=True, regex=True)]
        raw.rename(columns={raw.columns[0]: "Date"}, inplace=True)
        raw["Date"] = _smart_date(raw["Date"])
        raw = raw.dropna(subset=["Date"])
        raw = _nums(raw, list(raw.columns[1:]))
        raw["Date_Label"] = raw["Date"].dt.strftime("%d %b")
        fr = raw
    except Exception as e:
        st.warning(f"FID_RID_Backlog_Details: {e}"); fr = pd.DataFrame()

    # Aging_Distribution
    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Aging_Distribution")
        raw = raw.iloc[:, :14]
        raw.columns = ["Date","Region"] + [str(i) for i in range(1,11)] + ["10+","Total"]
        raw = raw[~raw["Date"].astype(str).str.contains(
            r"Grand Total|Report Date|^nan$", case=False, na=True, regex=True)]
        raw["Date"] = _smart_date(raw["Date"])
        raw = raw.dropna(subset=["Date"])
        raw["Region"] = raw["Region"].astype(str).str.strip()
        raw = _nums(raw, [str(i) for i in range(1,11)] + ["10+","Total"])
        raw["Date_Label"] = raw["Date"].dt.strftime("%d %b")
        ag = raw
    except Exception as e:
        st.warning(f"Aging_Distribution: {e}"); ag = pd.DataFrame()

    return dc, ft, fr, ag


with st.spinner("🐝 Loading live data…"):
    dc, ft, fr, ag = load_data()

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dash-header">
  <div class="dash-bee">🐝</div>
  <div>
    <div class="dash-title">Carrybee Delivery Intelligence</div>
    <div class="dash-subtitle">Live Backlog &amp; Operations Dashboard — Auto-refreshes every 10 minutes</div>
  </div>
  <div class="dash-live"><div class="live-dot"></div> Live</div>
</div>
""", unsafe_allow_html=True)

# ── DATE SLICER ───────────────────────────────────────────────────────────────
all_dates_ft = sorted(ft["Date"].dropna().unique()) if not ft.empty else []
all_dates_ag = sorted(ag["Date"].dropna().unique()) if not ag.empty else []
all_dates    = sorted(set(list(all_dates_ft) + list(all_dates_ag)))

st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
fc1, fc2, fc3 = st.columns([2, 2, 4])
if all_dates:
    date_opts = [pd.Timestamp(d).strftime("%d %b %Y") for d in all_dates]
    with fc1:
        sel_di = st.selectbox("📅 Report Date", range(len(date_opts)),
                              format_func=lambda i: date_opts[i],
                              index=len(date_opts)-1)
    with fc2:
        region_filter = st.multiselect("🗺️ Region", ["ISD","OSD"], default=["ISD","OSD"])
    with fc3:
        recent = all_dates[-min(7, len(all_dates)):]
        chips  = "".join(
            f'<span class="date-chip{" active" if all_dates[sel_di]==d else ""}">'
            f'{pd.Timestamp(d).strftime("%d %b")}</span>'
            for d in recent
        )
        st.markdown(
            f'<div style="padding-top:28px;">'
            f'<span style="font-size:10px;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:0.8px;color:{C_SLATE};margin-right:8px;">Recent:</span>'
            f'{chips}</div>',
            unsafe_allow_html=True)
    sel_date  = pd.Timestamp(all_dates[sel_di])
    sel_start = sel_date
    sel_end   = sel_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
else:
    region_filter = ["ISD","OSD"]
    sel_date = pd.Timestamp.now().normalize()
    sel_start = sel_date
    sel_end   = sel_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    st.error("No dates found.")
st.markdown('</div>', unsafe_allow_html=True)

# ── LATEST / PREV ROW HELPERS ─────────────────────────────────────────────────
def _latest(df):
    if df is None or df.empty: return None
    sub = df[df["Date"] <= sel_end].sort_values("Date")
    return sub.iloc[-1] if not sub.empty else None

def _prev(df):
    if df is None or df.empty: return None
    sub = df[df["Date"] <= sel_end].sort_values("Date")
    return sub.iloc[-2] if len(sub) >= 2 else None

lt_dc = _latest(dc); lt_fr = _latest(fr)
pr_dc = _prev(dc);   pr_fr = _prev(fr)

# ── KPI CALCULATIONS ──────────────────────────────────────────────────────────
ag_le = ag[ag["Date"] <= sel_end] if not ag.empty else pd.DataFrame()
if not ag_le.empty:
    ag_last_date = ag_le["Date"].max()
    ag_day       = ag_le[ag_le["Date"] == ag_last_date]
    isd_total    = ag_day[ag_day["Region"]=="ISD"]["Total"].sum()
    osd_total    = ag_day[ag_day["Region"]=="OSD"]["Total"].sum()
    tot_fid      = isd_total + osd_total
    prev_ag_d    = ag_le[ag_le["Date"] < ag_last_date]["Date"]
    if not prev_ag_d.empty:
        pr_ag  = ag_le[ag_le["Date"] == prev_ag_d.max()]
        pr_fid = pr_ag[pr_ag["Region"]=="ISD"]["Total"].sum() + pr_ag[pr_ag["Region"]=="OSD"]["Total"].sum()
    else:
        pr_fid = tot_fid
else:
    isd_total = osd_total = tot_fid = pr_fid = 0.0

fid_bl     = _safe(lt_fr, "FID Backlog")
rid_bl     = _safe(lt_fr, "RID Backlog")
overall_bl = fid_bl + rid_bl
pr_overall = _safe(pr_fr,"FID Backlog") + _safe(pr_fr,"RID Backlog")

zt_val     = _safe(lt_dc, "Zone Transfer")
pr_zt_val  = _safe(pr_dc, "Zone Transfer")
dc_total   = _safe(lt_dc, "Total")
denom      = dc_total if dc_total > 0 else tot_fid
fid_pct    = (fid_bl / denom * 100) if denom > 0 else 0.0
pr_dc_tot  = _safe(pr_dc, "Total")
pr_den     = pr_dc_tot if pr_dc_tot > 0 else pr_fid
pr_fid_pct = (_safe(pr_fr,"FID Backlog") / pr_den * 100) if pr_den > 0 else 0.0
zt_pct     = (zt_val    / dc_total  * 100) if (zt_val    > 0 and dc_total  > 0) else 0.0
pr_zt_pct  = (pr_zt_val / pr_dc_tot * 100) if (pr_zt_val > 0 and pr_dc_tot > 0) else 0.0

d_fid = tot_fid    - pr_fid
d_bl  = overall_bl - pr_overall
d_zt  = zt_val     - pr_zt_val

# ── SPARKLINES ────────────────────────────────────────────────────────────────
def _spark7_ag():
    if ag_le.empty: return []
    dates = sorted(ag_le["Date"].unique())[-7:]
    return [float(ag_le[ag_le["Date"]==d]["Total"].sum()) for d in dates]

def _spark7_bl():
    if fr.empty: return []
    sub = fr[fr["Date"] <= sel_end].sort_values("Date").tail(7)
    if "FID Backlog" not in sub.columns: return []
    rid = sub["RID Backlog"] if "RID Backlog" in sub.columns else 0
    return (sub["FID Backlog"] + rid).tolist()

def _spark7_zt():
    if dc.empty: return []
    sub = dc[dc["Date"] <= sel_end].sort_values("Date").tail(7)
    return sub["Zone Transfer"].tolist() if "Zone Transfer" in sub.columns else []

spark_fid = _spark7_ag()
spark_bl  = _spark7_bl()
spark_zt  = _spark7_zt()

def _sparkline_svg(values, color, width=110, height=40):
    if not values or len(values) < 2: return ""
    mn, mx = min(values), max(values)
    rng = mx - mn if mx != mn else 1
    pad = 4
    pts = []
    for i, v in enumerate(values):
        x = pad + (i/(len(values)-1))*(width-2*pad)
        y = pad + (1-(v-mn)/rng)*(height-2*pad)
        pts.append(f"{x:.1f},{y:.1f}")
    lx, ly = pts[-1].split(",")
    path  = f"M{pts[0]} " + " ".join(f"L{p}" for p in pts[1:])
    area  = path + f" L{width-pad},{height} L{pad},{height} Z"
    uid   = color.replace("#","")
    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g{uid}" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{color}" stop-opacity="0.35"/>
    <stop offset="100%" stop-color="{color}" stop-opacity="0.02"/>
  </linearGradient></defs>
  <path d="{area}" fill="url(#g{uid})"/>
  <polyline points="{' '.join(pts)}" fill="none" stroke="{color}" stroke-width="2.2"
            stroke-linejoin="round" stroke-linecap="round"/>
  <circle cx="{lx}" cy="{ly}" r="3.5" fill="{color}"/>
</svg>"""

def _trend(vals, lower_is_better=True):
    if not vals or len(vals) < 2: return C_GOLD
    return C_TEAL if (vals[-1] < vals[-2]) == lower_is_better else C_CORAL

fc = _trend(spark_fid, True)
bc = _trend(spark_bl,  True)
zc = _trend(spark_zt, False)

# ═══════════════════════════════════════════════════════════════════
# ROW 1 — 3 Sparkline KPI cards + Backlog Donut
# ═══════════════════════════════════════════════════════════════════
kc1, kc2, kc3, kc4 = st.columns([1,1,1,1])

def _spark_kpi(col_w, num, label, val_str, val_cls, spark_html, delta, note="", lower_is_better=True):
    good  = (delta < 0 and lower_is_better) or (delta > 0 and not lower_is_better)
    flat  = delta == 0
    dcls  = "delta-flat" if flat else ("delta-good" if good else "delta-bad")
    arrow = "—" if flat else ("▼" if delta < 0 else "▲")
    note_html = (f'<div style="font-size:13px;color:#6B7E91;margin-top:4px;">{note}</div>'
                 if note else "")
    col_w.markdown(f"""
    <div class="kpi-spark">
      <div class="kpi-spark-label">{num} · {label}</div>
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
        <div class="kpi-spark-value {val_cls}">{val_str}</div>
        <div style="margin-top:4px;">{spark_html}</div>
      </div>
      <div class="kpi-delta-row">
        <span class="{dcls}">{arrow} {abs(delta):,.0f} vs prev day</span>
      </div>
      {note_html}
      <div style="font-size:13px;color:#6B7E91;margin-top:5px;font-family:DM Mono,monospace;opacity:0.6;">7-day trend</div>
    </div>""", unsafe_allow_html=True)

with kc1:
    _spark_kpi(kc1, "01", "Total In-Process (FID)",
               f"{tot_fid:,.0f}",
               "green" if d_fid <= 0 else "red",
               _sparkline_svg(spark_fid, fc),
               d_fid, lower_is_better=True)

with kc2:
    _spark_kpi(kc2, "02", "Overall Backlog",
               f"{overall_bl:,.0f}",
               "green" if d_bl <= 0 else "red",
               _sparkline_svg(spark_bl, bc),
               d_bl, "FID + RID combined", lower_is_better=True)

with kc3:
    _spark_kpi(kc3, "03", "Zone Transfer Parcels",
               f"{int(zt_val):,}" if zt_val > 0 else "—",
               "gold",
               _sparkline_svg(spark_zt, zc),
               d_zt, "Dashboard_Card · Zone Transfer", lower_is_better=False)

with kc4:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">04 · Backlog — FID vs RID</div>', unsafe_allow_html=True)
        if (fid_bl + rid_bl) > 0:
            fig_dn = go.Figure(data=[go.Pie(
                labels=["FID","RID"], values=[fid_bl, rid_bl],
                hole=0.60, marker_colors=[C_ISD, C_OSD],
                textinfo="label+percent",
                textfont=dict(size=15, color="#FFFFFF"), pull=[0.03,0],
            )])
            fig_dn.add_annotation(
                text=f"<b>{fid_bl+rid_bl:,.0f}</b><br><span style='font-size:13px'>Total</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color=C_NAVY), xanchor="center",
            )
            _layout(fig_dn, height=175,
                    extra={"margin": dict(l=0,r=0,t=0,b=0),
                           "legend": dict(orientation="h", yanchor="bottom", y=-0.22,
                                          xanchor="center", x=0.5,
                                          font=dict(size=14, color=C_NAVY))})
            st.plotly_chart(fig_dn, use_container_width=True)
        else:
            st.info("No backlog data.")

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# ROW 2 — FID Backlog % | Zone Change % | (two spacer cols)
# ═══════════════════════════════════════════════════════════════════
kr1, kr2, _s1, _s2 = st.columns([1,1,1,1])

def _pct_kpi(col_w, num, label, val, prev, lower_is_better=True, note=""):
    diff     = val - prev
    good     = (diff < 0 and lower_is_better) or (diff > 0 and not lower_is_better)
    flat     = diff == 0
    vcol     = C_TEAL if good else (C_CORAL if not flat else C_NAVY)
    dcls     = "delta-flat" if flat else ("delta-good" if good else "delta-bad")
    arrow    = "—" if flat else ("▼" if diff < 0 else "▲")
    note_html = (f'<div style="font-size:13px;color:#6B7E91;margin-top:4px;">{note}</div>'
                 if note else "")
    col_w.markdown(f"""
    <div class="kpi-small">
      <div class="kpi-spark-label">{num} · {label}</div>
      <div style="font-size:44px;font-weight:800;font-family:'DM Mono',monospace;
                  color:{vcol};margin-bottom:10px;line-height:1;">{val:.2f}%</div>
      <div class="kpi-delta-row">
        <span class="{dcls}">{arrow} {abs(diff):.2f} pp vs prev day</span>
      </div>
      {note_html}
    </div>""", unsafe_allow_html=True)

with kr1:
    _pct_kpi(kr1, "05", "FID Backlog %", fid_pct, pr_fid_pct,
             lower_is_better=True, note="FID Backlog ÷ Total × 100")
with kr2:
    _pct_kpi(kr2, "06", "Zone Change %", zt_pct, pr_zt_pct,
             lower_is_better=True, note="Zone Transfer ÷ Total × 100")

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# ROW 3 — Backlog Details + Sort
# ═══════════════════════════════════════════════════════════════════
col_bl, col_sort = st.columns([3,2])

with col_bl:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">07 · Backlog Details — FID &amp; RID (LMH / FMH)</div>',
                    unsafe_allow_html=True)
        if lt_fr is not None:
            detail = [
                ("FID LMH", _safe(lt_fr,"FID LMH ISD"), _safe(lt_fr,"FID LMH SUB"),
                 _safe(lt_fr,"FID LMH OSD"), _safe(lt_fr,"FID LMH Total")),
                ("FID FMH", _safe(lt_fr,"FID FMH"), 0, 0, _safe(lt_fr,"FID FMH")),
                ("RID FMH", _safe(lt_fr,"RID FMH ISD"), _safe(lt_fr,"RID FMH SUB"),
                 _safe(lt_fr,"RID FMH OSD"),
                 _safe(lt_fr,"RID FMH ISD")+_safe(lt_fr,"RID FMH SUB")+_safe(lt_fr,"RID FMH OSD")),
                ("RID LMH", _safe(lt_fr,"RID LMH ISD"), _safe(lt_fr,"RID LMH SUB"),
                 _safe(lt_fr,"RID LMH OSD"),
                 _safe(lt_fr,"RID LMH ISD")+_safe(lt_fr,"RID LMH SUB")+_safe(lt_fr,"RID LMH OSD")),
            ]
            labs,iv,sv,ov,tots = zip(*detail)
            fig7 = go.Figure()
            for vals, name, color in [(iv,"ISD",C_ISD),(sv,"SUB",C_SUB),(ov,"OSD",C_OSD)]:
                fig7.add_trace(go.Bar(
                    name=name, y=labs, x=vals, orientation="h", marker_color=color,
                    text=[f"{v:,.0f}" if v>0 else "" for v in vals],
                    textposition="inside", insidetextanchor="middle",
                    textfont=dict(color="#FFFFFF", size=16),
                ))
            for lbl, tot in zip(labs, tots):
                if tot > 0:
                    fig7.add_annotation(x=tot, y=lbl, text=f"  <b>{tot:,.0f}</b>",
                                        showarrow=False, xanchor="left",
                                        font=dict(size=16, color=C_NAVY))
            _layout(fig7, height=320, extra={
                "barmode":"stack",
                "xaxis": dict(**_AX, title="Count"),
                "yaxis": dict(**_AX, autorange="reversed"),
            })
            st.plotly_chart(fig7, use_container_width=True)
        else:
            st.info("No backlog detail data.")

with col_sort:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">08 · Sort — FID Sort vs RID Sort</div>',
                    unsafe_allow_html=True)
        if lt_fr is not None:
            fid_sort = _safe(lt_fr, "FID Sort")
            rid_sort = _safe_multi(lt_fr, "RID Sort", "RID LMH Sort")
            fig8 = go.Figure(data=[go.Bar(
                y=["FID Sort","RID Sort"], x=[fid_sort, rid_sort],
                orientation="h",
                marker_color=[C_ISD, C_OSD],
                text=[f"{fid_sort:,.0f}", f"{rid_sort:,.0f}"],
                textposition="outside",
                textfont=dict(size=16, color=C_NAVY, family="DM Mono"),
                width=0.45,
            )])
            _layout(fig8, height=320, extra={
                "showlegend": False,
                "xaxis": dict(**_AX, title="Parcels Sorted"),
                "yaxis": dict(**_AX),
                "margin": dict(l=8, r=90, t=30, b=8),
            })
            st.plotly_chart(fig8, use_container_width=True)
        else:
            st.info("No sort data.")

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# ROW 4 — Date-range Tracking + Region bars
# ═══════════════════════════════════════════════════════════════════
col_track, col_region = st.columns([3,2])

with col_track:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">09 · Date-wise Backlog Progress Tracking (FID)</div>',
                    unsafe_allow_html=True)
        if all_dates:
            t_opts = [pd.Timestamp(d).strftime("%d %b %Y") for d in all_dates]
            tc1, tc2 = st.columns(2)
            with tc1:
                t_si = st.selectbox("From", range(len(t_opts)),
                                    format_func=lambda i: t_opts[i],
                                    index=0, key="tr_from")
            with tc2:
                t_ei = st.selectbox("To", range(len(t_opts)),
                                    format_func=lambda i: t_opts[i],
                                    index=len(t_opts)-1, key="tr_to")
            if t_ei < t_si: t_ei = t_si
            t_start = pd.Timestamp(all_dates[t_si])
            t_end   = pd.Timestamp(all_dates[t_ei]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            ft_r    = (ft[(ft["Date"]>=t_start)&(ft["Date"]<=t_end)].sort_values("Date")
                       if not ft.empty else pd.DataFrame())
        else:
            ft_r = pd.DataFrame(); t_start = sel_start; t_end = sel_end

        if not ft_r.empty:
            fig9 = go.Figure()
            if "Total In Progress (Backlog)" in ft_r.columns:
                fig9.add_trace(go.Bar(
                    x=ft_r["Date_Label"], y=ft_r["Total In Progress (Backlog)"],
                    name="Total In Process", marker_color=C_ISD, opacity=0.88))
            if "Newly Added" in ft_r.columns:
                fig9.add_trace(go.Bar(
                    x=ft_r["Date_Label"], y=ft_r["Newly Added"],
                    name="Newly Added", marker_color=C_GOLD, opacity=0.88))
            if "Carry Forward" in ft_r.columns:
                fig9.add_trace(go.Bar(
                    x=ft_r["Date_Label"], y=ft_r["Carry Forward"],
                    name="Carry Forward", marker_color=C_SLATE, opacity=0.75))
            if "Worked On" in ft_r.columns:
                fig9.add_trace(go.Scatter(
                    x=ft_r["Date_Label"], y=ft_r["Worked On"],
                    name="Worked On", mode="lines+markers",
                    line=dict(color=C_TEAL, width=3),
                    marker=dict(size=7, color=C_TEAL,
                                line=dict(color="#FFFFFF", width=1.5))))
            _layout(fig9, height=320, extra={"barmode":"group"})
            st.plotly_chart(fig9, use_container_width=True)
        else:
            st.info("No FID tracking data for selected range.")

with col_region:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">10 · Region Wise In-Process Parcels</div>',
                    unsafe_allow_html=True)
        if tot_fid > 0:
            df_reg = pd.DataFrame({"Region":["ISD","OSD"],
                                    "Parcels":[isd_total, osd_total]})
            fig10  = px.bar(df_reg, x="Region", y="Parcels",
                            color="Region",
                            color_discrete_map={"ISD":C_ISD,"OSD":C_OSD},
                            text="Parcels")
            fig10.update_traces(
                texttemplate="%{text:,.0f}", textposition="outside",
                textfont=dict(color=C_NAVY, size=16, family="DM Mono"),
                width=0.45)
            _layout(fig10, height=240, extra={
                "showlegend": False,
                "yaxis": dict(**_AX, title="Parcels"),
                "xaxis": dict(**_AX, title=""),
            })
            st.plotly_chart(fig10, use_container_width=True)
            st.markdown(f"""
            <div style="display:flex;border-top:2px solid {C_GOLD};padding-top:12px;margin-top:4px;">
              <div style="flex:1;text-align:center;border-right:1px solid #EAE6DC;">
                <div style="font-size:13px;color:{C_SLATE};text-transform:uppercase;
                            letter-spacing:0.8px;margin-bottom:3px;">ISD</div>
                <div style="font-size:26px;font-weight:800;color:{C_ISD};
                            font-family:'DM Mono',monospace;">{isd_total:,.0f}</div>
              </div>
              <div style="flex:1;text-align:center;border-right:1px solid #EAE6DC;">
                <div style="font-size:13px;color:{C_SLATE};text-transform:uppercase;
                            letter-spacing:0.8px;margin-bottom:3px;">OSD</div>
                <div style="font-size:26px;font-weight:800;color:{C_OSD};
                            font-family:'DM Mono',monospace;">{osd_total:,.0f}</div>
              </div>
              <div style="flex:1;text-align:center;">
                <div style="font-size:13px;color:{C_SLATE};text-transform:uppercase;
                            letter-spacing:0.8px;margin-bottom:3px;">Total</div>
                <div style="font-size:26px;font-weight:800;color:{C_ACTIVE};
                            font-family:'DM Mono',monospace;">{tot_fid:,.0f}</div>
              </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("No region data.")

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# ROW 5 — Aging Distribution + Aging Table
# ═══════════════════════════════════════════════════════════════════
AGE_COLS = [str(i) for i in range(1,11)] + ["10+"]
ag_f = (ag[(ag["Date"]>=sel_start)&(ag["Date"]<=sel_end)].copy()
        if not ag.empty else pd.DataFrame())
if not ag_f.empty and "Region" in ag_f.columns:
    ag_f = ag_f[ag_f["Region"].isin(region_filter)]

col_ag, col_ag_tbl = st.columns([3,2])

with col_ag:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">11 · Aging Distribution</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="aging-badge">ISD &amp; SUB = 4 Days+ &nbsp;|&nbsp; OSD = 5 Days+</div>',
            unsafe_allow_html=True)
        if not ag_f.empty:
            ag_max   = ag_f["Date"].max()
            ag_day_f = ag_f[ag_f["Date"]==ag_max].copy()
            rows8 = []
            for _, row in ag_day_f.iterrows():
                region = str(row.get("Region","")).strip()
                if region not in region_filter: continue
                total = float(row.get("Total",0) or 0)
                if total == 0:
                    total = sum(float(row[c]) for c in AGE_COLS
                                if c in ag_day_f.columns and pd.notna(row[c]))
                for c in AGE_COLS:
                    if c in ag_day_f.columns:
                        val = float(row[c]) if pd.notna(row[c]) else 0.0
                        rows8.append({"Region":region,"Age":f"{c}d",
                                      "Count":val,"Pct":val/total*100 if total>0 else 0.0})
            ag_melt = pd.DataFrame(rows8)
            if not ag_melt.empty:
                fig11 = px.bar(ag_melt, x="Age", y="Pct", color="Region",
                               color_discrete_map={"ISD":C_ISD,"OSD":C_OSD},
                               barmode="group",
                               text=ag_melt["Pct"].apply(lambda x: f"{x:.1f}%"))
                fig11.update_traces(
                    textposition="outside",
                    textfont=dict(color=C_NAVY, size=15),
                    customdata=ag_melt[["Count","Region"]],
                    hovertemplate="<b>%{x}</b><br>Region: %{customdata[1]}"
                                  "<br>Count: %{customdata[0]:,.0f}<br>Pct: %{y:.1f}%")
                _layout(fig11, height=320,
                        extra={"yaxis": dict(**_AX, title="Percentage (%)")})
                st.plotly_chart(fig11, use_container_width=True)
            else:
                st.info("No aging data.")
        else:
            st.info("No aging distribution data available.")

with col_ag_tbl:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">12 · Aging Count &amp; % by Region</div>',
                    unsafe_allow_html=True)
        if not ag_f.empty:
            ag_tbl = ag_f[ag_f["Date"]==ag_f["Date"].max()].copy()
            isd_r  = ag_tbl[ag_tbl["Region"]=="ISD"].iloc[0] if "ISD" in ag_tbl["Region"].values else None
            osd_r  = ag_tbl[ag_tbl["Region"]=="OSD"].iloc[0] if "OSD" in ag_tbl["Region"].values else None
            isd_t  = float(isd_r["Total"]) if isd_r is not None else 0
            osd_t  = float(osd_r["Total"]) if osd_r is not None else 0
            th = "<th>Days</th>"
            if isd_r is not None: th += "<th>ISD</th><th>ISD %</th>"
            if osd_r is not None: th += "<th>OSD</th><th>OSD %</th>"
            body = ""
            for c in AGE_COLS:
                if c not in ag_tbl.columns: continue
                td = f"<td><b>{c}d</b></td>"
                if isd_r is not None:
                    v = float(isd_r[c]) if pd.notna(isd_r[c]) else 0
                    td += (f"<td>{v:,.0f}</td><td>{v/isd_t*100:.1f}%</td>"
                           if isd_t else "<td>—</td><td>—</td>")
                if osd_r is not None:
                    v = float(osd_r[c]) if pd.notna(osd_r[c]) else 0
                    td += (f"<td>{v:,.0f}</td><td>{v/osd_t*100:.1f}%</td>"
                           if osd_t else "<td>—</td><td>—</td>")
                body += f"<tr>{td}</tr>"
            td_tot = "<td><b>Total</b></td>"
            if isd_r is not None: td_tot += f"<td><b>{isd_t:,.0f}</b></td><td><b>100%</b></td>"
            if osd_r is not None: td_tot += f"<td><b>{osd_t:,.0f}</b></td><td><b>100%</b></td>"
            body += f"<tr>{td_tot}</tr>"
            st.markdown(f"""
            <div style="overflow-x:auto;max-height:380px;overflow-y:auto;">
            <table class="styled-table">
              <thead><tr>{th}</tr></thead>
              <tbody>{body}</tbody>
            </table></div>""", unsafe_allow_html=True)
        else:
            st.info("No aging data.")

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# ROW 6 — Full FID Tracking Table
# ═══════════════════════════════════════════════════════════════════
with st.container(border=True):
    st.markdown('<div class="sec-hdr">13 · Date-wise Backlog Progress Tracking — Full Table (FID)</div>',
                unsafe_allow_html=True)
    try:
        ft_tbl = (ft[(ft["Date"]>=t_start)&(ft["Date"]<=t_end)].sort_values("Date").copy()
                  if not ft.empty else pd.DataFrame())
    except Exception:
        ft_tbl = ft.sort_values("Date").copy() if not ft.empty else pd.DataFrame()

    if not ft_tbl.empty:
        COL_MAP = {
            "Date_Label":                  "Date",
            "Newly Added":                 "Newly Added",
            "Total In Progress (Backlog)": "Total In Process (Backlog)",
            "Worked On":                   "Worked On",
            "Carry Forward":               "Carry Forward",
        }
        sc     = [c for c in COL_MAP if c in ft_tbl.columns]
        df_tbl = ft_tbl[sc].rename(columns=COL_MAP)
        headers = "".join(f"<th>{c}</th>" for c in df_tbl.columns)
        body = ""
        for i,(_, r) in enumerate(df_tbl.iterrows()):
            is_last = i == len(df_tbl)-1
            cells   = ""
            for j, v in enumerate(r):
                cls = "col-date" if j==0 else ("col-high" if is_last else "")
                try:   disp = v if j==0 else (f"{int(float(v)):,}" if float(v)!=0 else "—")
                except: disp = "—"
                cells += f"<td class='{cls}'>{disp}</td>"
            body += f"<tr>{cells}</tr>"
        st.markdown(f"""
        <div style="overflow-x:auto;">
        <table class="styled-table">
          <thead><tr>{headers}</tr></thead>
          <tbody>{body}</tbody>
        </table></div>""", unsafe_allow_html=True)
    else:
        st.info("No FID tracking data to display.")

# ═══════════════════════════════════════════════════════════════════
# APPENDIX
# ═══════════════════════════════════════════════════════════════════
with st.expander("📖  Appendix — Definitions & Calculation Methods", expanded=False):
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="app-title">📊 KPI Definitions &amp; Calculation Methods</div>',
                unsafe_allow_html=True)
    items = [
        ("01 · Total In-Process (FID)",
         "All parcels in the First Inbound Delivery cycle on the selected date. Green = count fell vs yesterday.",
         "Aging_Distribution → ISD Total + OSD Total"),
        ("02 · Overall Backlog (FID+RID)",
         "Total undelivered backlog. Green = falling day-on-day.",
         "FID Backlog + RID Backlog  (FID_RID_Backlog_Details)"),
        ("03 · Zone Transfer Parcels",
         "Parcels transferred between zones. Manually entered in Dashboard_Card.",
         "Dashboard_Card → 'Zone Transfer' column"),
        ("04 · Backlog FID vs RID (Donut)",
         "Visual split of overall backlog between FID and RID pipelines.",
         "FID_RID_Backlog_Details → FID Backlog & RID Backlog"),
        ("05 · FID Backlog %",
         "Share of total FID parcels in backlog. Green ↓ = improving.",
         "FID Backlog ÷ Total In-Process × 100"),
        ("06 · Zone Change %",
         "Share of all parcels that had a zone transfer.",
         "Zone Transfer ÷ Total (Dashboard_Card) × 100"),
        ("07 · Backlog Details (LMH / FMH)",
         "Stacked bar by service type × region. LMH = Last Mile Hub, FMH = First Mile Hub.",
         "FID_RID_Backlog_Details → FID/RID × LMH/FMH × ISD/SUB/OSD"),
        ("08 · Sort — FID vs RID",
         "Horizontal bars: parcels sorted through each pipeline on selected date.",
         "FID_RID_Backlog_Details → 'FID Sort' and 'RID Sort'"),
        ("09 · Date-wise Backlog Tracking",
         "Grouped bar chart over custom date range. Includes Newly Added, Carry Forward, Worked On.",
         "FID_Tracking → all columns"),
        ("10 · Region Wise In-Process",
         "Vertical bars: ISD vs OSD parcel volume on selected date.",
         "Aging_Distribution → ISD Total and OSD Total"),
        ("11 · Aging Distribution",
         "% of parcels per day-bucket (1d → 10+d). Threshold: ISD/SUB ≥ 4 days, OSD ≥ 5 days.",
         "Aging_Distribution → columns 1 through 10+"),
        ("12 · Aging Count Table",
         "Raw counts and percentages for ISD and OSD per aging bucket.",
         "Aging_Distribution → same as above"),
        ("Sparklines", "Green = last value better than previous day. Red = worsening. 7 data points.", ""),
        ("ISD", "Inbound Standard Delivery", ""),
        ("OSD", "Outbound Standard Delivery", ""),
        ("SUB", "Sub-hub — intermediate processing centre", ""),
        ("LMH", "Last Mile Hub — final hub before customer delivery", ""),
        ("FMH", "First Mile Hub — network entry point", ""),
        ("FID", "First Inbound Delivery cycle", ""),
        ("RID", "Return Inbound Delivery — re-entered returned parcels", ""),
    ]
    for key, desc, formula in items:
        fh = f'<br><span class="app-form">{formula}</span>' if formula else ""
        st.markdown(f"""
        <div class="app-row">
          <div class="app-key">▸ {key}</div>
          <div class="app-val">{desc}{fh}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;color:{C_SLATE};font-size:13px;
            padding:20px 0 10px;letter-spacing:0.5px;font-family:'DM Mono',monospace;">
  🐝 Carrybee Delivery Intelligence &nbsp;·&nbsp;
  Report Date: <span style="color:{C_ACTIVE};font-weight:700;">{sel_date.strftime('%d %b %Y')}</span>
  &nbsp;·&nbsp; Cache TTL: 10 min &nbsp;·&nbsp; Powered by Google Sheets
</div>
""", unsafe_allow_html=True)
