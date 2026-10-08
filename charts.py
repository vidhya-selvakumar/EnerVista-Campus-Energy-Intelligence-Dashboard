from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# EnerVista - Professional Visualization Engine
# ============================================================

FONT_FAMILY = "Inter, Segoe UI, Arial, sans-serif"

PLOT_BG = "rgba(0,0,0,0)"
PAPER_BG = "rgba(0,0,0,0)"

GRID_COLOR = "rgba(120, 130, 150, 0.16)"
TEXT_COLOR = "#334155"
MUTED_COLOR = "#64748B"

CHART_HEIGHT = 390


# ============================================================
# Generic Helpers
# ============================================================

def _empty_figure(
    message: str = "No data available for this visualization.",
    height: int = CHART_HEIGHT,
) -> go.Figure:
    """Return a professional empty-state Plotly figure."""

    fig = go.Figure()

    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={
            "family": FONT_FAMILY,
            "size": 15,
            "color": MUTED_COLOR,
        },
    )

    fig.update_layout(
        height=height,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),
        xaxis=dict(
            visible=False
        ),
        yaxis=dict(
            visible=False
        ),
    )

    return fig


def _base_layout(
    fig: go.Figure,
    *,
    title: str | None = None,
    height: int = CHART_HEIGHT,
) -> go.Figure:
    """Apply the common EnerVista chart design."""

    fig.update_layout(
        height=height,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(
            family=FONT_FAMILY,
            color=TEXT_COLOR,
            size=12,
        ),
        margin=dict(
            l=55,
            r=35,
            t=60 if title else 25,
            b=50,
        ),
        hoverlabel=dict(
            font=dict(
                family=FONT_FAMILY,
                size=12,
            )
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0,
            bgcolor="rgba(0,0,0,0)",
        ),
    )

    if title:
        fig.update_layout(
            title=dict(
                text=title,
                x=0,
                xanchor="left",
                font=dict(
                    family=FONT_FAMILY,
                    size=17,
                    color=TEXT_COLOR,
                ),
            )
        )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor=GRID_COLOR,
        tickfont=dict(
            color=MUTED_COLOR,
            size=11,
        ),
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor=GRID_COLOR,
        zeroline=False,
        tickfont=dict(
            color=MUTED_COLOR,
            size=11,
        ),
    )

    return fig


def _prepare(
    df: pd.DataFrame,
    required: Iterable[str],
) -> pd.DataFrame:
    """Return a safe dataframe containing required columns."""

    if df is None or df.empty:
        return pd.DataFrame()

    required = list(required)

    if any(
        column not in df.columns
        for column in required
    ):
        return pd.DataFrame()

    result = df.copy()

    return result


def _numeric(
    df: pd.DataFrame,
    column: str,
) -> pd.Series:
    """Safely convert a dataframe column to numeric."""
    return (
        pd.to_numeric(
            df[column],
            errors="coerce",
        )
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
        .fillna(0)
    )


def _date(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Safely normalize Date."""
    result = df.copy()

    result["Date"] = pd.to_datetime(
        result["Date"],
        errors="coerce",
    )

    return result.dropna(
        subset=["Date"]
    )


def _format_axis(
    fig: go.Figure,
    y_title: str | None = None,
) -> go.Figure:
    """Apply consistent axis formatting."""

    if y_title:
        fig.update_yaxes(
            title_text=y_title
        )

    fig.update_xaxes(
        title_text=None
    )

    return fig


# ============================================================
# Daily Energy
# ============================================================

def daily_energy_chart(
    df: pd.DataFrame,
) -> go.Figure:
    """Daily energy consumption trend."""

    data = _prepare(
        df,
        ["Date", "Energy_kWh"],
    )

    if data.empty:
        return _empty_figure()

    data = _date(data)

    if data.empty:
        return _empty_figure()

    daily = (
        data.assign(
            Energy_kWh=_numeric(
                data,
                "Energy_kWh",
            )
        )
        .groupby(
            data["Date"].dt.normalize(),
            as_index=False,
        )["Energy_kWh"]
        .sum()
    )

    fig = px.line(
        daily,
        x="Date",
        y="Energy_kWh",
        markers=True,
    )

    fig.update_traces(
        line=dict(
            width=2.5
        ),
        marker=dict(
            size=5
        ),
        hovertemplate=(
            "<b>%{x|%d %b %Y}</b>"
            "<br>Energy: %{y:,.2f} kWh"
            "<extra></extra>"
        ),
    )

    _base_layout(
        fig,
        title="Daily Energy Consumption",
    )

    return _format_axis(
        fig,
        "Energy (kWh)",
    )


# ============================================================
# Energy vs Waste
# ============================================================

def energy_waste_trend_chart(
    df: pd.DataFrame,
) -> go.Figure:
    """Daily energy consumption versus energy waste."""

    data = _prepare(
        df,
        [
            "Date",
            "Energy_kWh",
            "Energy_Waste_kWh",
        ],
    )

    if data.empty:
        return _empty_figure()

    data = _date(data)

    if data.empty:
        return _empty_figure()

    data["Energy_kWh"] = _numeric(
        data,
        "Energy_kWh",
    )

    data["Energy_Waste_kWh"] = _numeric(
        data,
        "Energy_Waste_kWh",
    )

    daily = (
        data.groupby(
            data["Date"].dt.normalize(),
            as_index=False,
        )[
            [
                "Energy_kWh",
                "Energy_Waste_kWh",
            ]
        ]
        .sum()
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=daily["Date"],
            y=daily["Energy_kWh"],
            mode="lines",
            name="Energy",
            line=dict(
                width=2.5
            ),
            hovertemplate=(
                "<b>%{x|%d %b %Y}</b>"
                "<br>Energy: %{y:,.2f} kWh"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=daily["Date"],
            y=daily["Energy_Waste_kWh"],
            mode="lines",
            name="Waste",
            line=dict(
                width=2.5,
                dash="dot",
            ),
            hovertemplate=(
                "<b>%{x|%d %b %Y}</b>"
                "<br>Waste: %{y:,.2f} kWh"
                "<extra></extra>"
            ),
        )
    )

    _base_layout(
        fig,
        title="Daily Energy Consumption vs Waste",
    )

    return _format_axis(
        fig,
        "Energy (kWh)",
    )


# ============================================================
# Renewable Energy
# ============================================================

def renewable_energy_chart(
    df: pd.DataFrame,
) -> go.Figure:
    """Daily renewable energy contribution."""

    data = _prepare(
        df,
        ["Date", "Renewable_kWh"],
    )

    if data.empty:
        return _empty_figure()

    data = _date(data)

    if data.empty:
        return _empty_figure()

    data["Renewable_kWh"] = _numeric(
        data,
        "Renewable_kWh",
    )

    daily = (
        data.groupby(
            data["Date"].dt.normalize(),
            as_index=False,
        )["Renewable_kWh"]
        .sum()
    )

    fig = px.area(
        daily,
        x="Date",
        y="Renewable_kWh",
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{x|%d %b %Y}</b>"
            "<br>Renewable: %{y:,.2f} kWh"
            "<extra></extra>"
        )
    )

    _base_layout(
        fig,
        title="Daily Renewable Energy",
    )

    return _format_axis(
        fig,
        "Renewable Energy (kWh)",
    )


# ============================================================
# Carbon
# ============================================================

def carbon_emission_chart(
    df: pd.DataFrame,
) -> go.Figure:
    """Daily carbon emissions."""

    data = _prepare(
        df,
        ["Date", "Carbon_kgCO2"],
    )

    if data.empty:
        return _empty_figure()

    data = _date(data)

    if data.empty:
        return _empty_figure()

    data["Carbon_kgCO2"] = _numeric(
        data,
        "Carbon_kgCO2",
    )

    daily = (
        data.groupby(
            data["Date"].dt.normalize(),
            as_index=False,
        )["Carbon_kgCO2"]
        .sum()
    )

    fig = px.line(
        daily,
        x="Date",
        y="Carbon_kgCO2",
        markers=True,
    )

    fig.update_traces(
        line=dict(
            width=2.5
        ),
        hovertemplate=(
            "<b>%{x|%d %b %Y}</b>"
            "<br>Carbon: %{y:,.2f} kgCO₂"
            "<extra></extra>"
        ),
    )

    _base_layout(
        fig,
        title="Daily Carbon Emissions",
    )

    return _format_axis(
        fig,
        "Carbon (kgCO₂)",
    )


# ============================================================
# Carbon vs Renewable
# ============================================================

def carbon_vs_renewable_chart(
    df: pd.DataFrame,
) -> go.Figure:
    """Compare daily carbon emissions and renewable energy."""

    data = _prepare(
        df,
        [
            "Date",
            "Carbon_kgCO2",
            "Renewable_kWh",
        ],
    )

    if data.empty:
        return _empty_figure()

    data = _date(data)

    if data.empty:
        return _empty_figure()

    data["Carbon_kgCO2"] = _numeric(
        data,
        "Carbon_kgCO2",
    )

    data["Renewable_kWh"] = _numeric(
        data,
        "Renewable_kWh",
    )

    daily = (
        data.groupby(
            data["Date"].dt.normalize(),
            as_index=False,
        )[
            [
                "Carbon_kgCO2",
                "Renewable_kWh",
            ]
        ]
        .sum()
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=daily["Date"],
            y=daily["Carbon_kgCO2"],
            name="Carbon",
            mode="lines",
            line=dict(
                width=2.5
            ),
            hovertemplate=(
                "<b>%{x|%d %b %Y}</b>"
                "<br>Carbon: %{y:,.2f} kgCO₂"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=daily["Date"],
            y=daily["Renewable_kWh"],
            name="Renewable",
            mode="lines",
            yaxis="y2",
            line=dict(
                width=2.5,
                dash="dot",
            ),
            hovertemplate=(
                "<b>%{x|%d %b %Y}</b>"
                "<br>Renewable: %{y:,.2f} kWh"
                "<extra></extra>"
            ),
        )
    )

    _base_layout(
        fig,
        title="Carbon Emissions vs Renewable Energy",
    )

    fig.update_layout(
        yaxis=dict(
            title="Carbon (kgCO₂)",
            showgrid=True,
            gridcolor=GRID_COLOR,
        ),
        yaxis2=dict(
            title="Renewable Energy (kWh)",
            overlaying="y",
            side="right",
            showgrid=False,
        ),
    )

    return fig


# Backward-compatible alias
carbon_renewable_chart = carbon_vs_renewable_chart


# ============================================================
# Building Analysis
# ============================================================

def building_energy_chart(
    df: pd.DataFrame,
) -> go.Figure:
    """Energy consumption by building."""

    data = _prepare(
        df,
        ["Building", "Energy_kWh"],
    )

    if data.empty:
        return _empty_figure()

    data["Energy_kWh"] = _numeric(
        data,
        "Energy_kWh",
    )

    summary = (
        data.groupby(
            "Building",
            as_index=False,
        )["Energy_kWh"]
        .sum()
        .sort_values(
            "Energy_kWh",
            ascending=True,
        )
    )

    fig = px.bar(
        summary,
        x="Energy_kWh",
        y="Building",
        orientation="h",
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b>"
            "<br>Energy: %{x:,.2f} kWh"
            "<extra></extra>"
        )
    )

    _base_layout(
        fig,
        title="Energy Consumption by Building",
    )

    fig.update_yaxes(
        categoryorder="array",
        categoryarray=summary["Building"].tolist(),
    )

    return _format_axis(
        fig,
        "Energy (kWh)",
    )


# ============================================================
# Top Energy Consumers
# ============================================================

def top_energy_consumers_chart(
    df: pd.DataFrame,
    n: int = 10,
) -> go.Figure:
    """Top appliances by energy consumption."""

    data = _prepare(
        df,
        ["Appliance", "Energy_kWh"],
    )

    if data.empty:
        return _empty_figure()

    data["Energy_kWh"] = _numeric(
        data,
        "Energy_kWh",
    )

    summary = (
        data.groupby(
            "Appliance",
            as_index=False,
        )["Energy_kWh"]
        .sum()
        .nlargest(
            max(int(n), 1),
            "Energy_kWh",
        )
        .sort_values(
            "Energy_kWh",
            ascending=True,
        )
    )

    fig = px.bar(
        summary,
        x="Energy_kWh",
        y="Appliance",
        orientation="h",
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b>"
            "<br>Energy: %{x:,.2f} kWh"
            "<extra></extra>"
        )
    )

    _base_layout(
        fig,
        title=f"Top {max(int(n), 1)} Energy Consumers",
    )

    return _format_axis(
        fig,
        "Energy (kWh)",
    )


# ============================================================
# Department
# ============================================================

def department_energy_chart(
    df: pd.DataFrame,
) -> go.Figure:
    """Energy consumption by department."""

    data = _prepare(
        df,
        ["Department", "Energy_kWh"],
    )

    if data.empty:
        return _empty_figure()

    data["Energy_kWh"] = _numeric(
        data,
        "Energy_kWh",
    )

    summary = (
        data.groupby(
            "Department",
            as_index=False,
        )["Energy_kWh"]
        .sum()
        .sort_values(
            "Energy_kWh",
            ascending=False,
        )
    )

    fig = px.bar(
        summary,
        x="Department",
        y="Energy_kWh",
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{x}</b>"
            "<br>Energy: %{y:,.2f} kWh"
            "<extra></extra>"
        )
    )

    _base_layout(
        fig,
        title="Energy Consumption by Department",
    )

    return _format_axis(
        fig,
        "Energy (kWh)",
    )


# ============================================================
# Floor
# ============================================================

def floor_energy_chart(
    df: pd.DataFrame,
) -> go.Figure:
    """Energy consumption by floor."""

    data = _prepare(
        df,
        ["Floor", "Energy_kWh"],
    )

    if data.empty:
        return _empty_figure()

    data["Energy_kWh"] = _numeric(
        data,
        "Energy_kWh",
    )

    summary = (
        data.groupby(
            "Floor",
            as_index=False,
        )["Energy_kWh"]
        .sum()
    )

    summary["Floor"] = summary["Floor"].astype(str)

    summary = summary.sort_values(
        "Energy_kWh",
        ascending=False,
    )

    fig = px.bar(
        summary,
        x="Floor",
        y="Energy_kWh",
    )

    fig.update_traces(
        hovertemplate=(
            "<b>Floor %{x}</b>"
            "<br>Energy: %{y:,.2f} kWh"
            "<extra></extra>"
        )
    )

    _base_layout(
        fig,
        title="Energy Consumption by Floor",
    )

    return _format_axis(
        fig,
        "Energy (kWh)",
    )


# ============================================================
# Appliance
# ============================================================

def appliance_energy_chart(
    df: pd.DataFrame,
) -> go.Figure:
    """Energy consumption by appliance category."""

    return top_energy_consumers_chart(
        df,
        n=15,
    )


# ============================================================
# Waste Reason
# ============================================================

def waste_reason_chart(
    df: pd.DataFrame,
) -> go.Figure:
    """Energy waste by reason."""

    data = _prepare(
        df,
        ["Waste_Reason", "Energy_Waste_kWh"],
    )

    if data.empty:
        return _empty_figure()

    data["Energy_Waste_kWh"] = _numeric(
        data,
        "Energy_Waste_kWh",
    )

    summary = (
        data.groupby(
            "Waste_Reason",
            as_index=False,
        )["Energy_Waste_kWh"]
        .sum()
        .sort_values(
            "Energy_Waste_kWh",
            ascending=False,
        )
    )

    fig = px.bar(
        summary,
        x="Waste_Reason",
        y="Energy_Waste_kWh",
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{x}</b>"
            "<br>Waste: %{y:,.2f} kWh"
            "<extra></extra>"
        )
    )

    _base_layout(
        fig,
        title="Energy Waste by Reason",
    )

    return _format_axis(
        fig,
        "Waste (kWh)",
    )


# ============================================================
# Building Waste
# ============================================================

def building_waste_chart(
    df: pd.DataFrame,
) -> go.Figure:
    """Energy waste by building."""

    data = _prepare(
        df,
        ["Building", "Energy_Waste_kWh"],
    )

    if data.empty:
        return _empty_figure()

    data["Energy_Waste_kWh"] = _numeric(
        data,
        "Energy_Waste_kWh",
    )

    summary = (
        data.groupby(
            "Building",
            as_index=False,
        )["Energy_Waste_kWh"]
        .sum()
        .sort_values(
            "Energy_Waste_kWh",
            ascending=True,
        )
    )

    fig = px.bar(
        summary,
        x="Energy_Waste_kWh",
        y="Building",
        orientation="h",
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b>"
            "<br>Waste: %{x:,.2f} kWh"
            "<extra></extra>"
        )
    )

    _base_layout(
        fig,
        title="Energy Waste by Building",
    )

    return _format_axis(
        fig,
        "Waste (kWh)",
    )


# ============================================================
# AI Anomaly
# ============================================================

def _normalize_anomaly(
    series: pd.Series,
) -> pd.Series:
    """Normalize common anomaly labels."""

    if series is None:
        return pd.Series(
            dtype="string"
        )

    raw = (
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

    result = raw.map(mapping)

    return result.fillna(
        series.astype("string").str.strip()
    )


def ai_anomaly_chart(
    df: pd.DataFrame,
) -> go.Figure:
    """AI anomaly distribution."""

    data = _prepare(
        df,
        ["AI_Anomaly"],
    )

    if data.empty:
        return _empty_figure()

    data = data.copy()

    data["AI_Anomaly"] = _normalize_anomaly(
        data["AI_Anomaly"]
    )

    summary = (
        data["AI_Anomaly"]
        .value_counts()
        .rename_axis("AI_Anomaly")
        .reset_index(name="Count")
    )

    fig = px.pie(
        summary,
        names="AI_Anomaly",
        values="Count",
        hole=0.58,
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate=(
            "<b>%{label}</b>"
            "<br>Records: %{value:,}"
            "<extra></extra>"
        ),
    )

    _base_layout(
        fig,
        title="AI Anomaly Distribution",
    )

    return fig


# ============================================================
# Anomaly by Building
# ============================================================

def anomaly_by_building_chart(
    df: pd.DataFrame,
) -> go.Figure:
    """AI anomaly count by building."""

    data = _prepare(
        df,
        [
            "Building",
            "AI_Anomaly",
        ],
    )

    if data.empty:
        return _empty_figure()

    data = data.copy()

    data["AI_Anomaly"] = _normalize_anomaly(
        data["AI_Anomaly"]
    )

    data["Is_Anomaly"] = (
        data["AI_Anomaly"]
        .eq("Anomaly")
        .astype(int)
    )

    summary = (
        data.groupby(
            "Building",
            as_index=False,
        )["Is_Anomaly"]
        .sum()
        .rename(
            columns={
                "Is_Anomaly": "Anomaly_Count"
            }
        )
        .sort_values(
            "Anomaly_Count",
            ascending=True,
        )
    )

    fig = px.bar(
        summary,
        x="Anomaly_Count",
        y="Building",
        orientation="h",
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b>"
            "<br>Anomalies: %{x:,}"
            "<extra></extra>"
        )
    )

    _base_layout(
        fig,
        title="AI Anomalies by Building",
    )

    return _format_axis(
        fig,
        "Anomaly Count",
    )


# ============================================================
# Occupancy vs Energy
# ============================================================

def occupancy_energy_chart(
    df: pd.DataFrame,
) -> go.Figure:
    """Relationship between occupancy and energy consumption."""

    data = _prepare(
        df,
        [
            "Occupancy",
            "Energy_kWh",
        ],
    )

    if data.empty:
        return _empty_figure()

    data = data.copy()

    data["Occupancy"] = _numeric(
        data,
        "Occupancy",
    )

    data["Energy_kWh"] = _numeric(
        data,
        "Energy_kWh",
    )

    fig = px.scatter(
        data,
        x="Occupancy",
        y="Energy_kWh",
        opacity=0.62,
    )

    fig.update_traces(
        marker=dict(
            size=7
        ),
        hovertemplate=(
            "Occupancy: %{x:,.1f}"
            "<br>Energy: %{y:,.2f} kWh"
            "<extra></extra>"
        ),
    )

    # Add trend line only when enough valid observations exist.
    if len(data) >= 3:
        x = data["Occupancy"].to_numpy(
            dtype=float
        )
        y = data["Energy_kWh"].to_numpy(
            dtype=float
        )

        valid = (
            np.isfinite(x)
            & np.isfinite(y)
        )

        x = x[valid]
        y = y[valid]

        if len(x) >= 3 and np.ptp(x) > 0:
            slope, intercept = np.polyfit(
                x,
                y,
                1,
            )

            x_line = np.linspace(
                float(x.min()),
                float(x.max()),
                100,
            )

            y_line = (
                slope * x_line
                + intercept
            )

            fig.add_trace(
                go.Scatter(
                    x=x_line,
                    y=y_line,
                    mode="lines",
                    name="Trend",
                    line=dict(
                        width=2,
                        dash="dash",
                    ),
                    hoverinfo="skip",
                )
            )

    _base_layout(
        fig,
        title="Occupancy vs Energy Consumption",
    )

    fig.update_xaxes(
        title_text="Occupancy"
    )

    fig.update_yaxes(
        title_text="Energy (kWh)"
    )

    return fig


# ============================================================
# Power Factor
# ============================================================

def power_factor_chart(
    df: pd.DataFrame,
) -> go.Figure:
    """Power factor distribution."""

    data = _prepare(
        df,
        ["Power_Factor"],
    )

    if data.empty:
        return _empty_figure()

    values = _numeric(
        data,
        "Power_Factor",
    )

    fig = px.histogram(
        x=values,
        nbins=25,
    )

    fig.update_traces(
        hovertemplate=(
            "Power factor: %{x:.2f}"
            "<br>Records: %{y:,}"
            "<extra></extra>"
        )
    )

    _base_layout(
        fig,
        title="Power Factor Distribution",
    )

    fig.update_xaxes(
        title_text="Power Factor"
    )

    fig.update_yaxes(
        title_text="Record Count"
    )

    return fig


# ============================================================
# Sustainability Gauges
# ============================================================

def sustainability_gauge(
    value: float,
    title: str = "Sustainability Score",
    maximum: float = 100,
) -> go.Figure:
    """Generic sustainability gauge."""

    value = float(
        np.clip(
            value,
            0,
            maximum,
        )
    )

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={
                "text": title
            },
            gauge={
                "axis": {
                    "range": [
                        0,
                        maximum,
                    ]
                },
                "bar": {},
                "steps": [
                    {
                        "range": [
                            0,
                            maximum * 0.40,
                        ],
                    },
                    {
                        "range": [
                            maximum * 0.40,
                            maximum * 0.70,
                        ],
                    },
                    {
                        "range": [
                            maximum * 0.70,
                            maximum,
                        ],
                    },
                ],
            },
        )
    )

    fig.update_layout(
        height=CHART_HEIGHT,
        paper_bgcolor=PAPER_BG,
        font=dict(
            family=FONT_FAMILY,
            color=TEXT_COLOR,
        ),
        margin=dict(
            l=20,
            r=20,
            t=50,
            b=20,
        ),
    )

    return fig


def renewable_gauge(
    percentage: float,
) -> go.Figure:
    """Renewable energy contribution gauge."""

    return sustainability_gauge(
        percentage,
        title="Renewable Energy Share",
        maximum=100,
    )


# ============================================================
# Forecast Charts
# ============================================================

def energy_forecast_chart(
    history: pd.DataFrame,
    forecast: pd.DataFrame,
) -> go.Figure:
    """Historical and forecast energy chart."""

    if (
        history is None
        or history.empty
        or forecast is None
        or forecast.empty
    ):
        return _empty_figure(
            "Forecast data is not available."
        )

    required_history = {
        "Date",
        "Energy_kWh",
    }

    required_forecast = {
        "Date",
        "Energy_kWh",
    }

    if not required_history.issubset(
        history.columns
    ):
        return _empty_figure()

    if not required_forecast.issubset(
        forecast.columns
    ):
        return _empty_figure()

    hist = history.copy()
    pred = forecast.copy()

    hist["Date"] = pd.to_datetime(
        hist["Date"],
        errors="coerce",
    )

    pred["Date"] = pd.to_datetime(
        pred["Date"],
        errors="coerce",
    )

    hist["Energy_kWh"] = _numeric(
        hist,
        "Energy_kWh",
    )

    pred["Energy_kWh"] = _numeric(
        pred,
        "Energy_kWh",
    )

    hist = hist.dropna(
        subset=["Date"]
    )

    pred = pred.dropna(
        subset=["Date"]
    )

    if hist.empty or pred.empty:
        return _empty_figure()

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=hist["Date"],
            y=hist["Energy_kWh"],
            mode="lines",
            name="Historical",
            line=dict(
                width=2.5
            ),
            hovertemplate=(
                "<b>%{x|%d %b %Y}</b>"
                "<br>Actual: %{y:,.2f} kWh"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=pred["Date"],
            y=pred["Energy_kWh"],
            mode="lines+markers",
            name="Forecast",
            line=dict(
                width=2.5,
                dash="dash",
            ),
            hovertemplate=(
                "<b>%{x|%d %b %Y}</b>"
                "<br>Forecast: %{y:,.2f} kWh"
                "<extra></extra>"
            ),
        )
    )

    _base_layout(
        fig,
        title="Energy Consumption Forecast",
    )

    return _format_axis(
        fig,
        "Energy (kWh)",
    )


def cost_forecast_chart(
    forecast: pd.DataFrame,
) -> go.Figure:
    """Forecast electricity cost."""

    if (
        forecast is None
        or forecast.empty
        or "Date" not in forecast.columns
        or "Cost_INR" not in forecast.columns
    ):
        return _empty_figure()

    data = forecast.copy()

    data["Date"] = pd.to_datetime(
        data["Date"],
        errors="coerce",
    )

    data["Cost_INR"] = _numeric(
        data,
        "Cost_INR",
    )

    data = data.dropna(
        subset=["Date"]
    )

    if data.empty:
        return _empty_figure()

    fig = px.line(
        data,
        x="Date",
        y="Cost_INR",
        markers=True,
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{x|%d %b %Y}</b>"
            "<br>Forecast cost: ₹%{y:,.2f}"
            "<extra></extra>"
        )
    )

    _base_layout(
        fig,
        title="Forecast Electricity Cost",
    )

    return _format_axis(
        fig,
        "Cost (INR)",
    )


def carbon_forecast_chart(
    forecast: pd.DataFrame,
) -> go.Figure:
    """Forecast carbon emissions."""

    if (
        forecast is None
        or forecast.empty
        or "Date" not in forecast.columns
        or "Carbon_kgCO2" not in forecast.columns
    ):
        return _empty_figure()

    data = forecast.copy()

    data["Date"] = pd.to_datetime(
        data["Date"],
        errors="coerce",
    )

    data["Carbon_kgCO2"] = _numeric(
        data,
        "Carbon_kgCO2",
    )

    data = data.dropna(
        subset=["Date"]
    )

    if data.empty:
        return _empty_figure()

    fig = px.line(
        data,
        x="Date",
        y="Carbon_kgCO2",
        markers=True,
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{x|%d %b %Y}</b>"
            "<br>Forecast carbon: %{y:,.2f} kgCO₂"
            "<extra></extra>"
        )
    )

    _base_layout(
        fig,
        title="Forecast Carbon Emissions",
    )

    return _format_axis(
        fig,
        "Carbon (kgCO₂)",
    )


# ============================================================
# Monthly Energy
# ============================================================

def monthly_energy_chart(
    df: pd.DataFrame,
) -> go.Figure:
    """Monthly energy consumption."""

    data = _prepare(
        df,
        ["Date", "Energy_kWh"],
    )

    if data.empty:
        return _empty_figure()

    data = _date(data)

    if data.empty:
        return _empty_figure()

    data["Energy_kWh"] = _numeric(
        data,
        "Energy_kWh",
    )

    monthly = (
        data.assign(
            Period=data["Date"]
            .dt.to_period("M")
            .dt.to_timestamp()
        )
        .groupby(
            "Period",
            as_index=False,
        )["Energy_kWh"]
        .sum()
    )

    fig = px.bar(
        monthly,
        x="Period",
        y="Energy_kWh",
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{x|%b %Y}</b>"
            "<br>Energy: %{y:,.2f} kWh"
            "<extra></extra>"
        )
    )

    _base_layout(
        fig,
        title="Monthly Energy Consumption",
    )

    return _format_axis(
        fig,
        "Energy (kWh)",
    )


# ============================================================
# Energy Distribution
# ============================================================

def energy_distribution_chart(
    df: pd.DataFrame,
) -> go.Figure:
    """Distribution of record-level energy consumption."""

    data = _prepare(
        df,
        ["Energy_kWh"],
    )

    if data.empty:
        return _empty_figure()

    values = _numeric(
        data,
        "Energy_kWh",
    )

    fig = px.histogram(
        x=values,
        nbins=30,
    )

    fig.update_traces(
        hovertemplate=(
            "Energy: %{x:,.2f} kWh"
            "<br>Records: %{y:,}"
            "<extra></extra>"
        )
    )

    _base_layout(
        fig,
        title="Energy Consumption Distribution",
    )

    fig.update_xaxes(
        title_text="Energy (kWh)"
    )

    fig.update_yaxes(
        title_text="Record Count"
    )

    return fig


# ============================================================
# Generic Daily Metric
# ============================================================

def daily_metric_chart(
    df: pd.DataFrame,
    metric: str,
    label: str | None = None,
    aggregation: str = "sum",
) -> go.Figure:
    """Generic daily metric chart."""

    if (
        df is None
        or df.empty
        or "Date" not in df.columns
        or metric not in df.columns
    ):
        return _empty_figure()

    data = df.copy()

    data["Date"] = pd.to_datetime(
        data["Date"],
        errors="coerce",
    )

    data[metric] = _numeric(
        data,
        metric,
    )

    data = data.dropna(
        subset=["Date"]
    )

    if data.empty:
        return _empty_figure()

    if aggregation not in {
        "sum",
        "mean",
        "max",
        "min",
        "median",
    }:
        aggregation = "sum"

    daily = (
        data.groupby(
            data["Date"].dt.normalize()
        )[metric]
        .agg(aggregation)
        .reset_index()
    )

    display_label = label or metric

    fig = px.line(
        daily,
        x="Date",
        y=metric,
        markers=True,
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{x|%d %b %Y}</b>"
            f"<br>{display_label}: "
            "%{y:,.2f}"
            "<extra></extra>"
        )
    )

    _base_layout(
        fig,
        title=display_label,
    )

    return _format_axis(
        fig,
        display_label,
    )


# ============================================================
# Public API
# ============================================================

__all__ = [
    "daily_energy_chart",
    "energy_waste_trend_chart",
    "renewable_energy_chart",
    "carbon_emission_chart",
    "carbon_vs_renewable_chart",
    "carbon_renewable_chart",
    "building_energy_chart",
    "top_energy_consumers_chart",
    "department_energy_chart",
    "floor_energy_chart",
    "appliance_energy_chart",
    "waste_reason_chart",
    "building_waste_chart",
    "_normalize_anomaly",
    "ai_anomaly_chart",
    "anomaly_by_building_chart",
    "occupancy_energy_chart",
    "power_factor_chart",
    "sustainability_gauge",
    "renewable_gauge",
    "energy_forecast_chart",
    "cost_forecast_chart",
    "carbon_forecast_chart",
    "monthly_energy_chart",
    "energy_distribution_chart",
    "daily_metric_chart",
]