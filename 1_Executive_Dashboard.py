from pathlib import Path

import streamlit as st

from utils.calculations import (
    executive_kpis,
    top_energy_consumers,
    top_waste_buildings,
)
from utils.charts import (
    building_energy_chart,
    daily_energy_chart,
    energy_waste_trend_chart,
    renewable_energy_chart,
    top_energy_consumers_chart,
)
from utils.data_loader import load_data
from utils.filters import (
    executive_filters,
    filter_summary_text,
    show_filter_status,
)


# ============================================================
# EnerVista
# Executive Dashboard
# ============================================================


# ------------------------------------------------------------
# Page Configuration
# ------------------------------------------------------------

st.set_page_config(
    page_title="Executive Dashboard | EnerVista",
    page_icon="▣",
    layout="wide",
)


# ------------------------------------------------------------
# Load Global Styles
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
        # Styling failure should never prevent analytics from loading.
        pass


load_css()


# ------------------------------------------------------------
# Page Header
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-page-header">
        <div class="ev-page-title">
            Executive Dashboard
        </div>
        <div class="ev-page-subtitle">
            Enterprise-level visibility into energy consumption,
            cost, waste, renewable energy and carbon performance.
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
    st.error(
        "EnerVista dataset was not found."
    )
    st.info(
        "Verify that "
        "`data/EnerVista_10000_Enhanced_Dataset.xlsx` "
        "exists inside the project."
    )
    st.stop()

except Exception as exc:
    st.error(
        "Unable to load the EnerVista dataset."
    )
    st.exception(exc)
    st.stop()


if df is None or df.empty:
    st.warning(
        "No records are available for the Executive Dashboard."
    )
    st.stop()


# ------------------------------------------------------------
# Executive Filters
# ------------------------------------------------------------

filtered_df, filter_state = executive_filters(df)


if filtered_df is None or filtered_df.empty:
    st.warning(
        "No records match the selected filters."
    )

    st.info(
        "Try widening the date range or removing one or more "
        "sidebar filters."
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
# KPI Calculations
# ------------------------------------------------------------

kpis = executive_kpis(filtered_df)


# ------------------------------------------------------------
# Safe Formatting
# ------------------------------------------------------------

def format_energy(value) -> str:
    """Format energy values in kWh."""

    try:
        value = float(value)

        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"

        if abs(value) >= 1_000:
            return f"{value / 1_000:.2f}K"

        return f"{value:,.1f}"

    except (TypeError, ValueError):
        return "0.0"


def format_currency(value) -> str:
    """Format currency values in INR."""

    try:
        value = float(value)

        if abs(value) >= 1_000_000:
            return f"₹{value / 1_000_000:.2f}M"

        if abs(value) >= 1_000:
            return f"₹{value / 1_000:.2f}K"

        return f"₹{value:,.2f}"

    except (TypeError, ValueError):
        return "₹0.00"


def format_percentage(value) -> str:
    """Format percentage values."""

    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return "0.0%"


# ------------------------------------------------------------
# KPI Header
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Executive Performance
        </div>
        <div class="ev-section-subtitle">
            Key performance indicators for the currently selected scope.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


kpi_columns = st.columns(5)


with kpi_columns[0]:
    st.metric(
        "Total Energy",
        f"{format_energy(kpis.get('total_energy', 0))} kWh",
        help="Total recorded energy consumption.",
    )


with kpi_columns[1]:
    st.metric(
        "Energy Waste",
        f"{format_energy(kpis.get('total_energy_waste', 0))} kWh",
        help="Estimated energy classified as waste.",
    )


with kpi_columns[2]:
    st.metric(
        "Energy Cost",
        format_currency(kpis.get("total_cost", 0)),
        help="Total recorded energy cost.",
    )


with kpi_columns[3]:
    st.metric(
        "Renewable Share",
        format_percentage(
            kpis.get("renewable_percentage", 0)
        ),
        help="Renewable energy as a percentage of total energy.",
    )


with kpi_columns[4]:
    st.metric(
        "Carbon Emissions",
        f"{format_energy(kpis.get('total_carbon', 0))} kg",
        help="Total recorded carbon emissions.",
    )


# ------------------------------------------------------------
# Primary Trend Analysis
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Energy Performance Trend
        </div>
        <div class="ev-section-subtitle">
            Daily energy consumption and waste movement across the
            selected period.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


trend_left, trend_right = st.columns(2)


with trend_left:
    st.plotly_chart(
        daily_energy_chart(filtered_df),
        use_container_width=True,
    )


with trend_right:
    st.plotly_chart(
        energy_waste_trend_chart(filtered_df),
        use_container_width=True,
    )


# ------------------------------------------------------------
# Resource Performance
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Resource Distribution
        </div>
        <div class="ev-section-subtitle">
            Building-level consumption and renewable-energy contribution.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


resource_left, resource_right = st.columns(2)


with resource_left:
    st.plotly_chart(
        building_energy_chart(filtered_df),
        use_container_width=True,
    )


with resource_right:
    st.plotly_chart(
        renewable_energy_chart(filtered_df),
        use_container_width=True,
    )


# ------------------------------------------------------------
# Top Energy Consumers
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Highest Energy Consumers
        </div>
        <div class="ev-section-subtitle">
            Buildings or operational units contributing the greatest
            energy consumption.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


consumer_left, consumer_right = st.columns([1.5, 1])


with consumer_left:
    st.plotly_chart(
        top_energy_consumers_chart(
            filtered_df,
            n=10,
        ),
        use_container_width=True,
    )


with consumer_right:

    consumer_df = top_energy_consumers(
        filtered_df,
        n=10,
    )

    if consumer_df.empty:
        st.info(
            "No energy-consumption ranking is available."
        )

    else:
        display_columns = [
            column
            for column in [
                "Building",
                "Energy_kWh",
            ]
            if column in consumer_df.columns
        ]

        if display_columns:
            st.dataframe(
                consumer_df[display_columns],
                use_container_width=True,
                hide_index=True,
            )


# ------------------------------------------------------------
# Executive Waste Risk
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Waste Risk Overview
        </div>
        <div class="ev-section-subtitle">
            Locations requiring attention based on energy waste levels.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


waste_df = top_waste_buildings(
    filtered_df,
    n=10,
)


if waste_df.empty:

    st.info(
        "No building-level waste information is available "
        "for the selected filters."
    )

else:

    display_columns = [
        column
        for column in [
            "Building",
            "Energy_Waste_kWh",
            "Energy_kWh",
        ]
        if column in waste_df.columns
    ]

    if display_columns:

        st.dataframe(
            waste_df[display_columns],
            use_container_width=True,
            hide_index=True,
        )


# ------------------------------------------------------------
# Executive Interpretation
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Executive Interpretation
        </div>
        <div class="ev-section-subtitle">
            Automated observations generated from the selected dataset.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


total_energy = float(
    kpis.get("total_energy", 0) or 0
)

total_waste = float(
    kpis.get("total_energy_waste", 0) or 0
)

renewable_share = float(
    kpis.get("renewable_percentage", 0) or 0
)

total_cost = float(
    kpis.get("total_cost", 0) or 0
)

total_carbon = float(
    kpis.get("total_carbon", 0) or 0
)


if total_energy > 0:
    waste_ratio = (
        total_waste / total_energy
    ) * 100
else:
    waste_ratio = 0.0


insight_columns = st.columns(3)


with insight_columns[0]:

    st.markdown(
        f"""
        <div class="ev-insight-card">
            <div class="ev-insight-title">
                Energy Efficiency
            </div>
            <div class="ev-insight-text">
                Total consumption is
                <b>{format_energy(total_energy)} kWh</b>,
                with approximately
                <b>{format_percentage(waste_ratio)}</b>
                classified as energy waste.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with insight_columns[1]:

    st.markdown(
        f"""
        <div class="ev-insight-card">
            <div class="ev-insight-title">
                Renewable Contribution
            </div>
            <div class="ev-insight-text">
                Renewable sources contribute
                <b>{format_percentage(renewable_share)}</b>
                of the recorded energy profile.
                Increasing this contribution can support
                long-term sustainability objectives.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with insight_columns[2]:

    st.markdown(
        f"""
        <div class="ev-insight-card">
            <div class="ev-insight-title">
                Financial & Carbon Exposure
            </div>
            <div class="ev-insight-text">
                The selected scope represents approximately
                <b>{format_currency(total_cost)}</b>
                in energy cost and
                <b>{format_energy(total_carbon)} kg</b>
                of recorded carbon emissions.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# Export
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Executive Data Export
        </div>
        <div class="ev-section-subtitle">
            Download the filtered dataset for further analysis or reporting.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


csv_data = filtered_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="Download Filtered Executive Dataset",
    data=csv_data,
    file_name="EnerVista_Executive_Filtered_Data.csv",
    mime="text/csv",
)


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

st.markdown(
    """
    <div class="ev-footer">
        <strong>EnerVista Executive Dashboard</strong>
        &nbsp;•&nbsp;
        Energy Intelligence & Decision Visualization Platform
    </div>
    """,
    unsafe_allow_html=True,
)