"""Estimadores de ATT para el proyecto LaLonde/NSW.

Pipeline:
    1. PSM  — Propensity Score Matching (sklearn)
    2. AIPW — Augmented IPW con cross-fitting manual
    3. DML  — Double/Debiased ML (econml.dml.LinearDML)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42  # semilla global del proyecto
COVARIABLES = ["age", "educ", "black", "hisp", "married", "nodegree", "re74", "re75"]


# ---------------------------------------------------------------------------
# 1. PSM — Propensity Score Matching
# ---------------------------------------------------------------------------

def estimar_psm(
    df: pd.DataFrame,
    outcome: str = "re78",
    tratamiento: str = "treat",
    covariables: list[str] | None = None,
    random_state: int = RANDOM_STATE,
) -> dict:
    """
    ATT vía Propensity Score Matching 1:1 sin reemplazo.

    Replica el enfoque de Dehejia & Wahba (1999):
    - Propensity score: LogisticRegression con covariables estandarizadas.
    - Matching: NearestNeighbors en espacio del PS (caliper implícito).
    - SE: bootstrap (500 réplicas).

    Returns
    -------
    dict con claves: ATT, SE, CI_lower, CI_upper, ps (propensity scores)
    """
    if covariables is None:
        covariables = COVARIABLES

    X_raw = df[covariables].values.astype(float)
    T = df[tratamiento].values.astype(int)
    Y = df[outcome].values.astype(float)

    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)

    lr = LogisticRegression(max_iter=1000, C=1.0, random_state=random_state)
    lr.fit(X, T)
    ps = lr.predict_proba(X)[:, 1]

    idx_t = np.where(T == 1)[0]
    idx_c = np.where(T == 0)[0]

    nn = NearestNeighbors(n_neighbors=1, algorithm="ball_tree")
    nn.fit(ps[idx_c].reshape(-1, 1))
    matched_idx = nn.kneighbors(ps[idx_t].reshape(-1, 1), return_distance=False).flatten()

    diffs = Y[idx_t] - Y[idx_c[matched_idx]]
    ATT = diffs.mean()

    # Bootstrap SE
    rng = np.random.default_rng(random_state)
    boot_atts = []
    for _ in range(500):
        sample = rng.choice(len(diffs), size=len(diffs), replace=True)
        boot_atts.append(diffs[sample].mean())
    SE = np.std(boot_atts)

    return {
        "ATT": float(ATT),
        "SE": float(SE),
        "CI_lower": float(ATT - 1.96 * SE),
        "CI_upper": float(ATT + 1.96 * SE),
        "ps": ps,
        "matched_control_idx": idx_c[matched_idx],
        "treated_idx": idx_t,
    }


# ---------------------------------------------------------------------------
# 2. AIPW — Augmented Inverse Probability Weighting
# ---------------------------------------------------------------------------

def estimar_aipw(
    df: pd.DataFrame,
    outcome: str = "re78",
    tratamiento: str = "treat",
    covariables: list[str] | None = None,
    n_splits: int = 5,
    random_state: int = RANDOM_STATE,
) -> dict:
    """
    ATT vía AIPW (estimador doblemente robusto) con cross-fitting de 5 pliegues.

    Fórmula del score de influencia para ATT (Hahn 1998, Wooldridge 2007):
        ψᵢ = [(μ₁(Xᵢ) − μ₀(Xᵢ)) · Tᵢ
               + Tᵢ · (Yᵢ − μ₁(Xᵢ))
               − (1 − Tᵢ) · e(Xᵢ) · (Yᵢ − μ₀(Xᵢ)) / (1 − e(Xᵢ))] / P̄(T=1)

    Modelos de nuisance: GradientBoosting (Regressor y Classifier).
    SE: estimado a partir de la varianza del score de influencia.

    Returns
    -------
    dict con claves: ATT, SE, CI_lower, CI_upper
    """
    if covariables is None:
        covariables = COVARIABLES

    X = df[covariables].values.astype(float)
    T = df[tratamiento].values.astype(float)
    Y = df[outcome].values.astype(float)
    n = len(Y)

    mu0_hat = np.zeros(n)
    mu1_hat = np.zeros(n)
    ps_hat = np.zeros(n)

    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    for train_idx, val_idx in kf.split(X):
        X_tr, X_val = X[train_idx], X[val_idx]
        T_tr = T[train_idx]
        Y_tr = Y[train_idx]

        ps_model = GradientBoostingClassifier(
            n_estimators=100, random_state=random_state
        )
        ps_model.fit(X_tr, T_tr)
        ps_hat[val_idx] = ps_model.predict_proba(X_val)[:, 1]

        idx0 = T_tr == 0
        m0 = GradientBoostingRegressor(n_estimators=100, random_state=random_state)
        m0.fit(X_tr[idx0], Y_tr[idx0])
        mu0_hat[val_idx] = m0.predict(X_val)

        idx1 = T_tr == 1
        m1 = GradientBoostingRegressor(n_estimators=100, random_state=random_state)
        m1.fit(X_tr[idx1], Y_tr[idx1])
        mu1_hat[val_idx] = m1.predict(X_val)

    ps_hat = np.clip(ps_hat, 0.01, 0.99)
    p_treat = T.mean()

    # Score de influencia para ATT
    psi = (
        (mu1_hat - mu0_hat) * T / p_treat
        + T * (Y - mu1_hat) / p_treat
        - (1 - T) * ps_hat * (Y - mu0_hat) / (p_treat * (1 - ps_hat))
    )

    ATT = psi.mean()
    SE = psi.std() / np.sqrt(n)

    return {
        "ATT": float(ATT),
        "SE": float(SE),
        "CI_lower": float(ATT - 1.96 * SE),
        "CI_upper": float(ATT + 1.96 * SE),
    }


# ---------------------------------------------------------------------------
# 3. DML — Double/Debiased Machine Learning
# ---------------------------------------------------------------------------

def estimar_dml(
    df: pd.DataFrame,
    outcome: str = "re78",
    tratamiento: str = "treat",
    covariables: list[str] | None = None,
    n_splits: int = 5,
    random_state: int = RANDOM_STATE,
) -> dict:
    """
    ATT vía Double/Debiased ML con cross-fitting (Chernozhukov et al. 2018).

    Usa econml.dml.LinearDML con modelos GradientBoosting como nuisance.
    Reporta el efecto promedio sobre los tratados (ATT) promediando el CATE
    estimado en las unidades tratadas.

    Returns
    -------
    dict con claves: ATT, SE, CI_lower, CI_upper
    """
    if covariables is None:
        covariables = COVARIABLES

    from econml.dml import LinearDML

    X = df[covariables]
    T = df[tratamiento].values.astype(float)
    Y = df[outcome].values.astype(float)

    # LinearDML requiere regresor para model_t (trata T como continuo 0/1)
    est = LinearDML(
        model_y=GradientBoostingRegressor(n_estimators=100, random_state=random_state),
        model_t=GradientBoostingRegressor(n_estimators=100, random_state=random_state),
        cv=n_splits,
        random_state=random_state,
    )
    est.fit(Y, T, X=X)

    X_treated = X[T == 1]
    inf = est.effect_inference(X_treated)
    effects = est.effect(X_treated)

    ATT = float(effects.mean())
    SE = float(inf.stderr.mean())

    return {
        "ATT": ATT,
        "SE": SE,
        "CI_lower": float(ATT - 1.96 * SE),
        "CI_upper": float(ATT + 1.96 * SE),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def tabla_resultados(resultados: dict[str, dict]) -> pd.DataFrame:
    """
    Convierte un dict {nombre_estimador: resultado_dict} en tabla resumen.

    Parameters
    ----------
    resultados : dict
        Clave = nombre del estimador, valor = dict con ATT, SE, CI_lower, CI_upper.
    """
    filas = []
    for nombre, r in resultados.items():
        filas.append(
            {
                "Estimador": nombre,
                "ATT ($)": round(r["ATT"], 0),
                "SE": round(r["SE"], 0),
                "IC 95% inferior": round(r["CI_lower"], 0),
                "IC 95% superior": round(r["CI_upper"], 0),
            }
        )
    return pd.DataFrame(filas).set_index("Estimador")
