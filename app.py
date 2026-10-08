from pathlib import Path

import streamlit as st

from utils.calculations import executive_kpis, overview_summary
from utils.data_loader import get_dataset_info, load_data


# ============================================================
# EnerVista
# Main Application Shell
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
CSS_FILE = PROJECT_ROOT / "assets" / "styles.css"


# ------------------------------------------------------------
# Page Configuration
# ------------------------------------------------------------

st.set_page_config(
    page_title="EnerVista | Energy Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ------------------------------------------------------------
# Global CSS
# ------------------------------------------------------------

def load_css() -> None:
    """Load the application's global stylesheet."""

    if not CSS_FILE.exists():
        st.warning(
            "Global stylesheet was not found. "
            "The application will continue with default styling."
        )
        return

    try:
        css = CSS_FILE.read_text(encoding="utf-8")
        st.markdown(
            f"<style>{css}</style>",
            unsafe_allow_html=True,
        )
    except Exception as exc:
        st.warning(f"Unable to load application styles: {exc}")


load_css()


# ------------------------------------------------------------
# Application Navigation
# ------------------------------------------------------------

PAGES = [
    ("app.py", "Home", "⌂"),
    ("pages/1_Executive_Dashboard.py", "Executive Dashboard", "▣"),
    ("pages/2_Energy_Analysis.py", "Energy Analysis", "⚡"),
    ("pages/3_Waste_Analysis.py", "Waste Analysis", "♻"),
    ("pages/4_Sustainability.py", "Sustainability", "◉"),
    ("pages/5_AI_Insights.py", "AI Insights", "✦"),
    ("pages/6_Predictive_Analytics.py", "Predictive Analytics", "◌"),
]


def render_sidebar() -> None:
    """Render the EnerVista sidebar navigation."""

    with st.sidebar:

        st.markdown(
            """
            <div class="ev-brand">
                <div class="ev-brand-icon">⚡</div>
                <div>
                    <div class="ev-brand-name">EnerVista</div>
                    <div class="ev-brand-subtitle">
                        ENERGY INTELLIGENCE PLATFORM
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption("Decision Visualization & Energy Waste Management")

        st.markdown("---")

        st.markdown(
            """
            <div style="
                font-size:0.72rem;
                font-weight:700;
                letter-spacing:0.06em;
                color:#94a3b8;
                margin-bottom:8px;
            ">
                NAVIGATION
            </div>
            """,
            unsafe_allow_html=True,
        )

        for page_path, label, icon in PAGES:
            st.page_link(
                page_path,
                label=f"{icon}  {label}",
            )

        st.markdown("---")

        st.markdown(
            """
            <div style="
                font-size:0.72rem;
                font-weight:700;
                letter-spacing:0.06em;
                color:#94a3b8;
                margin-bottom:8px;
            ">
                PLATFORM
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="
                color:#cbd5e1;
                font-size:0.78rem;
                line-height:1.65;
            ">
                <b>EnerVista</b> provides centralized visibility
                into energy consumption, waste, sustainability,
                AI-based insights and predictive analytics.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        st.caption("Enterprise Energy Analytics")
        st.caption("Version 1.0")


render_sidebar()


# ------------------------------------------------------------
# Safe Number Formatting
# ------------------------------------------------------------

def format_number(value: float, decimals: int = 1) -> str:
    """Format a numeric value safely for the dashboard."""

    try:
        if value is None:
            return "0"

        numeric_value = float(value)

        if abs(numeric_value) >= 1_000_000:
            return f"{numeric_value / 1_000_000:.{decimals}f}M"

        if abs(numeric_value) >= 1_000:
            return f"{numeric_value / 1_000:.{decimals}f}K"

        return f"{numeric_value:,.{decimals}f}"

    except (TypeError, ValueError):
        return "0"


def format_currency(value: float) -> str:
    """Format INR values safely."""

    try:
        numeric_value = float(value)

        if abs(numeric_value) >= 1_000_000:
            return f"₹{numeric_value / 1_000_000:.2f}M"

        if abs(numeric_value) >= 1_000:
            return f"₹{numeric_value / 1_000:.2f}K"

        return f"₹{numeric_value:,.2f}"

    except (TypeError, ValueError):
        return "₹0.00"


# ------------------------------------------------------------
# Reusable HTML Components
# ------------------------------------------------------------

def render_page_header() -> None:
    """Render the main EnerVista page heading."""

    st.markdown(
        """
        <div class="ev-page-header">
            <div class="ev-page-title">
                EnerVista Energy Intelligence
            </div>
            <div class="ev-page-subtitle">
                Centralized energy monitoring, waste analysis,
                sustainability intelligence and predictive decision support.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    """Render the application hero section."""

    st.markdown(
        """
        <div class="ev-hero">
            <div class="ev-hero-title">
                Smarter Energy. Lower Waste. Better Decisions.
            </div>
            <p class="ev-hero-text">
                EnerVista transforms operational energy data into
                actionable intelligence across consumption, cost,
                waste, renewable energy, carbon emissions and future demand.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(
    label: str,
    value: str,
    description: str,
    variant: str = "primary",
) -> None:
    """Render a styled KPI card."""

    st.markdown(
        f"""
        <div class="ev-kpi-card ev-kpi-{variant}">
            <div class="ev-kpi-label">{label}</div>
            <div class="ev-kpi-value">{value}</div>
            <div class="ev-kpi-description">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section(
    title: str,
    subtitle: str = "",
) -> None:
    """Render a section heading."""

    subtitle_html = ""

    if subtitle:
        subtitle_html = (
            f'<div class="ev-section-subtitle">{subtitle}</div>'
        )

    st.markdown(
        f"""
        <div class="ev-section">
            <div class="ev-section-title">{title}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Render application footer."""

    st.markdown(
        """
        <div class="ev-footer">
            <strong>EnerVista</strong>
            &nbsp;•&nbsp;
            Energy Intelligence & Decision Visualization Platform
            &nbsp;•&nbsp;
            Enterprise Analytics
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# Load Dataset
# ------------------------------------------------------------

@st.cache_data(show_spinner=False, ttl=3600)
def get_application_data():
    """Load the cleaned EnerVista dataset."""

    return load_data()


try:
    df = get_application_data()

except FileNotFoundError:
    st.error(
        "EnerVista dataset was not found."
    )

    st.info(
        "Please make sure the dataset exists at: "
        "`data/EnerVista_10000_Enhanced_Dataset.xlsx`"
    )

    st.stop()

except ValueError as exc:
    st.error("The EnerVista dataset could not be validated.")
    st.exception(exc)
    st.stop()

except Exception as exc:
    st.error("EnerVista could not load the dataset.")
    st.exception(exc)
    st.stop()


# ------------------------------------------------------------
# Dataset Validation
# ------------------------------------------------------------

if df is None or df.empty:
    st.error(
        "The dataset is empty after data preparation."
    )

    st.info(
        "Please verify the Excel file contains valid Date and Energy_kWh data."
    )

    st.stop()


# ------------------------------------------------------------
# Main Home Page
# ------------------------------------------------------------

render_page_header()

render_hero()


# ------------------------------------------------------------
# Dataset Information
# ------------------------------------------------------------

dataset_info = get_dataset_info(df)

summary = overview_summary(df)

kpis = executive_kpis(df)


# ------------------------------------------------------------
# KPI Section
# ------------------------------------------------------------

render_section(
    "Operational Overview",
    "Current performance indicators calculated from the loaded dataset.",
)

kpi_columns = st.columns(5)

with kpi_columns[0]:
    render_kpi_card(
        "Total Energy",
        f"{format_number(kpis.get('total_energy', 0), 1)} kWh",
        "Total recorded energy consumption",
        "primary",
    )

with kpi_columns[1]:
    render_kpi_card(
        "Energy Waste",
        f"{format_number(kpis.get('total_energy_waste', 0), 1)} kWh",
        "Estimated avoidable energy usage",
        "danger",
    )

with kpi_columns[2]:
    render_kpi_card(
        "Energy Cost",
        format_currency(kpis.get("total_cost", 0)),
        "Estimated recorded energy cost",
        "warning",
    )

with kpi_columns[3]:
    render_kpi_card(
        "Renewable Share",
        f"{format_number(kpis.get('renewable_percentage', 0), 1)}%",
        "Share of energy supplied by renewables",
        "success",
    )

with kpi_columns[4]:
    render_kpi_card(
        "Carbon Emissions",
        f"{format_number(kpis.get('total_carbon', 0), 1)} kg",
        "Recorded carbon emissions",
        "primary",
    )


# ------------------------------------------------------------
# Dataset Snapshot
# ------------------------------------------------------------

render_section(
    "Dataset Snapshot",
    "High-level information about the current EnerVista data source.",
)

snapshot_columns = st.columns(4)

with snapshot_columns[0]:
    st.metric(
        "Records",
        f"{dataset_info.get('records', len(df)):,}",
    )

with snapshot_columns[1]:
    st.metric(
        "Buildings",
        f"{summary.get('buildings', 0):,}",
    )

with snapshot_columns[2]:
    st.metric(
        "Departments",
        f"{summary.get('departments', 0):,}",
    )

with snapshot_columns[3]:
    st.metric(
        "Appliances",
        f"{summary.get('appliances', 0):,}",
    )


# ------------------------------------------------------------
# Date Coverage
# ------------------------------------------------------------

date_range = summary.get("date_range")

if date_range and len(date_range) == 2:
    start_date, end_date = date_range

    render_section(
        "Data Coverage",
        "Time period represented in the current dataset.",
    )

    coverage_columns = st.columns(2)

    with coverage_columns[0]:
        st.metric(
            "Start Date",
            str(start_date),
        )

    with coverage_columns[1]:
        st.metric(
            "End Date",
            str(end_date),
        )


# ------------------------------------------------------------
# Platform Modules
# ------------------------------------------------------------

render_section(
    "Analytics Modules",
    "Use the navigation panel to explore each analytical capability.",
)

module_columns = st.columns(3)

modules = [
    (
        "▣",
        "Executive Dashboard",
        "Monitor enterprise-level energy, cost, waste and performance KPIs.",
    ),
    (
        "⚡",
        "Energy Analysis",
        "Explore daily consumption, peak demand, buildings, departments and appliances.",
    ),
    (
        "♻",
        "Waste Analysis",
        "Identify waste patterns, reasons, high-waste locations and improvement opportunities.",
    ),
    (
        "◉",
        "Sustainability",
        "Evaluate renewable energy, carbon emissions and sustainability performance.",
    ),
    (
        "✦",
        "AI Insights",
        "Surface anomalies, operational patterns and data-driven recommendations.",
    ),
    (
        "◌",
        "Predictive Analytics",
        "Estimate future energy consumption, cost and carbon-emission trends.",
    ),
]

for index, (icon, title, description) in enumerate(modules):
    column = module_columns[index % 3]

    with column:
        st.markdown(
            f"""
            <div class="ev-module-card">
                <div class="ev-module-icon">{icon}</div>
                <div class="ev-module-title">{title}</div>
                <div class="ev-module-description">
                    {description}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if index % 3 == 2 and index < len(modules) - 1:
        st.write("")


# ------------------------------------------------------------
# Data Quality Information
# ------------------------------------------------------------

render_section(
    "Data Quality",
    "Basic validation status of the loaded dataset.",
)

quality_columns = st.columns(3)

with quality_columns[0]:
    st.metric(
        "Valid Records",
        f"{len(df):,}",
    )

with quality_columns[1]:
    missing_count = int(df.isna().sum().sum())

    st.metric(
        "Missing Values",
        f"{missing_count:,}",
    )

with quality_columns[2]:
    column_count = len(df.columns)

    st.metric(
        "Data Fields",
        f"{column_count:,}",
    )


# ------------------------------------------------------------
# Dataset Preview
# ------------------------------------------------------------

with st.expander(
    "View Dataset Preview",
    expanded=False,
):
    preview_columns = [
        column
        for column in [
            "Date",
            "Building",
            "Department",
            "Appliance",
            "Energy_kWh",
            "Energy_Waste_kWh",
            "Renewable_kWh",
            "Carbon_kgCO2",
            "AI_Anomaly",
        ]
        if column in df.columns
    ]

    if preview_columns:
        st.dataframe(
            df[preview_columns].head(20),
            width="stretch",
            hide_index=True,
        )
    else:
        st.dataframe(
            df.head(20),
            width="stretch",
            hide_index=True,
        )


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

render_footer()