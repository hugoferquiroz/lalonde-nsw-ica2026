"""Análisis de sensibilidad: placebo temporal, E-value y Rosenbaum Γ."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def placebo_temporal(
    df: pd.DataFrame,
    placebo_outcome: str = "re74",
    tratamiento: str = "treat",
    covariables: list[str] | None = None,
    metodo: str = "aipw",
    random_state: int = 42,
) -> dict:
    """
    Prueba placebo temporal: estima el efecto sobre un outcome pre-tratamiento.

    Si el estimador es válido, el efecto debe ser estadísticamente indistinguible
    de cero (el tratamiento NSW no puede afectar ingresos anteriores a 1975).

    Parameters
    ----------
    placebo_outcome : str
        're74' (ingresos 1974) o 're75' (ingresos 1975).
    metodo : str
        'aipw' o 'psm'.

    Returns
    -------
    dict con claves: ATT_placebo, SE, CI_lower, CI_upper, p_valor, rechaza_H0
    """
    from lalonde_nsw.estimators import estimar_aipw, estimar_psm

    covs = [c for c in (covariables or []) if c != placebo_outcome] or [
        c for c in ["age", "educ", "black", "hisp", "married", "nodegree", "re75"]
        if c != placebo_outcome
    ]

    if metodo == "psm":
        res = estimar_psm(df, outcome=placebo_outcome, tratamiento=tratamiento,
                          covariables=covs, random_state=random_state)
    else:
        res = estimar_aipw(df, outcome=placebo_outcome, tratamiento=tratamiento,
                           covariables=covs, random_state=random_state)

    z = res["ATT"] / res["SE"] if res["SE"] > 0 else np.nan
    p_valor = 2 * (1 - stats.norm.cdf(abs(z)))

    return {
        "ATT_placebo": res["ATT"],
        "SE": res["SE"],
        "CI_lower": res["CI_lower"],
        "CI_upper": res["CI_upper"],
        "p_valor": float(p_valor),
        "rechaza_H0": bool(p_valor < 0.05),
        "outcome_placebo": placebo_outcome,
    }


def calcular_evalor(rr: float) -> dict:
    """
    E-value de VanderWeele & Ding (2017) para un Risk Ratio observado.

    El E-value es el mínimo grado de asociación (en escala RR) que un
    confundidor no observado necesitaría tener con tratamiento Y resultado
    para explicar completamente el efecto estimado.

    E-value = RR + sqrt(RR · (RR − 1))
    E-value_IC = RR_IC_inferior + sqrt(RR_IC_inferior · (RR_IC_inferior − 1))

    Parameters
    ----------
    rr : float
        Risk Ratio del efecto puntual (debe ser ≥ 1; si RR < 1, usar 1/RR).

    Returns
    -------
    dict con claves: RR, evalor, interpretacion
    """
    if rr < 1:
        rr = 1.0 / rr
    evalor = rr + np.sqrt(rr * (rr - 1))
    return {
        "RR": round(rr, 3),
        "evalor": round(evalor, 3),
        "interpretacion": (
            f"Un confundidor no observado necesitaría una asociación RR ≥ {evalor:.2f} "
            "tanto con el tratamiento como con el resultado para explicar el efecto observado."
        ),
    }


def evalor_desde_att(
    ATT: float,
    media_control: float,
    CI_lower: float | None = None,
) -> dict:
    """
    Calcula el E-value convirtiendo el ATT en escala de Risk Ratio.

    RR aproximado = (media_control + ATT) / media_control
    """
    if media_control <= 0:
        raise ValueError("media_control debe ser positiva para convertir ATT a RR")
    rr = (media_control + ATT) / media_control
    resultado = calcular_evalor(rr)

    if CI_lower is not None:
        rr_ic = (media_control + CI_lower) / media_control
        if rr_ic < 1:
            rr_ic = 1.0 / rr_ic
        evalor_ic = rr_ic + np.sqrt(rr_ic * (rr_ic - 1)) if rr_ic > 1 else 1.0
        resultado["evalor_CI_lower"] = round(evalor_ic, 3)

    return resultado


def analisis_rosenbaum_gamma(
    ATT: float,
    SE: float,
    gamma_range: list[float] | None = None,
) -> pd.DataFrame:
    """
    Análisis de sensibilidad de Rosenbaum (2002) al sesgo oculto.

    Para cada valor de Γ (odds ratio de asignación al tratamiento por U no observada),
    calcula el p-valor de Rosenbaum bajo el escenario más adverso.
    Γ = 1 corresponde a ausencia de sesgo; el umbral crítico es el menor Γ
    que hace el intervalo de confianza incluir el cero (p-valor ≥ 0.05).

    Aproximación normal: bajo Γ, el ATT límite superior del sesgo es
        ATT_max = ATT · (Γ + 1) / (2Γ)  [aproximación de Imbens & Rubin, Cap. 14]
    y se calcula el p-valor correspondiente.

    Returns
    -------
    pd.DataFrame con columnas: Gamma, ATT_ajustado, p_valor, significativo
    """
    if gamma_range is None:
        gamma_range = [1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]

    filas = []
    for gamma in gamma_range:
        # Bajo Γ, el sesgo de selección máximo reduce el ATT estimado
        # en un factor relacionado con la asimetría de odds
        factor_sesgo = (gamma) / (gamma + 1)
        ATT_ajustado = ATT * (1 - (gamma - 1) / (2 * gamma))
        z = ATT_ajustado / SE if SE > 0 else np.nan
        p_val = float(1 - stats.norm.cdf(z))
        filas.append(
            {
                "Gamma": gamma,
                "ATT_ajustado": round(ATT_ajustado, 0),
                "p_valor": round(p_val, 4),
                "significativo (p<0.05)": p_val < 0.05,
            }
        )

    return pd.DataFrame(filas).set_index("Gamma")
