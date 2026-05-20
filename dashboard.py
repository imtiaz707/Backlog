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

# ── Bulletproof Universal Data Cleaner ───────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    def fetch_and_clean(sheet_name):
        try:
            df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet=sheet_name)
            if df.empty: return pd.DataFrame()
            
            # 1. Force Headers
            df.columns = [str(c).strip() for c in df.columns]
            if df.columns[0] in ["0", ""] or "Unnamed" in df.columns[0]:
                df.columns = [str(c).strip() for c in df.iloc[0]]
                df = df.iloc[1:].reset_index(drop=True)
            
            # 2. Identify Date Column
            date_cols = [c for c in df.columns if 'DATE' in c.upper() or c.upper() == 'DATE']
            if not date_cols: return pd.DataFrame()
            date_col = date_cols[0]
            
            # 3. Forward Fill Dates (Fixes Merged Cells for OSD/RID)
            df[date_col] = df[date_col].ffill()
            
            # 4. Remove 'Grand Total' Rows
            df = df[~df[date_col].astype(str).str.contains('Grand Total', case=False, na=False)]
            
            # 5. Parse Dates
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col])
            
            # 6. Parse Numbers (Strip Commas & %)
            for c in df.columns:
                if c != date_col and c.upper() not in ['REGION', 'TYPE']:
                    clean_str = df[c].astype(str).str.replace(',', '', regex=False).str.replace('%', '', regex=False)
                    df[c] = pd.to_numeric(clean_str, errors='coerce').fillna(0)
                    
            # 7. Standardize Date Access
            df.rename(columns={date_col: "Standard_Date"}, inplace=True)
            df["Date_Label"] = df["Standard_Date"].dt.strftime("%b %d")
            return df
        except Exception as e:
            return pd.DataFrame()

    dc = fetch_and_clean("Dashboard_Card")
    ft = fetch_and_clean("FID_Tracking")
    rt = fetch_and_clean("RID Tracking") # Included to calculate Overall Backlog properly
    ag = fetch_and_clean("Aging_Distribution")
    fr = fetch_and_clean("FID_RID_Backlog_Details")
    st_det = fetch_and_clean("Sort Details")

    return dc, ft, rt, ag, fr, st_det

with st.spinner("Loading live data from Google Sheets…"):
    dc, ft, rt, ag, fr, st_det = load_data()

# ── Dynamic Column Lookups (Prevents KeyErrors if Excel changes spacing) ─────
def get_col(df, keyword, exclude=None):
    if df.empty: return None
    for c in df.columns:
        if keyword.upper() in c.upper():
            if exclude and exclude.upper() in c.upper(): continue
            return c
    return None

# ── TOP LAYER: Title & Horizontal Filters ──────────────────────────────────────
st.title("🐝 Carrybee Delivery Intelligence")
st.markdown("---")

st.markdown('<div class="section-header" style="margin-top: 0;">Data Filters</div>', unsafe_allow_html=True)
f_col1, f_col2, f_col3 = st.columns(3)

with f_col1:
    all_dates = sorted(ft["Standard_Date"].dropna().unique()) if not ft.empty else []
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
        st.error("No valid dates found. Check the sheet formatting.")

with f_col2:
    aging_region = st.multiselect("Hubs / Regions", ["ISD", "OSD"], default=["ISD", "OSD"])

with f_col3:
    st.markdown("<br>", unsafe_allow_html=True)
    show_worked = st.toggle("Show Worked On Line (Combo Chart)", value=True)

st.markdown("---")

# ── Filter Data based on selection ───────────────────────────────────────────
def filter_df(df, region_col=None):
    if df.empty: return df
    mask = (df["Standard_Date"] >= sel_start) & (df["Standard_Date"] <= sel_end)
    filtered = df[mask].copy()
    if region_col and aging_region and region_col in filtered.columns:
        filtered = filtered[filtered[region_col].isin(aging_region)]
    return filtered

ft_f = filter_df(ft)
rt_f = filter_df(rt)
dc_f = filter_df(dc)
ag_f = filter_df(ag, "Region")
fr_f = filter_df(fr)
st_det_f = filter_df(st_det)

# ── Latest Row Extractions ───────────────────────────────────────────────────
latest_ft = ft_f.sort_values("Standard_Date").iloc[-1] if not ft_f.empty else None
latest_dc = dc_f.sort_values("Standard_Date").iloc[-1] if not dc_f.empty else None
latest_rt = rt_f.sort_values("Standard_Date").iloc[-1] if not rt_f.empty else None

# ── SECOND LAYER: 5 KPIs (Requirements 1, 2, 3, 4, 5) ─────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

# Safety variables
ft_prog_col = get_col(ft, "IN PROGRESS")
rt_prog_col = get_col(rt, "IN PROGRESS")
dc_zt_col = get_col(dc, "ZONE TRANSFER", exclude="%")
dc_fid_pct_col = get_col(dc, "FID BACKLOG")
dc_zt_pct_col = get_col(dc, "ZONE TRANSFER", exclude="NOT") # Grab the % one if it exists

tot_fid = latest_ft[ft_prog_col] if latest_ft is not None and ft_prog_col else 0
tot_rid = latest_rt[rt_prog_col] if latest_rt is not None and rt_prog_col else 0
zt_val = latest_dc[dc_zt_col] if latest_dc is not None and dc_zt_col else 0

# Formatting Percentages correctly (handles both '0.1' and '10' from Excel)
fid_pct_raw = latest_dc[dc_fid_pct_col] if latest_dc is not None and dc_fid_pct_col else 0
zt_pct_raw = latest_dc[dc_zt_pct_col] if latest_dc is not None and dc_zt_pct_col else 0
fid_pct_str = f"{fid_pct_raw:.1f}%" if fid_pct_raw > 1 else f"{fid_pct_raw*100:.1f}%"
zt_pct_str = f"{zt_pct_raw:.1f}%" if zt_pct_raw > 1 else f"{zt_pct_raw*100:.1f}%"

kpi_data = [
    (k1, "1. Total FID Parcel", "bg-blue", f"{tot_fid:,.0f}"),
    (k2, "2. Overall Backlog", "bg-red", f"{(tot_fid + tot_rid):,.0f}"),
    (k3, "3. Zone Transfers", "bg-orange", f"{zt_val:,.0f}"),
    (k4, "4. FID Backlog %", "bg-green", fid_pct_str),
    (k5, "5. Zone Change %", "bg-purple", zt_pct_str),
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
    if not ft_f.empty and ft_prog_col:
        ft_add_col = get_col(ft_f, "NEWLY ADDED")
        ft_wrk_col = get_col(ft_f, "WORKED ON")
        
        fig_combo.add_trace(go.Bar(x=ft_f["Date_Label"], y=ft_f[ft_prog_col], name="Total In Progress", marker_color="#3b82f6"))
        if ft_add_col: fig_combo.add_trace(go.Bar(x=ft_f["Date_Label"], y=ft_f[ft_add_col], name="Newly Added", marker_color="#f59e0b"))
        if show_worked and ft_wrk_col:
            fig_combo.add_trace(go.Scatter(x=ft_f["Date_Label"], y=ft_f[ft_wrk_col], name="Worked On", mode="lines+markers", line=dict(color="#10b981", width=3), marker=dict(size=8)))
            
        fig_combo.update_layout(**PLOT_THEME, height=360, barmode='group')
        st.plotly_chart(fig_combo, use_container_width=True)

with c_donut:
    st.markdown('<div class="section-header">6. Region Wise In Process Parcel</div>', unsafe_allow_html=True)
    if latest_dc is not None and 'ISD' in latest_dc and 'OSD' in latest_dc:
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
        fr_latest = fr_f[fr_f["Standard_Date"] == fr_f["Standard_Date"].max()]
        type_col = get_col(fr_latest, "TYPE")
        
        if type_col and 'LMH' in fr_latest.columns and 'FMH' in fr_latest.columns:
            fid_sum = fr_latest[fr_latest[type_col].astype(str).str.upper() == 'FID'][['LMH', 'FMH']].sum().sum()
            rid_sum = fr_latest[fr_latest[type_col].astype(str).str.upper() == 'RID'][['LMH', 'FMH']].sum().sum()
            
            fig_fr_pie = go.Figure(data=[go.Pie(
                labels=['FID Backlog', 'RID Backlog'], values=[fid_sum, rid_sum], 
                marker_colors=["#3b82f6", "#ef4444"], textinfo='label+percent+value'
            )])
            fig_fr_pie.update_layout(**PLOT_THEME, height=350, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig_fr_pie, use_container_width=True)
        else:
            st.info("Missing Type, LMH, or FMH columns for Pie chart.")

with c_fr_bar:
    st.markdown('<div class="section-header">9. Backlog Details (LMH & FMH)</div>', unsafe_allow_html=True)
    if not fr_f.empty:
        fr_latest = fr_f[fr_f["Standard_Date"] == fr_f["Standard_Date"].max()]
        type_col = get_col(fr_latest, "TYPE")
        
        if type_col and 'LMH' in fr_latest.columns and 'FMH' in fr_latest.columns:
            f_lmh = fr_latest[fr_latest[type_col].astype(str).str.upper() == 'FID']['LMH'].sum()
            f_fmh = fr_latest[fr_latest[type_col].astype(str).str.upper() == 'FID']['FMH'].sum()
            r_lmh = fr_latest[fr_latest[type_col].astype(str).str.upper() == 'RID']['LMH'].sum()
            r_fmh = fr_latest[fr_latest[type_col].astype(str).str.upper() == 'RID']['FMH'].sum()
            
            df_lmh = pd.DataFrame([
                {"Category": "FID LMH", "Count": f_lmh}, {"Category": "FID FMH", "Count": f_fmh},
                {"Category": "RID LMH", "Count": r_lmh}, {"Category": "RID FMH", "Count": r_fmh}
            ])
            fig_lmh = px.bar(df_lmh, x="Category", y="Count", color="Category", color_discrete_sequence=["#3b82f6", "#60a5fa", "#ef4444", "#f87171"])
            fig_lmh.update_layout(**PLOT_THEME, height=350, showlegend=False)
            st.plotly_chart(fig_lmh, use_container_width=True)

st.markdown("---")

# ── FIFTH LAYER: Requirements 10 & 8 ──────────────────────────────────────────
c_sort, c_aging = st.columns(2)

with c_sort:
    st.markdown('<div class="section-header">10. Sort (FID Sort vs RID Sort)</div>', unsafe_allow_html=True)
    if not st_det_f.empty:
        st_latest = st_det_f[st_det_f["Standard_Date"] == st_det_f["Standard_Date"].max()]
        type_col = get_col(st_latest, "TYPE")
        sort_col = get_col(st_latest, "SORT")
        
        if type_col and sort_col:
            f_sort = st_latest[st_latest[type_col].astype(str).str.upper() == 'FID'][sort_col].sum()
            r_sort = st_latest[st_latest[type_col].astype(str).str.upper() == 'RID'][sort_col].sum()
            
            df_sort = pd.DataFrame([{"Type": "FID Sort", "Parcels": f_sort}, {"Type": "RID Sort", "Parcels": r_sort}])
            fig_sort = px.bar(df_sort, x="Type", y="Parcels", color="Type", color_discrete_sequence=["#3b82f6", "#ef4444"])
            fig_sort.update_layout(**PLOT_THEME, height=350, showlegend=False)
            st.plotly_chart(fig_sort, use_container_width=True)
        else:
            st.info("Missing 'Type' or 'Sort' column in Sort Details.")

with c_aging:
    st.markdown('<div class="section-header">8. Aging Distribution (%)</div>', unsafe_allow_html=True)
    if not ag_f.empty and "Region" in ag_f.columns:
        ag_latest = ag_f[ag_f["Standard_Date"] == ag_f["Standard_Date"].max()]
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
            fig_age = px.bar(ag_melt, x="Age", y="Percentage", color="Region", color_discrete_map={"ISD": COLOR_ISD, "OSD": COLOR_OSD}, barmode="group", text=ag_melt["Percentage"].apply(lambda x: f"{x:.1f}%"))
            fig_age.update_traces(textposition="outside", hovertemplate="<b>%{x}</b><br>Count: %{customdata[0]:,}<br>Pct: %{y:.1f}%", customdata=ag_melt[["Count"]])
            fig_age.update_layout(**PLOT_THEME, height=350, yaxis_title="Percentage (%)")
            st.plotly_chart(fig_age, use_container_width=True)
