"""
EnerVista - Centralized Filtering Engine

Provides reusable Power BI-style sidebar filters for all dashboard pages.

All preset filter functions return:
    filtered_dataframe, filter_state
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Optional, Sequence

import pandas as pd
import streamlit as st


# ============================================================
# FILTER STATE
# ============================================================

@dataclass(frozen=True)
class FilterState:
    """
    Stores the active filter configuration.

    The object is intentionally immutable so that filter state
    remains predictable across dashboard pages.
    """

    start_date: Optional[date] = None
    end_date: Optional[date] = None

    buildings: tuple[str, ...] = ()
    floors: tuple[str, ...] = ()
    departments: tuple[str, ...] = ()
    appliances: tuple[str, ...] = ()
    seasons: tuple[str, ...] = ()
    statuses: tuple[str, ...] = ()
    maintenance_statuses: tuple[str, ...] = ()
    waste_reasons: tuple[str, ...] = ()
    anomalies: tuple[str, ...] = ()

    occupancy_min: Optional[float] = None
    occupancy_max: Optional[float] = None

    power_factor_min: Optional[float] = None
    power_factor_max: Optional[float] = None

    @property
    def active_count(self) -> int:
        """Return the number of actively selected filter groups."""

        count = 0

        if self.start_date is not None:
            count += 1

        if self.end_date is not None:
            count += 1

        filter_groups = (
            self.buildings,
            self.floors,
            self.departments,
            self.appliances,
            self.seasons,
            self.statuses,
            self.maintenance_statuses,
            self.waste_reasons,
            self.anomalies,
        )

        count += sum(1 for group in filter_groups if group)

        if self.occupancy_min is not None:
            count += 1

        if self.occupancy_max is not None:
            count += 1

        if self.power_factor_min is not None:
            count += 1

        if self.power_factor_max is not None:
            count += 1

        return count

    def to_dict(self) -> dict:
        """Convert filter state into a serializable dictionary."""

        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "buildings": list(self.buildings),
            "floors": list(self.floors),
            "departments": list(self.departments),
            "appliances": list(self.appliances),
            "seasons": list(self.seasons),
            "statuses": list(self.statuses),
            "maintenance_statuses": list(self.maintenance_statuses),
            "waste_reasons": list(self.waste_reasons),
            "anomalies": list(self.anomalies),
            "occupancy_min": self.occupancy_min,
            "occupancy_max": self.occupancy_max,
            "power_factor_min": self.power_factor_min,
            "power_factor_max": self.power_factor_max,
        }


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _column_exists(df: pd.DataFrame, column: str) -> bool:
    """Safely check whether a column exists."""

    return column in df.columns


def _available_options(
    df: pd.DataFrame,
    column: str,
) -> list[str]:
    """Return sorted non-empty unique values from a column."""

    if not _column_exists(df, column):
        return []

    values = (
        df[column]
        .dropna()
        .astype(str)
        .str.strip()
    )

    values = values[values != ""]

    return sorted(values.unique().tolist())


def _multiselect(
    label: str,
    options: Sequence[str],
    key: str,
    help_text: Optional[str] = None,
) -> tuple[str, ...]:
    """
    Render a reusable Streamlit multiselect.

    Empty selection means 'All'.
    """

    if not options:
        return ()

    selected = st.sidebar.multiselect(
        label,
        options=list(options),
        default=[],
        key=key,
        help=help_text,
        placeholder="All",
    )

    return tuple(str(value) for value in selected)


def _date_bounds(df: pd.DataFrame) -> tuple[Optional[date], Optional[date]]:
    """Return minimum and maximum available dates."""

    if "Date" not in df.columns:
        return None, None

    dates = pd.to_datetime(
        df["Date"],
        errors="coerce",
    ).dropna()

    if dates.empty:
        return None, None

    return dates.min().date(), dates.max().date()


def _render_date_filter(
    df: pd.DataFrame,
    key_prefix: str,
) -> tuple[Optional[date], Optional[date]]:
    """Render the dashboard date-range filter."""

    min_date, max_date = _date_bounds(df)

    if min_date is None or max_date is None:
        return None, None

    selected_range = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key=f"{key_prefix}_date_range",
        help="Select the date range to analyze.",
    )

    if isinstance(selected_range, tuple):
        if len(selected_range) == 2:
            return selected_range[0], selected_range[1]

        if len(selected_range) == 1:
            return selected_range[0], selected_range[0]

    if isinstance(selected_range, list):
        if len(selected_range) >= 2:
            return selected_range[0], selected_range[1]

        if len(selected_range) == 1:
            return selected_range[0], selected_range[0]

    if isinstance(selected_range, date):
        return selected_range, selected_range

    return min_date, max_date


def _apply_date_filter(
    df: pd.DataFrame,
    start_date: Optional[date],
    end_date: Optional[date],
) -> pd.DataFrame:
    """Apply date filtering safely."""

    if "Date" not in df.columns:
        return df

    if start_date is None and end_date is None:
        return df

    result = df.copy()

    dates = pd.to_datetime(
        result["Date"],
        errors="coerce",
    )

    if start_date is not None:
        result = result[dates.dt.date >= start_date]

        dates = pd.to_datetime(
            result["Date"],
            errors="coerce",
        )

    if end_date is not None:
        result = result[dates.dt.date <= end_date]

    return result


def _apply_multiselect(
    df: pd.DataFrame,
    column: str,
    selected: Iterable[str],
) -> pd.DataFrame:
    """
    Apply a categorical multi-select filter.

    Empty selection means 'All'.
    """

    selected = tuple(selected)

    if not selected:
        return df

    if column not in df.columns:
        return df

    values = df[column].astype(str).str.strip()

    return df[values.isin(selected)].copy()


def _apply_numeric_range(
    df: pd.DataFrame,
    column: str,
    minimum: Optional[float],
    maximum: Optional[float],
) -> pd.DataFrame:
    """Apply a numeric range filter safely."""

    if column not in df.columns:
        return df

    if minimum is None and maximum is None:
        return df

    result = df.copy()

    values = pd.to_numeric(
        result[column],
        errors="coerce",
    )

    if minimum is not None:
        result = result[values >= minimum]

        values = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    if maximum is not None:
        result = result[values <= maximum]

    return result


def _render_numeric_range(
    df: pd.DataFrame,
    column: str,
    label: str,
    key_prefix: str,
    step: float = 1.0,
    format_string: Optional[str] = None,
) -> tuple[Optional[float], Optional[float]]:
    """
    Render a numeric range slider.

    Returns None, None when the column is unavailable.
    """

    if column not in df.columns:
        return None, None

    values = pd.to_numeric(
        df[column],
        errors="coerce",
    ).dropna()

    if values.empty:
        return None, None

    minimum = float(values.min())
    maximum = float(values.max())

    if minimum == maximum:
        return minimum, maximum

    slider_kwargs = {
        "label": label,
        "min_value": minimum,
        "max_value": maximum,
        "value": (minimum, maximum),
        "step": step,
        "key": f"{key_prefix}_{column}",
    }

    if format_string is not None:
        slider_kwargs["format"] = format_string

    selected = st.sidebar.slider(**slider_kwargs)

    return float(selected[0]), float(selected[1])


# ============================================================
# MAIN FILTER ENGINE
# ============================================================

def apply_filters(
    df: pd.DataFrame,
    *,
    key_prefix: str = "global",
    show_date: bool = True,
    show_building: bool = True,
    show_floor: bool = True,
    show_department: bool = True,
    show_appliance: bool = True,
    show_season: bool = True,
    show_status: bool = True,
    show_maintenance: bool = True,
    show_waste_reason: bool = False,
    show_anomaly: bool = False,
    show_occupancy: bool = False,
    show_power_factor: bool = False,
) -> tuple[pd.DataFrame, FilterState]:
    """
    Central reusable filtering engine.

    Returns:
        filtered_df, filter_state
    """

    if df is None:
        empty = pd.DataFrame()
        return empty, FilterState()

    if df.empty:
        return df.copy(), FilterState()

    filtered_df = df.copy()

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    if show_date:
        start_date, end_date = _render_date_filter(
            filtered_df,
            key_prefix,
        )
    else:
        start_date, end_date = None, None

    filtered_df = _apply_date_filter(
        filtered_df,
        start_date,
        end_date,
    )

    # --------------------------------------------------------
    # CATEGORICAL FILTERS
    # --------------------------------------------------------

    buildings = ()
    floors = ()
    departments = ()
    appliances = ()
    seasons = ()
    statuses = ()
    maintenance_statuses = ()
    waste_reasons = ()
    anomalies = ()

    if show_building:
        buildings = _multiselect(
            "Building",
            _available_options(filtered_df, "Building"),
            f"{key_prefix}_building",
        )

        filtered_df = _apply_multiselect(
            filtered_df,
            "Building",
            buildings,
        )

    if show_floor:
        floors = _multiselect(
            "Floor",
            _available_options(filtered_df, "Floor"),
            f"{key_prefix}_floor",
        )

        filtered_df = _apply_multiselect(
            filtered_df,
            "Floor",
            floors,
        )

    if show_department:
        departments = _multiselect(
            "Department",
            _available_options(filtered_df, "Department"),
            f"{key_prefix}_department",
        )

        filtered_df = _apply_multiselect(
            filtered_df,
            "Department",
            departments,
        )

    if show_appliance:
        appliances = _multiselect(
            "Appliance",
            _available_options(filtered_df, "Appliance"),
            f"{key_prefix}_appliance",
        )

        filtered_df = _apply_multiselect(
            filtered_df,
            "Appliance",
            appliances,
        )

    if show_season:
        seasons = _multiselect(
            "Season",
            _available_options(filtered_df, "Season"),
            f"{key_prefix}_season",
        )

        filtered_df = _apply_multiselect(
            filtered_df,
            "Season",
            seasons,
        )

    if show_status:
        statuses = _multiselect(
            "Status",
            _available_options(filtered_df, "Status"),
            f"{key_prefix}_status",
        )

        filtered_df = _apply_multiselect(
            filtered_df,
            "Status",
            statuses,
        )

    if show_maintenance:
        maintenance_statuses = _multiselect(
            "Maintenance status",
            _available_options(
                filtered_df,
                "Maintenance_Status",
            ),
            f"{key_prefix}_maintenance",
        )

        filtered_df = _apply_multiselect(
            filtered_df,
            "Maintenance_Status",
            maintenance_statuses,
        )

    if show_waste_reason:
        waste_reasons = _multiselect(
            "Waste reason",
            _available_options(
                filtered_df,
                "Waste_Reason",
            ),
            f"{key_prefix}_waste_reason",
        )

        filtered_df = _apply_multiselect(
            filtered_df,
            "Waste_Reason",
            waste_reasons,
        )

    if show_anomaly:
        anomaly_options = _available_options(
            filtered_df,
            "AI_Anomaly",
        )

        anomalies = _multiselect(
            "AI anomaly",
            anomaly_options,
            f"{key_prefix}_anomaly",
        )

        filtered_df = _apply_multiselect(
            filtered_df,
            "AI_Anomaly",
            anomalies,
        )

    # --------------------------------------------------------
    # NUMERIC FILTERS
    # --------------------------------------------------------

    occupancy_min = None
    occupancy_max = None

    if show_occupancy:
        occupancy_min, occupancy_max = _render_numeric_range(
            filtered_df,
            "Occupancy",
            "Occupancy",
            key_prefix,
            step=1.0,
            format_string="%.0f",
        )

        filtered_df = _apply_numeric_range(
            filtered_df,
            "Occupancy",
            occupancy_min,
            occupancy_max,
        )

    power_factor_min = None
    power_factor_max = None

    if show_power_factor:
        power_factor_min, power_factor_max = _render_numeric_range(
            filtered_df,
            "Power_Factor",
            "Power factor",
            key_prefix,
            step=0.01,
            format_string="%.2f",
        )

        filtered_df = _apply_numeric_range(
            filtered_df,
            "Power_Factor",
            power_factor_min,
            power_factor_max,
        )

    # --------------------------------------------------------
    # FILTER STATE
    # --------------------------------------------------------

    state = FilterState(
        start_date=start_date,
        end_date=end_date,
        buildings=buildings,
        floors=floors,
        departments=departments,
        appliances=appliances,
        seasons=seasons,
        statuses=statuses,
        maintenance_statuses=maintenance_statuses,
        waste_reasons=waste_reasons,
        anomalies=anomalies,
        occupancy_min=occupancy_min,
        occupancy_max=occupancy_max,
        power_factor_min=power_factor_min,
        power_factor_max=power_factor_max,
    )

    return filtered_df.reset_index(drop=True), state


# ============================================================
# PRESET FILTERS
# ============================================================

def global_filters(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, FilterState]:
    """
    Global filter configuration.

    Used by the Home / overall dashboard.
    """

    return apply_filters(
        df,
        key_prefix="global",
        show_date=True,
        show_building=True,
        show_floor=True,
        show_department=True,
        show_appliance=True,
        show_season=True,
        show_status=True,
        show_maintenance=True,
        show_waste_reason=False,
        show_anomaly=False,
        show_occupancy=False,
        show_power_factor=False,
    )


def executive_filters(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, FilterState]:
    """
    Executive Dashboard filter configuration.

    This wrapper intentionally uses the global filter engine.
    It fixes compatibility with 1_Executive_Dashboard.py.
    """

    return global_filters(df)


def energy_analysis_filters(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, FilterState]:
    """
    Energy Analysis filter configuration.
    """

    return apply_filters(
        df,
        key_prefix="energy_analysis",
        show_date=True,
        show_building=True,
        show_floor=True,
        show_department=True,
        show_appliance=True,
        show_season=True,
        show_status=True,
        show_maintenance=False,
        show_waste_reason=False,
        show_anomaly=False,
        show_occupancy=True,
        show_power_factor=True,
    )


def waste_analysis_filters(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, FilterState]:
    """
    Waste Analysis filter configuration.
    """

    return apply_filters(
        df,
        key_prefix="waste_analysis",
        show_date=True,
        show_building=True,
        show_floor=True,
        show_department=True,
        show_appliance=True,
        show_season=True,
        show_status=True,
        show_maintenance=True,
        show_waste_reason=True,
        show_anomaly=False,
        show_occupancy=False,
        show_power_factor=False,
    )


def sustainability_filters(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, FilterState]:
    """
    Sustainability filter configuration.
    """

    return apply_filters(
        df,
        key_prefix="sustainability",
        show_date=True,
        show_building=True,
        show_floor=True,
        show_department=True,
        show_appliance=False,
        show_season=True,
        show_status=True,
        show_maintenance=False,
        show_waste_reason=False,
        show_anomaly=False,
        show_occupancy=False,
        show_power_factor=False,
    )


def ai_insights_filters(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, FilterState]:
    """
    AI Insights filter configuration.
    """

    return apply_filters(
        df,
        key_prefix="ai_insights",
        show_date=True,
        show_building=True,
        show_floor=True,
        show_department=True,
        show_appliance=True,
        show_season=True,
        show_status=True,
        show_maintenance=True,
        show_waste_reason=True,
        show_anomaly=True,
        show_occupancy=True,
        show_power_factor=True,
    )


def predictive_filters(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, FilterState]:
    """
    Predictive Analytics filter configuration.

    Uses filters that are useful for constructing
    historical forecasting series.
    """

    return apply_filters(
        df,
        key_prefix="predictive",
        show_date=True,
        show_building=True,
        show_floor=True,
        show_department=True,
        show_appliance=True,
        show_season=True,
        show_status=True,
        show_maintenance=False,
        show_waste_reason=False,
        show_anomaly=False,
        show_occupancy=False,
        show_power_factor=False,
    )


# ============================================================
# FILTER SUMMARY
# ============================================================

def filter_summary_text(
    state: Optional[FilterState],
) -> str:
    """
    Generate a human-readable summary of active filters.
    """

    if state is None:
        return "No filters applied."

    if state.active_count == 0:
        return "All available data is selected."

    parts: list[str] = []

    # Date
    if state.start_date and state.end_date:
        parts.append(
            f"Date: {state.start_date.strftime('%d %b %Y')} – "
            f"{state.end_date.strftime('%d %b %Y')}"
        )
    elif state.start_date:
        parts.append(
            f"From: {state.start_date.strftime('%d %b %Y')}"
        )
    elif state.end_date:
        parts.append(
            f"Until: {state.end_date.strftime('%d %b %Y')}"
        )

    # Categorical
    categorical = [
        ("Building", state.buildings),
        ("Floor", state.floors),
        ("Department", state.departments),
        ("Appliance", state.appliances),
        ("Season", state.seasons),
        ("Status", state.statuses),
        ("Maintenance", state.maintenance_statuses),
        ("Waste reason", state.waste_reasons),
        ("AI anomaly", state.anomalies),
    ]

    for label, values in categorical:
        if values:
            if len(values) <= 3:
                value_text = ", ".join(values)
            else:
                value_text = (
                    f"{', '.join(values[:3])} "
                    f"+{len(values) - 3} more"
                )

            parts.append(f"{label}: {value_text}")

    # Numeric
    if (
        state.occupancy_min is not None
        and state.occupancy_max is not None
    ):
        parts.append(
            f"Occupancy: "
            f"{state.occupancy_min:.0f}–"
            f"{state.occupancy_max:.0f}"
        )

    if (
        state.power_factor_min is not None
        and state.power_factor_max is not None
    ):
        parts.append(
            f"Power factor: "
            f"{state.power_factor_min:.2f}–"
            f"{state.power_factor_max:.2f}"
        )

    if not parts:
        return "All available data is selected."

    return " | ".join(parts)


def show_filter_status(
    state: Optional[FilterState],
) -> None:
    """
    Display a compact filter status card below the sidebar filters.
    """

    if state is None:
        return

    if state.active_count == 0:
        st.markdown(
            """
            <div class="ev-filter-summary">
                <span class="ev-filter-summary-label">Filters</span>
                <span>All available data</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    summary = filter_summary_text(state)

    st.markdown(
        f"""
        <div class="ev-filter-summary">
            <span class="ev-filter-summary-label">
                Active filters ({state.active_count})
            </span>
            <span>{summary}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def clear_filter_state(
    key_prefix: str,
) -> None:
    """
    Remove known filter widget values from Streamlit session state.

    This can be used by a page if a Reset Filters button is added.
    """

    suffixes = [
        "date_range",
        "building",
        "floor",
        "department",
        "appliance",
        "season",
        "status",
        "maintenance",
        "waste_reason",
        "anomaly",
        "Occupancy",
        "Power_Factor",
    ]

    for suffix in suffixes:
        key = f"{key_prefix}_{suffix}"

        if key in st.session_state:
            del st.session_state[key]


def filter_dataframe(
    df: pd.DataFrame,
    state: FilterState,
) -> pd.DataFrame:
    """
    Reapply an existing FilterState to a dataframe.

    Useful when the same saved filter state needs to be applied
    outside the interactive sidebar rendering process.
    """

    if df is None or df.empty:
        return pd.DataFrame() if df is None else df.copy()

    result = df.copy()

    result = _apply_date_filter(
        result,
        state.start_date,
        state.end_date,
    )

    result = _apply_multiselect(
        result,
        "Building",
        state.buildings,
    )

    result = _apply_multiselect(
        result,
        "Floor",
        state.floors,
    )

    result = _apply_multiselect(
        result,
        "Department",
        state.departments,
    )

    result = _apply_multiselect(
        result,
        "Appliance",
        state.appliances,
    )

    result = _apply_multiselect(
        result,
        "Season",
        state.seasons,
    )

    result = _apply_multiselect(
        result,
        "Status",
        state.statuses,
    )

    result = _apply_multiselect(
        result,
        "Maintenance_Status",
        state.maintenance_statuses,
    )

    result = _apply_multiselect(
        result,
        "Waste_Reason",
        state.waste_reasons,
    )

    result = _apply_multiselect(
        result,
        "AI_Anomaly",
        state.anomalies,
    )

    result = _apply_numeric_range(
        result,
        "Occupancy",
        state.occupancy_min,
        state.occupancy_max,
    )

    result = _apply_numeric_range(
        result,
        "Power_Factor",
        state.power_factor_min,
        state.power_factor_max,
    )

    return result.reset_index(drop=True)


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "FilterState",
    "apply_filters",
    "global_filters",
    "executive_filters",
    "energy_analysis_filters",
    "waste_analysis_filters",
    "sustainability_filters",
    "ai_insights_filters",
    "predictive_filters",
    "filter_summary_text",
    "show_filter_status",
    "filter_dataframe",
    "clear_filter_state",
]