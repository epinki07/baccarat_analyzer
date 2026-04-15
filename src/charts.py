from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from src.analytics import RESULT_ORDER, calculate_result_counts, calculate_result_percentages

RESULT_COLORS = {
    "Banker": "#1f77b4",
    "Player": "#d62728",
    "Tie": "#2ca02c",
}
RESULT_POSITIONS = {
    "Banker": 0,
    "Player": 1,
    "Tie": 2,
}


def build_timeline_chart(dataframe: pd.DataFrame) -> go.Figure:
    """Plot results over time using one point per hand."""
    hand_numbers = dataframe.get("hand_index", pd.Series(range(1, len(dataframe) + 1)))
    y_values = dataframe["result"].map(RESULT_POSITIONS)

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=hand_numbers,
            y=y_values,
            mode="lines",
            line={"color": "#b0b0b0", "width": 1},
            name="Secuencia",
            hoverinfo="skip",
            showlegend=False,
        )
    )

    for result in RESULT_ORDER:
        subset = dataframe[dataframe["result"] == result]
        subset_hand_numbers = subset.get("hand_index", pd.Series(range(1, len(subset) + 1)))
        figure.add_trace(
            go.Scatter(
                x=subset_hand_numbers,
                y=subset["result"].map(RESULT_POSITIONS),
                mode="markers",
                name=result,
                marker={"color": RESULT_COLORS[result], "size": 9},
                customdata=subset[["hand_id"]],
                hovertemplate=(
                    "Mano %{x}<br>"
                    f"Resultado: {result}<br>"
                    "hand_id: %{customdata[0]}<extra></extra>"
                ),
            )
        )

    figure.update_layout(
        title="Línea temporal de resultados",
        xaxis_title="Número de mano",
        yaxis_title="Resultado",
        yaxis={"tickvals": list(RESULT_POSITIONS.values()), "ticktext": list(RESULT_POSITIONS.keys())},
        template="plotly_white",
        legend_title="Resultado",
    )
    return figure


def build_streak_chart(streak_dataframe: pd.DataFrame) -> go.Figure:
    """Plot each streak segment as a bar chart."""
    figure = go.Figure()
    if streak_dataframe.empty:
        figure.add_annotation(text="No hay datos de rachas.", showarrow=False)
        figure.update_layout(template="plotly_white")
        return figure

    for result in RESULT_ORDER:
        subset = streak_dataframe[streak_dataframe["result"] == result]
        figure.add_trace(
            go.Bar(
                x=subset["segment_id"],
                y=subset["length"],
                name=result,
                marker_color=RESULT_COLORS[result],
                hovertemplate=(
                    "Racha %{x}<br>"
                    f"Resultado: {result}<br>"
                    "Longitud: %{y}<extra></extra>"
                ),
            )
        )

    figure.update_layout(
        title="Gráfico de rachas",
        xaxis_title="Segmento de racha",
        yaxis_title="Longitud",
        barmode="group",
        template="plotly_white",
        legend_title="Resultado",
    )
    return figure


def build_distribution_chart(dataframe: pd.DataFrame) -> go.Figure:
    """Plot the result distribution as a bar chart."""
    counts = calculate_result_counts(dataframe)
    percentages = calculate_result_percentages(dataframe)

    figure = go.Figure(
        data=[
            go.Bar(
                x=list(RESULT_ORDER),
                y=[int(counts[result]) for result in RESULT_ORDER],
                marker_color=[RESULT_COLORS[result] for result in RESULT_ORDER],
                text=[f'{percentages[result]:.2f}%' for result in RESULT_ORDER],
                textposition="auto",
                hovertemplate="Resultado: %{x}<br>Conteo: %{y}<extra></extra>",
            )
        ]
    )
    figure.update_layout(
        title="Distribución de resultados",
        xaxis_title="Resultado",
        yaxis_title="Conteo",
        template="plotly_white",
    )
    return figure


def build_bankroll_chart(history: pd.DataFrame, starting_bankroll: float) -> go.Figure:
    """Plot bankroll evolution through the simulated session."""
    figure = go.Figure()
    if history.empty:
        figure.add_annotation(text="No se pudo ejecutar la simulación.", showarrow=False)
        figure.update_layout(template="plotly_white")
        return figure

    figure.add_trace(
        go.Scatter(
            x=history["hand_number"],
            y=history["bankroll_after"],
            mode="lines+markers",
            name="Bankroll",
            line={"color": "#0f766e", "width": 2},
            marker={"size": 7},
            hovertemplate="Mano %{x}<br>Bankroll: %{y:.2f}<extra></extra>",
        )
    )
    figure.add_hline(
        y=starting_bankroll,
        line_dash="dash",
        line_color="#7f7f7f",
        annotation_text="Bankroll inicial",
    )
    figure.update_layout(
        title="Impacto del bankroll simulado",
        xaxis_title="Número de mano",
        yaxis_title="Bankroll",
        template="plotly_white",
    )
    return figure
