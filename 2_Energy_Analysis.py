from __future__ import annotations

import streamlit as st

from utils.data_loader import load_data
from utils.calculations import (
    average_energy,
    average_peak_demand,
    average_power_factor,
    average_occupancy,
    average_temperature,
    building_energy_summary,
    department_energy_summary,
    energy_kpis,
    floor_energy_summary,
    peak_energy,
    top_energy_consumers,
    total_cost,
    total_energy,
)
from utils.charts import (
    appliance_energy_chart,
    building_energy_chart,
    daily_energy_chart,
    department_energy_chart,
    energy_distribution_chart,
    floor_energy_chart,
    power_factor_chart,
    top_energy_consumers_chart,
)
from utils.filters import (
    energy_analysis_filters,
    filter_summary_text,
    show_filter_status,
)
from utils.theme import load_global_styles


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="EnerVista | Energy Analysis",
    page_icon="⚡",
    layout="wide",
)

load_global_styles()


# =========================================================
# LOAD DATA
# =========================================================

df = load_data()

if df.empty:
    st.error("No valid energy dataset is available.")
    st.stop()


# =========================================================
# PAGE HEADER
# =========================================================

st.html(
    """
    <div class="ev-page-header">
        <div>
            <div class="ev-page-title">Energy Analysis</div>
            <div class="ev-page-subtitle">
                Analyze daily energy consumption, demand, cost,
                building performance and electrical behaviour.
            </div>
        </div>

        <div class="ev-badge ev-badge-info">
            Energy Intelligence
        </div>
    </div>
    """
)


# =========================================================
# FILTERS
# =========================================================

filtered_df, filter_state = energy_analysis_filters(df)

show_filter_status(filter_state)

st.html(
    f"""
    <div class="ev-filter-summary">
        <strong>Active analysis:</strong>
        {filter_summary_text(filter_state)}
    </div>
    """
)


# =========================================================
# EMPTY FILTER RESULT
# =========================================================

if filtered_df.empty:
    st.html(
        """
        <div class="ev-empty-state">
            <h3>No data matches the selected filters</h3>
            <p>
                Adjust the Energy Analysis filters to continue.
            </p>
        </div>
        """
    )
    st.stop()


# =========================================================
# KPI CALCULATIONS
# =========================================================

kpis = energy_kpis(filtered_df)

energy_value = total_energy(filtered_df)
cost_value = total_cost(filtered_df)
average_energy_value = average_energy(filtered_df)
peak_energy_value = peak_energy(filtered_df)
average_peak_value = average_peak_demand(filtered_df)
average_occupancy_value = average_occupancy(filtered_df)
average_temperature_value = average_temperature(filtered_df)
average_power_factor_value = average_power_factor(filtered_df)


# =========================================================
# KPI HEADER
# =========================================================

st.html(
    """
    <div class="ev-section">
        <div class="ev-section-title">Energy performance overview</div>
        <div class="ev-section-subtitle">
            Key energy indicators for the selected date range and filters.
        </div>
    </div>
    """
)


# =========================================================
# KPI CARDS
# =========================================================

kpi_cols = st.columns(5)

with kpi_cols[0]:
    st.metric(
        "Total Energy",
        f"{energy_value:,.1f} kWh",
    )

with kpi_cols[1]:
    st.metric(
        "Average Daily Energy",
        f"{average_energy_value:,.1f} kWh",
    )

with kpi_cols[2]:
    st.metric(
        "Peak Demand",
        f"{peak_energy_value:,.1f} kW",
    )

with kpi_cols[3]:
    st.metric(
        "Total Cost",
        f"₹{cost_value:,.0f}",
    )

with kpi_cols[4]:
    st.metric(
        "Power Factor",
        f"{average_power_factor_value:.3f}",
    )


# =========================================================
# SECONDARY METRICS
# =========================================================

secondary_cols = st.columns(4)

with secondary_cols[0]:
    st.html(
        f"""
        <div class="ev-metric-card">
            <div class="ev-metric-label">Average Peak Demand</div>
            <div class="ev-metric-value">
                {average_peak_value:,.2f} kW
            </div>
            <div class="ev-metric-help">
                Average recorded peak demand.
            </div>
        </div>
        """
    )

with secondary_cols[1]:
    st.html(
        f"""
        <div class="ev-metric-card">
            <div class="ev-metric-label">Average Occupancy</div>
            <div class="ev-metric-value">
                {average_occupancy_value:,.1f}
            </div>
            <div class="ev-metric-help">
                Average occupancy across selected records.
            </div>
        </div>
        """
    )

with secondary_cols[2]:
    st.html(
        f"""
        <div class="ev-metric-card">
            <div class="ev-metric-label">Average Temperature</div>
            <div class="ev-metric-value">
                {average_temperature_value:.1f} °C
            </div>
            <div class="ev-metric-help">
                Average recorded temperature.
            </div>
        </div>
        """
    )

with secondary_cols[3]:
    st.html(
        f"""
        <div class="ev-metric-card">
            <div class="ev-metric-label">Peak Energy Record</div>
            <div class="ev-metric-value">
                {peak_energy_value:,.1f} kWh
            </div>
            <div class="ev-metric-help">
                Highest energy-consumption observation.
            </div>
        </div>
        """
    )


# =========================================================
# DAILY ENERGY TREND
# =========================================================

st.html(
    """
    <div class="ev-section">
        <div class="ev-section-title">Daily energy consumption</div>
        <div class="ev-section-subtitle">
            Daily energy consumption across the complete selected period.
        </div>
    </div>
    """
)

st.plotly_chart(
    daily_energy_chart(filtered_df),
    use_container_width=True,
    config={"displayModeBar": False},
    key="energy_analysis_daily_energy",
)


# =========================================================
# ENERGY DISTRIBUTION
# =========================================================

left_col, right_col = st.columns(2)

with left_col:

    st.html(
        """
        <div class="ev-section">
            <div class="ev-section-title">Energy distribution</div>
            <div class="ev-section-subtitle">
                Distribution of energy consumption across the selected data.
            </div>
        </div>
        """
    )

    st.plotly_chart(
        energy_distribution_chart(filtered_df),
        use_container_width=True,
        config={"displayModeBar": False},
        key="energy_analysis_distribution",
    )


with right_col:

    st.html(
        """
        <div class="ev-section">
            <div class="ev-section-title">Electrical efficiency</div>
            <div class="ev-section-subtitle">
                Power-factor behaviour across the selected records.
            </div>
        </div>
        """
    )

    st.plotly_chart(
        power_factor_chart(filtered_df),
        use_container_width=True,
        config={"displayModeBar": False},
        key="energy_analysis_power_factor",
    )


# =========================================================
# BUILDING ANALYSIS
# =========================================================

st.html(
    """
    <div class="ev-section">
        <div class="ev-section-title">Building-wise energy analysis</div>
        <div class="ev-section-subtitle">
            Compare total energy consumption across buildings.
        </div>
    </div>
    """
)

st.plotly_chart(
    building_energy_chart(filtered_df),
    use_container_width=True,
    config={"displayModeBar": False},
    key="energy_analysis_building_energy",
)


# =========================================================
# BUILDING SUMMARY TABLE
# =========================================================

building_summary = building_energy_summary(filtered_df)

if not building_summary.empty:
    st.dataframe(
        building_summary,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Building energy summary is unavailable.")


# =========================================================
# DEPARTMENT ANALYSIS
# =========================================================

st.html(
    """
    <div class="ev-section">
        <div class="ev-section-title">Department-wise energy analysis</div>
        <div class="ev-section-subtitle">
            Identify departments with high energy consumption.
        </div>
    </div>
    """
)

st.plotly_chart(
    department_energy_chart(filtered_df),
    use_container_width=True,
    config={"displayModeBar": False},
    key="energy_analysis_department_energy",
)


# =========================================================
# DEPARTMENT TABLE
# =========================================================

department_summary = department_energy_summary(filtered_df)

if not department_summary.empty:
    st.dataframe(
        department_summary,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Department energy summary is unavailable.")


# =========================================================
# FLOOR ANALYSIS
# =========================================================

st.html(
    """
    <div class="ev-section">
        <div class="ev-section-title">Floor-wise energy analysis</div>
        <div class="ev-section-subtitle">
            Compare energy consumption across floors.
        </div>
    </div>
    """
)

st.plotly_chart(
    floor_energy_chart(filtered_df),
    use_container_width=True,
    config={"displayModeBar": False},
    key="energy_analysis_floor_energy",
)


# =========================================================
# APPLIANCE ANALYSIS
# =========================================================

st.html(
    """
    <div class="ev-section">
        <div class="ev-section-title">Appliance energy analysis</div>
        <div class="ev-section-subtitle">
            Identify appliance categories contributing to energy demand.
        </div>
    </div>
    """
)

st.plotly_chart(
    appliance_energy_chart(filtered_df),
    use_container_width=True,
    config={"displayModeBar": False},
    key="energy_analysis_appliance_energy",
)


# =========================================================
# TOP ENERGY CONSUMERS
# =========================================================

st.html(
    """
    <div class="ev-section">
        <div class="ev-section-title">Top energy consumers</div>
        <div class="ev-section-subtitle">
            Rank the highest-consuming energy categories in the selected data.
        </div>
    </div>
    """
)

st.plotly_chart(
    top_energy_consumers_chart(filtered_df, n=10),
    use_container_width=True,
    config={"displayModeBar": False},
    key="energy_analysis_top_consumers",
)


# =========================================================
# TOP CONSUMER TABLE
# =========================================================

top_consumers = top_energy_consumers(
    filtered_df,
    n=10,
)

if not top_consumers.empty:
    st.dataframe(
        top_consumers,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Top energy consumer information is unavailable.")


# =========================================================
# ENERGY INSIGHTS
# =========================================================

st.html(
    """
    <div class="ev-section">
        <div class="ev-section-title">Energy insights</div>
        <div class="ev-section-subtitle">
            Data-driven observations from the current energy profile.
        </div>
    </div>
    """
)

insight_col1, insight_col2, insight_col3 = st.columns(3)


# =========================================================
# OCCUPANCY INSIGHT
# =========================================================

with insight_col1:

    if average_occupancy_value > 0:
        occupancy_message = (
            f"The selected records show an average occupancy of "
            f"{average_occupancy_value:,.1f}. Compare consumption during "
            "occupied and low-occupancy periods to identify avoidable demand."
        )
    else:
        occupancy_message = (
            "Occupancy information is limited. Combining occupancy with "
            "energy consumption can improve operational analysis."
        )

    st.html(
        f"""
        <div class="ev-insight-card">
            <h4>Occupancy insight</h4>
            <p>{occupancy_message}</p>
        </div>
        """
    )


# =========================================================
# POWER FACTOR INSIGHT
# =========================================================

with insight_col2:

    if average_power_factor_value < 0.85:
        power_factor_message = (
            "The average power factor is relatively low. Review major "
            "electrical loads and equipment that may be contributing to "
            "reduced electrical efficiency."
        )
    else:
        power_factor_message = (
            "The average power factor is comparatively healthy. Continue "
            "monitoring electrical loads for abnormal changes."
        )

    st.html(
        f"""
        <div class="ev-insight-card">
            <h4>Power-factor insight</h4>
            <p>{power_factor_message}</p>
        </div>
        """
    )


# =========================================================
# ENVIRONMENTAL INSIGHT
# =========================================================

with insight_col3:

    if average_temperature_value > 30:
        temperature_message = (
            "The selected records show relatively high average temperature. "
            "Review cooling-related loads and operating schedules."
        )
    else:
        temperature_message = (
            "Temperature conditions appear moderate in the selected records. "
            "Continue monitoring environmental conditions alongside energy use."
        )

    st.html(
        f"""
        <div class="ev-insight-card">
            <h4>Environmental insight</h4>
            <p>{temperature_message}</p>
        </div>
        """
    )


# =========================================================
# RECOMMENDATIONS
# =========================================================

st.html(
    """
    <div class="ev-section">
        <div class="ev-section-title">Energy recommendations</div>
        <div class="ev-section-subtitle">
            Recommended operational actions based on the selected data.
        </div>
    </div>
    """
)

recommendations = []


if peak_energy_value > average_energy_value * 2:
    recommendations.append(
        "Investigate high-energy periods where consumption rises "
        "significantly above the normal average."
    )
else:
    recommendations.append(
        "Continue monitoring daily consumption and establish a stable "
        "baseline for future anomaly detection."
    )


if average_power_factor_value < 0.85:
    recommendations.append(
        "Review low power-factor equipment and electrical loads to "
        "identify opportunities for improved electrical efficiency."
    )


if average_occupancy_value > 0:
    recommendations.append(
        "Compare energy consumption against occupancy levels to identify "
        "energy usage during low-utilization periods."
    )


if average_temperature_value > 30:
    recommendations.append(
        "Review cooling and temperature-sensitive equipment because "
        "higher environmental temperatures can increase energy demand."
    )


recommendations.append(
    "Prioritize the highest-consuming buildings, departments and "
    "appliances for detailed energy-efficiency investigations."
)


for recommendation in recommendations:

    st.html(
        f"""
        <div class="ev-recommendation">
            <strong>Recommended action</strong>
            <p>{recommendation}</p>
        </div>
        """
    )


# =========================================================
# DATA EXPORT
# =========================================================

st.html(
    """
    <div class="ev-section">
        <div class="ev-section-title">Energy analysis export</div>
        <div class="ev-section-subtitle">
            Download the currently filtered dataset for further analysis.
        </div>
    </div>
    """
)

csv_data = filtered_df.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download filtered energy data",
    data=csv_data,
    file_name="EnerVista_Energy_Analysis_Data.csv",
    mime="text/csv",
    key="energy_analysis_download",
)


# =========================================================
# FOOTER
# =========================================================

st.html(
    """
    <div class="ev-footer">
        EnerVista Energy Analysis • Energy consumption •
        Demand • Cost • Electrical efficiency
    </div>
    """
)