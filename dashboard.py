import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
import base64
import os

st.set_page_config(
    page_title="Carrybee Intelligence",
    page_icon="🐝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── SVG ICON HELPER (replaces file-based image loading) ──────────────────────
def get_icon_svg(icon_type, size_px=48):
    """Returns inline SVG icons — no external file dependency."""
    icons = {
        "fid": f"""<svg width="{size_px}" height="{size_px}" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" rx="12" fill="#1C2B3A" fill-opacity="0.12"/>
  <path d="M14 20h20M14 28h14" stroke="#1C2B3A" stroke-width="2.5" stroke-linecap="round"/>
  <circle cx="34" cy="28" r="5" fill="#E05C3A"/>
  <path d="M32 28h4M34 26v4" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/>
  <rect x="10" y="12" width="28" height="24" rx="4" stroke="#1C2B3A" stroke-width="2" fill="none"/>
</svg>""",
        "backlog": f"""<svg width="{size_px}" height="{size_px}" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" rx="12" fill="#1C2B3A" fill-opacity="0.12"/>
  <rect x="10" y="30" width="8" height="10" rx="2" fill="#1C2B3A"/>
  <rect x="20" y="22" width="8" height="18" rx="2" fill="#8A6A00"/>
  <rect x="30" y="14" width="8" height="26" rx="2" fill="#E05C3A"/>
  <path d="M10 10h28" stroke="#1C2B3A" stroke-width="2" stroke-linecap="round"/>
</svg>""",
        "zone": f"""<svg width="{size_px}" height="{size_px}" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" rx="12" fill="#1C2B3A" fill-opacity="0.12"/>
  <path d="M12 24h24M30 18l6 6-6 6" stroke="#1C2B3A" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="16" cy="24" r="4" fill="#2E7D6B"/>
  <circle cx="32" cy="24" r="4" fill="#1C2B3A"/>
</svg>""",
    }
    return icons.get(icon_type, "")

# ── STYLES ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700;800&family=DM+Mono:wght@400;500;700&display=swap');

* { font-family: 'DM Sans', sans-serif; box-sizing: border-box; }

[data-testid="stAppViewContainer"] { background: #f4f3ee !important; }
[data-testid="stHeader"]           { background: transparent; }
[data-testid="stToolbar"]          { display: none; }
[data-testid="stDecoration"]       { display: none; }

.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    max-width: 98% !important;
    gap: 0.9rem !important;
}

/* ── HEADER ── */
.dash-header {
    background: #F5C200;
    border: 8px solid #C99B00;
    border-radius: 16px;
    padding: 14px 28px;
    margin-bottom: 0px;
    display: flex; align-items: center; gap: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.dash-title    { color:#1C2B3A !important; font-size:28px; font-weight:700; margin:0; letter-spacing:-0.5px; }
.dash-subtitle { color:#2E7D6B !important; font-size:18px; margin-top:2px; font-weight:600; }
.dash-bee      { font-size:42px; line-height:1; }

/* ── CHART CONTAINERS ── */
[data-testid="stVerticalBlockBorderWrapper"], .appendix-card {
    background-color: #FFFFFF !important;
    border-radius: 20px !important;
    border: 8px solid #C4C0B3 !important;
    box-shadow: 0px 6px 18px rgba(0,0,0,0.1) !important;
    height: 100% !important; 
}

[data-testid="stVerticalBlockBorderWrapper"] {
    padding: 20px 24px 16px !important;
}

/* ══════════════════════════════════════════
   KPI CARDS
   ══════════════════════════════════════════ */
.kpi-spark {
    border-radius: 16px !important;
    border: 8px solid #E8CD68 !important;
    box-shadow: 0 6px 16px rgba(0,0,0,0.05) !important;
    min-height: 220px;
    width: 100%;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: flex-start !important;
    padding: 20px 16px 14px !important;
}

.kpi-small {
    background: #f0ede5!important;
    border-radius: 16px !important;
    border: 8px solid #E8CD68 !important;
    box-shadow: 0 6px 16px rgba(0,0,0,0.05) !important;
    min-height: 180px;
    width: 100%;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: flex-start !important;
    padding: 20px 16px 14px !important;
}

@media (min-width: 800px) {
    .kpi-small { margin-top: -65px !important; z-index: 10; }
}

.kpi-icon-top {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 10px;
    width: 100%;
}

.kpi-label {
    font-size: 20px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #1C2B3A;
    text-align: center;
    line-height: 1.3;
    margin-bottom: 8px;
    width: 100%;
}

.kpi-center-val {
    font-size: 36px;
    font-weight: 700;
    font-family: 'DM Mono', monospace;
    color: #1C2B3A;
    line-height: 1.1;
    text-align: center;
    white-space: nowrap;
    width: 100%;
    position: static !important;
    transform: none !important;
    top: unset !important;
    left: unset !important;
}

.kpi-footer {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: auto;
    padding-top: 10px;
}

/* ── SECTION HEADER ── */
.sec-hdr {
    font-size:24px; font-weight:700; color:#1C2B3A !important;
    text-transform:uppercase; letter-spacing:1px;
    border-left:8px solid #F5C200;
    padding-left:12px; margin-bottom:18px;
    background-color: #F9DE7A;
}

/* ── DELTA COLOURS ── */
.delta-up-good,  .delta-down-good { color: #2E7D6B !important; }
.delta-up-bad,   .delta-down-bad  { color: #E05C3A !important; }
.delta-neutral                    { color: #6B7E91 !important; }

/* ── AGING BADGE ── */
.aging-badge {
    background: rgba(245,194,0,0.15); border:8px solid #F5C200; border-radius:8px;
    padding:6px 14px; font-size:12px; color:#1C2B3A !important; font-weight:700;
    display:inline-block; margin-bottom:12px;
}

/* ── TABLE ── */
.styled-table { width:100%; border-collapse:collapse; font-size:13px; }
.styled-table thead tr { background: #F9F8F6; }
.styled-table th { padding:12px 14px; text-align:center; font-weight:700; color:#1C2B3A !important;
    border-bottom:8px solid #F5C200; text-transform:uppercase; letter-spacing:0.5px; }
.styled-table tbody tr:hover { background: rgba(0,0,0,0.02); }
.styled-table tbody tr:last-child { background:#F9F8F6; font-weight:700; }
.styled-table td { padding:12px 14px; text-align:center;
    border-bottom:8px solid rgba(28,43,58,0.05); color:#1C2B3A !important; }
.styled-table .col-date { text-align:left; font-weight:700; color:#1C2B3A !important; }

/* ── FORM CONTROLS ── */
label, .stSelectbox label, .stMultiSelect label, .stToggle label {
    color: #1C2B3A !important; font-size: 14px !important; font-weight: 600 !important;
}
.stSelectbox div[data-baseweb="select"] *,
.stMultiSelect div[data-baseweb="select"] * { color: #1C2B3A !important; }
div[data-baseweb="select"] > div { background-color: #FFFFFF; border-color: #C4C0B3; }
div[data-baseweb="popover"] * { color: #FFFFFF !important; }

/* ── EXPANDER ── */
[data-testid="stExpander"] details summary p,
[data-testid="stExpander"] details summary span {
    color: #1C2B3A !important; font-size: 15px !important; font-weight: 700 !important;
}
[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 8px solid #C4C0B3 !important;
    border-radius: 24px !important;
}
</style>
""", unsafe_allow_html=True)

# ── SPREADSHEET ───────────────────────────────────────────────────────────────
SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1n9GW1UksZ-jhCQ-zmCqwx4EH20fa-Zm5wA5BiMmdZAE/edit?gid=713116247#gid=713116247"
)

# FIXED: Correct axis layout properties (removed unsupported 'weight' and 'title_font')
_AX = dict(
    gridcolor="rgba(28,43,58,0.08)",
    linecolor="rgba(28,43,58,0.2)",
    tickcolor="rgba(28,43,58,0.2)",
    showgrid=True,
    tickfont=dict(color="#1C2B3A", size=12, family="DM Sans, sans-serif"),
    title=dict(font=dict(color="#1C2B3A", size=14, family="DM Sans, sans-serif"))
)

_HOVERLABEL = dict(
    bgcolor="white",
    bordercolor="#F5C200",
    borderwidth=4,
    font=dict(color="#1C2B3A", size=28, family="DM Sans, sans-serif"),
    namelength=-1,
)

_BASE = dict(
    paper_bgcolor="#f0ede5",
    plot_bgcolor="#F0EDE5",
    font=dict(color="#1C2B3A", family="DM Sans, sans-serif", size=12),
    legend=dict(
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#D9D5C8",
        borderwidth=1,
        font=dict(size=12, color="#1C2B3A", family="DM Sans, sans-serif")
    ),
    hoverlabel=_HOVERLABEL,
    margin=dict(l=20, r=20, t=42, b=20),
    xaxis=_AX,
    yaxis=_AX,
)

def _layout(fig, height=None, extra=None):
    """Apply consistent layout with large popup (hover) styling."""
    kw = dict(**_BASE)
    if height:
        kw["height"] = height
    if extra:
        kw.update(extra)
    fig.update_layout(**kw)
    # Ensure all traces also inherit the large hoverlabel
    fig.update_traces(hoverlabel=_HOVERLABEL)
    return fig

C_ISD = "#1C2B3A"
C_OSD = "#8A6A00"
C_SUB = "#6B7E91"
C_AMB = "#E05C3A"
C_PUR = "#2E7D6B"

# ── UTILITY ───────────────────────────────────────────────────────────────────
def _safe(row, col, default=0.0):
    if row is None: return default
    try:
        if isinstance(row, dict): v = row.get(col, default)
        else: v = row[col] if col in row.index else default
        return float(v) if pd.notna(v) else default
    except Exception: return default

def _safe_multi(row, *cols, default=0.0):
    for col in cols:
        v = _safe(row, col, default=None)
        if v is not None and v != 0.0: return v
    return default

def _fix_year(s):
    cy = pd.Timestamp.now().year
    bad = s.dt.year < 2000
    if bad.any():
        s = s.copy()
        s[bad] = s[bad].apply(lambda t: t.replace(year=cy) if pd.notna(t) else t)
    return s

def _parse_dates(col):
    return _fix_year(pd.to_datetime(col.astype(str).str.strip(), dayfirst=True, errors="coerce"))

def _to_date(ts_series):
    return pd.to_datetime(ts_series.dt.date)

def _nums(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(
                df[c].astype(str).str.replace(",", "").str.replace("%", ""),
                errors="coerce").fillna(0)
    return df

# ── DATA LOAD ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Dashboard_Card", header=None)
        raw.columns = [str(c).strip() for c in raw.iloc[1]]
        raw = raw.iloc[2:].reset_index(drop=True)
        raw = raw[~raw["Date"].astype(str).str.contains(
            "Grand Total|Date|nan|Backlog|ISD Backlog", case=False, na=True)]
        raw["Date"] = _parse_dates(raw["Date"])
        raw = raw.dropna(subset=["Date"])
        raw["Date"] = _to_date(raw["Date"])
        raw = _nums(raw, [c for c in raw.columns if c != "Date"])
        raw["Date_Label"] = raw["Date"].dt.strftime("%d %b")
        dc = raw
    except Exception: dc = pd.DataFrame()

    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="FID_Tracking")
        raw.columns = [str(c).strip() for c in raw.columns]
        raw = raw[~raw.iloc[:, 0].astype(str).str.contains(
            "Grand Total|Report Date|nan", case=False, na=True)]
        raw.rename(columns={raw.columns[0]: "Date"}, inplace=True)
        raw["Date"] = _parse_dates(raw["Date"])
        raw = raw.dropna(subset=["Date"])
        raw["Date"] = _to_date(raw["Date"])
        raw = _nums(raw, list(raw.columns[1:]))
        raw["Date_Label"] = raw["Date"].dt.strftime("%d %b")
        ft = raw
    except Exception: ft = pd.DataFrame()

    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="FID_RID_Backlog_Details")
        raw.columns = [str(c).strip() for c in raw.columns]
        raw = raw[~raw.iloc[:, 0].astype(str).str.contains(
            "Grand Total|Date|nan", case=False, na=True)]
        raw.rename(columns={raw.columns[0]: "Date"}, inplace=True)
        raw["Date"] = _parse_dates(raw["Date"])
        raw = raw.dropna(subset=["Date"])
        raw["Date"] = _to_date(raw["Date"])
        raw = _nums(raw, list(raw.columns[1:]))
        raw["Date_Label"] = raw["Date"].dt.strftime("%d %b")
        fr = raw
    except Exception: fr = pd.DataFrame()

    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Aging_Distribution")
        raw = raw.iloc[:, :14]
        raw.columns = ["Date", "Region"] + [str(i) for i in range(1, 11)] + ["10+", "Total"]
        raw = raw[~raw["Date"].astype(str).str.contains(
            "Grand Total|Report Date|nan", case=False, na=True)]
        raw["Date"] = _parse_dates(raw["Date"])
        raw = raw.dropna(subset=["Date"])
        raw["Date"] = _to_date(raw["Date"])
        raw["Region"] = raw["Region"].astype(str).str.strip()
        raw = _nums(raw, [str(i) for i in range(1, 11)] + ["10+", "Total"])
        raw["Date_Label"] = raw["Date"].dt.strftime("%d %b")
        ag = raw
    except Exception: ag = pd.DataFrame()

    return dc, ft, fr, ag

with st.spinner("🐝 Loading live data…"):
    dc, ft, fr, ag = load_data()

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dash-header">
  <div class="dash-bee">🐝</div>
  <div>
    <div class="dash-title">Carrybee Delivery Intelligence</div>
    <div class="dash-subtitle">Live Backlog &amp; Operations Dashboard </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── DATE + REGION FILTER ──────────────────────────────────────────────────────
with st.container(border=True):
    fc1, fc2, _sp = st.columns([2, 2, 4])

    all_dates_ft = sorted(ft["Date"].dropna().unique()) if not ft.empty else []
    all_dates_ag = sorted(ag["Date"].dropna().unique()) if not ag.empty else []
    all_dates    = sorted(set(list(all_dates_ft) + list(all_dates_ag)))

    if all_dates:
        date_opts = [pd.Timestamp(d).strftime("%d %b %Y") for d in all_dates]
        with fc1:
            sel_di = st.selectbox("📅 Report Date", range(len(date_opts)),
                                  format_func=lambda i: date_opts[i],
                                  index=len(date_opts) - 1)
        sel_date  = pd.Timestamp(all_dates[sel_di])
        sel_start = sel_date
        sel_end   = sel_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    else:
        sel_date  = pd.Timestamp.now().normalize()
        sel_start = sel_date
        sel_end   = sel_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    with fc2:
        region_filter = st.multiselect("🗺️ Region", ["ISD", "OSD"], default=["ISD", "OSD"])

# ── ROW HELPERS ───────────────────────────────────────────────────────────────
def _latest(df):
    if df is None or df.empty: return None
    sub = df[df["Date"] <= sel_end].sort_values("Date")
    return sub.iloc[-1] if not sub.empty else None

def _prev(df):
    if df is None or df.empty: return None
    sub = df[df["Date"] <= sel_end].sort_values("Date")
    return sub.iloc[-2] if len(sub) >= 2 else None

lt_dc = _latest(dc);  lt_fr = _latest(fr)
pr_dc = _prev(dc);    pr_fr = _prev(fr)

# ── COMPUTED KPIs ─────────────────────────────────────────────────────────────
ag_le = ag[ag["Date"] <= sel_end] if not ag.empty else pd.DataFrame()
if not ag_le.empty:
    ag_last_date = ag_le["Date"].max()
    ag_day       = ag_le[ag_le["Date"] == ag_last_date]
    isd_total    = ag_day[ag_day["Region"] == "ISD"]["Total"].sum()
    osd_total    = ag_day[ag_day["Region"] == "OSD"]["Total"].sum()
    tot_fid      = isd_total + osd_total
    prev_ag_dates = ag_le[ag_le["Date"] < ag_last_date]["Date"]
    if not prev_ag_dates.empty:
        pr_ag_day = ag_le[ag_le["Date"] == prev_ag_dates.max()]
        pr_fid = (pr_ag_day[pr_ag_day["Region"] == "ISD"]["Total"].sum()
                + pr_ag_day[pr_ag_day["Region"] == "OSD"]["Total"].sum())
    else:
        pr_fid = tot_fid
else:
    isd_total = osd_total = tot_fid = pr_fid = 0.0

fid_bl     = _safe(lt_fr, "FID Backlog")
rid_bl     = _safe(lt_fr, "RID Backlog")
overall_bl = fid_bl + rid_bl
pr_overall = _safe(pr_fr, "FID Backlog") + _safe(pr_fr, "RID Backlog")

zt_val    = _safe(lt_dc, "Zone Transfer", default=0.0)
pr_zt_val = _safe(pr_dc, "Zone Transfer", default=0.0)

dc_total_val = _safe(lt_dc, "Total")
denom        = dc_total_val if dc_total_val > 0 else tot_fid
fid_pct      = (fid_bl / denom * 100) if denom > 0 else 0.0
pr_dc_total  = _safe(pr_dc, "Total")
pr_denom     = pr_dc_total if pr_dc_total > 0 else pr_fid
pr_fid_pct   = (_safe(pr_fr, "FID Backlog") / pr_denom * 100) if pr_denom > 0 else 0.0

zt_pct    = (zt_val / dc_total_val * 100) if (zt_val > 0 and dc_total_val > 0) else 0.0
pr_zt_pct = (pr_zt_val / pr_dc_total * 100) if (pr_zt_val > 0 and pr_dc_total > 0) else 0.0

# ── SPARKLINE HELPERS ─────────────────────────────────────────────────────────
def _last7_ag_total():
    if ag_le.empty: return []
    dates = sorted(ag_le["Date"].unique())[-7:]
    return [ag_le[ag_le["Date"] == d]["Total"].sum() for d in dates]

def _last7_bl():
    if fr.empty: return []
    sub = fr[fr["Date"] <= sel_end].sort_values("Date").tail(7)
    if "FID Backlog" not in sub.columns: return []
    rid = sub["RID Backlog"] if "RID Backlog" in sub.columns else 0
    return (sub["FID Backlog"] + rid).tolist()

def _last7_zt():
    if dc.empty: return []
    sub = dc[dc["Date"] <= sel_end].sort_values("Date").tail(7)
    return sub["Zone Transfer"].tolist() if "Zone Transfer" in sub.columns else []

spark_fid = _last7_ag_total()
spark_bl  = _last7_bl()
spark_zt  = _last7_zt()

def _sparkline_svg(values, color, width=110, height=40):
    if not values or len(values) < 2: return ""
    mn, mx = min(values), max(values)
    rng = mx - mn if mx != mn else 1
    pad = 4
    pts = []
    for i, v in enumerate(values):
        x = pad + (i / (len(values) - 1)) * (width - 2 * pad)
        y = pad + (1 - (v - mn) / rng) * (height - 2 * pad)
        pts.append(f"{x:.1f},{y:.1f}")
    area = (f"M{pts[0]} " + " ".join(f"L{p}" for p in pts[1:])
            + f" L{width-pad},{height} L{pad},{height} Z")
    last_x, last_y = pts[-1].split(",")
    uid = color.replace("#", "")
    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g{uid}" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{color}" stop-opacity="0.3"/>
    <stop offset="100%" stop-color="{color}" stop-opacity="0.02"/>
  </linearGradient></defs>
  <path d="{area}" fill="url(#g{uid})"/>
  <polyline points="{' '.join(pts)}" fill="none" stroke="{color}" stroke-width="2.2"
            stroke-linejoin="round" stroke-linecap="round"/>
  <circle cx="{last_x}" cy="{last_y}" r="3.5" fill="{color}"/>
</svg>"""

def _trend_color(values, lower_is_better=True):
    if not values or len(values) < 2: return "#1C2B3A"
    improving = values[-1] < values[-2] if lower_is_better else values[-1] > values[-2]
    return "#2E7D6B" if improving else "#E05C3A"

fid_color = _trend_color(spark_fid, lower_is_better=True)
bl_color  = _trend_color(spark_bl,  lower_is_better=True)
zt_color  = _trend_color(spark_zt,  lower_is_better=False)

# ══════════════════════════════════════════════════════════════════════════════
#  KPI CARD RENDERERS
# ══════════════════════════════════════════════════════════════════════════════

def _spark_kpi(col_w, label, value_str, spark_svg, delta_val,
               lower_is_better=True, card_bg="#FDF3BF",
               static_color=None, icon_type=None):
    """Renders a KPI card using inline SVG icons — no external file loading."""
    d = delta_val
    arr = "▼" if d < 0 else ("▲" if d > 0 else "—")

    if static_color:
        delta_style = f"color:{static_color};"
        d_cls = ""
    else:
        d_cls = (
            "delta-down-good" if (d < 0 and lower_is_better) else
            "delta-up-good"   if (d > 0 and not lower_is_better) else
            "delta-up-bad"    if d > 0 else
            "delta-down-bad"  if d < 0 else
            "delta-neutral"
        )
        delta_style = ""

    # Use inline SVG icon — safe, no file I/O
    icon_html = get_icon_svg(icon_type, size_px=48) if icon_type else ""

    col_w.markdown(f"""
    <div class="kpi-spark"
         style="background-color:{card_bg} !important; border-color:{card_bg} !important;">
      <div class="kpi-icon-top">{icon_html}</div>
      <div class="kpi-label">{label}</div>
      <div class="kpi-center-val">{value_str}</div>
      <div class="kpi-footer">
        <span class="{d_cls}" style="font-size:15px; font-weight:700; {delta_style}">
          {arr} {abs(d):,.0f}
        </span>
        <span>{spark_svg}</span>
      </div>
    </div>""", unsafe_allow_html=True)


def _pct_kpi(col_w, label, value, prev_value, lower_is_better=True):
    """Percentage KPI card."""
    diff    = value - prev_value
    good    = (diff < 0 and lower_is_better) or (diff > 0 and not lower_is_better)
    v_color = "#2E7D6B" if good else ("#E05C3A" if diff != 0 else "#1C2B3A")
    arr     = "▼" if diff < 0 else ("▲" if diff > 0 else "—")
    d_cls   = (
        "delta-down-good" if (diff < 0 and lower_is_better) else
        "delta-up-good"   if (diff > 0 and not lower_is_better) else
        "delta-up-bad"    if diff > 0 else
        "delta-down-bad"  if diff < 0 else
        "delta-neutral"
    )

    col_w.markdown(f"""
    <div class="kpi-small">
      <div class="kpi-label" style="margin-top:10px;">{label}</div>
      <div class="kpi-center-val" style="color:{v_color};">{value:.2f}%</div>
      <div class="kpi-footer">
        <span class="{d_cls}" style="font-size:15px; font-weight:700;">
          {arr} {abs(diff):.2f}
        </span>
      </div>
    </div>""", unsafe_allow_html=True)

# ── ROW 1: 3 KPI cards + Donut ───────────────────────────────────────────────
kc1, kc2, kc3, kc4 = st.columns([1, 1, 1, 1])

d_fid_v = tot_fid - pr_fid
d_bl_v  = overall_bl - pr_overall
d_zt_v  = zt_val - pr_zt_val

with kc1:
    _spark_kpi(
        col_w=kc1,
        label="Total In-Process (FID)",
        value_str=f"{tot_fid:,.0f}",
        spark_svg=_sparkline_svg(spark_fid, "#E05C3A"),
        delta_val=d_fid_v,
        lower_is_better=True,
        card_bg="#e3d6b3",
        static_color="#E05C3A",
        icon_type="fid",
    )

with kc2:
    _spark_kpi(
        col_w=kc2,
        label="Overall Backlog",
        value_str=f"{overall_bl:,.0f}",
        spark_svg=_sparkline_svg(spark_bl, bl_color),
        delta_val=d_bl_v,
        lower_is_better=True,
        icon_type="backlog",
    )

with kc3:
    is_good    = d_zt_v <= 0
    zt_display = f"{int(zt_val):,}" if zt_val > 0 else "0"
    _spark_kpi(
        col_w=kc3,
        label="Zone Transfer Parcels",
        value_str=zt_display,
        spark_svg=_sparkline_svg(spark_zt, "#2E7D6B" if is_good else "#E05C3A"),
        delta_val=d_zt_v,
        lower_is_better=True,
        icon_type="zone",
    )

with kc4:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr" style="margin-bottom:8px;">Backlog — FID vs RID</div>',
                    unsafe_allow_html=True)
        if (fid_bl + rid_bl) > 0:
            fid_pct_donut = fid_bl / (fid_bl + rid_bl) * 100
            rid_pct_donut = rid_bl / (fid_bl + rid_bl) * 100
            fig_donut = go.Figure(data=[go.Pie(
                labels=["FID", "RID"], values=[fid_bl, rid_bl],
                hole=0.55,
                marker=dict(colors=["#F5C200", "#1C2B3A"], line=dict(color="#8A6A00", width=3)),
                textinfo="label+percent", textposition="outside",
                textfont=dict(size=12, color="#1C2B3A", family="DM Sans, sans-serif"),
                pull=[0.05, 0.05],
                hovertemplate="<b>%{label}</b><br>Count: %{value:,.0f}<br>Share: %{percent}<extra></extra>",
            )])
            fig_donut.add_annotation(
                text=f"<b>{int(fid_bl+rid_bl):,}</b><br><span style='font-size:10px;color:#6B7E91'>Total</span>",
                x=0.5, y=0.5, showarrow=False, xanchor="center", yanchor="middle",
                font=dict(size=15, color="#1C2B3A", family="DM Sans, sans-serif"),
            )
            _layout(fig_donut, height=180,
                    extra={"margin": dict(l=12, r=10, t=20, b=0), "showlegend": False})
            st.plotly_chart(fig_donut, use_container_width=True)
            st.markdown(f"""
            <div style="display:flex;gap:0;border-top:8px solid #E8E4DB;padding-top:8px;">
              <div style="flex:1;text-align:center;border-right:8px solid #E8E4DB;">
                <div style="font-size:10px;font-weight:700;text-transform:uppercase;color:#8A6A00;margin-bottom:2px;">FID</div>
                <div style="font-size:18px;font-weight:700;color:#1C2B3A;font-family:'DM Mono',monospace;">{fid_bl:,.0f}</div>
                <div style="font-size:10px;color:#6B7E91;font-weight:600;">{fid_pct_donut:.1f}%</div>
              </div>
              <div style="flex:1;text-align:center;">
                <div style="font-size:10px;font-weight:700;text-transform:uppercase;color:#1C2B3A;margin-bottom:2px;">RID</div>
                <div style="font-size:18px;font-weight:700;color:#1C2B3A;font-family:'DM Mono',monospace;">{rid_bl:,.0f}</div>
                <div style="font-size:10px;color:#6B7E91;font-weight:600;">{rid_pct_donut:.1f}%</div>
              </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("No backlog data.")

# ── ROW 2: Percentage KPI cards ───────────────────────────────────────────────
kr1, kr2, _sp1, _sp2 = st.columns([1, 1, 1, 1])

with kr1:
    _pct_kpi(col_w=kr1, label="FID Backlog %",
             value=fid_pct, prev_value=pr_fid_pct, lower_is_better=True)
with kr2:
    _pct_kpi(col_w=kr2, label="Zone Change %",
             value=zt_pct, prev_value=pr_zt_pct, lower_is_better=True)

# ── ROW 3: Backlog Details + Sort ─────────────────────────────────────────────
col_bl, col_sort = st.columns([3, 2])

with col_bl:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">Backlog Details</div>',
                    unsafe_allow_html=True)
        if lt_fr is not None:
            detail_rows = [
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
            labels, isd_v, sub_v, osd_v, tots = zip(*detail_rows)
            fig9 = go.Figure()
            for vals, name, color in [(isd_v,"ISD",C_ISD),(sub_v,"SUB",C_SUB),(osd_v,"OSD",C_OSD)]:
                fig9.add_trace(go.Bar(
                    name=name, y=labels, x=vals, orientation="h", marker_color=color,
                    text=[f"{v:,.0f}" if v > 0 else "" for v in vals],
                    textposition="inside", insidetextanchor="middle",
                    textfont=dict(color="#FFFFFF", size=13, family="DM Sans, sans-serif"),
                ))
            for lbl, tot in zip(labels, tots):
                if tot > 0:
                    fig9.add_annotation(x=tot, y=lbl, text=f"  <b>{tot:,.0f}</b>",
                                        showarrow=False, xanchor="left",
                                        font=dict(size=14, color="#1C2B3A", family="DM Sans, sans-serif"))
            _layout(fig9, height=380, extra={
                "barmode": "stack",
                "xaxis": dict(**_AX, title="Count"),
                "yaxis": dict(**_AX, autorange="reversed"),
            })
            st.plotly_chart(fig9, use_container_width=True)
        else:
            st.info("No backlog detail data.")

with col_sort:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">Backlog Details(Sort)</div>',
                    unsafe_allow_html=True)
        if lt_fr is not None:
            fid_sort = _safe(lt_fr, "FID Sort")
            rid_sort = _safe_multi(lt_fr, "RID Sort", "RID LMH Sort")
            fig10 = go.Figure(data=[go.Bar(
                y=["FID Sort", "RID Sort"], x=[fid_sort, rid_sort],
                orientation="h", marker_color=[C_ISD, C_OSD],
                marker_line=dict(color="#8A6A00", width=1),
                text=[f"{fid_sort:,.0f}", f"{rid_sort:,.0f}"], textposition="outside",
                textfont=dict(size=14, color="#1C2B3A", family="DM Sans, sans-serif"), width=0.5,
            )])
            _layout(fig10, height=380, extra={
                "showlegend": False,
                "xaxis": dict(**_AX, title="Count"),
                "yaxis": dict(**_AX),
                "margin": dict(l=8, r=70, t=32, b=8),
            })
            st.plotly_chart(fig10, use_container_width=True)
        else:
            st.info("No sort data.")

# ── ROW 4: Backlog Tracking + Region ──────────────────────────────────────────
col_track, col_region = st.columns([3, 2])

with col_track:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">Date-wise Backlog Progress Tracking (FID)</div>',
                    unsafe_allow_html=True)
        if all_dates and len(all_dates) >= 1:
            t_opts = [pd.Timestamp(d).strftime("%d %b %Y") for d in all_dates]
            tc1, tc2 = st.columns(2)
            with tc1:
                t_si = st.selectbox("📅 From", range(len(t_opts)),
                                    format_func=lambda i: t_opts[i], index=0, key="track_from")
            with tc2:
                t_ei = st.selectbox("📅 To", range(len(t_opts)),
                                    format_func=lambda i: t_opts[i],
                                    index=len(t_opts) - 1, key="track_to")
            if t_ei < t_si: t_ei = t_si
            t_start  = pd.Timestamp(all_dates[t_si])
            t_end    = pd.Timestamp(all_dates[t_ei]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            ft_range = (ft[(ft["Date"] >= t_start) & (ft["Date"] <= t_end)].sort_values("Date")
                        if not ft.empty else pd.DataFrame())
        else:
            ft_range = pd.DataFrame()
            t_start  = sel_start
            t_end    = sel_end

        if not ft_range.empty:
            fig_track = go.Figure()
            if "Total In Progress (Backlog)" in ft_range.columns:
                fig_track.add_trace(go.Bar(
                    x=ft_range["Date_Label"], y=ft_range["Total In Progress (Backlog)"],
                    name="Total In Process (FID)", marker_color=C_ISD, opacity=0.9,
                ))
            if "Worked On" in ft_range.columns:
                fig_track.add_trace(go.Bar(
                    x=ft_range["Date_Label"], y=ft_range["Worked On"],
                    name="Worked On", marker_color=C_SUB, opacity=0.9,
                ))
            _layout(fig_track, height=380, extra={"barmode": "group"})
            st.plotly_chart(fig_track, use_container_width=True)
        else:
            st.info("No FID tracking data for selected period.")

with col_region:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">Region Wise In-Process Parcels</div>',
                    unsafe_allow_html=True)
        if tot_fid > 0:
            df_reg = pd.DataFrame({"Region": ["ISD", "OSD"], "Parcels": [isd_total, osd_total]})
            fig_reg = px.bar(df_reg, x="Region", y="Parcels",
                             color="Region", color_discrete_map={"ISD": C_ISD, "OSD": C_OSD},
                             text="Parcels")
            fig_reg.update_traces(
                texttemplate="%{text:,.0f}", textposition="outside",
                textfont=dict(color="#1C2B3A", size=14, family="DM Sans, sans-serif"),
                width=0.5,
            )
            _layout(fig_reg, height=300, extra={
                "showlegend": False,
                "yaxis": dict(**_AX, title="Parcels"),
                "xaxis": dict(**_AX, title=""),
            })
            st.plotly_chart(fig_reg, use_container_width=True)
            st.markdown(f"""
            <div style="display:flex;gap:16px;justify-content:center;padding:12px 0 4px;
                        border-top:8px solid rgba(28,43,58,0.15);">
              <div style="text-align:center;flex:1;border-right:8px solid rgba(28,43,58,0.15);">
                <div style="font-size:13px;color:#1C2B3A;font-weight:700;text-transform:uppercase;
                            letter-spacing:0.8px;margin-bottom:4px;">ISD</div>
                <div style="font-size:26px;font-weight:700;color:{C_ISD};
                            font-family:'DM Mono',monospace;">{isd_total:,.0f}</div>
              </div>
              <div style="text-align:center;flex:1;border-right:8px solid rgba(28,43,58,0.15);">
                <div style="font-size:13px;color:#1C2B3A;font-weight:700;text-transform:uppercase;
                            letter-spacing:0.8px;margin-bottom:4px;">OSD</div>
                <div style="font-size:26px;font-weight:700;color:{C_OSD};
                            font-family:'DM Mono',monospace;">{osd_total:,.0f}</div>
              </div>
              <div style="text-align:center;flex:1;">
                <div style="font-size:13px;color:#1C2B3A;font-weight:700;text-transform:uppercase;
                            letter-spacing:0.8px;margin-bottom:4px;">Total</div>
                <div style="font-size:26px;font-weight:700;color:#1C2B3A;
                            font-family:'DM Mono',monospace;">{tot_fid:,.0f}</div>
              </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("No region data.")

# ── ROW 5: Aging Distribution + Table ─────────────────────────────────────────
AGE_COLS = [str(i) for i in range(1, 11)] + ["10+"]
ag_f = (ag[(ag["Date"] >= sel_start) & (ag["Date"] <= sel_end)].copy()
        if not ag.empty else pd.DataFrame())
if not ag_f.empty and "Region" in ag_f.columns:
    ag_f = ag_f[ag_f["Region"].isin(region_filter)]

col_aging, col_aging_tbl = st.columns([3, 2])

with col_aging:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">Aging Distribution</div>', unsafe_allow_html=True)
        st.markdown('<div class="aging-badge">ISD &amp; SUB = 4 Days+ &nbsp;|&nbsp; OSD = 5 Days+</div>',
                    unsafe_allow_html=True)
        if not ag_f.empty:
            ag_max   = ag_f["Date"].max()
            ag_day_f = ag_f[ag_f["Date"] == ag_max].copy()
            rows8 = []
            for _, row in ag_day_f.iterrows():
                region = str(row.get("Region", "")).strip()
                if region not in region_filter: continue
                total = float(row.get("Total", 0) or 0)
                if total == 0:
                    total = sum(float(row[c]) for c in AGE_COLS
                                if c in ag_day_f.columns and pd.notna(row[c]))
                for c in AGE_COLS:
                    if c in ag_day_f.columns:
                        val = float(row[c]) if pd.notna(row[c]) else 0.0
                        pct = val / total * 100 if total > 0 else 0.0
                        rows8.append({"Region": region, "Age": f"{c}d", "Count": val, "Pct": pct})
            ag_melt = pd.DataFrame(rows8)
            if not ag_melt.empty:
                max_slider_val = max(5.0, float(ag_melt["Pct"].max()) + 5.0)
                y_zoom = st.slider("🔍 Adjust Y-Axis Zoom (%)", min_value=0.0,
                                   max_value=max_slider_val,
                                   value=(0.0, max_slider_val), step=1.0)
                fig8 = px.bar(ag_melt, x="Age", y="Pct", color="Region",
                              color_discrete_map={"ISD": C_ISD, "OSD": C_OSD},
                              barmode="group",
                              text=ag_melt["Pct"].apply(lambda x: f"{x:.1f}%"))
                fig8.update_traces(
                    textposition="outside", textfont=dict(color="#1C2B3A", size=11, family="DM Sans, sans-serif"),
                    customdata=ag_melt[["Count", "Region"]],
                    hovertemplate="<b>%{x}</b><br>Region: %{customdata[1]}<br>"
                                  "Count: %{customdata[0]:,.0f}<br>Pct: %{y:.1f}%",
                )
                _layout(fig8, height=380, extra={
                    "yaxis": dict(**_AX, title="Percentage (%)", range=[y_zoom[0], y_zoom[1]])
                })
                st.plotly_chart(fig8, use_container_width=True)
            else:
                st.info("No aging data.")
        else:
            st.info("No aging distribution data available.")

with col_aging_tbl:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">Aging Count &amp; % by Region</div>', unsafe_allow_html=True)
        if not ag_f.empty:
            ag_day_f2 = ag_f[ag_f["Date"] == ag_f["Date"].max()].copy()
            isd_row = (ag_day_f2[ag_day_f2["Region"] == "ISD"].iloc[0]
                       if "ISD" in ag_day_f2["Region"].values else None)
            osd_row = (ag_day_f2[ag_day_f2["Region"] == "OSD"].iloc[0]
                       if "OSD" in ag_day_f2["Region"].values else None)
            isd_tot_v = float(isd_row["Total"]) if isd_row is not None else 0
            osd_tot_v = float(osd_row["Total"]) if osd_row is not None else 0
            th = "<th>Days</th>"
            if isd_row is not None: th += "<th>ISD Count</th><th>ISD %</th>"
            if osd_row is not None: th += "<th>OSD Count</th><th>OSD %</th>"
            body_rows = ""
            for c in AGE_COLS:
                if c not in ag_day_f2.columns: continue
                td = f"<td><b>{c}d</b></td>"
                if isd_row is not None:
                    v = float(isd_row[c]) if pd.notna(isd_row[c]) else 0
                    td += (f"<td>{v:,.0f}</td><td>{v/isd_tot_v*100:.1f}%</td>"
                           if isd_tot_v else "<td>—</td><td>—</td>")
                if osd_row is not None:
                    v = float(osd_row[c]) if pd.notna(osd_row[c]) else 0
                    td += (f"<td>{v:,.0f}</td><td>{v/osd_tot_v*100:.1f}%</td>"
                           if osd_tot_v else "<td>—</td><td>—</td>")
                body_rows += f"<tr>{td}</tr>"
            td_tot = "<td><b>Total</b></td>"
            if isd_row is not None: td_tot += f"<td><b>{isd_tot_v:,.0f}</b></td><td><b>100%</b></td>"
            if osd_row is not None: td_tot += f"<td><b>{osd_tot_v:,.0f}</b></td><td><b>100%</b></td>"
            body_rows += f"<tr>{td_tot}</tr>"
            st.markdown(f"""
            <div style="overflow-x:auto;max-height:430px;overflow-y:auto;
                        border:8px solid #C4C0B3;border-radius:16px;">
            <table class="styled-table" style="margin:0;">
              <thead><tr>{th}</tr></thead>
              <tbody>{body_rows}</tbody>
            </table></div>""", unsafe_allow_html=True)
        else:
            st.info("No aging data.")

# ── ROW 6: Full FID Tracking Table ────────────────────────────────────────────
with st.container(border=True):
    st.markdown('<div class="sec-hdr">Date-wise Backlog Progress Tracking — Full Table (FID)</div>',
                unsafe_allow_html=True)
    try:
        ft_tbl = (ft[(ft["Date"] >= t_start) & (ft["Date"] <= t_end)]
                  .sort_values("Date").copy() if not ft.empty else pd.DataFrame())
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
        show_cols = [c for c in COL_MAP if c in ft_tbl.columns]
        df_tbl    = ft_tbl[show_cols].rename(columns=COL_MAP)
        headers   = "".join(f"<th>{c}</th>" for c in df_tbl.columns)
        body      = ""
        for i, (_, r) in enumerate(df_tbl.iterrows()):
            is_last = i == len(df_tbl) - 1
            cells   = ""
            for j, v in enumerate(r):
                cls = "col-date" if j == 0 else ("col-high" if is_last else "")
                try:
                    disp = v if j == 0 else (f"{int(float(v)):,}" if float(v) != 0 else "—")
                except Exception:
                    disp = "—"
                cells += f"<td class='{cls}'>{disp}</td>"
            body += f"<tr>{cells}</tr>"
        st.markdown(f"""
        <div style="overflow-x:auto;border:8px solid #C4C0B3;border-radius:16px;">
        <table class="styled-table" style="margin:0;">
          <thead><tr>{headers}</tr></thead>
          <tbody>{body}</tbody>
        </table></div>""", unsafe_allow_html=True)
    else:
        st.info("No FID tracking data to display.")

# ── APPENDIX ──────────────────────────────────────────────────────────────────
with st.expander("📖 Appendix — Definitions & Calculation Methods", expanded=False):
    st.markdown('<div class="appendix-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr" style="border:none;">📊 KPI Definitions & Calculation Methods</div>',
                unsafe_allow_html=True)
    items = [
        ("1. Total In-Process (FID)", "All parcels currently in the First Inbound Delivery process on the selected date.", "Aging_Distribution → ISD Total + OSD Total"),
        ("2. Overall Backlog (FID+RID)", "Total undelivered backlog across FID and RID.", "FID Backlog + RID Backlog  (Source: FID_RID_Backlog_Details)"),
        ("3. Zone Transfer Parcels", "Parcels transferred between delivery zones on the selected date.", "Dashboard_Card → 'Zone Transfer' column"),
        ("4. Backlog — FID vs RID (Donut)", "Visual split of overall backlog between FID and RID.", "FID Backlog and RID Backlog from FID_RID_Backlog_Details"),
        ("5. FID Backlog %", "Percentage of total in-process FID parcels in backlog.", "FID Backlog ÷ Total In-Process × 100"),
        ("6. Zone Change %", "Share of total parcels that underwent a zone transfer.", "Zone Transfer ÷ Total (Dashboard_Card) × 100"),
        ("7. Backlog Details", "Stacked bar breakdown by service type and region.", "FID_RID_Backlog_Details → FID/RID × LMH/FMH × ISD/SUB/OSD columns"),
        ("8. Sort — FID Sort vs RID Sort", "Horizontal bar comparing parcels sorted through each pipeline.", "FID_RID_Backlog_Details → 'FID Sort' and 'RID Sort'"),
        ("9. Date-wise Backlog Progress Tracking", "Grouped bar chart over a custom date range.", "FID_Tracking → 'Total In Progress (Backlog)' and 'Worked On'"),
        ("10. Region Wise In-Process Parcels", "Vertical bars comparing ISD vs OSD parcel counts.", "Aging_Distribution → ISD Total and OSD Total"),
        ("11. Aging Distribution", "Percentage of parcels per day-bucket (1d → 10+d) by region.", "Aging_Distribution — columns 1 through 10+"),
        ("ISD", "Inbound Standard Delivery", ""),
        ("OSD", "Outbound Standard Delivery", ""),
        ("SUB", "Sub-hub (intermediate processing)", ""),
        ("LMH", "Last Mile Hub — final hub before customer delivery", ""),
        ("FMH", "First Mile Hub — entry point into the network", ""),
        ("FID", "First Inbound Delivery cycle", ""),
        ("RID", "Return Inbound Delivery — re-entered returned parcels", ""),
    ]
    for key, desc, formula in items:
        formula_html = f'<br><span style="color:#6B7E91;font-size:12px;">{formula}</span>' if formula else ""
        st.markdown(f"""
        <div style="margin-bottom:12px;">
          <div style="font-weight:700;color:#1C2B3A;">▸ {key}</div>
          <div style="color:#1C2B3A;padding-left:14px;">{desc}{formula_html}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;color:#6B7E91;font-size:13px;font-weight:700;
            padding:20px 0 10px;letter-spacing:0.5px;">
  🐝 Carrybee Delivery Intelligence &nbsp;·&nbsp;
  Report Date: <span style="color:#1C2B3A;">{sel_date.strftime('%d %b %Y')}</span>
  &nbsp;·&nbsp; Refreshes every 10 min &nbsp;·&nbsp; Powered by Google Sheets
</div>
""", unsafe_allow_html=True)
