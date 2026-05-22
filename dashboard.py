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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

* { font-family: 'DM Sans', sans-serif; box-sizing: border-box; }

/* ── App Background ── */
[data-testid="stAppViewContainer"] { background: #F4F7F9; }
[data-testid="stHeader"]           { background: transparent; }
[data-testid="stToolbar"]          { display: none; }
[data-testid="stDecoration"]       { display: none; }
.block-container { padding-top:1.2rem !important; padding-bottom:2rem !important; max-width:98% !important; }

/* ── Premium Header ── */
.dash-header {
    background: #1C2B3A;
    border-left: 6px solid #F5C200;
    border-radius: 12px; padding: 24px 32px; margin-bottom: 20px;
    display: flex; align-items: center; gap: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.dash-title    { color:#FFFFFF !important; font-size:26px; font-weight:700; margin:0; letter-spacing:-0.5px; }
.dash-subtitle { color:#F5C200 !important; font-size:13px; margin-top:4px; font-weight:500; }
.dash-bee      { font-size:40px; line-height:1; filter: drop-shadow(0 2px 4px rgba(245,194,0,0.3)); }

/* ── Filter Bar ── */
.filter-bar {
    background: #FFFFFF; border-radius: 12px; padding: 14px 20px;
    border: 1px solid #E2E8F0; margin-bottom: 18px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

/* ── Streamlit Native Container Styling (Replaces .chart-card) ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;
    border-radius: 12px !important;
    border: 1px solid #E2E8F0 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    padding: 18px 20px 12px !important;
    height: 100%; /* Makes columns stretch equally */
}

/* ── Section Headers ── */
.sec-hdr {
    font-size:14px; font-weight:700; color:#1C2B3A !important;
    text-transform:uppercase; letter-spacing:0.8px;
    border-left:4px solid #F5C200;
    padding-left:10px; margin-bottom:14px;
    border-bottom: 1px solid #F1F5F9; padding-bottom: 8px;
}

/* ── HTML KPI Sparkline Cards ── */
.kpi-spark {
    background: #FFFFFF;
    border-radius: 12px; padding: 18px 20px 14px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    position: relative; overflow: hidden; min-height: 140px; height: 100%;
}
.kpi-spark-label {
    font-size: 12px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.8px; color: #6B7E91 !important; margin-bottom: 6px;
}
.kpi-spark-value {
    font-size: 34px; font-weight: 700; line-height: 1;
    font-family: 'DM Mono', monospace; margin-bottom: 6px; letter-spacing: -1px;
}

/* ── Delta Badges ── */
.kpi-delta-row {
    font-size: 12px; font-weight: 700; display: flex; align-items: center; gap: 6px;
}
.delta-good { color: #2E7D6B !important; background: rgba(46,125,107,0.12); padding: 3px 8px; border-radius: 12px; }
.delta-bad  { color: #E05C3A !important; background: rgba(224,92,58,0.12); padding: 3px 8px; border-radius: 12px; }
.delta-neu  { color: #6B7E91 !important; background: #F1F5F9; padding: 3px 8px; border-radius: 12px; }

/* ── Small KPIs ── */
.kpi-small {
    background: #FFFFFF;
    border-radius: 12px; padding: 18px 20px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    min-height: 110px;
}

/* ── Badges ── */
.aging-badge {
    background:#FDF3BF; border:1px solid #F5C200; border-radius:6px;
    padding:5px 12px; font-size:12px; color:#8A6A00 !important; font-weight:700;
    display:inline-block; margin-bottom:12px;
}

/* ── Tables ── */
.styled-table { width:100%; border-collapse:collapse; font-size:13px; }
.styled-table thead tr { background: #1C2B3A; }
.styled-table th { padding:10px 12px; text-align:center;
                   font-weight:600; font-size:12px; color:#FFFFFF !important;
                   text-transform:uppercase; letter-spacing:0.5px; }
.styled-table tbody tr { background: #FFFFFF; }
.styled-table tbody tr:nth-child(even) { background: #F8FAFC; }
.styled-table tbody tr:hover { background: #FDF3BF; }
.styled-table tbody tr:last-child { background:#FDF3BF; font-weight:700; border-top: 2px solid #F5C200; }
.styled-table td { padding:9px 12px; text-align:center;
                   border-bottom:1px solid #E2E8F0; color:#1C2B3A !important; }
.styled-table .col-date { text-align:left; font-weight:600; color:#2E7D6B !important; }
.styled-table .col-high { color:#E05C3A !important; font-weight:700; }

/* ── Appendix ── */
.appendix-card {
    background: #FFFFFF; border-radius:12px; padding:22px 26px;
    border:1px solid #E2E8F0; margin-bottom:8px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.appendix-title { font-size:15px; font-weight:700; color:#1C2B3A !important; margin-bottom:14px; border-bottom: 2px solid #F5C200; padding-bottom: 6px; }
.appendix-row { display:flex; gap:8px; margin-bottom:12px; align-items:flex-start; }
.appendix-key { font-size:13px; font-weight:700; color:#1C2B3A !important; min-width:220px; }
.appendix-val { font-size:13px; color:#6B7E91 !important; line-height: 1.5; }
.appendix-formula { font-family:'DM Mono',monospace; font-size:11px; font-weight: 600;
                    background:#FDF3BF; border:1px solid #F5C200;
                    border-radius:5px; padding:2px 8px; color:#8A6A00 !important; display:inline-block; margin-top:4px; }

/* ── Streamlit Overrides ── */
label, .stSelectbox label, .stMultiSelect label, .stToggle label {
    color: #1C2B3A !important; font-size: 12px !important; font-weight: 700 !important; text-transform: uppercase;
}
[data-testid="stSelectbox"] > div > div {
    background: #FFFFFF !important; border: 1px solid #CBD5E1 !important; border-radius: 8px !important; color: #1C2B3A !important;
}
</style>
""", unsafe_allow_html=True)

SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1n9GW1UksZ-jhCQ-zmCqwx4EH20fa-Zm5wA5BiMmdZAE/edit?gid=713116247#gid=713116247"
)

# ── Industry Standard Palette ──
C_ISD  = "#1C2B3A" # Deep Navy
C_OSD  = "#E05C3A" # Burnt Coral
C_SUB  = "#2E7D6B" # Teal Green
C_AMB  = "#F5C200" # Golden Yellow
C_PUR  = "#6B7E91" # Slate Gray

_AX = dict(
    gridcolor="#F1F5F9", linecolor="#E2E8F0",
    tickcolor="#CBD5E1", showgrid=True,
    tickfont=dict(color="#6B7E91", size=12),
    title_font=dict(color="#1C2B3A", size=13, weight="bold"),
)
_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#1C2B3A", family="DM Sans, sans-serif", size=12),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#E2E8F0",
                borderwidth=1, font=dict(size=12, color="#1C2B3A")),
    hoverlabel=dict(bgcolor="#1C2B3A", bordercolor="#F5C200", font_color="#FFFFFF", font_size=13),
    margin=dict(l=8, r=8, t=32, b=8),
    xaxis=_AX, yaxis=_AX,
)

def _layout(fig, height=None, extra=None):
    kw = dict(**_BASE)
    if height: kw["height"] = height
    if extra:  kw.update(extra)
    fig.update_layout(**kw)
    return fig

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
        num_cols = [c for c in raw.columns if c != "Date"]
        raw = _nums(raw, num_cols)
        raw["Date_Label"] = raw["Date"].dt.strftime("%d %b")
        dc = raw
    except Exception as e:
        st.warning(f"Dashboard_Card error: {e}"); dc = pd.DataFrame()

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
    except Exception as e:
        st.warning(f"FID_Tracking error: {e}"); ft = pd.DataFrame()

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
    except Exception as e:
        st.warning(f"FID_RID_Backlog_Details error: {e}"); fr = pd.DataFrame()

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
    except Exception as e:
        st.warning(f"Aging_Distribution error: {e}"); ag = pd.DataFrame()

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
</div>
""", unsafe_allow_html=True)

# ── SINGLE DATE SLICER ────────────────────────────────────────────────────────
st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
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
    st.error("No dates found — check sheet format.")

with fc2:
    region_filter = st.multiselect("🗺️ Region", ["ISD", "OSD"], default=["ISD", "OSD"])
st.markdown('</div>', unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
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

# ── Computed KPIs ─────────────────────────────────────────────────────────────
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
        pr_fid    = (pr_ag_day[pr_ag_day["Region"] == "ISD"]["Total"].sum()
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

# ── Last-7-day sparkline data ─────────────────────────────────────────────────
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
        x = pad + (i / (len(values)-1)) * (width - 2*pad)
        y = pad + (1 - (v - mn)/rng) * (height - 2*pad)
        pts.append(f"{x:.1f},{y:.1f}")
    area = (f"M{pts[0]} " + " ".join(f"L{p}" for p in pts[1:])
            + f" L{width-pad},{height} L{pad},{height} Z")
    last_x, last_y = pts[-1].split(",")
    uid = color.replace("#","")
    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g{uid}" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{color}" stop-opacity="0.25"/>
    <stop offset="100%" stop-color="{color}" stop-opacity="0.0"/>
  </linearGradient></defs>
  <path d="{area}" fill="url(#g{uid})"/>
  <polyline points="{' '.join(pts)}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>
  <circle cx="{last_x}" cy="{last_y}" r="3.5" fill="{color}"/>
</svg>"""

def _trend_color(values, lower_is_better=True):
    if not values or len(values) < 2: return C_AMB
    improving = values[-1] < values[-2] if lower_is_better else values[-1] > values[-2]
    return "#2E7D6B" if improving else "#E05C3A"

fid_color = _trend_color(spark_fid, lower_is_better=True)
bl_color  = _trend_color(spark_bl,  lower_is_better=True)
zt_color  = _trend_color(spark_zt,  lower_is_better=False)

# ── ROW 1: 3 Sparkline KPIs + Donut ──────────────────────────────────────────
st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)
kc1, kc2, kc3, kc4 = st.columns([1, 1, 1, 1])

def _spark_kpi(col_w, number, label, value_str, val_color, spark_svg, delta_val, delta_label, lower_is_better=True):
    d_fid  = delta_val
    arr    = "▼" if d_fid < 0 else ("▲" if d_fid > 0 else "—")
    good   = (d_fid < 0 and lower_is_better) or (d_fid > 0 and not lower_is_better)
    d_cls  = "delta-good" if good else ("delta-bad" if d_fid != 0 else "delta-neu")
    col_w.markdown(f"""
    <div class="kpi-spark">
      <div class="kpi-spark-label">{number}. {label}</div>
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
        <div class="kpi-spark-value" style="color:{val_color};">{value_str}</div>
        <div style="margin-top:6px;">{spark_svg}</div>
      </div>
      <div class="kpi-delta-row">
        <span class="{d_cls}">{arr} {abs(d_fid):,.0f} {delta_label}</span>
      </div>
      <div style="font-size:11px; font-weight:600; color:#6B7E91; margin-top:8px;">↑ last 7 days</div>
    </div>""", unsafe_allow_html=True)

d_fid_v = tot_fid - pr_fid
d_bl_v  = overall_bl - pr_overall
d_zt_v  = zt_val - pr_zt_val

with kc1:
    _spark_kpi(kc1, 1, "Total In-Process (FID)", f"{tot_fid:,.0f}", "#1C2B3A", _sparkline_svg(spark_fid, fid_color), d_fid_v, "vs prev day", True)

with kc2:
    _spark_kpi(kc2, 2, "Overall Backlog", f"{overall_bl:,.0f}", "#1C2B3A", _sparkline_svg(spark_bl, bl_color), d_bl_v, "FID+RID vs prev", True)

with kc3:
    zt_display = f"{int(zt_val):,}" if zt_val > 0 else "0"
    _spark_kpi(kc3, 3, "Zone Transfer Parcels", zt_display, "#1C2B3A", _sparkline_svg(spark_zt, zt_color), d_zt_v, "vs prev day", False)

# FIX: Replaced raw HTML with st.container(border=True) to prevent DOM breakage
with kc4:
    with st.container(border=True):
        st.markdown('<div class="kpi-spark-label" style="margin-bottom:0px;">4. Backlog — FID vs RID</div>', unsafe_allow_html=True)
        if (fid_bl + rid_bl) > 0:
            fig_donut = go.Figure(data=[go.Pie(
                labels=["FID", "RID"], values=[fid_bl, rid_bl],
                hole=0.62, marker_colors=[C_ISD, C_OSD],
                textinfo="label+percent",
                textfont=dict(size=12, color="#FFFFFF", weight="bold"),
                pull=[0.03, 0],
            )])
            fig_donut.add_annotation(
                text=f"<b>{fid_bl+rid_bl:,.0f}</b><br><span style='font-size:11px; color:#6B7E91;'>Total</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=18, color="#1C2B3A"), xanchor="center",
            )
            _layout(fig_donut, height=140,
                    extra={"margin": dict(l=0,r=0,t=0,b=0),
                           "legend": dict(orientation="h", yanchor="bottom", y=-0.18,
                                          xanchor="center", x=0.5, font=dict(size=11, color="#1C2B3A"))})
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("No backlog data.")

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ── ROW 2: FID Backlog % + Zone Change % ─────────────────────────────────────
kr1, kr2, _sp1, _sp2 = st.columns([1, 1, 1, 1])

def _pct_kpi(col_w, number, label, value, prev_value, lower_is_better=True):
    diff    = value - prev_value
    good    = (diff < 0 and lower_is_better) or (diff > 0 and not lower_is_better)
    v_color = "#2E7D6B" if good else ("#E05C3A" if diff != 0 else "#1C2B3A")
    arr     = "▼" if diff < 0 else ("▲" if diff > 0 else "—")
    d_cls   = "delta-good" if good else ("delta-bad" if diff != 0 else "delta-neu")
    col_w.markdown(f"""
    <div class="kpi-small">
      <div class="kpi-spark-label">{number}. {label}</div>
      <div style="font-size:32px; font-weight:700; font-family:'DM Mono',monospace;
                  color:{v_color}; margin-bottom:12px; line-height:1; letter-spacing: -1px;">{value:.2f}%</div>
      <div class="kpi-delta-row">
        <span class="{d_cls}" style="font-size:13px; line-height:1;">{arr} {abs(diff):.2f} pp vs prev day</span>
      </div>
    </div>""", unsafe_allow_html=True)

with kr1:
    _pct_kpi(kr1, 5, "FID Backlog %", fid_pct, pr_fid_pct, lower_is_better=True)
with kr2:
    _pct_kpi(kr2, 6, "Zone Change %", zt_pct, pr_zt_pct, lower_is_better=True)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ── ROW 3: Backlog Details + FID/RID Sort (horizontal bars) ──────────────────
col_bl, col_sort = st.columns([3, 2])

# FIX: Wrapped in st.container(border=True)
with col_bl:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">7. Backlog Details — FID &amp; RID (LMH / FMH)</div>', unsafe_allow_html=True)
        if lt_fr is not None:
            detail_rows = [
                ("FID LMH", _safe(lt_fr,"FID LMH ISD"), _safe(lt_fr,"FID LMH SUB"), _safe(lt_fr,"FID LMH OSD"), _safe(lt_fr,"FID LMH Total")),
                ("FID FMH", _safe(lt_fr,"FID FMH"), 0, 0, _safe(lt_fr,"FID FMH")),
                ("RID FMH", _safe(lt_fr,"RID FMH ISD"), _safe(lt_fr,"RID FMH SUB"), _safe(lt_fr,"RID FMH OSD"), _safe(lt_fr,"RID FMH ISD")+_safe(lt_fr,"RID FMH SUB")+_safe(lt_fr,"RID FMH OSD")),
                ("RID LMH", _safe(lt_fr,"RID LMH ISD"), _safe(lt_fr,"RID LMH SUB"), _safe(lt_fr,"RID LMH OSD"), _safe(lt_fr,"RID LMH ISD")+_safe(lt_fr,"RID LMH SUB")+_safe(lt_fr,"RID LMH OSD")),
            ]
            labels, isd_v, sub_v, osd_v, tots = zip(*detail_rows)
            fig9 = go.Figure()
            for vals, name, color in [(isd_v,"ISD",C_ISD),(sub_v,"SUB",C_SUB),(osd_v,"OSD",C_OSD)]:
                fig9.add_trace(go.Bar(
                    name=name, y=labels, x=vals, orientation="h", marker_color=color,
                    text=[f"{v:,.0f}" if v>0 else "" for v in vals],
                    textposition="inside", insidetextanchor="middle",
                    textfont=dict(color="#FFFFFF", size=12, weight="bold"),
                ))
            for lbl, tot in zip(labels, tots):
                if tot > 0:
                    fig9.add_annotation(x=tot, y=lbl, text=f"  <b>{tot:,.0f}</b>",
                                        showarrow=False, xanchor="left",
                                        font=dict(size=13, color="#1C2B3A"))
            _layout(fig9, height=280, extra={"barmode":"stack", "xaxis": dict(**_AX, title="Count"), "yaxis": dict(**_AX, autorange="reversed")})
            st.plotly_chart(fig9, use_container_width=True)
        else: st.info("No backlog detail data.")

# FIX: Wrapped in st.container(border=True)
with col_sort:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">8. Sort — FID Sort vs RID Sort</div>', unsafe_allow_html=True)
        if lt_fr is not None:
            fid_sort = _safe(lt_fr, "FID Sort")
            rid_sort = _safe_multi(lt_fr, "RID Sort", "RID LMH Sort")
            fig10 = go.Figure(data=[go.Bar(
                y=["FID Sort", "RID Sort"], x=[fid_sort, rid_sort],
                orientation="h", marker_color=[C_ISD, C_OSD], marker_line=dict(color="#FFFFFF", width=1),
                text=[f"{fid_sort:,.0f}", f"{rid_sort:,.0f}"], textposition="outside",
                textfont=dict(size=14, color="#1C2B3A", weight="bold"), width=0.5,
            )])
            _layout(fig10, height=280, extra={"showlegend": False, "xaxis": dict(**_AX, title="Count"), "yaxis": dict(**_AX), "margin": dict(l=8, r=70, t=32, b=8)})
            st.plotly_chart(fig10, use_container_width=True)
        else: st.info("No sort data.")

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── ROW 4: Date-range Backlog Tracking + Region Vertical Bar ─────────────────
col_track, col_region = st.columns([3, 2])

# FIX: Wrapped in st.container(border=True)
with col_track:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">9. Date-wise Backlog Progress Tracking (FID)</div>', unsafe_allow_html=True)

        if all_dates and len(all_dates) >= 1:
            t_opts = [pd.Timestamp(d).strftime("%d %b %Y") for d in all_dates]
            tc1, tc2 = st.columns(2)
            with tc1: t_si = st.selectbox("📅 From", range(len(t_opts)), format_func=lambda i: t_opts[i], index=0, key="track_from")
            with tc2: t_ei = st.selectbox("📅 To", range(len(t_opts)), format_func=lambda i: t_opts[i], index=len(t_opts)-1, key="track_to")
            if t_ei < t_si: t_ei = t_si
            t_start  = pd.Timestamp(all_dates[t_si])
            t_end    = pd.Timestamp(all_dates[t_ei]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            ft_range = ft[(ft["Date"] >= t_start) & (ft["Date"] <= t_end)].sort_values("Date") if not ft.empty else pd.DataFrame()
        else:
            ft_range = pd.DataFrame(); t_start = sel_start; t_end = sel_end

        if not ft_range.empty:
            fig_track = go.Figure()
            if "Total In Progress (Backlog)" in ft_range.columns:
                fig_track.add_trace(go.Bar(x=ft_range["Date_Label"], y=ft_range["Total In Progress (Backlog)"], name="Total In Process (FID)", marker_color=C_ISD, opacity=0.9))
            if "Worked On" in ft_range.columns:
                fig_track.add_trace(go.Bar(x=ft_range["Date_Label"], y=ft_range["Worked On"], name="Worked On", marker_color=C_SUB, opacity=0.9))
            _layout(fig_track, height=300, extra={"barmode": "group"})
            st.plotly_chart(fig_track, use_container_width=True)
        else: st.info("No FID tracking data for selected period.")

# FIX: Wrapped in st.container(border=True)
with col_region:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">10. Region Wise In-Process Parcels</div>', unsafe_allow_html=True)
        if tot_fid > 0:
            df_reg = pd.DataFrame({"Region": ["ISD", "OSD"], "Parcels": [isd_total, osd_total]})
            fig_reg = px.bar(df_reg, x="Region", y="Parcels", color="Region", color_discrete_map={"ISD": C_ISD, "OSD": C_OSD}, text="Parcels")
            fig_reg.update_traces(texttemplate="%{text:,.0f}", textposition="outside", textfont=dict(color="#1C2B3A", size=14, weight="bold"), width=0.45)
            _layout(fig_reg, height=260, extra={"showlegend": False, "yaxis": dict(**_AX, title="Parcels"), "xaxis": dict(**_AX, title="")})
            st.plotly_chart(fig_reg, use_container_width=True)
            st.markdown(f"""
            <div style="display:flex; gap:16px; justify-content:center; padding:12px 0 4px; border-top: 1px solid #E2E8F0;">
              <div style="text-align:center; flex:1; border-right: 1px solid #E2E8F0;">
                <div style="font-size:11px; color:#6B7E91; text-transform:uppercase; font-weight:700; margin-bottom:2px;">ISD</div>
                <div style="font-size:22px; font-weight:700; color:{C_ISD}; font-family:'DM Mono',monospace;">{isd_total:,.0f}</div>
              </div>
              <div style="text-align:center; flex:1; border-right: 1px solid #E2E8F0;">
                <div style="font-size:11px; color:#6B7E91; text-transform:uppercase; font-weight:700; margin-bottom:2px;">OSD</div>
                <div style="font-size:22px; font-weight:700; color:{C_OSD}; font-family:'DM Mono',monospace;">{osd_total:,.0f}</div>
              </div>
              <div style="text-align:center; flex:1;">
                <div style="font-size:11px; color:#6B7E91; text-transform:uppercase; font-weight:700; margin-bottom:2px;">Total</div>
                <div style="font-size:22px; font-weight:700; color:#1C2B3A; font-family:'DM Mono',monospace;">{tot_fid:,.0f}</div>
              </div>
            </div>""", unsafe_allow_html=True)
        else: st.info("No region data.")

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── ROW 5: Aging Distribution + Aging Table ───────────────────────────────────
AGE_COLS = [str(i) for i in range(1, 11)] + ["10+"]
ag_f = ag[(ag["Date"] >= sel_start) & (ag["Date"] <= sel_end)].copy() if not ag.empty else pd.DataFrame()
if not ag_f.empty and "Region" in ag_f.columns: ag_f = ag_f[ag_f["Region"].isin(region_filter)]

col_aging, col_aging_tbl = st.columns([3, 2])

# FIX: Wrapped in st.container(border=True)
with col_aging:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">11. Aging Distribution</div>', unsafe_allow_html=True)
        st.markdown('<div class="aging-badge">ISD &amp; SUB = 4 Days+ &nbsp;|&nbsp; OSD = 5 Days+</div>', unsafe_allow_html=True)
        if not ag_f.empty:
            ag_max   = ag_f["Date"].max()
            ag_day_f = ag_f[ag_f["Date"] == ag_max].copy()
            rows8 = []
            for _, row in ag_day_f.iterrows():
                region = str(row.get("Region","")).strip()
                if region not in region_filter: continue
                total = float(row.get("Total", 0) or 0)
                if total == 0: total = sum(float(row[c]) for c in AGE_COLS if c in ag_day_f.columns and pd.notna(row[c]))
                for c in AGE_COLS:
                    if c in ag_day_f.columns:
                        val = float(row[c]) if pd.notna(row[c]) else 0.0
                        pct = val / total * 100 if total > 0 else 0.0
                        rows8.append({"Region": region, "Age": f"{c}d", "Count": val, "Pct": pct})
            ag_melt = pd.DataFrame(rows8)
            if not ag_melt.empty:
                fig8 = px.bar(ag_melt, x="Age", y="Pct", color="Region", color_discrete_map={"ISD": C_ISD, "OSD": C_OSD}, barmode="group", text=ag_melt["Pct"].apply(lambda x: f"{x:.1f}%"))
                fig8.update_traces(textposition="outside", textfont=dict(color="#1C2B3A", size=10), customdata=ag_melt[["Count","Region"]], hovertemplate="<b>%{x}</b><br>Region: %{customdata[1]}<br>Count: %{customdata[0]:,.0f}<br>Pct: %{y:.1f}%")
                _layout(fig8, height=300, extra={"yaxis": dict(**_AX, title="Percentage (%)")})
                st.plotly_chart(fig8, use_container_width=True)
            else: st.info("No aging data.")
        else: st.info("No aging distribution data available.")

# FIX: Wrapped in st.container(border=True)
with col_aging_tbl:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">Aging Count &amp; % by Region</div>', unsafe_allow_html=True)
        if not ag_f.empty:
            ag_day_f2 = ag_f[ag_f["Date"] == ag_f["Date"].max()].copy()
            isd_row   = ag_day_f2[ag_day_f2["Region"]=="ISD"].iloc[0] if "ISD" in ag_day_f2["Region"].values else None
            osd_row   = ag_day_f2[ag_day_f2["Region"]=="OSD"].iloc[0] if "OSD" in ag_day_f2["Region"].values else None
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
                    td += f"<td>{v:,.0f}</td><td>{v/isd_tot_v*100:.1f}%</td>" if isd_tot_v else "<td>—</td><td>—</td>"
                if osd_row is not None:
                    v = float(osd_row[c]) if pd.notna(osd_row[c]) else 0
                    td += f"<td>{v:,.0f}</td><td>{v/osd_tot_v*100:.1f}%</td>" if osd_tot_v else "<td>—</td><td>—</td>"
                body_rows += f"<tr>{td}</tr>"
            td_tot = "<td><b>Total</b></td>"
            if isd_row is not None: td_tot += f"<td><b>{isd_tot_v:,.0f}</b></td><td><b>100%</b></td>"
            if osd_row is not None: td_tot += f"<td><b>{osd_tot_v:,.0f}</b></td><td><b>100%</b></td>"
            body_rows += f"<tr>{td_tot}</tr>"
            st.markdown(f"""
            <div style="overflow-x:auto; max-height:340px; overflow-y:auto; border: 1px solid #E2E8F0; border-radius: 8px;">
            <table class="styled-table" style="margin: 0;">
              <thead><tr>{th}</tr></thead>
              <tbody>{body_rows}</tbody>
            </table></div>""", unsafe_allow_html=True)
        else: st.info("No aging data.")

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── ROW 6: Full FID Tracking Table ───────────────────────────────────────────
# FIX: Wrapped in st.container(border=True)
with st.container(border=True):
    st.markdown('<div class="sec-hdr">12. Date-wise Backlog Progress Tracking — Full Table (FID)</div>', unsafe_allow_html=True)
    try: ft_tbl = ft[(ft["Date"] >= t_start) & (ft["Date"] <= t_end)].sort_values("Date").copy() if not ft.empty else pd.DataFrame()
    except Exception: ft_tbl = ft.sort_values("Date").copy() if not ft.empty else pd.DataFrame()

    if not ft_tbl.empty:
        COL_MAP = {"Date_Label": "Date", "Newly Added": "Newly Added", "Total In Progress (Backlog)": "Total In Process (Backlog)", "Worked On": "Worked On", "Carry Forward": "Carry Forward"}
        show_cols = [c for c in COL_MAP if c in ft_tbl.columns]
        df_tbl    = ft_tbl[show_cols].rename(columns=COL_MAP)
        headers   = "".join(f"<th>{c}</th>" for c in df_tbl.columns)
        body      = ""
        for i, (_, r) in enumerate(df_tbl.iterrows()):
            is_last = i == len(df_tbl) - 1
            cells   = ""
            for j, v in enumerate(r):
                cls = "col-date" if j==0 else ("col-high" if is_last else "")
                try: disp = v if j==0 else (f"{int(float(v)):,}" if float(v)!=0 else "—")
                except: disp = "—"
                cells += f"<td class='{cls}'>{disp}</td>"
            body += f"<tr>{cells}</tr>"
        st.markdown(f"""
        <div style="overflow-x:auto; border: 1px solid #E2E8F0; border-radius: 8px;">
        <table class="styled-table" style="margin: 0;">
          <thead><tr>{headers}</tr></thead>
          <tbody>{body}</tbody>
        </table></div>""", unsafe_allow_html=True)
    else: st.info("No FID tracking data to display.")

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── Appendix ──────────────────────────────────────────────────────────────────
with st.expander("📖 Appendix — Definitions & Calculation Methods", expanded=False):
    st.markdown('<div class="appendix-card">', unsafe_allow_html=True)
    st.markdown('<div class="appendix-title">📊 KPI Definitions & Calculation Methods</div>', unsafe_allow_html=True)

    items = [
        ("1. Total In-Process (FID)", "All parcels currently in the First Inbound Delivery process on the selected date. Green = count is lower than yesterday (improving).", "Aging_Distribution → ISD Total + OSD Total"),
        ("2. Overall Backlog (FID+RID)", "Total undelivered backlog across FID and RID. Green = total is falling.", "FID Backlog + RID Backlog  (Source: FID_RID_Backlog_Details)"),
        ("3. Zone Transfer Parcels", "Parcels transferred between delivery zones on the selected date. Sparkline shows 7-day movement.", "Dashboard_Card → 'Zone Transfer' column"),
        ("4. Backlog — FID vs RID (Donut)", "Visual split of overall backlog between First Inbound (FID) and Return Inbound (RID).", "FID Backlog and RID Backlog from FID_RID_Backlog_Details"),
        ("5. FID Backlog %", "Percentage of total in-process FID parcels in backlog. Green arrow + green value = % is lower than yesterday.", "FID Backlog ÷ Total In-Process × 100"),
        ("6. Zone Change %", "Share of total parcels that underwent a zone transfer. Green = lower than yesterday.", "Zone Transfer ÷ Total (Dashboard_Card) × 100"),
        ("7. Backlog Details — FID & RID", "Stacked bar breakdown by service type and region. LMH = Last Mile Hub, FMH = First Mile Hub.", "FID_RID_Backlog_Details → FID/RID × LMH/FMH × ISD/SUB/OSD columns"),
        ("8. Sort — FID Sort vs RID Sort", "Horizontal bar comparing parcels sorted through each pipeline on the selected date.", "FID_RID_Backlog_Details → 'FID Sort' and 'RID Sort'"),
        ("9. Date-wise Backlog Progress Tracking", "Grouped bar chart: Total In-Process FID (blue) vs Worked On (green) over a custom date range.", "FID_Tracking → 'Total In Progress (Backlog)' and 'Worked On'"),
        ("10. Region Wise In-Process Parcels", "Vertical bars comparing ISD vs OSD parcel counts on the selected report date.", "Aging_Distribution → ISD Total and OSD Total"),
        ("11. Aging Distribution", "Percentage of parcels per day-bucket (1d → 10+d) by region. Threshold: ISD/SUB ≥ 4 days, OSD ≥ 5 days = aged.", "Aging_Distribution — columns 1 through 10+"),
        ("Sparkline Colors", "Green sparkline = last value is better than the day before. Red = worsening. Covers last 7 available data points.", "Current day vs previous day comparison"),
        ("ISD / OSD", "Inbound Standard Delivery / Outbound Standard Delivery", ""),
        ("SUB / LMH / FMH", "Sub-hub (intermediate processing) / Last Mile Hub (final) / First Mile Hub (entry)", ""),
        ("FID / RID", "First Inbound Delivery cycle / Return Inbound Delivery", ""),
    ]

    for key, desc, formula in items:
        formula_html = f'<br><span class="appendix-formula">{formula}</span>' if formula else ""
        st.markdown(f"""
        <div class="appendix-row">
          <div class="appendix-key">▸ {key}</div>
          <div class="appendix-val">{desc}{formula_html}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center; color:#6B7E91; font-weight:600; font-size:12px; padding:20px 0 10px; letter-spacing:0.5px;">
  🐝 Carrybee Delivery Intelligence &nbsp;·&nbsp;
  Report Date: <span style="color:#1C2B3A;">{sel_date.strftime('%d %b %Y')}</span>
  &nbsp;·&nbsp; Refreshes every 10 min &nbsp;·&nbsp; Powered by Google Sheets
</div>
""", unsafe_allow_html=True)
    
