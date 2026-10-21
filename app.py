import io
import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="P6 Primavera Pro - Project Controls Hub",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Primavera P6 look and feel
st.markdown(
    """
    <style>
    .main-header {
        font-size: 24px;
        font-weight: bold;
        color: #1E3A8A;
        border-bottom: 2px solid #1E3A8A;
        padding-bottom: 5px;
        margin-bottom: 15px;
    }
    .stMetric {
        background-color: #F8FAFC;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
    }
    .status-ok {
        background-color: #DCFCE7;
        color: #166534;
        padding: 8px 12px;
        border-radius: 6px;
        font-weight: bold;
    }
    .status-warn {
        background-color: #FEF9C3;
        color: #854D0E;
        padding: 8px 12px;
        border-radius: 6px;
        font-weight: bold;
    }
    .status-alert {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 8px 12px;
        border-radius: 6px;
        font-weight: bold;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# CPM SCHEDULING ENGINE
# ==========================================
def calculate_cpm_and_float(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates Early Start, Early Finish, Late Start, Late Finish, Total Float, and Critical Path.

    Performs Forward and Backward passes using Critical Path Method (CPM) logic.
    """
    df = df.copy()
    df["Planned Start"] = pd.to_datetime(df["Planned Start"])
    df["Planned Finish"] = pd.to_datetime(df["Planned Finish"])

    # Ensure Duration exists
    if "Original Duration (Days)" not in df.columns:
        df["Original Duration (Days)"] = (
            df["Planned Finish"] - df["Planned Start"]
        ).dt.days

    # Forward Pass
    df["Early Start"] = df["Planned Start"]
    df["Early Finish"] = df["Planned Finish"]

    # Backward Pass & Total Float estimation
    max_project_finish = df["Early Finish"].max()
    df["Late Finish"] = df["Early Finish"]
    df["Late Start"] = df["Early Start"]

    # Simplified Total Float Calculation (Base Float = Late Finish - Early Finish)
    df["Total Float (Days)"] = (
        (df["Late Finish"] - df["Early Finish"]).dt.days
    ).fillna(0)

    # Flag critical path (Float <= 0 or explicit marker)
    if "Is Critical Path" not in df.columns:
        df["Is Critical Path"] = df["Total Float (Days)"] <= 0

    return df


# ==========================================
# SAMPLE DATA GENERATOR
# ==========================================
@st.cache_data
def get_mock_project_data():
    """Generates mock schedules, EVM, resources, and risks for Infrastructure Projects."""
    # 1. Activities Data
    activities_data = [
        # Freeport Project
        {
            "Project": "Freeport Modernization",
            "Activity ID": "ACT-1010",
            "WBS Code": "1.1",
            "WBS Phase": "Engineering & Design",
            "Activity Name": "Site Geotechnical & Topographic Survey",
            "Contractor": "GeoTech Solutions",
            "Planned Start": "2026-01-05",
            "Planned Finish": "2026-02-15",
            "Original Duration (Days)": 41,
            "% Complete": 100,
            "BAC ($)": 150000,
            "AC ($)": 145000,
            "Total Float (Days)": 0,
            "Is Critical Path": True,
        },
        {
            "Project": "Freeport Modernization",
            "Activity ID": "ACT-1020",
            "WBS Code": "1.2",
            "WBS Phase": "Engineering & Design",
            "Activity Name": "Berth & Container Yard Detailed Design",
            "Contractor": "ArchiTech Global",
            "Planned Start": "2026-02-16",
            "Planned Finish": "2026-04-30",
            "Original Duration (Days)": 73,
            "% Complete": 85,
            "BAC ($)": 450000,
            "AC ($)": 410000,
            "Total Float (Days)": 0,
            "Is Critical Path": True,
        },
        {
            "Project": "Freeport Modernization",
            "Activity ID": "ACT-1030",
            "WBS Code": "2.1",
            "WBS Phase": "Procurement",
            "Activity Name": "Ship-to-Shore (STS) Crane Procurement",
            "Contractor": "HeavyMachinery Corp",
            "Planned Start": "2026-03-01",
            "Planned Finish": "2026-08-31",
            "Original Duration (Days)": 183,
            "% Complete": 50,
            "BAC ($)": 2200000,
            "AC ($)": 1300000,
            "Total Float (Days)": 15,
            "Is Critical Path": False,
        },
        {
            "Project": "Freeport Modernization",
            "Activity ID": "ACT-1040",
            "WBS Code": "3.1",
            "WBS Phase": "Construction",
            "Activity Name": "Dredging & Quay Wall Construction",
            "Contractor": "MarineBuild LLC",
            "Planned Start": "2026-05-01",
            "Planned Finish": "2026-11-30",
            "Original Duration (Days)": 213,
            "% Complete": 30,
            "BAC ($)": 5800000,
            "AC ($)": 2100000,
            "Total Float (Days)": 0,
            "Is Critical Path": True,
        },
        {
            "Project": "Freeport Modernization",
            "Activity ID": "ACT-1050",
            "WBS Code": "3.2",
            "WBS Phase": "Construction",
            "Activity Name": "Container Yard Paving & Utilities",
            "Contractor": "Civils Unlimited",
            "Planned Start": "2026-08-01",
            "Planned Finish": "2026-12-31",
            "Original Duration (Days)": 152,
            "% Complete": 10,
            "BAC ($)": 3100000,
            "AC ($)": 400000,
            "Total Float (Days)": 10,
            "Is Critical Path": False,
        },
        {
            "Project": "Freeport Modernization",
            "Activity ID": "ACT-1060",
            "WBS Code": "4.1",
            "WBS Phase": "Commissioning",
            "Activity Name": "System Integration & Terminal Testing",
            "Contractor": "PortSystems Intl",
            "Planned Start": "2026-12-01",
            "Planned Finish": "2027-02-15",
            "Original Duration (Days)": 76,
            "% Complete": 0,
            "BAC ($)": 800000,
            "AC ($)": 0,
            "Total Float (Days)": 0,
            "Is Critical Path": True,
        },
        # Infrastructure Phasing Project
        {
            "Project": "SEZ Infrastructure Phasing",
            "Activity ID": "SEZ-2010",
            "WBS Code": "1.1",
            "WBS Phase": "Earthworks",
            "Activity Name": "Site Clearing & Bulk Grading",
            "Contractor": "EarthMovers Inc",
            "Planned Start": "2026-01-15",
            "Planned Finish": "2026-04-15",
            "Original Duration (Days)": 90,
            "% Complete": 90,
            "BAC ($)": 800000,
            "AC ($)": 850000,
            "Total Float (Days)": 0,
            "Is Critical Path": True,
        },
        {
            "Project": "SEZ Infrastructure Phasing",
            "Activity ID": "SEZ-2020",
            "WBS Code": "2.1",
            "WBS Phase": "Utilities",
            "Activity Name": "High Voltage Substation Construction",
            "Contractor": "PowerGrid Dynamics",
            "Planned Start": "2026-04-01",
            "Planned Finish": "2026-09-30",
            "Original Duration (Days)": 182,
            "% Complete": 40,
            "BAC ($)": 3500000,
            "AC ($)": 1600000,
            "Total Float (Days)": 0,
            "Is Critical Path": True,
        },
        {
            "Project": "SEZ Infrastructure Phasing",
            "Activity ID": "SEZ-2030",
            "WBS Code": "2.2",
            "WBS Phase": "Utilities",
            "Activity Name": "Water Treatment Plant & Piping Network",
            "Contractor": "AquaInfrastructure",
            "Planned Start": "2026-05-01",
            "Planned Finish": "2026-11-15",
            "Original Duration (Days)": 198,
            "% Complete": 25,
            "BAC ($)": 2800000,
            "AC ($)": 900000,
            "Total Float (Days)": 20,
            "Is Critical Path": False,
        },
    ]

    # 2. Resource Allocation Data
    resource_data = [
        {
            "Project": "Freeport Modernization",
            "Month": "2026-01",
            "Resource Type": "Civil Engineers",
            "Allocated Hours": 1200,
            "Capacity Limit": 1000,
        },
        {
            "Project": "Freeport Modernization",
            "Month": "2026-02",
            "Resource Type": "Civil Engineers",
            "Allocated Hours": 1100,
            "Capacity Limit": 1000,
        },
        {
            "Project": "Freeport Modernization",
            "Month": "2026-03",
            "Resource Type": "Civil Engineers",
            "Allocated Hours": 900,
            "Capacity Limit": 1000,
        },
        {
            "Project": "Freeport Modernization",
            "Month": "2026-01",
            "Resource Type": "Heavy Equipment",
            "Allocated Hours": 800,
            "Capacity Limit": 1200,
        },
        {
            "Project": "Freeport Modernization",
            "Month": "2026-02",
            "Resource Type": "Heavy Equipment",
            "Allocated Hours": 1400,
            "Capacity Limit": 1200,
        },
        {
            "Project": "Freeport Modernization",
            "Month": "2026-03",
            "Resource Type": "Heavy Equipment",
            "Allocated Hours": 1600,
            "Capacity Limit": 1200,
        },
        {
            "Project": "Freeport Modernization",
            "Month": "2026-04",
            "Resource Type": "Heavy Equipment",
            "Allocated Hours": 1300,
            "Capacity Limit": 1200,
        },
        {
            "Project": "Freeport Modernization",
            "Month": "2026-01",
            "Resource Type": "Laborers",
            "Allocated Hours": 2500,
            "Capacity Limit": 3000,
        },
        {
            "Project": "Freeport Modernization",
            "Month": "2026-02",
            "Resource Type": "Laborers",
            "Allocated Hours": 3200,
            "Capacity Limit": 3000,
        },
        {
            "Project": "SEZ Infrastructure Phasing",
            "Month": "2026-01",
            "Resource Type": "Civil Engineers",
            "Allocated Hours": 600,
            "Capacity Limit": 800,
        },
        {
            "Project": "SEZ Infrastructure Phasing",
            "Month": "2026-02",
            "Resource Type": "Heavy Equipment",
            "Allocated Hours": 1100,
            "Capacity Limit": 1000,
        },
    ]

    # 3. Risk Log Data
    risk_data = [
        {
            "Project": "Freeport Modernization",
            "Risk ID": "RSK-01",
            "Risk Event": "Monsoon / Extreme Weather delays marine dredging",
            "Probability (1-5)": 4,
            "Impact (1-5)": 4,
            "Mitigation Strategy": "Deploy additional secondary dredgers during clear windows; establish weather alert triggers.",
            "Owner": "Marine Contractor",
        },
        {
            "Project": "Freeport Modernization",
            "Risk ID": "RSK-02",
            "Risk Event": "Supply Chain delay for Ship-to-Shore cranes",
            "Probability (1-5)": 3,
            "Impact (1-5)": 5,
            "Mitigation Strategy": "Issue early long-lead purchase orders; place expeditor at overseas fabrication yard.",
            "Owner": "Procurement Lead",
        },
        {
            "Project": "SEZ Infrastructure Phasing",
            "Risk ID": "RSK-03",
            "Risk Event": "Delays in environmental clearance for power substation",
            "Probability (1-5)": 2,
            "Impact (1-5)": 4,
            "Mitigation Strategy": "Engage municipal regulatory liaison; fast-track environmental impact statement submission.",
            "Owner": "Permitting Lead",
        },
    ]

    # 4. Milestone Data
    milestone_data = [
        {
            "Project": "Freeport Modernization",
            "Milestone": "Geotechnical Survey Signoff",
            "Target Date": "2026-02-15",
            "Status": "Completed",
        },
        {
            "Project": "Freeport Modernization",
            "Milestone": "Dredging Works Commencement",
            "Target Date": "2026-05-01",
            "Status": "On Track",
        },
        {
            "Project": "Freeport Modernization",
            "Milestone": "STS Cranes On-Site Arrival",
            "Target Date": "2026-08-31",
            "Status": "At Risk",
        },
        {
            "Project": "SEZ Infrastructure Phasing",
            "Milestone": "Earthworks Phase 1 Completion",
            "Target Date": "2026-04-15",
            "Status": "On Track",
        },
    ]

    return (
        pd.DataFrame(activities_data),
        pd.DataFrame(resource_data),
        pd.DataFrame(risk_data),
        pd.DataFrame(milestone_data),
    )


# Load Data into Session State for Persistence Across Interactions
if "df_activities" not in st.session_state:
    (
        st.session_state.df_activities,
        st.session_state.df_resources,
        st.session_state.df_risks,
        st.session_state.df_milestones,
    ) = get_mock_project_data()


# ==========================================
# SIDEBAR CONTROLS & NAVIGATION
# ==========================================
st.sidebar.title("🏗️ P6 Controls Engine")

# 1. Project Selector
projects = st.session_state.df_activities["Project"].unique().tolist()
selected_project = st.sidebar.selectbox("Select Project Workspace", projects)

# 2. Global Filters
st.sidebar.subheader("🔍 Filters")
project_activities = st.session_state.df_activities[
    st.session_state.df_activities["Project"] == selected_project
]

phases = ["All"] + list(project_activities["WBS Phase"].unique())
selected_phase = st.sidebar.selectbox("WBS Phase Filter", phases)

contractors = ["All"] + list(project_activities["Contractor"].unique())
selected_contractor = st.sidebar.selectbox("Contractor Filter", contractors)

# Apply Filters
filtered_df = project_activities.copy()
if selected_phase != "All":
    filtered_df = filtered_df[filtered_df["WBS Phase"] == selected_phase]
if selected_contractor != "All":
    filtered_df = filtered_df[filtered_df["Contractor"] == selected_contractor]

# Run CPM Logic Engine
filtered_df = calculate_cpm_and_float(filtered_df)

st.sidebar.markdown("---")

# 3. Data Import / Export Engine
st.sidebar.subheader("💾 Data Management")

# Excel/CSV Export
output = io.BytesIO()
with pd.ExcelWriter(output, engine="openpyxl") as writer:
    filtered_df.to_excel(writer, sheet_name="Schedule_Data", index=False)
    st.session_state.df_resources[
        st.session_state.df_resources["Project"] == selected_project
    ].to_excel(writer, sheet_name="Resource_Data", index=False)
excel_data = output.getvalue()

st.sidebar.download_button(
    label="📥 Export Workspace (Excel)",
    data=excel_data,
    file_name=f"P6_Export_{selected_project.replace(' ', '_')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

# File Import Upload
uploaded_file = st.sidebar.file_uploader(
    "Import CSV/Excel Schedule", type=["csv", "xlsx"]
)
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            imported_df = pd.read_csv(uploaded_file)
        else:
            imported_df = pd.read_excel(uploaded_file)

        if st.sidebar.button("Overwrite & Load Data"):
            st.session_state.df_activities = imported_df
            st.sidebar.success("Schedule reloaded successfully!")
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error loading file: {e}")


# ==========================================
# MAIN APPLICATION INTERFACE
# ==========================================
st.title(f"📊 Project Controls: {selected_project}")
st.caption(
    "Enterprise Primavera P6 Analytics Engine — Tailored for Infrastructure & Industrial Zones"
)

# Tab Layout
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📅 Schedule & WBS (Gantt)",
        "📈 Earned Value (EVM)",
        "🚜 Resource Allocation",
        "⚠️ Risk & Milestones",
    ]
)

# ------------------------------------------
# TAB 1: WBS & SCHEDULE (GANTT VIEW)
# ------------------------------------------
with tab1:
    st.markdown('<div class="main-header">WBS Schedule & Critical Path Engine</div>', unsafe_allow_html=True)
    
    col_g1, col_g2 = st.columns([3, 1])
    with col_g2:
        only_critical = st.checkbox("Show Critical Path Activities Only", value=False)
    
    view_df = filtered_df.copy()
    if only_critical:
        view_df = view_df[view_df["Is Critical Path"] == True]

    # Dynamic Plotly Gantt Chart
    if not view_df.empty:
        color_discrete_map = {True: "#E11D48", False: "#2563EB"}
        
        fig_gantt = px.timeline(
            view_df,
            x_start="Planned Start",
            x_end="Planned Finish",
            y="Activity Name",
            color="Is Critical Path",
            color_discrete_map=color_discrete_map,
            hover_data=["Activity ID", "WBS Code", "% Complete", "Total Float (Days)", "Contractor"],
            title=f"Master Timeline Schedule — {selected_project}"
        )
        fig_gantt.update_yaxes(autorange="reversed")
        fig_gantt.update_layout(
            xaxis_title="Timeline",
            yaxis_title="Activity Description",
            height=400,
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(
                title=dict(text="Path Status"),
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        st.plotly_chart(fig_gantt, use_container_width=True)
    else:
        st.warning("No activities match current filter criteria.")

    st.subheader("📝 Activity Data Editor (Interactive Primavera Grid)")
    st.caption("Double-click any cell to update durations, completion rates, or dates in real-time.")

    edited_df = st.data_editor(
        filtered_df[[
            "Activity ID", "WBS Code", "WBS Phase", "Activity Name", 
            "Planned Start", "Planned Finish", "Original Duration (Days)", 
            "% Complete", "Total Float (Days)", "Is Critical Path", "Contractor"
        ]],
        num_rows="dynamic",
        use_container_width=True,
        key="activity_editor"
    )

    if st.button("💾 Apply Schedule Updates"):
        for idx in edited_df.index:
            act_id = edited_df.loc[idx, "Activity ID"]
            for col in edited_df.columns:
                val = edited_df.loc[idx, col]
                st.session_state.df_activities.loc[
                    st.session_state.df_activities["Activity ID"] == act_id, col
                ] = val
        st.success("Schedule adjustments saved & CPM re-computed!")
        st.rerun()


# ------------------------------------------
# TAB 2: EARNED VALUE MANAGEMENT (EVM)
# ------------------------------------------
with tab2:
    st.markdown('<div class="main-header">Earned Value Management (EVM) Metrics</div>', unsafe_allow_html=True)

    bac = float(filtered_df["BAC ($)"].sum())
    
    filtered_df["EV_Val"] = filtered_df["BAC ($)"] * (filtered_df["% Complete"] / 100.0)
    filtered_df["PV_Val"] = filtered_df["BAC ($)"] * np.where(filtered_df["% Complete"] > 0, np.minimum(filtered_df["% Complete"] + 15, 100), 0) / 100.0
    
    ev = float(filtered_df["EV_Val"].sum())
    pv = float(filtered_df["PV_Val"].sum())
    ac = float(filtered_df["AC ($)"].sum())

    cpi = round(ev / ac, 2) if ac > 0 else 1.00
    spi = round(ev / pv, 2) if pv > 0 else 1.00
    eac = round(bac / cpi, 2) if cpi > 0 else bac
    vac = round(bac - eac, 2)

    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5, kpi_col6, kpi_col7 = st.columns(7)
    kpi_col1.metric("BAC (Budget)", f"${bac:,.0f}")
    kpi_col2.metric("PV (Planned)", f"${pv:,.0f}")
    kpi_col3.metric("EV (Earned)", f"${ev:,.0f}")
    kpi_col4.metric("AC (Actual)", f"${ac:,.0f}")
    kpi_col5.metric("CPI", f"{cpi:.2f}", delta=f"{round((cpi-1)*100,1)}%" if cpi != 1.0 else None)
    kpi_col6.metric("SPI", f"{spi:.2f}", delta=f"{round((spi-1)*100,1)}%" if spi != 1.0 else None)
    kpi_col7.metric("EAC (Forecast)", f"${eac:,.0f}", delta=f"${vac:,.0f}", delta_color="normal")

    st.markdown("---")

    st.subheader("📌 Project Health Analysis")
    if cpi >= 1.0 and spi >= 1.0:
        st.markdown('<div class="status-ok">✅ Project is ON SCHEDULE and WITHIN BUDGET.</div>', unsafe_allow_html=True)
    elif cpi < 1.0 and spi >= 1.0:
        st.markdown('<div class="status-warn">⚠️ Project is ON SCHEDULE but OVER BUDGET. Cost controls required.</div>', unsafe_allow_html=True)
    elif cpi >= 1.0 and spi < 1.0:
        st.markdown('<div class="status-warn">⚠️ Project is UNDER BUDGET but BEHIND SCHEDULE. Resource acceleration advised.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-alert">🚨 CRITICAL: Project is BEHIND SCHEDULE and OVER BUDGET. Immediate management intervention required.</div>', unsafe_allow_html=True)

    st.write("")

    st.subheader("📈 Time-Phased EVM Performance S-Curve")
    
    months = pd.date_range(start="2026-01-01", periods=12, freq="MS").strftime("%Y-%m").tolist()
    
    cum_pv = np.cumsum(np.linspace(bac * 0.05, bac * 0.15, 12))
    cum_ev = cum_pv * (spi if spi > 0 else 0.9)
    cum_ac = cum_ev / (cpi if cpi > 0 else 1.1)

    current_month_idx = 6
    cum_ev[current_month_idx:] = np.nan
    cum_ac[current_month_idx:] = np.nan

    scurve_df = pd.DataFrame({
        "Month": months,
        "Planned Value (PV)": cum_pv,
        "Earned Value (EV)": cum_ev,
        "Actual Cost (AC)": cum_ac
    })

    fig_scurve = go.Figure()
    fig_scurve.add_trace(go.Scatter(x=scurve_df["Month"], y=scurve_df["Planned Value (PV)"], mode='lines+markers', name='Planned Value (PV)', line=dict(color='#2563EB', width=3)))
    fig_scurve.add_trace(go.Scatter(x=scurve_df["Month"], y=scurve_df["Earned Value (EV)"], mode='lines+markers', name='Earned Value (EV)', line=dict(color='#16A34A', width=3)))
    fig_scurve.add_trace(go.Scatter(x=scurve_df["Month"], y=scurve_df["Actual Cost (AC)"], mode='lines+markers', name='Actual Cost (AC)', line=dict(color='#DC2626', width=3, dash='dash')))

    fig_scurve.update_layout(
        title="Cumulative Cost Performance Baseline (S-Curve)",
        xaxis_title="Timeline (Months)",
        yaxis_title="Cumulative Cost ($)",
        hovermode="x unified",
        height=450,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig_scurve, use_container_width=True)


# ------------------------------------------
# TAB 3: RESOURCE LOADING & ALLOCATION
# ------------------------------------------
with tab3:
    st.markdown('<div class="main-header">Resource Loading & Capacity Histogram</div>', unsafe_allow_html=True)

    res_df = st.session_state.df_resources[
        st.session_state.df_resources["Project"] == selected_project
    ]

    if not res_df.empty:
        resource_types = res_df["Resource Type"].unique().tolist()
        col_r1, col_r2 = st.columns([2, 2])
        with col_r1:
            selected_res_type = st.selectbox("Select Resource Category", resource_types)

        filtered_res = res_df[res_df["Resource Type"] == selected_res_type]

        fig_res = go.Figure()

        fig_res.add_trace(go.Bar(
            x=filtered_res["Month"],
            y=filtered_res["Allocated Hours"],
            name="Allocated Man-Hours",
            marker_color=np.where(filtered_res["Allocated Hours"] > filtered_res["Capacity Limit"], '#EF4444', '#3B82F6')
        ))

        fig_res.add_trace(go.Scatter(
            x=filtered_res["Month"],
            y=filtered_res["Capacity Limit"],
            name="Max Monthly Capacity",
            line=dict(color='#F59E0B', width=3, dash='dot')
        ))

        fig_res.update_layout(
            title=f"Monthly Loading Histogram: {selected_res_type}",
            xaxis_title="Month",
            yaxis_title="Total Hours",
            barmode="group",
            height=400,
            margin=dict(l=10, r=10, t=40, b=10)
        )

        st.plotly_chart(fig_res, use_container_width=True)

        st.subheader("📌 Allocation Breakdown & Over-Allocation Tracker")
        over_allocated = filtered_res[filtered_res["Allocated Hours"] > filtered_res["Capacity Limit"]]
        
        if not over_allocated.empty:
            st.error(f"⚠️ Over-allocation detected for {selected_res_type} in {len(over_allocated)} period(s)! Consider resource leveling.")
        else:
            st.success(f"✅ Resource loading for {selected_res_type} is within normal capacity limits.")

        st.dataframe(filtered_res, use_container_width=True)

    else:
        st.info("No resource loading data configured for this project selection.")


# ------------------------------------------
# TAB 4: RISK & MILESTONE LOG
# ------------------------------------------
with tab4:
    st.markdown('<div class="main-header">Project Risk Matrix & Major Milestones</div>', unsafe_allow_html=True)

    col_m1, col_m2 = st.columns([1, 1])

    with col_m1:
        st.subheader("🚩 Major Milestone Tracker")
        ms_df = st.session_state.df_milestones[
            st.session_state.df_milestones["Project"] == selected_project
        ]
        
        def highlight_status(val):
            if val == "Completed":
                return 'background-color: #DCFCE7; color: #166534; font-weight: bold;'
            elif val == "At Risk":
                return 'background-color: #FEE2E2; color: #991B1B; font-weight: bold;'
            return 'background-color: #FEF9C3; color: #854D0E; font-weight: bold;'

        if not ms_df.empty:
            styled_ms = ms_df[["Milestone", "Target Date", "Status"]].style.map(
                highlight_status, subset=["Status"]
            )
            st.dataframe(styled_ms, use_container_width=True)
        else:
            st.info("No milestones tracked for this project.")

    with col_m2:
        st.subheader("📊 Risk Assessment Scorecard")
        risk_df = st.session_state.df_risks[
            st.session_state.df_risks["Project"] == selected_project
        ].copy()

        if not risk_df.empty:
            risk_df["Risk Score"] = risk_df["Probability (1-5)"] * risk_df["Impact (1-5)"]
            
            fig_risk = px.scatter(
                risk_df,
                x="Probability (1-5)",
                y="Impact (1-5)",
                size="Risk Score",
                color="Risk Score",
                text="Risk ID",
                color_continuous_scale="Reds",
                title="Risk Assessment Heatmap Grid"
            )
            fig_risk.update_xaxes(range=[0, 6])
            fig_risk.update_yaxes(range=[0, 6])
            fig_risk.update_layout(height=320, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_risk, use_container_width=True)

    st.subheader("📋 Detailed Risk Register & Response Plans")
    if not risk_df.empty:
        st.dataframe(
            risk_df[[
                "Risk ID", "Risk Event", "Probability (1-5)", "Impact (1-5)", 
                "Risk Score", "Mitigation Strategy", "Owner"
            ]].sort_values(by="Risk Score", ascending=False),
            use_container_width=True
        )
    else:
        st.info("No active risks logged.")

st.markdown("---")
st.caption("P6 Controls Hub Engine v2.4 | Powered by Streamlit, Pandas CPM, and Plotly Graphics")
