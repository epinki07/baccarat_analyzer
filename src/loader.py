from __future__ import annotations

from pathlib import Path
from typing import IO

import pandas as pd

REQUIRED_COLUMNS = (
    "hand_id",
    "timestamp",
    "result",
    "banker_pair",
    "player_pair",
    "total_banker",
    "total_player",
)
VALID_RESULTS = ("Banker", "Player", "Tie")

_BOOLEAN_MAP = {
    "": False,
    "0": False,
    "false": False,
    "n": False,
    "no": False,
    "nan": False,
    "none": False,
    "1": True,
    "true": True,
    "y": True,
    "yes": True,
    "si": True,
    "sí": True,
}


class LoaderError(ValueError):
    """Raised when the baccarat CSV cannot be parsed safely."""


def load_baccarat_csv(source: str | Path | IO[str] | IO[bytes]) -> pd.DataFrame:
    """Load and validate a baccarat history CSV."""
    try:
        dataframe = pd.read_csv(source)
    except Exception as exc:  # pragma: no cover - pandas surfaces many reader errors
        raise LoaderError(f"No se pudo leer el archivo CSV: {exc}") from exc

    if dataframe.empty:
        raise LoaderError("El archivo CSV no contiene filas.")

    return normalize_baccarat_dataframe(dataframe)


def normalize_baccarat_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names and validate the expected baccarat schema."""
    normalized = dataframe.copy()
    normalized.columns = [str(column).strip().lower() for column in normalized.columns]

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in normalized.columns]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise LoaderError(f"Faltan columnas requeridas en el CSV: {missing}.")

    normalized = normalized.loc[:, list(REQUIRED_COLUMNS)].copy()
    normalized["hand_id"] = normalized["hand_id"].astype("string").str.strip()
    if normalized["hand_id"].eq("").any():
        raise LoaderError("La columna hand_id contiene valores vacíos.")

    normalized["timestamp"] = _parse_timestamp_series(normalized["timestamp"])
    normalized["result"] = _parse_result_series(normalized["result"])
    normalized["banker_pair"] = _parse_boolean_series(normalized["banker_pair"], "banker_pair")
    normalized["player_pair"] = _parse_boolean_series(normalized["player_pair"], "player_pair")
    normalized["total_banker"] = _parse_total_series(normalized["total_banker"], "total_banker")
    normalized["total_player"] = _parse_total_series(normalized["total_player"], "total_player")

    normalized = normalized.sort_values(["timestamp", "hand_id"], kind="mergesort").reset_index(drop=True)
    normalized["hand_index"] = range(1, len(normalized) + 1)
    return normalized


def _parse_timestamp_series(series: pd.Series) -> pd.Series:
    timestamps = pd.to_datetime(series, errors="coerce")
    if timestamps.isna().any():
        invalid_rows = series[timestamps.isna()].index.tolist()
        preview = ", ".join(str(index + 1) for index in invalid_rows[:5])
        raise LoaderError(
            "La columna timestamp contiene fechas inválidas en las filas: "
            f"{preview}."
        )
    return timestamps


def _parse_result_series(series: pd.Series) -> pd.Series:
    normalized = series.astype("string").str.strip().str.title()
    valid_mask = normalized.isin(VALID_RESULTS)
    if not valid_mask.all():
        invalid_values = normalized[~valid_mask].dropna().unique().tolist()
        invalid = ", ".join(str(value) for value in invalid_values[:5]) or "vacío"
        raise LoaderError(
            "La columna result solo admite Banker, Player o Tie. "
            f"Valores inválidos detectados: {invalid}."
        )
    return normalized


def _parse_boolean_series(series: pd.Series, column_name: str) -> pd.Series:
    normalized = series.astype("string").fillna("").str.strip().str.lower()
    valid_mask = normalized.isin(_BOOLEAN_MAP)
    if not valid_mask.all():
        invalid_values = normalized[~valid_mask].unique().tolist()
        invalid = ", ".join(str(value) for value in invalid_values[:5])
        raise LoaderError(
            f"La columna {column_name} contiene valores booleanos inválidos: {invalid}."
        )
    return normalized.map(_BOOLEAN_MAP).astype(bool)


def _parse_total_series(series: pd.Series, column_name: str) -> pd.Series:
    totals = pd.to_numeric(series, errors="coerce")
    if totals.isna().any():
        invalid_rows = series[totals.isna()].index.tolist()
        preview = ", ".join(str(index + 1) for index in invalid_rows[:5])
        raise LoaderError(
            f"La columna {column_name} contiene valores no numéricos en las filas: {preview}."
        )

    invalid_range_mask = (totals < 0) | (totals > 9)
    if invalid_range_mask.any():
        invalid_rows = totals[invalid_range_mask].index.tolist()
        preview = ", ".join(str(index + 1) for index in invalid_rows[:5])
        raise LoaderError(
            f"La columna {column_name} debe estar entre 0 y 9. Filas inválidas: {preview}."
        )

    return totals.astype(int)


def dataframe_to_csv_bytes(dataframe: pd.DataFrame) -> bytes:
    """Serialize a DataFrame for Streamlit downloads."""
    return dataframe.to_csv(index=False).encode("utf-8")
