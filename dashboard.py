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
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

* { font-family: 'DM Sans', sans-serif; box-sizing: border-box; }

[data-testid="stAppViewContainer"] { background: #F0EDE5 !important; }
[data-testid="stHeader"]           { background: transparent; }
[data-testid="stToolbar"]          { display: none; }
[data-testid="stDecoration"]       { display: none; }

.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    max-width: 98% !important;
}

/* ── Header ── */
.dash-header {
    background: #F5C200;
    border: 1px solid #C99B00;
    border-radius: 12px;
    padding: 14px 28px;
    margin-bottom: 16px;
    display: flex; align-items: center; gap: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.dash-title    { color:#1C2B3A !important; font-size:28px; font-weight:700; margin:0; letter-spacing:-0.5px; }
.dash-subtitle { color:#8A6A00 !important; font-size:14px; margin-top:2px; font-weight:600; }
.dash-bee      { font-size:42px; line-height:1; }

/* ── Filter bar ── */
.filter-bar {
    background: #FFFFFF;
    border-radius: 12px; padding: 16px 24px;
    border: 1px solid #F9DE7A; margin-bottom: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

/* ── KPI cards (yellow) ── */
.kpi-spark, .kpi-small {
    background: #F9DE7A;
    border-radius: 12px;
    border: 1px solid #E8CD68;
    box-shadow: 0 4px 14px rgba(0,0,0,0.07);
    padding: 18px 20px 14px;
    position: relative;
    overflow: hidden;
    width: 100%;
}

.kpi-spark-label {
    font-size: 11px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.9px; color: #8A6A00 !important; margin-bottom: 6px;
}
.kpi-spark-value {
    font-size: 36px; font-weight: 700; line-height: 1;
    font-family: 'DM Mono', monospace; margin-bottom: 6px;
    color: #1C2B3A !important;
}
.kpi-delta-row { font-size: 12px; font-weight: 700; display: flex; align-items: center; gap: 5px; }
.delta-down-good, .delta-up-good { color: #2E7D6B !important; }
.delta-up-bad,   .delta-down-bad { color: #E05C3A !important; }
.delta-neutral                   { color: #6B7E91 !important; }

/* ── Donut card (white, tall) ── */
.donut-card {
    background: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #C4C0B3;
    box-shadow: 0 4px 14px rgba(0,0,0,0.07);
    padding: 18px 20px;
    width: 100%;
    /* height will be set inline to match the two-row left side */
}

/* ── Chart cards ── */
.chart-card {
    background: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #C4C0B3;
    box-shadow: 0 4px 14px rgba(0,0,0,0.07);
    padding: 18px 22px 14px;
    margin-bottom: 0;
}

/* ── Section header ── */
.sec-hdr {
    font-size: 13px; font-weight: 700; color: #1C2B3A !important;
    text-transform: uppercase; letter-spacing: 0.9px;
    border-left: 4px solid #F5C200;
    padding-left: 10px; margin-bottom: 14px;
}

/* ── Aging badge ── */
.aging-badge {
    background: rgba(245,194,0,0.15); border: 1px solid #F5C200; border-radius: 6px;
    padding: 5px 12px; font-size: 11px; color: #1C2B3A !important; font-weight: 700;
    display: inline-block; margin-bottom: 10px;
}

/* ── Table ── */
.styled-table { width:100%; border-collapse:collapse; font-size:12px; }
.styled-table thead tr { background: #F9F8F6; }
.styled-table th {
    padding:10px 12px; text-align:center; font-weight:700;
    color:#1C2B3A !important; border-bottom:2px solid #F5C200;
    text-transform:uppercase; letter-spacing:0.5px;
}
.styled-table tbody tr:hover { background: rgba(0,0,0,0.02); }
.styled-table tbody tr:last-child { background:#FDF3BF; font-weight:700; }
.styled-table td {
    padding:9px 12px; text-align:center;
    border-bottom:1px solid rgba(28,43,58,0.05);
    color:#1C2B3A !important;
}
.styled-table .col-date { text-align:left; font-weight:700; color:#1C2B3A !important; }
.styled-table .col-high { color:#E05C3A !important; font-weight:700; }

/* ── Streamlit overrides ── */
label, .stSelectbox label, .stMultiSelect label {
    color: #1C2B3A !important; font-size: 13px !important; font-weight: 600 !important;
}
div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    border-color: #C4C0B3 !important;
    color: #1C2B3A !important;
}
[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 1px solid #C4C0B3 !important;
    border-radius: 12px !important;
}
</style>
""", unsafe_allow_html=True)

SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1n9GW1UksZ-jhCQ-zmCqwx4EH20fa-Zm5wA5BiMmdZAE/edit?gid=713116247#gid=713116247"
)

C_ISD = "#1C2B3A"
C_OSD = "#8A6A00"
C_SUB = "#6B7E91"
C_AMB = "#E05C3A"
C_PUR = "#2E7D6B"

_AX = dict(
    gridcolor="rgba(28,43,58,0.08)", linecolor="rgba(28,43,58,0.2)",
    tickcolor="rgba(28,43,58,0.2)", showgrid=True,
    tickfont=dict(color="#1C2B3A", size=11),
    title_font=dict(color="#1C2B3A"),
)
_BASE = dict(
    paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
    font=dict(color="#1C2B3A", family="DM Sans, sans-serif", size=11),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#D9D5C8",
                borderwidth=1, font=dict(size=11, color="#1C2B3A")),
    hoverlabel=dict(bgcolor="#1C2B3A", bordercolor="#F5C200",
                    font_color="#FFFFFF", font_size=12),
    margin=dict(l=10, r=10, t=32, b=10),
    xaxis=_AX, yaxis=_AX,
)

def _layout(fig, height=None, extra=None):
    kw = dict(**_BASE)
    if height: kw["height"] = height
    if extra:  kw.update(extra)
    fig.update_layout(**kw)
    return fig

# ── Helpers ───────────────────────────────────────────────────────────────────
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
                df[c].astype(str).str.replace(",","").str.replace("%",""),
                errors="coerce").fillna(0)
    return df

# ── Data Loading ──────────────────────────────────────────────────────────────
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
        raw = raw[~raw.iloc[:,0].astype(str).str.contains(
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
        raw = raw[~raw.iloc[:,0].astype(str).str.contains(
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
        raw = raw.iloc[:,:14]
        raw.columns = ["Date","Region"] + [str(i) for i in range(1,11)] + ["10+","Total"]
        raw = raw[~raw["Date"].astype(str).str.contains(
            "Grand Total|Report Date|nan", case=False, na=True)]
        raw["Date"] = _parse_dates(raw["Date"])
        raw = raw.dropna(subset=["Date"])
        raw["Date"] = _to_date(raw["Date"])
        raw["Region"] = raw["Region"].astype(str).str.strip()
        raw = _nums(raw, [str(i) for i in range(1,11)] + ["10+","Total"])
        raw["Date_Label"] = raw["Date"].dt.strftime("%d %b")
        ag = raw
    except Exception: ag = pd.DataFrame()

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

# ── Filter bar ────────────────────────────────────────────────────────────────
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
                              index=len(date_opts)-1)
    sel_date  = pd.Timestamp(all_dates[sel_di])
    sel_start = sel_date
    sel_end   = sel_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
else:
    sel_date = pd.Timestamp.now().normalize()
    sel_start = sel_date
    sel_end   = sel_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

with fc2:
    region_filter = st.multiselect("🗺️ Region", ["ISD","OSD"], default=["ISD","OSD"])
st.markdown('</div>', unsafe_allow_html=True)

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
    isd_total    = ag_day[ag_day["Region"]=="ISD"]["Total"].sum()
    osd_total    = ag_day[ag_day["Region"]=="OSD"]["Total"].sum()
    tot_fid      = isd_total + osd_total
    prev_ag_d    = ag_le[ag_le["Date"] < ag_last_date]["Date"]
    if not prev_ag_d.empty:
        pr_ag  = ag_le[ag_le["Date"] == prev_ag_d.max()]
        pr_fid = (pr_ag[pr_ag["Region"]=="ISD"]["Total"].sum()
                + pr_ag[pr_ag["Region"]=="OSD"]["Total"].sum())
    else:
        pr_fid = tot_fid
else:
    isd_total = osd_total = tot_fid = pr_fid = 0.0

fid_bl     = _safe(lt_fr, "FID Backlog")
rid_bl     = _safe(lt_fr, "RID Backlog")
overall_bl = fid_bl + rid_bl
pr_overall = _safe(pr_fr,"FID Backlog") + _safe(pr_fr,"RID Backlog")

zt_val    = _safe(lt_dc, "Zone Transfer", default=0.0)
pr_zt_val = _safe(pr_dc, "Zone Transfer", default=0.0)

dc_total   = _safe(lt_dc, "Total")
denom      = dc_total if dc_total > 0 else tot_fid
fid_pct    = (fid_bl / denom * 100) if denom > 0 else 0.0

pr_dc_tot  = _safe(pr_dc, "Total")
pr_den     = pr_dc_tot if pr_dc_tot > 0 else pr_fid
pr_fid_pct = (_safe(pr_fr,"FID Backlog") / pr_den * 100) if pr_den > 0 else 0.0

zt_pct    = (zt_val    / dc_total  * 100) if (zt_val    > 0 and dc_total  > 0) else 0.0
pr_zt_pct = (pr_zt_val / pr_dc_tot * 100) if (pr_zt_val > 0 and pr_dc_tot > 0) else 0.0

# ── Sparkline data ────────────────────────────────────────────────────────────
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

def _sparkline_svg(values, color, width=110, height=42):
    if not values or len(values) < 2: return ""
    mn, mx = min(values), max(values)
    rng = mx - mn if mx != mn else 1
    pad = 4
    pts = []
    for i, v in enumerate(values):
        x = pad + (i/(len(values)-1)) * (width - 2*pad)
        y = pad + (1 - (v-mn)/rng) * (height - 2*pad)
        pts.append(f"{x:.1f},{y:.1f}")
    area = (f"M{pts[0]} " + " ".join(f"L{p}" for p in pts[1:])
            + f" L{width-pad},{height} L{pad},{height} Z")
    lx, ly = pts[-1].split(",")
    uid = color.replace("#","")
    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g{uid}" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{color}" stop-opacity="0.25"/>
    <stop offset="100%" stop-color="{color}" stop-opacity="0.02"/>
  </linearGradient></defs>
  <path d="{area}" fill="url(#g{uid})"/>
  <polyline points="{' '.join(pts)}" fill="none" stroke="{color}" stroke-width="2.2"
            stroke-linejoin="round" stroke-linecap="round"/>
  <circle cx="{lx}" cy="{ly}" r="3.5" fill="{color}"/>
</svg>"""

def _trend(vals, lib=True):
    if not vals or len(vals) < 2: return "#1C2B3A"
    return "#2E7D6B" if (vals[-1] < vals[-2]) == lib else "#E05C3A"

fc = _trend(spark_fid, True)
bc = _trend(spark_bl,  True)
zc = _trend(spark_zt, False)

d_fid = tot_fid    - pr_fid
d_bl  = overall_bl - pr_overall
d_zt  = zt_val     - pr_zt_val

def _delta_html(val, lower_is_better=True, label="vs prev day"):
    arr   = "▼" if val < 0 else ("▲" if val > 0 else "—")
    good  = (val < 0 and lower_is_better) or (val > 0 and not lower_is_better)
    cls   = "delta-down-good" if (val < 0 and lower_is_better) else \
            "delta-up-good"   if (val > 0 and not lower_is_better) else \
            "delta-up-bad"    if val > 0 else \
            "delta-down-bad"  if val < 0 else "delta-neutral"
    return f'<span class="{cls}">{arr} {abs(val):,.0f} {label}</span>'

# ═══════════════════════════════════════════════════════════════════════════════
# KPI BLOCK — Left grid (3 top + 2 bottom) + Right tall donut
# ═══════════════════════════════════════════════════════════════════════════════

# Outer split: 75% left (cards 1-2-3 and 5-6) | 25% right (card 4 donut)
left_col, right_col = st.columns([3, 1])

with left_col:
    # ── Top row: Cards 1, 2, 3 ──────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)

    def _spark_card(col, num, label, value_str, spark_svg, delta_val,
                    delta_label="vs prev day", lower_is_better=True):
        col.markdown(f"""
        <div class="kpi-spark">
          <div class="kpi-spark-label">{num}. {label}</div>
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
            <div class="kpi-spark-value">{value_str}</div>
            <div style="margin-top:4px;">{spark_svg}</div>
          </div>
          <div class="kpi-delta-row">
            {_delta_html(delta_val, lower_is_better, delta_label)}
          </div>
          <div style="font-size:10px;color:#8A6A00;margin-top:4px;font-style:italic;">7-day trend</div>
        </div>""", unsafe_allow_html=True)

    with c1:
        _spark_card(c1, 1, "Total In-Process (FID)",
                    f"{tot_fid:,.0f}", _sparkline_svg(spark_fid, fc),
                    d_fid, "vs prev day", True)
    with c2:
        _spark_card(c2, 2, "Overall Backlog",
                    f"{overall_bl:,.0f}", _sparkline_svg(spark_bl, bc),
                    d_bl, "FID+RID vs prev", True)
    with c3:
        zt_display = f"{int(zt_val):,}" if zt_val > 0 else "0"
        _spark_card(c3, 3, "Zone Transfer Parcels",
                    zt_display, _sparkline_svg(spark_zt, zc),
                    d_zt, "vs prev day", False)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Bottom row: Cards 5, 6 (same width as above, left-aligned) ──────────
    c5, c6, _gap = st.columns([1, 1, 1])   # _gap keeps them same width as c1/c2/c3

    def _pct_card(col, num, label, value, prev, lower_is_better=True):
        diff  = value - prev
        good  = (diff < 0 and lower_is_better) or (diff > 0 and not lower_is_better)
        vcol  = "#2E7D6B" if good else ("#E05C3A" if diff != 0 else "#1C2B3A")
        arr   = "▼" if diff < 0 else ("▲" if diff > 0 else "—")
        d_cls = "delta-down-good" if (diff < 0 and lower_is_better) else \
                "delta-up-good"   if (diff > 0 and not lower_is_better) else \
                "delta-up-bad"    if diff > 0 else \
                "delta-down-bad"  if diff < 0 else "delta-neutral"
        col.markdown(f"""
        <div class="kpi-small">
          <div class="kpi-spark-label">{num}. {label}</div>
          <div style="font-size:36px;font-weight:700;font-family:'DM Mono',monospace;
                      color:{vcol};margin-bottom:8px;line-height:1;">{value:.2f}%</div>
          <div class="kpi-delta-row">
            <span class="{d_cls}" style="font-size:15px;">{arr}</span>
            <span class="{d_cls}">{abs(diff):.2f} pp vs prev day</span>
          </div>
        </div>""", unsafe_allow_html=True)

    with c5:
        _pct_card(c5, 5, "FID Backlog %", fid_pct, pr_fid_pct, True)
    with c6:
        _pct_card(c6, 6, "Zone Change %", zt_pct, pr_zt_pct, True)
    # _gap column stays empty — gives cards 5&6 the same width as 1&2

with right_col:
    # ── Card 4: Tall Donut spanning both rows ────────────────────────────────
    # We inject a fixed min-height so it visually matches the two left rows
    fid_pct_d = fid_bl / (fid_bl + rid_bl) * 100 if (fid_bl + rid_bl) > 0 else 0
    rid_pct_d = rid_bl / (fid_bl + rid_bl) * 100 if (fid_bl + rid_bl) > 0 else 0

    st.markdown("""
    <div class="donut-card" style="min-height:320px;">
      <div class="sec-hdr" style="margin-bottom:10px;">4. Backlog — FID vs RID</div>
    """, unsafe_allow_html=True)

    if (fid_bl + rid_bl) > 0:
        fig_donut = go.Figure(data=[go.Pie(
            labels=["FID","RID"],
            values=[fid_bl, rid_bl],
            hole=0.55,
            marker=dict(colors=["#F5C200","#1C2B3A"],
                        line=dict(color="#FFFFFF", width=3)),
            textinfo="label+percent",
            textposition="outside",
            textfont=dict(size=12, color="#1C2B3A"),
            pull=[0.05, 0.05],
            hovertemplate="<b>%{label}</b><br>Count: %{value:,.0f}<br>Share: %{percent}<extra></extra>",
        )])
        fig_donut.add_annotation(
            text=f"<b>{int(fid_bl+rid_bl):,}</b><br><span style='font-size:10px;color:#6B7E91'>Total</span>",
            x=0.5, y=0.5, showarrow=False,
            xanchor="center", yanchor="middle",
            font=dict(size=15, color="#1C2B3A"),
        )
        _layout(fig_donut, height=220,
                extra={"margin": dict(l=10,r=10,t=30,b=0),
                       "showlegend": False})
        st.plotly_chart(fig_donut, use_container_width=True)

        # FID / RID value strip
        st.markdown(f"""
        <div style="display:flex;gap:0;border-top:1px solid #E8E4DB;padding-top:10px;margin-top:4px;">
          <div style="flex:1;text-align:center;border-right:1px solid #E8E4DB;">
            <div style="font-size:10px;font-weight:700;text-transform:uppercase;
                        color:#8A6A00;margin-bottom:3px;">FID</div>
            <div style="font-size:20px;font-weight:700;color:#1C2B3A;
                        font-family:'DM Mono',monospace;">{fid_bl:,.0f}</div>
            <div style="font-size:11px;color:#6B7E91;font-weight:600;">{fid_pct_d:.1f}%</div>
          </div>
          <div style="flex:1;text-align:center;">
            <div style="font-size:10px;font-weight:700;text-transform:uppercase;
                        color:#1C2B3A;margin-bottom:3px;">RID</div>
            <div style="font-size:20px;font-weight:700;color:#1C2B3A;
                        font-family:'DM Mono',monospace;">{rid_bl:,.0f}</div>
            <div style="font-size:11px;color:#6B7E91;font-weight:600;">{rid_pct_d:.1f}%</div>
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.info("No backlog data.")

    st.markdown('</div>', unsafe_allow_html=True)   # close .donut-card

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 3: Backlog Details + Sort
# ═══════════════════════════════════════════════════════════════════════════════
col_bl, col_sort = st.columns([3, 2])

with col_bl:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">7. Backlog Details — FID &amp; RID (LMH / FMH)</div>',
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
        labs, iv, sv, ov, tots = zip(*detail)
        fig9 = go.Figure()
        for vals, name, color in [(iv,"ISD",C_ISD),(sv,"SUB",C_SUB),(ov,"OSD",C_OSD)]:
            fig9.add_trace(go.Bar(
                name=name, y=labs, x=vals, orientation="h", marker_color=color,
                text=[f"{v:,.0f}" if v>0 else "" for v in vals],
                textposition="inside", insidetextanchor="middle",
                textfont=dict(color="#FFFFFF", size=12),
            ))
        for lbl, tot in zip(labs, tots):
            if tot > 0:
                fig9.add_annotation(x=tot, y=lbl, text=f"  <b>{tot:,.0f}</b>",
                                    showarrow=False, xanchor="left",
                                    font=dict(size=13, color="#1C2B3A"))
        _layout(fig9, height=340, extra={
            "barmode":"stack",
            "xaxis": dict(**_AX, title="Count"),
            "yaxis": dict(**_AX, autorange="reversed"),
        })
        st.plotly_chart(fig9, use_container_width=True)
    else:
        st.info("No backlog detail data.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_sort:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">8. Sort — FID Sort vs RID Sort</div>',
                unsafe_allow_html=True)
    if lt_fr is not None:
        fid_sort = _safe(lt_fr, "FID Sort")
        rid_sort = _safe_multi(lt_fr, "RID Sort","RID LMH Sort")
        fig10 = go.Figure(data=[go.Bar(
            y=["FID Sort","RID Sort"], x=[fid_sort, rid_sort],
            orientation="h",
            marker_color=[C_ISD, C_OSD],
            marker_line=dict(color="#FFFFFF", width=1),
            text=[f"{fid_sort:,.0f}", f"{rid_sort:,.0f}"],
            textposition="outside",
            textfont=dict(size=13, color="#1C2B3A"),
            width=0.5,
        )])
        _layout(fig10, height=340, extra={
            "showlegend": False,
            "xaxis": dict(**_AX, title="Count"),
            "yaxis": dict(**_AX),
            "margin": dict(l=8, r=80, t=32, b=8),
        })
        st.plotly_chart(fig10, use_container_width=True)
    else:
        st.info("No sort data.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 4: Date-range Tracking + Region bars
# ═══════════════════════════════════════════════════════════════════════════════
col_track, col_region = st.columns([3, 2])

with col_track:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">9. Date-wise Backlog Progress Tracking (FID)</div>',
                unsafe_allow_html=True)
    if all_dates:
        t_opts = [pd.Timestamp(d).strftime("%d %b %Y") for d in all_dates]
        tc1, tc2 = st.columns(2)
        with tc1:
            t_si = st.selectbox("📅 From", range(len(t_opts)),
                                format_func=lambda i: t_opts[i],
                                index=0, key="tr_from")
        with tc2:
            t_ei = st.selectbox("📅 To", range(len(t_opts)),
                                format_func=lambda i: t_opts[i],
                                index=len(t_opts)-1, key="tr_to")
        if t_ei < t_si: t_ei = t_si
        t_start = pd.Timestamp(all_dates[t_si])
        t_end   = pd.Timestamp(all_dates[t_ei]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        ft_r    = ft[(ft["Date"]>=t_start)&(ft["Date"]<=t_end)].sort_values("Date") \
                  if not ft.empty else pd.DataFrame()
    else:
        ft_r    = pd.DataFrame()
        t_start = sel_start
        t_end   = sel_end

    if not ft_r.empty:
        fig_tr = go.Figure()
        if "Total In Progress (Backlog)" in ft_r.columns:
            fig_tr.add_trace(go.Bar(
                x=ft_r["Date_Label"], y=ft_r["Total In Progress (Backlog)"],
                name="Total In Process (FID)", marker_color=C_ISD, opacity=0.9,
            ))
        if "Worked On" in ft_r.columns:
            fig_tr.add_trace(go.Bar(
                x=ft_r["Date_Label"], y=ft_r["Worked On"],
                name="Worked On", marker_color=C_SUB, opacity=0.9,
            ))
        _layout(fig_tr, height=340, extra={"barmode":"group"})
        st.plotly_chart(fig_tr, use_container_width=True)
    else:
        st.info("No FID tracking data.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_region:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">10. Region Wise In-Process Parcels</div>',
                unsafe_allow_html=True)
    if tot_fid > 0:
        df_reg = pd.DataFrame({"Region":["ISD","OSD"], "Parcels":[isd_total,osd_total]})
        fig_reg = px.bar(df_reg, x="Region", y="Parcels",
                         color="Region",
                         color_discrete_map={"ISD":C_ISD,"OSD":C_OSD},
                         text="Parcels")
        fig_reg.update_traces(
            texttemplate="%{text:,.0f}", textposition="outside",
            textfont=dict(color="#1C2B3A", size=13),
            width=0.45,
        )
        _layout(fig_reg, height=260, extra={
            "showlegend": False,
            "yaxis": dict(**_AX, title="Parcels"),
            "xaxis": dict(**_AX, title=""),
        })
        st.plotly_chart(fig_reg, use_container_width=True)
        st.markdown(f"""
        <div style="display:flex;gap:0;border-top:1px solid rgba(28,43,58,0.1);
                    padding-top:10px;margin-top:4px;">
          <div style="flex:1;text-align:center;border-right:1px solid rgba(28,43,58,0.08);">
            <div style="font-size:11px;font-weight:700;text-transform:uppercase;
                        color:#8A6A00;margin-bottom:2px;">ISD</div>
            <div style="font-size:22px;font-weight:700;color:{C_ISD};
                        font-family:'DM Mono',monospace;">{isd_total:,.0f}</div>
          </div>
          <div style="flex:1;text-align:center;border-right:1px solid rgba(28,43,58,0.08);">
            <div style="font-size:11px;font-weight:700;text-transform:uppercase;
                        color:#1C2B3A;margin-bottom:2px;">OSD</div>
            <div style="font-size:22px;font-weight:700;color:{C_OSD};
                        font-family:'DM Mono',monospace;">{osd_total:,.0f}</div>
          </div>
          <div style="flex:1;text-align:center;">
            <div style="font-size:11px;font-weight:700;text-transform:uppercase;
                        color:#1C2B3A;margin-bottom:2px;">Total</div>
            <div style="font-size:22px;font-weight:700;color:#1C2B3A;
                        font-family:'DM Mono',monospace;">{tot_fid:,.0f}</div>
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.info("No region data.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 5: Aging Distribution + Aging Table
# ═══════════════════════════════════════════════════════════════════════════════
AGE_COLS = [str(i) for i in range(1,11)] + ["10+"]
ag_f = ag[(ag["Date"]>=sel_start)&(ag["Date"]<=sel_end)].copy() if not ag.empty else pd.DataFrame()
if not ag_f.empty and "Region" in ag_f.columns:
    ag_f = ag_f[ag_f["Region"].isin(region_filter)]

col_aging, col_aging_tbl = st.columns([3, 2])

with col_aging:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">11. Aging Distribution</div>', unsafe_allow_html=True)
    st.markdown('<div class="aging-badge">ISD &amp; SUB = 4 Days+ &nbsp;|&nbsp; OSD = 5 Days+</div>',
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
                    pct = val/total*100 if total > 0 else 0.0
                    rows8.append({"Region":region,"Age":f"{c}d","Count":val,"Pct":pct})
        ag_melt = pd.DataFrame(rows8)
        if not ag_melt.empty:
            fig8 = px.bar(ag_melt, x="Age", y="Pct", color="Region",
                          color_discrete_map={"ISD":C_ISD,"OSD":C_OSD},
                          barmode="group",
                          text=ag_melt["Pct"].apply(lambda x: f"{x:.1f}%"))
            fig8.update_traces(
                textposition="outside",
                textfont=dict(color="#1C2B3A", size=10),
                customdata=ag_melt[["Count","Region"]],
                hovertemplate="<b>%{x}</b><br>Region: %{customdata[1]}<br>"
                              "Count: %{customdata[0]:,.0f}<br>Pct: %{y:.1f}%",
            )
            _layout(fig8, height=320, extra={"yaxis": dict(**_AX, title="Percentage (%)")})
            st.plotly_chart(fig8, use_container_width=True)
        else:
            st.info("No aging data.")
    else:
        st.info("No aging distribution data available.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_aging_tbl:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">Aging Count &amp; % by Region</div>', unsafe_allow_html=True)
    if not ag_f.empty:
        ag_d2  = ag_f[ag_f["Date"]==ag_f["Date"].max()].copy()
        isd_r  = ag_d2[ag_d2["Region"]=="ISD"].iloc[0] if "ISD" in ag_d2["Region"].values else None
        osd_r  = ag_d2[ag_d2["Region"]=="OSD"].iloc[0] if "OSD" in ag_d2["Region"].values else None
        isd_t  = float(isd_r["Total"]) if isd_r is not None else 0
        osd_t  = float(osd_r["Total"]) if osd_r is not None else 0
        th = "<th>Days</th>"
        if isd_r is not None: th += "<th>ISD</th><th>ISD %</th>"
        if osd_r is not None: th += "<th>OSD</th><th>OSD %</th>"
        body = ""
        for c in AGE_COLS:
            if c not in ag_d2.columns: continue
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
        <div style="overflow-x:auto;max-height:360px;overflow-y:auto;
                    border:1px solid #C4C0B3;border-radius:10px;">
        <table class="styled-table" style="margin:0;">
          <thead><tr>{th}</tr></thead>
          <tbody>{body}</tbody>
        </table></div>""", unsafe_allow_html=True)
    else:
        st.info("No aging data.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 6: Full FID Tracking Table
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="chart-card">', unsafe_allow_html=True)
st.markdown('<div class="sec-hdr">12. Date-wise Backlog Progress Tracking — Full Table (FID)</div>',
            unsafe_allow_html=True)
try:
    ft_tbl = ft[(ft["Date"]>=t_start)&(ft["Date"]<=t_end)].sort_values("Date").copy() \
             if not ft.empty else pd.DataFrame()
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
    body    = ""
    for i, (_, r) in enumerate(df_tbl.iterrows()):
        is_last = i == len(df_tbl)-1
        cells   = ""
        for j, v in enumerate(r):
            cls = "col-date" if j==0 else ("col-high" if is_last else "")
            try: disp = v if j==0 else (f"{int(float(v)):,}" if float(v)!=0 else "—")
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
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# APPENDIX
# ═══════════════════════════════════════════════════════════════════════════════
with st.expander("📖 Appendix — Definitions & Calculation Methods", expanded=False):
    items = [
        ("1. Total In-Process (FID)", "All parcels in the First Inbound Delivery cycle on the selected date.", "Aging_Distribution → ISD Total + OSD Total"),
        ("2. Overall Backlog (FID+RID)", "Total undelivered backlog across FID and RID.", "FID Backlog + RID Backlog  (Source: FID_RID_Backlog_Details)"),
        ("3. Zone Transfer Parcels", "Parcels transferred between delivery zones on the selected date.", "Dashboard_Card → 'Zone Transfer' column"),
        ("4. Backlog — FID vs RID (Donut)", "Visual split of overall backlog between FID and RID.", "FID Backlog and RID Backlog from FID_RID_Backlog_Details"),
        ("5. FID Backlog %", "Percentage of total in-process FID parcels in backlog.", "FID Backlog ÷ Total In-Process × 100"),
        ("6. Zone Change %", "Share of total parcels that underwent a zone transfer.", "Zone Transfer ÷ Total (Dashboard_Card) × 100"),
        ("7. Backlog Details — FID & RID (LMH/FMH)", "Stacked bar breakdown by service type and region.", "FID_RID_Backlog_Details → FID/RID × LMH/FMH × ISD/SUB/OSD"),
        ("8. Sort — FID Sort vs RID Sort", "Horizontal bars comparing parcels sorted through each pipeline.", "FID_RID_Backlog_Details → 'FID Sort' and 'RID Sort'"),
        ("9. Date-wise Backlog Tracking", "Grouped bars: Total In-Process FID vs Worked On over a custom date range.", "FID_Tracking → 'Total In Progress (Backlog)' and 'Worked On'"),
        ("10. Region Wise In-Process", "Vertical bars comparing ISD vs OSD parcel volume on the selected date.", "Aging_Distribution → ISD Total and OSD Total"),
        ("11. Aging Distribution", "% of parcels per day-bucket (1d→10+d) by region. ISD/SUB ≥ 4 days = aged.", "Aging_Distribution → columns 1 through 10+"),
        ("ISD", "Inbound Standard Delivery", ""),
        ("OSD", "Outbound Standard Delivery", ""),
        ("SUB", "Sub-hub — intermediate processing centre", ""),
        ("LMH", "Last Mile Hub — final hub before customer delivery", ""),
        ("FMH", "First Mile Hub — network entry point", ""),
        ("FID", "First Inbound Delivery cycle", ""),
        ("RID", "Return Inbound Delivery — re-entered returned parcels", ""),
    ]
    for key, desc, formula in items:
        fh = f'<br><span style="color:#6B7E91;font-size:12px;">{formula}</span>' if formula else ""
        st.markdown(f"""
        <div style="margin-bottom:12px;">
          <div style="font-weight:700;color:#1C2B3A;">▸ {key}</div>
          <div style="color:#1C2B3A;padding-left:14px;">{desc}{fh}</div>
        </div>""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;color:#6B7E91;font-size:12px;font-weight:600;
            padding:18px 0 8px;letter-spacing:0.4px;">
  🐝 Carrybee Delivery Intelligence &nbsp;·&nbsp;
  Report Date: <span style="color:#1C2B3A;">{sel_date.strftime('%d %b %Y')}</span>
  &nbsp;·&nbsp; Refreshes every 10 min &nbsp;·&nbsp; Powered by Google Sheets
</div>
""", unsafe_allow_html=True)
