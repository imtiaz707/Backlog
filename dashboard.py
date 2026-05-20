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

# ── CSS Theme ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }
[data-testid="stAppViewContainer"] { background: #f0f4f8; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { display: none; }
[data-testid="stDecoration"] { display: none; }
.block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 100% !important; }
.dashboard-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
    border-radius: 16px; padding: 18px 28px; margin-bottom: 18px;
}
.dashboard-title { color: #fff; font-size: 26px; font-weight: 800; margin: 0; }
.dashboard-subtitle { color: rgba(255,255,255,0.75); font-size: 13px; margin-top: 4px; }
.kpi-card {
    border-radius: 14px; padding: 18px 20px 14px 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08); color: #fff;
    position: relative; overflow: hidden; min-height: 110px;
}
.kpi-card::after {
    content: ''; position: absolute; top: -20px; right: -20px;
    width: 90px; height: 90px; border-radius: 50%; background: rgba(255,255,255,0.12);
}
.kpi-bg-blue   { background: linear-gradient(135deg, #1d4ed8, #3b82f6); }
.kpi-bg-red    { background: linear-gradient(135deg, #b91c1c, #ef4444); }
.kpi-bg-amber  { background: linear-gradient(135deg, #b45309, #f59e0b); }
.kpi-bg-green  { background: linear-gradient(135deg, #065f46, #10b981); }
.kpi-bg-purple { background: linear-gradient(135deg, #5b21b6, #8b5cf6); }
.kpi-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.7px; opacity: 0.85; margin-bottom: 6px; }
.kpi-value { font-size: 30px; font-weight: 800; line-height: 1.1; margin-bottom: 6px; }
.kpi-delta { font-size: 11px; background: rgba(255,255,255,0.22); padding: 2px 8px; border-radius: 20px; display: inline-block; }
.kpi-delta.up   { color: #bbf7d0; }
.kpi-delta.down { color: #fecaca; }
.sec-hdr {
    font-size: 14px; font-weight: 700; color: #1e3a5f;
    text-transform: uppercase; letter-spacing: 0.6px;
    border-left: 4px solid #2563eb; padding-left: 10px;
    margin-bottom: 8px; margin-top: 4px;
}
.chart-card {
    background: #fff; border-radius: 14px; padding: 16px 18px 8px 18px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06); margin-bottom: 14px;
}
.styled-table { width:100%; border-collapse:collapse; font-size:12px; }
.styled-table thead tr { background:#1e3a5f; color:#fff; }
.styled-table th { padding:8px 10px; text-align:center; font-weight:600; font-size:11px; }
.styled-table tbody tr:nth-child(even) { background:#f8fafc; }
.styled-table tbody tr:last-child { background:#fef9c3; font-weight:700; }
.styled-table td { padding:7px 10px; text-align:center; border-bottom:1px solid #e2e8f0; }
.styled-table .col-date { text-align:left; font-weight:600; color:#1e3a5f; }
.styled-table .col-num { color:#1e3a5f; }
.styled-table .col-high { color:#dc2626; font-weight:700; }
.filter-bar {
    background: #fff; border-radius: 12px; padding: 12px 18px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 14px;
}
.aging-note {
    background:#fef3c7; border:1px solid #f59e0b; border-radius:8px;
    padding:6px 12px; font-size:11px; color:#92400e; font-weight:600;
    margin-top:6px; display:inline-block;
}
div[data-testid="stMetric"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Google Sheet URL ──────────────────────────────────────────────────────────
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1n9GW1UksZ-jhCQ-zmCqwx4EH20fa-Zm5wA5BiMmdZAE/edit?gid=713116247#gid=713116247"

# ── Plot theme (NO xaxis/yaxis keys — apply those per chart to avoid conflict) ─
PLOT_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#334155", family="Inter, sans-serif", size=11),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#e2e8f0", borderwidth=1, font_size=11),
    hoverlabel=dict(bgcolor="#1e293b", bordercolor="#3b82f6", font_color="#f1f5f9"),
    margin=dict(l=10, r=10, t=36, b=10),
)

# Reusable axis style dicts
AXIS_STYLE = dict(gridcolor="#e2e8f0", linecolor="#cbd5e1", tickcolor="#94a3b8", showgrid=True)

COLOR_ISD = "#2563eb"
COLOR_OSD = "#ef4444"


# ── Data Loading ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)

    def fetch_and_clean(sheet_name):
        try:
            df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet=sheet_name)
            if df.empty:
                return pd.DataFrame()
            df.columns = [str(c).strip() for c in df.columns]
            # Fix unnamed headers
            if df.columns[0] in ["0", ""] or "Unnamed" in str(df.columns[0]):
                df.columns = [str(c).strip() for c in df.iloc[0]]
                df = df.iloc[1:].reset_index(drop=True)
            # Find date column
            date_cols = [c for c in df.columns if 'DATE' in c.upper() or c.upper() == 'DATE']
            if not date_cols:
                return pd.DataFrame()
            date_col = date_cols[0]
            df[date_col] = df[date_col].ffill()
            df = df[~df[date_col].astype(str).str.contains('Grand Total', case=False, na=False)]

            # ── FIX 1: Parse dates with dayfirst=True and explicit formats ───
            # Google Sheets often gives "20-May", "20 May", "20/05/2026" etc.
            # dayfirst=True + format guessing handles DD-MM and DD/MM patterns correctly.
            raw_dates = df[date_col].astype(str).str.strip()
            parsed = pd.to_datetime(raw_dates, dayfirst=True, errors='coerce')
            # If year parsed as 0001 or < 2000, it means the date had no year — assume current year
            current_year = pd.Timestamp.now().year
            bad_year_mask = parsed.dt.year < 2000
            if bad_year_mask.any():
                # Re-parse those rows by appending the current year
                fixed = raw_dates[bad_year_mask].apply(
                    lambda s: pd.to_datetime(f"{s} {current_year}", dayfirst=True, errors='coerce')
                )
                parsed[bad_year_mask] = fixed
            df[date_col] = parsed
            df = df.dropna(subset=[date_col])

            # Parse numeric columns
            for c in df.columns:
                if c != date_col and c.upper() not in ['REGION', 'TYPE']:
                    cleaned = df[c].astype(str).str.replace(',', '', regex=False).str.replace('%', '', regex=False)
                    df[c] = pd.to_numeric(cleaned, errors='coerce').fillna(0)
            df.rename(columns={date_col: "Standard_Date"}, inplace=True)
            df["Date_Label"] = df["Standard_Date"].dt.strftime("%d %b")
            return df
        except Exception as e:
            st.warning(f"Error loading sheet '{sheet_name}': {e}")
            return pd.DataFrame()

    dc     = fetch_and_clean("Dashboard_Card")
    ft     = fetch_and_clean("FID_Tracking")
    rt     = fetch_and_clean("RID Tracking")
    ag     = fetch_and_clean("Aging_Distribution")
    fr     = fetch_and_clean("FID_RID_Backlog_Details")
    sd     = fetch_and_clean("Sort Details")
    return dc, ft, rt, ag, fr, sd


def get_col(df, keyword, exclude=None):
    """Case-insensitive column search; optionally excludes columns containing 'exclude' keyword."""
    if df is None or df.empty:
        return None
    for c in df.columns:
        if keyword.upper() in c.upper():
            if exclude and exclude.upper() in c.upper():
                continue
            return c
    return None


def apply_theme(fig, height=None, extra=None):
    """
    Apply PLOT_THEME plus axis styles. Accepts extra kwargs dict.
    Avoids the TypeError from passing yaxis= both inside **PLOT_THEME and as kwarg.
    """
    layout = dict(**PLOT_THEME, xaxis=AXIS_STYLE, yaxis=AXIS_STYLE)
    if height:
        layout["height"] = height
    if extra:
        layout.update(extra)
    fig.update_layout(**layout)
    return fig


# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("🐝 Loading live data…"):
    dc, ft, rt, ag, fr, st_det = load_data()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dashboard-header">
  <div>
    <div class="dashboard-title">🐝 Carrybee Delivery Intelligence</div>
    <div class="dashboard-subtitle">Live Backlog &amp; Operations Dashboard — Auto-refreshes every 10 minutes</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────────────────────────
st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 2])

all_dates = sorted(ft["Standard_Date"].dropna().unique()) if not ft.empty else []
if all_dates:
    date_opts = [pd.Timestamp(d).strftime("%d %b %Y") for d in all_dates]
    with fc1:
        start_idx = st.selectbox("📅 From Date", range(len(date_opts)),
                                 format_func=lambda i: date_opts[i], index=0)
    with fc2:
        end_idx = st.selectbox("📅 To Date", range(len(date_opts)),
                               format_func=lambda i: date_opts[i], index=len(date_opts)-1)
    if end_idx < start_idx:
        end_idx = start_idx
    sel_start = pd.Timestamp(all_dates[start_idx])
    sel_end   = pd.Timestamp(all_dates[end_idx])
else:
    sel_start = sel_end = pd.Timestamp.now()
    st.error("No valid dates found. Check sheet date format.")

with fc3:
    aging_region = st.multiselect("🗺️ Region Filter", ["ISD", "OSD"], default=["ISD", "OSD"])
with fc4:
    show_worked = st.toggle("📈 Show Worked On Line", value=True)
st.markdown('</div>', unsafe_allow_html=True)


# ── Filter helper ─────────────────────────────────────────────────────────────
def filter_df(df, region_col=None):
    if df is None or df.empty:
        return pd.DataFrame()
    mask = (df["Standard_Date"] >= sel_start) & (df["Standard_Date"] <= sel_end)
    filtered = df[mask].copy()
    if region_col and aging_region and region_col in filtered.columns:
        filtered = filtered[filtered[region_col].isin(aging_region)]
    return filtered


ft_f     = filter_df(ft)
rt_f     = filter_df(rt)
dc_f     = filter_df(dc)
ag_f     = filter_df(ag, "Region")
fr_f     = filter_df(fr)
st_det_f = filter_df(st_det)

latest_ft = ft_f.sort_values("Standard_Date").iloc[-1] if not ft_f.empty else None
latest_dc = dc_f.sort_values("Standard_Date").iloc[-1] if not dc_f.empty else None
latest_rt = rt_f.sort_values("Standard_Date").iloc[-1] if not rt_f.empty else None

# ── Column lookups ────────────────────────────────────────────────────────────
ft_prog_col    = get_col(ft_f, "IN PROGRESS")
rt_prog_col    = get_col(rt_f, "IN PROGRESS")
dc_zt_col      = get_col(dc_f, "ZONE TRANSFER", exclude="%")
dc_fid_pct_col = get_col(dc_f, "FID BACKLOG")
dc_zt_pct_col  = get_col(dc_f, "ZONE CHANGE") or get_col(dc_f, "ZONE TRANSFER %")

tot_fid = float(latest_ft[ft_prog_col]) if latest_ft is not None and ft_prog_col else 0.0
tot_rid = float(latest_rt[rt_prog_col]) if latest_rt is not None and rt_prog_col else 0.0
zt_val  = float(latest_dc[dc_zt_col])   if latest_dc is not None and dc_zt_col else 0.0

fid_pct_raw = float(latest_dc[dc_fid_pct_col]) if latest_dc is not None and dc_fid_pct_col else 0.0
zt_pct_raw  = float(latest_dc[dc_zt_pct_col])  if latest_dc is not None and dc_zt_pct_col else 0.0
fid_pct_str = f"{fid_pct_raw:.2f}%"       if fid_pct_raw > 1 else f"{fid_pct_raw*100:.2f}%"
zt_pct_str  = f"{zt_pct_raw:.2f}%"        if zt_pct_raw  > 1 else f"{zt_pct_raw*100:.2f}%"

def prev_val(df_sorted, col, fallback=0.0):
    if df_sorted is not None and len(df_sorted) >= 2 and col and col in df_sorted.columns:
        return float(df_sorted.iloc[-2][col])
    return float(fallback)

prev_ft = ft_f.sort_values("Standard_Date") if not ft_f.empty else None
prev_dc = dc_f.sort_values("Standard_Date") if not dc_f.empty else None
prev_rt = rt_f.sort_values("Standard_Date") if not rt_f.empty else None

d_fid     = tot_fid - prev_val(prev_ft, ft_prog_col)
d_rid     = tot_rid - prev_val(prev_rt, rt_prog_col)
d_fid_pct = fid_pct_raw - prev_val(prev_dc, dc_fid_pct_col)

# ── ROW 1: 5 KPI Cards ────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
kpi_defs = [
    (k1, "1. Total In-Process (FID)", "kpi-bg-blue",   f"{tot_fid:,.0f}",       d_fid,         "parcels"),
    (k2, "2. Overall Backlog",        "kpi-bg-red",    f"{tot_fid+tot_rid:,.0f}", d_fid+d_rid,  "FID+RID"),
    (k3, "3. Zone Transfer Parcels",  "kpi-bg-amber",  f"{zt_val:,.0f}",         None,          "transfers"),
    (k4, "4. FID Backlog %",          "kpi-bg-green",  fid_pct_str,              d_fid_pct,     "vs yesterday"),
    (k5, "5. Zone Change %",          "kpi-bg-purple", zt_pct_str,               None,          "of total"),
]
for col_w, label, bg, value, delta, unit in kpi_defs:
    with col_w:
        delta_html = ""
        if delta is not None:
            arrow = "▲" if delta >= 0 else "▼"
            cls   = "up" if delta >= 0 else "down"
            delta_html = f'<div class="kpi-delta {cls}">{arrow} {abs(delta):,.0f} {unit}</div>'
        st.markdown(f"""
        <div class="kpi-card {bg}">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          {delta_html}
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ── ROW 2: Chart 11 (combo) + Chart 6 (region donut) ─────────────────────────
col_combo, col_donut = st.columns([3, 2])

with col_combo:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">11. Date-wise Backlog Progress Tracking (FID)</div>', unsafe_allow_html=True)
    if not ft_f.empty and ft_prog_col:
        ft_add_col = get_col(ft_f, "NEWLY ADDED")
        ft_wrk_col = get_col(ft_f, "WORKED ON")
        ft_cf_col  = get_col(ft_f, "CARRY FORWARD")

        fig11 = go.Figure()
        fig11.add_trace(go.Bar(x=ft_f["Date_Label"], y=ft_f[ft_prog_col],
                               name="Total In Process", marker_color="#2563eb"))
        if ft_add_col:
            fig11.add_trace(go.Bar(x=ft_f["Date_Label"], y=ft_f[ft_add_col],
                                   name="Newly Added", marker_color="#f59e0b"))
        if ft_cf_col:
            fig11.add_trace(go.Bar(x=ft_f["Date_Label"], y=ft_f[ft_cf_col],
                                   name="Carry Forward", marker_color="#8b5cf6"))
        if show_worked and ft_wrk_col:
            fig11.add_trace(go.Scatter(x=ft_f["Date_Label"], y=ft_f[ft_wrk_col],
                                       name="Worked On", mode="lines+markers",
                                       line=dict(color="#10b981", width=3),
                                       marker=dict(size=7, line=dict(color="#fff", width=1.5))))
        apply_theme(fig11, height=330, extra={"barmode": "group"})
        st.plotly_chart(fig11, use_container_width=True)
    else:
        st.info("No FID tracking data for selected period.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_donut:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">6. Region Wise In-Process Parcels</div>', unsafe_allow_html=True)
    # ── FIX 2: Robust ISD/OSD lookup — try direct key then get_col ───────────
    if latest_dc is not None:
        def _safe_num(row, key):
            """Try exact key first, then case-insensitive search."""
            if key in row.index:
                return float(row[key])
            for k in row.index:
                if str(k).strip().upper() == key.upper():
                    return float(row[k])
            return 0.0

        isd_val = _safe_num(latest_dc, "ISD")
        osd_val = _safe_num(latest_dc, "OSD")

        if isd_val + osd_val > 0:
            fig6 = go.Figure(data=[go.Pie(
                labels=["ISD", "OSD"], values=[isd_val, osd_val],
                hole=0.55, marker_colors=[COLOR_ISD, COLOR_OSD],
                textinfo="label+percent", textfont_size=13, pull=[0.04, 0]
            )])
            apply_theme(fig6, height=300,
                        extra={"legend": dict(orientation="h", yanchor="bottom",
                                              y=-0.15, xanchor="center", x=0.5)})
            fig6.add_annotation(
                text=f"<b>{isd_val+osd_val:,.0f}</b><br><span style='font-size:10px'>Total</span>",
                x=0.5, y=0.5, showarrow=False, font=dict(size=15, color="#1e3a5f"), xanchor="center"
            )
            st.plotly_chart(fig6, use_container_width=True)
        else:
            st.info("ISD/OSD columns not found. Check Dashboard_Card sheet column names.")

        # Horizontal bar
        df_region = pd.DataFrame({"Region": ["ISD", "OSD"], "Parcels": [isd_val, osd_val]})
        fig6b = px.bar(df_region, x="Parcels", y="Region", orientation="h",
                       color="Region", color_discrete_map={"ISD": COLOR_ISD, "OSD": COLOR_OSD},
                       text="Parcels")
        fig6b.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        apply_theme(fig6b, height=130,
                    extra={"showlegend": False, "margin": dict(l=10, r=60, t=5, b=5)})
        st.plotly_chart(fig6b, use_container_width=True)
    else:
        st.info("Dashboard_Card data unavailable.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── ROW 3: Chart 7 (FID vs RID backlog bar) + Chart 9 (LMH/FMH details) ──────
col_7, col_9 = st.columns([2, 3])

with col_7:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">7. Backlog — FID vs RID</div>', unsafe_allow_html=True)

    fid_backlog = 0.0
    rid_backlog = 0.0
    if not fr_f.empty:
        fr_latest = fr_f[fr_f["Standard_Date"] == fr_f["Standard_Date"].max()]
        type_col7 = get_col(fr_latest, "TYPE")
        if type_col7 and "LMH" in fr_latest.columns and "FMH" in fr_latest.columns:
            fid_backlog = float(fr_latest[fr_latest[type_col7].astype(str).str.upper() == "FID"][["LMH","FMH"]].sum().sum())
            rid_backlog = float(fr_latest[fr_latest[type_col7].astype(str).str.upper() == "RID"][["LMH","FMH"]].sum().sum())
    if fid_backlog == 0 and rid_backlog == 0:
        fid_backlog = tot_fid
        rid_backlog = tot_rid

    if fid_backlog + rid_backlog > 0:
        fig7 = go.Figure(data=[go.Bar(
            x=["FID Backlog", "RID Backlog"],
            y=[fid_backlog, rid_backlog],
            marker_color=[COLOR_ISD, COLOR_OSD],
            text=[f"{fid_backlog:,.0f}", f"{rid_backlog:,.0f}"],
            textposition="outside",
            textfont=dict(size=13, color="#1e3a5f"),
            width=0.5
        )])
        # ── FIX 3: Do NOT pass yaxis= again here — apply_theme already sets it ─
        apply_theme(fig7, height=300, extra={"showlegend": False})
        st.plotly_chart(fig7, use_container_width=True)
    else:
        st.info("No backlog data found.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_9:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">9. Backlog Details — FID &amp; RID (LMH / FMH)</div>', unsafe_allow_html=True)

    if not fr_f.empty:
        fr_latest = fr_f[fr_f["Standard_Date"] == fr_f["Standard_Date"].max()]
        type_col9 = get_col(fr_latest, "TYPE")
        if type_col9 and "LMH" in fr_latest.columns and "FMH" in fr_latest.columns:
            rows9 = []
            for t in ["FID", "RID"]:
                sub_df = fr_latest[fr_latest[type_col9].astype(str).str.upper() == t]
                rows9.append({"Category": f"{t} LMH", "Count": float(sub_df["LMH"].sum())})
                rows9.append({"Category": f"{t} FMH", "Count": float(sub_df["FMH"].sum())})
                if "SUB" in fr_latest.columns:
                    rows9.append({"Category": f"{t} SUB", "Count": float(sub_df["SUB"].sum())})
            df9 = pd.DataFrame(rows9)
            color_map9 = {
                "FID LMH":"#1d4ed8","FID FMH":"#60a5fa","FID SUB":"#93c5fd",
                "RID LMH":"#b91c1c","RID FMH":"#f87171","RID SUB":"#fca5a5"
            }
            fig9 = go.Figure()
            for _, r in df9.iterrows():
                fig9.add_trace(go.Bar(
                    name=r["Category"], x=[r["Category"]], y=[r["Count"]],
                    marker_color=color_map9.get(r["Category"], "#94a3b8"),
                    text=f"{r['Count']:,.0f}", textposition="outside",
                    textfont=dict(size=12)
                ))
            apply_theme(fig9, height=300, extra={"showlegend": True, "barmode": "group"})
            st.plotly_chart(fig9, use_container_width=True)
        else:
            st.info("Missing TYPE / LMH / FMH columns in FID_RID_Backlog_Details sheet.")
    else:
        st.info("No backlog detail data available.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── ROW 4: Chart 10 (Sort) + Chart 8 (Aging) ─────────────────────────────────
col_sort, col_age = st.columns(2)

with col_sort:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">10. Sort — FID Sort vs RID Sort</div>', unsafe_allow_html=True)
    if not st_det_f.empty:
        st_latest = st_det_f[st_det_f["Standard_Date"] == st_det_f["Standard_Date"].max()]
        type_col10 = get_col(st_latest, "TYPE")
        sort_col10 = get_col(st_latest, "SORT")
        if type_col10 and sort_col10:
            f_sort = float(st_latest[st_latest[type_col10].astype(str).str.upper() == "FID"][sort_col10].sum())
            r_sort = float(st_latest[st_latest[type_col10].astype(str).str.upper() == "RID"][sort_col10].sum())
            fig10 = go.Figure(data=[go.Bar(
                x=["FID Sort", "RID Sort"], y=[f_sort, r_sort],
                marker_color=[COLOR_ISD, COLOR_OSD],
                text=[f"{f_sort:,.0f}", f"{r_sort:,.0f}"],
                textposition="outside", textfont=dict(size=13, color="#1e3a5f"),
                width=0.5
            )])
            apply_theme(fig10, height=300, extra={"showlegend": False})
            st.plotly_chart(fig10, use_container_width=True)
        else:
            st.info("Missing 'Type' or 'Sort' column in Sort Details sheet.")
    else:
        st.info("No sort data available.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_age:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">8. Aging Distribution (%)</div>', unsafe_allow_html=True)
    st.markdown('<div class="aging-note">ISD &amp; SUB = 4 Days+ &nbsp;|&nbsp; OSD = 5 Days+</div>', unsafe_allow_html=True)

    if not ag_f.empty and "Region" in ag_f.columns:
        ag_latest = ag_f[ag_f["Standard_Date"] == ag_f["Standard_Date"].max()]
        AGE_COLS  = [str(i) for i in range(1, 11)] + ["10+"]
        rows_age  = []
        for _, row in ag_latest.iterrows():
            region = str(row.get("Region", "")).strip()
            if region not in aging_region:
                continue
            total = sum(float(row[c]) for c in AGE_COLS if c in ag_latest.columns and pd.notna(row[c]))
            for c in AGE_COLS:
                if c in ag_latest.columns:
                    val = float(row[c])
                    pct = (val / total * 100) if total > 0 else 0
                    rows_age.append({"Region": region, "Age": f"{c}d", "Count": val, "Pct": pct})

        ag_melt = pd.DataFrame(rows_age)
        if not ag_melt.empty:
            fig8 = px.bar(ag_melt, x="Age", y="Pct", color="Region",
                          color_discrete_map={"ISD": COLOR_ISD, "OSD": COLOR_OSD},
                          barmode="group",
                          text=ag_melt["Pct"].apply(lambda x: f"{x:.1f}%"))
            fig8.update_traces(
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Region: %{fullData.name}<br>"
                              "Count: %{customdata[0]:,.0f}<br>Pct: %{y:.1f}%",
                customdata=ag_melt[["Count"]]
            )
            apply_theme(fig8, height=300, extra={"yaxis": dict(**AXIS_STYLE, title="Percentage (%)")})
            st.plotly_chart(fig8, use_container_width=True)
        else:
            st.info("No aging data for selected regions.")
    else:
        st.info("No aging distribution data available.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── ROW 5: FID Backlog Table ──────────────────────────────────────────────────
st.markdown('<div class="chart-card">', unsafe_allow_html=True)
st.markdown('<div class="sec-hdr">11. Date-wise Backlog Progress Tracking — Full Table (FID)</div>', unsafe_allow_html=True)

if not ft_f.empty and ft_prog_col:
    ft_table   = ft_f.sort_values("Standard_Date").copy()
    ft_add_col = get_col(ft_table, "NEWLY ADDED")
    ft_wrk_col = get_col(ft_table, "WORKED ON")
    ft_cf_col  = get_col(ft_table, "CARRY FORWARD")

    col_map = {"Date_Label": "Date"}
    if ft_add_col:  col_map[ft_add_col]  = "Newly Added"
    col_map[ft_prog_col] = "Total In Process (Backlog)"
    if ft_wrk_col:  col_map[ft_wrk_col]  = "Worked On"
    if ft_cf_col:   col_map[ft_cf_col]   = "Carry Forward"

    display_cols = [c for c in col_map if c in ft_table.columns]
    df_show = ft_table[display_cols].rename(columns=col_map)

    headers = "".join(f"<th>{c}</th>" for c in df_show.columns)
    rows_html = ""
    for i, (_, r) in enumerate(df_show.iterrows()):
        is_last = (i == len(df_show) - 1)
        cells = ""
        for j, v in enumerate(r):
            cls = "col-date" if j == 0 else ("col-high" if is_last else "col-num")
            try:
                val = v if j == 0 else f"{int(float(v)):,}"
            except Exception:
                val = "—"
            cells += f"<td class='{cls}'>{val}</td>"
        rows_html += f"<tr>{cells}</tr>"

    st.markdown(f"""
    <div style="overflow-x:auto">
    <table class="styled-table">
      <thead><tr>{headers}</tr></thead>
      <tbody>{rows_html}</tbody>
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
