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
[data-testid="stAppViewContainer"] { background: #f0f4f8; }
[data-testid="stHeader"]           { background: transparent; }
[data-testid="stToolbar"]          { display: none; }
[data-testid="stDecoration"]       { display: none; }
.block-container { padding-top:1rem !important; padding-bottom:1rem !important; max-width:100% !important; }

.dash-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
    border-radius: 16px; padding: 18px 28px; margin-bottom: 16px;
}
.dash-title    { color:#fff !important; font-size:26px; font-weight:800; margin:0; }
.dash-subtitle { color:rgba(255,255,255,0.80) !important; font-size:13px; margin-top:4px; }

.kpi-card {
    border-radius: 14px; padding: 18px 20px 14px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.09);
    position: relative; overflow: hidden; min-height: 120px;
}
.kpi-card::after {
    content:''; position:absolute; top:-20px; right:-20px;
    width:90px; height:90px; border-radius:50%; background:rgba(255,255,255,0.30);
}
.kpi-card * { color:#111827 !important; }
.bg-blue   { background:#dbeafe !important; border:2px solid #2563eb; }
.bg-red    { background:#fee2e2 !important; border:2px solid #ef4444; }
.bg-amber  { background:#fef3c7 !important; border:2px solid #d97706; }
.bg-green  { background:#d1fae5 !important; border:2px solid #059669; }
.bg-purple { background:#ede9fe !important; border:2px solid #7c3aed; }

.kpi-label { font-size:11px; font-weight:700; text-transform:uppercase;
             letter-spacing:0.7px; margin-bottom:6px; color:#1e3a5f !important; }
.kpi-value { font-size:30px; font-weight:800; line-height:1.1;
             margin-bottom:6px; color:#111827 !important; }
.kpi-delta { font-size:11px; padding:2px 9px; border-radius:20px;
             display:inline-block; font-weight:600; }
.kpi-delta.up   { color:#065f46 !important; background:rgba(16,185,129,0.20); }
.kpi-delta.down { color:#991b1b !important; background:rgba(239,68,68,0.20); }

.sec-hdr {
    font-size:13px; font-weight:700; color:#1e3a5f !important;
    text-transform:uppercase; letter-spacing:0.6px;
    border-left:4px solid #2563eb;
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
    padding:5px 12px; font-size:11px; color:#92400e !important; font-weight:700;
    display:inline-block; margin-bottom:8px;
}
.styled-table { width:100%; border-collapse:collapse; font-size:12px; }
.styled-table thead tr { background:#1e3a5f; }
.styled-table th { padding:8px 10px; text-align:center;
                   font-weight:700; font-size:11px; color:#ffffff !important; }
.styled-table tbody tr:nth-child(even) { background:#f8fafc; }
.styled-table tbody tr:last-child      { background:#fef9c3; font-weight:700; }
.styled-table td { padding:7px 10px; text-align:center;
                   border-bottom:1px solid #e2e8f0; color:#111827 !important; }
.styled-table .col-date { text-align:left; font-weight:600; color:#1e3a5f !important; }
.styled-table .col-high { color:#dc2626 !important; font-weight:700; }
</style>
""", unsafe_allow_html=True)

SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1n9GW1UksZ-jhCQ-zmCqwx4EH20fa-Zm5wA5BiMmdZAE/edit?gid=713116247#gid=713116247"
)

_AX = dict(
    gridcolor="#e2e8f0", linecolor="#cbd5e1", tickcolor="#94a3b8",
    showgrid=True,
    tickfont=dict(color="#111827", size=11),
    title_font=dict(color="#111827"),
)
_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#111827", family="Inter, sans-serif", size=11),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#e2e8f0",
                borderwidth=1, font=dict(size=11, color="#111827")),
    hoverlabel=dict(bgcolor="#1e293b", bordercolor="#3b82f6", font_color="#f1f5f9"),
    margin=dict(l=10, r=10, t=36, b=10),
    xaxis=_AX, yaxis=_AX,
)

def _layout(fig, height=None, extra=None):
    kw = dict(**_BASE)
    if height: kw["height"] = height
    if extra:  kw.update(extra)
    fig.update_layout(**kw)
    return fig

C_ISD = "#1d4ed8"
C_OSD = "#ef4444"
C_SUB = "#10b981"
C_AMB = "#f59e0b"
C_PUR = "#8b5cf6"

# ── Helpers ───────────────────────────────────────────────────────────────────
def _safe(row, col, default=0.0):
    """Safely extract a numeric value from a pandas Series or dict row."""
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
    """Try multiple column names and return the first non-zero match."""
    for col in cols:
        v = _safe(row, col, default=None)
        if v is not None and v != 0.0:
            return v
    return default

def _find_col(row, *keywords, exclude=None):
    """
    Fuzzy-find a column whose name contains ALL keywords (case-insensitive).
    Optionally exclude columns containing any of the exclude strings.
    Returns the numeric value of the first match, or 0.0.
    """
    if row is None:
        return 0.0
    exclude = exclude or []
    index = row.keys() if isinstance(row, dict) else row.index
    for col in index:
        col_lower = str(col).lower()
        if all(kw.lower() in col_lower for kw in keywords):
            if not any(ex.lower() in col_lower for ex in exclude):
                v = _safe(row, col, default=0.0)
                if v != 0.0:
                    return v
    return 0.0

def _fix_year(s):
    """Replace year < 2000 with current year (handles date strings with no year)."""
    cy = pd.Timestamp.now().year
    bad = s.dt.year < 2000
    if bad.any():
        s = s.copy()
        s[bad] = s[bad].apply(lambda t: t.replace(year=cy) if pd.notna(t) else t)
    return s

def _parse_dates(col):
    """Parse dates and fix missing years."""
    return _fix_year(
        pd.to_datetime(col.astype(str).str.strip(), dayfirst=True, errors="coerce")
    )

def _to_date(ts_series):
    """Normalize timestamps to date-only (midnight)."""
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

    # ── Dashboard_Card ────────────────────────────────────────────────────────
    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Dashboard_Card", header=None)
        raw.columns = [str(c).strip() for c in raw.iloc[1]]
        raw = raw.iloc[2:].reset_index(drop=True)
        raw = raw[~raw["Date"].astype(str).str.contains(
            "Grand Total|Date|nan|Backlog|ISD Backlog", case=False, na=True
        )]
        raw["Date"] = _parse_dates(raw["Date"])
        raw = raw.dropna(subset=["Date"])
        raw["Date"] = _to_date(raw["Date"])
        # Numeric-ify all columns except Date
        num_cols = [c for c in raw.columns if c != "Date"]
        raw = _nums(raw, num_cols)
        raw["Date_Label"] = raw["Date"].dt.strftime("%d %b")
        dc = raw
    except Exception as e:
        st.warning(f"Dashboard_Card error: {e}")
        dc = pd.DataFrame()

    # ── FID_Tracking ──────────────────────────────────────────────────────────
    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="FID_Tracking")
        raw.columns = [str(c).strip() for c in raw.columns]
        raw = raw[~raw.iloc[:, 0].astype(str).str.contains(
            "Grand Total|Report Date|nan", case=False, na=True
        )]
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

    # ── FID_RID_Backlog_Details ───────────────────────────────────────────────
    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="FID_RID_Backlog_Details")
        raw.columns = [str(c).strip() for c in raw.columns]
        raw = raw[~raw.iloc[:, 0].astype(str).str.contains(
            "Grand Total|Date|nan", case=False, na=True
        )]
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

    # ── Aging_Distribution ────────────────────────────────────────────────────
    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Aging_Distribution")
        raw = raw.iloc[:, :14]
        raw.columns = ["Date", "Region"] + [str(i) for i in range(1, 11)] + ["10+", "Total"]
        raw = raw[~raw["Date"].astype(str).str.contains(
            "Grand Total|Report Date|nan", case=False, na=True
        )]
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
        si = st.selectbox("📅 From Date", range(len(date_opts)),
                          format_func=lambda i: date_opts[i], index=0)
    with fc2:
        ei = st.selectbox("📅 To Date", range(len(date_opts)),
                          format_func=lambda i: date_opts[i], index=len(date_opts) - 1)
    if ei < si:
        ei = si
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
    if df is None or df.empty:
        return pd.DataFrame()
    mask = (df["Date"] >= sel_start) & (df["Date"] <= sel_end)
    out  = df[mask].copy()
    if region_col and region_filter and region_col in out.columns:
        out = out[out[region_col].isin(region_filter)]
    return out

def _latest(df):
    """Return the most recent row at or before sel_end."""
    if df is None or df.empty:
        return None
    sub = df[df["Date"] <= sel_end].sort_values("Date")
    return sub.iloc[-1] if not sub.empty else None

def _prev(df):
    """Return the second-most-recent row (for delta calculation)."""
    if df is None or df.empty:
        return None
    sub = df[df["Date"] <= sel_end].sort_values("Date")
    return sub.iloc[-2] if len(sub) >= 2 else None

ft_f = _filt(ft)
dc_f = _filt(dc)
fr_f = _filt(fr)
ag_f = _filt(ag, "Region")

lt_dc = _latest(dc)
lt_fr = _latest(fr)

# ── DEBUG (uncomment to inspect exact column names from Dashboard_Card) ───────
# if lt_dc is not None:
#     with st.expander("🔍 Debug — Dashboard_Card columns & values"):
#         st.write(dict(lt_dc))

# ── KPI 1: Total In-Process (FID) from Aging_Distribution ─────────────────────
ag_le = ag[ag["Date"] <= sel_end] if not ag.empty else ag
if not ag_le.empty:
    ag_last_date = ag_le["Date"].max()
    ag_day       = ag_le[ag_le["Date"] == ag_last_date]
    isd_total    = ag_day[ag_day["Region"] == "ISD"]["Total"].sum()
    osd_total    = ag_day[ag_day["Region"] == "OSD"]["Total"].sum()
    tot_fid      = isd_total + osd_total
else:
    isd_total = osd_total = tot_fid = 0.0

# ── KPI 2: Overall Backlog (FID Backlog + RID Backlog) ────────────────────────
fid_bl     = _safe(lt_fr, "FID Backlog")
rid_bl     = _safe(lt_fr, "RID Backlog")
overall_bl = fid_bl + rid_bl

# ── KPI 3: Zone Transfer Parcels ──────────────────────────────────────────────
# Directly fetch the "Zone Transfer" column from the Dashboard_Card
zt_val = _safe(lt_dc, "Zone Transfer", default=0.0)
# ── KPI 4: FID Backlog % ──────────────────────────────────────────────────────
dc_total_val = _safe(lt_dc, "Total")
denom        = dc_total_val if dc_total_val > 0 else tot_fid
fid_pct      = (fid_bl / denom * 100) if denom > 0 else 0.0
# ── KPI 5: Zone Change % = Zone Transfer / Total ──────────────────────────────
# Formula: (Zone Transfer / Total) * 100
if zt_val > 0 and dc_total_val > 0:
    zt_pct = (zt_val / dc_total_val) * 100
else:
    zt_pct = 0.0
# ── KPI display ───────────────────────────────────────────────────────────────


# ── Deltas ────────────────────────────────────────────────────────────────────
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
        d_color = "#065f46" if delta >= 0 else "#991b1b"
        d_bg    = "rgba(16,185,129,0.20)" if delta >= 0 else "rgba(239,68,68,0.20)"
        dh = (f'<div style="font-size:11px;padding:2px 9px;border-radius:20px;'
              f'display:inline-block;font-weight:600;color:{d_color} !important;'
              f'background:{d_bg};">'
              f'{arr} {abs(delta):,.2f} {unit}</div>')
    sub_html = (f'<div style="font-size:10px;color:#374151 !important;margin-top:3px;">{sub}</div>'
                if sub else "")
    col_w.markdown(f"""
    <div class="kpi-card {bg}">
      <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.7px;
                  margin-bottom:6px;color:#1e3a5f !important;">{label}</div>
      <div style="font-size:30px;font-weight:800;line-height:1.1;margin-bottom:6px;
                  color:#111827 !important;">{value_str}</div>
      {dh}{sub_html}
    </div>""", unsafe_allow_html=True)

# Zone Transfer display: show value if found, else "0"
zt_display = f"{int(zt_val):,}" if zt_val > 0 else "0"

_kpi(c1, "1. Total In-Process (FID)", "bg-blue",   f"{tot_fid:,.0f}",    d_fid,   "vs prev day")
_kpi(c2, "2. Overall Backlog",         "bg-red",    f"{overall_bl:,.0f}", d_bl,    "FID+RID")
_kpi(c3, "3. Zone Transfer Parcels",   "bg-amber",  zt_display,           None)
_kpi(c4, "4. FID Backlog %",           "bg-green",  f"{fid_pct:.2f}%",    -d_fpct, "pp vs prev")
_kpi(c5, "5. Zone Change %",           "bg-purple", f"{zt_pct:.2f}%",     None)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ── ROW 2: Chart 11 (FID Tracking combo) + Chart 6 (Region donut/bar) ─────────
col_l, col_r = st.columns([3, 2])

with col_l:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">11. Date-wise Backlog Progress Tracking (FID)</div>',
                unsafe_allow_html=True)
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
                                       line=dict(color="#10b981", width=3),
                                       marker=dict(size=7, line=dict(color="#fff", width=1.5))))
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
            hole=0.55, marker_colors=[C_ISD, C_OSD],
            textinfo="label+percent",
            textfont=dict(size=12, color="#111827"), pull=[0.04, 0],
        )])
        fig_d.add_annotation(
            text=f"<b>{tot_fid:,.0f}</b><br><span style='font-size:10px'>Total</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#111827"), xanchor="center",
        )
        _layout(fig_d, height=240,
                extra={"legend": dict(orientation="h", yanchor="bottom", y=-0.18,
                                      xanchor="center", x=0.5,
                                      font=dict(color="#111827"))})
        st.plotly_chart(fig_d, use_container_width=True)

        df_reg = pd.DataFrame({"Region": ["ISD", "OSD"], "Parcels": [isd_total, osd_total]})
        fig_rb = px.bar(df_reg, x="Parcels", y="Region", orientation="h",
                        color="Region", color_discrete_map={"ISD": C_ISD, "OSD": C_OSD},
                        text="Parcels")
        fig_rb.update_traces(texttemplate="%{text:,.0f}", textposition="outside",
                             textfont=dict(color="#111827"))
        _layout(fig_rb, height=130,
                extra={"showlegend": False, "margin": dict(l=10, r=90, t=5, b=5)})
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
            textposition="outside", textfont=dict(size=13, color="#111827"),
            width=0.5,
        )])
        _layout(fig7, height=300, extra={"showlegend": False})
        st.plotly_chart(fig7, use_container_width=True)
    else:
        st.info("No FID/RID backlog data for selected period.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_r3:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">9. Backlog Details — FID &amp; RID (LMH / FMH)</div>',
                unsafe_allow_html=True)
    if lt_fr is not None:
        detail_rows = [
            ("FID LMH",
             _safe(lt_fr, "FID LMH ISD"), _safe(lt_fr, "FID LMH SUB"), _safe(lt_fr, "FID LMH OSD"),
             _safe(lt_fr, "FID LMH Total")),
            ("FID FMH",
             _safe(lt_fr, "FID FMH"), 0, 0,
             _safe(lt_fr, "FID FMH")),
            ("RID FMH",
             _safe(lt_fr, "RID FMH ISD"), _safe(lt_fr, "RID FMH SUB"), _safe(lt_fr, "RID FMH OSD"),
             _safe(lt_fr, "RID FMH ISD") + _safe(lt_fr, "RID FMH SUB") + _safe(lt_fr, "RID FMH OSD")),
            ("RID LMH",
             _safe(lt_fr, "RID LMH ISD"), _safe(lt_fr, "RID LMH SUB"), _safe(lt_fr, "RID LMH OSD"),
             _safe(lt_fr, "RID LMH ISD") + _safe(lt_fr, "RID LMH SUB") + _safe(lt_fr, "RID LMH OSD")),
        ]
        labels = [r[0] for r in detail_rows]
        isd_v  = [r[1] for r in detail_rows]
        sub_v  = [r[2] for r in detail_rows]
        osd_v  = [r[3] for r in detail_rows]
        tots   = [r[4] for r in detail_rows]

        fig9 = go.Figure()
        for vals, name, color in [(isd_v, "ISD", C_ISD), (sub_v, "SUB", C_SUB), (osd_v, "OSD", C_OSD)]:
            fig9.add_trace(go.Bar(
                name=name, y=labels, x=vals, orientation="h",
                marker_color=color,
                text=[f"{v:,.0f}" if v > 0 else "" for v in vals],
                textposition="inside", insidetextanchor="middle",
                textfont=dict(color="#ffffff", size=11),
            ))
        for lbl, tot in zip(labels, tots):
            if tot > 0:
                fig9.add_annotation(x=tot, y=lbl, text=f"  <b>{tot:,.0f}</b>",
                                    showarrow=False, xanchor="left",
                                    font=dict(size=12, color="#111827"))
        _layout(fig9, height=320, extra={
            "barmode": "stack",
            "xaxis": dict(**_AX, title="Count"),
            "yaxis": dict(**_AX, autorange="reversed"),
        })
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
            x=["FID Sort", "RID Sort"],
            y=[fid_sort, rid_sort],
            marker_color=[C_ISD, C_OSD],
            text=[f"{fid_sort:,.0f}", f"{rid_sort:,.0f}"],
            textposition="outside",
            textfont=dict(size=13, color="#111827"),
            width=0.5,
        )])
        _layout(fig10, height=300, extra={"showlegend": False})
        st.plotly_chart(fig10, use_container_width=True)
    else:
        st.info("No sort data for selected period.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_r4:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">8. Aging Distribution</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="aging-badge">ISD &amp; SUB = 4 Days+ &nbsp;|&nbsp; OSD = 5 Days+</div>',
        unsafe_allow_html=True,
    )
    AGE_COLS = [str(i) for i in range(1, 11)] + ["10+"]

    if not ag_f.empty and "Region" in ag_f.columns:
        ag_max   = ag_f["Date"].max()
        ag_day_f = ag_f[ag_f["Date"] == ag_max].copy()

        rows8 = []
        for _, row in ag_day_f.iterrows():
            region = str(row.get("Region", "")).strip()
            if region not in region_filter:
                continue
            total = float(row.get("Total", 0) or 0)
            if total == 0:
                total = sum(float(row[c]) for c in AGE_COLS
                            if c in ag_day_f.columns and pd.notna(row[c]))
            for c in AGE_COLS:
                if c in ag_day_f.columns:
                    val = float(row[c]) if pd.notna(row[c]) else 0.0
                    pct = val / total * 100 if total > 0 else 0.0
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
                customdata=ag_melt[["Count", "Region"]],
                hovertemplate=(
                    "<b>%{x}</b><br>Region: %{customdata[1]}"
                    "<br>Count: %{customdata[0]:,.0f}<br>Pct: %{y:.1f}%"
                ),
            )
            _layout(fig8, height=300,
                    extra={"yaxis": dict(**_AX, title="Percentage (%)")})
            st.plotly_chart(fig8, use_container_width=True)

            # Aging count table
            st.markdown("**Aging Count &amp; % by Region**", unsafe_allow_html=True)
            isd_row   = ag_day_f[ag_day_f["Region"] == "ISD"].iloc[0] if "ISD" in ag_day_f["Region"].values else None
            osd_row   = ag_day_f[ag_day_f["Region"] == "OSD"].iloc[0] if "OSD" in ag_day_f["Region"].values else None
            isd_tot_v = float(isd_row["Total"]) if isd_row is not None else 0
            osd_tot_v = float(osd_row["Total"]) if osd_row is not None else 0

            th = "<th>Days</th>"
            if isd_row is not None: th += "<th>ISD Count</th><th>ISD %</th>"
            if osd_row is not None: th += "<th>OSD Count</th><th>OSD %</th>"
            body_rows = ""
            for c in AGE_COLS:
                if c not in ag_day_f.columns:
                    continue
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
            body_rows += f"<tr style='background:#fef9c3;font-weight:700'>{td_tot}</tr>"

            st.markdown(f"""
            <div style="overflow-x:auto;max-height:240px;overflow-y:auto">
            <table class="styled-table">
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
st.markdown(
    '<div class="sec-hdr">11. Date-wise Backlog Progress Tracking — Full Table (FID)</div>',
    unsafe_allow_html=True,
)
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
            try:
                disp = v if j == 0 else (f"{int(float(v)):,}" if float(v) != 0 else "—")
            except Exception:
                disp = "—"
            cells += f"<td class='{cls}'>{disp}</td>"
        body += f"<tr>{cells}</tr>"

    st.markdown(f"""
    <div style="overflow-x:auto">
    <table class="styled-table">
      <thead><tr>{headers}</tr></thead>
      <tbody>{body}</tbody>
    </table></div>""", unsafe_allow_html=True)
else:
    st.info("No FID tracking data to display.")
st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;color:#64748b;font-size:11px;padding:16px 0 6px;">
  🐝 Carrybee Delivery Intelligence &nbsp;·&nbsp;
  Data refreshes every 10 min &nbsp;·&nbsp; Powered by Google Sheets
</div>
""", unsafe_allow_html=True)
