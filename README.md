# Baccarat Analyzer

Aplicacion analitica en Python y Streamlit para detectar patrones, simular bankroll y explorar datos de partidas de bacara. Incluye estructura modular y pruebas unitarias.

## Que hace

Toma un historial de partidas en CSV y genera estadisticas sobre rachas, frecuencia de resultados, distribucion y evolucion del bankroll. El dashboard es interactivo y corre en el navegador.

## Como correrlo

```bash
git clone https://github.com/epinki07/baccarat_analyzer.git
cd baccarat_analyzer
pip install -r requirements.txt
streamlit run app.py
```

La aplicacion queda disponible en `http://localhost:8501`.

## Estructura

```
baccarat_analyzer/
├── app.py
├── src/
│   ├── analyzer.py
│   ├── patterns.py
│   └── bankroll.py
├── data/
│   └── historial.csv
├── tests/
│   └── test_analyzer.py
└── requirements.txt
```

## Tech Stack

Python 3.9+, Streamlit, pandas, numpy, matplotlib.

## Autor

Diego Ramirez Magana — [LinkedIn](https://www.linkedin.com/in/diego-ramirez-maga%C3%B1a-b15022298/) | [GitHub](https://github.com/epinki07) | dramirezmagana@gmail.com
