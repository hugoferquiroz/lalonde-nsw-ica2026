"""Tests de estimadores sobre el DGP sintético.

Criterio de aprobación (CLAUDE.md): |ATT_estimado - ATT_verdadero| < 500
con ATT_verdadero = $1,794.
"""
import numpy as np
import pytest

from data.synthetic.dgp_nsw import generar_dgp_nsw
from lalonde_nsw.estimators import estimar_aipw, estimar_dml, estimar_psm, tabla_resultados

ATT_VERDADERO = 1794.0
TOLERANCIA = 500.0
DF_SINT = generar_dgp_nsw(n=2000, ATT_verdadero=ATT_VERDADERO, random_state=42)


def _verificar_resultado(res: dict) -> None:
    """Checks comunes a todos los estimadores."""
    assert "ATT" in res
    assert "SE" in res
    assert "CI_lower" in res
    assert "CI_upper" in res
    assert res["SE"] > 0
    assert res["CI_lower"] < res["ATT"] < res["CI_upper"]


def test_psm_estructura():
    res = estimar_psm(DF_SINT, random_state=42)
    _verificar_resultado(res)


def test_psm_precision():
    res = estimar_psm(DF_SINT, random_state=42)
    error = abs(res["ATT"] - ATT_VERDADERO)
    assert error < TOLERANCIA, f"PSM error={error:.0f} > tolerancia={TOLERANCIA}"


def test_aipw_estructura():
    res = estimar_aipw(DF_SINT, n_splits=3, random_state=42)
    _verificar_resultado(res)


def test_aipw_precision():
    res = estimar_aipw(DF_SINT, n_splits=3, random_state=42)
    error = abs(res["ATT"] - ATT_VERDADERO)
    assert error < TOLERANCIA, f"AIPW error={error:.0f} > tolerancia={TOLERANCIA}"


def test_dml_estructura():
    res = estimar_dml(DF_SINT, n_splits=3, random_state=42)
    _verificar_resultado(res)


def test_dml_precision():
    res = estimar_dml(DF_SINT, n_splits=3, random_state=42)
    error = abs(res["ATT"] - ATT_VERDADERO)
    assert error < TOLERANCIA, f"DML error={error:.0f} > tolerancia={TOLERANCIA}"


def test_tabla_resultados():
    resultados = {
        "PSM": estimar_psm(DF_SINT, random_state=42),
        "AIPW": estimar_aipw(DF_SINT, n_splits=3, random_state=42),
    }
    tabla = tabla_resultados(resultados)
    assert "ATT ($)" in tabla.columns
    assert len(tabla) == 2
