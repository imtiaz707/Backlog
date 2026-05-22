import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dateutil import parser as dtparser
from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title="Carrybee Intelligence",
    page_icon="🐝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*, *::before, *::after { box-sizing: border-box; }
* { font-family: 'Inter', sans-serif; }

/* ── App Background: Deep Navy ── */
[data-testid="stAppViewContainer"] {
    background: #1C2B3A;
}
[data-testid="stHeader"]     { background: transparent; }
[data-testid="stToolbar"]    { display: none; }
[data-testid="stDecoration"] { display: none; }
.block-container {
    padding-top: 1.4rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 98% !important;
}

/* ── Header ── */
.dash-header {
    background: #1C2B3A;
    border-left: 6px solid #F5C200;
    border-radius: 12px;
    padding: 20px 30px;
    margin-bottom: 22px;
    display: flex;
    align-items: center;
    gap: 22px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.dash-bee { font-size: 44px; line-height: 1; filter: drop-shadow(0 2px 4px rgba(245,194,0,0.3)); }
.dash-title {
    color: #FFFFFF !important;
    font-size: 28px;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.5px;
}
.dash-subtitle {
    color: #F5C200 !important;
    font-size: 14px;
    margin-top: 5px;
    font-weight: 500;
}
.dash-live {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: #FFFFFF;
    font-weight: 600;
}
.live-dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: #2E7D6B;
    box-shadow: 0 0 8px rgba(46,125,107,0.8);
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%,100% { opacity:1; transform:scale(1); }
    50% { opacity:0.5; transform:scale(0.85); }
}

/* ── Filter bar (date slicer) ── */
.filter-wrap {
    background: #F0EDE5;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px 24px 14px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    display: flex;
    align-items: center;
    gap: 14px;
}
.date-chip {
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: 600;
    color: #6B7E91 !important;
    cursor: pointer;
    transition: all 0.2s;
}
.date-chip:hover, .date-chip.active {
    background: #FDF3BF;
    border-color: #F5C200;
    color: #8A6A00 !important;
}

/* ── KPI Cards: Warm White Surface ── */
.kpi-card {
    background: #F0EDE5;
    border-radius: 12px;
    padding: 22px 24px 18px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    position: relative;
    overflow: hidden;
    min-height: 165px;
    transition: box-shadow 0.3s;
}
.kpi-card:hover { box-shadow: 0 6px 16px rgba(0,0,0,0.15); }
.kpi-num   { font-size: 12px; font-weight: 700; text-transform: uppercase;
             letter-spacing: 1px; color: #6B7E91 !important; margin-bottom: 4px; }
.kpi-lbl   { font-size: 13px; font-weight: 600; text-transform: uppercase;
             letter-spacing: 0.5px; color: #1C2B3A !important; margin-bottom: 12px; }
.kpi-val   { font-size: 38px; font-weight: 800; line-height: 1;
             color: #1C2B3A !important; margin-bottom: 10px; letter-spacing: -0.5px; }

/* Specific value overrides if needed */
.kpi-val.g { color: #2E7D6B !important; }
.kpi-val.r { color: #E05C3A !important; }
.kpi-val.a { color: #C99B00 !important; }

/* ── Delta Badges ── */
.kpi-delta {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 13px; font-weight: 700;
    padding: 4px 10px; border-radius: 20px;
}
.kpi-delta.dg { color: #2E7D6B !important; background: rgba(46,125,107,0.15); }
.kpi-delta.dr { color: #E05C3A !important; background: rgba(224,92,58,0.15); }
.kpi-delta.dn { color: #6B7E91 !important; background: rgba(107,126,145,0.15); }

/* ── Small KPI (row 2) ── */
.kpi-sm {
    background: #F0EDE5;
    border-radius: 12px;
    padding: 20px 22px 16px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    min-height: 130px;
}
.kpi-sm-val {
    font-size: 36px; font-weight: 800; line-height: 1;
    color: #1C2B3A !important; margin-bottom: 10px;
}

/* ── Chart cards ── */
.cc {
    background: #F0EDE5;
    border-radius: 12px;
    padding: 20px 22px 14px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    margin-bottom: 18px;
}
.sec-hdr {
    font-size: 14px; font-weight: 700; color: #1C2B3A !important;
    text-transform: uppercase; letter-spacing: 0.8px;
    border-left: 4px solid #F5C200;
    padding-left: 10px; margin-bottom: 14px;
    border-bottom: 1px solid #D9D9D9; padding-bottom: 8px;
}

/* ── Badges ── */
.aging-badge {
    background: #FDF3BF; border: 1px solid #F5C200; border-radius: 6px;
    padding: 6px 12px; font-size: 12px; color: #8A6A00 !important;
    font-weight: 600; display: inline-block; margin-bottom: 12px;
}

/* ── Table ── */
.styled-table { width:100%; border-collapse:collapse; font-size:13px; }
.styled-table thead tr { background: #1C2B3A; }
.styled-table th {
    padding: 10px 12px; text-align: center; font-weight: 600;
    font-size: 12px; color: #F0EDE5 !important;
    text-transform: uppercase; letter-spacing: 0.5px;
}
.styled-table tbody tr { background: #FFFFFF; transition: background 0.15s; }
.styled-table tbody tr:nth-child(even) { background: rgba(28,43,58,0.03); }
.styled-table tbody tr:hover { background: rgba(245,194,0,0.1); }
.styled-table tbody tr:last-child { background: #FDF3BF; font-weight: 700; border-top: 2px solid #F5C200; }
.styled-table td {
    padding: 9px 12px; text-align: center;
    border-bottom: 1px solid #E2E8F0;
    color: #1C2B3A !important;
}
.styled-table .col-date { text-align:left; font-weight:600; color: #2E7D6B !important; }
.styled-table .col-high { color: #E05C3A !important; font-weight:700; }

/* ── Appendix ── */
.app-card {
    background: #F0EDE5; border-radius: 12px; padding: 24px 28px;
    border: 1px solid #E2E8F0; margin-bottom: 8px;
}
.app-title { font-size:16px; font-weight:700; color:#1C2B3A !important; margin-bottom:16px; border-bottom: 2px solid #F5C200; padding-bottom: 8px;}
.app-row { display:flex; gap:10px; margin-bottom:12px; align-items:flex-start; }
.app-key { font-size:13px; font-weight:700; color:#1C2B3A !important; min-width:230px; }
.app-val { font-size:13px; color:#6B7E91 !important; line-height:1.5; }
.app-form {
    font-family: 'Inter', monospace; font-size:11px;
    background: #FDF3BF; border: 1px solid #F9DE7A;
    border-radius:5px; padding:3px 9px; color:#8A6A00 !important;
    display:inline-block; margin-top:4px; font-weight: 600;
}

/* Streamlit widget label overrides for Light Cards */
label, .stSelectbox label, [data-testid="stWidgetLabel"] p {
    color: #6B7E91 !important; font-size: 12px !important;
    font-weight: 600 !important; text-transform: uppercase !important;
}
[data-testid="stSelectbox"] > div > div {
    background: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 8px !important;
    color: #1C2B3A !important;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1n9GW1UksZ-jhCQ-zmCqwx4EH20fa-Zm5wA5BiMmdZAE/edit?gid=713116247#gid=713116247"
)

# New Industry-Standard Palette mapping
C_ISD = "#F5C200" # Golden Yellow
C_OSD = "#E05C3A" # Burnt Coral
C_SUB = "#2E7D6B" # Teal Green
C_AMB = "#1C2B3A" # Deep Navy (Totals/Neutral)
C_PUR = "#6B7E91" # Slate Gray

_AX = dict(
    gridcolor="rgba(28,43,58,0.1)",
    linecolor="rgba(28,43,58,0.2)",
    tickcolor="rgba(28,43,58,0.3)",
    showgrid=True,
    tickfont=dict(color="#6B7E91", size=12),
    title_font=dict(color="#1C2B3A", size=13, weight="bold"),
)
_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#1C2B3A", family="Inter, sans-serif", size=12),
    legend=dict(
        bgcolor="rgba(240,237,229,0.9)",
        bordercolor="#6B7E91",
        borderwidth=1,
        font=dict(size=12, color="#1C2B3A"),
    ),
    hoverlabel=dict(bgcolor="#1C2B3A", bordercolor="#F5C200", font_color="#FFFFFF", font_size=13),
    margin=dict(l=10, r=10, t=36, b=10),
    xaxis=_AX, yaxis=_AX,
)

def _layout(fig, height=None, extra=None):
    kw = dict(**_BASE)
    if height: kw["height"] = height
    if extra:  kw.update(extra)
    fig.update_layout(**kw)
    return fig

# ── Utilities ─────────────────────────────────────────────────────────────────
def _safe(row, col, default=0.0):
    if row is None: return default
    try:
        v = row[col] if col in row.index else default
        return float(v) if pd.notna(v) else default
    except Exception: return default

def _safe_multi(row, *cols, default=0.0):
    for col in cols:
        v = _safe(row, col, default=None)
        if v is not None and v != 0.0: return float(v)
    return default

def _smart_date(col):
    s = col.astype(str).str.strip()
    parsed = pd.to_datetime(s, errors="coerce", dayfirst=False)
    failed = parsed.isna() & ~s.isin(["nan", "NaT", "", "None"])
    if failed.any():
        def _try(x):
            try: return pd.Timestamp(dtparser.parse(x, dayfirst=False))
            except: return pd.NaT
        parsed[failed] = s[failed].apply(_try)
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

# ── Data Loading ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Dashboard_Card", header=False)
        raw.columns = [str(c).strip() for c in raw.iloc[1]]
        raw = raw.iloc[2:].reset_index(drop=True)
        raw = raw[~raw["Date"].astype(str).str.contains(r"Grand Total|^Date$|^nan$|Backlog Threshold|ISD Backlog|OSD Backlog", case=False, na=True, regex=True)]
        raw["Date"] = _smart_date(raw["Date"])
        raw = raw.dropna(subset=["Date"])
        raw = _nums(raw, [c for c in raw.columns if c != "Date"])
        raw["Date_Label"] = raw["Date"].dt.strftime("%d %b")
        dc = raw
    except Exception as e:
        st.warning(f"Dashboard_Card: {e}"); dc = pd.DataFrame()
        
    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="FID_Tracking")
        raw.columns = [str(c).strip() for c in raw.columns]
        raw = raw[~raw.iloc[:,0].astype(str).str.contains(r"Grand Total|Report Date|^nan$", case=False, na=True, regex=True)]
        raw.rename(columns={raw.columns[0]: "Date"}, inplace=True)
        raw["Date"] = _smart_date(raw["Date"])
        raw = raw.dropna(subset=["Date"])
        raw = _nums(raw, list(raw.columns[1:]))
        raw["Date_Label"] = raw["Date"].dt.strftime("%d %b")
        ft = raw
    except Exception as e:
        st.warning(f"FID_Tracking: {e}"); ft = pd.DataFrame()
        
    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="FID_RID_Backlog_Details")
        raw.columns = [str(c).strip() for c in raw.columns]
        raw = raw[~raw.iloc[:,0].astype(str).str.contains(r"Grand Total|^Date$|^nan$", case=False, na=True, regex=True)]
        raw.rename(columns={raw.columns[0]: "Date"}, inplace=True)
        raw["Date"] = _smart_date(raw["Date"])
        raw = raw.dropna(subset=["Date"])
        raw = _nums(raw, list(raw.columns[1:]))
        raw["Date_Label"] = raw["Date"].dt.strftime("%d %b")
        fr = raw
    except Exception as e:
        st.warning(f"FID_RID_Backlog_Details: {e}"); fr = pd.DataFrame()
        
    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Aging_Distribution")
        raw = raw.iloc[:, :14]
        raw.columns = ["Date","Region"] + [str(i) for i in range(1,11)] + ["10+","Total"]
        raw = raw[~raw["Date"].astype(str).str.contains(r"Grand Total|Report Date|^nan$", case=False, na=True, regex=True)]
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

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dash-header">
  <div class="dash-bee">🐝</div>
  <div>
    <div class="dash-title">Carrybee Delivery Intelligence</div>
    <div class="dash-subtitle">Live Backlog &amp; Operations Dashboard — Auto-refreshes every 10 minutes</div>
  </div>
  <div class="dash-live">
    <div class="live-dot"></div>
    Live
  </div>
</div>
""", unsafe_allow_html=True)

# ── DATE SLICER ───────────────────────────────────────────────────────────────
all_dates_ft = sorted(ft["Date"].dropna().unique()) if not ft.empty else []
all_dates_ag = sorted(ag["Date"].dropna().unique()) if not ag.empty else []
all_dates    = sorted(set(list(all_dates_ft) + list(all_dates_ag)))

if all_dates:
    date_opts = [pd.Timestamp(d).strftime("%d %b %Y") for d in all_dates]
    slicer_col, _ = st.columns([3, 5])
    with slicer_col:
        st.markdown("""
        <div style="
            display:flex; align-items:center; gap:14px;
            background: #F0EDE5; border:1px solid #E2E8F0;
            border-radius:12px; padding:12px 20px 10px;
            box-shadow:0 4px 12px rgba(0,0,0,0.1); margin-bottom:4px;">
          <div style="font-size:12px;font-weight:700;text-transform:uppercase;
                      color:#1C2B3A;white-space:nowrap;">
            📅 Report Date
          </div>
        </div>
        """, unsafe_allow_html=True)
        sel_di = st.selectbox(
            "report_date_hidden", range(len(date_opts)),
            format_func=lambda i: date_opts[i], index=len(date_opts) - 1,
            label_visibility="collapsed",
        )
    sel_date  = pd.Timestamp(all_dates[sel_di])
    sel_start = sel_date
    sel_end   = sel_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    
    recent = all_dates[-min(6, len(all_dates)):]
    chips_html = "".join(
        f'<span class="date-chip{" active" if all_dates[sel_di]==d else ""}">'
        f'{pd.Timestamp(d).strftime("%d %b")}</span>'
        for d in recent
    )
    st.markdown(
        f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px;padding-left:4px;">'
        f'<span style="font-size:12px;font-weight:600;text-transform:uppercase;color:#6B7E91;align-self:center;">Recent:</span>'
        f'{chips_html}</div>',
        unsafe_allow_html=True,
    )
else:
    sel_date  = pd.Timestamp.now().normalize()
    sel_start = sel_date
    sel_end   = sel_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    st.error("No dates found.")

region_filter = ["ISD", "OSD"]

# ── Latest row helpers ────────────────────────────────────────────────────────
def _latest(df):
    if df is None or df.empty: return None
    sub = df[df["Date"] <= sel_end].sort_values("Date")
    return sub.iloc[-1] if not sub.empty else None
def _prev(df):
    if df is None or df.empty: return None
    sub = df[df["Date"] <= sel_end].sort_values("Date")
    return sub.iloc[-2] if len(sub) >= 2 else None

lt_dc = _latest(dc)
lt_fr = _latest(fr)
pr_dc = _prev(dc)
pr_fr = _prev(fr)

# ── KPI calculations ──────────────────────────────────────────────────────────
ag_le = ag[ag["Date"] <= sel_end] if not ag.empty else pd.DataFrame()
if not ag_le.empty:
    ag_last_date = ag_le["Date"].max()
    ag_day       = ag_le[ag_le["Date"] == ag_last_date]
    isd_total    = ag_day[ag_day["Region"] == "ISD"]["Total"].sum()
    osd_total    = ag_day[ag_day["Region"] == "OSD"]["Total"].sum()
    tot_fid      = isd_total + osd_total
    prev_ag_d    = ag_le[ag_le["Date"] < ag_last_date]["Date"]
    if not prev_ag_d.empty:
        pr_ag = ag_le[ag_le["Date"] == prev_ag_d.max()]
        pr_fid = (pr_ag[pr_ag["Region"]=="ISD"]["Total"].sum() + pr_ag[pr_ag["Region"]=="OSD"]["Total"].sum())
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
zt_pct     = (zt_val / dc_total * 100) if (zt_val > 0 and dc_total > 0) else 0.0
pr_zt_pct  = (pr_zt_val / pr_dc_tot * 100) if (pr_zt_val > 0 and pr_dc_tot > 0) else 0.0

# ── 7-day sparkline series ────────────────────────────────────────────────────
def _s7_ag():
    if ag_le.empty: return []
    dates = sorted(ag_le["Date"].unique())[-7:]
    return [float(ag_le[ag_le["Date"]==d]["Total"].sum()) for d in dates]

def _s7_bl():
    if fr.empty: return []
    sub = fr[fr["Date"] <= sel_end].sort_values("Date").tail(7)
    if "FID Backlog" not in sub.columns: return []
    rid = sub["RID Backlog"] if "RID Backlog" in sub.columns else 0
    return (sub["FID Backlog"] + rid).tolist()

def _s7_zt():
    if dc.empty: return []
    sub = dc[dc["Date"] <= sel_end].sort_values("Date").tail(7)
    return sub["Zone Transfer"].tolist() if "Zone Transfer" in sub.columns else []

spark_fid = _s7_ag()
spark_bl  = _s7_bl()
spark_zt  = _s7_zt()

def _spark_svg(values, color, w=120, h=48):
    if not values or len(values) < 2: return ""
    mn, mx = min(values), max(values)
    rng = mx - mn if mx != mn else 1
    pad = 5; pts = []
    for i, v in enumerate(values):
        x = pad + (i / (len(values)-1)) * (w - 2*pad)
        y = pad + (1 - (v - mn)/rng) * (h - 2*pad)
        pts.append((x, y))
        
    def _path(pts):
        d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for i in range(1, len(pts)):
            x0,y0 = pts[i-1]; x1,y1 = pts[i]
            cx = (x0+x1)/2
            d += f" C{cx:.1f},{y0:.1f} {cx:.1f},{y1:.1f} {x1:.1f},{y1:.1f}"
        return d
    
    path = _path(pts)
    area_path = path + f" L{pts[-1][0]:.1f},{h} L{pts[0][0]:.1f},{h} Z"
    uid = color.replace("#","")
    lx, ly = pts[-1]
    return f"""<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="sg{uid}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{color}" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="{color}" stop-opacity="0.0"/>
    </linearGradient>
  </defs>
  <path d="{area_path}" fill="url(#sg{uid})"/>
  <path d="{path}" fill="none" stroke="{color}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>
  <circle cx="{lx:.1f}" cy="{ly:.1f}" r="4" fill="{color}"/>
</svg>"""

def _trend(vals, lib=True):
    if not vals or len(vals) < 2: return "#6B7E91"
    return "#2E7D6B" if (vals[-1] < vals[-2]) == lib else "#E05C3A"

fc = _trend(spark_fid, True)
bc = _trend(spark_bl,  True)
zc = _trend(spark_zt, False)

d_fid = tot_fid - pr_fid
d_bl  = overall_bl - pr_overall
d_zt  = zt_val - pr_zt_val

def _delta_html(val, lower_is_better=True):
    if val == 0: return '<span class="kpi-delta dn">— unchanged</span>'
    good  = (val < 0 and lower_is_better) or (val > 0 and not lower_is_better)
    cls   = "dg" if good else "dr"
    arrow = "↓" if val < 0 else "↑"
    return f'<span class="kpi-delta {cls}">{arrow} {abs(val):,.0f}</span>'

# ── ROW 1: THREE LARGE KPI CARDS ──────────────────────────────────────────────
r1c1, r1c2, r1c3 = st.columns(3)

def _big_kpi(col, num, label, val_str, spark_svg_html, d_html):
    col.markdown(f"""
    <div class="kpi-card">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0;">
        <div>
          <div class="kpi-num">{num}</div>
          <div class="kpi-lbl">{label}</div>
        </div>
        <div style="margin-top:4px;">{spark_svg_html}</div>
      </div>
      <div class="kpi-val">{val_str}</div>
      {d_html}
      <div style="font-size:11px;color:#6B7E91;margin-top:8px;font-weight:500;">7-day trend ↑</div>
    </div>""", unsafe_allow_html=True)

with r1c1:
    _big_kpi(r1c1, "01", "Total In-Process (FID)", f"{tot_fid:,.0f}", _spark_svg(spark_fid, fc), _delta_html(d_fid, True))
with r1c2:
    _big_kpi(r1c2, "02", "Overall Backlog (FID+RID)", f"{overall_bl:,.0f}", _spark_svg(spark_bl, bc), _delta_html(d_bl, True))
with r1c3:
    zt_disp = f"{int(zt_val):,}" if zt_val > 0 else "—"
    _big_kpi(r1c3, "03", "Zone Transfer Parcels", zt_disp, _spark_svg(spark_zt, zc), _delta_html(d_zt, False))

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# ── ROW 2: FID % | Zone % | Backlog Donut ─────────────────────────────────────
r2c1, r2c2, r2c3 = st.columns([1, 1, 1])

def _pct_kpi(col, num, label, val, prev, lib=True):
    diff   = val - prev
    good   = (diff < 0 and lib) or (diff > 0 and not lib)
    vcol   = "#2E7D6B" if good else ("#E05C3A" if diff != 0 else "#1C2B3A")
    arrow  = "↓" if diff < 0 else ("↑" if diff > 0 else "—")
    dcls   = "dg" if good else ("dr" if diff != 0 else "dn")
    col.markdown(f"""
    <div class="kpi-sm">
      <div style="font-size:12px;font-weight:700;color:#6B7E91;margin-bottom:4px;">{num}</div>
      <div style="font-size:13px;font-weight:600;text-transform:uppercase;color:#1C2B3A;margin-bottom:12px;">{label}</div>
      <div class="kpi-sm-val" style="color:{vcol}!important;">{val:.2f}%</div>
      <span class="kpi-delta {dcls}">{arrow} {abs(diff):.2f} pp vs prev</span>
    </div>""", unsafe_allow_html=True)

with r2c1: _pct_kpi(r2c1, "04", "FID Backlog %", fid_pct, pr_fid_pct, True)
with r2c2: _pct_kpi(r2c2, "05", "Zone Change %", zt_pct,  pr_zt_pct,  True)

with r2c3:
    st.markdown('<div class="kpi-sm" style="padding:16px 20px 10px;">', unsafe_allow_html=True)
    st.markdown("""<div style="font-size:12px;font-weight:700;color:#6B7E91;margin-bottom:2px;">06</div>
                  <div style="font-size:13px;font-weight:600;text-transform:uppercase;color:#1C2B3A;margin-bottom:6px;">
                  Backlog — FID vs RID</div>""", unsafe_allow_html=True)
    if (fid_bl + rid_bl) > 0:
        fig_dn = go.Figure(data=[go.Pie(
            labels=["FID","RID"], values=[fid_bl, rid_bl],
            hole=0.60, marker_colors=[C_ISD, C_OSD],
            textinfo="label+percent", textfont=dict(size=12, color="#FFFFFF", weight="bold"), pull=[0.03, 0],
        )])
        fig_dn.add_annotation(
            text=f"<span style='font-size:18px; font-weight:800; color:#1C2B3A;'>{fid_bl+rid_bl:,.0f}</span><br><span style='font-size:11px; color:#6B7E91;'>Total</span>",
            x=0.5, y=0.5, showarrow=False, xanchor="center",
        )
        _layout(fig_dn, height=145, extra={"margin": dict(l=0,r=0,t=0,b=0), "legend": dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5)})
        st.plotly_chart(fig_dn, use_container_width=True)
    else:
        st.markdown('<p style="color:#6B7E91;font-size:13px;">No data</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# ── ROW 3: Backlog Details | Sort ─────────────────────────────────────────────
r3c1, r3c2 = st.columns([3, 2])
with r3c1:
    st.markdown('<div class="cc">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">07 · Backlog Details — FID &amp; RID (LMH / FMH)</div>', unsafe_allow_html=True)
    if lt_fr is not None:
        detail = [
            ("FID LMH", _safe(lt_fr,"FID LMH ISD"), _safe(lt_fr,"FID LMH SUB"), _safe(lt_fr,"FID LMH OSD"), _safe(lt_fr,"FID LMH Total")),
            ("FID FMH", _safe(lt_fr,"FID FMH"), 0, 0, _safe(lt_fr,"FID FMH")),
            ("RID FMH", _safe(lt_fr,"RID FMH ISD"), _safe(lt_fr,"RID FMH SUB"), _safe(lt_fr,"RID FMH OSD"), _safe(lt_fr,"RID FMH ISD")+_safe(lt_fr,"RID FMH SUB")+_safe(lt_fr,"RID FMH OSD")),
            ("RID LMH", _safe(lt_fr,"RID LMH ISD"), _safe(lt_fr,"RID LMH SUB"), _safe(lt_fr,"RID LMH OSD"), _safe(lt_fr,"RID LMH ISD")+_safe(lt_fr,"RID LMH SUB")+_safe(lt_fr,"RID LMH OSD")),
        ]
        labs, iv, sv, ov, tots = zip(*detail)
        fig7 = go.Figure()
        for vals, name, color in [(iv,"ISD",C_ISD),(sv,"SUB",C_SUB),(ov,"OSD",C_OSD)]:
            fig7.add_trace(go.Bar(
                name=name, y=labs, x=vals, orientation="h", marker_color=color,
                text=[f"{v:,.0f}" if v>0 else "" for v in vals],
                textposition="inside", insidetextanchor="middle", textfont=dict(color="#FFFFFF", size=12, weight="bold"),
            ))
        for lbl, tot in zip(labs, tots):
            if tot > 0: fig7.add_annotation(x=tot, y=lbl, text=f"  <b>{tot:,.0f}</b>", showarrow=False, xanchor="left", font=dict(size=13, color="#1C2B3A"))
        _layout(fig7, height=280, extra={"barmode":"stack", "xaxis": dict(**_AX, title="Count"), "yaxis": dict(**_AX, autorange="reversed")})
        st.plotly_chart(fig7, use_container_width=True)
    else: st.info("No backlog detail data.")
    st.markdown('</div>', unsafe_allow_html=True)

with r3c2:
    st.markdown('<div class="cc">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">08 · Sort — FID Sort vs RID Sort</div>', unsafe_allow_html=True)
    if lt_fr is not None:
        fid_sort = _safe(lt_fr, "FID Sort")
        rid_sort = _safe_multi(lt_fr, "RID Sort", "RID LMH Sort")
        fig8 = go.Figure(data=[go.Bar(
            y=["FID Sort", "RID Sort"], x=[fid_sort, rid_sort], orientation="h",
            marker_color=[C_ISD, C_OSD], marker_line=dict(color="#F0EDE5", width=1),
            text=[f"{fid_sort:,.0f}", f"{rid_sort:,.0f}"], textposition="outside", textfont=dict(size=14, color="#1C2B3A", weight="bold"), width=0.45,
        )])
        _layout(fig8, height=280, extra={"showlegend": False, "xaxis": dict(**_AX, title="Parcels Sorted"), "yaxis": dict(**_AX), "margin": dict(l=8, r=80, t=30, b=8)})
        st.plotly_chart(fig8, use_container_width=True)
    else: st.info("No sort data.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)

# ── ROW 4: Date-range Tracking | Region Vertical Bar ──────────────────────────
r4c1, r4c2 = st.columns([3, 2])
with r4c1:
    st.markdown('<div class="cc">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">09 · Date-wise Backlog Progress Tracking (FID)</div>', unsafe_allow_html=True)
    if all_dates:
        t_opts = [pd.Timestamp(d).strftime("%d %b %Y") for d in all_dates]
        tc1, tc2 = st.columns(2)
        with tc1: t_si = st.selectbox("From", range(len(t_opts)), format_func=lambda i: t_opts[i], index=0, key="tr_from")
        with tc2: t_ei = st.selectbox("To", range(len(t_opts)), format_func=lambda i: t_opts[i], index=len(t_opts)-1, key="tr_to")
        if t_ei < t_si: t_ei = t_si
        t_start = pd.Timestamp(all_dates[t_si])
        t_end   = pd.Timestamp(all_dates[t_ei]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        ft_r    = ft[(ft["Date"]>=t_start)&(ft["Date"]<=t_end)].sort_values("Date") if not ft.empty else pd.DataFrame()
    else:
        ft_r = pd.DataFrame(); t_start = sel_start; t_end = sel_end
        
    if not ft_r.empty:
        fig9 = go.Figure()
        if "Total In Progress (Backlog)" in ft_r.columns:
            fig9.add_trace(go.Bar(x=ft_r["Date_Label"], y=ft_r["Total In Progress (Backlog)"], name="Total In Process (FID)", marker_color=C_ISD, opacity=0.90))
        if "Worked On" in ft_r.columns:
            fig9.add_trace(go.Bar(x=ft_r["Date_Label"], y=ft_r["Worked On"], name="Worked On", marker_color=C_SUB, opacity=0.90))
        _layout(fig9, height=300, extra={"barmode": "group"})
        st.plotly_chart(fig9, use_container_width=True)
    else: st.info("No FID tracking data for selected range.")
    st.markdown('</div>', unsafe_allow_html=True)

with r4c2:
    st.markdown('<div class="cc">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">10 · Region Wise In-Process Parcels</div>', unsafe_allow_html=True)
    if tot_fid > 0:
        df_reg = pd.DataFrame({"Region":["ISD","OSD"], "Parcels":[isd_total, osd_total]})
        fig10  = px.bar(df_reg, x="Region", y="Parcels", color="Region", color_discrete_map={"ISD":C_ISD,"OSD":C_OSD}, text="Parcels")
        fig10.update_traces(texttemplate="%{text:,.0f}", textposition="outside", textfont=dict(color="#1C2B3A", size=14, weight="bold"), width=0.45)
        _layout(fig10, height=250, extra={"showlegend": False, "yaxis": dict(**_AX, title="Parcels"), "xaxis": dict(**_AX, title="")})
        st.plotly_chart(fig10, use_container_width=True)
        
        st.markdown(f"""
        <div style="display:flex;gap:0;border-top:1px solid #D9D9D9; padding-top:16px;margin-top:8px;">
          <div style="flex:1;text-align:center;border-right:1px solid #D9D9D9;">
            <div style="font-size:12px;color:#6B7E91;text-transform:uppercase;font-weight:600;margin-bottom:4px;">ISD</div>
            <div style="font-size:22px;font-weight:800;color:{C_ISD};">{isd_total:,.0f}</div>
          </div>
          <div style="flex:1;text-align:center;border-right:1px solid #D9D9D9;">
            <div style="font-size:12px;color:#6B7E91;text-transform:uppercase;font-weight:600;margin-bottom:4px;">OSD</div>
            <div style="font-size:22px;font-weight:800;color:{C_OSD};">{osd_total:,.0f}</div>
          </div>
          <div style="flex:1;text-align:center;">
            <div style="font-size:12px;color:#6B7E91;text-transform:uppercase;font-weight:600;margin-bottom:4px;">Total</div>
            <div style="font-size:22px;font-weight:800;color:{C_AMB};">{tot_fid:,.0f}</div>
          </div>
        </div>""", unsafe_allow_html=True)
    else: st.info("No region data.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)

# ── ROW 5: Aging Distribution | Aging Table ───────────────────────────────────
AGE_COLS = [str(i) for i in range(1, 11)] + ["10+"]
ag_f = ag[(ag["Date"]>=sel_start)&(ag["Date"]<=sel_end)].copy() if not ag.empty else pd.DataFrame()
if not ag_f.empty and "Region" in ag_f.columns: ag_f = ag_f[ag_f["Region"].isin(region_filter)]

r5c1, r5c2 = st.columns([3, 2])
with r5c1:
    st.markdown('<div class="cc">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">11 · Aging Distribution</div>', unsafe_allow_html=True)
    st.markdown('<div class="aging-badge">ISD &amp; SUB = 4 Days+ &nbsp;|&nbsp; OSD = 5 Days+</div>', unsafe_allow_html=True)
    if not ag_f.empty:
        ag_max = ag_f["Date"].max()
        ag_day_f = ag_f[ag_f["Date"]==ag_max].copy()
        rows8 = []
        for _, row in ag_day_f.iterrows():
            region = str(row.get("Region","")).strip()
            if region not in region_filter: continue
            total = float(row.get("Total",0) or 0)
            if total == 0: total = sum(float(row[c]) for c in AGE_COLS if c in ag_day_f.columns and pd.notna(row[c]))
            for c in AGE_COLS:
                if c in ag_day_f.columns:
                    val = float(row[c]) if pd.notna(row[c]) else 0.0
                    pct = val/total*100 if total > 0 else 0.0
                    rows8.append({"Region":region,"Age":f"{c}d","Count":val,"Pct":pct})
        ag_melt = pd.DataFrame(rows8)
        if not ag_melt.empty:
            fig11 = px.bar(ag_melt, x="Age", y="Pct", color="Region", color_discrete_map={"ISD":C_ISD,"OSD":C_OSD}, barmode="group", text=ag_melt["Pct"].apply(lambda x: f"{x:.1f}%"))
            fig11.update_traces(textposition="outside", textfont=dict(color="#1C2B3A", size=10), customdata=ag_melt[["Count","Region"]], hovertemplate="<b>%{x}</b><br>Region: %{customdata[1]}<br>Count: %{customdata[0]:,.0f}<br>Pct: %{y:.1f}%")
            _layout(fig11, height=300, extra={"yaxis": dict(**_AX, title="Percentage (%)")})
            st.plotly_chart(fig11, use_container_width=True)
        else: st.info("No aging data.")
    else: st.info("No aging distribution data available.")
    st.markdown('</div>', unsafe_allow_html=True)

with r5c2:
    st.markdown('<div class="cc">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">12 · Aging Count &amp; % by Region</div>', unsafe_allow_html=True)
    if not ag_f.empty:
        ag_tbl_day = ag_f[ag_f["Date"]==ag_f["Date"].max()].copy()
        isd_r = ag_tbl_day[ag_tbl_day["Region"]=="ISD"].iloc[0] if "ISD" in ag_tbl_day["Region"].values else None
        osd_r = ag_tbl_day[ag_tbl_day["Region"]=="OSD"].iloc[0] if "OSD" in ag_tbl_day["Region"].values else None
        isd_t = float(isd_r["Total"]) if isd_r is not None else 0
        osd_t = float(osd_r["Total"]) if osd_r is not None else 0
        
        th = "<th>Days</th>"
        if isd_r is not None: th += "<th>ISD</th><th>ISD %</th>"
        if osd_r is not None: th += "<th>OSD</th><th>OSD %</th>"
        body = ""
        for c in AGE_COLS:
            if c not in ag_tbl_day.columns: continue
            td = f"<td><b>{c}d</b></td>"
            if isd_r is not None:
                v = float(isd_r[c]) if pd.notna(isd_r[c]) else 0
                td += (f"<td>{v:,.0f}</td><td>{v/isd_t*100:.1f}%</td>" if isd_t else "<td>—</td><td>—</td>")
            if osd_r is not None:
                v = float(osd_r[c]) if pd.notna(osd_r[c]) else 0
                td += (f"<td>{v:,.0f}</td><td>{v/osd_t*100:.1f}%</td>" if osd_t else "<td>—</td><td>—</td>")
            body += f"<tr>{td}</tr>"
        td_tot = "<td><b>Total</b></td>"
        if isd_r is not None: td_tot += f"<td><b>{isd_t:,.0f}</b></td><td><b>100%</b></td>"
        if osd_r is not None: td_tot += f"<td><b>{osd_t:,.0f}</b></td><td><b>100%</b></td>"
        body += f"<tr>{td_tot}</tr>"
        
        st.markdown(f"""
        <div style="overflow-x:auto;max-height:340px;overflow-y:auto; border-radius:8px; border:1px solid #E2E8F0;">
        <table class="styled-table" style="margin:0;">
          <thead><tr>{th}</tr></thead>
          <tbody>{body}</tbody>
        </table></div>""", unsafe_allow_html=True)
    else: st.info("No aging data.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)

# ── ROW 6: Full FID Tracking Table ────────────────────────────────────────────
st.markdown('<div class="cc">', unsafe_allow_html=True)
st.markdown('<div class="sec-hdr">13 · Date-wise Backlog Progress Tracking — Full Table (FID)</div>', unsafe_allow_html=True)
try: ft_tbl = ft[(ft["Date"]>=t_start)&(ft["Date"]<=t_end)].sort_values("Date").copy() if not ft.empty else pd.DataFrame()
except Exception: ft_tbl = ft.sort_values("Date").copy() if not ft.empty else pd.DataFrame()

if not ft_tbl.empty:
    COL_MAP = {"Date_Label":"Date", "Newly Added":"Newly Added", "Total In Progress (Backlog)":"Total In Process (Backlog)", "Worked On":"Worked On", "Carry Forward":"Carry Forward"}
    sc = [c for c in COL_MAP if c in ft_tbl.columns]
    df_tbl = ft_tbl[sc].rename(columns=COL_MAP)
    headers = "".join(f"<th>{c}</th>" for c in df_tbl.columns)
    body = ""
    for i, (_, r) in enumerate(df_tbl.iterrows()):
        is_last = i == len(df_tbl)-1
        cells = ""
        for j, v in enumerate(r):
            cls = "col-date" if j==0 else ("col-high" if is_last else "")
            try: disp = v if j==0 else (f"{int(float(v)):,}" if float(v)!=0 else "—")
            except: disp = "—"
            cells += f"<td class='{cls}'>{disp}</td>"
        body += f"<tr>{cells}</tr>"
    st.markdown(f"""
    <div style="overflow-x:auto; border-radius:8px; border:1px solid #E2E8F0;">
    <table class="styled-table" style="margin:0;">
      <thead><tr>{headers}</tr></thead>
      <tbody>{body}</tbody>
    </table></div>""", unsafe_allow_html=True)
else: st.info("No FID tracking data to display.")
st.markdown('</div>', unsafe_allow_html=True)

# ── APPENDIX ──────────────────────────────────────────────────────────────────
with st.expander("📖  Appendix — Definitions & Calculation Methods", expanded=False):
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="app-title">📊 KPI Definitions &amp; Calculation Methods</div>', unsafe_allow_html=True)
    items = [
        ("01 · Total In-Process (FID)", "All parcels in the First Inbound Delivery cycle on the selected date. Green = count is lower than the previous day.", "Aging_Distribution → ISD Total + OSD Total"),
        ("02 · Overall Backlog (FID+RID)", "Total undelivered backlog. Green = total is falling day-on-day.", "FID Backlog + RID Backlog (source: FID_RID_Backlog_Details)"),
        ("03 · Zone Transfer Parcels", "Parcels transferred between delivery zones. Sparkline shows 7-day trend.", "Dashboard_Card → 'Zone Transfer' column"),
        ("04 · FID Backlog %", "Share of total in-process FID parcels that are in backlog.", "FID Backlog ÷ Total In-Process × 100"),
        ("05 · Zone Change %", "Share of all parcels that underwent a zone transfer.", "Zone Transfer ÷ Total (Dashboard_Card) × 100"),
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

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;color:#6B7E91;font-size:12px;padding:22px 0 12px;font-weight:600;">
  🐝 Carrybee Delivery Intelligence &nbsp;·&nbsp;
  Report Date: <span style="color:#F5C200;">{sel_date.strftime('%d %b %Y')}</span>
  &nbsp;·&nbsp; Cache TTL: 10 min &nbsp;·&nbsp; Powered by Google Sheets
</div>
""", unsafe_allow_html=True)
