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
[data-testid="stAppViewContainer"] { background: #0d1117; }
[data-testid="stHeader"]           { background: transparent; }

.kpi-card {
    border-radius: 12px;
    padding: 16px 20px;
    text-align: left;
    box-shadow: 0 4px 16px rgba(0,0,0,.4);
    color: #ffffff; 
}
.bg-blue   { background-color: #3b82f6; }
.bg-green  { background-color: #10b981; }
.bg-orange { background-color: #f59e0b; }
.bg-purple { background-color: #8b5cf6; }
.bg-red    { background-color: #ef4444; }
.bg-teal   { background-color: #14b8a6; }

.kpi-label  { font-size: 12px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 6px; opacity: 0.9; line-height: 1.2;}
.kpi-value  { font-size: 32px; font-weight: 700; line-height: 1; margin-bottom: 8px; }
.kpi-delta  { font-size: 12px; font-weight: 500; background: rgba(255,255,255,0.2); padding: 2px 6px; border-radius: 4px;}

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
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#161b22",
    font=dict(color="#c9d1d9", family="Inter, sans-serif", size=12),
    xaxis=dict(gridcolor="#21262d", linecolor="#30363d", tickcolor="#30363d"),
    yaxis=dict(gridcolor="#21262d", linecolor="#30363d", tickcolor="#30363d"),
    legend=dict(bgcolor="#1c2333", bordercolor="#30363d", borderwidth=1),
    hoverlabel=dict(bgcolor="#1c2333", bordercolor="#388bfd", font_color="#e6edf3"),
    margin=dict(l=20, r=20, t=45, b=20),
)

COLOR_ISD = "#388bfd"
COLOR_OSD = "#3fb950"

# ── Robust Data Loading & Cleaning ───────────────────────────────────────────
# ── Robust Data Loading & Cleaning ───────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    def get_sheet(sheet_name):
        try:
            return conn.read(spreadsheet=SPREADSHEET_URL, worksheet=sheet_name)
        except Exception:
            return pd.DataFrame()

    dc = get_sheet("Dashboard_Card")
    ft = get_sheet("FID_Tracking")
    ag = get_sheet("Aging_Distribution")
    fr = get_sheet("FID_RID_Backlog_Details")
    st_det = get_sheet("Sort Details")

    # 1. Clean Dashboard_Card
    if not dc.empty:
        if "Date" not in dc.columns:
            dc.columns = dc.iloc[0]
            dc = dc.iloc[1:].reset_index(drop=True)
        dc = dc[~dc.iloc[:, 0].astype(str).str.contains('Grand Total', case=False, na=False)]
        dc.rename(columns={"FID Backlog (%)": "FID_Backlog_Pct", "Zone Transfer": "Zone_Transfer", "Zone Transfer (%)": "Zone_Transfer_Pct"}, inplace=True)
        if "Date" in dc.columns:
            dc["Date"] = pd.to_datetime(dc["Date"], errors='coerce')
            dc = dc.dropna(subset=["Date"])
            for col in ["ISD", "OSD", "Total", "FID_Backlog_Pct", "Zone_Transfer", "Zone_Transfer_Pct"]: 
                if col in dc.columns: dc[col] = pd.to_numeric(dc[col].astype(str).str.replace(',', ''), errors="coerce").fillna(0)
            dc["Date_Label"] = dc["Date"].dt.strftime("%b %d")

    # 2. Clean FID_Tracking
    if not ft.empty:
        if "Report Date" not in ft.columns:
            ft.columns = ft.iloc[0]
            ft = ft.iloc[1:].reset_index(drop=True)
        ft = ft[~ft.iloc[:, 0].astype(str).str.contains('Grand Total', case=False, na=False)]
        ft.rename(columns={"Report Date": "Report_Date", "Newly Added": "Newly_Added", "Total In Progress (Backlog)": "Total_In_Progress", "Worked On": "Worked_On", "Carry Forward": "Carry_Forward"}, inplace=True)
        if "Report_Date" in ft.columns:
            ft["Report_Date"] = pd.to_datetime(ft["Report_Date"], errors='coerce')
            ft = ft.dropna(subset=["Report_Date"])
            for col in ["Newly_Added", "Total_In_Progress", "Worked_On", "Carry_Forward"]:
                if col in ft.columns: ft[col] = pd.to_numeric(ft[col].astype(str).str.replace(',', ''), errors="coerce").fillna(0)
            ft["Date_Label"] = ft["Report_Date"].dt.strftime("%b %d")

    # 3. Clean Aging_Distribution
    if not ag.empty:
        if "Report Date" not in ag.columns:
            ag.columns = ag.iloc[0]
            ag = ag.iloc[1:].reset_index(drop=True)
        ag["Report Date"] = ag["Report Date"].ffill()
        ag = ag[~ag.iloc[:, 0].astype(str).str.contains('Grand Total', case=False, na=False)]
        if "Report Date" in ag.columns:
            ag["Report Date"] = pd.to_datetime(ag["Report Date"], errors='coerce')
            ag = ag.dropna(subset=["Report Date"])
            ag.columns = [str(c).strip() for c in ag.columns]
            ag["Region"] = ag["Region"].astype(str).str.strip()
            for c in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "10+", "Total"]:
                if c in ag.columns: ag[c] = pd.to_numeric(ag[c].astype(str).str.replace(',', ''), errors="coerce").fillna(0)

    # 4. Clean FID_RID Details
    if not fr.empty:
        if "Report Date" not in fr.columns and "Date" not in fr.columns:
            fr.columns = fr.iloc[0]
            fr = fr.iloc[1:].reset_index(drop=True)
        fr = fr[~fr.iloc[:, 0].astype(str).str.contains('Grand Total', case=False, na=False)]
        date_col = "Report Date" if "Report Date" in fr.columns else "Date"
        if date_col in fr.columns:
            fr[date_col] = pd.to_datetime(fr[date_col], errors='coerce')
            fr = fr.dropna(subset=[date_col])
        for col in fr.columns:
            if col not in ["Date", "Report Date", "Region", "Type"]:
                fr[col] = pd.to_numeric(fr[col].astype(str).str.replace(',', ''), errors="coerce").fillna(0)

    # 5. Clean Sort Details
    if not st_det.empty:
        if "Report Date" not in st_det.columns and "Date" not in st_det.columns:
            st_det.columns = st_det.iloc[0]
            st_det = st_det.iloc[1:].reset_index(drop=True)
        st_det = st_det[~st_det.iloc[:, 0].astype(str).str.contains('Grand Total', case=False, na=False)]
        date_col = "Report Date" if "Report Date" in st_det.columns else "Date"
        if date_col in st_det.columns:
            st_det[date_col] = pd.to_datetime(st_det[date_col], errors='coerce')
            st_det = st_det.dropna(subset=[date_col])
        for col in st_det.columns:
            if col not in ["Date", "Report Date", "Region"]:
                st_det[col] = pd.to_numeric(st_det[col].astype(str).str.replace(',', ''), errors="coerce").fillna(0)

    return dc, ft, ag, fr, st_det

with st.spinner("Loading live data from Google Sheets…"):
    dc, ft, ag, fr, st_det = load_data()

# ── TOP LAYER: Title & Horizontal Filters ──────────────────────────────────────
st.title("🐝 Carrybee Delivery Intelligence")
st.markdown("---")

st.markdown('<div class="section-header" style="margin-top: 0;">Data Filters</div>', unsafe_allow_html=True)
f_col1, f_col2, f_col3 = st.columns(3)

with f_col1:
    all_dates = sorted(ft["Report_Date"].dropna().unique()) if not ft.empty else []
    if all_dates:
        date_opts = [pd.Timestamp(d).strftime("%b %d, %Y") for d in all_dates]
        sub_col1, sub_col2 = st.columns(2)
        with sub_col1: start_idx = st.selectbox("From date", range(len(date_opts)), format_func=lambda i: date_opts[i], index=0)
        with sub_col2: end_idx   = st.selectbox("To date",   range(len(date_opts)), format_func=lambda i: date_opts[i], index=len(date_opts)-1)
        
        if end_idx < start_idx:
            st.warning("End date is before start date.")
            end_idx = start_idx
        sel_start = pd.Timestamp(all_dates[start_idx])
        sel_end   = pd.Timestamp(all_dates[end_idx])
    else:
        sel_start, sel_end = pd.Timestamp.now(), pd.Timestamp.now()

with f_col2:
    aging_region = st.multiselect("Hubs / Regions", ["ISD", "OSD"], default=["ISD", "OSD"])

with f_col3:
    st.markdown("<br>", unsafe_allow_html=True)
    show_worked = st.toggle("Show Worked On Line (Combo Chart)", value=True)

st.markdown("---")

# ── Filter Data based on selection ───────────────────────────────────────────
ft_f = ft[(ft["Report_Date"] >= sel_start) & (ft["Report_Date"] <= sel_end)].copy() if not ft.empty else ft
dc_f = dc[(dc["Date"] >= sel_start) & (dc["Date"] <= sel_end)].copy() if not dc.empty else dc
ag_f = ag[(ag["Report Date"] >= sel_start) & (ag["Report Date"] <= sel_end)].copy() if not ag.empty else ag
ag_f = ag_f[ag_f["Region"].isin(aging_region)] if aging_region and not ag_f.empty else ag_f

# Dynamic filter for FR and Sort
fr_date_col = "Report Date" if "Report Date" in fr.columns else "Date"
st_date_col = "Report Date" if "Report Date" in st_det.columns else "Date"
fr_f = fr[(fr[fr_date_col] >= sel_start) & (fr[fr_date_col] <= sel_end)].copy() if not fr.empty else fr
st_det_f = st_det[(st_det[st_date_col] >= sel_start) & (st_det[st_date_col] <= sel_end)].copy() if not st_det.empty else st_det

# Extract Latest Values
latest_ft = ft_f.sort_values("Report_Date").iloc[-1] if not ft_f.empty else None
latest_dc = dc_f.sort_values("Date").iloc[-1] if not dc_f.empty else None

def delta_html(curr, prev, fmt="{:,.0f}", inverse=False):
    if prev is None or pd.isna(curr) or pd.isna(prev): return ""
    d = curr - prev
    if d == 0: return '<span class="kpi-delta">→ No change</span>'
    arrow = "▲" if d > 0 else "▼"
    return f'<span class="kpi-delta">{arrow} {fmt.format(abs(d))}</span>'

# ── SECOND LAYER: 5 KPIs (Requirements 1, 2, 3, 4, 5) ─────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

# Calculate Overall Backlog safely (Requirement 2)
overall_backlog = "—"
if latest_ft is not None:
    overall_backlog_val = latest_ft['Total_In_Progress']
    # If we have RID backlog in FR Details, add it
    if not fr_f.empty and len(fr_f) > 0:
        latest_fr = fr_f.sort_values(fr_date_col).iloc[-1]
        rid_cols = [c for c in fr.columns if "RID" in c.upper() and ("TOTAL" in c.upper() or "BACKLOG" in c.upper())]
        if rid_cols:
            overall_backlog_val += latest_fr[rid_cols[0]]
    overall_backlog = f"{overall_backlog_val:,.0f}"

kpi_data = [
    (k1, "1. Total FID Parcel", "bg-blue", f"{latest_ft['Total_In_Progress']:,.0f}" if latest_ft is not None else "—"),
    (k2, "2. Overall Backlog", "bg-red", overall_backlog),
    (k3, "3. Zone Transfers", "bg-orange", f"{latest_dc['Zone_Transfer']:,.0f}" if latest_dc is not None else "—"),
    (k4, "4. FID Backlog %", "bg-green", f"{latest_dc['FID_Backlog_Pct']*100:.2f}%" if latest_dc is not None else "—"),
    (k5, "5. Zone Change %", "bg-purple", f"{latest_dc.get('Zone_Transfer_Pct', 0)*100:.2f}%" if latest_dc is not None and 'Zone_Transfer_Pct' in latest_dc else "—"),
]

for col, label, color_class, value in kpi_data:
    with col:
        st.markdown(f'<div class="kpi-card {color_class}"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── THIRD LAYER: Requirements 11 & 6 ──────────────────────────────────────────
c_combo, c_donut = st.columns([3, 2])

with c_combo:
    st.markdown('<div class="section-header">11. Date Wise Backlog Tracking (FID)</div>', unsafe_allow_html=True)
    fig_combo = go.Figure()
    if not ft_f.empty:
        fig_combo.add_trace(go.Bar(x=ft_f["Date_Label"], y=ft_f["Total_In_Progress"], name="Total In Progress", marker_color="#3b82f6"))
        fig_combo.add_trace(go.Bar(x=ft_f["Date_Label"], y=ft_f["Newly_Added"], name="Newly Added", marker_color="#f59e0b"))
        if show_worked:
            fig_combo.add_trace(go.Scatter(x=ft_f["Date_Label"], y=ft_f["Worked_On"], name="Worked On", mode="lines+markers", line=dict(color="#10b981", width=3), marker=dict(size=8)))
        fig_combo.update_layout(**PLOT_THEME, height=360, barmode='group')
        st.plotly_chart(fig_combo, use_container_width=True)

with c_donut:
    st.markdown('<div class="section-header">6. Region Wise In Process Parcel</div>', unsafe_allow_html=True)
    if latest_dc is not None:
        fig_donut = go.Figure(data=[go.Pie(
            labels=['ISD', 'OSD'], values=[latest_dc['ISD'], latest_dc['OSD']], 
            hole=.6, marker_colors=[COLOR_ISD, COLOR_OSD], textinfo='label+percent',
        )])
        fig_donut.update_layout(**PLOT_THEME, height=360, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
        st.plotly_chart(fig_donut, use_container_width=True)

st.markdown("---")

# ── FOURTH LAYER: Requirements 7 & 9 ──────────────────────────────────────────
c_fr_pie, c_fr_bar = st.columns([2, 3])

with c_fr_pie:
    st.markdown('<div class="section-header">7. Backlog (FID vs RID)</div>', unsafe_allow_html=True)
    if not fr_f.empty:
        latest_fr = fr_f.sort_values(fr_date_col).iloc[-1]
        
        # Safely find columns matching Total FID and Total RID
        fid_tots = [c for c in fr.columns if "FID" in c.upper() and "TOTAL" in c.upper()]
        rid_tots = [c for c in fr.columns if "RID" in c.upper() and "TOTAL" in c.upper()]
        
        if fid_tots and rid_tots:
            fig_fr_pie = go.Figure(data=[go.Pie(
                labels=['FID Backlog', 'RID Backlog'], 
                values=[latest_fr[fid_tots[0]], latest_fr[rid_tots[0]]], 
                marker_colors=["#3b82f6", "#ef4444"], textinfo='label+percent+value'
            )])
            fig_fr_pie.update_layout(**PLOT_THEME, height=350, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig_fr_pie, use_container_width=True)
        else:
            st.info("Could not find 'Total FID' and 'Total RID' columns in FID_RID_Backlog_Details.")
    else:
        st.warning("FID_RID_Backlog_Details sheet is missing or empty.")

with c_fr_bar:
    st.markdown('<div class="section-header">9. Backlog Details (LMH & FMH)</div>', unsafe_allow_html=True)
    if not fr_f.empty:
        latest_fr = fr_f.sort_values(fr_date_col).iloc[-1]
        
        # Safely identify the 4 specific columns
        lmh_fmh_data = {}
        for metric in ["FID LMH", "FID FMH", "RID LMH", "RID FMH"]:
            matched_col = [c for c in fr.columns if metric.replace(" ", "") in c.replace(" ", "")]
            if matched_col:
                lmh_fmh_data[metric] = latest_fr[matched_col[0]]
        
        if lmh_fmh_data:
            df_lmh = pd.DataFrame(list(lmh_fmh_data.items()), columns=["Category", "Count"])
            fig_lmh = px.bar(df_lmh, x="Category", y="Count", color="Category", 
                             color_discrete_sequence=["#3b82f6", "#60a5fa", "#ef4444", "#f87171"])
            fig_lmh.update_layout(**PLOT_THEME, height=350, showlegend=False)
            st.plotly_chart(fig_lmh, use_container_width=True)
        else:
            st.info("LMH/FMH columns not detected.")
    else:
        st.warning("Data not available.")

st.markdown("---")

# ── FIFTH LAYER: Requirements 10 & 8 ──────────────────────────────────────────
c_sort, c_aging = st.columns(2)

with c_sort:
    st.markdown('<div class="section-header">10. Sort (FID Sort vs RID Sort)</div>', unsafe_allow_html=True)
    if not st_det_f.empty:
        latest_sort = st_det_f.sort_values(st_date_col).iloc[-1]
        
        sort_data = {}
        for metric in ["FID Sort", "RID Sort"]:
            matched_col = [c for c in st_det.columns if metric.upper() in c.upper()]
            if matched_col:
                sort_data[metric] = latest_sort[matched_col[0]]
                
        if sort_data:
            df_sort = pd.DataFrame(list(sort_data.items()), columns=["Type", "Parcels"])
            fig_sort = px.bar(df_sort, x="Type", y="Parcels", color="Type", color_discrete_sequence=["#3b82f6", "#ef4444"])
            fig_sort.update_layout(**PLOT_THEME, height=350, showlegend=False)
            st.plotly_chart(fig_sort, use_container_width=True)
        else:
            st.info("Sort columns not detected in Sort Details sheet.")
    else:
        st.warning("Sort Details sheet is missing or empty.")

with c_aging:
    st.markdown('<div class="section-header">8. Aging Distribution (%)</div>', unsafe_allow_html=True)
    if not ag_f.empty:
        latest_ag_date = ag_f["Report Date"].max()
        ag_latest = ag_f[ag_f["Report Date"] == latest_ag_date].copy()
        
        AGE_COLS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "10+"]
        rows = []
        for _, row in ag_latest.iterrows():
            total_region = sum([row[c] for c in AGE_COLS if c in ag_latest.columns and pd.notna(row[c])])
            for col in AGE_COLS:
                if col in ag_latest.columns:
                    val = row[col]
                    pct = (val / total_region * 100) if total_region > 0 else 0
                    rows.append({"Region": row["Region"], "Age": f"{col}d", "Count": val, "Percentage": pct})
                    
        ag_melt = pd.DataFrame(rows)
        if not ag_melt.empty:
            # Using 100% Stacked Bar behavior by showing percentage
            fig_age = px.bar(
                ag_melt, x="Age", y="Percentage", color="Region",
                color_discrete_map={"ISD": COLOR_ISD, "OSD": COLOR_OSD},
                barmode="group", text=ag_melt["Percentage"].apply(lambda x: f"{x:.1f}%")
            )
            fig_age.update_traces(textposition="outside", hovertemplate="<b>%{x}</b><br>Count: %{customdata[0]:,}<br>Pct: %{y:.1f}%", customdata=ag_melt[["Count"]])
            fig_age.update_layout(**PLOT_THEME, height=350, yaxis_title="Percentage (%)")
            st.plotly_chart(fig_age, use_container_width=True)
