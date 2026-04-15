# Baccarat Analyzer

Aplicación local en Python + Streamlit para analizar historiales de baccarat, visualizar tendencias, revisar rachas y simular impacto sobre el bankroll a partir de resultados históricos.

## Advertencia importante

Esta herramienta **no** ofrece predicción segura ni garantiza ganancias.

- Baccarat tiene ventaja de la casa.
- Los resultados pasados no garantizan resultados futuros.
- El módulo de bankroll es una simulación analítica sobre datos históricos.

## Requisitos

- Python 3.11+
- pip

## Instalación

Desde la carpeta del proyecto:

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
streamlit run app.py
```

## Tests

```bash
pytest
```

## Uso en VS Code

1. Abre VS Code.
2. Selecciona `File > Open Folder`.
3. Abre la carpeta `baccarat_analyzer`.
4. Abre una terminal integrada en VS Code.
5. Ejecuta:

```bash
pip install -r requirements.txt
streamlit run app.py
```

6. Si quieres ejecutar tests:

```bash
pytest
```

## Formato esperado del CSV

Columnas requeridas:

- `hand_id`
- `timestamp`
- `result`
- `banker_pair`
- `player_pair`
- `total_banker`
- `total_player`

Valores válidos para `result`:

- `Banker`
- `Player`
- `Tie`

## Funcionalidades incluidas

- Carga de CSV y validación de esquema.
- Métricas de sesión:
  - total de manos
  - porcentaje de Banker, Player y Tie
  - racha actual
  - racha máxima por tipo
  - frecuencia por bloques de 10, 25 y 50 manos
  - conteo de alternancias y repeticiones
- Visualizaciones:
  - línea temporal de resultados
  - gráfico de rachas
  - distribución de resultados
  - tabla resumen
- Simulación de bankroll:
  - bankroll inicial
  - apuesta fija
  - progresión opcional
  - límite de pérdida
  - objetivo de ganancia
- Alertas analíticas:
  - racha de Banker >= 4
  - racha de Player >= 4
  - alta alternancia en últimas 20 manos
  - sesión sin patrón dominante
- Exportación a CSV:
  - resumen analítico
  - datos normalizados
  - simulación de bankroll

## Estructura del proyecto

```text
baccarat_analyzer/
├── app.py
├── AGENTS.md
├── README.md
├── requirements.txt
├── sample_data/
│   └── sample_baccarat.csv
├── src/
│   ├── alerts.py
│   ├── analytics.py
│   ├── bankroll.py
│   ├── charts.py
│   └── loader.py
└── tests/
    ├── test_analytics.py
    └── test_bankroll.py
```

## Notas de implementación

- La carga de datos normaliza columnas, tipos y orden temporal.
- Las alternancias y repeticiones se calculan comparando resultados consecutivos, incluyendo `Tie`.
- En la simulación de bankroll:
  - apostar a `Banker` aplica comisión del 5%
  - `Tie` se trata como `push`
  - la progresión incrementa la apuesta tras pérdidas hasta el límite configurado

## Dataset de ejemplo

Se incluye un archivo funcional en:

```text
sample_data/sample_baccarat.csv
```

La app lo usa por defecto si no cargas un CSV manualmente.
