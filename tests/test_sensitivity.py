"""Tests para el módulo sensitivity.py — usan solo datos sintéticos."""
import numpy as np
import pytest

from data.synthetic.dgp_nsw import generar_dgp_nsw
from lalonde_nsw.sensitivity import (
    analisis_rosenbaum_gamma,
    calcular_evalor,
    evalor_desde_att,
    placebo_temporal,
)

DF_SINT = generar_dgp_nsw(n=1000, ATT_verdadero=1794.0, random_state=42)


def test_evalor_mayor_que_rr():
    res = calcular_evalor(rr=2.0)
    assert res["evalor"] > res["RR"]


def test_evalor_rr_igual_1():
    res = calcular_evalor(rr=1.0)
    assert res["evalor"] == pytest.approx(1.0)


def test_evalor_desde_att_estructura():
    res = evalor_desde_att(ATT=1794, media_control=5000, CI_lower=600)
    assert "evalor" in res
    assert "evalor_CI_lower" in res
    assert res["evalor"] > 1.0


def test_rosenbaum_gamma_sin_sesgo():
    tabla = analisis_rosenbaum_gamma(ATT=1794.0, SE=632.0)
    # Con Γ=1 (sin sesgo) el resultado debe ser significativo
    assert tabla.loc[1.0, "significativo (p<0.05)"]


def test_rosenbaum_gamma_retorna_dataframe():
    import pandas as pd
    tabla = analisis_rosenbaum_gamma(ATT=1794.0, SE=632.0)
    assert isinstance(tabla, pd.DataFrame)
    assert "p_valor" in tabla.columns


def test_placebo_temporal_estructura():
    # Solo ejecuta con sample pequeño para no tardar mucho en CI
    df_small = DF_SINT.sample(200, random_state=42).reset_index(drop=True)
    res = placebo_temporal(df_small, placebo_outcome="re75", metodo="psm", random_state=42)
    assert "ATT_placebo" in res
    assert "p_valor" in res
    assert 0.0 <= res["p_valor"] <= 1.0
