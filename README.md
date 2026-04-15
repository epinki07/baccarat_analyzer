# 📊 Baccarat Analyzer

Aplicación analítica en **Python + Streamlit** para detectar patrones, simular bankroll y explorar datos de juego de bacará.

## 📋 ¿Qué hace?

- **Análisis de tendencias**: Rachas, patrones y estadísticas
- **Simulación de bankroll**: Probar estrategias con datos históricos
- **Visualización interactiva**: Dashboard en Streamlit
- **Módulo de tests**: Validación de lógica analítica

## 🛠️ Tech Stack

| Lenguaje | Framework | Análisis |
|----------|-----------|----------|
| Python 3.9+ | Streamlit | pandas |
| | | numpy |
| | | matplotlib |

## 🚀 Cómo correrlo localmente

### Prerrequisitos

```bash
python3 --version  # Python 3.9+
pip3 --version
```

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/epinki07/baccarat_analyzer.git
cd baccarat_analyzer

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
streamlit run app.py
```

### Acceder

```
http://localhost:8501
```

## 📁 Estructura del proyecto

```
baccarat_analyzer/
├── app.py                  # Aplicación Streamlit
├── src/
│   ├── analyzer.py         # Lógica de análisis
│   ├── patterns.py         # Detección de patrones
│   └── bankroll.py         # Simulaciones
├── data/
│   └── historial.csv       # Datos de ejemplo
├── tests/
│   └── test_analyzer.py    # Tests unitarios
├── requirements.txt
└── README.md
```

## 📊 Características

### Métricas analizadas

- **Rachas**: Secuencias de victorias/derrotas
- **Frecuencias**: Distribución de resultados
- **Tendencias**: Patrones repetitivos
- **ROI**: Retorno sobre inversión simulado

### Visualizaciones

- Gráficas de evolución de bankroll
- Heatmaps de patrones
- Distribuciones de resultados

## 💡 Qué aprendí

- **Streamlit**: Dashboards rápidos en Python
- **Análisis de datos**: pandas, estadísticas
- **Visualización**: matplotlib, seaborn
- **Testing**: pytest para lógica analítica
- **Pensamiento analítico**: Detectar patrones en datos

## 🔮 Mejoras futuras

- [ ] Exportar reportes a PDF
- [ ] Más estrategias de betting
- [ ] Backtesting automático
- [ ] Interfaz multi-usuario

## 🤝 Autor

**Diego Ramirez Magaña**

- 📧 dramirezmagana@gmail.com
- 🔗 [LinkedIn](https://www.linkedin.com/in/diego-ramirez-maga%C3%B1a-b15022298/)
- 🐙 [GitHub](https://github.com/epinki07)

---

> **Nota**: Este proyecto comunica pensamiento analítico y disciplina técnica. Incluye estructura modular y tests.
