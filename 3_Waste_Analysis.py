from pathlib import Path

import streamlit as st

from utils.calculations import (
    average_energy_waste,
    building_waste_summary,
    department_waste_summary,
    estimated_waste_cost,
    total_energy,
    total_energy_waste,
    waste_kpis,
    waste_percentage,
    waste_reason_summary,
    useful_energy,
    top_waste_buildings,
)
from utils.charts import (
    building_waste_chart,
    energy_waste_trend_chart,
    waste_reason_chart,
)
from utils.data_loader import load_data
from utils.filters import (
    filter_summary_text,
    show_filter_status,
    waste_analysis_filters,
)


# ============================================================
# EnerVista
# Waste Analysis
# ============================================================


# ------------------------------------------------------------
# Page Configuration
# ------------------------------------------------------------

st.set_page_config(
    page_title="Waste Analysis | EnerVista",
    page_icon="♻",
    layout="wide",
)


# ------------------------------------------------------------
# Global Styles
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSS_FILE = PROJECT_ROOT / "assets" / "styles.css"


def load_css() -> None:
    """Load the global EnerVista stylesheet."""

    if not CSS_FILE.exists():
        return

    try:
        css = CSS_FILE.read_text(encoding="utf-8")

        st.markdown(
            f"<style>{css}</style>",
            unsafe_allow_html=True,
        )

    except Exception:
        pass


load_css()


# ------------------------------------------------------------
# Header
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-page-header">
        <div class="ev-page-title">
            Waste Analysis
        </div>
        <div class="ev-page-subtitle">
            Identify energy waste patterns, major waste sources,
            high-risk buildings and potential cost-saving opportunities.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# Data Loading
# ------------------------------------------------------------

@st.cache_data(show_spinner=False, ttl=3600)
def get_data():
    """Load the prepared EnerVista dataset."""

    return load_data()


try:
    df = get_data()

except FileNotFoundError:
    st.error("EnerVista dataset was not found.")

    st.info(
        "Verify that "
        "`data/EnerVista_10000_Enhanced_Dataset.xlsx` "
        "exists inside the project."
    )

    st.stop()

except Exception as exc:
    st.error("Unable to load the EnerVista dataset.")
    st.exception(exc)
    st.stop()


if df is None or df.empty:
    st.warning(
        "No records are available for waste analysis."
    )
    st.stop()


# ------------------------------------------------------------
# Waste Filters
# ------------------------------------------------------------

filtered_df, filter_state = waste_analysis_filters(df)


if filtered_df is None or filtered_df.empty:
    st.warning(
        "No records match the selected filters."
    )

    st.info(
        "Adjust the filters in the sidebar and try again."
    )

    st.stop()


# ------------------------------------------------------------
# Filter Status
# ------------------------------------------------------------

show_filter_status(filter_state)

st.caption(
    filter_summary_text(filter_state)
)


# ------------------------------------------------------------
# Formatting Helpers
# ------------------------------------------------------------

def number(value, decimals: int = 1) -> str:
    """Format numeric values."""

    try:
        value = float(value)

        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"

        if abs(value) >= 1_000:
            return f"{value / 1_000:.2f}K"

        return f"{value:,.{decimals}f}"

    except (TypeError, ValueError):
        return "0"


def currency(value) -> str:
    """Format INR currency."""

    try:
        value = float(value)

        if abs(value) >= 1_000_000:
            return f"₹{value / 1_000_000:.2f}M"

        if abs(value) >= 1_000:
            return f"₹{value / 1_000:.2f}K"

        return f"₹{value:,.2f}"

    except (TypeError, ValueError):
        return "₹0.00"


def percent(value) -> str:
    """Format percentage."""

    try:
        return f"{float(value):.1f}%"

    except (TypeError, ValueError):
        return "0.0%"


# ------------------------------------------------------------
# KPI Section
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Waste Performance
        </div>
        <div class="ev-section-subtitle">
            Key waste indicators calculated for the current selection.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


kpis = waste_kpis(filtered_df)


kpi_columns = st.columns(5)


with kpi_columns[0]:
    st.metric(
        "Total Energy",
        f"{number(total_energy(filtered_df))} kWh",
    )


with kpi_columns[1]:
    st.metric(
        "Total Waste",
        f"{number(total_energy_waste(filtered_df))} kWh",
    )


with kpi_columns[2]:
    st.metric(
        "Waste Rate",
        percent(waste_percentage(filtered_df)),
    )


with kpi_columns[3]:
    st.metric(
        "Estimated Waste Cost",
        currency(estimated_waste_cost(filtered_df)),
    )


with kpi_columns[4]:
    st.metric(
        "Useful Energy",
        f"{number(useful_energy(filtered_df))} kWh",
    )


# ------------------------------------------------------------
# Waste Trend
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Energy Waste Trend
        </div>
        <div class="ev-section-subtitle">
            Daily movement of energy consumption and identified waste.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


st.plotly_chart(
    energy_waste_trend_chart(filtered_df),
    use_container_width=True,
)


# ------------------------------------------------------------
# Waste Distribution
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Waste Distribution
        </div>
        <div class="ev-section-subtitle">
            Understand where waste originates and which locations
            contribute most to the total.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


distribution_left, distribution_right = st.columns(2)


with distribution_left:

    st.plotly_chart(
        waste_reason_chart(filtered_df),
        use_container_width=True,
    )


with distribution_right:

    st.plotly_chart(
        building_waste_chart(filtered_df),
        use_container_width=True,
    )


# ------------------------------------------------------------
# Waste Reasons
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Waste Reason Analysis
        </div>
        <div class="ev-section-subtitle">
            Ranked summary of the operational reasons associated
            with recorded energy waste.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


reason_df = waste_reason_summary(
    filtered_df
)


if reason_df.empty:

    st.info(
        "No waste-reason information is available "
        "for the selected filters."
    )

else:

    st.dataframe(
        reason_df,
        use_container_width=True,
        hide_index=True,
    )


# ------------------------------------------------------------
# High-Waste Buildings
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            High-Waste Buildings
        </div>
        <div class="ev-section-subtitle">
            Buildings ranked according to their recorded energy waste.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


building_waste_df = top_waste_buildings(
    filtered_df,
    n=10,
)


if building_waste_df.empty:

    st.info(
        "No building-level waste information is available."
    )

else:

    st.dataframe(
        building_waste_df,
        use_container_width=True,
        hide_index=True,
    )


# ------------------------------------------------------------
# Building Waste Detail
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Building Waste Comparison
        </div>
        <div class="ev-section-subtitle">
            Detailed comparison of energy consumption and waste
            across individual buildings.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


building_summary = building_waste_summary(
    filtered_df
)


if building_summary.empty:

    st.info(
        "No building waste data is available."
    )

else:

    st.dataframe(
        building_summary,
        use_container_width=True,
        hide_index=True,
    )


# ------------------------------------------------------------
# Department Waste Analysis
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Department Waste Analysis
        </div>
        <div class="ev-section-subtitle">
            Identify departments with significant energy waste.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


department_summary = department_waste_summary(
    filtered_df
)


if department_summary.empty:

    st.info(
        "No department-level waste information is available."
    )

else:

    st.dataframe(
        department_summary,
        use_container_width=True,
        hide_index=True,
    )


# ------------------------------------------------------------
# Waste Efficiency Indicators
# ------------------------------------------------------------

total_energy_value = float(
    total_energy(filtered_df) or 0
)

total_waste_value = float(
    total_energy_waste(filtered_df) or 0
)

useful_energy_value = float(
    useful_energy(filtered_df) or 0
)

avg_waste_value = float(
    average_energy_waste(filtered_df) or 0
)

waste_rate_value = float(
    waste_percentage(filtered_df) or 0
)

waste_cost_value = float(
    estimated_waste_cost(filtered_df) or 0
)


st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Waste Efficiency Indicators
        </div>
        <div class="ev-section-subtitle">
            Operational interpretation of the selected waste profile.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


indicator_columns = st.columns(4)


with indicator_columns[0]:

    st.metric(
        "Average Waste",
        f"{number(avg_waste_value)} kWh",
    )


with indicator_columns[1]:

    st.metric(
        "Waste Rate",
        percent(waste_rate_value),
    )


with indicator_columns[2]:

    st.metric(
        "Useful Energy",
        f"{number(useful_energy_value)} kWh",
    )


with indicator_columns[3]:

    st.metric(
        "Potential Cost Exposure",
        currency(waste_cost_value),
    )


# ------------------------------------------------------------
# Automated Waste Insights
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Waste Insights
        </div>
        <div class="ev-section-subtitle">
            Rule-based observations derived from the current dataset.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


insight_columns = st.columns(3)


with insight_columns[0]:

    if waste_rate_value >= 20:

        message = (
            "The current waste ratio is relatively high. "
            "Priority should be given to identifying recurring "
            "operational waste sources."
        )

    elif waste_rate_value >= 10:

        message = (
            "The selected records show a moderate level of "
            "energy waste. Targeted operational improvements "
            "may provide measurable savings."
        )

    else:

        message = (
            "The recorded waste ratio is comparatively low "
            "within the selected scope. Continued monitoring "
            "can help maintain performance."
        )

    st.markdown(
        f"""
        <div class="ev-insight-card">
            <div class="ev-insight-title">
                Waste Exposure
            </div>
            <div class="ev-insight-text">
                {message}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with insight_columns[1]:

    if building_waste_df.empty:

        building_message = (
            "There is insufficient building-level information "
            "to identify a dominant waste location."
        )

    else:

        first_row = building_waste_df.iloc[0]

        building_name = first_row.get(
            "Building",
            "Top building",
        )

        building_message = (
            f"<b>{building_name}</b> currently appears "
            "among the highest waste contributors in the "
            "selected scope. This location can be prioritized "
            "for further investigation."
        )

    st.markdown(
        f"""
        <div class="ev-insight-card">
            <div class="ev-insight-title">
                Priority Location
            </div>
            <div class="ev-insight-text">
                {building_message}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with insight_columns[2]:

    if total_energy_value > 0:

        avoidable_share = (
            total_waste_value /
            total_energy_value
        ) * 100

    else:

        avoidable_share = 0

    st.markdown(
        f"""
        <div class="ev-insight-card">
            <div class="ev-insight-title">
                Savings Opportunity
            </div>
            <div class="ev-insight-text">
                Approximately
                <b>{number(total_waste_value)} kWh</b>
                is classified as waste, representing
                <b>{percent(avoidable_share)}</b>
                of the selected energy consumption.
                The corresponding estimated cost exposure is
                <b>{currency(waste_cost_value)}</b>.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# Waste Reduction Priorities
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Waste Reduction Priorities
        </div>
        <div class="ev-section-subtitle">
            Recommended operational focus areas based on waste behavior.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


recommendations = []


if waste_rate_value >= 15:

    recommendations.append(
        (
            "Investigate high-waste operations",
            "Review the highest-consuming and highest-waste buildings "
            "for recurring operational inefficiencies.",
        )
    )

if waste_cost_value > 0:

    recommendations.append(
        (
            "Prioritize financially significant waste",
            "Focus corrective actions on waste sources with the "
            "largest estimated cost impact.",
        )
    )

if not reason_df.empty:

    recommendations.append(
        (
            "Address recurring waste reasons",
            "Use the waste-reason ranking to identify operational "
            "causes that appear repeatedly in the selected period.",
        )
    )

recommendations.append(
    (
        "Monitor waste continuously",
        "Track daily energy waste alongside total consumption "
        "to determine whether corrective actions are reducing waste.",
    )
)


for title, text in recommendations:

    st.markdown(
        f"""
        <div class="ev-recommendation">
            <div class="ev-recommendation-title">
                {title}
            </div>
            <div class="ev-recommendation-text">
                {text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# Detailed Waste Tables
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Detailed Waste Data
        </div>
        <div class="ev-section-subtitle">
            Inspect the aggregated waste information by reason,
            building and department.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


waste_tabs = st.tabs(
    [
        "Waste Reasons",
        "Buildings",
        "Departments",
    ]
)


with waste_tabs[0]:

    if reason_df.empty:
        st.info("No waste-reason data available.")
    else:
        st.dataframe(
            reason_df,
            use_container_width=True,
            hide_index=True,
        )


with waste_tabs[1]:

    if building_summary.empty:
        st.info("No building waste data available.")
    else:
        st.dataframe(
            building_summary,
            use_container_width=True,
            hide_index=True,
        )


with waste_tabs[2]:

    if department_summary.empty:
        st.info("No department waste data available.")
    else:
        st.dataframe(
            department_summary,
            use_container_width=True,
            hide_index=True,
        )


# ------------------------------------------------------------
# Export
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Waste Data Export
        </div>
        <div class="ev-section-subtitle">
            Download the filtered records for external reporting
            or detailed investigation.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


csv_data = filtered_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="Download Filtered Waste Dataset",
    data=csv_data,
    file_name="EnerVista_Waste_Analysis_Data.csv",
    mime="text/csv",
)


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-footer">
        <strong>EnerVista Waste Analysis</strong>
        &nbsp;•&nbsp;
        Energy Waste Detection & Reduction Intelligence
    </div>
    """,
    unsafe_allow_html=True,
)