from __future__ import annotations

import re
from typing import Any

import pandas as pd

RESULT_ORDER = ("Banker", "Player", "Tie")
RESULT_ALIASES = {
    "b": "Banker",
    "banker": "Banker",
    "p": "Player",
    "player": "Player",
    "t": "Tie",
    "tie": "Tie",
}


def calculate_result_counts(dataframe: pd.DataFrame) -> pd.Series:
    counts = dataframe["result"].value_counts().reindex(RESULT_ORDER, fill_value=0)
    return counts.astype(int)


def calculate_result_percentages(dataframe: pd.DataFrame) -> dict[str, float]:
    total_hands = len(dataframe)
    if total_hands == 0:
        return {result: 0.0 for result in RESULT_ORDER}

    counts = calculate_result_counts(dataframe)
    return {
        result: round((float(counts[result]) / total_hands) * 100, 2)
        for result in RESULT_ORDER
    }


def estimate_next_result_likelihood(
    dataframe: pd.DataFrame,
    *,
    window: int = 20,
) -> dict[str, Any]:
    """Estimate the most likely next result from recent empirical frequencies."""
    recent_hands = dataframe.tail(min(window, len(dataframe)))
    percentages = calculate_result_percentages(recent_hands)
    counts = calculate_result_counts(recent_hands)
    top_result = max(RESULT_ORDER, key=lambda result: (percentages[result], counts[result], -RESULT_ORDER.index(result)))

    return {
        "window": int(len(recent_hands)),
        "top_result": top_result,
        "top_probability": float(percentages[top_result]),
        "probabilities": percentages,
        "counts": counts.to_dict(),
    }


def parse_result_sequence(sequence_text: str) -> list[str]:
    """Parse a visible baccarat sequence entered by the user."""
    raw_tokens = [token.strip().lower() for token in re.split(r"[\s,;|/-]+", sequence_text) if token.strip()]
    if not raw_tokens:
        raise ValueError("Ingresa una secuencia visible con valores como B, P, T o Banker, Player, Tie.")

    invalid_tokens = [token for token in raw_tokens if token not in RESULT_ALIASES]
    if invalid_tokens:
        invalid_values = ", ".join(invalid_tokens[:5])
        raise ValueError(f"Valores inválidos en la secuencia visible: {invalid_values}.")

    return [RESULT_ALIASES[token] for token in raw_tokens]


def build_observation_dataframe(results: list[str]) -> pd.DataFrame:
    """Build a minimal dataframe from a manually observed sequence."""
    start_timestamp = pd.Timestamp.now().floor("s")
    return pd.DataFrame(
        {
            "hand_id": [f"OBS{index:03d}" for index in range(1, len(results) + 1)],
            "timestamp": pd.date_range(start_timestamp, periods=len(results), freq="s"),
            "result": results,
            "banker_pair": [False] * len(results),
            "player_pair": [False] * len(results),
            "total_banker": [0] * len(results),
            "total_player": [0] * len(results),
            "hand_index": list(range(1, len(results) + 1)),
        }
    )


def classify_empirical_confidence(
    *,
    top_probability: float,
    window: int,
) -> dict[str, Any]:
    """Classify recent dominance without framing it as certainty."""
    if window < 5:
        level = "Muy baja"
    elif top_probability < 45:
        level = "Sin dominancia"
    elif top_probability < 55:
        level = "Baja"
    elif top_probability < 65:
        level = "Moderada"
    else:
        level = "Alta"

    dominant_signal = window >= 10 and top_probability >= 55
    return {
        "level": level,
        "dominant_signal": dominant_signal,
        "note": "Confiabilidad descriptiva basada en frecuencia observada, no certeza.",
    }


def build_streak_segments(dataframe: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "segment_id",
        "result",
        "length",
        "start_hand_number",
        "end_hand_number",
        "start_hand_id",
        "end_hand_id",
        "start_timestamp",
        "end_timestamp",
    ]
    if dataframe.empty:
        return pd.DataFrame(columns=columns)

    results = dataframe["result"].tolist()
    hand_numbers = dataframe.get("hand_index", pd.Series(range(1, len(dataframe) + 1))).tolist()
    hand_ids = dataframe["hand_id"].astype(str).tolist()
    timestamps = dataframe["timestamp"].tolist()

    segments: list[dict[str, Any]] = []
    start_index = 0
    current_result = results[0]
    current_length = 1
    segment_id = 1

    for index in range(1, len(results)):
        next_result = results[index]
        if next_result == current_result:
            current_length += 1
            continue

        segments.append(
            _build_segment_row(
                segment_id=segment_id,
                result=current_result,
                length=current_length,
                start_index=start_index,
                end_index=index - 1,
                hand_numbers=hand_numbers,
                hand_ids=hand_ids,
                timestamps=timestamps,
            )
        )
        segment_id += 1
        start_index = index
        current_result = next_result
        current_length = 1

    segments.append(
        _build_segment_row(
            segment_id=segment_id,
            result=current_result,
            length=current_length,
            start_index=start_index,
            end_index=len(results) - 1,
            hand_numbers=hand_numbers,
            hand_ids=hand_ids,
            timestamps=timestamps,
        )
    )
    return pd.DataFrame(segments, columns=columns)


def calculate_current_streak(dataframe: pd.DataFrame) -> dict[str, Any]:
    segments = build_streak_segments(dataframe)
    if segments.empty:
        return {"result": "N/A", "length": 0}

    last_segment = segments.iloc[-1]
    return {
        "result": str(last_segment["result"]),
        "length": int(last_segment["length"]),
    }


def calculate_max_streaks(dataframe: pd.DataFrame) -> dict[str, int]:
    segments = build_streak_segments(dataframe)
    max_streaks = {result: 0 for result in RESULT_ORDER}
    if segments.empty:
        return max_streaks

    grouped = segments.groupby("result")["length"].max().to_dict()
    for result in RESULT_ORDER:
        max_streaks[result] = int(grouped.get(result, 0))
    return max_streaks


def calculate_block_frequencies(
    dataframe: pd.DataFrame,
    block_sizes: tuple[int, ...] = (10, 25, 50),
) -> dict[int, pd.DataFrame]:
    block_tables: dict[int, pd.DataFrame] = {}

    for block_size in block_sizes:
        rows: list[dict[str, Any]] = []
        for start in range(0, len(dataframe), block_size):
            block = dataframe.iloc[start : start + block_size]
            counts = calculate_result_counts(block)
            percentages = calculate_result_percentages(block)
            start_hand = int(block["hand_index"].iloc[0]) if "hand_index" in block else start + 1
            end_hand = int(block["hand_index"].iloc[-1]) if "hand_index" in block else start + len(block)

            rows.append(
                {
                    "block_number": (start // block_size) + 1,
                    "hand_range": f"{start_hand}-{end_hand}",
                    "hands_in_block": len(block),
                    "Banker": int(counts["Banker"]),
                    "Player": int(counts["Player"]),
                    "Tie": int(counts["Tie"]),
                    "banker_pct": percentages["Banker"],
                    "player_pct": percentages["Player"],
                    "tie_pct": percentages["Tie"],
                }
            )

        block_tables[block_size] = pd.DataFrame(rows)

    return block_tables


def calculate_transitions(dataframe: pd.DataFrame) -> dict[str, float]:
    results = dataframe["result"].tolist()
    if len(results) < 2:
        return {
            "alternations": 0,
            "repetitions": 0,
            "alternation_ratio": 0.0,
            "repetition_ratio": 0.0,
        }

    alternations = sum(current != previous for previous, current in zip(results, results[1:]))
    total_pairs = len(results) - 1
    repetitions = total_pairs - alternations

    return {
        "alternations": int(alternations),
        "repetitions": int(repetitions),
        "alternation_ratio": round((alternations / total_pairs) * 100, 2),
        "repetition_ratio": round((repetitions / total_pairs) * 100, 2),
    }


def calculate_core_metrics(dataframe: pd.DataFrame) -> dict[str, Any]:
    counts = calculate_result_counts(dataframe)
    percentages = calculate_result_percentages(dataframe)
    current_streak = calculate_current_streak(dataframe)
    max_streaks = calculate_max_streaks(dataframe)
    transitions = calculate_transitions(dataframe)

    return {
        "total_hands": len(dataframe),
        "counts": counts.to_dict(),
        "percentages": percentages,
        "current_streak": current_streak,
        "max_streaks": max_streaks,
        "transitions": transitions,
    }


def build_summary_table(dataframe: pd.DataFrame) -> pd.DataFrame:
    metrics = calculate_core_metrics(dataframe)
    rows = [
        {"metric": "Total de manos", "value": metrics["total_hands"]},
        {"metric": "Banker (conteo)", "value": metrics["counts"]["Banker"]},
        {"metric": "Player (conteo)", "value": metrics["counts"]["Player"]},
        {"metric": "Tie (conteo)", "value": metrics["counts"]["Tie"]},
        {"metric": "Banker (%)", "value": f'{metrics["percentages"]["Banker"]:.2f}%'},
        {"metric": "Player (%)", "value": f'{metrics["percentages"]["Player"]:.2f}%'},
        {"metric": "Tie (%)", "value": f'{metrics["percentages"]["Tie"]:.2f}%'},
        {
            "metric": "Racha actual",
            "value": f'{metrics["current_streak"]["result"]} x{metrics["current_streak"]["length"]}',
        },
        {"metric": "Racha máxima Banker", "value": metrics["max_streaks"]["Banker"]},
        {"metric": "Racha máxima Player", "value": metrics["max_streaks"]["Player"]},
        {"metric": "Racha máxima Tie", "value": metrics["max_streaks"]["Tie"]},
        {"metric": "Alternancias consecutivas", "value": metrics["transitions"]["alternations"]},
        {"metric": "Repeticiones consecutivas", "value": metrics["transitions"]["repetitions"]},
        {
            "metric": "Ratio de alternancia",
            "value": f'{metrics["transitions"]["alternation_ratio"]:.2f}%',
        },
        {
            "metric": "Ratio de repetición",
            "value": f'{metrics["transitions"]["repetition_ratio"]:.2f}%',
        },
    ]
    return pd.DataFrame(rows)


def _build_segment_row(
    *,
    segment_id: int,
    result: str,
    length: int,
    start_index: int,
    end_index: int,
    hand_numbers: list[int],
    hand_ids: list[str],
    timestamps: list[pd.Timestamp],
) -> dict[str, Any]:
    return {
        "segment_id": segment_id,
        "result": result,
        "length": int(length),
        "start_hand_number": int(hand_numbers[start_index]),
        "end_hand_number": int(hand_numbers[end_index]),
        "start_hand_id": hand_ids[start_index],
        "end_hand_id": hand_ids[end_index],
        "start_timestamp": timestamps[start_index],
        "end_timestamp": timestamps[end_index],
    }
