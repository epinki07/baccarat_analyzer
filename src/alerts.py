from __future__ import annotations

from typing import Any

import pandas as pd

from src.analytics import calculate_current_streak, calculate_result_percentages, calculate_transitions


def generate_alerts(
    dataframe: pd.DataFrame,
    *,
    recent_window: int = 20,
    streak_threshold: int = 4,
    alternation_threshold: float = 70.0,
    dominant_threshold: float = 45.0,
) -> list[dict[str, Any]]:
    """Generate simple analytical alerts from the loaded session."""
    alerts: list[dict[str, Any]] = []
    alerts.extend(build_streak_alerts(dataframe, streak_threshold=streak_threshold))
    alerts.extend(
        build_alternation_alert(
            dataframe,
            recent_window=recent_window,
            alternation_threshold=alternation_threshold,
        )
    )
    alerts.extend(
        build_no_pattern_alert(
            dataframe,
            recent_window=recent_window,
            dominant_threshold=dominant_threshold,
        )
    )
    return alerts


def build_streak_alerts(
    dataframe: pd.DataFrame,
    *,
    streak_threshold: int,
) -> list[dict[str, Any]]:
    """Alert when the current Banker or Player streak is above the threshold."""
    current_streak = calculate_current_streak(dataframe)
    result = current_streak["result"]
    length = int(current_streak["length"])

    if result in {"Banker", "Player"} and length >= streak_threshold:
        return [
            {
                "level": "warning",
                "title": f"Racha de {result} >= {streak_threshold}",
                "message": f"La sesión actual muestra una racha activa de {result} con longitud {length}.",
            }
        ]
    return []


def build_alternation_alert(
    dataframe: pd.DataFrame,
    *,
    recent_window: int,
    alternation_threshold: float,
) -> list[dict[str, Any]]:
    """Alert when recent hands are alternating too frequently."""
    recent_hands = dataframe.tail(min(recent_window, len(dataframe)))
    if len(recent_hands) < 5:
        return []

    transitions = calculate_transitions(recent_hands)
    if transitions["alternation_ratio"] >= alternation_threshold:
        return [
            {
                "level": "info",
                "title": f"Alta alternancia en últimas {len(recent_hands)} manos",
                "message": (
                    "El ratio de alternancia reciente es "
                    f'{transitions["alternation_ratio"]:.2f}%.'
                ),
            }
        ]
    return []


def build_no_pattern_alert(
    dataframe: pd.DataFrame,
    *,
    recent_window: int,
    dominant_threshold: float,
) -> list[dict[str, Any]]:
    """Alert when no result dominates the session."""
    if len(dataframe) < recent_window:
        return []

    percentages = calculate_result_percentages(dataframe)
    dominant_result = max(percentages, key=percentages.get)
    dominant_share = percentages[dominant_result]
    if dominant_share < dominant_threshold:
        return [
            {
                "level": "info",
                "title": "Sesión sin patrón dominante",
                "message": (
                    f"El resultado más frecuente es {dominant_result} "
                    f"con {dominant_share:.2f}% del total."
                ),
            }
        ]
    return []
