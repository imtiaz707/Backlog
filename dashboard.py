import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Carrybee Intelligence",
    page_icon="🐝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Theme / CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ---- global ---- */
[data-testid="stAppViewContainer"] { background: #0d1117; }
[data-testid="stHeader"]           { background: transparent; }

/* ---- vibrant metric cards ---- */
.kpi-card {
    border-radius: 12px;
    padding: 20px 24px;
    text-align: left;
    box-shadow: 0 4px 16px rgba(0,0,0,.4);
    color: #ffffff; 
}

/* Custom background colors for each card */
.bg-blue   { background-color: #3b82f6; }
.bg-green  { background-color: #10b981; }
.bg-orange { background-color: #f59e0b; }
.bg-purple { background-color: #8b5cf6; }

.kpi-label  { font-size: 13px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 6px; opacity: 0.9; }
.kpi-value  { font-size: 36px; font-weight: 700; line-height: 1; margin-bottom: 8px; }
.kpi-delta  { font-size: 13px; font-weight: 500; background: rgba(255,255,255,0.2); padding: 2px 6px; border-radius: 4px;}

/* ---- section headers ---- */
.section-header {
    font-size: 16px; font-weight: 600; color: #e6edf3;
    letter-spacing: .5px; margin: 20px 0 15px 0;
}
hr { border-color: #30363d !important; }
</style>
""", unsafe_allow_html=True)

# ── 🚨 YOUR REAL SPREADSHEET URL ───────────────────────────────────────────────
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

# ── Data loading (Connected to GSheets) ───────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    dc_raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Dashboard_Card")
    ft_raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="FID_Tracking")
    ag_raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Aging_Distribution")

    dc = dc_raw.copy()
    dc.columns = dc.iloc[0]
    dc = dc.iloc[1:].reset_index(drop=True)
    dc.rename(columns={"Date": "Date", "ISD": "ISD", "OSD": "OSD", "Total": "Total", "FID Backlog (%)": "FID_Backlog_Pct", "Zone Transfer": "Zone_Transfer"}, inplace=True)
    dc = dc[["Date", "ISD", "OSD", "Total", "FID_Backlog_Pct", "Zone_Transfer"]].dropna(subset=["Date"])
    dc["Date"] = pd.to_datetime(dc["Date"])
    for col in ["ISD", "OSD", "Total", "FID_Backlog_Pct", "Zone_Transfer"]: dc[col] = pd.to_numeric(dc[col], errors="coerce")
    dc["Date_Label"] = dc["Date"].dt.strftime("%b %d")

    ft = ft_raw.copy()
    ft["Report Date"] = pd.to_datetime(ft["Report Date"])
    ft.rename(columns={"Report Date": "Report_Date", "Newly Added": "Newly_Added", "Total In Progress (Backlog)": "Total_In_Progress", "Worked On": "Worked_On", "Carry Forward": "Carry_Forward"}, inplace=True)
    ft["Date_Label"] = ft["Report_Date"].dt.strftime("%b %d")

    ag = ag_raw.copy()
    ag["Report Date"] = pd.to_datetime(ag["Report Date"])
    age_cols = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, "10+"]
    keep_cols = ["Report Date", "Region"] + age_cols + ["Total"]
    ag = ag[[c for c in keep_cols if c in ag.columns]].copy()
    ag["Region"] = ag["Region"].astype(str).str.strip()
    for c in age_cols + ["Total"]:
        if c in ag.columns: ag[c] = pd.to_numeric(ag[c], errors="coerce")
    ag["Date_Label"] = ag["Report Date"].dt.strftime("%b %d")

    return dc, ft, ag

with st.spinner("Loading live data from Google Sheets…"):
    dc, ft, ag = load_data()

# ── TOP LAYER: Title & Horizontal Filters ──────────────────────────────────────
st.title("🐝 Carrybee Delivery Intelligence")
st.markdown("---")

st.markdown('<div class="section-header" style="margin-top: 0;">Data Filters</div>', unsafe_allow_html=True)
f_col1, f_col2, f_col3 = st.columns(3)

with f_col1:
    all_dates = sorted(ft["Report_Date"].dropna().unique())
    date_opts = [pd.Timestamp(d).strftime("%b %d, %Y") for d in all_dates]
    
    sub_col1, sub_col2 = st.columns(2)
    with sub_col1: start_idx = st.selectbox("From date", range(len(date_opts)), format_func=lambda i: date_opts[i], index=0)
    with sub_col2: end_idx   = st.selectbox("To date",   range(len(date_opts)), format_func=lambda i: date_opts[i], index=len(date_opts)-1)
    
    if end_idx < start_idx:
        st.warning("End date is before start date.")
        end_idx = start_idx
        
    sel_start = pd.Timestamp(all_dates[start_idx])
    sel_end   = pd.Timestamp(all_dates[end_idx])

with f_col2:
    aging_region = st.multiselect("Hubs / Regions", ["ISD", "OSD"], default=["ISD", "OSD"])

with f_col3:
    st.markdown("<br>", unsafe_allow_html=True) # Spacer for alignment
    show_worked  = st.toggle("Show Worked On Line", value=True)

st.markdown("---")

# ── Filter data ───────────────────────────────────────────────────────────────
ft_f = ft[(ft["Report_Date"] >= sel_start) & (ft["Report_Date"] <= sel_end)].copy()
dc_f = dc[(dc["Date"] >= sel_start) & (dc["Date"] <= sel_end)].copy()
ag_f = ag[(ag["Report Date"] >= sel_start) & (ag["Report Date"] <= sel_end)].copy()
ag_f = ag_f[ag_f["Region"].isin(aging_region)] if aging_region else ag_f

latest_ft = ft_f.sort_values("Report_Date").iloc[-1] if not ft_f.empty else None
latest_dc = dc_f.sort_values("Date").iloc[-1] if not dc_f.empty else None
prev_ft   = ft_f.sort_values("Report_Date").iloc[-2] if len(ft_f) > 1 else None

def delta_html(curr, prev, fmt="{:,.0f}", inverse=False):
    if prev is None or pd.isna(curr) or pd.isna(prev): return ""
    d = curr - prev
    if d == 0: return '<span class="kpi-delta">→ No change</span>'
    arrow = "▲" if d > 0 else "▼"
    return f'<span class="kpi-delta">{arrow} {fmt.format(abs(d))}</span>'

# ── SECOND LAYER: 4 KPIs ───────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

kpi_data = [
    (k1, "Total Process", "bg-blue",
     f"{latest_ft['Total_In_Progress']:,.0f}" if latest_ft is not None else "—",
     delta_html(latest_ft["Total_In_Progress"] if latest_ft is not None else None, prev_ft["Total_In_Progress"] if prev_ft is not None else None)),
    
    (k2, "FID Backlog %", "bg-green",
     f"{latest_dc['FID_Backlog_Pct']*100:.2f}%" if latest_dc is not None and pd.notna(latest_dc["FID_Backlog_Pct"]) else "—",
     delta_html(latest_dc["FID_Backlog_Pct"] if latest_dc is not None else None, dc_f.sort_values("Date").iloc[-2]["FID_Backlog_Pct"] if len(dc_f) > 1 else None, fmt="{:.2%}")),
     
    (k3, "Newly Added", "bg-orange",
     f"{latest_ft['Newly_Added']:,.0f}" if latest_ft is not None else "—",
     delta_html(latest_ft["Newly_Added"] if latest_ft is not None else None, prev_ft["Newly_Added"] if prev_ft is not None else None)),
    
    (k4, "Zone Transfer", "bg-purple",
     f"{latest_dc['Zone_Transfer']:,.0f}" if latest_dc is not None and pd.notna(latest_dc["Zone_Transfer"]) else "—", ""),
]

for col, label, color_class, value, delta in kpi_data:
    with col:
        st.markdown(f"""
        <div class="kpi-card {color_class}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta}
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── THIRD LAYER: Combo & Donut Charts ──────────────────────────────────────────
c_combo, c_donut = st.columns([3, 2])

with c_combo:
    st.markdown('<div class="section-header">Combo Chart: Daily Workflow</div>', unsafe_allow_html=True)

    fig_combo = go.Figure()
    fig_combo.add_trace(go.Bar(
        x=ft_f["Date_Label"], y=ft_f["Total_In_Progress"],
        name="Total In Progress", marker_color="#3b82f6",
        hovertemplate="<b>Total In Progress</b>: %{y:,}<extra></extra>"
    ))
    fig_combo.add_trace(go.Bar(
        x=ft_f["Date_Label"], y=ft_f["Newly_Added"],
        name="Newly Added", marker_color="#f59e0b",
        hovertemplate="<b>Newly Added</b>: %{y:,}<extra></extra>"
    ))
    if show_worked:
        fig_combo.add_trace(go.Scatter(
            x=ft_f["Date_Label"], y=ft_f["Worked_On"],
            name="Worked On", mode="lines+markers",
            line=dict(color="#10b981", width=3),
            marker=dict(size=8, symbol="circle"),
            hovertemplate="<b>Worked On</b>: %{y:,}<extra></extra>"
        ))
    fig_combo.update_layout(**PLOT_THEME, height=360, barmode='group')
    st.plotly_chart(fig_combo, use_container_width=True)

with c_donut:
    st.markdown('<div class="section-header">Donut: Distribution</div>', unsafe_allow_html=True)
    if latest_dc is not None:
        fig_donut = go.Figure(data=[go.Pie(
            labels=['ISD', 'OSD'], values=[latest_dc['ISD'], latest_dc['OSD']], 
            hole=.6, marker_colors=[COLOR_ISD, COLOR_OSD], textinfo='label+percent',
            hovertemplate="<b>%{label}</b><br>Count: %{value:,}<extra></extra>"
        )])
        fig_donut.update_layout(**PLOT_THEME, height=360, showlegend=True)
        fig_donut.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
        st.plotly_chart(fig_donut, use_container_width=True)

st.markdown("---")

# ── FOURTH LAYER: Bar & Stacked Bar Charts ─────────────────────────────────────
c_aging, c_region = st.columns([3, 2])

AGE_COLS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, "10+"]
AGE_LABELS = ["1d", "2d", "3d", "4d", "5d", "6d", "7d", "8d", "9d", "10d", "10+d"]

with c_aging:
    st.markdown('<div class="section-header">Bar Chart: Aging</div>', unsafe_allow_html=True)
    latest_ag_date = ag_f["Report Date"].max()
    ag_latest = ag_f[ag_f["Report Date"] == latest_ag_date].copy()
    rows = []
    for _, row in ag_latest.iterrows():
        for col, lbl in zip(AGE_COLS, AGE_LABELS):
            if col in ag_latest.columns:
                rows.append({"Region": row["Region"], "Age": lbl, "Count": row[col]})
    ag_melt = pd.DataFrame(rows)
    if not ag_melt.empty:
        fig_age = px.bar(
            ag_melt, x="Age", y="Count", color="Region",
            color_discrete_map={"ISD": COLOR_ISD, "OSD": COLOR_OSD},
            barmode="group", category_orders={"Age": AGE_LABELS},
        )
        fig_age.update_traces(hovertemplate="<b>%{x}</b><br>Count: %{y:,}<extra></extra>")
        fig_age.update_layout(**PLOT_THEME, height=350)
        st.plotly_chart(fig_age, use_container_width=True)

with c_region:
    st.markdown('<div class="section-header">Stacked Bar: Region Trend</div>', unsafe_allow_html=True)
    fig_reg = go.Figure()
    fig_reg.add_trace(go.Bar(x=dc_f["Date_Label"], y=dc_f["ISD"], name="ISD", marker_color=COLOR_ISD))
    fig_reg.add_trace(go.Bar(x=dc_f["Date_Label"], y=dc_f["OSD"], name="OSD", marker_color=COLOR_OSD))
    fig_reg.update_layout(**PLOT_THEME, barmode="stack", height=350)
    st.plotly_chart(fig_reg, use_container_width=True)

st.markdown("---")

# ── BOTTOM LAYER: Raw Data Table ──────────────────────────────────────────────
with st.expander("📋 Raw Data Table"):
    disp = ft_f[["Date_Label", "Newly_Added", "Total_In_Progress", "Worked_On", "Carry_Forward"]].copy()
    disp.columns = ["Date", "Newly Added", "Total In Progress", "Worked On", "Carry Forward"]
    st.dataframe(disp.style.format({
        "Newly Added": "{:,.0f}", "Total In Progress": "{:,.0f}",
        "Worked On": "{:,.0f}", "Carry Forward": "{:,.0f}",
    }), use_container_width=True)
