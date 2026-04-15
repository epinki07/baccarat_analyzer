from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import pandas as pd

BetSide = Literal["Banker", "Player"]


@dataclass(slots=True)
class BankrollConfig:
    """Configuration for a simple historical bankroll simulation."""

    initial_bankroll: float
    base_bet: float
    bet_on: BetSide = "Banker"
    progression_enabled: bool = False
    progression_multiplier: float = 2.0
    progression_steps: int = 0
    stop_loss: float | None = None
    target_profit: float | None = None
    banker_commission: float = 0.05

    def validate(self) -> None:
        """Validate configuration values before running a simulation."""
        if self.initial_bankroll <= 0:
            raise ValueError("El bankroll inicial debe ser mayor que 0.")
        if self.base_bet <= 0:
            raise ValueError("La apuesta fija debe ser mayor que 0.")
        if self.base_bet > self.initial_bankroll:
            raise ValueError("La apuesta fija no puede ser mayor que el bankroll inicial.")
        if self.progression_multiplier <= 0:
            raise ValueError("El multiplicador de progresión debe ser mayor que 0.")
        if self.progression_steps < 0:
            raise ValueError("Los pasos de progresión no pueden ser negativos.")
        if self.stop_loss is not None and self.stop_loss <= 0:
            raise ValueError("El límite de pérdida debe ser mayor que 0.")
        if self.target_profit is not None and self.target_profit <= 0:
            raise ValueError("El objetivo de ganancia debe ser mayor que 0.")
        if not 0 <= self.banker_commission < 1:
            raise ValueError("La comisión de Banker debe estar entre 0 y 1.")


def simulate_bankroll(
    dataframe: pd.DataFrame,
    config: BankrollConfig,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Simulate the impact of betting one side over historical results."""
    config.validate()

    bankroll = round(config.initial_bankroll, 2)
    starting_bankroll = bankroll
    progression_step = 0
    history_rows: list[dict[str, Any]] = []
    stop_reason = "completed"

    for _, hand in dataframe.iterrows():
        bet_amount = calculate_bet_amount(config, progression_step)
        if bet_amount > bankroll:
            stop_reason = "insufficient_bankroll"
            break

        hand_result = str(hand["result"])
        bankroll_before = bankroll
        outcome, pnl = resolve_hand_outcome(
            hand_result=hand_result,
            bet_amount=bet_amount,
            bet_on=config.bet_on,
            banker_commission=config.banker_commission,
        )
        bankroll = round(bankroll + pnl, 2)
        next_step = calculate_next_step(
            current_step=progression_step,
            outcome=outcome,
            config=config,
        )

        history_rows.append(
            {
                "hand_number": int(hand.get("hand_index", len(history_rows) + 1)),
                "hand_id": str(hand["hand_id"]),
                "result": hand_result,
                "bet_on": config.bet_on,
                "bet_amount": round(bet_amount, 2),
                "outcome": outcome,
                "pnl": round(pnl, 2),
                "bankroll_before": bankroll_before,
                "bankroll_after": bankroll,
                "progression_step_used": progression_step,
                "next_progression_step": next_step,
            }
        )

        progression_step = next_step
        stop_reason = evaluate_stop_reason(
            config=config,
            bankroll=bankroll,
            starting_bankroll=starting_bankroll,
        )
        if stop_reason != "completed":
            break

    history = pd.DataFrame(history_rows)
    summary = build_simulation_summary(
        history=history,
        starting_bankroll=starting_bankroll,
        final_bankroll=bankroll,
        stop_reason=stop_reason,
    )
    return history, summary


def calculate_bet_amount(config: BankrollConfig, progression_step: int) -> float:
    """Return the bet amount for the current step."""
    if not config.progression_enabled:
        return round(config.base_bet, 2)

    multiplier = config.progression_multiplier ** progression_step
    return round(config.base_bet * multiplier, 2)


def resolve_hand_outcome(
    *,
    hand_result: str,
    bet_amount: float,
    bet_on: BetSide,
    banker_commission: float,
) -> tuple[str, float]:
    """Return the outcome label and profit/loss for one hand."""
    if hand_result == "Tie":
        return "push", 0.0
    if hand_result == bet_on:
        payout_multiplier = 1 - banker_commission if bet_on == "Banker" else 1.0
        return "win", round(bet_amount * payout_multiplier, 2)
    return "loss", round(-bet_amount, 2)


def calculate_next_step(
    *,
    current_step: int,
    outcome: str,
    config: BankrollConfig,
) -> int:
    """Update the progression step after a hand outcome."""
    if not config.progression_enabled:
        return 0
    if outcome == "win":
        return 0
    if outcome == "loss":
        return min(current_step + 1, config.progression_steps)
    return current_step


def evaluate_stop_reason(
    *,
    config: BankrollConfig,
    bankroll: float,
    starting_bankroll: float,
) -> str:
    """Check whether the simulation should stop after the current hand."""
    if config.stop_loss is not None and bankroll <= starting_bankroll - config.stop_loss:
        return "stop_loss"
    if config.target_profit is not None and bankroll >= starting_bankroll + config.target_profit:
        return "target_profit"
    return "completed"


def build_simulation_summary(
    *,
    history: pd.DataFrame,
    starting_bankroll: float,
    final_bankroll: float,
    stop_reason: str,
) -> dict[str, Any]:
    """Build a summary dictionary for the bankroll simulation."""
    if history.empty:
        max_drawdown = 0.0
        wins = losses = pushes = 0
    else:
        running_peak = history["bankroll_after"].cummax()
        max_drawdown = round(float((running_peak - history["bankroll_after"]).max()), 2)
        wins = int((history["outcome"] == "win").sum())
        losses = int((history["outcome"] == "loss").sum())
        pushes = int((history["outcome"] == "push").sum())

    profit_loss = round(final_bankroll - starting_bankroll, 2)
    roi_pct = round((profit_loss / starting_bankroll) * 100, 2)

    return {
        "starting_bankroll": round(starting_bankroll, 2),
        "final_bankroll": round(final_bankroll, 2),
        "profit_loss": profit_loss,
        "roi_pct": roi_pct,
        "hands_processed": int(len(history)),
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "max_drawdown": max_drawdown,
        "stop_reason": stop_reason,
    }
