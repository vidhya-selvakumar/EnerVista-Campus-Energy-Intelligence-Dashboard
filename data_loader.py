from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import streamlit as st


# ============================================================
# EnerVista - Central Data Loader
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "EnerVista_10000_Enhanced_Dataset.xlsx"


REQUIRED_COLUMNS = [
    "Record_ID",
    "Date",
    "Day",
    "Month",
    "Season",
    "Building",
    "Floor",
    "Department",
    "Room_ID",
    "Appliance",
    "Appliance_Count",
    "Appliance_Age",
    "Energy_kWh",
    "Peak_Demand_kW",
    "Voltage",
    "Current",
    "Power_Factor",
    "Cost_INR",
    "Occupancy",
    "Temperature_C",
    "Humidity",
    "Working_Hours",
    "Status",
    "Renewable_kWh",
    "Carbon_kgCO2",
    "Maintenance_Status",
    "Energy_Waste_kWh",
    "Waste_Reason",
    "AI_Anomaly",
    "Recommendation",
]


NUMERIC_COLUMNS = [
    "Appliance_Count",
    "Appliance_Age",
    "Energy_kWh",
    "Peak_Demand_kW",
    "Voltage",
    "Current",
    "Power_Factor",
    "Cost_INR",
    "Occupancy",
    "Temperature_C",
    "Humidity",
    "Working_Hours",
    "Renewable_kWh",
    "Carbon_kgCO2",
    "Energy_Waste_kWh",
]


TEXT_COLUMNS = [
    "Day",
    "Month",
    "Season",
    "Building",
    "Floor",
    "Department",
    "Room_ID",
    "Appliance",
    "Status",
    "Maintenance_Status",
    "Waste_Reason",
    "AI_Anomaly",
    "Recommendation",
]


def _clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names without changing their meaning."""
    result = df.copy()

    result.columns = (
        result.columns.astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )

    return result


def _convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Safely convert known numeric columns."""
    result = df.copy()

    for column in NUMERIC_COLUMNS:
        if column in result.columns:
            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
            )

    return result


def _convert_date_column(df: pd.DataFrame) -> pd.DataFrame:
    """Safely convert Date into pandas datetime."""
    result = df.copy()

    if "Date" in result.columns:
        result["Date"] = pd.to_datetime(
            result["Date"],
            errors="coerce",
        )

    return result


def _clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize text columns while preserving missing values."""
    result = df.copy()

    for column in TEXT_COLUMNS:
        if column in result.columns:
            result[column] = (
                result[column]
                .astype("string")
                .str.strip()
            )

    return result


def _remove_invalid_records(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove records that cannot participate in the main energy analysis.

    A record is retained when it has a valid date and energy value.
    """
    result = df.copy()

    if "Date" in result.columns:
        result = result[result["Date"].notna()]

    if "Energy_kWh" in result.columns:
        result = result[result["Energy_kWh"].notna()]

    return result.reset_index(drop=True)


def _add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Create safe reusable columns used throughout the application."""
    result = df.copy()

    if "Date" in result.columns:
        result["Year"] = result["Date"].dt.year
        result["Date_Only"] = result["Date"].dt.date

    if "Energy_kWh" in result.columns:
        result["Energy_kWh"] = result["Energy_kWh"].clip(lower=0)

    if "Renewable_kWh" in result.columns:
        result["Renewable_kWh"] = result["Renewable_kWh"].clip(lower=0)

    if "Energy_Waste_kWh" in result.columns:
        result["Energy_Waste_kWh"] = result["Energy_Waste_kWh"].clip(lower=0)

    if "Cost_INR" in result.columns:
        result["Cost_INR"] = result["Cost_INR"].clip(lower=0)

    if {
        "Energy_kWh",
        "Energy_Waste_kWh",
    }.issubset(result.columns):
        denominator = result["Energy_kWh"].replace(0, np.nan)

        result["Waste_Percentage"] = (
            result["Energy_Waste_kWh"]
            .div(denominator)
            .mul(100)
            .replace([np.inf, -np.inf], np.nan)
            .fillna(0)
        )

    if {
        "Renewable_kWh",
        "Energy_kWh",
    }.issubset(result.columns):
        denominator = result["Energy_kWh"].replace(0, np.nan)

        result["Renewable_Percentage"] = (
            result["Renewable_kWh"]
            .div(denominator)
            .mul(100)
            .replace([np.inf, -np.inf], np.nan)
            .fillna(0)
            .clip(lower=0, upper=100)
        )

    return result


def validate_dataset(
    df: pd.DataFrame,
    required_columns: Iterable[str] | None = None,
) -> tuple[bool, list[str]]:
    """
    Validate whether the dataset contains required columns.

    Returns
    -------
    tuple
        (is_valid, missing_columns)
    """
    required = list(required_columns or REQUIRED_COLUMNS)

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    return len(missing) == 0, missing


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the complete EnerVista cleaning pipeline.

    This function never mutates the original dataframe.
    """
    if df is None or not isinstance(df, pd.DataFrame):
        return pd.DataFrame()

    if df.empty:
        return pd.DataFrame(columns=df.columns)

    result = df.copy()

    result = _clean_column_names(result)
    result = _convert_date_column(result)
    result = _convert_numeric_columns(result)
    result = _clean_text_columns(result)
    result = _remove_invalid_records(result)
    result = _add_derived_columns(result)

    return result


@st.cache_data(
    show_spinner=False,
    ttl=3600,
)
def load_data(
    file_path: str | Path | None = None,
) -> pd.DataFrame:
    """
    Load and prepare the EnerVista Excel dataset.

    Parameters
    ----------
    file_path:
        Optional custom Excel path.

    Returns
    -------
    pandas.DataFrame
        Cleaned and analysis-ready dataframe.
    """
    path = Path(file_path) if file_path else DEFAULT_DATA_PATH

    if not path.exists():
        raise FileNotFoundError(
            f"EnerVista dataset not found:\n{path}"
        )

    try:
        dataframe = pd.read_excel(
            path,
            engine="openpyxl",
        )
    except Exception as exc:
        raise RuntimeError(
            f"Unable to read Excel dataset:\n{exc}"
        ) from exc

    dataframe = prepare_dataframe(dataframe)

    if dataframe.empty:
        raise ValueError(
            "The EnerVista dataset contains no valid records "
            "after data preparation."
        )

    return dataframe


def get_dataset_info(
    df: pd.DataFrame,
) -> dict[str, object]:
    """Return a compact dataset metadata summary."""
    if df is None or df.empty:
        return {
            "records": 0,
            "columns": 0,
            "date_min": None,
            "date_max": None,
            "buildings": 0,
            "departments": 0,
            "appliances": 0,
        }

    date_min = (
        df["Date"].min()
        if "Date" in df.columns
        else None
    )

    date_max = (
        df["Date"].max()
        if "Date" in df.columns
        else None
    )

    return {
        "records": len(df),
        "columns": len(df.columns),
        "date_min": date_min,
        "date_max": date_max,
        "buildings": (
            df["Building"].nunique()
            if "Building" in df.columns
            else 0
        ),
        "departments": (
            df["Department"].nunique()
            if "Department" in df.columns
            else 0
        ),
        "appliances": (
            df["Appliance"].nunique()
            if "Appliance" in df.columns
            else 0
        ),
    }


def get_missing_columns(
    df: pd.DataFrame,
) -> list[str]:
    """Return required columns missing from a dataframe."""
    _, missing = validate_dataset(df)
    return missing


def get_numeric_columns(
    df: pd.DataFrame,
) -> list[str]:
    """Return numeric columns that actually exist in the dataframe."""
    return [
        column
        for column in NUMERIC_COLUMNS
        if column in df.columns
    ]


def get_categorical_columns(
    df: pd.DataFrame,
) -> list[str]:
    """Return categorical columns that actually exist."""
    return [
        column
        for column in TEXT_COLUMNS
        if column in df.columns
    ]


def clear_data_cache() -> None:
    """Clear the cached dataset."""
    load_data.clear()


__all__ = [
    "DEFAULT_DATA_PATH",
    "REQUIRED_COLUMNS",
    "NUMERIC_COLUMNS",
    "TEXT_COLUMNS",
    "load_data",
    "prepare_dataframe",
    "validate_dataset",
    "get_dataset_info",
    "get_missing_columns",
    "get_numeric_columns",
    "get_categorical_columns",
    "clear_data_cache",
]