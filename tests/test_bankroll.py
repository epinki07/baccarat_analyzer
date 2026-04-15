from __future__ import annotations

import pandas as pd

from src.bankroll import BankrollConfig, simulate_bankroll


def build_bankroll_dataframe(results: list[str]) -> pd.DataFrame:
    """Create a deterministic dataframe for bankroll tests."""
    return pd.DataFrame(
        {
            "hand_id": [f"H{index:03d}" for index in range(1, len(results) + 1)],
            "timestamp": pd.date_range("2026-01-01 13:00:00", periods=len(results), freq="min"),
            "result": results,
            "banker_pair": [False] * len(results),
            "player_pair": [False] * len(results),
            "total_banker": [0] * len(results),
            "total_player": [0] * len(results),
            "hand_index": list(range(1, len(results) + 1)),
        }
    )


def test_flat_bankroll_simulation_with_tie_push() -> None:
    dataframe = build_bankroll_dataframe(["Banker", "Player", "Tie", "Banker"])
    config = BankrollConfig(
        initial_bankroll=100.0,
        base_bet=10.0,
        bet_on="Banker",
    )

    history, summary = simulate_bankroll(dataframe, config)

    assert history["outcome"].tolist() == ["win", "loss", "push", "win"]
    assert summary["final_bankroll"] == 109.0
    assert summary["profit_loss"] == 9.0
    assert summary["wins"] == 2
    assert summary["losses"] == 1
    assert summary["pushes"] == 1
    assert summary["stop_reason"] == "completed"


def test_progression_and_stop_loss() -> None:
    progression_dataframe = build_bankroll_dataframe(["Player", "Banker"])
    progression_config = BankrollConfig(
        initial_bankroll=100.0,
        base_bet=10.0,
        bet_on="Banker",
        progression_enabled=True,
        progression_multiplier=2.0,
        progression_steps=2,
    )

    history, summary = simulate_bankroll(progression_dataframe, progression_config)

    assert history["bet_amount"].tolist() == [10.0, 20.0]
    assert summary["final_bankroll"] == 109.0
    assert summary["stop_reason"] == "completed"

    stop_loss_dataframe = build_bankroll_dataframe(["Player", "Player", "Player"])
    stop_loss_config = BankrollConfig(
        initial_bankroll=50.0,
        base_bet=10.0,
        bet_on="Banker",
        stop_loss=20.0,
    )

    stop_history, stop_summary = simulate_bankroll(stop_loss_dataframe, stop_loss_config)

    assert len(stop_history) == 2
    assert stop_summary["final_bankroll"] == 30.0
    assert stop_summary["stop_reason"] == "stop_loss"
