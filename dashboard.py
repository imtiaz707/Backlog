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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

* { font-family: 'Inter', sans-serif; box-sizing: border-box; }

/* ── App Background ── */
[data-testid="stAppViewContainer"] { background: #F9FAFB; }
[data-testid="stHeader"]           { background: transparent; }
[data-testid="stToolbar"]          { display: none; }
.block-container { padding-top:1.5rem !important; padding-bottom:2rem !important; max-width:98% !important; }

/* ── Streamlit Native Container Styling (Replaces .chart-card) ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;
    border-radius: 4px !important;
    border: 1px solid #E5E7EB !important;
    box-shadow: none !important;
    padding: 0px !important;
    height: 100%; 
}

/* ── Section Headers (Inside Cards) ── */
.sec-hdr {
    font-size: 13px; font-weight: 500; color: #6B7280 !important;
    padding: 12px 16px;
    border-bottom: 1px solid #E5E7EB;
    margin-bottom: 12px;
    display: flex; align-items: center; gap: 6px;
}
.sec-hdr::before {
    content: "ⓘ";
    font-size: 14px; color: #9CA3AF;
}

/* ── HTML KPI Cards (Matched to Image) ── */
.kpi-flat {
    background: #FFFFFF;
    border-radius: 4px;
    border: 1px solid #E5E7EB;
    height: 100%;
    display: flex;
    flex-direction: column;
}
.kpi-flat-header {
    font-size: 12px; font-weight: 500; color: #6B7280;
    padding: 10px 16px;
    border-bottom: 1px solid #E5E7EB;
}
.kpi-flat-body {
    padding: 24px 16px;
    text-align: center;
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}
.kpi-flat-value {
    font-size: 46px; font-weight: 300; line-height: 1;
    color: #374151; margin-bottom: 8px;
}
.kpi-flat-delta {
    font-size: 12px; font-weight: 500; color: #9CA3AF;
}

/* ── Badges ── */
.aging-badge {
    background:#FFFBEB; border:1px solid #FBC02D; border-radius:4px;
    padding:4px 10px; font-size:11px; color:#B45309 !important; font-weight:500;
    margin: 0 16px 12px 16px; display:inline-block;
}

/* ── Tables ── */
.styled-table { width:100%; border-collapse:collapse; font-size:12px; }
.styled-table thead tr { background: #F9FAFB; }
.styled-table th { padding:10px 16px; text-align:left;
                   font-weight:600; font-size:12px; color:#6B7280 !important;
                   border-bottom: 1px solid #E5E7EB; }
.styled-table tbody tr { background: #FFFFFF; border-bottom: 1px solid #E5E7EB; }
.styled-table tbody tr:last-child { background:#F9FAFB; font-weight:600; }
.styled-table td { padding:10px 16px; text-align:left; color:#374151 !important; }

/* ── Overrides ── */
label, .stSelectbox label, .stMultiSelect label {
    color: #374151 !important; font-size: 13px !important; font-weight: 500 !important;
}
[data-testid="stSelectbox"] > div > div {
    background: #FFFFFF !important; border: 1px solid #D1D5DB !important; border-radius: 4px !important;
}
</style>
""", unsafe_allow_html=True)

SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1n9GW1UksZ-jhCQ-zmCqwx4EH20fa-Zm5wA5BiMmdZAE/edit?gid=713116247#gid=713116247"
)

# ── Color Palette Extracted from Uploaded Image ──
C_ISD  = "#FBC02D" # Yellow (Primary)
C_OSD  = "#374151" # Dark Charcoal (Secondary)
C_SUB  = "#9E7A8F" # Muted Plum/Purple (Tertiary)
C_AMB  = "#FBC02D"
C_PUR  = "#9E7A8F"

_AX = dict(
    gridcolor="#F3F4F6", linecolor="#E5E7EB",
    tickcolor="#E5E7EB", showgrid=True,
    tickfont=dict(color="#9CA3AF", size=11),
    title_font=dict(color="#6B7280", size=12),
)
_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#374151", family="Inter, sans-serif", size=11),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#E5E7EB",
                borderwidth=0, font=dict(size=11, color="#6B7280"),
                orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
    margin=dict(l=10, r=10, t=20, b=10),
    xaxis=_AX, yaxis=_AX,
)

def _layout(fig, height=None, extra=None):
    kw = dict(**_BASE)
    if height: kw["height"] = height
    if extra:  kw.update(extra)
    fig.update_layout(**kw)
    return fig

# ── Data Loading & Helper Functions (Unchanged) ──
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
                df[c].astype(str).str.replace(",", "").str.replace("%", ""),
                errors="coerce").fillna(0)
    return df

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
        raw["Date_Label"] = raw["Date"].dt.strftime("%b")
        dc = raw
    except Exception: dc = pd.DataFrame()

    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="FID_Tracking")
        raw.columns = [str(c).strip() for c in raw.columns]
        raw = raw[~raw.iloc[:, 0].astype(str).str.contains("Grand Total|Report Date|nan", case=False, na=True)]
        raw.rename(columns={raw.columns[0]: "Date"}, inplace=True)
        raw["Date"] = _parse_dates(raw["Date"])
        raw = raw.dropna(subset=["Date"])
        raw["Date"] = _to_date(raw["Date"])
        raw = _nums(raw, list(raw.columns[1:]))
        raw["Date_Label"] = raw["Date"].dt.strftime("%b")
        ft = raw
    except Exception: ft = pd.DataFrame()

    try:
        raw = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="FID_RID_Backlog_Details")
        raw.columns = [str(c).strip() for c in raw.columns]
        raw = raw[~raw.iloc[:, 0].astype(str).str.contains("Grand Total|Date|nan", case=False, na=True)]
        raw.rename(columns={raw.columns[0]: "Date"}, inplace=True)
        raw["Date"] = _parse_dates(raw["Date"])
        raw = raw.dropna(subset=["Date"])
        raw["Date"] = _to_date(raw["Date"])
        raw = _nums(raw, list(raw.columns[1:]))
        raw["Date_Label"] = raw["Date"].dt.strftime("%b")
        fr = raw
    except Exception: fr = pd.DataFrame()

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
        raw["Date_Label"] = raw["Date"].dt.strftime("%b")
        ag = raw
    except Exception: ag = pd.DataFrame()

    return dc, ft, fr, ag

with st.spinner("🐝 Loading live data…"):
    dc, ft, fr, ag = load_data()

# ── SINGLE DATE SLICER ────────────────────────────────────────────────────────
fc1, fc2, _sp = st.columns([2, 2, 4])

all_dates_ft = sorted(ft["Date"].dropna().unique()) if not ft.empty else []
all_dates_ag = sorted(ag["Date"].dropna().unique()) if not ag.empty else []
all_dates    = sorted(set(list(all_dates_ft) + list(all_dates_ag)))

if all_dates:
    date_opts = [pd.Timestamp(d).strftime("%d %b %Y") for d in all_dates]
    with fc1:
        sel_di = st.selectbox("Report Date", range(len(date_opts)),
                              format_func=lambda i: date_opts[i],
                              index=len(date_opts) - 1)
    sel_date  = pd.Timestamp(all_dates[sel_di])
    sel_start = sel_date
    sel_end   = sel_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
else:
    sel_date  = pd.Timestamp.now().normalize()
    sel_start = sel_date
    sel_end   = sel_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

with fc2:
    region_filter = st.multiselect("Region", ["ISD", "OSD"], default=["ISD", "OSD"])

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── Computed KPIs ─────────────────────────────────────────────────────────────
def _latest(df):
    if df is None or df.empty: return None
    sub = df[df["Date"] <= sel_end].sort_values("Date")
    return sub.iloc[-1] if not sub.empty else None

lt_dc = _latest(dc)
lt_fr = _latest(fr)

ag_le = ag[ag["Date"] <= sel_end] if not ag.empty else pd.DataFrame()
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
zt_val     = _safe(lt_dc, "Zone Transfer", default=0.0)
dc_tot     = _safe(lt_dc, "Total")
denom      = dc_tot if dc_tot > 0 else tot_fid
fid_pct    = (fid_bl / denom * 100) if denom > 0 else 0.0
zt_pct     = (zt_val / dc_tot * 100) if (zt_val > 0 and dc_tot > 0) else 0.0

# ── ROW 1: 6 Flat White KPI Cards ──────────────────────────────────────────
kc1, kc2, kc3, kc4, kc5, kc6 = st.columns(6)

def _flat_kpi(col, label, value_str, suffix=""):
    col.markdown(f"""
    <div class="kpi-flat">
      <div class="kpi-flat-header">{label}</div>
      <div class="kpi-flat-body">
        <div class="kpi-flat-value">{value_str}</div>
        <div class="kpi-flat-delta">{suffix}</div>
      </div>
    </div>""", unsafe_allow_html=True)

with kc1: _flat_kpi(kc1, "Total In-Process", f"{tot_fid:,.0f}")
with kc2: _flat_kpi(kc2, "Overall Backlog", f"{overall_bl:,.0f}")
with kc3: _flat_kpi(kc3, "Zone Transfer", f"{int(zt_val):,}" if zt_val > 0 else "0")
with kc4: _flat_kpi(kc4, "FID Backlog Rate", f"{fid_pct:.0f}%")
with kc5: _flat_kpi(kc5, "Zone Change Rate", f"{zt_pct:.0f}%")
with kc6:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr" style="margin:0; border:none; padding: 10px 16px;">Backlog Split</div>', unsafe_allow_html=True)
        if (fid_bl + rid_bl) > 0:
            fig_donut = go.Figure(data=[go.Pie(
                labels=["FID", "RID"], values=[fid_bl, rid_bl],
                hole=0.75, marker_colors=[C_ISD, C_OSD],
                textinfo="none",
                hoverinfo="label+percent"
            )])
            fig_donut.add_annotation(
                text=f"<span style='font-size:24px; font-weight:300; color:#374151;'>{fid_bl+rid_bl:,.0f}</span>",
                x=0.5, y=0.5, showarrow=False, xanchor="center",
            )
            _layout(fig_donut, height=110, extra={"margin": dict(l=0,r=0,t=0,b=0)})
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.markdown("<div style='padding:20px;text-align:center;color:#9CA3AF;'>No data</div>", unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── ROW 2: Tracking Charts (Line + Stacked Bar) ──────────────────────────
r2c1, r2c2 = st.columns([1, 1])

with r2c1:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">Backlog Progress Over Time</div>', unsafe_allow_html=True)
        t_start = sel_start - pd.Timedelta(days=30) # Show last 30 days
        t_end   = sel_end
        ft_range = ft[(ft["Date"] >= t_start) & (ft["Date"] <= t_end)].sort_values("Date") if not ft.empty else pd.DataFrame()
        
        if not ft_range.empty and "Total In Progress (Backlog)" in ft_range.columns:
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=ft_range["Date_Label"], y=ft_range["Total In Progress (Backlog)"],
                mode='lines+markers', name="In Process",
                line=dict(color=C_ISD, width=2),
                marker=dict(size=6, color="#FFFFFF", line=dict(width=2, color=C_ISD))
            ))
            _layout(fig_line, height=250, extra={"showlegend": False})
            st.plotly_chart(fig_line, use_container_width=True)
        else: st.info("No tracking data.")

with r2c2:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">Backlog Details (LMH / FMH)</div>', unsafe_allow_html=True)
        if lt_fr is not None:
            detail_rows = [
                ("FID LMH", _safe(lt_fr,"FID LMH ISD"), _safe(lt_fr,"FID LMH SUB"), _safe(lt_fr,"FID LMH OSD")),
                ("RID FMH", _safe(lt_fr,"RID FMH ISD"), _safe(lt_fr,"RID FMH SUB"), _safe(lt_fr,"RID FMH OSD")),
                ("RID LMH", _safe(lt_fr,"RID LMH ISD"), _safe(lt_fr,"RID LMH SUB"), _safe(lt_fr,"RID LMH OSD")),
            ]
            labels, isd_v, sub_v, osd_v = zip(*detail_rows)
            fig_bar = go.Figure()
            for vals, name, color in [(isd_v,"ISD",C_ISD),(sub_v,"SUB",C_SUB),(osd_v,"OSD",C_OSD)]:
                fig_bar.add_trace(go.Bar(
                    name=name, x=labels, y=vals, marker_color=color,
                    text=[f"{v:,.0f}" if v>0 else "" for v in vals], textposition="inside",
                    textfont=dict(color="#FFFFFF", size=10)
                ))
            _layout(fig_bar, height=250, extra={"barmode":"stack"})
            st.plotly_chart(fig_bar, use_container_width=True)
        else: st.info("No detail data.")

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── ROW 3: Aging + Region Bars ────────────────────────────────────────────
r3c1, r3c2 = st.columns([1, 1])

AGE_COLS = [str(i) for i in range(1, 11)] + ["10+"]
ag_f = ag[(ag["Date"] >= sel_start) & (ag["Date"] <= sel_end)].copy() if not ag.empty else pd.DataFrame()
if not ag_f.empty and "Region" in ag_f.columns: ag_f = ag_f[ag_f["Region"].isin(region_filter)]

with r3c1:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">Aging Distribution</div>', unsafe_allow_html=True)
        if not ag_f.empty:
            ag_max = ag_f["Date"].max()
            ag_day_f = ag_f[ag_f["Date"] == ag_max].copy()
            rows8 = []
            for _, row in ag_day_f.iterrows():
                region = str(row.get("Region","")).strip()
                if region not in region_filter: continue
                for c in AGE_COLS:
                    if c in ag_day_f.columns:
                        val = float(row[c]) if pd.notna(row[c]) else 0.0
                        rows8.append({"Region": region, "Age": f"{c}d", "Count": val})
            ag_melt = pd.DataFrame(rows8)
            if not ag_melt.empty:
                fig_age = px.bar(ag_melt, x="Age", y="Count", color="Region", 
                                 color_discrete_map={"ISD": C_ISD, "OSD": C_OSD}, barmode="group")
                _layout(fig_age, height=250)
                st.plotly_chart(fig_age, use_container_width=True)
            else: st.info("No aging data.")
        else: st.info("No aging distribution data available.")

with r3c2:
    with st.container(border=True):
        st.markdown('<div class="sec-hdr">Region Wise In-Process & Sort</div>', unsafe_allow_html=True)
        if tot_fid > 0 and lt_fr is not None:
            fid_sort = _safe(lt_fr, "FID Sort")
            rid_sort = _safe_multi(lt_fr, "RID Sort", "RID LMH Sort")
            
            fig_combo = go.Figure()
            # Region Split
            fig_combo.add_trace(go.Bar(x=["ISD In-Process", "OSD In-Process"], y=[isd_total, osd_total], marker_color=[C_ISD, C_OSD], showlegend=False))
            # Sort Split
            fig_combo.add_trace(go.Bar(x=["FID Sort", "RID Sort"], y=[fid_sort, rid_sort], marker_color=[C_ISD, C_OSD], showlegend=False))
            
            _layout(fig_combo, height=250)
            st.plotly_chart(fig_combo, use_container_width=True)
        else: st.info("No region data.")

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── ROW 4: Table ──────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown('<div class="sec-hdr" style="margin-bottom:0px;">Date-wise Backlog Progress Tracking</div>', unsafe_allow_html=True)
    try: ft_tbl = ft[(ft["Date"] >= t_start) & (ft["Date"] <= t_end)].sort_values("Date", ascending=False).copy() if not ft.empty else pd.DataFrame()
    except Exception: ft_tbl = ft.sort_values("Date", ascending=False).copy() if not ft.empty else pd.DataFrame()

    if not ft_tbl.empty:
        COL_MAP = {"Date_Label": "Date", "Newly Added": "Newly Added", "Total In Progress (Backlog)": "Total In Process", "Worked On": "Worked On", "Carry Forward": "Carry Forward"}
        show_cols = [c for c in COL_MAP if c in ft_tbl.columns]
        df_tbl    = ft_tbl[show_cols].rename(columns=COL_MAP)
        headers   = "".join(f"<th>{c}</th>" for c in df_tbl.columns)
        body      = ""
        for i, (_, r) in enumerate(df_tbl.head(10).iterrows()): # Only show top 10 rows for clean UI
            cells   = ""
            for j, v in enumerate(r):
                try: disp = v if j==0 else (f"{int(float(v)):,}" if float(v)!=0 else "—")
                except: disp = "—"
                cells += f"<td>{disp}</td>"
            body += f"<tr>{cells}</tr>"
        st.markdown(f"""
        <div style="overflow-x:auto;">
        <table class="styled-table" style="margin: 0;">
          <thead><tr>{headers}</tr></thead>
          <tbody>{body}</tbody>
        </table></div>""", unsafe_allow_html=True)
    else: st.info("No tracking data.")
        
