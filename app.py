import io
import os
import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# PAGE CONFIGURATION & DESIGN SYSTEM
# ==========================================
st.set_page_config(
    page_title="BEZA - Advanced Project Controls & Investment Appraisal Hub",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

def hide_streamlit_branding():
    """Hides Streamlit branding, top header, footer, and viewer badge."""
    hide_css = """
    <style>
        /* BEZA Government Enterprise Design System */
        :root {
            --beza-navy: #0B2545;
            --beza-slate: #134074;
            --beza-blue: #8DA9C4;
            --beza-light: #EEF4F8;
            --beza-accent: #EE9B00;
            --ink: #17233c;
            --muted: #64748b;
            --line: #e2e8f0;
            --page: #f8fafc;
            --green: #10b981;
            --sidebar: #0B2545;
        }

        .stApp {
            background-color: var(--page);
            color: var(--ink);
            font-family: 'Inter', Arial, sans-serif;
        }

        /* Hide Streamlit Header, Footer & Branding */
        header, footer, #MainMenu {
            visibility: hidden !important;
            display: none !important;
        }
        div[data-testid="stStatusWidget"],
        .viewerBadge_container,
        a[href*="streamlit.io"],
        a[href*="streamlit.cloud"] {
            visibility: hidden !important;
            display: none !important;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: var(--sidebar);
            color: #ffffff;
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }
        [data-testid="stSidebar"] .stMarkdown h1, 
        [data-testid="stSidebar"] .stMarkdown h2, 
        [data-testid="stSidebar"] .stMarkdown h3,
        [data-testid="stSidebar"] label {
            color: #cbd5e1 !important;
        }

        /* Modern Headers */
        .main-header {
            font-size: 22px;
            font-weight: 800;
            color: var(--beza-navy);
            letter-spacing: -0.5px;
            border-bottom: 2px solid var(--line);
            padding-bottom: 8px;
            margin-bottom: 20px;
        }

        /* Metric Cards */
        .stMetric {
            background: white;
            padding: 16px 18px;
            border-radius: 12px;
            border: 1px solid var(--line);
            box-shadow: 0 4px 12px rgba(11, 37, 69, 0.04);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .stMetric:hover {
            box-shadow: 0 6px 16px rgba(11, 37, 69, 0.08);
        }
        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
            font-weight: 800 !important;
            color: var(--beza-navy) !important;
            white-space: nowrap !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.8rem !important;
            font-weight: 700 !important;
            color: var(--muted) !important;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }

        /* Status Badges */
        .status-ok {
            background-color: #ecfdf5;
            color: #047857;
            padding: 12px 16px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 13px;
            border: 1px solid #a7f3d0;
        }
        .status-warn {
            background-color: #fffbeb;
            color: #b45309;
            padding: 12px 16px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 13px;
            border: 1px solid #fde68a;
        }
        .status-alert {
            background-color: #fef2f2;
            color: #b91c1c;
            padding: 12px 16px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 13px;
            border: 1px solid #fecaca;
        }

        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
            padding-bottom: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 44px;
            border-radius: 10px;
            background-color: white;
            border: 1px solid var(--line);
            color: var(--muted);
            font-weight: 700;
            font-size: 12px;
            padding: 0 16px;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #0B2545, #134074) !important;
            color: white !important;
            border: none !important;
        }
    </style>
    """
    st.markdown(hide_css, unsafe_allow_html=True)

hide_streamlit_branding()

def format_currency_compact(val: float) -> str:
    """Formats monetary figures in Philippine Peso (₱) concisely."""
    if abs(val) >= 1_000_000:
        return f"₱{val / 1_000_000:,.2f}M"
    elif abs(val) >= 1_000:
        return f"₱{val / 1_000:,.2f}K"
    return f"₱{val:,.2f}"


# ==========================================
# CPM SCHEDULING ENGINE (INTERACTIVE)
# ==========================================
def calculate_cpm_and_float(df: pd.DataFrame) -> pd.DataFrame:
    """Processes schedule durations, finish dates, and editable critical path status."""
    df = df.copy()
    
    df["Planned Start"] = pd.to_datetime(df["Planned Start"], errors="coerce")
    df["Planned Finish"] = pd.to_datetime(df["Planned Finish"], errors="coerce")
    df["Original Duration (Days)"] = pd.to_numeric(df["Original Duration (Days)"], errors="coerce")

    mask_valid = df["Original Duration (Days)"].notna() & (df["Original Duration (Days)"] > 0)
    if mask_valid.any():
        df.loc[mask_valid, "Planned Finish"] = df.loc[mask_valid, "Planned Start"] + pd.to_timedelta(df.loc[mask_valid, "Original Duration (Days)"], unit="days")

    df["Original Duration (Days)"] = (
        (df["Planned Finish"] - df["Planned Start"]).dt.days
    ).fillna(1).astype(int)

    df["Total Float (Days)"] = pd.to_numeric(df.get("Total Float (Days)", 0), errors="coerce").fillna(0).astype(int)

    if "Is Critical Path" not in df.columns:
        df["Is Critical Path"] = df["Total Float (Days)"] <= 0
    else:
        df["Is Critical Path"] = df["Is Critical Path"].fillna(df["Total Float (Days)"] <= 0).astype(bool)

    df["Path Type"] = np.where(df["Is Critical Path"], "Critical Path", "Non-Critical")

    return df


# ==========================================
# SAMPLE DATA GENERATOR & BASELINE SETUP
# ==========================================
@st.cache_data
def get_mock_project_data():
    activities_data = [
        {
            "Project": "Freeport Modernization",
            "Activity ID": "ACT-1010",
            "WBS Code": "1.1",
            "WBS Phase": "Engineering & Design",
            "Activity Name": "Site Geotechnical & Topographic Survey",
            "Contractor": "GeoTech Solutions",
            "Baseline Start": "2026-01-05",
            "Baseline Finish": "2026-02-15",
            "Planned Start": "2026-01-05",
            "Planned Finish": "2026-02-15",
            "Actual Start": "2026-01-05",
            "Actual Finish": "2026-02-15",
            "Original Duration (Days)": 41,
            "% Complete": 100,
            "BAC (₱)": 150000.0,
            "AC (₱)": 145000.0,
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
            "Baseline Start": "2026-02-16",
            "Baseline Finish": "2026-04-30",
            "Planned Start": "2026-02-16",
            "Planned Finish": "2026-04-30",
            "Actual Start": "2026-02-16",
            "Actual Finish": None,
            "Original Duration (Days)": 73,
            "% Complete": 85,
            "BAC (₱)": 450000.0,
            "AC (₱)": 410000.0,
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
            "Baseline Start": "2026-03-01",
            "Baseline Finish": "2026-08-31",
            "Planned Start": "2026-03-01",
            "Planned Finish": "2026-08-31",
            "Actual Start": "2026-03-05",
            "Actual Finish": None,
            "Original Duration (Days)": 183,
            "% Complete": 50,
            "BAC (₱)": 2200000.0,
            "AC (₱)": 1300000.0,
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
            "Baseline Start": "2026-05-01",
            "Baseline Finish": "2026-11-30",
            "Planned Start": "2026-05-01",
            "Planned Finish": "2026-11-30",
            "Actual Start": "2026-05-05",
            "Actual Finish": None,
            "Original Duration (Days)": 213,
            "% Complete": 30,
            "BAC (₱)": 5800000.0,
            "AC (₱)": 2100000.0,
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
            "Baseline Start": "2026-08-01",
            "Baseline Finish": "2026-12-31",
            "Planned Start": "2026-08-01",
            "Planned Finish": "2026-12-31",
            "Actual Start": "2026-08-10",
            "Actual Finish": None,
            "Original Duration (Days)": 152,
            "% Complete": 10,
            "BAC (₱)": 3100000.0,
            "AC (₱)": 400000.0,
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
            "Baseline Start": "2026-12-01",
            "Baseline Finish": "2027-02-15",
            "Planned Start": "2026-12-01",
            "Planned Finish": "2027-02-15",
            "Actual Start": None,
            "Actual Finish": None,
            "Original Duration (Days)": 76,
            "% Complete": 0,
            "BAC (₱)": 800000.0,
            "AC (₱)": 0.0,
            "Total Float (Days)": 0,
            "Is Critical Path": True,
        },
        {
            "Project": "SEZ Infrastructure Phasing",
            "Activity ID": "SEZ-2010",
            "WBS Code": "1.1",
            "WBS Phase": "Earthworks",
            "Activity Name": "Site Clearing & Bulk Grading",
            "Contractor": "EarthMovers Inc",
            "Baseline Start": "2027-01-15",
            "Baseline Finish": "2027-04-15",
            "Planned Start": "2027-01-15",
            "Planned Finish": "2027-04-15",
            "Actual Start": "2027-01-15",
            "Actual Finish": None,
            "Original Duration (Days)": 90,
            "% Complete": 90,
            "BAC (₱)": 800000.0,
            "AC (₱)": 850000.0,
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
            "Baseline Start": "2027-04-01",
            "Baseline Finish": "2027-09-30",
            "Planned Start": "2027-04-01",
            "Planned Finish": "2027-09-30",
            "Actual Start": "2027-04-05",
            "Actual Finish": None,
            "Original Duration (Days)": 182,
            "% Complete": 40,
            "BAC (₱)": 3500000.0,
            "AC (₱)": 1600000.0,
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
            "Baseline Start": "2027-05-01",
            "Baseline Finish": "2027-11-15",
            "Planned Start": "2027-05-01",
            "Planned Finish": "2027-11-15",
            "Actual Start": "2027-05-10",
            "Actual Finish": None,
            "Original Duration (Days)": 198,
            "% Complete": 25,
            "BAC (₱)": 2800000.0,
            "AC (₱)": 900000.0,
            "Total Float (Days)": 20,
            "Is Critical Path": False,
        },
    ]

    resource_data = [
        {"Project": "Freeport Modernization", "Month": "2026-01", "Resource Type": "Civil Engineers", "Allocated Hours": 1200, "Capacity Limit": 1000},
        {"Project": "Freeport Modernization", "Month": "2026-02", "Resource Type": "Civil Engineers", "Allocated Hours": 1100, "Capacity Limit": 1000},
        {"Project": "Freeport Modernization", "Month": "2026-03", "Resource Type": "Civil Engineers", "Allocated Hours": 900, "Capacity Limit": 1000},
        {"Project": "Freeport Modernization", "Month": "2026-01", "Resource Type": "Heavy Equipment", "Allocated Hours": 800, "Capacity Limit": 1200},
        {"Project": "Freeport Modernization", "Month": "2026-02", "Resource Type": "Heavy Equipment", "Allocated Hours": 1400, "Capacity Limit": 1200},
        {"Project": "Freeport Modernization", "Month": "2026-03", "Resource Type": "Heavy Equipment", "Allocated Hours": 1600, "Capacity Limit": 1200},
        {"Project": "Freeport Modernization", "Month": "2026-04", "Resource Type": "Heavy Equipment", "Allocated Hours": 1300, "Capacity Limit": 1200},
        {"Project": "Freeport Modernization", "Month": "2026-01", "Resource Type": "Laborers", "Allocated Hours": 2500, "Capacity Limit": 3000},
        {"Project": "Freeport Modernization", "Month": "2026-02", "Resource Type": "Laborers", "Allocated Hours": 3200, "Capacity Limit": 3000},
        {"Project": "SEZ Infrastructure Phasing", "Month": "2027-01", "Resource Type": "Civil Engineers", "Allocated Hours": 600, "Capacity Limit": 800},
        {"Project": "SEZ Infrastructure Phasing", "Month": "2027-02", "Resource Type": "Heavy Equipment", "Allocated Hours": 1100, "Capacity Limit": 1000},
    ]

    risk_data = [
        {"Project": "Freeport Modernization", "Risk ID": "RSK-01", "Risk Event": "Monsoon / Extreme Weather delays marine dredging", "Probability (1-5)": 4, "Impact (1-5)": 4, "Mitigation Strategy": "Deploy additional secondary dredgers during clear windows.", "Owner": "Marine Contractor"},
        {"Project": "Freeport Modernization", "Risk ID": "RSK-02", "Risk Event": "Supply Chain delay for Ship-to-Shore cranes", "Probability (1-5)": 3, "Impact (1-5)": 5, "Mitigation Strategy": "Issue early long-lead purchase orders.", "Owner": "Procurement Lead"},
        {"Project": "SEZ Infrastructure Phasing", "Risk ID": "RSK-03", "Risk Event": "Delays in environmental clearance for power substation", "Probability (1-5)": 2, "Impact (1-5)": 4, "Mitigation Strategy": "Engage municipal regulatory liaison.", "Owner": "Permitting Lead"},
    ]

    milestone_data = [
        {"Project": "Freeport Modernization", "Milestone": "Geotechnical Survey Signoff", "Target Date": "2026-02-15", "Status": "Completed"},
        {"Project": "Freeport Modernization", "Milestone": "Dredging Works Commencement", "Target Date": "2026-05-01", "Status": "On Track"},
        {"Project": "Freeport Modernization", "Milestone": "STS Cranes On-Site Arrival", "Target Date": "2026-08-31", "Status": "At Risk"},
        {"Project": "SEZ Infrastructure Phasing", "Milestone": "Earthworks Phase 1 Completion", "Target Date": "2027-04-15", "Status": "On Track"},
    ]

    df_act = pd.DataFrame(activities_data)
    date_cols = ["Baseline Start", "Baseline Finish", "Planned Start", "Planned Finish", "Actual Start", "Actual Finish"]
    for col in date_cols:
        df_act[col] = pd.to_datetime(df_act[col], errors="coerce").dt.date

    df_act["Baseline BAC (₱)"] = df_act["BAC (₱)"]

    return (
        df_act,
        pd.DataFrame(resource_data),
        pd.DataFrame(risk_data),
        pd.DataFrame(milestone_data),
    )


if "df_activities" not in st.session_state:
    (
        st.session_state.df_activities,
        st.session_state.df_resources,
        st.session_state.df_risks,
        st.session_state.df_milestones,
    ) = get_mock_project_data()


# ==========================================
# SIDEBAR CONTROLS & NAVIGATION (BEZA BRANDED)
# ==========================================
logo_paths = [
    "BEZA-LOGO-Copy-300x300.png",
    "assets/BEZA-LOGO-Copy-300x300.png",
    "./BEZA-LOGO-Copy-300x300.png",
    "../BEZA-LOGO-Copy-300x300.png"
]
logo_path = None
for p in logo_paths:
    if os.path.exists(p):
        logo_path = p
        break

if logo_path:
    st.sidebar.image(logo_path, width=140)
else:
    st.sidebar.markdown("🏛️ **BEZA**")

st.sidebar.markdown("### Bangsamoro Economic Zone Authority")
st.sidebar.markdown("#### Investment & Project Controls Hub")
st.sidebar.markdown("---")

projects = st.session_state.df_activities["Project"].unique().tolist()
selected_project = st.sidebar.selectbox("Select Project Workspace", projects)

st.sidebar.markdown("#### 🔍 Workspace Filters")
project_activities = st.session_state.df_activities[
    st.session_state.df_activities["Project"] == selected_project
]

phases = ["All"] + list(project_activities["WBS Phase"].unique())
selected_phase = st.sidebar.selectbox("WBS Phase Filter", phases)

contractors = ["All"] + list(project_activities["Contractor"].unique())
selected_contractor = st.sidebar.selectbox("Contractor Filter", contractors)

filtered_df = project_activities.copy()
if selected_phase != "All":
    filtered_df = filtered_df[filtered_df["WBS Phase"] == selected_phase]
if selected_contractor != "All":
    filtered_df = filtered_df[filtered_df["Contractor"] == selected_contractor]

filtered_df = calculate_cpm_and_float(filtered_df)

st.sidebar.markdown("---")
st.sidebar.markdown("#### 💾 Data Management")

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
    file_name=f"BEZA_P6_Export_{selected_project.replace(' ', '_')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)


# ==========================================
# MAIN APPLICATION INTERFACE
# ==========================================
st.title(f"BEZA Project Workspace: {selected_project}")
st.caption(
    "Bangsamoro Economic Zone Authority — Enterprise Infrastructure Investment Appraisal & Project Controls"
)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "📅 Schedule & WBS (Gantt)",
        "📈 Earned Value (EVM & S-Curve)",
        "🚜 Resource Allocation",
        "⚠️ Risk & Milestones",
        "💼 Economic Viability & Appraisal",
    ]
)

# ------------------------------------------
# TAB 1: WBS & SCHEDULE (GANTT VIEW)
# ------------------------------------------
with tab1:
    st.markdown(
        '<div class="main-header">WBS Schedule & Actual Progress Engine</div>',
        unsafe_allow_html=True,
    )

    col_g1, col_g2 = st.columns([3, 1])
    with col_g2:
        only_critical = st.checkbox(
            "Show Critical Path Activities Only", value=False
        )

    view_df = filtered_df.copy()
    if only_critical:
        view_df = view_df[view_df["Is Critical Path"] == True]

    if not view_df.empty:
        color_discrete_map = {
            "Critical Path": "#EF4444",
            "Non-Critical": "#0B2545"
        }

        fig_gantt = px.timeline(
            view_df,
            x_start="Planned Start",
            x_end="Planned Finish",
            y="Activity Name",
            color="Path Type",
            color_discrete_map=color_discrete_map,
            hover_data=[
                "Activity ID",
                "WBS Code",
                "% Complete",
                "Total Float (Days)",
                "Contractor",
            ],
            title=f"Master Timeline Schedule — {selected_project}",
        )
        fig_gantt.update_yaxes(autorange="reversed")
        fig_gantt.update_layout(
            xaxis_title="Timeline",
            yaxis_title="Activity Description",
            height=400,
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(
                title=dict(text="CPM Path Status"),
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_gantt, use_container_width=True)
    else:
        st.warning("No activities match current filter criteria.")

    st.subheader(
        "📝 Activity Data Editor (Baseline, Actuals & Cost Tracking Grid)"
    )
    st.caption(
        "Edit 'Original Duration', 'Planned Start', or check/uncheck 'Is Critical Path?', then click **Apply Schedule Updates** below."
    )

    editor_df = filtered_df.copy()
    date_cols = ["Baseline Start", "Baseline Finish", "Planned Start", "Planned Finish", "Actual Start", "Actual Finish"]
    for col in date_cols:
        if col in editor_df.columns:
            editor_df[col] = pd.to_datetime(editor_df[col], errors="coerce").dt.date

    column_config = {
        "Baseline Start": st.column_config.DateColumn("Baseline Start", format="YYYY-MM-DD"),
        "Baseline Finish": st.column_config.DateColumn("Baseline Finish", format="YYYY-MM-DD"),
        "Planned Start": st.column_config.DateColumn("Planned Start", format="YYYY-MM-DD"),
        "Planned Finish": st.column_config.DateColumn("Planned Finish", format="YYYY-MM-DD", help="Recalculated automatically upon applying updates"),
        "Actual Start": st.column_config.DateColumn("Actual Start", format="YYYY-MM-DD"),
        "Actual Finish": st.column_config.DateColumn("Actual Finish", format="YYYY-MM-DD"),
        "Original Duration (Days)": st.column_config.NumberColumn("Original Duration (Days)", format="%d", help="Enter days to automatically push Planned Finish"),
        "Total Float (Days)": st.column_config.NumberColumn("Total Float (Days)", format="%d"),
        "Path Type": st.column_config.TextColumn("CPM Path Type", disabled=True),
        "Is Critical Path": st.column_config.CheckboxColumn("Is Critical Path?", help="Check to set activity as Critical Path"),
        "BAC (₱)": st.column_config.NumberColumn("BAC (₱)", format="₱%.2f"),
        "AC (₱)": st.column_config.NumberColumn("AC (₱)", format="₱%.2f"),
        "% Complete": st.column_config.NumberColumn("% Complete", min_value=0, max_value=100, step=1, format="%d%%"),
    }

    edited_df = st.data_editor(
        editor_df[[
            "Activity ID",
            "WBS Code",
            "WBS Phase",
            "Activity Name",
            "Path Type",
            "Is Critical Path",
            "Baseline Start",
            "Baseline Finish",
            "Planned Start",
            "Planned Finish",
            "Original Duration (Days)",
            "Actual Start",
            "Actual Finish",
            "% Complete",
            "Total Float (Days)",
            "BAC (₱)",
            "AC (₱)",
            "Contractor",
        ]],
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        key="activity_editor",
    )

    if st.button("💾 Apply Schedule, Actuals & Baseline Updates", type="primary"):
        other_projects_df = st.session_state.df_activities[
            st.session_state.df_activities["Project"] != selected_project
        ]
        edited_df["Project"] = selected_project
        
        for col in date_cols:
            if col in edited_df.columns:
                edited_df[col] = pd.to_datetime(edited_df[col], errors="coerce").dt.date

        recalculated_df = calculate_cpm_and_float(edited_df)

        st.session_state.df_activities = pd.concat(
            [other_projects_df, recalculated_df], ignore_index=True
        )
        st.success("Interactive schedule updated & saved successfully!")
        st.rerun()


# ------------------------------------------
# TAB 2: EARNED VALUE MANAGEMENT (EVM & S-CURVE)
# ------------------------------------------
with tab2:
    st.markdown(
        '<div class="main-header">Earned Value Management (EVM) Analytics</div>',
        unsafe_allow_html=True,
    )

    bac = float(filtered_df["BAC (₱)"].sum())
    filtered_df["EV_Val"] = filtered_df["BAC (₱)"] * (
        filtered_df["% Complete"] / 100.0
    )
    filtered_df["PV_Val"] = (
        filtered_df["BAC (₱)"]
        * np.where(
            filtered_df["% Complete"] > 0,
            np.minimum(filtered_df["% Complete"] + 10, 100),
            0,
        )
        / 100.0
    )

    ev = float(filtered_df["EV_Val"].sum())
    pv = float(filtered_df["PV_Val"].sum())
    ac = float(filtered_df["AC (₱)"].sum())

    cpi = round(ev / ac, 2) if ac > 0 else 1.00
    spi = round(ev / pv, 2) if pv > 0 else 1.00
    eac = round(bac / cpi, 2) if cpi > 0 else bac
    vac = round(bac - eac, 2)

    r1_col1, r1_col2, r1_col3, r1_col4 = st.columns(4)
    r1_col1.metric("BAC (Baseline Budget)", format_currency_compact(bac), help=f"Full BAC: ₱{bac:,.2f}")
    r1_col2.metric("PV (Planned Value)", format_currency_compact(pv), help=f"Full PV: ₱{pv:,.2f}")
    r1_col3.metric("EV (Earned Value)", format_currency_compact(ev), help=f"Full EV: ₱{ev:,.2f}")
    r1_col4.metric("AC (Actual Cost)", format_currency_compact(ac), help=f"Full AC: ₱{ac:,.2f}")

    st.write("")
    r2_col1, r2_col2, r2_col3 = st.columns(3)
    r2_col1.metric(
        "CPI (Cost Performance)",
        f"{cpi:.2f}",
        delta=f"{round((cpi-1)*100,1)}%",
    )
    r2_col2.metric(
        "SPI (Schedule Performance)",
        f"{spi:.2f}",
        delta=f"{round((spi-1)*100,1)}%",
    )
    r2_col3.metric(
        "EAC (Forecast At Completion)",
        format_currency_compact(eac),
        delta=format_currency_compact(vac),
        delta_color="normal",
        help=f"Full Forecast: ₱{eac:,.2f}",
    )

    st.markdown("---")

    st.subheader("📌 Project Performance & Slippage Evaluation")
    if cpi >= 1.0 and spi >= 1.0:
        st.markdown(
            '<div class="status-ok">✅ Project is ON SCHEDULE (SPI ≥ 1) and WITHIN BUDGET (CPI ≥ 1). No negative schedule slippage.</div>',
            unsafe_allow_html=True,
        )
    elif cpi < 1.0 and spi >= 1.0:
        st.markdown(
            '<div class="status-warn">⚠️ Project is ON SCHEDULE but OVER BUDGET (CPI < 1).</div>',
            unsafe_allow_html=True,
        )
    elif cpi >= 1.0 and spi < 1.0:
        st.markdown(
            '<div class="status-warn">⚠️ Project is UNDER BUDGET but BEHIND SCHEDULE (SPI < 1). Schedule slippage detected.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="status-alert">🚨 CRITICAL: Project is BEHIND SCHEDULE (Slippage present) and OVER BUDGET.</div>',
            unsafe_allow_html=True,
        )

    st.write("")
    st.subheader("📈 Time-Phased Performance S-Curve with Data Date (Baseline Status Line)")

    all_starts = pd.to_datetime(filtered_df["Planned Start"], errors="coerce").dropna()
    all_finishes = pd.to_datetime(filtered_df["Planned Finish"], errors="coerce").dropna()

    min_date = all_starts.min() if not all_starts.empty else pd.Timestamp("2026-01-01")
    max_date = all_finishes.max() if not all_finishes.empty else pd.Timestamp("2026-12-31")

    months_series = pd.date_range(start=min_date, end=max_date + pd.Timedelta(days=30), freq="MS")
    months = months_series.strftime("%Y-%m").tolist()
    if len(months) < 2:
        months = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]

    col_d1, col_d2 = st.columns([2, 2])
    with col_d1:
        selected_data_date_obj = st.date_input(
            "📅 Select Status Data Date (Current Progress Point)",
            value=datetime.date(min_date.year, min_date.month, 15) if min_date else datetime.date(2026, 6, 15),
            help="Pick any date across 2026, 2027, 2028+ using the calendar view.",
        )
        selected_data_date = selected_data_date_obj.strftime("%Y-%m")

    cum_pv = np.cumsum(np.linspace(bac * 0.04, bac * (1.0 / len(months)), len(months)))
    cum_ev = cum_pv * (spi if spi > 0 else 0.9)
    cum_ac = cum_ev / (cpi if cpi > 0 else 1.1)

    if selected_data_date in months:
        data_date_idx = months.index(selected_data_date)
        cum_ev[data_date_idx + 1:] = np.nan
        cum_ac[data_date_idx + 1:] = np.nan

    scurve_df = pd.DataFrame({
        "Month": months,
        "Planned Value (PV Baseline)": cum_pv,
        "Earned Value (EV)": cum_ev,
        "Actual Cost (AC)": cum_ac,
    })

    fig_scurve = go.Figure()
    fig_scurve.add_trace(
        go.Scatter(
            x=scurve_df["Month"],
            y=scurve_df["Planned Value (PV Baseline)"],
            mode="lines+markers",
            name="Planned Value (PV Baseline)",
            line=dict(color="#0B2545", width=3),
        )
    )
    fig_scurve.add_trace(
        go.Scatter(
            x=scurve_df["Month"],
            y=scurve_df["Earned Value (EV)"],
            mode="lines+markers",
            name="Earned Value (EV)",
            line=dict(color="#10B981", width=3),
        )
    )
    fig_scurve.add_trace(
        go.Scatter(
            x=scurve_df["Month"],
            y=scurve_df["Actual Cost (AC)"],
            mode="lines+markers",
            name="Actual Cost (AC)",
            line=dict(color="#EF4444", width=3, dash="dash"),
        )
    )

    fig_scurve.add_shape(
        type="line",
        x0=selected_data_date,
        y0=0,
        x1=selected_data_date,
        y1=1,
        yref="paper",
        line=dict(color="#B91C1C", width=3, dash="dash")
    )
    
    fig_scurve.add_annotation(
        x=selected_data_date,
        y=1,
        yref="paper",
        text=f"Data Date: {selected_data_date_obj.strftime('%Y-%m-%d')}",
        showarrow=False,
        xanchor="left",
        yanchor="bottom",
        font=dict(color="#B91C1C", size=12, family="sans-serif")
    )

    fig_scurve.update_layout(
        title=f"Cost Performance Baseline & Slippage Analysis (Status Date: {selected_data_date_obj.strftime('%Y-%m-%d')})",
        xaxis_title="Timeline (Months)",
        yaxis_title="Cumulative Cost (₱)",
        hovermode="x unified",
        height=450,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_scurve, use_container_width=True)


# ------------------------------------------
# TAB 3: RESOURCE LOADING & ALLOCATION
# ------------------------------------------
with tab3:
    st.markdown(
        '<div class="main-header">Resource Loading & Capacity Histogram</div>',
        unsafe_allow_html=True,
    )

    res_df = st.session_state.df_resources[
        st.session_state.df_resources["Project"] == selected_project
    ]

    if not res_df.empty:
        resource_types = res_df["Resource Type"].unique().tolist()
        col_r1, col_r2 = st.columns([2, 2])
        with col_r1:
            selected_res_type = st.selectbox(
                "Select Resource Category", resource_types
            )

        filtered_res = res_df[res_df["Resource Type"] == selected_res_type]

        fig_res = go.Figure()
        fig_res.add_trace(
            go.Bar(
                x=filtered_res["Month"],
                y=filtered_res["Allocated Hours"],
                name="Allocated Man-Hours",
                marker_color=np.where(
                    filtered_res["Allocated Hours"]
                    > filtered_res["Capacity Limit"],
                    "#EF4444",
                    "#134074",
                ),
            )
        )
        fig_res.add_trace(
            go.Scatter(
                x=filtered_res["Month"],
                y=filtered_res["Capacity Limit"],
                name="Max Monthly Capacity Limit",
                line=dict(color="#EE9B00", width=3, dash="dot"),
            )
        )

        fig_res.update_layout(
            title=f"Monthly Loading Histogram: {selected_res_type}",
            xaxis_title="Month",
            yaxis_title="Total Hours",
            barmode="group",
            height=400,
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_res, use_container_width=True)
        st.dataframe(filtered_res, use_container_width=True)
    else:
        st.info("No resource loading data configured for this project.")


# ------------------------------------------
# TAB 4: RISK & MILESTONE LOG
# ------------------------------------------
with tab4:
    st.markdown(
        '<div class="main-header">Project Risk Matrix & Major Milestones</div>',
        unsafe_allow_html=True,
    )

    col_m1, col_m2 = st.columns([1, 1])
    with col_m1:
        st.subheader("🚩 Major Milestone Tracker")
        ms_df = st.session_state.df_milestones[
            st.session_state.df_milestones["Project"] == selected_project
        ]
        if not ms_df.empty:
            st.dataframe(ms_df, use_container_width=True)
        else:
            st.info("No milestones tracked.")

    with col_m2:
        st.subheader("📊 Risk Assessment Scorecard")
        risk_df = st.session_state.df_risks[
            st.session_state.df_risks["Project"] == selected_project
        ].copy()
        if not risk_df.empty:
            risk_df["Risk Score"] = (
                risk_df["Probability (1-5)"] * risk_df["Impact (1-5)"]
            )
            st.dataframe(
                risk_df[
                    [
                        "Risk ID",
                        "Risk Event",
                        "Risk Score",
                        "Mitigation Strategy",
                    ]
                ],
                use_container_width=True,
            )
        else:
            st.info("No active risks logged.")


# ------------------------------------------
# TAB 5: ECONOMIC VIABILITY & APPRAISAL
# ------------------------------------------
with tab5:
    st.markdown(
        '<div class="main-header">Infrastructure Economic Viability & Financial Appraisal Workspace</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        Welcome to the **BEZA Investment Appraisal & Economic Viability Workspace**. 
        This specialized executive module evaluates capital projects across financial returns (FNPV, FIRR), 
        socio-economic benefits (ENPV, EIRR, BCR), debt servicing capacity (DSCR), and sensitivity risk profiles.
        """
    )

    col_app1, col_app2, col_app3 = st.columns(3)
    col_app1.metric("Financial NPV (FNPV @ 10%)", "₱482.50M", delta="+12.4% vs Baseline")
    col_app2.metric("Financial IRR (FIRR)", "16.8%", delta="Hurdle: 10.0%")
    col_app3.metric("Economic IRR (EIRR)", "21.5%", delta="Social Discount: 9%")

    st.markdown("---")

    app_tab_a, app_tab_b, app_tab_c = st.tabs([
        "🏗️ 1. Overview & Cost-Benefit",
        "📊 2. Financial & Debt Analysis",
        "📄 3. Printable Appraisal Report"
    ])

    with app_tab_a:
        st.subheader("Project Economic Appraisal Summary")
        st.markdown(
            """
            * **Project Category**: Regional Port & Economic Zone Logistics Expansion
            * **Appraisal Status**: Reviewed & Recommended for Board Concurrence
            * **Economic Net Present Value (ENPV)**: ₱890.42 Million
            * **Benefit-Cost Ratio (BCR)**: 1.84 (Meets NEDA-ICC criteria > 1.0)
            """
        )
        
        # Cash Flow Projection Chart
        cf_years = [f"Yr {i}" for i in range(1, 11)]
        cf_net = [-1200, -800, 200, 450, 680, 850, 920, 950, 980, 1050]
        
        fig_cf = px.bar(
            x=cf_years, y=cf_net,
            title="Project Net Cash Flow Projections (10-Year Horizon)",
            labels={"x": "Project Timeline", "y": "Net Cash Flow (₱M)"},
            color=cf_net,
            color_continuous_scale=["#EF4444", "#10B981"]
        )
        fig_cf.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350)
        st.plotly_chart(fig_cf, use_container_width=True)

    with app_tab_b:
        st.subheader("Financing Structure & Debt Service Coverage (DSCR)")
        st.markdown(
            """
            * **Total Capital Expenditure (CAPEX)**: ₱3,500,000,000.00
            * **Debt Financing (70%)**: ₱2,450,000,000.00 @ 6.5% interest rate (15-year term)
            * **Equity Financing (30%)**: ₱1,050,000,000.00
            * **Minimum DSCR**: 1.45x (Threshold: 1.20x) — *Robust debt repayment capacity.*
            """
        )
        
        debt_schedule = pd.DataFrame({
            "Year": [f"Year {i}" for i in range(1, 6)],
            "Principal Repayment (₱M)": [120, 140, 160, 185, 210],
            "Interest Payment (₱M)": [159, 149, 138, 126, 112],
            "DSCR Ratio": [1.35, 1.42, 1.50, 1.58, 1.65]
        })
        st.dataframe(debt_schedule, use_container_width=True)

    with app_tab_c:
        st.subheader("Printable Investment Appraisal Report Preview")
        st.markdown(
            """
            > **BANGSAMORO ECONOMIC ZONE AUTHORITY (BEZA)**  
            > **OFFICE OF THE EXECUTIVE DIRECTOR — INVESTMENT PROMOTION & EVALUATION GROUP**  
            > *Project Appraisal Committee Report #2026-BEZA-049*  
            > 
            > **Project Name**: Freeport Modernization & SEZ Infrastructure Phasing  
            > **Recommendation**: APPROVED FOR IMPLEMENTATION SUBJECT TO ENVIRONMENTAL COMPLIANCE CERTIFICATE (ECC) CONDITIONS.  
            > 
            > **Summary of Findings**:  
            > The economic appraisal confirms that the project yields substantial net positive socio-economic benefits to the Bangsamoro Autonomous Region, with an EIRR of 21.5% and a robust Benefit-Cost Ratio of 1.84. Financial viability is secured via a balanced 70:30 debt-equity structure with healthy DSCR margins.
            """
        )
        st.download_button(
            label="📥 Download Official Appraisal Report (PDF)",
            data=b"BEZA Official Appraisal Report PDF Binary Data Placeholder",
            file_name=f"BEZA_Appraisal_Report_{selected_project.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )

st.markdown("---")
st.caption(
    "Bangsamoro Economic Zone Authority (BEZA) | Project Controls Hub Engine v6.3 | Enterprise UI/UX Refactored"
)
