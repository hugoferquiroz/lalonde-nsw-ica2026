"""Paquete lalonde_nsw — Inferencia Causal Aplicada ICA 2026-I."""
from lalonde_nsw.data import cargar_experimental, cargar_obs_cps1, cargar_obs_psid1, smd
from lalonde_nsw.estimators import estimar_psm, estimar_aipw, estimar_dml, tabla_resultados
from lalonde_nsw.dag import construir_dag_nsw, obtener_conjunto_ajuste

__all__ = [
    "cargar_experimental",
    "cargar_obs_cps1",
    "cargar_obs_psid1",
    "smd",
    "estimar_psm",
    "estimar_aipw",
    "estimar_dml",
    "tabla_resultados",
    "construir_dag_nsw",
    "obtener_conjunto_ajuste",
]
