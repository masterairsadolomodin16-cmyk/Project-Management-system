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
        padding: 8px 12px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
        white-space: nowrap !important;
        overflow: visible !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
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


def format_currency_compact(val: float) -> str:
    """Formats monetary figures in Philippine Peso (₱) concisely."""
    if abs(val) >= 1_000_000:
        return f"₱{val / 1_000_000:,.2f}M"
    elif abs(val) >= 1_000:
        return f"₱{val / 1_000:,.2f}K"
    return f"₱{val:,.2f}"


# ==========================================
# CPM SCHEDULING ENGINE WITH AUTO-CALCULATION
# ==========================================
def calculate_cpm_and_float(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Planned Start"] = pd.to_datetime(df["Planned Start"])
    df["Original Duration (Days)"] = pd.to_numeric(df.get("Original Duration (Days)", 30), errors="coerce").fillna(30)

    # Auto-calculate Planned Finish based on Planned Start + Original Duration (Days)
    df["Planned Finish"] = df["Planned Start"] + pd.to_timedelta(df["Original Duration (Days)"], unit="d")

    df["Early Start"] = df["Planned Start"]
    df["Early Finish"] = df["Planned Finish"]
    df["Late Finish"] = df["Early Finish"]
    df["Late Start"] = df["Early Start"]

    df["Total Float (Days)"] = pd.to_numeric(df.get("Total Float (Days)", 0), errors="coerce").fillna(0)

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
            "
