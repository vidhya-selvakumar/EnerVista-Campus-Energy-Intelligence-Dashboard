# pages/6_Predictive_Analytics.py

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from utils.data_loader import load_data
from utils.calculations import (
    total_energy,
    total_cost,
    total_carbon,
)
from utils.charts import (
    energy_forecast_chart,
    cost_forecast_chart,
    carbon_forecast_chart,
)
from utils.filters import (
    predictive_filters,
    filter_summary_text,
    show_filter_status,
)
from utils.theme import load_global_styles


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="EnerVista | Predictive Analytics",
    page_icon="◌",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_global_styles()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _safe_number(value, default=0.0):
    """Safely convert a value to float."""

    try:
        if value is None or pd.isna(value):
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def _format_number(value, decimals=2):
    """Format a number for dashboard display."""

    try:
        return f"{float(value):,.{decimals}f}"

    except (TypeError, ValueError):
        return "0.00"


def _build_daily_series(
    df: pd.DataFrame,
    value_column: str,
    aggregation: str = "sum",
) -> pd.DataFrame:
    """
    Create a daily time series while preserving the
    original metric column name.

    Example:
        Energy_kWh -> Date, Energy_kWh
        Cost_INR -> Date, Cost_INR
        Carbon_kgCO2 -> Date, Carbon_kgCO2
    """

    if df is None or df.empty:
        return pd.DataFrame(
            columns=["Date", value_column]
        )

    if "Date" not in df.columns:
        return pd.DataFrame(
            columns=["Date", value_column]
        )

    if value_column not in df.columns:
        return pd.DataFrame(
            columns=["Date", value_column]
        )

    working = df[
        ["Date", value_column]
    ].copy()

    working["Date"] = pd.to_datetime(
        working["Date"],
        errors="coerce",
    )

    working[value_column] = pd.to_numeric(
        working[value_column],
        errors="coerce",
    )

    working = working.dropna(
        subset=[
            "Date",
            value_column,
        ]
    )

    if working.empty:
        return pd.DataFrame(
            columns=["Date", value_column]
        )

    working["Date"] = working["Date"].dt.normalize()

    if aggregation == "mean":

        daily = (
            working
            .groupby(
                "Date",
                as_index=False,
            )[value_column]
            .mean()
        )

    elif aggregation == "max":

        daily = (
            working
            .groupby(
                "Date",
                as_index=False,
            )[value_column]
            .max()
        )

    else:

        daily = (
            working
            .groupby(
                "Date",
                as_index=False,
            )[value_column]
            .sum()
        )

    daily = (
        daily
        .sort_values("Date")
        .reset_index(drop=True)
    )

    return daily


def _build_cost_series(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Create daily operating-cost series."""

    return _build_daily_series(
        df,
        "Cost_INR",
        aggregation="sum",
    )


def _build_carbon_series(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Create daily carbon-emission series."""

    return _build_daily_series(
        df,
        "Carbon_kgCO2",
        aggregation="sum",
    )


def _linear_forecast(
    series: pd.DataFrame,
    value_column: str,
    forecast_days: int,
) -> pd.DataFrame:
    """
    Generate a simple linear trend forecast.

    Historical values are indexed by day and a linear
    trend is extrapolated into the selected future period.
    """

    empty_result = pd.DataFrame(
        columns=[
            "Date",
            value_column,
        ]
    )

    if series is None or series.empty:
        return empty_result

    if "Date" not in series.columns:
        return empty_result

    if value_column not in series.columns:
        return empty_result

    working = series[
        [
            "Date",
            value_column,
        ]
    ].copy()

    working["Date"] = pd.to_datetime(
        working["Date"],
        errors="coerce",
    )

    working[value_column] = pd.to_numeric(
        working[value_column],
        errors="coerce",
    )

    working = working.dropna(
        subset=[
            "Date",
            value_column,
        ]
    )

    working = (
        working
        .sort_values("Date")
        .drop_duplicates(
            subset=["Date"]
        )
        .reset_index(drop=True)
    )

    if working.empty:
        return empty_result

    forecast_days = max(
        int(forecast_days),
        1,
    )

    # --------------------------------------------------------
    # Only one historical observation
    # --------------------------------------------------------

    if len(working) == 1:

        last_date = working[
            "Date"
        ].iloc[-1]

        last_value = _safe_number(
            working[
                value_column
            ].iloc[-1]
        )

        future_dates = pd.date_range(
            start=(
                last_date
                + pd.Timedelta(days=1)
            ),
            periods=forecast_days,
            freq="D",
        )

        future_values = np.repeat(
            last_value,
            forecast_days,
        )

        return pd.DataFrame(
            {
                "Date": future_dates,
                value_column: future_values,
            }
        )

    # --------------------------------------------------------
    # Linear regression
    # --------------------------------------------------------

    x = np.arange(
        len(working),
        dtype=float,
    )

    y = working[
        value_column
    ].to_numpy(
        dtype=float
    )

    valid = (
        np.isfinite(x)
        & np.isfinite(y)
    )

    x = x[valid]
    y = y[valid]

    if len(x) < 2:
        return empty_result

    try:

        slope, intercept = np.polyfit(
            x,
            y,
            1,
        )

    except (
        TypeError,
        ValueError,
        np.linalg.LinAlgError,
    ):

        slope = 0.0
        intercept = float(
            np.nanmean(y)
        )

    future_x = np.arange(
        len(working),
        len(working) + forecast_days,
        dtype=float,
    )

    forecast_values = (
        intercept
        + slope * future_x
    )

    # Energy, cost and carbon should not become negative.

    forecast_values = np.maximum(
        forecast_values,
        0,
    )

    last_date = working[
        "Date"
    ].max()

    future_dates = pd.date_range(
        start=(
            last_date
            + pd.Timedelta(days=1)
        ),
        periods=forecast_days,
        freq="D",
    )

    return pd.DataFrame(
        {
            "Date": future_dates,
            value_column: forecast_values,
        }
    )


def _create_forecast_dataframe(
    history: pd.DataFrame,
    value_column: str,
    forecast_days: int,
) -> pd.DataFrame:
    """Create forecast data from historical observations."""

    return _linear_forecast(
        history,
        value_column,
        forecast_days,
    )


# ============================================================
# LOAD DATA
# ============================================================

try:

    df = load_data()

except Exception as exc:

    st.error(
        f"Unable to load EnerVista dataset: {exc}"
    )

    st.stop()


if df is None or df.empty:

    st.warning(
        "No valid data is available for predictive analytics."
    )

    st.stop()


# ============================================================
# FILTERS
# ============================================================

try:

    filtered_df, filter_state = predictive_filters(
        df
    )

except Exception:

    filtered_df = df.copy()
    filter_state = None


if filtered_df is None or filtered_df.empty:

    st.warning(
        "No records match the selected filters. "
        "Please adjust the filters in the sidebar."
    )

    st.stop()


# ============================================================
# PAGE HEADER
# ============================================================

st.html(
    """
    <div class="ev-page-header">
        <div class="ev-page-title">
            Predictive Analytics
        </div>

        <div class="ev-page-subtitle">
            Forecast future energy consumption, operating cost,
            and carbon emissions using historical daily patterns.
        </div>
    </div>
    """,
)


# ============================================================
# FILTER STATUS
# ============================================================

if filter_state is not None:

    try:

        show_filter_status(
            filter_state
        )

    except Exception:
        pass

    try:

        summary_text = filter_summary_text(
            filter_state
        )

        if summary_text:

            st.caption(
                summary_text
            )

    except Exception:
        pass


# ============================================================
# FORECAST CONFIGURATION
# ============================================================

st.html(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Forecast Configuration
        </div>

        <div class="ev-section-subtitle">
            Configure the forecasting horizon and
            historical analysis settings.
        </div>
    </div>
    """,
)


config_col1, config_col2, config_col3 = st.columns(
    3
)


with config_col1:

    forecast_days = st.selectbox(
        "Forecast horizon",
        options=[
            7,
            14,
            30,
            60,
            90,
        ],
        index=2,
        format_func=lambda x: f"{x} days",
        key="predictive_forecast_horizon",
    )


with config_col2:

    confidence_level = st.selectbox(
        "Forecast confidence",
        options=[
            "Standard",
            "Conservative",
            "Extended",
        ],
        index=0,
        key="predictive_confidence_level",
    )


with config_col3:

    aggregation = st.selectbox(
        "Historical aggregation",
        options=[
            "Daily",
            "Weekly",
        ],
        index=0,
        key="predictive_aggregation",
    )


# ============================================================
# HISTORICAL DAILY SERIES
# ============================================================

historical_daily_energy = _build_daily_series(
    filtered_df,
    "Energy_kWh",
    aggregation="sum",
)

historical_daily_cost = _build_cost_series(
    filtered_df
)

historical_daily_carbon = _build_carbon_series(
    filtered_df
)


# ============================================================
# FORECAST SERIES
# ============================================================

energy_forecast = _create_forecast_dataframe(
    historical_daily_energy,
    "Energy_kWh",
    forecast_days,
)

cost_forecast = _create_forecast_dataframe(
    historical_daily_cost,
    "Cost_INR",
    forecast_days,
)

carbon_forecast = _create_forecast_dataframe(
    historical_daily_carbon,
    "Carbon_kgCO2",
    forecast_days,
)


# ============================================================
# HISTORICAL KPIs
# ============================================================

historical_energy = _safe_number(
    total_energy(
        filtered_df
    )
)

historical_cost = _safe_number(
    total_cost(
        filtered_df
    )
)

historical_carbon = _safe_number(
    total_carbon(
        filtered_df
    )
)


# ============================================================
# FORECAST TOTALS
# ============================================================

forecast_energy_total = 0.0
forecast_cost_total = 0.0
forecast_carbon_total = 0.0


if (
    not energy_forecast.empty
    and "Energy_kWh"
    in energy_forecast.columns
):

    forecast_energy_total = _safe_number(
        energy_forecast[
            "Energy_kWh"
        ].sum()
    )


if (
    not cost_forecast.empty
    and "Cost_INR"
    in cost_forecast.columns
):

    forecast_cost_total = _safe_number(
        cost_forecast[
            "Cost_INR"
        ].sum()
    )


if (
    not carbon_forecast.empty
    and "Carbon_kgCO2"
    in carbon_forecast.columns
):

    forecast_carbon_total = _safe_number(
        carbon_forecast[
            "Carbon_kgCO2"
        ].sum()
    )


# ============================================================
# KPI SECTION
# ============================================================

st.html(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Forecast Summary
        </div>
    </div>
    """,
)


kpi1, kpi2, kpi3, kpi4 = st.columns(
    4
)


with kpi1:

    st.metric(
        label="Historical Energy",
        value=(
            f"{_format_number(historical_energy)} kWh"
        ),
    )


with kpi2:

    st.metric(
        label=(
            f"Forecast Energy ({forecast_days}d)"
        ),
        value=(
            f"{_format_number(forecast_energy_total)} kWh"
        ),
    )


with kpi3:

    st.metric(
        label=(
            f"Forecast Cost ({forecast_days}d)"
        ),
        value=(
            f"₹{_format_number(forecast_cost_total)}"
        ),
    )


with kpi4:

    st.metric(
        label=(
            f"Forecast Carbon ({forecast_days}d)"
        ),
        value=(
            f"{_format_number(forecast_carbon_total)} kgCO₂"
        ),
    )


# ============================================================
# FORECAST ANALYSIS
# ============================================================

st.html(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Forecast Analysis
        </div>

        <div class="ev-section-subtitle">
            Historical performance and projected future trends.
        </div>
    </div>
    """,
)


# ============================================================
# ENERGY FORECAST
# ============================================================

st.markdown(
    "### Energy Consumption Forecast"
)


if (
    not historical_daily_energy.empty
    and not energy_forecast.empty
):

    st.plotly_chart(
        energy_forecast_chart(
            historical_daily_energy,
            energy_forecast,
        ),
        use_container_width=True,
        config={
            "displayModeBar": False
        },
        key="predictive_energy_forecast",
    )

else:

    st.info(
        "Insufficient historical energy data is available "
        "to generate an energy forecast."
    )


# ============================================================
# COST FORECAST
# ============================================================

st.markdown(
    "### Operating Cost Forecast"
)


if not cost_forecast.empty:

    st.plotly_chart(
        cost_forecast_chart(
            cost_forecast
        ),
        use_container_width=True,
        config={
            "displayModeBar": False
        },
        key="predictive_cost_forecast",
    )

else:

    st.info(
        "Insufficient cost data is available "
        "to generate a cost forecast."
    )


# ============================================================
# CARBON FORECAST
# ============================================================

st.markdown(
    "### Carbon Emission Forecast"
)


if not carbon_forecast.empty:

    st.plotly_chart(
        carbon_forecast_chart(
            carbon_forecast
        ),
        use_container_width=True,
        config={
            "displayModeBar": False
        },
        key="predictive_carbon_forecast",
    )

else:

    st.info(
        "Insufficient carbon data is available "
        "to generate a carbon forecast."
    )


# ============================================================
# FORECAST INTERPRETATION
# ============================================================

st.markdown(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Forecast Interpretation
        </div>

        <div class="ev-section-subtitle">
            Key observations from the projected operating trend.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


interpretation_items = []


# ------------------------------------------------------------
# Energy interpretation
# ------------------------------------------------------------

if (
    not historical_daily_energy.empty
    and not energy_forecast.empty
):

    historical_avg_energy = _safe_number(
        historical_daily_energy[
            "Energy_kWh"
        ].mean()
    )

    forecast_avg_energy = _safe_number(
        energy_forecast[
            "Energy_kWh"
        ].mean()
    )

    if historical_avg_energy > 0:

        energy_change = (
            (
                forecast_avg_energy
                - historical_avg_energy
            )
            / historical_avg_energy
        ) * 100

        if energy_change > 5:

            interpretation_items.append(
                "Projected daily energy consumption is "
                f"approximately "
                f"{_format_number(abs(energy_change), 1)}% "
                "higher than the historical daily average."
            )

        elif energy_change < -5:

            interpretation_items.append(
                "Projected daily energy consumption is "
                f"approximately "
                f"{_format_number(abs(energy_change), 1)}% "
                "lower than the historical daily average."
            )

        else:

            interpretation_items.append(
                "Projected energy consumption remains broadly "
                "consistent with the historical operating pattern."
            )


# ------------------------------------------------------------
# Cost interpretation
# ------------------------------------------------------------

if (
    not historical_daily_cost.empty
    and not cost_forecast.empty
):

    historical_avg_cost = _safe_number(
        historical_daily_cost[
            "Cost_INR"
        ].mean()
    )

    forecast_avg_cost = _safe_number(
        cost_forecast[
            "Cost_INR"
        ].mean()
    )

    if historical_avg_cost > 0:

        cost_change = (
            (
                forecast_avg_cost
                - historical_avg_cost
            )
            / historical_avg_cost
        ) * 100

        if cost_change > 5:

            interpretation_items.append(
                "Operating cost is projected to increase by "
                f"approximately "
                f"{_format_number(abs(cost_change), 1)}% "
                "relative to the historical daily average."
            )

        elif cost_change < -5:

            interpretation_items.append(
                "Operating cost is projected to decrease by "
                f"approximately "
                f"{_format_number(abs(cost_change), 1)}% "
                "relative to the historical daily average."
            )

        else:

            interpretation_items.append(
                "Projected operating cost remains relatively "
                "stable compared with the historical pattern."
            )


# ------------------------------------------------------------
# Carbon interpretation
# ------------------------------------------------------------

if (
    not historical_daily_carbon.empty
    and not carbon_forecast.empty
):

    historical_avg_carbon = _safe_number(
        historical_daily_carbon[
            "Carbon_kgCO2"
        ].mean()
    )

    forecast_avg_carbon = _safe_number(
        carbon_forecast[
            "Carbon_kgCO2"
        ].mean()
    )

    if historical_avg_carbon > 0:

        carbon_change = (
            (
                forecast_avg_carbon
                - historical_avg_carbon
            )
            / historical_avg_carbon
        ) * 100

        if carbon_change > 5:

            interpretation_items.append(
                "Projected carbon emissions are approximately "
                f"{_format_number(abs(carbon_change), 1)}% "
                "higher than the historical daily average."
            )

        elif carbon_change < -5:

            interpretation_items.append(
                "Projected carbon emissions are approximately "
                f"{_format_number(abs(carbon_change), 1)}% "
                "lower than the historical daily average."
            )

        else:

            interpretation_items.append(
                "Projected carbon emissions remain broadly "
                "aligned with the historical operating pattern."
            )


# ------------------------------------------------------------
# Display interpretations
# ------------------------------------------------------------

if interpretation_items:

    for item in interpretation_items:

        st.html(
            f"""
            <div class="ev-insight-card">
                <strong>Forecast insight</strong><br>
                {item}
            </div>
            """,
        )

else:

    st.info(
        "Not enough historical information is available "
        "to generate forecast interpretations."
    )


# ============================================================
# RECOMMENDATIONS
# ============================================================

st.html(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Recommended Actions
        </div>

        <div class="ev-section-subtitle">
            Operational actions that can improve future
            energy performance.
        </div>
    </div>
    """,
)


recommendations = [
    (
        "Monitor high-consumption periods",
        "Compare future daily consumption against the "
        "forecast baseline and investigate significant deviations.",
    ),
    (
        "Prioritize inefficient equipment",
        "Review high-energy appliances and aging equipment "
        "for maintenance, replacement, or operating-hour optimization.",
    ),
    (
        "Control avoidable operating hours",
        "Reduce unnecessary equipment runtime during "
        "low-occupancy or non-working periods.",
    ),
    (
        "Track cost exposure",
        "Use the projected cost trend to identify periods "
        "where energy-efficiency interventions can provide "
        "financial benefits.",
    ),
    (
        "Improve renewable utilization",
        "Increase renewable-energy utilization where feasible "
        "to reduce dependence on conventional energy sources "
        "and emissions.",
    ),
]


for title, description in recommendations:

    st.html(
        f"""
        <div class="ev-recommendation">
            <strong>{title}</strong><br>
            <span>{description}</span>
        </div>
        """,
    )


# ============================================================
# FORECAST DATA TABLE
# ============================================================

st.html(
    """
    <div class="ev-section">
        <div class="ev-section-title">
            Forecast Data
        </div>

        <div class="ev-section-subtitle">
            Daily projected energy, operating cost,
            and carbon emissions.
        </div>
    </div>
    """,
)


# ------------------------------------------------------------
# IMPORTANT:
# Keep Date as datetime while performing merges.
# Format Date only after all merges are complete.
# ------------------------------------------------------------

forecast_table = energy_forecast.copy()


if not cost_forecast.empty:

    forecast_table = forecast_table.merge(
        cost_forecast,
        on="Date",
        how="left",
    )


if not carbon_forecast.empty:

    forecast_table = forecast_table.merge(
        carbon_forecast,
        on="Date",
        how="left",
    )


if not forecast_table.empty:

    forecast_table["Date"] = pd.to_datetime(
        forecast_table["Date"],
        errors="coerce",
    )

    forecast_table = (
        forecast_table
        .sort_values("Date")
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # Create display copy
    # --------------------------------------------------------

    display_forecast_table = (
        forecast_table.copy()
    )

    display_forecast_table["Date"] = (
        display_forecast_table[
            "Date"
        ]
        .dt.strftime("%d %b %Y")
    )

    if "Energy_kWh" in display_forecast_table.columns:

        display_forecast_table[
            "Energy_kWh"
        ] = (
            display_forecast_table[
                "Energy_kWh"
            ].round(2)
        )

    if "Cost_INR" in display_forecast_table.columns:

        display_forecast_table[
            "Cost_INR"
        ] = (
            display_forecast_table[
                "Cost_INR"
            ].round(2)
        )

    if "Carbon_kgCO2" in display_forecast_table.columns:

        display_forecast_table[
            "Carbon_kgCO2"
        ] = (
            display_forecast_table[
                "Carbon_kgCO2"
            ].round(2)
        )

    # --------------------------------------------------------
    # User-friendly column names
    # --------------------------------------------------------

    display_forecast_table = (
        display_forecast_table.rename(
            columns={
                "Energy_kWh": "Forecast Energy (kWh)",
                "Cost_INR": "Forecast Cost (₹)",
                "Carbon_kgCO2": "Forecast Carbon (kgCO₂)",
            }
        )
    )

    st.dataframe(
        display_forecast_table,
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info(
        "No forecast records are available."
    )


# ============================================================
# DOWNLOAD FORECAST
# ============================================================

if not forecast_table.empty:

    download_table = (
        forecast_table.copy()
    )

    download_table["Date"] = (
        pd.to_datetime(
            download_table["Date"],
            errors="coerce",
        )
        .dt.strftime("%Y-%m-%d")
    )

    csv_data = download_table.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Forecast CSV",
        data=csv_data,
        file_name="EnerVista_Forecast.csv",
        mime="text/csv",
        key="predictive_forecast_download",
    )


# ============================================================
# FORECAST METHODOLOGY
# ============================================================

with st.expander(
    "Forecast methodology"
):

    st.markdown(
        """
        ### Forecasting approach

        EnerVista prepares the filtered historical dataset as
        a daily time series for:

        - Energy consumption
        - Operating cost
        - Carbon emissions

        A linear trend model is applied to the historical daily
        observations and extrapolated into the selected future
        period.

        ### Interpretation

        The forecast is intended as a decision-support estimate.
        Actual results may differ because of:

        - Changes in occupancy
        - Equipment failures
        - Maintenance activities
        - Weather conditions
        - Changes in working hours
        - Operational changes
        - Energy tariff changes

        Longer forecast horizons generally carry greater uncertainty.
        """
    )


# ============================================================
# FOOTER
# ============================================================

st.html(
    """
    <div class="ev-footer">
        EnerVista Predictive Analytics •
        AI-assisted energy intelligence and decision support
    </div>
    """,
)