from __future__ import annotations

import pandas as pd

from src.analytics import (
    build_observation_dataframe,
    build_streak_segments,
    build_summary_table,
    classify_empirical_confidence,
    calculate_block_frequencies,
    calculate_current_streak,
    calculate_max_streaks,
    calculate_result_counts,
    calculate_result_percentages,
    calculate_transitions,
    estimate_next_result_likelihood,
    parse_result_sequence,
)


def build_test_dataframe() -> pd.DataFrame:
    """Create a small deterministic baccarat history for tests."""
    results = [
        "Banker",
        "Banker",
        "Player",
        "Player",
        "Player",
        "Tie",
        "Banker",
        "Banker",
        "Banker",
        "Banker",
    ]
    return pd.DataFrame(
        {
            "hand_id": [f"H{index:03d}" for index in range(1, len(results) + 1)],
            "timestamp": pd.date_range("2026-01-01 12:00:00", periods=len(results), freq="min"),
            "result": results,
            "banker_pair": [False] * len(results),
            "player_pair": [False] * len(results),
            "total_banker": [0] * len(results),
            "total_player": [0] * len(results),
            "hand_index": list(range(1, len(results) + 1)),
        }
    )


def test_result_metrics_and_streaks() -> None:
    dataframe = build_test_dataframe()

    counts = calculate_result_counts(dataframe)
    percentages = calculate_result_percentages(dataframe)
    current_streak = calculate_current_streak(dataframe)
    max_streaks = calculate_max_streaks(dataframe)

    assert counts.to_dict() == {"Banker": 6, "Player": 3, "Tie": 1}
    assert percentages == {"Banker": 60.0, "Player": 30.0, "Tie": 10.0}
    assert current_streak == {"result": "Banker", "length": 4}
    assert max_streaks == {"Banker": 4, "Player": 3, "Tie": 1}


def test_block_frequencies_and_transitions() -> None:
    dataframe = build_test_dataframe()

    block_tables = calculate_block_frequencies(dataframe)
    transitions = calculate_transitions(dataframe)
    streaks = build_streak_segments(dataframe)

    assert list(block_tables.keys()) == [10, 25, 50]
    assert block_tables[10].iloc[0]["Banker"] == 6
    assert block_tables[10].iloc[0]["Player"] == 3
    assert block_tables[10].iloc[0]["Tie"] == 1
    assert transitions == {
        "alternations": 3,
        "repetitions": 6,
        "alternation_ratio": 33.33,
        "repetition_ratio": 66.67,
    }
    assert streaks["length"].tolist() == [2, 3, 1, 4]


def test_summary_table_contains_expected_rows() -> None:
    dataframe = build_test_dataframe()
    summary_table = build_summary_table(dataframe)

    metrics = dict(zip(summary_table["metric"], summary_table["value"]))
    assert metrics["Total de manos"] == 10
    assert metrics["Racha actual"] == "Banker x4"
    assert metrics["Racha máxima Player"] == 3


def test_estimate_next_result_likelihood_uses_recent_window() -> None:
    dataframe = build_test_dataframe()
    estimate = estimate_next_result_likelihood(dataframe, window=4)

    assert estimate["window"] == 4
    assert estimate["top_result"] == "Banker"
    assert estimate["top_probability"] == 100.0


def test_visible_sequence_parsing_and_confidence() -> None:
    results = parse_result_sequence("B, p, banker, T, player")
    dataframe = build_observation_dataframe(results)
    estimate = estimate_next_result_likelihood(dataframe, window=5)
    confidence = classify_empirical_confidence(
        top_probability=estimate["top_probability"],
        window=estimate["window"],
    )

    assert results == ["Banker", "Player", "Banker", "Tie", "Player"]
    assert estimate["top_probability"] == 40.0
    assert confidence["level"] == "Sin dominancia"
    assert confidence["dominant_signal"] is False
