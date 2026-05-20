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
    color: #fff; position: relative; overflow: hidden; min-height: 115px;
}
.kpi-card::after {
    content:''; position:absolute; top:-20px; right:-20px;
    width:90px; height:90px; border-radius:50%; background:rgba(255,255,255,0.12);
}
.bg-blue   { background: linear-gradient(135deg,#1d4ed8,#3b82f6); }
.bg-red    { background: linear-gradient(135deg,#b91c1c,#ef4444); }
.bg-amber  { background: linear-gradient(135deg,#b45309,#f59e0b); }
.bg-green  { background: linear-gradient(135deg,#065f46,#10b981); }
.bg-purple { background: linear-gradient(135deg,#5b21b6,#8b5cf6); }

.kpi-label { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.7px;
             opacity:0.9; margin-bottom:6px; color:#ffffff !important; }
.kpi-value { font-size:30px; font-weight:800; line-height:1.1; margin-bottom:6px; color:#ffffff !important; }
.kpi-delta { font-size:11px; background:rgba(255,255,255,0.22); padding:2px 8px;
             border-radius:20px; display:inline-block; }
.kpi-delta.up   { color:#bbf7d0; }
.kpi-delta.down { color:#fecaca; }

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
                          border-bottom:1px solid #e2e8f0; color:#1e293b; }
.styled-table .col-date { text-align:left; font-weight:600; color:#1e3a5f; }
.styled-table .col-high { color:#dc2626; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ── Google Sheet URL ──────────────────────────────────────────────────────────
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1n9GW1UksZ-jhCQ-zmCqwx4EH20fa-Zm5wA5BiMmdZAE/edit?gid=713116247#gid=713116247"

# ── Plot helpers ──────────────────────────────────────────────────────────────
AXIS_STYLE = dict(gridcolor="#e2e8f0", linecolor="#cbd5e1", tickcolor="#94a3b8", showgrid=True)
BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#334155", family="Inter, sans-serif", size=11),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#e2e8f0", borderwidth=1, font_size=11),
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

C_ISD = "#2563eb"
C_OSD = "#ef4444"
C_SUB = "#10b981"

# ── Data Loading ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)

    def fix_year(series):
        """If year parsed as < 2000 (no year in string), replace with current year."""
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

    # ── 1. Dashboard_Card — has 2-row header; real header is row index 1 ──────
    try:
        raw_dc = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Dashboard_Card", header=False)
        # Row 0 = title string, Row 1 = actual column names
        raw_dc.columns = [str(c).strip() for c in raw_dc.iloc[1]]
        raw_dc = raw_dc.iloc[2:].reset_index(drop=True)
        raw_dc = raw_dc[~raw_dc["Date"].astype(str).str.contains("Grand Total|Date|nan", case=False, na=True)]
        raw_dc["Date"] = clean_dates(raw_dc["Date"])
        raw_dc = raw_dc.dropna(subset=["Date"])
        for c in ["ISD", "OSD", "Total", "FID Backlog (%)", "Zone Transfer", "Zone Transfer (%)"]:
            if c in raw_dc.columns:
                raw_dc[c] = pd.to_numeric(
                    raw_dc[c].astype(str).str.replace(",", "").str.replace("%", ""),
                    errors="coerce"
                ).fillna(0)
        raw_dc["Date_Label"] = raw_dc["Date"].dt.strftime("%d %b")
        dc = raw_dc
    except Exception as e:
        st.warning(f"Dashboard_Card load error: {e}")
        dc = pd.DataFrame()

    # ── 2. FID_Tracking — clean standard sheet ────────────────────────────────
    try:
        raw_ft = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="FID_Tracking")
        raw_ft.columns = [str(c).strip() for c in raw_ft.columns]
        raw_ft = raw_ft[~raw_ft.iloc[:, 0].astype(str).str.contains("Grand Total|Report Date|nan", case=False, na=True)]
        raw_ft.rename(columns={raw_ft.columns[0]: "Date"}, inplace=True)
        raw_ft["Date"] = clean_dates(raw_ft["Date"])
        raw_ft = raw_ft.dropna(subset=["Date"])
        for c in raw_ft.columns[1:]:
            raw_ft[c] = pd.to_numeric(
                raw_ft[c].astype(str).str.replace(",", "").str.replace("%", ""),
                errors="coerce"
            ).fillna(0)
        raw_ft["Date_Label"] = raw_ft["Date"].dt.strftime("%d %b")
        ft = raw_ft
    except Exception as e:
        st.warning(f"FID_Tracking load error: {e}")
        ft = pd.DataFrame()

    # ── 3. FID_RID_Backlog_Details — single sheet with all breakdown data ──────
    try:
        raw_fr = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="FID_RID_Backlog_Details")
        raw_fr.columns = [str(c).strip() for c in raw_fr.columns]
        raw_fr = raw_fr[~raw_fr.iloc[:, 0].astype(str).str.contains("Grand Total|Date|nan", case=False, na=True)]
        raw_fr.rename(columns={raw_fr.columns[0]: "Date"}, inplace=True)
        raw_fr["Date"] = clean_dates(raw_fr["Date"])
        raw_fr = raw_fr.dropna(subset=["Date"])
        for c in raw_fr.columns[1:]:
            raw_fr[c] = pd.to_numeric(
                raw_fr[c].astype(str).str.replace(",", "").str.replace("%", ""),
                errors="coerce"
            ).fillna(0)
        raw_fr["Date_Label"] = raw_fr["Date"].dt.strftime("%d %b")
        fr = raw_fr
    except Exception as e:
        st.warning(f"FID_RID_Backlog_Details load error: {e}")
        fr = pd.DataFrame()

    # ── 4. Aging_Distribution ────────────────────────────────────────────────
    try:
        raw_ag = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Aging_Distribution")
        raw_ag.columns = [str(c).strip() for c in raw_ag.columns]
        raw_ag = raw_ag[~raw_ag.iloc[:, 0].astype(str).str.contains("Grand Total|Report Date|nan", case=False, na=True)]
        raw_ag.rename(columns={raw_ag.columns[0]: "Date"}, inplace=True)
        raw_ag["Date"] = clean_dates(raw_ag["Date"])
        raw_ag = raw_ag.dropna(subset=["Date"])
        # Parse numeric age columns (1-10, 10+, Total)
        age_cols = [str(i) for i in range(1, 11)] + ["10+", "Total"]
        for c in age_cols:
            if c in raw_ag.columns:
                raw_ag[c] = pd.to_numeric(
                    raw_ag[c].astype(str).str.replace(",", ""),
                    errors="coerce"
                ).fillna(0)
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

# Use FID_Tracking dates as reference for the date filter
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


# ── Filter helper (works for any date column named "Date") ────────────────────
def filt(df, region_col=None):
    if df is None or df.empty:
        return pd.DataFrame()
    m = (df["Date"] >= sel_start) & (df["Date"] <= sel_end)
    out = df[m].copy()
    if region_col and region_filter and region_col in out.columns:
        out = out[out[region_col].isin(region_filter)]
    return out


ft_f  = filt(ft)
dc_f  = filt(dc)
fr_f  = filt(fr)
ag_f  = filt(ag, "Region")

# Latest rows from each sheet
def latest(df):
    return df.sort_values("Date").iloc[-1] if not df.empty else None

lt_ft = latest(ft_f)   # FID Tracking latest
lt_dc = latest(dc_f)   # Dashboard Card latest
lt_fr = latest(fr_f)   # FID_RID_Backlog_Details latest


# ── KPI values ────────────────────────────────────────────────────────────────
# 1. Total In-Process FID  → Dashboard_Card "Total"
tot_fid    = float(lt_dc["Total"])            if lt_dc is not None and "Total"            in lt_dc.index else 0.0

# 2. Overall Backlog       → FID Backlog + RID Backlog from FID_RID_Backlog_Details
fid_bl     = float(lt_fr["FID Backlog"])      if lt_fr is not None and "FID Backlog"      in lt_fr.index else 0.0
rid_bl     = float(lt_fr["RID Backlog"])      if lt_fr is not None and "RID Backlog"      in lt_fr.index else 0.0
overall_bl = fid_bl + rid_bl

# 3. Zone Transfer Parcels → Dashboard_Card "Zone Transfer"
zt_val     = float(lt_dc["Zone Transfer"])    if lt_dc is not None and "Zone Transfer"    in lt_dc.index else 0.0

# 4. FID Backlog %         → Dashboard_Card "FID Backlog (%)" (stored as 0.075 = 7.5%)
fid_pct_r  = float(lt_dc["FID Backlog (%)"])  if lt_dc is not None and "FID Backlog (%)" in lt_dc.index else 0.0
fid_pct_s  = f"{fid_pct_r*100:.2f}%" if fid_pct_r <= 1 else f"{fid_pct_r:.2f}%"

# 5. Zone Change %         → Dashboard_Card "Zone Transfer (%)"
zt_pct_r   = float(lt_dc["Zone Transfer (%)"])if lt_dc is not None and "Zone Transfer (%)" in lt_dc.index else 0.0
zt_pct_s   = f"{zt_pct_r*100:.2f}%" if zt_pct_r <= 1 else f"{zt_pct_r:.2f}%"

# Delta helpers
def prev_num(df, col, fallback=0.0):
    ds = df.sort_values("Date") if df is not None and not df.empty else None
    if ds is not None and len(ds) >= 2 and col in ds.columns:
        return float(ds.iloc[-2][col])
    return float(fallback)

d_fid   = tot_fid   - prev_num(dc_f,  "Total")
d_bl    = overall_bl - (prev_num(fr_f, "FID Backlog") + prev_num(fr_f, "RID Backlog"))
d_fpct  = fid_pct_r - prev_num(dc_f,  "FID Backlog (%)")


# ── ROW 1: 5 KPI Cards ────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
kpis = [
    (c1, "1. Total In-Process (FID)", "bg-blue",   f"{tot_fid:,.0f}",    d_fid,  "vs prev"),
    (c2, "2. Overall Backlog",        "bg-red",    f"{overall_bl:,.0f}", d_bl,   "FID+RID"),
    (c3, "3. Zone Transfer Parcels",  "bg-amber",  f"{zt_val:,.0f}",     None,   ""),
    (c4, "4. FID Backlog %",          "bg-green",  fid_pct_s,            d_fpct*100, "pp vs prev"),
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

# ── ROW 2: Chart 11 (Date-wise FID combo) + Chart 6 (Region donut) ───────────
col_c11, col_c6 = st.columns([3, 2])

with col_c11:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">11. Date-wise Backlog Progress Tracking (FID)</div>', unsafe_allow_html=True)
    if not ft_f.empty:
        # Column name mapping (exact from sheet)
        add_col = "Newly Added"
        prg_col = "Total In Progress (Backlog)"
        wrk_col = "Worked On"
        cf_col  = "Carry Forward"

        fig11 = go.Figure()
        if prg_col in ft_f.columns:
            fig11.add_trace(go.Bar(x=ft_f["Date_Label"], y=ft_f[prg_col],
                                   name="Total In Process", marker_color="#2563eb"))
        if add_col in ft_f.columns:
            fig11.add_trace(go.Bar(x=ft_f["Date_Label"], y=ft_f[add_col],
                                   name="Newly Added", marker_color="#f59e0b"))
        if cf_col in ft_f.columns:
            fig11.add_trace(go.Bar(x=ft_f["Date_Label"], y=ft_f[cf_col],
                                   name="Carry Forward", marker_color="#8b5cf6"))
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
        isd_v = float(lt_dc["ISD"]) if "ISD" in lt_dc.index else 0.0
        osd_v = float(lt_dc["OSD"]) if "OSD" in lt_dc.index else 0.0
        if isd_v + osd_v > 0:
            fig6 = go.Figure(data=[go.Pie(
                labels=["ISD", "OSD"], values=[isd_v, osd_v],
                hole=0.55, marker_colors=[C_ISD, C_OSD],
                textinfo="label+percent", textfont_size=13, pull=[0.04, 0]
            )])
            apply_layout(fig6, height=260,
                         extra={"legend": dict(orientation="h", yanchor="bottom",
                                               y=-0.15, xanchor="center", x=0.5)})
            fig6.add_annotation(
                text=f"<b>{isd_v+osd_v:,.0f}</b><br><span style='font-size:10px'>Total</span>",
                x=0.5, y=0.5, showarrow=False, font=dict(size=15, color="#1e3a5f"), xanchor="center"
            )
            st.plotly_chart(fig6, use_container_width=True)

        # Horizontal bar
        df_reg = pd.DataFrame({"Region": ["ISD", "OSD"], "Parcels": [isd_v, osd_v]})
        fig6b = px.bar(df_reg, x="Parcels", y="Region", orientation="h",
                       color="Region", color_discrete_map={"ISD": C_ISD, "OSD": C_OSD},
                       text="Parcels")
        fig6b.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        apply_layout(fig6b, height=130,
                     extra={"showlegend": False, "margin": dict(l=10, r=70, t=5, b=5)})
        st.plotly_chart(fig6b, use_container_width=True)
    else:
        st.info("Dashboard_Card data unavailable for selected date range.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── ROW 3: Chart 7 (FID vs RID backlog) + Chart 9 (Backlog Details LMH/FMH) ──
col_c7, col_c9 = st.columns([2, 3])

with col_c7:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">7. Backlog — FID vs RID</div>', unsafe_allow_html=True)
    if lt_fr is not None and fid_bl + rid_bl > 0:
        fig7 = go.Figure(data=[go.Bar(
            x=["FID Backlog", "RID Backlog"],
            y=[fid_bl, rid_bl],
            marker_color=[C_ISD, C_OSD],
            text=[f"{fid_bl:,.0f}", f"{rid_bl:,.0f}"],
            textposition="outside",
            textfont=dict(size=13, color="#1e3a5f"),
            width=0.5
        )])
        apply_layout(fig7, height=300, extra={"showlegend": False})
        st.plotly_chart(fig7, use_container_width=True)
    else:
        st.info("No FID/RID backlog data for selected period.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_c9:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">9. Backlog Details — FID &amp; RID (LMH / FMH / SUB)</div>', unsafe_allow_html=True)
    # Data lives in FID_RID_Backlog_Details with flat columns:
    # FID LMH ISD, FID LMH SUB, FID LMH OSD, FID FMH
    # RID LMH ISD, RID LMH SUB, RID LMH OSD, RID FMH ISD, RID FMH SUB, RID FMH OSD
    if lt_fr is not None:
        def safe(row, col):
            return float(row[col]) if col in row.index else 0.0

        # Build the 4 horizontal bar groups matching the report screenshot
        detail_rows = [
            # Label, ISD, SUB, OSD, Total
            ("FID LMH",
             safe(lt_fr, "FID LMH ISD"), safe(lt_fr, "FID LMH SUB"), safe(lt_fr, "FID LMH OSD"),
             safe(lt_fr, "FID LMH Total")),
            ("FID FMH",
             0, 0, 0,
             safe(lt_fr, "FID FMH")),
            ("RID FMH",
             safe(lt_fr, "RID FMH ISD"), safe(lt_fr, "RID FMH SUB"), safe(lt_fr, "RID FMH OSD"),
             safe(lt_fr, "RID FMH ISD") + safe(lt_fr, "RID FMH SUB") + safe(lt_fr, "RID FMH OSD")),
            ("RID LMH",
             safe(lt_fr, "RID LMH ISD"), safe(lt_fr, "RID LMH SUB"), safe(lt_fr, "RID LMH OSD"),
             safe(lt_fr, "RID LMH ISD") + safe(lt_fr, "RID LMH SUB") + safe(lt_fr, "RID LMH OSD")),
        ]

        fig9 = go.Figure()
        # Stacked horizontal bars: ISD (navy) | SUB (green) | OSD (red)
        labels    = [r[0] for r in detail_rows]
        isd_vals  = [r[1] for r in detail_rows]
        sub_vals  = [r[2] for r in detail_rows]
        osd_vals  = [r[3] for r in detail_rows]
        totals    = [r[4] for r in detail_rows]

        fig9.add_trace(go.Bar(name="ISD", y=labels, x=isd_vals, orientation="h",
                              marker_color=C_ISD,
                              text=[f"{v:,.0f}" if v > 0 else "" for v in isd_vals],
                              textposition="inside", insidetextanchor="middle"))
        fig9.add_trace(go.Bar(name="SUB", y=labels, x=sub_vals, orientation="h",
                              marker_color=C_SUB,
                              text=[f"{v:,.0f}" if v > 0 else "" for v in sub_vals],
                              textposition="inside", insidetextanchor="middle"))
        fig9.add_trace(go.Bar(name="OSD", y=labels, x=osd_vals, orientation="h",
                              marker_color=C_OSD,
                              text=[f"{v:,.0f}" if v > 0 else "" for v in osd_vals],
                              textposition="inside", insidetextanchor="middle"))
        # Totals as annotations at end of bars
        for i, (lbl, tot) in enumerate(zip(labels, totals)):
            fig9.add_annotation(x=tot, y=lbl, text=f"  <b>{tot:,.0f}</b>",
                                showarrow=False, xanchor="left",
                                font=dict(size=12, color="#1e3a5f"))

        apply_layout(fig9, height=320,
                     extra={"barmode": "stack", "showlegend": True,
                             "xaxis": dict(**AXIS_STYLE, title="Count"),
                             "yaxis": dict(**AXIS_STYLE, autorange="reversed")})
        st.plotly_chart(fig9, use_container_width=True)
    else:
        st.info("No backlog detail data for selected period.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── ROW 4: Chart 10 (Sort) + Chart 8 (Aging Distribution) ───────────────────
col_c10, col_c8 = st.columns(2)

with col_c10:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">10. Sort — FID Sort vs RID Sort</div>', unsafe_allow_html=True)
    # Sort data is in FID_RID_Backlog_Details: "FID Sort" and "RID LMH Sort"
    if lt_fr is not None:
        def safe(row, col):
            return float(row[col]) if col in row.index else 0.0
        fid_sort = safe(lt_fr, "FID Sort")
        rid_sort = safe(lt_fr, "RID LMH Sort")

        fig10 = go.Figure(data=[go.Bar(
            x=["FID Sort", "RID Sort"],
            y=[fid_sort, rid_sort],
            marker_color=[C_ISD, C_OSD],
            text=[f"{fid_sort:,.0f}", f"{rid_sort:,.0f}"],
            textposition="outside",
            textfont=dict(size=13, color="#1e3a5f"),
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
    st.markdown('<div class="aging-badge">ISD &amp; SUB = 4 Days+ &nbsp;|&nbsp; OSD = 5 Days+</div>', unsafe_allow_html=True)
    if not ag_f.empty and "Region" in ag_f.columns:
        ag_latest = ag_f[ag_f["Date"] == ag_f["Date"].max()]
        AGE_COLS = [str(i) for i in range(1, 11)] + ["10+"]
        rows8 = []
        for _, row in ag_latest.iterrows():
            region = str(row.get("Region", "")).strip()
            if region not in region_filter:
                continue
            total = sum(float(row[c]) for c in AGE_COLS if c in ag_latest.columns and pd.notna(row[c]))
            for c in AGE_COLS:
                if c in ag_latest.columns:
                    val = float(row[c])
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

# ── ROW 5: Full Table (Date-wise FID Tracking) ────────────────────────────────
st.markdown('<div class="chart-card">', unsafe_allow_html=True)
st.markdown('<div class="sec-hdr">11. Date-wise Backlog Progress Tracking — Full Table (FID)</div>', unsafe_allow_html=True)

if not ft_f.empty:
    tbl = ft_f.sort_values("Date").copy()
    COL_MAP = {
        "Date_Label":                    "Date",
        "Newly Added":                   "Newly Added",
        "Total In Progress (Backlog)":   "Total In Process (Backlog)",
        "Worked On":                     "Worked On",
        "Carry Forward":                 "Carry Forward",
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
<div style="text-align:center;color:#94a3b8;font-size:11px;padding:16px 0 6px 0;">
  🐝 Carrybee Delivery Intelligence &nbsp;·&nbsp; Data refreshes every 10 min &nbsp;·&nbsp; Powered by Google Sheets
</div>
""", unsafe_allow_html=True)
