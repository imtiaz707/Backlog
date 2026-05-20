import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Carrybee Intelligence",
    page_icon="🐝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }
[data-testid="stAppViewContainer"] { background: #f0f4f8; }
[data-testid="stHeader"]           { background: transparent; }
[data-testid="stToolbar"]          { display: none; }
[data-testid="stDecoration"]       { display: none; }
.block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 100% !important; }

.dash-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
    border-radius: 16px; padding: 18px 28px; margin-bottom: 16px;
}
.dash-title    { color:#fff; font-size:26px; font-weight:800; margin:0; }
.dash-subtitle { color:rgba(255,255,255,0.75); font-size:13px; margin-top:4px; }

.kpi-card {
    border-radius: 14px; padding: 18px 20px 14px; box-shadow: 0 2px 12px rgba(0,0,0,0.10);
    color: #111; position: relative; overflow: hidden; min-height: 115px;
}
.kpi-card::after {
    content:''; position:absolute; top:-20px; right:-20px;
    width:90px; height:90px; border-radius:50%; background:rgba(255,255,255,0.18);
}
.bg-blue   { background: linear-gradient(135deg,#dbeafe,#bfdbfe); border:2px solid #2563eb; }
.bg-red    { background: linear-gradient(135deg,#fee2e2,#fecaca); border:2px solid #ef4444; }
.bg-amber  { background: linear-gradient(135deg,#fef3c7,#fde68a); border:2px solid #f59e0b; }
.bg-green  { background: linear-gradient(135deg,#d1fae5,#a7f3d0); border:2px solid #10b981; }
.bg-purple { background: linear-gradient(135deg,#ede9fe,#ddd6fe); border:2px solid #8b5cf6; }

.kpi-label { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.7px;
             opacity:0.85; margin-bottom:6px; color:#1e3a5f !important; }
.kpi-value { font-size:30px; font-weight:800; line-height:1.1; margin-bottom:6px; color:#111827 !important; }
.kpi-delta { font-size:11px; padding:2px 8px; border-radius:20px; display:inline-block; font-weight:600; }
.kpi-delta.up   { color:#065f46; background:rgba(16,185,129,0.18); }
.kpi-delta.down { color:#991b1b; background:rgba(239,68,68,0.18); }

.sec-hdr {
    font-size:14px; font-weight:700; color:#1e3a5f; text-transform:uppercase;
    letter-spacing:0.6px; border-left:4px solid #2563eb;
    padding-left:10px; margin-bottom:8px; margin-top:4px;
}
.chart-card {
    background:#fff; border-radius:14px; padding:16px 18px 8px;
    box-shadow:0 2px 10px rgba(0,0,0,0.06); margin-bottom:14px;
}
.filter-bar {
    background:#fff; border-radius:12px; padding:12px 18px;
    box-shadow:0 2px 8px rgba(0,0,0,0.06); margin-bottom:14px;
}
.aging-badge {
    background:#fef3c7; border:1px solid #f59e0b; border-radius:8px;
    padding:5px 12px; font-size:11px; color:#92400e; font-weight:700;
    display:inline-block; margin-bottom:8px;
}
/* Table */
.styled-table { width:100%; border-collapse:collapse; font-size:12px; }
.styled-table thead tr  { background:#1e3a5f; }
.styled-table th        { padding:8px 10px; text-align:center; font-weight:700;
                          font-size:11px; color:#ffffff !important; }
.styled-table tbody tr:nth-child(even) { background:#f8fafc; }
.styled-table tbody tr:last-child      { background:#fef9c3; font-weight:700; }
.styled-table td        { padding:7px 10px; text-align:center;
                          border-bottom:1px solid #e2e8f0; color:#111827 !important; }
.styled-table .col-date { text-align:left; font-weight:600; color:#1e3a5f !important; }
.styled-table .col-high { color:#dc2626 !important; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ── Google Sheet URL ──────────────────────────────────────────────────────────
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1n9GW1UksZ-jhCQ-zmCqwx4EH20fa-Zm5wA5BiMmdZAE/edit?gid=713116247#gid=713116247"

# ── Plot helpers ──────────────────────────────────────────────────────────────
AXIS_STYLE = dict(
    gridcolor="#e2e8f0", linecolor="#cbd5e1", tickcolor="#94a3b8",
    showgrid=True, tickfont=dict(color="#111827"), title_font=dict(color="#111827")
)
BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#111827", family="Inter, sans-serif", size=11),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#e2e8f0",
                borderwidth=1, font=dict(size=11, color="#111827")),
    hoverlabel=dict(bgcolor="#1e293b", bordercolor="#3b82f6", font_color="#f1f5f9"),
    margin=dict(l=10, r=10, t=36, b=10),
    xaxis=AXIS_STYLE, yaxis=AXIS_STYLE,
)

def apply_layout(fig, height=None, extra=None):
    layout = dict(**BASE_LAYOUT)
    if height: layout["height"] = height
    if extra:  layout.update(extra)
    fig.update_layout(**layout)
    return fig

C_ISD    = "#1d4ed8"
C_OSD    = "#ef4444"
C_SUB    = "#10b981"
C_AMBER  = "#f59e0b"
C_PURPLE = "#8b5cf6"

# ── Data Loading ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)

    def fix_year(series):
        current_year = pd.Timestamp.now().year
        bad = series.dt.year < 2000
        if bad.any():
            series = series.copy()
            series[bad] = series[bad].apply(
                lambda t: t.replace(year=current_year) if pd.notna(t) else t
            )
        return series

    def clean_dates(col):
        parsed = pd.to_datetime(col.astype(str).str.strip(), dayfirst=True, errors='coerce')
        return fix_year(parsed)

    def num(df, cols):
        for c in cols:
            if c in df.columns:
                df[c] = pd.to_numeric(
                    df[c].astype(str).str.replace(",", "").str.replace("%", ""),
                    errors="coerce"
                ).fillna(0)
        return df

    # ── 1. Dashboard_Card — 2-row header ─────────────────────────────────────
    # Row 0 = merged title, Row 1 = actual column names
    try:
        raw_dc = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Dashboard_Card", header=False)
        raw_dc.columns = [str(c).strip() for c in raw_dc.iloc[1]]
        raw_dc = raw_dc.iloc[2:].reset_index(drop=True)
        raw_dc = raw_dc[~raw_dc["Date"].astype(str).str.contains(
            "Grand Total|Date|nan|Backlog Threshold", case=False, na=True)]
        raw_dc["Date"] = clean_dates(raw_dc["Date"])
        raw_dc = raw_dc.dropna(subset=["Date"])
        raw_dc = num(raw_dc, ["ISD", "OSD", "Total", "FID Backlog (%)", "Zone Transfer", "Zone Transfer (%)"])
        raw_dc["Date_Label"] = raw_dc["Date"].dt.strftime("%d %b")
        dc = raw_dc
    except Exception as e:
        st.warning(f"Dashboard_Card load error: {e}")
        dc = pd.DataFrame()

    # ── 2. FID_Tracking ───────────────────────────────────────────────────────
    try:
        raw_ft = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="FID_Tracking")
        raw_ft.columns = [str(c).strip() for c in raw_ft.columns]
        raw_ft = raw_ft[~raw_ft.iloc[:, 0].astype(str).str.contains(
            "Grand Total|Report Date|nan", case=False, na=True)]
        raw_ft.rename(columns={raw_ft.columns[0]: "Date"}, inplace=True)
        raw_ft["Date"] = clean_dates(raw_ft["Date"])
        raw_ft = raw_ft.dropna(subset=["Date"])
        raw_ft = num(raw_ft, list(raw_ft.columns[1:]))
        raw_ft["Date_Label"] = raw_ft["Date"].dt.strftime("%d %b")
        ft = raw_ft
    except Exception as e:
        st.warning(f"FID_Tracking load error: {e}")
        ft = pd.DataFrame()

    # ── 3. FID_RID_Backlog_Details ────────────────────────────────────────────
    try:
        raw_fr = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="FID_RID_Backlog_Details")
        raw_fr.columns = [str(c).strip() for c in raw_fr.columns]
        raw_fr = raw_fr[~raw_fr.iloc[:, 0].astype(str).str.contains(
            "Grand Total|Date|nan", case=False, na=True)]
        raw_fr.rename(columns={raw_fr.columns[0]: "Date"}, inplace=True)
        raw_fr["Date"] = clean_dates(raw_fr["Date"])
        raw_fr = raw_fr.dropna(subset=["Date"])
        raw_fr = num(raw_fr, list(raw_fr.columns[1:]))
        raw_fr["Date_Label"] = raw_fr["Date"].dt.strftime("%d %b")
        fr = raw_fr
    except Exception as e:
        st.warning(f"FID_RID_Backlog_Details load error: {e}")
        fr = pd.DataFrame()

    # ── 4. Aging_Distribution ─────────────────────────────────────────────────
    # Columns: Report Date, Region, 1,2,...,10,10+,Total  (then blank % cols)
    try:
        raw_ag = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Aging_Distribution")
        # Keep only the first 14 columns (Report Date, Region, 1-10, 10+, Total)
        raw_ag = raw_ag.iloc[:, :14]
        raw_ag.columns = ["Date", "Region"] + [str(i) for i in range(1, 11)] + ["10+", "Total"]
        raw_ag = raw_ag[~raw_ag["Date"].astype(str).str.contains(
            "Grand Total|Report Date|nan", case=False, na=True)]
        raw_ag["Date"] = clean_dates(raw_ag["Date"])
        raw_ag = raw_ag.dropna(subset=["Date"])
        raw_ag["Region"] = raw_ag["Region"].astype(str).str.strip()
        age_cols = [str(i) for i in range(1, 11)] + ["10+", "Total"]
        raw_ag = num(raw_ag, age_cols)
        raw_ag["Date_Label"] = raw_ag["Date"].dt.strftime("%d %b")
        ag = raw_ag
    except Exception as e:
        st.warning(f"Aging_Distribution load error: {e}")
        ag = pd.DataFrame()

    return dc, ft, fr, ag


# ── Load ──────────────────────────────────────────────────────────────────────
with st.spinner("🐝 Loading live data from Google Sheets…"):
    dc, ft, fr, ag = load_data()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dash-header">
  <div>
    <div class="dash-title">🐝 Carrybee Delivery Intelligence</div>
    <div class="dash-subtitle">Live Backlog &amp; Operations Dashboard — Auto-refreshes every 10 minutes</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────────────────────────
st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 2])

all_dates = sorted(ft["Date"].dropna().unique()) if not ft.empty else []
if all_dates:
    date_opts = [pd.Timestamp(d).strftime("%d %b %Y") for d in all_dates]
    with fc1:
        si = st.selectbox("📅 From Date", range(len(date_opts)),
                          format_func=lambda i: date_opts[i], index=0)
    with fc2:
        ei = st.selectbox("📅 To Date", range(len(date_opts)),
                          format_func=lambda i: date_opts[i], index=len(date_opts)-1)
    if ei < si: ei = si
    sel_start = pd.Timestamp(all_dates[si])
    sel_end   = pd.Timestamp(all_dates[ei])
else:
    sel_start = sel_end = pd.Timestamp.now()
    st.error("No dates found — check sheet format.")

with fc3:
    region_filter = st.multiselect("🗺️ Region Filter", ["ISD", "OSD"], default=["ISD", "OSD"])
with fc4:
    show_worked = st.toggle("📈 Show Worked On", value=True)
st.markdown('</div>', unsafe_allow_html=True)


# ── Filter helpers ────────────────────────────────────────────────────────────
def filt(df, region_col=None):
    if df is None or df.empty:
        return pd.DataFrame()
    m = (df["Date"] >= sel_start) & (df["Date"] <= sel_end)
    out = df[m].copy()
    if region_col and region_filter and region_col in out.columns:
        out = out[out[region_col].isin(region_filter)]
    return out

def latest(df):
    return df.sort_values("Date").iloc[-1] if not df.empty else None

def prev_num(df, col, fallback=0.0):
    ds = df.sort_values("Date") if df is not None and not df.empty else None
    if ds is not None and len(ds) >= 2 and col in ds.columns:
        return float(ds.iloc[-2][col])
    return float(fallback)

ft_f = filt(ft)
dc_f = filt(dc)
fr_f = filt(fr)
ag_f = filt(ag, "Region")

# ── For KPIs: use the PREVIOUS day's data (yesterday's report) ─────────────────
# "Previous day" = second-to-last row when all dates sorted;
# but if only 1 date selected or only 1 row, fall back to the latest.
def get_kpi_row(df):
    """Return the last row in the full (unfiltered) dataset up to sel_end."""
    if df is None or df.empty:
        return None
    sub = df[df["Date"] <= sel_end].sort_values("Date")
    if sub.empty:
        return None
    return sub.iloc[-1]

lt_ft = get_kpi_row(ft)
lt_dc = get_kpi_row(dc)
lt_fr = get_kpi_row(fr)

def safe(row, col, default=0.0):
    if row is None:
        return default
    if isinstance(row, pd.Series) and col in row.index:
        v = row[col]
        try:
            return float(v) if pd.notna(v) else default
        except Exception:
            return default
    return default


# ── KPI values ────────────────────────────────────────────────────────────────
# 1. Total In-Process FID  → Dashboard_Card "Total"
tot_fid = safe(lt_dc, "Total")

# 2. Overall Backlog = FID Backlog + RID Backlog from FID_RID_Backlog_Details
fid_bl     = safe(lt_fr, "FID Backlog")
rid_bl     = safe(lt_fr, "RID Backlog")
overall_bl = fid_bl + rid_bl

# 3. Zone Transfer Parcels → Dashboard_Card "Zone Transfer"
zt_val = safe(lt_dc, "Zone Transfer")

# 4. FID Backlog % → Dashboard_Card "FID Backlog (%)" (stored as 0.075 = 7.5%)
fid_pct_r = safe(lt_dc, "FID Backlog (%)")
fid_pct_s = f"{fid_pct_r*100:.2f}%" if fid_pct_r <= 1 else f"{fid_pct_r:.2f}%"

# 5. Zone Change % → Dashboard_Card "Zone Transfer (%)"
zt_pct_r = safe(lt_dc, "Zone Transfer (%)")
zt_pct_s = f"{zt_pct_r*100:.2f}%" if zt_pct_r <= 1 else f"{zt_pct_r:.2f}%"

# Deltas vs previous row
def prev_row(df):
    if df is None or df.empty:
        return None
    sub = df[df["Date"] <= sel_end].sort_values("Date")
    return sub.iloc[-2] if len(sub) >= 2 else None

pr_dc = prev_row(dc)
pr_fr = prev_row(fr)

d_fid  = tot_fid    - safe(pr_dc, "Total")
d_bl   = overall_bl - (safe(pr_fr, "FID Backlog") + safe(pr_fr, "RID Backlog"))
d_fpct_r = fid_pct_r - safe(pr_dc, "FID Backlog (%)")
d_fpct = d_fpct_r * 100  # convert to pp


# ── ROW 1: 5 KPI Cards ────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
kpis = [
    (c1, "1. Total In-Process (FID)", "bg-blue",   f"{tot_fid:,.0f}",    d_fid,  "vs prev"),
    (c2, "2. Overall Backlog",        "bg-red",    f"{overall_bl:,.0f}", d_bl,   "FID+RID"),
    (c3, "3. Zone Transfer Parcels",  "bg-amber",  f"{zt_val:,.0f}",     None,   ""),
    (c4, "4. FID Backlog %",          "bg-green",  fid_pct_s,            d_fpct, "pp vs prev"),
    (c5, "5. Zone Change %",          "bg-purple", zt_pct_s,             None,   ""),
]
for col_w, lbl, bg, val, delta, unit in kpis:
    with col_w:
        dh = ""
        if delta is not None:
            arrow = "▲" if delta >= 0 else "▼"
            cls   = "up" if delta >= 0 else "down"
            dh = f'<div class="kpi-delta {cls}">{arrow} {abs(delta):,.2f} {unit}</div>'
        st.markdown(f"""
        <div class="kpi-card {bg}">
          <div class="kpi-label">{lbl}</div>
          <div class="kpi-value">{val}</div>
          {dh}
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ── ROW 2: Chart 11 (FID tracking combo) + Chart 6 (Region donut) ────────────
col_c11, col_c6 = st.columns([3, 2])

with col_c11:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">11. Date-wise Backlog Progress Tracking (FID)</div>', unsafe_allow_html=True)
    if not ft_f.empty:
        add_col = "Newly Added"
        prg_col = "Total In Progress (Backlog)"
        wrk_col = "Worked On"
        cf_col  = "Carry Forward"

        fig11 = go.Figure()
        if prg_col in ft_f.columns:
            fig11.add_trace(go.Bar(x=ft_f["Date_Label"], y=ft_f[prg_col],
                                   name="Total In Process", marker_color=C_ISD))
        if add_col in ft_f.columns:
            fig11.add_trace(go.Bar(x=ft_f["Date_Label"], y=ft_f[add_col],
                                   name="Newly Added", marker_color=C_AMBER))
        if cf_col in ft_f.columns:
            fig11.add_trace(go.Bar(x=ft_f["Date_Label"], y=ft_f[cf_col],
                                   name="Carry Forward", marker_color=C_PURPLE))
        if show_worked and wrk_col in ft_f.columns:
            fig11.add_trace(go.Scatter(x=ft_f["Date_Label"], y=ft_f[wrk_col],
                                       name="Worked On", mode="lines+markers",
                                       line=dict(color="#10b981", width=3),
                                       marker=dict(size=7, line=dict(color="#fff", width=1.5))))
        apply_layout(fig11, height=330, extra={"barmode": "group"})
        st.plotly_chart(fig11, use_container_width=True)
    else:
        st.info("No FID tracking data for selected period.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_c6:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">6. Region Wise In-Process Parcels</div>', unsafe_allow_html=True)
    if lt_dc is not None:
        isd_v = safe(lt_dc, "ISD")
        osd_v = safe(lt_dc, "OSD")
        if isd_v + osd_v > 0:
            fig6 = go.Figure(data=[go.Pie(
                labels=["ISD", "OSD"], values=[isd_v, osd_v],
                hole=0.55, marker_colors=[C_ISD, C_OSD],
                textinfo="label+percent", textfont=dict(size=13, color="#111827"),
                pull=[0.04, 0]
            )])
            apply_layout(fig6, height=260,
                         extra={"legend": dict(orientation="h", yanchor="bottom",
                                               y=-0.15, xanchor="center", x=0.5,
                                               font=dict(color="#111827"))})
            fig6.add_annotation(
                text=f"<b>{isd_v+osd_v:,.0f}</b><br><span style='font-size:10px'>Total</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=15, color="#111827"), xanchor="center"
            )
            st.plotly_chart(fig6, use_container_width=True)

        df_reg = pd.DataFrame({"Region": ["ISD", "OSD"], "Parcels": [isd_v, osd_v]})
        fig6b = px.bar(df_reg, x="Parcels", y="Region", orientation="h",
                       color="Region", color_discrete_map={"ISD": C_ISD, "OSD": C_OSD},
                       text="Parcels")
        fig6b.update_traces(texttemplate="%{text:,.0f}", textposition="outside",
                            textfont=dict(color="#111827"))
        apply_layout(fig6b, height=130,
                     extra={"showlegend": False, "margin": dict(l=10, r=80, t=5, b=5)})
        st.plotly_chart(fig6b, use_container_width=True)
    else:
        st.info("Dashboard_Card data unavailable for selected date range.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── ROW 3: Chart 7 (FID vs RID) + Chart 9 (Backlog Details LMH/FMH) ──────────
col_c7, col_c9 = st.columns([2, 3])

with col_c7:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">7. Backlog — FID vs RID</div>', unsafe_allow_html=True)
    if lt_fr is not None and (fid_bl + rid_bl) > 0:
        fig7 = go.Figure(data=[go.Bar(
            x=["FID Backlog", "RID Backlog"],
            y=[fid_bl, rid_bl],
            marker_color=[C_ISD, C_OSD],
            text=[f"{fid_bl:,.0f}", f"{rid_bl:,.0f}"],
            textposition="outside",
            textfont=dict(size=13, color="#111827"),
            width=0.5
        )])
        apply_layout(fig7, height=300, extra={"showlegend": False})
        st.plotly_chart(fig7, use_container_width=True)
    else:
        st.info("No FID/RID backlog data for selected period.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_c9:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">9. Backlog Details — FID &amp; RID (LMH / FMH)</div>', unsafe_allow_html=True)
    if lt_fr is not None:
        # FID FMH has no ISD/SUB/OSD split — it's a single number
        fid_fmh_total = safe(lt_fr, "FID FMH")
        detail_rows = [
            # (label, ISD, SUB, OSD, show_total)
            ("FID LMH",
             safe(lt_fr, "FID LMH ISD"), safe(lt_fr, "FID LMH SUB"),
             safe(lt_fr, "FID LMH OSD"), safe(lt_fr, "FID LMH Total")),
            ("FID FMH",
             fid_fmh_total, 0, 0, fid_fmh_total),
            ("RID FMH",
             safe(lt_fr, "RID FMH ISD"), safe(lt_fr, "RID FMH SUB"),
             safe(lt_fr, "RID FMH OSD"),
             safe(lt_fr, "RID FMH ISD") + safe(lt_fr, "RID FMH SUB") + safe(lt_fr, "RID FMH OSD")),
            ("RID LMH",
             safe(lt_fr, "RID LMH ISD"), safe(lt_fr, "RID LMH SUB"),
             safe(lt_fr, "RID LMH OSD"),
             safe(lt_fr, "RID LMH ISD") + safe(lt_fr, "RID LMH SUB") + safe(lt_fr, "RID LMH OSD")),
        ]
        labels   = [r[0] for r in detail_rows]
        isd_vals = [r[1] for r in detail_rows]
        sub_vals = [r[2] for r in detail_rows]
        osd_vals = [r[3] for r in detail_rows]
        totals   = [r[4] for r in detail_rows]

        fig9 = go.Figure()
        fig9.add_trace(go.Bar(name="ISD", y=labels, x=isd_vals, orientation="h",
                              marker_color=C_ISD,
                              text=[f"{v:,.0f}" if v > 0 else "" for v in isd_vals],
                              textposition="inside", insidetextanchor="middle",
                              textfont=dict(color="#ffffff")))
        fig9.add_trace(go.Bar(name="SUB", y=labels, x=sub_vals, orientation="h",
                              marker_color=C_SUB,
                              text=[f"{v:,.0f}" if v > 0 else "" for v in sub_vals],
                              textposition="inside", insidetextanchor="middle",
                              textfont=dict(color="#ffffff")))
        fig9.add_trace(go.Bar(name="OSD", y=labels, x=osd_vals, orientation="h",
                              marker_color=C_OSD,
                              text=[f"{v:,.0f}" if v > 0 else "" for v in osd_vals],
                              textposition="inside", insidetextanchor="middle",
                              textfont=dict(color="#ffffff")))
        for lbl, tot in zip(labels, totals):
            if tot > 0:
                fig9.add_annotation(x=tot, y=lbl, text=f"  <b>{tot:,.0f}</b>",
                                    showarrow=False, xanchor="left",
                                    font=dict(size=12, color="#111827"))

        apply_layout(fig9, height=320,
                     extra={"barmode": "stack", "showlegend": True,
                             "xaxis": dict(**AXIS_STYLE, title="Count"),
                             "yaxis": dict(**AXIS_STYLE, autorange="reversed")})
        st.plotly_chart(fig9, use_container_width=True)
    else:
        st.info("No backlog detail data for selected period.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── ROW 4: Chart 10 (Sort) + Chart 8 (Aging Distribution) ────────────────────
col_c10, col_c8 = st.columns(2)

with col_c10:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">10. Sort — FID Sort vs RID Sort</div>', unsafe_allow_html=True)
    if lt_fr is not None:
        fid_sort = safe(lt_fr, "FID Sort")
        rid_sort = safe(lt_fr, "RID LMH Sort")
        fig10 = go.Figure(data=[go.Bar(
            x=["FID Sort", "RID Sort"],
            y=[fid_sort, rid_sort],
            marker_color=[C_ISD, C_OSD],
            text=[f"{fid_sort:,.0f}", f"{rid_sort:,.0f}"],
            textposition="outside",
            textfont=dict(size=13, color="#111827"),
            width=0.5
        )])
        apply_layout(fig10, height=300, extra={"showlegend": False})
        st.plotly_chart(fig10, use_container_width=True)
    else:
        st.info("No sort data for selected period.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_c8:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">8. Aging Distribution (%)</div>', unsafe_allow_html=True)
    st.markdown('<div class="aging-badge">ISD &amp; SUB = 4 Days+ &nbsp;|&nbsp; OSD = 5 Days+</div>',
                unsafe_allow_html=True)

    if not ag_f.empty and "Region" in ag_f.columns:
        # Use the most recent date's data
        ag_latest = ag_f[ag_f["Date"] == ag_f["Date"].max()].copy()
        AGE_COLS = [str(i) for i in range(1, 11)] + ["10+"]

        rows8 = []
        for _, row in ag_latest.iterrows():
            region = str(row.get("Region", "")).strip()
            if region not in region_filter:
                continue
            total = float(row.get("Total", 0))
            if total == 0:
                total = sum(float(row[c]) for c in AGE_COLS
                            if c in ag_latest.columns and pd.notna(row[c]))
            for c in AGE_COLS:
                if c in ag_latest.columns:
                    val = float(row[c]) if pd.notna(row[c]) else 0
                    pct = (val / total * 100) if total > 0 else 0
                    rows8.append({"Region": region, "Age": f"{c}d", "Count": val, "Pct": pct})

        ag_melt = pd.DataFrame(rows8)
        if not ag_melt.empty:
            fig8 = px.bar(ag_melt, x="Age", y="Pct", color="Region",
                          color_discrete_map={"ISD": C_ISD, "OSD": C_OSD},
                          barmode="group",
                          text=ag_melt["Pct"].apply(lambda x: f"{x:.1f}%"))
            fig8.update_traces(
                textposition="outside",
                textfont=dict(color="#111827", size=9),
                hovertemplate="<b>%{x}</b><br>Region: %{fullData.name}"
                              "<br>Count: %{customdata[0]:,.0f}<br>Pct: %{y:.1f}%",
                customdata=ag_melt[["Count"]]
            )
            apply_layout(fig8, height=300,
                         extra={"yaxis": dict(**AXIS_STYLE, title="Percentage (%)")})
            st.plotly_chart(fig8, use_container_width=True)
        else:
            st.info("No aging data for selected regions/period.")
    else:
        st.info("No aging distribution data available.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── ROW 5: Full Table ─────────────────────────────────────────────────────────
st.markdown('<div class="chart-card">', unsafe_allow_html=True)
st.markdown('<div class="sec-hdr">11. Date-wise Backlog Progress Tracking — Full Table (FID)</div>',
            unsafe_allow_html=True)

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
    df_tbl = tbl[show_cols].rename(columns=COL_MAP)

    headers = "".join(f"<th>{c}</th>" for c in df_tbl.columns)
    body = ""
    for i, (_, r) in enumerate(df_tbl.iterrows()):
        is_last = (i == len(df_tbl) - 1)
        cells = ""
        for j, v in enumerate(r):
            cls = "col-date" if j == 0 else ("col-high" if is_last else "")
            try:
                disp = v if j == 0 else (f"{int(float(v)):,}" if float(v) != 0 else "0")
            except Exception:
                disp = "—"
            cells += f"<td class='{cls}'>{disp}</td>"
        body += f"<tr>{cells}</tr>"

    st.markdown(f"""
    <div style="overflow-x:auto">
    <table class="styled-table">
      <thead><tr>{headers}</tr></thead>
      <tbody>{body}</tbody>
    </table>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("No FID tracking data to display.")

st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;color:#64748b;font-size:11px;padding:16px 0 6px 0;">
  🐝 Carrybee Delivery Intelligence &nbsp;·&nbsp; Data refreshes every 10 min &nbsp;·&nbsp; Powered by Google Sheets
</div>
""", unsafe_allow_html=True)
