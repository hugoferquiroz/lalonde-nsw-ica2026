# LaLonde NSW – ICA 2026

Evaluación de impacto causal del programa de empleo NSW usando los datos de LaLonde (1986).

## Estructura

```
data/raw/          → datos originales (no versionados)
data/processed/    → datos limpios generados por scripts
data/synthetic/    → DGP sintético para validación
src/lalonde_nsw/   → módulos Python reutilizables
notebooks/         → análisis por etapa (E1, E2, E3)
reports/           → entregables del curso
tests/             → pruebas unitarias
```

## Instalación

```bash
pip install -e ".[dev]"
```

## Etapas

| Etapa | Contenido |
|-------|-----------|
| E1 | Planificación: DAG, hipótesis causales |
| E2 | Ejecución: EDA, PSM, AIPW, DML, SynC |
| E3 | Finalización: sensibilidad, informe final |
