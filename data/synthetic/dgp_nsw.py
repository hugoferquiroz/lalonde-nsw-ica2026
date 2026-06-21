"""DGP sintético calibrado a estadísticas NSW experimental. ATT verdadero = $1,794."""
import numpy as np
import pandas as pd

RANDOM_STATE = 42  # semilla global del proyecto


def generar_dgp_nsw(
    n: int = 1000,
    ATT_verdadero: float = 1794.0,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """
    Genera observaciones sintéticas con estructura causal conocida.

    Calibrado a las estadísticas descriptivas de nsw_dw.dta (Dehejia & Wahba 1999).
    La columna ``tau`` contiene el efecto individual verdadero (solo en datos sintéticos).

    Returns
    -------
    pd.DataFrame con columnas:
        age, educ, black, hisp, married, nodegree, re74, re75, treat, re78, tau
    """
    rng = np.random.default_rng(random_state)

    age = rng.normal(25.8, 7.2, n).clip(17, 55).astype(int)
    educ = rng.normal(10.3, 2.0, n).clip(0, 16).astype(int)
    black = (rng.uniform(size=n) < 0.84).astype(int)
    hisp = (rng.uniform(size=n) < 0.06).astype(int)
    married = (rng.uniform(size=n) < 0.19).astype(int)
    nodegree = (rng.uniform(size=n) < 0.71).astype(int)
    re74 = np.maximum(rng.normal(2095, 5688, n), 0.0)
    re75 = np.maximum(rng.normal(1532, 3220, n), 0.0)

    logit = (
        -2.0
        + 0.05 * age
        - 0.1 * educ
        + 0.3 * black
        - 0.2 * married
        + 0.1 * nodegree
        - 0.0001 * re74
        - 0.0002 * re75
    )
    ps = 1.0 / (1.0 + np.exp(-logit))
    treat = (rng.uniform(size=n) < ps).astype(int)

    Y0 = np.maximum(
        500 + 80 * educ - 100 * nodegree + 0.3 * re74 + 0.4 * re75
        + rng.normal(0, 2000, n),
        0.0,
    )
    tau = ATT_verdadero + 200 * (educ - 10) - 150 * nodegree + rng.normal(0, 500, n)
    re78 = Y0 + treat * tau

    return pd.DataFrame(
        {
            "age": age,
            "educ": educ,
            "black": black,
            "hisp": hisp,
            "married": married,
            "nodegree": nodegree,
            "re74": re74.round(2),
            "re75": re75.round(2),
            "treat": treat,
            "re78": re78.round(2),
            "tau": tau.round(2),
        }
    )
