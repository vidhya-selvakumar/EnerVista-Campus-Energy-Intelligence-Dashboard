from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


# ============================================================
# EnerVista - Central Analytics & Calculation Engine
# ============================================================

EPSILON = 1e-9


# ============================================================
# Internal Helpers
# ============================================================

def _empty_series(df: pd.DataFrame) -> pd.Series:
    """Return an empty numeric series aligned to the dataframe."""
    return pd.Series(
        0.0,
        index=df.index,
        dtype="float64",
    )


def _numeric(
    df: pd.DataFrame,
    column: str,
    default: float = 0.0,
) -> pd.Series:
    """Safely return a numeric dataframe column."""
    if column not in df.columns:
        return pd.Series(
            default,
            index=df.index,
            dtype="float64",
        )

    return (
        pd.to_numeric(
            df[column],
            errors="coerce",
        )
        .replace([np.inf, -np.inf], np.nan)
        .fillna(default)
    )


def _sum(
    df: pd.DataFrame,
    column: str,
) -> float:
    """Safely calculate a column total."""
    if df is None or df.empty or column not in df.columns:
        return 0.0

    return float(
        _numeric(df, column).sum()
    )


def _mean(
    df: pd.DataFrame,
    column: str,
) -> float:
    """Safely calculate a column average."""
    if df is None or df.empty or column not in df.columns:
        return 0.0

    values = _numeric(df, column)

    if values.empty:
        return 0.0

    return float(values.mean())


def _max(
    df: pd.DataFrame,
    column: str,
) -> float:
    """Safely calculate a column maximum."""
    if df is None or df.empty or column not in df.columns:
        return 0.0

    values = _numeric(df, column)

    if values.empty:
        return 0.0

    return float(values.max())


def _min(
    df: pd.DataFrame,
    column: str,
) -> float:
    """Safely calculate a column minimum."""
    if df is None or df.empty or column not in df.columns:
        return 0.0

    values = _numeric(df, column)

    if values.empty:
        return 0.0

    return float(values.min())


def _safe_percentage(
    numerator: float,
    denominator: float,
) -> float:
    """Safely calculate a percentage."""
    if abs(denominator) <= EPSILON:
        return 0.0

    return float(
        (numerator / denominator) * 100
    )


def _safe_ratio(
    numerator: float,
    denominator: float,
) -> float:
    """Safely calculate a ratio."""
    if abs(denominator) <= EPSILON:
        return 0.0

    return float(
        numerator / denominator
    )


def _group_sum(
    df: pd.DataFrame,
    group_column: str,
    value_column: str,
) -> pd.DataFrame:
    """Safely aggregate a numeric metric by a category."""
    if (
        df is None
        or df.empty
        or group_column not in df.columns
        or value_column not in df.columns
    ):
        return pd.DataFrame(
            columns=[
                group_column,
                value_column,
            ]
        )

    result = (
        df.assign(
            _metric=_numeric(df, value_column)
        )
        .groupby(
            group_column,
            dropna=False,
            as_index=False,
        )["_metric"]
        .sum()
        .rename(
            columns={
                "_metric": value_column,
            }
        )
    )

    return result


def _group_mean(
    df: pd.DataFrame,
    group_column: str,
    value_column: str,
) -> pd.DataFrame:
    """Safely calculate a grouped average."""
    if (
        df is None
        or df.empty
        or group_column not in df.columns
        or value_column not in df.columns
    ):
        return pd.DataFrame(
            columns=[
                group_column,
                value_column,
            ]
        )

    result = (
        df.assign(
            _metric=_numeric(df, value_column)
        )
        .groupby(
            group_column,
            dropna=False,
            as_index=False,
        )["_metric"]
        .mean()
        .rename(
            columns={
                "_metric": value_column,
            }
        )
    )

    return result


# ============================================================
# Core Energy Metrics
# ============================================================

def total_energy(df: pd.DataFrame) -> float:
    """Total energy consumption in kWh."""
    return _sum(df, "Energy_kWh")


def average_energy(df: pd.DataFrame) -> float:
    """Average record-level energy consumption."""
    return _mean(df, "Energy_kWh")


def peak_energy(df: pd.DataFrame) -> float:
    """Maximum record-level energy consumption."""
    return _max(df, "Energy_kWh")


def minimum_energy(df: pd.DataFrame) -> float:
    """Minimum record-level energy consumption."""
    return _min(df, "Energy_kWh")


def total_cost(df: pd.DataFrame) -> float:
    """Total electricity cost in INR."""
    return _sum(df, "Cost_INR")


def average_cost(df: pd.DataFrame) -> float:
    """Average electricity cost per record."""
    return _mean(df, "Cost_INR")


def total_peak_demand(df: pd.DataFrame) -> float:
    """Total recorded peak demand in kW."""
    return _sum(df, "Peak_Demand_kW")


def maximum_peak_demand(df: pd.DataFrame) -> float:
    """Maximum recorded peak demand."""
    return _max(df, "Peak_Demand_kW")


def average_peak_demand(df: pd.DataFrame) -> float:
    """Average peak demand."""
    return _mean(df, "Peak_Demand_kW")


# ============================================================
# Renewable Energy
# ============================================================

def total_renewable_energy(df: pd.DataFrame) -> float:
    """Total renewable energy generated/used in kWh."""
    return _sum(df, "Renewable_kWh")


def renewable_percentage(df: pd.DataFrame) -> float:
    """Renewable energy contribution as a percentage."""
    return _safe_percentage(
        total_renewable_energy(df),
        total_energy(df),
    )


def non_renewable_energy(df: pd.DataFrame) -> float:
    """Energy remaining after renewable contribution."""
    return max(
        total_energy(df) - total_renewable_energy(df),
        0.0,
    )


# ============================================================
# Carbon Metrics
# ============================================================

def total_carbon(df: pd.DataFrame) -> float:
    """Total carbon emissions in kgCO2."""
    return _sum(df, "Carbon_kgCO2")


def average_carbon(df: pd.DataFrame) -> float:
    """Average carbon emissions per record."""
    return _mean(df, "Carbon_kgCO2")


def carbon_intensity(df: pd.DataFrame) -> float:
    """
    Carbon intensity in kgCO2 per kWh.
    """
    return _safe_ratio(
        total_carbon(df),
        total_energy(df),
    )


def carbon_reduction_from_renewables(df: pd.DataFrame) -> float:
    """
    Approximate renewable contribution toward avoiding
    grid-based energy emissions.

    Uses the observed ratio:
        Carbon / Energy
    """
    intensity = carbon_intensity(df)

    return float(
        total_renewable_energy(df) * intensity
    )


# ============================================================
# Waste Metrics
# ============================================================

def total_energy_waste(df: pd.DataFrame) -> float:
    """Total wasted energy in kWh."""
    return _sum(df, "Energy_Waste_kWh")


def average_energy_waste(df: pd.DataFrame) -> float:
    """Average wasted energy per record."""
    return _mean(df, "Energy_Waste_kWh")


def waste_percentage(df: pd.DataFrame) -> float:
    """Waste as a percentage of total energy consumption."""
    return _safe_percentage(
        total_energy_waste(df),
        total_energy(df),
    )


def useful_energy(df: pd.DataFrame) -> float:
    """Estimated useful energy after waste."""
    return max(
        total_energy(df) - total_energy_waste(df),
        0.0,
    )


def estimated_waste_cost(
    df: pd.DataFrame,
) -> float:
    """
    Estimate monetary impact of wasted energy.

    If Energy and Cost are available, the effective
    cost per kWh is derived from the dataset.
    """
    energy = total_energy(df)
    cost = total_cost(df)
    waste = total_energy_waste(df)

    rate = _safe_ratio(cost, energy)

    return float(
        waste * rate
    )


# ============================================================
# Occupancy & Environment
# ============================================================

def average_occupancy(df: pd.DataFrame) -> float:
    """Average occupancy."""
    return _mean(df, "Occupancy")


def maximum_occupancy(df: pd.DataFrame) -> float:
    """Maximum occupancy."""
    return _max(df, "Occupancy")


def average_temperature(df: pd.DataFrame) -> float:
    """Average temperature in Celsius."""
    return _mean(df, "Temperature_C")


def average_humidity(df: pd.DataFrame) -> float:
    """Average humidity."""
    return _mean(df, "Humidity")


def average_working_hours(df: pd.DataFrame) -> float:
    """Average working hours."""
    return _mean(df, "Working_Hours")


# ============================================================
# Electrical Metrics
# ============================================================

def average_voltage(df: pd.DataFrame) -> float:
    """Average voltage."""
    return _mean(df, "Voltage")


def average_current(df: pd.DataFrame) -> float:
    """Average current."""
    return _mean(df, "Current")


def average_power_factor(df: pd.DataFrame) -> float:
    """Average power factor."""
    return _mean(df, "Power_Factor")


def low_power_factor_percentage(
    df: pd.DataFrame,
    threshold: float = 0.90,
) -> float:
    """Percentage of records below a power-factor threshold."""
    if df is None or df.empty or "Power_Factor" not in df.columns:
        return 0.0

    values = _numeric(df, "Power_Factor")

    return _safe_percentage(
        float((values < threshold).sum()),
        float(len(values)),
    )


# ============================================================
# Record / Entity Metrics
# ============================================================

def record_count(df: pd.DataFrame) -> int:
    """Number of records."""
    if df is None:
        return 0

    return int(len(df))


def unique_buildings(df: pd.DataFrame) -> int:
    """Number of unique buildings."""
    if df is None or df.empty or "Building" not in df.columns:
        return 0

    return int(
        df["Building"].dropna().nunique()
    )


def unique_departments(df: pd.DataFrame) -> int:
    """Number of unique departments."""
    if df is None or df.empty or "Department" not in df.columns:
        return 0

    return int(
        df["Department"].dropna().nunique()
    )


def unique_appliances(df: pd.DataFrame) -> int:
    """Number of unique appliance categories."""
    if df is None or df.empty or "Appliance" not in df.columns:
        return 0

    return int(
        df["Appliance"].dropna().nunique()
    )


def unique_rooms(df: pd.DataFrame) -> int:
    """Number of unique rooms."""
    if df is None or df.empty or "Room_ID" not in df.columns:
        return 0

    return int(
        df["Room_ID"].dropna().nunique()
    )


# ============================================================
# Date Metrics
# ============================================================

def date_range(
    df: pd.DataFrame,
) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """Return minimum and maximum available dates."""
    if (
        df is None
        or df.empty
        or "Date" not in df.columns
    ):
        return None, None

    dates = pd.to_datetime(
        df["Date"],
        errors="coerce",
    ).dropna()

    if dates.empty:
        return None, None

    return dates.min(), dates.max()


def date_range_days(df: pd.DataFrame) -> int:
    """Return number of calendar days between first and last date."""
    start, end = date_range(df)

    if start is None or end is None:
        return 0

    return int(
        (end.normalize() - start.normalize()).days + 1
    )


# ============================================================
# Daily Aggregations
# ============================================================

def daily_energy_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Daily energy, cost, waste, renewable and carbon summary."""
    if (
        df is None
        or df.empty
        or "Date" not in df.columns
    ):
        return pd.DataFrame(
            columns=[
                "Date",
                "Energy_kWh",
                "Cost_INR",
                "Energy_Waste_kWh",
                "Renewable_kWh",
                "Carbon_kgCO2",
                "Occupancy",
            ]
        )

    data = df.copy()

    data["Date"] = pd.to_datetime(
        data["Date"],
        errors="coerce",
    )

    data = data.dropna(
        subset=["Date"]
    )

    if data.empty:
        return pd.DataFrame()

    aggregations: dict[str, str] = {}

    for column in [
        "Energy_kWh",
        "Cost_INR",
        "Energy_Waste_kWh",
        "Renewable_kWh",
        "Carbon_kgCO2",
    ]:
        if column in data.columns:
            aggregations[column] = "sum"

    if "Occupancy" in data.columns:
        aggregations["Occupancy"] = "mean"

    result = (
        data.groupby(
            data["Date"].dt.normalize(),
            as_index=False,
        )
        .agg(aggregations)
        .rename(
            columns={
                "Date": "Date",
            }
        )
    )

    result["Date"] = pd.to_datetime(
        result["Date"]
    )

    return result.sort_values(
        "Date"
    ).reset_index(drop=True)


def daily_metric_summary(
    df: pd.DataFrame,
    metric: str,
    aggregation: str = "sum",
) -> pd.DataFrame:
    """Generic daily metric aggregation."""
    if (
        df is None
        or df.empty
        or "Date" not in df.columns
        or metric not in df.columns
    ):
        return pd.DataFrame(
            columns=[
                "Date",
                metric,
            ]
        )

    data = df.copy()

    data["Date"] = pd.to_datetime(
        data["Date"],
        errors="coerce",
    )

    data = data.dropna(
        subset=["Date"]
    )

    data[metric] = pd.to_numeric(
        data[metric],
        errors="coerce",
    ).fillna(0)

    if aggregation not in {
        "sum",
        "mean",
        "max",
        "min",
        "median",
    }:
        aggregation = "sum"

    result = (
        data.groupby(
            data["Date"].dt.normalize()
        )[metric]
        .agg(aggregation)
        .reset_index()
    )

    return result.sort_values(
        "Date"
    ).reset_index(drop=True)


# ============================================================
# Monthly Aggregations
# ============================================================

def monthly_energy_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Monthly energy performance summary."""
    if (
        df is None
        or df.empty
        or "Date" not in df.columns
    ):
        return pd.DataFrame()

    data = df.copy()

    data["Date"] = pd.to_datetime(
        data["Date"],
        errors="coerce",
    )

    data = data.dropna(
        subset=["Date"]
    )

    if data.empty:
        return pd.DataFrame()

    aggregations: dict[str, str] = {}

    for column in [
        "Energy_kWh",
        "Cost_INR",
        "Energy_Waste_kWh",
        "Renewable_kWh",
        "Carbon_kgCO2",
        "Peak_Demand_kW",
    ]:
        if column in data.columns:
            aggregations[column] = "sum"

    if "Occupancy" in data.columns:
        aggregations["Occupancy"] = "mean"

    result = (
        data.assign(
            Period=data["Date"].dt.to_period("M").dt.to_timestamp()
        )
        .groupby(
            "Period",
            as_index=False,
        )
        .agg(aggregations)
        .sort_values("Period")
    )

    return result.reset_index(drop=True)


# ============================================================
# Building / Department / Floor Analysis
# ============================================================

def building_energy_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Energy summary by building."""
    return _group_sum(
        df,
        "Building",
        "Energy_kWh",
    ).sort_values(
        "Energy_kWh",
        ascending=False,
    ).reset_index(drop=True)


def department_energy_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Energy summary by department."""
    return _group_sum(
        df,
        "Department",
        "Energy_kWh",
    ).sort_values(
        "Energy_kWh",
        ascending=False,
    ).reset_index(drop=True)


def floor_energy_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Energy summary by floor."""
    return _group_sum(
        df,
        "Floor",
        "Energy_kWh",
    ).sort_values(
        "Energy_kWh",
        ascending=False,
    ).reset_index(drop=True)


def appliance_energy_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Energy summary by appliance."""
    return _group_sum(
        df,
        "Appliance",
        "Energy_kWh",
    ).sort_values(
        "Energy_kWh",
        ascending=False,
    ).reset_index(drop=True)


# ============================================================
# Waste Analysis
# ============================================================

def waste_reason_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Energy waste grouped by waste reason."""
    return _group_sum(
        df,
        "Waste_Reason",
        "Energy_Waste_kWh",
    ).sort_values(
        "Energy_Waste_kWh",
        ascending=False,
    ).reset_index(drop=True)


def building_waste_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Energy waste grouped by building."""
    return _group_sum(
        df,
        "Building",
        "Energy_Waste_kWh",
    ).sort_values(
        "Energy_Waste_kWh",
        ascending=False,
    ).reset_index(drop=True)


def department_waste_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Energy waste grouped by department."""
    return _group_sum(
        df,
        "Department",
        "Energy_Waste_kWh",
    ).sort_values(
        "Energy_Waste_kWh",
        ascending=False,
    ).reset_index(drop=True)


# ============================================================
# Sustainability Analysis
# ============================================================

def building_sustainability_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Building-level sustainability metrics."""
    if (
        df is None
        or df.empty
        or "Building" not in df.columns
    ):
        return pd.DataFrame()

    aggregations: dict[str, str] = {}

    for column in [
        "Energy_kWh",
        "Renewable_kWh",
        "Carbon_kgCO2",
        "Energy_Waste_kWh",
        "Cost_INR",
    ]:
        if column in df.columns:
            aggregations[column] = "sum"

    if not aggregations:
        return pd.DataFrame()

    result = (
        df.groupby(
            "Building",
            as_index=False,
        )
        .agg(aggregations)
    )

    if {
        "Renewable_kWh",
        "Energy_kWh",
    }.issubset(result.columns):
        result["Renewable_Percentage"] = (
            result["Renewable_kWh"]
            .div(
                result["Energy_kWh"].replace(0, np.nan)
            )
            .mul(100)
            .fillna(0)
        )

    if {
        "Energy_Waste_kWh",
        "Energy_kWh",
    }.issubset(result.columns):
        result["Waste_Percentage"] = (
            result["Energy_Waste_kWh"]
            .div(
                result["Energy_kWh"].replace(0, np.nan)
            )
            .mul(100)
            .fillna(0)
        )

    return result.sort_values(
        "Energy_kWh",
        ascending=False,
    ).reset_index(drop=True)


# ============================================================
# AI / Anomaly Analysis
# ============================================================

def normalize_anomaly_series(
    series: pd.Series,
) -> pd.Series:
    """Normalize common AI anomaly labels into a consistent form."""
    if series is None:
        return pd.Series(dtype="string")

    text = (
        series
        .astype("string")
        .str.strip()
        .str.lower()
    )

    mapping = {
        "yes": "Anomaly",
        "true": "Anomaly",
        "1": "Anomaly",
        "anomaly": "Anomaly",
        "abnormal": "Anomaly",
        "high": "Anomaly",
        "no": "Normal",
        "false": "Normal",
        "0": "Normal",
        "normal": "Normal",
        "low": "Normal",
    }

    normalized = text.map(mapping)

    normalized = normalized.fillna(
        series.astype("string").str.strip()
    )

    return normalized


def anomaly_count(
    df: pd.DataFrame,
) -> int:
    """Count anomaly records."""
    if (
        df is None
        or df.empty
        or "AI_Anomaly" not in df.columns
    ):
        return 0

    normalized = normalize_anomaly_series(
        df["AI_Anomaly"]
    )

    return int(
        (normalized == "Anomaly").sum()
    )


def anomaly_percentage(
    df: pd.DataFrame,
) -> float:
    """Percentage of records classified as anomalies."""
    if df is None or df.empty:
        return 0.0

    return _safe_percentage(
        anomaly_count(df),
        len(df),
    )


def anomaly_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Return normalized anomaly distribution."""
    if (
        df is None
        or df.empty
        or "AI_Anomaly" not in df.columns
    ):
        return pd.DataFrame(
            columns=[
                "AI_Anomaly",
                "Count",
            ]
        )

    normalized = normalize_anomaly_series(
        df["AI_Anomaly"]
    )

    result = (
        normalized
        .value_counts(dropna=False)
        .rename_axis("AI_Anomaly")
        .reset_index(name="Count")
    )

    return result


def anomaly_by_building(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Anomaly counts by building."""
    if (
        df is None
        or df.empty
        or "Building" not in df.columns
        or "AI_Anomaly" not in df.columns
    ):
        return pd.DataFrame(
            columns=[
                "Building",
                "Anomaly_Count",
            ]
        )

    data = df.copy()

    data["_Anomaly_Normalized"] = normalize_anomaly_series(
        data["AI_Anomaly"]
    )

    result = (
        data.assign(
            _is_anomaly=(
                data["_Anomaly_Normalized"]
                == "Anomaly"
            ).astype(int)
        )
        .groupby(
            "Building",
            as_index=False,
        )["_is_anomaly"]
        .sum()
        .rename(
            columns={
                "_is_anomaly": "Anomaly_Count",
            }
        )
        .sort_values(
            "Anomaly_Count",
            ascending=False,
        )
    )

    return result.reset_index(drop=True)


# ============================================================
# Maintenance / Status Analysis
# ============================================================

def maintenance_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Maintenance status distribution."""
    if (
        df is None
        or df.empty
        or "Maintenance_Status" not in df.columns
    ):
        return pd.DataFrame(
            columns=[
                "Maintenance_Status",
                "Count",
            ]
        )

    return (
        df["Maintenance_Status"]
        .astype("string")
        .str.strip()
        .value_counts(dropna=False)
        .rename_axis("Maintenance_Status")
        .reset_index(name="Count")
    )


def status_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Equipment status distribution."""
    if (
        df is None
        or df.empty
        or "Status" not in df.columns
    ):
        return pd.DataFrame(
            columns=[
                "Status",
                "Count",
            ]
        )

    return (
        df["Status"]
        .astype("string")
        .str.strip()
        .value_counts(dropna=False)
        .rename_axis("Status")
        .reset_index(name="Count")
    )


# ============================================================
# Ranking Helpers
# ============================================================

def top_energy_consumers(
    df: pd.DataFrame,
    n: int = 10,
) -> pd.DataFrame:
    """Return top energy-consuming entities."""
    n = max(int(n), 1)

    result = appliance_energy_summary(df)

    return result.head(n).reset_index(drop=True)


def top_waste_buildings(
    df: pd.DataFrame,
    n: int = 10,
) -> pd.DataFrame:
    """Return buildings with the highest energy waste."""
    n = max(int(n), 1)

    result = building_waste_summary(df)

    return result.head(n).reset_index(drop=True)


# ============================================================
# KPI Bundles
# ============================================================

def executive_kpis(
    df: pd.DataFrame,
) -> dict[str, float | int]:
    """KPIs for the executive dashboard."""
    return {
        "total_energy": total_energy(df),
        "total_cost": total_cost(df),
        "total_waste": total_energy_waste(df),
        "renewable_energy": total_renewable_energy(df),
        "renewable_percentage": renewable_percentage(df),
        "total_carbon": total_carbon(df),
        "anomaly_count": anomaly_count(df),
        "record_count": record_count(df),
    }


def energy_kpis(
    df: pd.DataFrame,
) -> dict[str, float | int]:
    """KPIs for energy analysis."""
    return {
        "total_energy": total_energy(df),
        "average_energy": average_energy(df),
        "peak_energy": peak_energy(df),
        "total_cost": total_cost(df),
        "average_cost": average_cost(df),
        "peak_demand": maximum_peak_demand(df),
        "average_peak_demand": average_peak_demand(df),
        "average_power_factor": average_power_factor(df),
    }


def waste_kpis(
    df: pd.DataFrame,
) -> dict[str, float | int]:
    """KPIs for waste analysis."""
    return {
        "total_waste": total_energy_waste(df),
        "waste_percentage": waste_percentage(df),
        "useful_energy": useful_energy(df),
        "waste_cost": estimated_waste_cost(df),
        "anomaly_count": anomaly_count(df),
        "anomaly_percentage": anomaly_percentage(df),
    }


def sustainability_kpis(
    df: pd.DataFrame,
) -> dict[str, float | int]:
    """KPIs for sustainability analysis."""
    return {
        "total_energy": total_energy(df),
        "renewable_energy": total_renewable_energy(df),
        "renewable_percentage": renewable_percentage(df),
        "non_renewable_energy": non_renewable_energy(df),
        "total_carbon": total_carbon(df),
        "carbon_intensity": carbon_intensity(df),
        "carbon_reduction": carbon_reduction_from_renewables(df),
    }


def ai_kpis(
    df: pd.DataFrame,
) -> dict[str, float | int]:
    """KPIs for AI insights."""
    return {
        "records": record_count(df),
        "anomalies": anomaly_count(df),
        "anomaly_percentage": anomaly_percentage(df),
        "total_waste": total_energy_waste(df),
        "waste_percentage": waste_percentage(df),
        "buildings": unique_buildings(df),
    }


def forecast_kpis(
    df: pd.DataFrame,
) -> dict[str, float | int]:
    """KPIs used by predictive analytics."""
    start, end = date_range(df)

    return {
        "records": record_count(df),
        "total_energy": total_energy(df),
        "average_energy": average_energy(df),
        "start_date": start,
        "end_date": end,
        "history_days": date_range_days(df),
    }


# ============================================================
# Forecast Preparation
# ============================================================

def forecast_ready_data(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepare daily energy data for time-series forecasting.

    Missing calendar dates are retained and energy is filled
    with zero so that lag features remain chronologically valid.
    """
    if (
        df is None
        or df.empty
        or "Date" not in df.columns
        or "Energy_kWh" not in df.columns
    ):
        return pd.DataFrame(
            columns=[
                "Date",
                "Energy_kWh",
            ]
        )

    data = df.copy()

    data["Date"] = pd.to_datetime(
        data["Date"],
        errors="coerce",
    )

    data["Energy_kWh"] = pd.to_numeric(
        data["Energy_kWh"],
        errors="coerce",
    ).fillna(0)

    data = data.dropna(
        subset=["Date"]
    )

    if data.empty:
        return pd.DataFrame(
            columns=[
                "Date",
                "Energy_kWh",
            ]
        )

    daily = (
        data.groupby(
            data["Date"].dt.normalize()
        )["Energy_kWh"]
        .sum()
        .reset_index()
    )

    daily["Date"] = pd.to_datetime(
        daily["Date"]
    )

    full_dates = pd.date_range(
        daily["Date"].min(),
        daily["Date"].max(),
        freq="D",
    )

    daily = (
        daily.set_index("Date")
        .reindex(full_dates)
        .rename_axis("Date")
        .reset_index()
    )

    daily["Energy_kWh"] = (
        pd.to_numeric(
            daily["Energy_kWh"],
            errors="coerce",
        )
        .fillna(0)
        .clip(lower=0)
    )

    return daily.sort_values(
        "Date"
    ).reset_index(drop=True)


# ============================================================
# Generic Summary
# ============================================================

def overview_summary(
    df: pd.DataFrame,
) -> dict[str, Any]:
    """Complete high-level dataset summary."""
    start, end = date_range(df)

    return {
        "records": record_count(df),
        "buildings": unique_buildings(df),
        "departments": unique_departments(df),
        "appliances": unique_appliances(df),
        "rooms": unique_rooms(df),
        "date_start": start,
        "date_end": end,
        "date_range_days": date_range_days(df),
        "total_energy_kwh": total_energy(df),
        "total_cost_inr": total_cost(df),
        "total_waste_kwh": total_energy_waste(df),
        "renewable_kwh": total_renewable_energy(df),
        "carbon_kgco2": total_carbon(df),
        "average_occupancy": average_occupancy(df),
        "average_power_factor": average_power_factor(df),
    }


# ============================================================
# Backward-Compatible Aliases
# ============================================================

get_total_energy = total_energy
get_average_energy = average_energy
get_total_cost = total_cost
get_total_waste = total_energy_waste
get_total_renewable = total_renewable_energy
get_total_carbon = total_carbon
get_waste_percentage = waste_percentage
get_renewable_percentage = renewable_percentage
get_anomaly_count = anomaly_count


__all__ = [
    "total_energy",
    "average_energy",
    "peak_energy",
    "minimum_energy",
    "total_cost",
    "average_cost",
    "total_peak_demand",
    "maximum_peak_demand",
    "average_peak_demand",
    "total_renewable_energy",
    "renewable_percentage",
    "non_renewable_energy",
    "total_carbon",
    "average_carbon",
    "carbon_intensity",
    "carbon_reduction_from_renewables",
    "total_energy_waste",
    "average_energy_waste",
    "waste_percentage",
    "useful_energy",
    "estimated_waste_cost",
    "average_occupancy",
    "maximum_occupancy",
    "average_temperature",
    "average_humidity",
    "average_working_hours",
    "average_voltage",
    "average_current",
    "average_power_factor",
    "low_power_factor_percentage",
    "record_count",
    "unique_buildings",
    "unique_departments",
    "unique_appliances",
    "unique_rooms",
    "date_range",
    "date_range_days",
    "daily_energy_summary",
    "daily_metric_summary",
    "monthly_energy_summary",
    "building_energy_summary",
    "department_energy_summary",
    "floor_energy_summary",
    "appliance_energy_summary",
    "waste_reason_summary",
    "building_waste_summary",
    "department_waste_summary",
    "building_sustainability_summary",
    "normalize_anomaly_series",
    "anomaly_count",
    "anomaly_percentage",
    "anomaly_summary",
    "anomaly_by_building",
    "maintenance_summary",
    "status_summary",
    "top_energy_consumers",
    "top_waste_buildings",
    "executive_kpis",
    "energy_kpis",
    "waste_kpis",
    "sustainability_kpis",
    "ai_kpis",
    "forecast_kpis",
    "forecast_ready_data",
    "overview_summary",
    "get_total_energy",
    "get_average_energy",
    "get_total_cost",
    "get_total_waste",
    "get_total_renewable",
    "get_total_carbon",
    "get_waste_percentage",
    "get_renewable_percentage",
    "get_anomaly_count",
]