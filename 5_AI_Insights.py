from __future__ import annotations

import streamlit as st

from utils.data_loader import load_data
from utils.calculations import (
    ai_kpis,
    anomaly_by_building,
    anomaly_count,
    anomaly_percentage,
    anomaly_summary,
    average_energy,
    average_occupancy,
    average_power_factor,
    average_temperature,
    building_energy_summary,
    maintenance_summary,
    top_energy_consumers,
)
from utils.charts import (
    ai_anomaly_chart,
    anomaly_by_building_chart,
    building_energy_chart,
    occupancy_energy_chart,
    power_factor_chart,
)
from utils.filters import (
    ai_insights_filters,
    filter_summary_text,
    show_filter_status,
)
from utils.theme import load_global_styles


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="EnerVista | AI Insights",
    page_icon="✦",
    layout="wide",
)

load_global_styles()


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

df = load_data()

if df.empty:
    st.error("No valid energy dataset is available.")
    st.stop()


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.markdown(
    """
    <div class="ev-page-header">
        <div>
            <div class="ev-page-title">AI Insights</div>
            <div class="ev-page-subtitle">
                Detect abnormal energy behaviour, identify high-impact
                buildings and generate data-driven operational insights.
            </div>
        </div>
        <div class="ev-badge ev-badge-info">
            AI-Powered Intelligence
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# FILTERS
# ---------------------------------------------------------

filtered_df, filter_state = ai_insights_filters(df)

show_filter_status(filter_state)

st.markdown(
    f"""
    <div class="ev-filter-summary">
        <strong>Active analysis:</strong>
        {filter_summary_text(filter_state)}
    </div>
    """,
    unsafe_allow_html=True,
)


if filtered_df.empty:
    st.markdown(
        """
        <div class="ev-empty-state">
            <h3>No data matches the selected filters</h3>
            <p>
                Adjust the AI insight filters to continue the analysis.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()


# ---------------------------------------------------------
# AI KPI ENGINE
# ---------------------------------------------------------

kpis = ai_kpis(filtered_df)

anomalies = anomaly_count(filtered_df)
anomaly_pct = anomaly_percentage(filtered_df)
avg_energy = average_energy(filtered_df)
avg_occupancy = average_occupancy(filtered_df)
avg_pf = average_power_factor(filtered_df)
avg_temperature = average_temperature(filtered_df)


# ---------------------------------------------------------
# KPI SECTION
# ---------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">AI monitoring overview</div>
        <div class="ev-section-subtitle">
            Key indicators generated from the selected energy dataset.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

kpi_cols = st.columns(5)

with kpi_cols[0]:
    st.metric(
        "AI Anomalies",
        f"{anomalies:,}",
    )

with kpi_cols[1]:
    st.metric(
        "Anomaly Rate",
        f"{anomaly_pct:.1f}%",
    )

with kpi_cols[2]:
    st.metric(
        "Average Energy",
        f"{avg_energy:,.1f} kWh",
    )

with kpi_cols[3]:
    st.metric(
        "Average Occupancy",
        f"{avg_occupancy:,.1f}",
    )

with kpi_cols[4]:
    st.metric(
        "Average Power Factor",
        f"{avg_pf:.3f}",
    )


# ---------------------------------------------------------
# AI STATUS
# ---------------------------------------------------------

if anomaly_pct <= 5:
    ai_status = "Stable"
    ai_status_message = (
        "The selected portfolio shows a relatively low level of "
        "detected abnormal energy behaviour."
    )
elif anomaly_pct <= 15:
    ai_status = "Monitor"
    ai_status_message = (
        "A moderate number of abnormal records were detected. "
        "The affected assets and buildings should be monitored."
    )
else:
    ai_status = "Attention Required"
    ai_status_message = (
        "A high proportion of abnormal records was detected. "
        "Priority investigation is recommended."
    )

st.markdown(
    f"""
    <div class="ev-insight-card">
        <h4>AI operational status: {ai_status}</h4>
        <p>{ai_status_message}</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# ANOMALY TREND
# ---------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">AI anomaly detection</div>
        <div class="ev-section-subtitle">
            Daily abnormal-energy activity across the selected period.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.plotly_chart(
    ai_anomaly_chart(filtered_df),
    use_container_width=True,
    config={"displayModeBar": False},
)


# ---------------------------------------------------------
# ANOMALY BY BUILDING
# ---------------------------------------------------------

left_col, right_col = st.columns(2)

with left_col:
    st.markdown(
        """
        <div class="ev-section">
            <div class="ev-section-title">Anomalies by building</div>
            <div class="ev-section-subtitle">
                Identify locations with the highest abnormal activity.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        anomaly_by_building_chart(filtered_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with right_col:
    st.markdown(
        """
        <div class="ev-section">
            <div class="ev-section-title">Anomaly distribution</div>
            <div class="ev-section-subtitle">
                Summary of detected AI anomaly classifications.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    anomaly_data = anomaly_summary(filtered_df)

    if not anomaly_data.empty:
        st.dataframe(
            anomaly_data,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No anomaly classification data is available.")


# ---------------------------------------------------------
# HIGH-IMPACT ENERGY CONSUMERS
# ---------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">High-impact energy consumers</div>
        <div class="ev-section-subtitle">
            Buildings and equipment consuming significant amounts of energy.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

top_consumers = top_energy_consumers(filtered_df, n=10)

if not top_consumers.empty:
    st.plotly_chart(
        building_energy_chart(filtered_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.dataframe(
        top_consumers,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No energy-consumption ranking is available.")


# ---------------------------------------------------------
# OCCUPANCY VS ENERGY
# ---------------------------------------------------------

left_col, right_col = st.columns(2)

with left_col:
    st.markdown(
        """
        <div class="ev-section">
            <div class="ev-section-title">Occupancy vs energy</div>
            <div class="ev-section-subtitle">
                Examine how building occupancy relates to energy consumption.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        occupancy_energy_chart(filtered_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with right_col:
    st.markdown(
        """
        <div class="ev-section">
            <div class="ev-section-title">Power-factor behaviour</div>
            <div class="ev-section-subtitle">
                Identify electrical-efficiency patterns associated with
                energy usage.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        power_factor_chart(filtered_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )


# ---------------------------------------------------------
# BUILDING ANOMALY TABLE
# ---------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">Building anomaly intelligence</div>
        <div class="ev-section-subtitle">
            Rank buildings according to detected abnormal-energy activity.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

building_anomalies = anomaly_by_building(filtered_df)

if not building_anomalies.empty:
    st.dataframe(
        building_anomalies,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No building-level anomaly information is available.")


# ---------------------------------------------------------
# MAINTENANCE INTELLIGENCE
# ---------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">Maintenance intelligence</div>
        <div class="ev-section-subtitle">
            Current maintenance status distribution for the selected records.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

maintenance_data = maintenance_summary(filtered_df)

if not maintenance_data.empty:
    st.dataframe(
        maintenance_data,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Maintenance-status information is unavailable.")


# ---------------------------------------------------------
# AI INSIGHTS
# ---------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">Generated AI insights</div>
        <div class="ev-section-subtitle">
            Interpretable findings based on anomaly, consumption and
            operational patterns.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

insight_columns = st.columns(3)

with insight_columns[0]:
    if anomaly_pct > 15:
        message = (
            "A significant abnormal-energy pattern is present. "
            "Prioritize the buildings with the highest anomaly counts."
        )
    elif anomaly_pct > 5:
        message = (
            "Moderate anomaly activity is present. "
            "Investigate repeated abnormal records before they become "
            "persistent efficiency problems."
        )
    else:
        message = (
            "Anomaly activity is relatively low. "
            "Continue monitoring to identify emerging deviations."
        )

    st.markdown(
        f"""
        <div class="ev-insight-card">
            <h4>Anomaly intelligence</h4>
            <p>{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with insight_columns[1]:
    if avg_occupancy > 0 and avg_energy > 0:
        message = (
            "Compare energy consumption against occupancy patterns to "
            "identify periods where consumption appears disproportionate "
            "to building usage."
        )
    else:
        message = (
            "Occupancy and energy data should be monitored together to "
            "improve operational efficiency."
        )

    st.markdown(
        f"""
        <div class="ev-insight-card">
            <h4>Occupancy intelligence</h4>
            <p>{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with insight_columns[2]:
    if avg_pf < 0.85:
        message = (
            "Average power factor is relatively low. "
            "Electrical-system investigation may help improve efficiency."
        )
    else:
        message = (
            "Average power factor is within a comparatively healthy range. "
            "Continue monitoring for abnormal electrical behaviour."
        )

    st.markdown(
        f"""
        <div class="ev-insight-card">
            <h4>Electrical intelligence</h4>
            <p>{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# RECOMMENDATIONS
# ---------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">AI recommendations</div>
        <div class="ev-section-subtitle">
            Recommended actions based on detected patterns.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

recommendations = []

if anomaly_pct > 15:
    recommendations.append(
        "Investigate high-anomaly buildings first and review their "
        "equipment operating patterns."
    )
elif anomaly_pct > 5:
    recommendations.append(
        "Monitor recurring anomaly locations and compare them with "
        "occupancy, working hours and appliance usage."
    )
else:
    recommendations.append(
        "Maintain continuous anomaly monitoring to detect early changes "
        "in energy behaviour."
    )

if avg_pf < 0.85:
    recommendations.append(
        "Review equipment and electrical loads associated with low "
        "power-factor performance."
    )

if avg_occupancy > 0:
    recommendations.append(
        "Compare energy demand during occupied and low-occupancy periods "
        "to identify unnecessary consumption."
    )

if avg_temperature > 30:
    recommendations.append(
        "Review temperature-sensitive equipment and cooling-related "
        "energy consumption for optimization opportunities."
    )

recommendations.append(
    "Use AI anomaly results together with maintenance records before "
    "making equipment-level operational decisions."
)

for recommendation in recommendations:
    st.markdown(
        f"""
        <div class="ev-recommendation">
            <strong>AI recommendation</strong>
            <p>{recommendation}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# FILTERED DATA EXPORT
# ---------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">AI analysis export</div>
        <div class="ev-section-subtitle">
            Download the filtered records for detailed investigation.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

csv_data = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download AI analysis data",
    data=csv_data,
    file_name="EnerVista_AI_Insights_Data.csv",
    mime="text/csv",
)


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.markdown(
    """
    <div class="ev-footer">
        EnerVista AI Insights • Anomaly detection •
        Operational intelligence • Predictive decision support
    </div>
    """,
    unsafe_allow_html=True,
)