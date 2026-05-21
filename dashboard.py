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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }

/* Clean, modern light background for maximum readability */
[data-testid="stAppViewContainer"] { background: #F4F7F9; }
[data-testid="stHeader"]           { background: transparent; }
[data-testid="stToolbar"]          { display: none; }
[data-testid="stDecoration"]       { display: none; }
.block-container { padding-top:1.5rem !important; padding-bottom:1.5rem !important; max-width:98% !important; }

/* Premium Header: Deep Navy background with Golden Yellow accents */
.dash-header {
    background: #1C2B3A;
    border-left: 6px solid #F5C200;
    border-radius: 12px; padding: 22px 30px; margin-bottom: 24px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
.dash-title    { color:#FFFFFF !important; font-size:28px; font-weight:800; margin:0; letter-spacing: -0.5px; }
.dash-subtitle { color:#F5C200 !important; font-size:14px; margin-top:6px; font-weight: 500; }

/* Cards / Surface: Pure White for high contrast */
.chart-card, .filter-bar {
    background: #FFFFFF; border-radius: 12px; padding: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.03); 
    border: 1px solid #E2E8F0; margin-bottom: 16px;
}

/* KPI Cards: Minimalist enterprise design with left-border color accents */
.kpi-card {
    background: #FFFFFF;
    border-radius: 12px; padding: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    border: 1px solid #E2E8F0;
    position: relative; min-height: 124px;
    display: flex; flex-direction: column; justify-content: space-between;
}
.bg-blue   { border-left: 5px solid #1C2B3A; } /* Deep Navy */
.bg-red    { border-left: 5px solid #E05C3A; } /* Burnt Coral */
.bg-amber  { border-left: 5px solid #F5C200; } /* Golden Yellow */
.bg-green  { border-left: 5px solid #2E7D6B; } /* Teal Green */
.bg-purple { border-left: 5px solid #6B7E91; } /* Slate Gray */

.kpi-label { font-size:12px; font-weight:600; text-transform:uppercase;
             letter-spacing:0.5px; color:#6B7E91 !important; margin-bottom:8px; }
.kpi-value { font-size:32px; font-weight:800; line-height:1;
             color:#1C2B3A !important; margin-bottom:8px; letter-spacing:-0.5px; }
             
/* Delta Badges */
.kpi-delta { font-size:12px; padding:3px 10px; border-radius:20px;
             display:inline-flex; align-items:center; font-weight:600; }
.kpi-delta.up   { color:#2E7D6B !important; background:rgba(46,125,107,0.12); }
.kpi-delta.down { color:#E05C3A !important; background:rgba(224,92,58,0.12); }

/* Section Headers */
.sec-hdr {
    font-size:15px; font-weight:700; color:#1C2B3A !important;
    border-bottom: 2px solid #F1F5F9;
    padding-bottom: 10px; margin-bottom: 16px;
}

/* Badges */
.aging-badge {
    background:#FFFBEB; border:1px solid #F5C200; border-radius:6px;
    padding:6px 12px; font-size:12px; color:#8A6A00 !important; font-weight:600;
    display:inline-block; margin-bottom:12px;
}

/* Tables */
.styled-table { width:100%; border-collapse:collapse; font-size:13px; }
.styled-table thead tr { background:#1C2B3A; }
.styled-table th { padding:10px 12px; text-align:center;
                   font-weight:600; font-size:12px; color:#FFFFFF !important; text-transform:uppercase; letter-spacing:0.5px; }
.styled-table tbody tr:nth-child(even) { background:#F8FAFC; }
.styled-table tbody tr:last-child      { background:#FDF3BF; font-weight:700; border-top:2px solid #F5C200; }
.styled-table td { padding:10px 12px; text-align:center;
                   border-bottom:1px solid #E2E8F0; color:#1C2B3A !important; }
.styled-table .col-date { text-align:left; font-weight:600; color:#6B7E91 !important; }
.styled-table .col-high { color:#E05C3A !important; font-weight:700; }
</style>
""", unsafe_allow_html=True)

SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1n9GW1UksZ-jhCQ-zmCqwx4EH20fa-Zm5wA5BiMmdZAE/edit?gid=713116247#gid=713116247"
)

# Base Plotly styling adjusted for clean, readable light UI
_AX = dict(
    gridcolor="#F1F5F9", linecolor="#E2E8F0", tickcolor="#CBD5E1",
    showgrid=True,
    tickfont=dict(color="#6B7E91", size=12),
    title_font=dict(color="#1C2B3A", size=13, weight="bold"),
)
_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#1C2B3A", family="Inter, sans-serif", size=12),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#E2E8F0",
                borderwidth=1, font=dict(size=12, color="#1C2B3A")),
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

# Core palette mapping mapped to logical data series
C_ISD = "#1C2B3A" # Deep Navy
C_OSD = "#E05C3A" # Burnt Coral
C_SUB = "#2E7D6B" # Teal Green
C_AMB = "#F5C200" # Golden Yellow 
C_PUR = "#6B7E91" # Slate Gray

# ── Helpers ───────────────────────────────────────────────────────────────────
def _safe(row, col, default=0.0):
    if row is None:
        return default
    try:
        if isinstance(row, dict):
            v = row.get(col, default)
        else:
            v = row[col] if col in row.index else default
        return float(v) if pd.notna(v) else default
    except Exception:
        return default

def _safe_multi(row, *cols, default=0.0):
    for col in cols:
        v = _safe(row, col, default=None)
        if v is not None and v != 0.0:
            return v
    return default

def _fix_year(s):
    cy = pd.Timestamp.now().year
    bad = s.dt.year < 2000
    if bad.any():
        s = s.copy()
        s[bad] = s[bad].apply(lambda t: t.replace(year=cy) if pd.notna(t) else t)
    return s

def _parse_dates(col):
    return _fix_year(
        pd.to_datetime(col.astype(str).str.strip(), dayfirst=True, errors="coerce")
    )

def _to_date(ts_series):
    return pd.to_datetime(ts_series.dt.date)

def _nums(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(
                df[c].astype(str).str.replace(",", "").str.replace("%", ""),
                errors="coerce",
            ).fillna(0)
    return df

# ── Data Loading ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)

    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Dashboard_Card", header=None)
        raw.columns = [str(c).strip() for c in raw.iloc[1]]
        raw = raw.iloc[2:].reset_index(drop=True)
        raw = raw[~raw["Date"].astype(str).str.contains("Grand Total|Date|nan|Backlog|ISD Backlog", case=False, na=True)]
        raw["Date"] = _parse_dates(raw["Date"])
        raw = raw.dropna(subset=["Date"])
        raw["Date"] = _to_date(raw["Date"])
        num_cols = [c for c in raw.columns if c != "Date"]
        raw = _nums(raw, num_cols)
        raw["Date_Label"] = raw["Date"].dt.strftime("%d %b")
        dc = raw
    except Exception as e:
        st.warning(f"Dashboard_Card error: {e}")
        dc = pd.DataFrame()

    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="FID_Tracking")
        raw.columns = [str(c).strip() for c in raw.columns]
        raw = raw[~raw.iloc[:, 0].astype(str).str.contains("Grand Total|Report Date|nan", case=False, na=True)]
        raw.rename(columns={raw.columns[0]: "Date"}, inplace=True)
        raw["Date"] = _parse_dates(raw["Date"])
        raw = raw.dropna(subset=["Date"])
        raw["Date"] = _to_date(raw["Date"])
        raw = _nums(raw, list(raw.columns[1:]))
        raw["Date_Label"] = raw["Date"].dt.strftime("%d %b")
        ft = raw
    except Exception as e:
        st.warning(f"FID_Tracking error: {e}")
        ft = pd.DataFrame()

    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="FID_RID_Backlog_Details")
        raw.columns = [str(c).strip() for c in raw.columns]
        raw = raw[~raw.iloc[:, 0].astype(str).str.contains("Grand Total|Date|nan", case=False, na=True)]
        raw.rename(columns={raw.columns[0]: "Date"}, inplace=True)
        raw["Date"] = _parse_dates(raw["Date"])
        raw = raw.dropna(subset=["Date"])
        raw["Date"] = _to_date(raw["Date"])
        raw = _nums(raw, list(raw.columns[1:]))
        raw["Date_Label"] = raw["Date"].dt.strftime("%d %b")
        fr = raw
    except Exception as e:
        st.warning(f"FID_RID_Backlog_Details error: {e}")
        fr = pd.DataFrame()

    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Aging_Distribution")
        raw = raw.iloc[:, :14]
        raw.columns = ["Date", "Region"] + [str(i) for i in range(1, 11)] + ["10+", "Total"]
        raw = raw[~raw["Date"].astype(str).str.contains("Grand Total|Report Date|nan", case=False, na=True)]
        raw["Date"] = _parse_dates(raw["Date"])
        raw = raw.dropna(subset=["Date"])
        raw["Date"] = _to_date(raw["Date"])
        raw["Region"] = raw["Region"].astype(str).str.strip()
        raw = _nums(raw, [str(i) for i in range(1, 11)] + ["10+", "Total"])
        raw["Date_Label"] = raw["Date"].dt.strftime("%d %b")
        ag = raw
    except Exception as e:
        st.warning(f"Aging_Distribution error: {e}")
        ag = pd.DataFrame()

    return dc, ft, fr, ag

with st.spinner("🐝 Loading live data from Google Sheets…"):
    dc, ft, fr, ag = load_data()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dash-header">
  <div class="dash-title">🐝 Carrybee Delivery Intelligence</div>
  <div class="dash-subtitle">Live Backlog &amp; Operations Dashboard — Auto-refreshes every 10 minutes</div>
</div>
""", unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────────────────────────
st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 2])

all_dates = sorted(ft["Date"].dropna().unique()) if not ft.empty else []
if all_dates:
    date_opts = [pd.Timestamp(d).strftime("%d %b %Y") for d in all_dates]
    with fc1:
        si = st.selectbox("📅 From Date", range(len(date_opts)), format_func=lambda i: date_opts[i], index=0)
    with fc2:
        ei = st.selectbox("📅 To Date", range(len(date_opts)), format_func=lambda i: date_opts[i], index=len(date_opts) - 1)
    if ei < si: ei = si
    sel_start = pd.Timestamp(all_dates[si])
    sel_end   = pd.Timestamp(all_dates[ei]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
else:
    sel_start = pd.Timestamp.now().normalize()
    sel_end   = sel_start + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    st.error("No dates found — check sheet format.")

with fc3:
    region_filter = st.multiselect("🗺️ Region", ["ISD", "OSD"], default=["ISD", "OSD"])
with fc4:
    show_worked = st.toggle("📈 Show Worked On", value=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── Filter / latest helpers ───────────────────────────────────────────────────
def _filt(df, region_col=None):
    if df is None or df.empty: return pd.DataFrame()
    mask = (df["Date"] >= sel_start) & (df["Date"] <= sel_end)
    out  = df[mask].copy()
    if region_col and region_filter and region_col in out.columns:
        out = out[out[region_col].isin(region_filter)]
    return out

def _latest(df):
    if df is None or df.empty: return None
    sub = df[df["Date"] <= sel_end].sort_values("Date")
    return sub.iloc[-1] if not sub.empty else None

def _prev(df):
    if df is None or df.empty: return None
    sub = df[df["Date"] <= sel_end].sort_values("Date")
    return sub.iloc[-2] if len(sub) >= 2 else None

ft_f = _filt(ft)
dc_f = _filt(dc)
fr_f = _filt(fr)
ag_f = _filt(ag, "Region")

lt_dc = _latest(dc)
lt_fr = _latest(fr)

# ── Metrics Calculations ──────────────────────────────────────────────────────
ag_le = ag[ag["Date"] <= sel_end] if not ag.empty else ag
if not ag_le.empty:
    ag_last_date = ag_le["Date"].max()
    ag_day       = ag_le[ag_le["Date"] == ag_last_date]
    isd_total    = ag_day[ag_day["Region"] == "ISD"]["Total"].sum()
    osd_total    = ag_day[ag_day["Region"] == "OSD"]["Total"].sum()
    tot_fid      = isd_total + osd_total
else:
    isd_total = osd_total = tot_fid = 0.0

fid_bl     = _safe(lt_fr, "FID Backlog")
rid_bl     = _safe(lt_fr, "RID Backlog")
overall_bl = fid_bl + rid_bl

zt_val = _safe(lt_dc, "Zone Transfer", default=0.0)

dc_total_val = _safe(lt_dc, "Total")
denom        = dc_total_val if dc_total_val > 0 else tot_fid
fid_pct      = (fid_bl / denom * 100) if denom > 0 else 0.0

zt_pct = (zt_val / dc_total_val * 100) if (zt_val > 0 and dc_total_val > 0) else 0.0

pr_fr = _prev(fr)
if not ag_le.empty:
    prev_dates = ag_le[ag_le["Date"] < ag_last_date]["Date"]
    if not prev_dates.empty:
        pr_ag_day  = ag_le[ag_le["Date"] == prev_dates.max()]
        pr_isd     = pr_ag_day[pr_ag_day["Region"] == "ISD"]["Total"].sum()
        pr_osd     = pr_ag_day[pr_ag_day["Region"] == "OSD"]["Total"].sum()
        pr_tot_fid = pr_isd + pr_osd
    else:
        pr_tot_fid = tot_fid
else:
    pr_tot_fid = tot_fid

d_fid   = tot_fid    - pr_tot_fid
d_bl    = overall_bl - (_safe(pr_fr, "FID Backlog") + _safe(pr_fr, "RID Backlog"))
pr_fbl  = _safe(pr_fr, "FID Backlog")
d_fpct  = ((pr_fbl / pr_tot_fid * 100) - fid_pct) if pr_tot_fid > 0 else 0.0

# ── ROW 1: 5 KPI Cards ────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

def _kpi(col_w, label, bg, value_str, delta=None, unit="", sub=None):
    dh = ""
    if delta is not None:
        arr     = "▲" if delta >= 0 else "▼"
        d_class = "up" if delta >= 0 else "down"
        dh = f'<div class="kpi-delta {d_class}">{arr} {abs(delta):,.2f} {unit}</div>'
    sub_html = (f'<div style="font-size:11px;color:#6B7E91 !important;margin-top:4px;">{sub}</div>' if sub else "")
    col_w.markdown(f"""
    <div class="kpi-card {bg}">
      <div>
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value_str}</div>
      </div>
      <div>{dh}{sub_html}</div>
    </div>""", unsafe_allow_html=True)

zt_display = f"{int(zt_val):,}" if zt_val > 0 else "0"

_kpi(c1, "1. Total In-Process (FID)", "bg-blue",   f"{tot_fid:,.0f}",    d_fid,   "vs prev day")
_kpi(c2, "2. Overall Backlog",         "bg-red",    f"{overall_bl:,.0f}", d_bl,    "FID+RID")
_kpi(c3, "3. Zone Transfer Parcels",   "bg-amber",  zt_display,           None)
_kpi(c4, "4. FID Backlog %",           "bg-green",  f"{fid_pct:.2f}%",    -d_fpct, "pp vs prev")
_kpi(c5, "5. Zone Change %",           "bg-purple", f"{zt_pct:.2f}%",     None)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── ROW 2: Chart 11 (FID Tracking combo) + Chart 6 (Region donut/bar) ─────────
col_l, col_r = st.columns([3, 2])

with col_l:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">11. Date-wise Backlog Progress Tracking (FID)</div>', unsafe_allow_html=True)
    if not ft_f.empty:
        fig11 = go.Figure()
        if "Total In Progress (Backlog)" in ft_f.columns:
            fig11.add_trace(go.Bar(x=ft_f["Date_Label"], y=ft_f["Total In Progress (Backlog)"],
                                   name="Total In Process", marker_color=C_ISD))
        if "Newly Added" in ft_f.columns:
            fig11.add_trace(go.Bar(x=ft_f["Date_Label"], y=ft_f["Newly Added"],
                                   name="Newly Added", marker_color=C_AMB))
        if "Carry Forward" in ft_f.columns:
            fig11.add_trace(go.Bar(x=ft_f["Date_Label"], y=ft_f["Carry Forward"],
                                   name="Carry Forward", marker_color=C_PUR))
        if show_worked and "Worked On" in ft_f.columns:
            fig11.add_trace(go.Scatter(x=ft_f["Date_Label"], y=ft_f["Worked On"],
                                       name="Worked On", mode="lines+markers",
                                       line=dict(color=C_SUB, width=3),
                                       marker=dict(size=8, line=dict(color="#FFF", width=2))))
        _layout(fig11, height=330, extra={"barmode": "group"})
        st.plotly_chart(fig11, use_container_width=True)
    else:
        st.info("No FID tracking data for selected period.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_r:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">6. Region Wise In-Process Parcels</div>', unsafe_allow_html=True)
    if tot_fid > 0:
        fig_d = go.Figure(data=[go.Pie(
            labels=["ISD", "OSD"], values=[isd_total, osd_total],
            hole=0.6, marker_colors=[C_ISD, C_OSD],
            textinfo="label+percent",
            textfont=dict(size=13, color="#FFFFFF", weight="bold"), pull=[0.03, 0],
        )])
        fig_d.add_annotation(
            text=f"<span style='font-size:20px; font-weight:800; color:#1C2B3A;'>{tot_fid:,.0f}</span><br><span style='font-size:12px; color:#6B7E91;'>Total Parcels</span>",
            x=0.5, y=0.5, showarrow=False, xanchor="center",
        )
        _layout(fig_d, height=240, extra={"legend": dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)})
        st.plotly_chart(fig_d, use_container_width=True)

        df_reg = pd.DataFrame({"Region": ["ISD", "OSD"], "Parcels": [isd_total, osd_total]})
        fig_rb = px.bar(df_reg, x="Parcels", y="Region", orientation="h",
                        color="Region", color_discrete_map={"ISD": C_ISD, "OSD": C_OSD}, text="Parcels")
        fig_rb.update_traces(texttemplate="%{text:,.0f}", textposition="outside", textfont=dict(color="#1C2B3A", size=13))
        _layout(fig_rb, height=130, extra={"showlegend": False, "margin": dict(l=10, r=90, t=5, b=5)})
        st.plotly_chart(fig_rb, use_container_width=True)
    else:
        st.info("No Aging_Distribution data available for selected range.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── ROW 3: Chart 7 (FID vs RID backlog) + Chart 9 (Backlog Details) ───────────
col_l3, col_r3 = st.columns([2, 3])

with col_l3:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">7. Backlog — FID vs RID</div>', unsafe_allow_html=True)
    if lt_fr is not None and (fid_bl + rid_bl) > 0:
        fig7 = go.Figure(data=[go.Bar(
            x=["FID Backlog", "RID Backlog"], y=[fid_bl, rid_bl],
            marker_color=[C_ISD, C_OSD],
            text=[f"{fid_bl:,.0f}", f"{rid_bl:,.0f}"],
            textposition="outside", textfont=dict(size=14, color="#1C2B3A", weight="bold"),
            width=0.45,
        )])
        _layout(fig7, height=300, extra={"showlegend": False})
        st.plotly_chart(fig7, use_container_width=True)
    else:
        st.info("No FID/RID backlog data for selected period.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_r3:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">9. Backlog Details — FID &amp; RID (LMH / FMH)</div>', unsafe_allow_html=True)
    if lt_fr is not None:
        detail_rows = [
            ("FID LMH", _safe(lt_fr, "FID LMH ISD"), _safe(lt_fr, "FID LMH SUB"), _safe(lt_fr, "FID LMH OSD"), _safe(lt_fr, "FID LMH Total")),
            ("FID FMH", _safe(lt_fr, "FID FMH"), 0, 0, _safe(lt_fr, "FID FMH")),
            ("RID FMH", _safe(lt_fr, "RID FMH ISD"), _safe(lt_fr, "RID FMH SUB"), _safe(lt_fr, "RID FMH OSD"), _safe(lt_fr, "RID FMH ISD") + _safe(lt_fr, "RID FMH SUB") + _safe(lt_fr, "RID FMH OSD")),
            ("RID LMH", _safe(lt_fr, "RID LMH ISD"), _safe(lt_fr, "RID LMH SUB"), _safe(lt_fr, "RID LMH OSD"), _safe(lt_fr, "RID LMH ISD") + _safe(lt_fr, "RID LMH SUB") + _safe(lt_fr, "RID LMH OSD")),
        ]
        labels, isd_v, sub_v, osd_v, tots = zip(*detail_rows)

        fig9 = go.Figure()
        for vals, name, color in [(isd_v, "ISD", C_ISD), (sub_v, "SUB", C_SUB), (osd_v, "OSD", C_OSD)]:
            fig9.add_trace(go.Bar(
                name=name, y=labels, x=vals, orientation="h", marker_color=color,
                text=[f"{v:,.0f}" if v > 0 else "" for v in vals],
                textposition="inside", insidetextanchor="middle", textfont=dict(color="#FFFFFF", size=12),
            ))
        for lbl, tot in zip(labels, tots):
            if tot > 0:
                fig9.add_annotation(x=tot, y=lbl, text=f"  <b>{tot:,.0f}</b>", showarrow=False, xanchor="left", font=dict(size=13, color="#1C2B3A"))
        _layout(fig9, height=320, extra={"barmode": "stack", "xaxis": dict(**_AX, title="Count"), "yaxis": dict(**_AX, autorange="reversed")})
        st.plotly_chart(fig9, use_container_width=True)
    else:
        st.info("No backlog detail data for selected period.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── ROW 4: Chart 10 (Sort) + Chart 8 (Aging Distribution) ────────────────────
col_l4, col_r4 = st.columns(2)

with col_l4:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">10. Sort — FID Sort vs RID Sort</div>', unsafe_allow_html=True)
    if lt_fr is not None:
        fid_sort = _safe(lt_fr, "FID Sort")
        rid_sort = _safe_multi(lt_fr, "RID Sort", "RID LMH Sort")

        fig10 = go.Figure(data=[go.Bar(
            x=["FID Sort", "RID Sort"], y=[fid_sort, rid_sort],
            marker_color=[C_ISD, C_OSD],
            text=[f"{fid_sort:,.0f}", f"{rid_sort:,.0f}"],
            textposition="outside", textfont=dict(size=14, color="#1C2B3A", weight="bold"), width=0.4,
        )])
        _layout(fig10, height=300, extra={"showlegend": False})
        st.plotly_chart(fig10, use_container_width=True)
    else:
        st.info("No sort data for selected period.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_r4:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">8. Aging Distribution</div>', unsafe_allow_html=True)
    st.markdown('<div class="aging-badge">ISD &amp; SUB = 4 Days+ &nbsp;|&nbsp; OSD = 5 Days+</div>', unsafe_allow_html=True)
    AGE_COLS = [str(i) for i in range(1, 11)] + ["10+"]

    if not ag_f.empty and "Region" in ag_f.columns:
        ag_max   = ag_f["Date"].max()
        ag_day_f = ag_f[ag_f["Date"] == ag_max].copy()

        rows8 = []
        for _, row in ag_day_f.iterrows():
            region = str(row.get("Region", "")).strip()
            if region not in region_filter: continue
            total = float(row.get("Total", 0) or 0)
            if total == 0:
                total = sum(float(row[c]) for c in AGE_COLS if c in ag_day_f.columns and pd.notna(row[c]))
            for c in AGE_COLS:
                if c in ag_day_f.columns:
                    val = float(row[c]) if pd.notna(row[c]) else 0.0
                    pct = val / total * 100 if total > 0 else 0.0
                    rows8.append({"Region": region, "Age": f"{c}d", "Count": val, "Pct": pct})

        ag_melt = pd.DataFrame(rows8)
        if not ag_melt.empty:
            fig8 = px.bar(ag_melt, x="Age", y="Pct", color="Region",
                          color_discrete_map={"ISD": C_ISD, "OSD": C_OSD}, barmode="group",
                          text=ag_melt["Pct"].apply(lambda x: f"{x:.1f}%"))
            fig8.update_traces(
                textposition="outside", textfont=dict(color="#1C2B3A", size=10), customdata=ag_melt[["Count", "Region"]],
                hovertemplate="<b>%{x}</b><br>Region: %{customdata[1]}<br>Count: %{customdata[0]:,.0f}<br>Pct: %{y:.1f}%",
            )
            _layout(fig8, height=300, extra={"yaxis": dict(**_AX, title="Percentage (%)")})
            st.plotly_chart(fig8, use_container_width=True)

            st.markdown("<div style='color: #1C2B3A; font-weight: 700; font-size: 14px; margin-bottom: 12px; margin-top: 8px;'>Aging Count &amp; % by Region</div>", unsafe_allow_html=True)
            isd_row   = ag_day_f[ag_day_f["Region"] == "ISD"].iloc[0] if "ISD" in ag_day_f["Region"].values else None
            osd_row   = ag_day_f[ag_day_f["Region"] == "OSD"].iloc[0] if "OSD" in ag_day_f["Region"].values else None
            isd_tot_v = float(isd_row["Total"]) if isd_row is not None else 0
            osd_tot_v = float(osd_row["Total"]) if osd_row is not None else 0

            th = "<th>Days</th>"
            if isd_row is not None: th += "<th>ISD Count</th><th>ISD %</th>"
            if osd_row is not None: th += "<th>OSD Count</th><th>OSD %</th>"
            body_rows = ""
            for c in AGE_COLS:
                if c not in ag_day_f.columns: continue
                td = f"<td><b>{c}d</b></td>"
                if isd_row is not None:
                    v = float(isd_row[c]) if pd.notna(isd_row[c]) else 0
                    td += f"<td>{v:,.0f}</td><td>{v/isd_tot_v*100:.1f}%</td>"
                if osd_row is not None:
                    v = float(osd_row[c]) if pd.notna(osd_row[c]) else 0
                    td += f"<td>{v:,.0f}</td><td>{v/osd_tot_v*100:.1f}%</td>"
                body_rows += f"<tr>{td}</tr>"

            td_tot = "<td><b>Total</b></td>"
            if isd_row is not None: td_tot += f"<td><b>{isd_tot_v:,.0f}</b></td><td><b>100%</b></td>"
            if osd_row is not None: td_tot += f"<td><b>{osd_tot_v:,.0f}</b></td><td><b>100%</b></td>"
            body_rows += f"<tr>{td_tot}</tr>"

            st.markdown(f"""
            <div style="overflow-x:auto; max-height:260px; overflow-y:auto; border-radius:8px; border:1px solid #E2E8F0;">
            <table class="styled-table" style="margin:0;">
              <thead><tr>{th}</tr></thead>
              <tbody>{body_rows}</tbody>
            </table></div>""", unsafe_allow_html=True)
        else:
            st.info("No aging data for selected regions/period.")
    else:
        st.info("No aging distribution data available.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── ROW 5: Full FID Tracking Table ────────────────────────────────────────────
st.markdown('<div class="chart-card">', unsafe_allow_html=True)
st.markdown('<div class="sec-hdr">11. Date-wise Backlog Progress Tracking — Full Table (FID)</div>', unsafe_allow_html=True)
if not ft_f.empty:
    tbl = ft_f.sort_values("Date").copy()
    COL_MAP = {
        "Date_Label":                  "Date",
        "Newly Added":                 "Newly Added",
        "Total In Progress (Backlog)": "Total In Process (Backlog)",
        "Worked On":                   "Worked On",
        "Carry Forward":               "Carry Forward",
    }
    show_cols = [c for c in COL_MAP if c in tbl.columns]
    df_tbl    = tbl[show_cols].rename(columns=COL_MAP)

    headers = "".join(f"<th>{c}</th>" for c in df_tbl.columns)
    body    = ""
    for i, (_, r) in enumerate(df_tbl.iterrows()):
        is_last = i == len(df_tbl) - 1
        cells   = ""
        for j, v in enumerate(r):
            cls = "col-date" if j == 0 else ("col-high" if is_last else "")
            try: disp = v if j == 0 else (f"{int(float(v)):,}" if float(v) != 0 else "—")
            except Exception: disp = "—"
            cells += f"<td class='{cls}'>{disp}</td>"
        body += f"<tr>{cells}</tr>"

    st.markdown(f"""
    <div style="overflow-x:auto; border-radius:8px; border:1px solid #E2E8F0;">
    <table class="styled-table" style="margin:0;">
      <thead><tr>{headers}</tr></thead>
      <tbody>{body}</tbody>
    </table></div>""", unsafe_allow_html=True)
else:
    st.info("No FID tracking data to display.")
st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;color:#6B7E91;font-size:12px;padding:20px 0 10px;font-weight:500;">
  🐝 Carrybee Delivery Intelligence &nbsp;·&nbsp;
  Data refreshes every 10 min &nbsp;·&nbsp; Powered by Google Sheets
</div>
""", unsafe_allow_html=True)
