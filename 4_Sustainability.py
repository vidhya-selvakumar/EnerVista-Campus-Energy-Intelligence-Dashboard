from __future__ import annotations

import streamlit as st

from utils.data_loader import load_data
from utils.calculations import (
    building_sustainability_summary,
    carbon_intensity,
    carbon_reduction_from_renewables,
    non_renewable_energy,
    renewable_percentage,
    sustainability_kpis,
    total_carbon,
    total_energy,
    total_renewable_energy,
    waste_percentage,
)
from utils.charts import (
    carbon_emission_chart,
    carbon_vs_renewable_chart,
    renewable_energy_chart,
    renewable_gauge,
    sustainability_gauge,
)
from utils.filters import (
    filter_summary_text,
    show_filter_status,
    sustainability_filters,
)
from utils.theme import load_global_styles


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="EnerVista | Sustainability",
    page_icon="◉",
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
            <div class="ev-page-title">Sustainability</div>
            <div class="ev-page-subtitle">
                Monitor renewable energy adoption, carbon emissions,
                energy efficiency and environmental performance.
            </div>
        </div>
        <div class="ev-badge ev-badge-success">
            Sustainability Intelligence
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# FILTERS
# ---------------------------------------------------------

filtered_df, filter_state = sustainability_filters(df)

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
                Adjust the sustainability filters to continue the analysis.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()


# ---------------------------------------------------------
# CALCULATE CORE METRICS
# ---------------------------------------------------------

energy = total_energy(filtered_df)
renewable = total_renewable_energy(filtered_df)
renewable_pct = renewable_percentage(filtered_df)
non_renewable = non_renewable_energy(filtered_df)

carbon = total_carbon(filtered_df)
carbon_intensity_value = carbon_intensity(filtered_df)
carbon_avoided = carbon_reduction_from_renewables(filtered_df)

waste_pct = waste_percentage(filtered_df)

sustainability_data = sustainability_kpis(filtered_df)

# Use the centralized score when available.
sustainability_score = sustainability_data.get("sustainability_score")

# Safe fallback if the KPI bundle does not expose the score.
if sustainability_score is None:
    renewable_component = min(max(renewable_pct, 0.0), 100.0) * 0.50
    efficiency_component = max(0.0, min(100.0 - waste_pct, 100.0)) * 0.25
    carbon_component = max(
        0.0,
        min(100.0, 100.0 - (carbon_intensity_value * 10.0)),
    ) * 0.25

    sustainability_score = (
        renewable_component
        + efficiency_component
        + carbon_component
    )

sustainability_score = max(
    0.0,
    min(100.0, float(sustainability_score)),
)


# ---------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">Environmental performance</div>
        <div class="ev-section-subtitle">
            Key sustainability indicators for the selected period and filters.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

kpi_cols = st.columns(5)

with kpi_cols[0]:
    st.metric(
        "Sustainability Score",
        f"{sustainability_score:.1f}/100",
    )

with kpi_cols[1]:
    st.metric(
        "Renewable Energy",
        f"{renewable:,.1f} kWh",
    )

with kpi_cols[2]:
    st.metric(
        "Renewable Share",
        f"{renewable_pct:.1f}%",
    )

with kpi_cols[3]:
    st.metric(
        "Carbon Emissions",
        f"{carbon:,.1f} kgCO₂",
    )

with kpi_cols[4]:
    st.metric(
        "Carbon Intensity",
        f"{carbon_intensity_value:.3f} kgCO₂/kWh",
    )


# ---------------------------------------------------------
# SUSTAINABILITY SCORE + RENEWABLE GAUGE
# ---------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">Sustainability scorecard</div>
        <div class="ev-section-subtitle">
            Visual assessment of the selected energy portfolio.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

score_col, renewable_col, summary_col = st.columns([1, 1, 1.4])

with score_col:
    st.plotly_chart(
        sustainability_gauge(
            sustainability_score,
            title="Sustainability Score",
            maximum=100,
        ),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with renewable_col:
    st.plotly_chart(
        renewable_gauge(renewable_pct),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with summary_col:
    st.markdown(
        """
        <div class="ev-insight-card">
            <h4>Portfolio sustainability summary</h4>
        """,
        unsafe_allow_html=True,
    )

    st.write(
        f"""
        **Total energy:** {energy:,.1f} kWh

        **Renewable energy:** {renewable:,.1f} kWh

        **Non-renewable energy:** {non_renewable:,.1f} kWh

        **Renewable contribution:** {renewable_pct:.1f}%

        **Carbon emissions:** {carbon:,.1f} kgCO₂

        **Estimated carbon benefit from renewables:** {carbon_avoided:,.1f} kgCO₂
        """
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# RENEWABLE ENERGY TREND
# ---------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">Renewable energy trend</div>
        <div class="ev-section-subtitle">
            Daily renewable energy contribution across the selected period.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.plotly_chart(
    renewable_energy_chart(filtered_df),
    use_container_width=True,
    config={"displayModeBar": False},
)


# ---------------------------------------------------------
# CARBON EMISSIONS
# ---------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">Carbon emissions trend</div>
        <div class="ev-section-subtitle">
            Track daily carbon emissions generated by energy consumption.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.plotly_chart(
    carbon_emission_chart(filtered_df),
    use_container_width=True,
    config={"displayModeBar": False},
)


# ---------------------------------------------------------
# ENERGY VS RENEWABLE
# ---------------------------------------------------------

left_col, right_col = st.columns(2)

with left_col:
    st.markdown(
        """
        <div class="ev-section">
            <div class="ev-section-title">Energy and renewable relationship</div>
            <div class="ev-section-subtitle">
                Compare renewable contribution with overall energy activity.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        carbon_vs_renewable_chart(filtered_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with right_col:
    st.markdown(
        """
        <div class="ev-section">
            <div class="ev-section-title">Efficiency indicators</div>
            <div class="ev-section-subtitle">
                Additional indicators supporting sustainability decisions.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    indicator_cols = st.columns(2)

    with indicator_cols[0]:
        st.markdown(
            f"""
            <div class="ev-metric-card">
                <div class="ev-metric-label">Energy Waste</div>
                <div class="ev-metric-value">{waste_pct:.1f}%</div>
                <div class="ev-metric-help">
                    Share of energy identified as waste.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with indicator_cols[1]:
        st.markdown(
            f"""
            <div class="ev-metric-card">
                <div class="ev-metric-label">Carbon Avoided</div>
                <div class="ev-metric-value">{carbon_avoided:,.1f}</div>
                <div class="ev-metric-help">
                    Estimated kgCO₂ benefit from renewable energy.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------
# BUILDING SUSTAINABILITY PERFORMANCE
# ---------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">Building sustainability performance</div>
        <div class="ev-section-subtitle">
            Compare energy, renewable contribution and carbon performance
            across buildings.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

building_summary = building_sustainability_summary(filtered_df)

if not building_summary.empty:
    st.dataframe(
        building_summary,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Building-level sustainability data is unavailable.")


# ---------------------------------------------------------
# SUSTAINABILITY INSIGHTS
# ---------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">Sustainability insights</div>
        <div class="ev-section-subtitle">
            Decision-oriented interpretation of the current sustainability state.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

insight_col1, insight_col2, insight_col3 = st.columns(3)

with insight_col1:
    if renewable_pct >= 50:
        renewable_message = (
            "Renewable energy provides a strong contribution to the "
            "selected energy portfolio."
        )
    elif renewable_pct >= 20:
        renewable_message = (
            "Renewable energy has a meaningful contribution, but there is "
            "additional opportunity to increase its share."
        )
    else:
        renewable_message = (
            "Renewable contribution is relatively low. Increasing renewable "
            "generation or procurement could improve sustainability."
        )

    st.markdown(
        f"""
        <div class="ev-insight-card">
            <h4>Renewable adoption</h4>
            <p>{renewable_message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with insight_col2:
    if waste_pct <= 5:
        waste_message = (
            "Energy waste is currently controlled at a relatively low level."
        )
    elif waste_pct <= 15:
        waste_message = (
            "Moderate energy waste is present. Operational optimization "
            "could improve efficiency."
        )
    else:
        waste_message = (
            "High energy waste indicates a significant opportunity for "
            "energy-efficiency improvements."
        )

    st.markdown(
        f"""
        <div class="ev-insight-card">
            <h4>Energy efficiency</h4>
            <p>{waste_message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with insight_col3:
    if sustainability_score >= 75:
        score_message = (
            "The selected portfolio demonstrates strong overall "
            "sustainability performance."
        )
    elif sustainability_score >= 50:
        score_message = (
            "Sustainability performance is moderate and has clear scope "
            "for improvement."
        )
    else:
        score_message = (
            "The current sustainability profile requires focused "
            "intervention across energy, waste and renewable adoption."
        )

    st.markdown(
        f"""
        <div class="ev-insight-card">
            <h4>Overall assessment</h4>
            <p>{score_message}</p>
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
        <div class="ev-section-title">Recommended actions</div>
        <div class="ev-section-subtitle">
            Practical actions based on the current sustainability indicators.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

recommendations = []

if renewable_pct < 20:
    recommendations.append(
        "Increase renewable energy adoption through additional on-site "
        "generation or renewable energy procurement."
    )
elif renewable_pct < 50:
    recommendations.append(
        "Evaluate buildings with lower renewable contribution and prioritize "
        "renewable integration where technically and economically feasible."
    )
else:
    recommendations.append(
        "Maintain the current renewable-energy strategy and evaluate "
        "opportunities for further optimization."
    )

if waste_pct > 15:
    recommendations.append(
        "Prioritize high-waste buildings and departments for energy audits, "
        "equipment optimization and operational controls."
    )
elif waste_pct > 5:
    recommendations.append(
        "Investigate recurring waste patterns and improve operating schedules "
        "for energy-intensive equipment."
    )
else:
    recommendations.append(
        "Continue monitoring waste patterns to preserve the current efficiency "
        "level."
    )

if carbon_intensity_value > 0:
    recommendations.append(
        "Track carbon intensity over time and use renewable adoption and "
        "energy-efficiency programs to reduce emissions per kWh consumed."
    )

for recommendation in recommendations:
    st.markdown(
        f"""
        <div class="ev-recommendation">
            <strong>Action</strong>
            <p>{recommendation}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# EXPORT
# ---------------------------------------------------------

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">Sustainability data export</div>
        <div class="ev-section-subtitle">
            Download the filtered sustainability dataset for further analysis.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

csv_data = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download filtered sustainability data",
    data=csv_data,
    file_name="EnerVista_Sustainability_Data.csv",
    mime="text/csv",
)


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.markdown(
    """
    <div class="ev-footer">
        EnerVista Sustainability Intelligence • Renewable energy •
        Carbon management • Energy efficiency
    </div>
    """,
    unsafe_allow_html=True,
)