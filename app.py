from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.alerts import generate_alerts
from src.analytics import (
    build_observation_dataframe,
    build_streak_segments,
    build_summary_table,
    classify_empirical_confidence,
    calculate_block_frequencies,
    calculate_core_metrics,
    estimate_next_result_likelihood,
    parse_result_sequence,
)
from src.bankroll import BankrollConfig, simulate_bankroll
from src.charts import (
    build_bankroll_chart,
    build_distribution_chart,
    build_streak_chart,
    build_timeline_chart,
)
from src.loader import LoaderError, dataframe_to_csv_bytes, load_baccarat_csv

SAMPLE_DATA_PATH = Path(__file__).parent / "sample_data" / "sample_baccarat.csv"
OBSERVATION_SEQUENCE_KEY = "observation_sequence"
OBSERVATION_LOG_KEY = "observation_log"
STOP_REASON_LABELS = {
    "completed": "Sesión procesada completa",
    "stop_loss": "Límite de pérdida alcanzado",
    "target_profit": "Objetivo de ganancia alcanzado",
    "insufficient_bankroll": "Bankroll insuficiente para continuar",
}


def main() -> None:
    """Run the Streamlit application."""
    st.set_page_config(page_title="Baccarat Analyzer", layout="wide")
    st.title("Baccarat Analyzer")
    st.caption("Herramienta local de análisis estadístico, visualización y gestión de bankroll.")
    st.warning(
        "Aviso: baccarat tiene ventaja de la casa y los resultados pasados no garantizan "
        "resultados futuros. Esta app no ofrece predicción segura ni promesas de ganancias."
    )

    dataframe = load_session_data()
    if dataframe is None:
        return

    metrics = calculate_core_metrics(dataframe)
    streak_dataframe = build_streak_segments(dataframe)
    block_tables = calculate_block_frequencies(dataframe)
    summary_table = build_summary_table(dataframe)

    initialize_session_state()
    render_key_metrics(metrics)
    render_alerts(dataframe)

    summary_tab, charts_tab, observation_tab, bankroll_tab, export_tab = st.tabs(
        ["Resumen", "Visualizaciones", "Observación", "Bankroll", "Exportación"]
    )

    with summary_tab:
        st.subheader("Tabla resumen")
        st.dataframe(summary_table, use_container_width=True, hide_index=True)
        render_block_tables(block_tables)
        with st.expander("Ver datos normalizados"):
            st.dataframe(dataframe, use_container_width=True, hide_index=True)

    with charts_tab:
        st.subheader("Visualizaciones")
        st.plotly_chart(build_timeline_chart(dataframe), use_container_width=True)
        chart_left, chart_right = st.columns(2)
        with chart_left:
            st.plotly_chart(build_distribution_chart(dataframe), use_container_width=True)
        with chart_right:
            st.plotly_chart(build_streak_chart(streak_dataframe), use_container_width=True)

    with observation_tab:
        render_observation_section()

    with bankroll_tab:
        render_bankroll_section(dataframe)

    with export_tab:
        st.subheader("Exportación")
        st.download_button(
            label="Descargar resumen analítico (CSV)",
            data=dataframe_to_csv_bytes(summary_table),
            file_name="baccarat_summary.csv",
            mime="text/csv",
        )
        st.download_button(
            label="Descargar datos normalizados (CSV)",
            data=dataframe_to_csv_bytes(dataframe),
            file_name="baccarat_normalized_data.csv",
            mime="text/csv",
        )


def load_session_data() -> pd.DataFrame | None:
    """Load either an uploaded CSV or the bundled sample dataset."""
    st.sidebar.header("Fuente de datos")
    uploaded_file = st.sidebar.file_uploader("Carga un archivo CSV", type=["csv"])
    use_sample = st.sidebar.checkbox("Usar dataset de ejemplo si no hay archivo", value=True)

    if uploaded_file is None and not use_sample:
        st.info("Carga un archivo CSV o activa el dataset de ejemplo para comenzar.")
        return None

    source: Any = uploaded_file if uploaded_file is not None else SAMPLE_DATA_PATH
    source_name = uploaded_file.name if uploaded_file is not None else SAMPLE_DATA_PATH.name

    try:
        dataframe = load_baccarat_csv(source)
    except LoaderError as exc:
        st.error(f"Error al cargar el CSV: {exc}")
        return None
    except FileNotFoundError:
        st.error("No se encontró el archivo de ejemplo en sample_data/sample_baccarat.csv.")
        return None

    st.sidebar.success(f"Datos cargados: {source_name}")
    return dataframe


def initialize_session_state() -> None:
    """Prepare Streamlit session state keys used by the live observation panel."""
    if OBSERVATION_SEQUENCE_KEY not in st.session_state:
        st.session_state[OBSERVATION_SEQUENCE_KEY] = ""
    if OBSERVATION_LOG_KEY not in st.session_state:
        st.session_state[OBSERVATION_LOG_KEY] = []


def render_key_metrics(metrics: dict[str, Any]) -> None:
    """Display top-level metrics for the current session."""
    percentages = metrics["percentages"]
    current_streak = metrics["current_streak"]
    transitions = metrics["transitions"]

    top_columns = st.columns(4)
    top_columns[0].metric("Total de manos", metrics["total_hands"])
    top_columns[1].metric("Banker %", f'{percentages["Banker"]:.2f}%')
    top_columns[2].metric("Player %", f'{percentages["Player"]:.2f}%')
    top_columns[3].metric("Tie %", f'{percentages["Tie"]:.2f}%')

    second_columns = st.columns(3)
    second_columns[0].metric(
        "Racha actual",
        f'{current_streak["result"]} x{current_streak["length"]}',
    )
    second_columns[1].metric("Alternancias", int(transitions["alternations"]))
    second_columns[2].metric("Repeticiones", int(transitions["repetitions"]))


def render_alerts(dataframe: pd.DataFrame) -> None:
    """Display active analytical alerts for the loaded session."""
    st.subheader("Alertas analíticas")
    alerts = generate_alerts(dataframe)
    if not alerts:
        st.info("No hay alertas activas según las reglas analíticas configuradas.")
        return

    for alert in alerts:
        text = f'**{alert["title"]}**\n\n{alert["message"]}'
        if alert["level"] == "warning":
            st.warning(text)
        else:
            st.info(text)


def render_block_tables(block_tables: dict[int, pd.DataFrame]) -> None:
    """Display frequency tables for each requested block size."""
    st.subheader("Frecuencia por bloques")
    for block_size, table in block_tables.items():
        with st.expander(f"Bloques de {block_size} manos"):
            st.dataframe(table, use_container_width=True, hide_index=True)


def render_bankroll_section(dataframe: pd.DataFrame) -> None:
    """Render bankroll inputs, simulation output and CSV export."""
    st.subheader("Simulación de bankroll")
    st.caption(
        "La simulación usa los resultados históricos cargados para evaluar impacto sobre el bankroll. "
        "No implica predicción ni expectativa de ganancia futura."
    )

    left_column, right_column = st.columns(2)
    with left_column:
        initial_bankroll = st.number_input(
            "Bankroll inicial",
            min_value=1.0,
            value=1000.0,
            step=50.0,
        )
        base_bet = st.number_input(
            "Apuesta fija",
            min_value=1.0,
            value=25.0,
            step=5.0,
        )
        bet_on = st.selectbox("Apostar a", options=["Banker", "Player"])
        stop_loss = st.number_input(
            "Límite de pérdida (0 = desactivado)",
            min_value=0.0,
            value=200.0,
            step=25.0,
        )

    with right_column:
        progression_enabled = st.checkbox("Activar progresión", value=False)
        progression_multiplier = st.number_input(
            "Multiplicador de progresión",
            min_value=1.0,
            value=2.0,
            step=0.5,
            disabled=not progression_enabled,
        )
        progression_steps = st.number_input(
            "Pasos máximos de progresión",
            min_value=0,
            value=3,
            step=1,
            disabled=not progression_enabled,
        )
        target_profit = st.number_input(
            "Objetivo de ganancia (0 = desactivado)",
            min_value=0.0,
            value=200.0,
            step=25.0,
        )

    config = BankrollConfig(
        initial_bankroll=float(initial_bankroll),
        base_bet=float(base_bet),
        bet_on=bet_on,
        progression_enabled=progression_enabled,
        progression_multiplier=float(progression_multiplier),
        progression_steps=int(progression_steps),
        stop_loss=float(stop_loss) or None,
        target_profit=float(target_profit) or None,
    )

    try:
        history, summary = simulate_bankroll(dataframe, config)
    except ValueError as exc:
        st.error(f"No se pudo ejecutar la simulación: {exc}")
        return

    metric_columns = st.columns(4)
    metric_columns[0].metric("Bankroll final", f'{summary["final_bankroll"]:.2f}')
    metric_columns[1].metric("PnL", f'{summary["profit_loss"]:.2f}')
    metric_columns[2].metric("ROI", f'{summary["roi_pct"]:.2f}%')
    metric_columns[3].metric("Max drawdown", f'{summary["max_drawdown"]:.2f}')

    st.caption(f'Fin de simulación: {STOP_REASON_LABELS.get(summary["stop_reason"], summary["stop_reason"])}')
    st.plotly_chart(
        build_bankroll_chart(history, summary["starting_bankroll"]),
        use_container_width=True,
    )
    st.dataframe(history, use_container_width=True, hide_index=True)

    st.download_button(
        label="Descargar simulación de bankroll (CSV)",
        data=dataframe_to_csv_bytes(history),
        file_name="baccarat_bankroll_simulation.csv",
        mime="text/csv",
    )


def render_observation_section() -> None:
    """Render a manual live observation panel based on what the user sees on screen."""
    st.subheader("Observación visible")
    st.caption(
        "Ingresa o registra la secuencia que ves en pantalla. "
        "La app calcula una estimación empírica y un nivel de confianza descriptiva."
    )
    st.info(
        "Esto no es una predicción segura. Solo resume frecuencias observadas en la secuencia visible."
    )

    button_columns = st.columns(4)
    if button_columns[0].button("Agregar Banker", use_container_width=True):
        append_observation_token("B")
    if button_columns[1].button("Agregar Player", use_container_width=True):
        append_observation_token("P")
    if button_columns[2].button("Agregar Tie", use_container_width=True):
        append_observation_token("T")
    if button_columns[3].button("Limpiar secuencia", use_container_width=True):
        st.session_state[OBSERVATION_SEQUENCE_KEY] = ""

    st.text_area(
        "Secuencia visible",
        key=OBSERVATION_SEQUENCE_KEY,
        height=120,
        help="Ejemplo: B,P,B,B,T,P o Banker, Player, Tie.",
    )

    sequence_text = st.session_state[OBSERVATION_SEQUENCE_KEY]
    if not sequence_text.strip():
        st.info("Registra la secuencia visible para generar una estimación.")
        render_observation_log()
        return

    try:
        results = parse_result_sequence(sequence_text)
    except ValueError as exc:
        st.error(str(exc))
        render_observation_log()
        return

    max_window = min(50, len(results))
    min_window = min(5, max_window)
    window = st.slider(
        "Últimos resultados visibles a analizar",
        min_value=min_window,
        max_value=max_window,
        value=max_window,
        step=1,
        key="observation_window",
    )

    observation_dataframe = build_observation_dataframe(results)
    estimate = estimate_next_result_likelihood(observation_dataframe, window=window)
    confidence = classify_empirical_confidence(
        top_probability=estimate["top_probability"],
        window=estimate["window"],
    )

    columns = st.columns(4)
    columns[0].metric("Más frecuente", estimate["top_result"])
    columns[1].metric("Probabilidad empírica", f'{estimate["top_probability"]:.2f}%')
    columns[2].metric("Confianza descriptiva", confidence["level"])
    columns[3].metric("Dominancia estadística", "Sí" if confidence["dominant_signal"] else "No")

    st.caption(confidence["note"])

    probability_table = pd.DataFrame(
        {
            "result": list(estimate["probabilities"].keys()),
            "count": [estimate["counts"][result] for result in estimate["probabilities"]],
            "empirical_probability_pct": list(estimate["probabilities"].values()),
        }
    )
    st.dataframe(probability_table, use_container_width=True, hide_index=True)

    if st.button("Guardar esta estimación en el registro", use_container_width=True):
        st.session_state[OBSERVATION_LOG_KEY].append(
            {
                "recorded_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "visible_results_analyzed": estimate["window"],
                "top_result": estimate["top_result"],
                "empirical_probability_pct": estimate["top_probability"],
                "confidence_level": confidence["level"],
                "dominant_signal": "Sí" if confidence["dominant_signal"] else "No",
                "sequence_snapshot": sequence_text.strip(),
            }
        )
        st.success("Estimación guardada en el registro.")

    render_observation_log()


def append_observation_token(token: str) -> None:
    """Append a shorthand token to the visible observation sequence."""
    current_value = st.session_state.get(OBSERVATION_SEQUENCE_KEY, "").strip()
    st.session_state[OBSERVATION_SEQUENCE_KEY] = f"{current_value},{token}" if current_value else token


def render_observation_log() -> None:
    """Render and export the history of saved live observations."""
    st.subheader("Registro de observaciones")
    log_rows = st.session_state.get(OBSERVATION_LOG_KEY, [])
    if not log_rows:
        st.info("Todavía no has guardado estimaciones.")
        return

    log_dataframe = pd.DataFrame(log_rows)
    st.dataframe(log_dataframe, use_container_width=True, hide_index=True)
    st.download_button(
        label="Descargar registro de observaciones (CSV)",
        data=dataframe_to_csv_bytes(log_dataframe),
        file_name="baccarat_observation_log.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
