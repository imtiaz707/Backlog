import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from streamlit_gsheets import GSheetsConnection

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Courier Logistics Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme / CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ---- global ---- */
[data-testid="stAppViewContainer"] { background: #0d1117; }
[data-testid="stSidebar"]          { background: #161b22; border-right: 1px solid #30363d; }
[data-testid="stHeader"]           { background: transparent; }

/* ---- metric cards ---- */
.kpi-card {
    background: linear-gradient(135deg, #1c2333 0%, #21262d 100%);
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    box-shadow: 0 4px 16px rgba(0,0,0,.4);
}
.kpi-label  { font-size: 12px; color: #8b949e; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px; }
.kpi-value  { font-size: 36px; font-weight: 700; color: #e6edf3; line-height: 1; }
.kpi-delta  { font-size: 13px; margin-top: 6px; }
.kpi-delta.up   { color: #3fb950; }
.kpi-delta.down { color: #f85149; }
.kpi-delta.neutral { color: #8b949e; }

/* ---- section headers ---- */
.section-header {
    font-size: 15px; font-weight: 600; color: #e6edf3;
    letter-spacing: .5px; margin: 20px 0 8px 0;
    border-left: 3px solid #388bfd; padding-left: 10px;
}

/* ---- sidebar ---- */
.sidebar-title {
    font-size: 20px; font-weight: 700; color: #e6edf3; margin-bottom: 4px;
}
.sidebar-sub { font-size: 12px; color: #8b949e; }

/* ---- divider ---- */
hr { border-color: #30363d !important; }
</style>
""", unsafe_allow_html=True)

# Replace this with the actual URL of your restricted Google Sheet
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1n9GW1UksZ-jhCQ-zmCqwx4EH20fa-Zm5wA5BiMmdZAE/edit?gid=713116247#gid=713116247"

PLOT_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#161b22",
    font=dict(color="#c9d1d9", family="Inter, sans-serif", size=12),
    xaxis=dict(gridcolor="#21262d", linecolor="#30363d", tickcolor="#30363d"),
    yaxis=dict(gridcolor="#21262d", linecolor="#30363d", tickcolor="#30363d"),
    legend=dict(bgcolor="#1c2333", bordercolor="#30363d", borderwidth=1),
    hoverlabel=dict(bgcolor="#1c2333", bordercolor="#388bfd", font_color="#e6edf3"),
    margin=dict(l=20, r=20, t=45, b=20),
)

COLOR_ISD   = "#388bfd"
COLOR_OSD   = "#3fb950"
COLOR_ADDED = "#f0883e"
COLOR_PROG  = "#ff7b72"
COLOR_WRK   = "#58a6ff"
COLOR_CF    = "#8b949e"

# ── Data loading (Connected to GSheets) ───────────────────────────────────────
# ttl=600 tells Streamlit to re-fetch the data from Google every 10 minutes
@st.cache_data(show_spinner=False, ttl=600)
def load_data():
    # Establish secure connection
    conn = st.connection("gsheets", type=GSheetsConnection)

    # Read each specific worksheet from the Google Sheet
    dc_raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Dashboard_Card")
    ft_raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="FID_Tracking")
    ag_raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Aging_Distribution")

    # ── Dashboard_Card ───────────────────────────────────────────────────────
    dc = dc_raw.copy()
    dc.columns = dc.iloc[0]
    dc = dc.iloc[1:].reset_index(drop=True)
    dc.rename(columns={
        "Date": "Date",
        "ISD": "ISD",
        "OSD": "OSD",
        "Total": "Total",
        "FID Backlog (%)": "FID_Backlog_Pct",
        "Zone Transfer": "Zone_Transfer",
        "Zone Transfer (%)": "Zone_Transfer_Pct",
    }, inplace=True)
    dc = dc[["Date", "ISD", "OSD", "Total", "FID_Backlog_Pct", "Zone_Transfer"]].dropna(subset=["Date"])
    dc["Date"] = pd.to_datetime(dc["Date"])
    for col in ["ISD", "OSD", "Total", "FID_Backlog_Pct", "Zone_Transfer"]:
        dc[col] = pd.to_numeric(dc[col], errors="coerce")
    dc["Date_Label"] = dc["Date"].dt.strftime("%b %d")

    # ── FID_Tracking ─────────────────────────────────────────────────────────
    ft = ft_raw.copy()
    ft["Report Date"] = pd.to_datetime(ft["Report Date"])
    ft.rename(columns={
        "Report Date": "Report_Date",
        "Newly Added": "Newly_Added",
        "Total In Progress (Backlog)": "Total_In_Progress",
        "Worked On": "Worked_On",
        "Carry Forward": "Carry_Forward",
    }, inplace=True)
    ft["Date_Label"] = ft["Report_Date"].dt.strftime("%b %d")

    # ── Aging_Distribution ───────────────────────────────────────────────────
    ag = ag_raw.copy()
    ag["Report Date"] = pd.to_datetime(ag["Report Date"])
    age_cols = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, "10+"]
    keep_cols = ["Report Date", "Region"] + age_cols + ["Total"]
    ag = ag[[c for c in keep_cols if c in ag.columns]].copy()
    ag["Region"] = ag["Region"].astype(str).str.strip()
    for c in age_cols + ["Total"]:
        if c in ag.columns:
            ag[c] = pd.to_numeric(ag[c], errors="coerce")
    ag["Date_Label"] = ag["Report Date"].dt.strftime("%b %d")

    return dc, ft, ag


with st.spinner("Loading live data from Google Sheets…"):
    dc, ft, ag = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">📦 Logistics Hub</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Courier Delivery Team Dashboard</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### 🗓 Date Range Filter")
    all_dates = sorted(ft["Report_Date"].dropna().unique())
    date_opts = [pd.Timestamp(d).strftime("%b %d, %Y") for d in all_dates]

    start_idx = st.selectbox("From date", range(len(date_opts)), format_func=lambda i: date_opts[i], index=0)
    end_idx   = st.selectbox("To date",   range(len(date_opts)), format_func=lambda i: date_opts[i], index=len(date_opts)-1)

    if end_idx < start_idx:
        st.warning("End date is before start date.")
        end_idx = start_idx

    sel_start = pd.Timestamp(all_dates[start_idx])
    sel_end   = pd.Timestamp(all_dates[end_idx])

    st.markdown("---")
    st.markdown("### 📊 Chart Options")
    show_worked  = st.toggle("Show Worked On", value=True)
    show_carry   = st.toggle("Show Carry Forward", value=False)
    aging_region = st.multiselect("Aging Regions", ["ISD", "OSD"], default=["ISD", "OSD"])

    st.markdown("---")
    st.caption("Data source: Live Google Sheets DB")

# ── Filter data ───────────────────────────────────────────────────────────────
ft_f = ft[(ft["Report_Date"] >= sel_start) & (ft["Report_Date"] <= sel_end)].copy()
dc_f = dc[(dc["Date"] >= sel_start) & (dc["Date"] <= sel_end)].copy()
ag_f = ag[(ag["Report Date"] >= sel_start) & (ag["Report Date"] <= sel_end)].copy()
ag_f = ag_f[ag_f["Region"].isin(aging_region)] if aging_region else ag_f

# ── Latest row for KPIs ───────────────────────────────────────────────────────
latest_ft = ft_f.sort_values("Report_Date").iloc[-1] if not ft_f.empty else None
latest_dc = dc_f.sort_values("Date").iloc[-1] if not dc_f.empty else None
prev_ft   = ft_f.sort_values("Report_Date").iloc[-2] if len(ft_f) > 1 else None

def delta_html(curr, prev, fmt="{:,.0f}", inverse=False):
    if prev is None or pd.isna(curr) or pd.isna(prev): return ""
    d = curr - prev
    if d == 0: return '<span class="kpi-delta neutral">→ No change</span>'
    cls = ("down" if d > 0 else "up") if inverse else ("up" if d > 0 else "down")
    arrow = "▲" if d > 0 else "▼"
    return f'<span class="kpi-delta {cls}">{arrow} {fmt.format(abs(d))}</span>'

# ── Dashboard title ───────────────────────────────────────────────────────────
col_title, col_date = st.columns([3, 1])
with col_title:
    st.markdown("## 📦 Courier Delivery Operations")
with col_date:
    if latest_ft is not None:
        st.markdown(f"<p style='text-align:right;color:#8b949e;padding-top:12px'>As of <b style='color:#e6edf3'>{latest_ft['Report_Date'].strftime('%d %b %Y')}</b></p>", unsafe_allow_html=True)

# ── KPI Row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

kpi_data = [
    (k1, "Total In Process",
     f"{latest_ft['Total_In_Progress']:,.0f}" if latest_ft is not None else "—",
     delta_html(latest_ft["Total_In_Progress"] if latest_ft is not None else None,
                prev_ft["Total_In_Progress"] if prev_ft is not None else None, inverse=True)),
    (k2, "FID Backlog %",
     f"{latest_dc['FID_Backlog_Pct']*100:.2f}%" if latest_dc is not None and pd.notna(latest_dc["FID_Backlog_Pct"]) else "—",
     delta_html(latest_dc["FID_Backlog_Pct"] if latest_dc is not None else None,
                dc_f.sort_values("Date").iloc[-2]["FID_Backlog_Pct"] if len(dc_f) > 1 else None,
                fmt="{:.2%}", inverse=True)),
    (k3, "Zone Transfers",
     f"{latest_dc['Zone_Transfer']:,.0f}" if latest_dc is not None and pd.notna(latest_dc["Zone_Transfer"]) else "—",
     ""),
    (k4, "Newly Added Today",
     f"{latest_ft['Newly_Added']:,.0f}" if latest_ft is not None else "—",
     delta_html(latest_ft["Newly_Added"] if latest_ft is not None else None,
                prev_ft["Newly_Added"] if prev_ft is not None else None, inverse=True)),
    (k5, "Worked On Today",
     f"{latest_ft['Worked_On']:,.0f}" if latest_ft is not None and pd.notna(latest_ft["Worked_On"]) else "—",
     ""),
]

for col, label, value, delta in kpi_data:
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta}
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 2: Line chart + Backlog % sparkline ───────────────────────────────────
c_line, c_pct = st.columns([3, 2])

with c_line:
    st.markdown('<div class="section-header">FID Tracking — Newly Added vs Total In Progress</div>', unsafe_allow_html=True)

    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=ft_f["Date_Label"], y=ft_f["Total_In_Progress"],
        name="Total In Progress", mode="lines+markers",
        line=dict(color=COLOR_PROG, width=2.5),
        marker=dict(size=7, symbol="circle"),
        fill="tozeroy", fillcolor="rgba(255,123,114,0.08)",
        hovertemplate="<b>Total In Progress</b>: %{y:,}<extra></extra>",
    ))
    fig_line.add_trace(go.Scatter(
        x=ft_f["Date_Label"], y=ft_f["Newly_Added"],
        name="Newly Added", mode="lines+markers",
        line=dict(color=COLOR_ADDED, width=2.5, dash="dot"),
        marker=dict(size=7, symbol="diamond"),
        hovertemplate="<b>Newly Added</b>: %{y:,}<extra></extra>",
    ))
    if show_worked:
        fig_line.add_trace(go.Scatter(
            x=ft_f["Date_Label"], y=ft_f["Worked_On"],
            name="Worked On", mode="lines+markers",
            line=dict(color=COLOR_WRK, width=2),
            marker=dict(size=6),
            hovertemplate="<b>Worked On</b>: %{y:,}<extra></extra>",
        ))
    if show_carry:
        fig_line.add_trace(go.Scatter(
            x=ft_f["Date_Label"], y=ft_f["Carry_Forward"],
            name="Carry Forward", mode="lines+markers",
            line=dict(color=COLOR_CF, width=1.5, dash="dash"),
            marker=dict(size=5),
            hovertemplate="<b>Carry Forward</b>: %{y:,}<extra></extra>",
        ))

    fig_line.update_layout(**PLOT_THEME, height=340)
    fig_line.update_xaxes(title_text="Date")
    fig_line.update_yaxes(title_text="Parcel Count")
    st.plotly_chart(fig_line, use_container_width=True)

with c_pct:
    st.markdown('<div class="section-header">FID Backlog % over Time</div>', unsafe_allow_html=True)

    fig_pct = go.Figure()
    fig_pct.add_trace(go.Scatter(
        x=dc_f["Date_Label"], y=dc_f["FID_Backlog_Pct"] * 100,
        mode="lines+markers",
        line=dict(color="#d2a8ff", width=2.5),
        marker=dict(size=7, color="#d2a8ff"),
        fill="tozeroy", fillcolor="rgba(210,168,255,0.08)",
        hovertemplate="<b>FID Backlog</b>: %{y:.2f}%<extra></extra>",
        name="Backlog %",
    ))
    # threshold line at 10%
    fig_pct.add_hline(y=10, line_dash="dash", line_color="#f85149",
                      annotation_text="10% threshold", annotation_font_color="#f85149")
    fig_pct.update_layout(**PLOT_THEME, height=340, showlegend=False)
    fig_pct.update_xaxes(title_text="Date")
    fig_pct.update_yaxes(title_text="Backlog (%)")
    st.plotly_chart(fig_pct, use_container_width=True)

st.markdown("---")

# ── Row 3: Aging distribution + ISD vs OSD totals ────────────────────────────
c_aging, c_region = st.columns([3, 2])

AGE_COLS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, "10+"]
AGE_LABELS = ["1d", "2d", "3d", "4d", "5d", "6d", "7d", "8d", "9d", "10d", "10+d"]

with c_aging:
    st.markdown('<div class="section-header">Aging Distribution — ISD vs OSD (Most Recent Date)</div>', unsafe_allow_html=True)

    latest_ag_date = ag_f["Report Date"].max()
    ag_latest = ag_f[ag_f["Report Date"] == latest_ag_date].copy()

    rows = []
    for _, row in ag_latest.iterrows():
        for col, lbl in zip(AGE_COLS, AGE_LABELS):
            if col in ag_latest.columns:
                rows.append({"Region": row["Region"], "Age": lbl, "Count": row[col]})
    ag_melt = pd.DataFrame(rows)

    if not ag_melt.empty:
        pal = {"ISD": COLOR_ISD, "OSD": COLOR_OSD}
        fig_age = px.bar(
            ag_melt, x="Age", y="Count", color="Region",
            color_discrete_map=pal,
            barmode="group",
            category_orders={"Age": AGE_LABELS},
            labels={"Count": "Parcel Count", "Age": "Age Bucket"},
        )
        fig_age.update_traces(hovertemplate="<b>%{x}</b><br>Count: %{y:,}<extra></extra>")
        fig_age.update_layout(**PLOT_THEME, height=350)
        st.plotly_chart(fig_age, use_container_width=True)
    else:
        st.info("No aging data for selected filters.")

with c_region:
    st.markdown('<div class="section-header">ISD vs OSD Total In Process — Trend</div>', unsafe_allow_html=True)

    fig_reg = go.Figure()
    fig_reg.add_trace(go.Bar(
        x=dc_f["Date_Label"], y=dc_f["ISD"],
        name="ISD", marker_color=COLOR_ISD,
        hovertemplate="<b>ISD</b>: %{y:,}<extra></extra>",
    ))
    fig_reg.add_trace(go.Bar(
        x=dc_f["Date_Label"], y=dc_f["OSD"],
        name="OSD", marker_color=COLOR_OSD,
        hovertemplate="<b>OSD</b>: %{y:,}<extra></extra>",
    ))
    fig_reg.update_layout(**PLOT_THEME, barmode="stack", height=350)
    fig_reg.update_xaxes(title_text="Date")
    fig_reg.update_yaxes(title_text="Parcel Count")
    st.plotly_chart(fig_reg, use_container_width=True)

st.markdown("---")

# ── Row 4: Stacked aging bar over time + data table ──────────────────────────
st.markdown('<div class="section-header">Aging Distribution Over Time — Stacked (All Selected Days)</div>', unsafe_allow_html=True)

ag_all = ag_f.copy()
rows_all = []
for _, row in ag_all.iterrows():
    for col, lbl in zip(AGE_COLS, AGE_LABELS):
        if col in ag_all.columns:
            rows_all.append({"Date": row["Date_Label"], "Region": row["Region"], "Age": lbl, "Count": row[col]})
ag_all_melt = pd.DataFrame(rows_all)

if not ag_all_melt.empty:
    ag_all_melt["Label"] = ag_all_melt["Date"] + " · " + ag_all_melt["Region"]
    fig_stacked = px.bar(
        ag_all_melt, x="Label", y="Count", color="Age",
        category_orders={"Age": AGE_LABELS},
        labels={"Count": "Parcel Count", "Label": "Date · Region"},
        color_discrete_sequence=px.colors.sequential.Blues_r[::-1] + px.colors.sequential.Oranges_r[::-1],
    )
    fig_stacked.update_traces(hovertemplate="<b>%{x}</b><br>Age: %{data.name}<br>Count: %{y:,}<extra></extra>")
    fig_stacked.update_layout(**PLOT_THEME, height=380, barmode="stack")
    st.plotly_chart(fig_stacked, use_container_width=True)

st.markdown("---")

# ── Data tables (expandable) ──────────────────────────────────────────────────
with st.expander("📋 Raw Data — FID Tracking"):
    disp = ft_f[["Date_Label", "Newly_Added", "Total_In_Progress", "Worked_On", "Carry_Forward"]].copy()
    disp.columns = ["Date", "Newly Added", "Total In Progress", "Worked On", "Carry Forward"]
    st.dataframe(disp.style.format({
        "Newly Added": "{:,.0f}", "Total In Progress": "{:,.0f}",
        "Worked On": "{:,.0f}", "Carry Forward": "{:,.0f}",
    }), use_container_width=True)

with st.expander("📋 Raw Data — Dashboard Card"):
    disp2 = dc_f[["Date_Label", "ISD", "OSD", "Total", "FID_Backlog_Pct", "Zone_Transfer"]].copy()
    disp2.columns = ["Date", "ISD", "OSD", "Total", "FID Backlog %", "Zone Transfer"]
    st.dataframe(disp2.style.format({
        "ISD": "{:,.0f}", "OSD": "{:,.0f}", "Total": "{:,.0f}",
        "FID Backlog %": "{:.2%}", "Zone Transfer": "{:,.0f}",
    }), use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<p style='text-align:center;color:#484f58;font-size:11px;padding-top:8px'>"
    "Courier Logistics Dashboard • Built with Streamlit & Plotly"
    "</p>",
    unsafe_allow_html=True,
)
