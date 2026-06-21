"""Carga, limpieza y estadísticas de balance para los datos LaLonde/NSW."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent.parent / "data" / "processed"

COVARIABLES = ["age", "educ", "black", "hisp", "married", "nodegree", "re74", "re75"]
COLUMNAS_RENAME = {"education": "educ", "hispanic": "hisp"}


def _cargar_dta(ruta: Path) -> pd.DataFrame:
    import pyreadstat

    df, _ = pyreadstat.read_dta(str(ruta))
    df = df.rename(columns=COLUMNAS_RENAME)
    df = df.drop(columns=["data_id"], errors="ignore")
    # Asegurar tipos correctos
    for col in ["treat", "black", "hisp", "married", "nodegree"]:
        if col in df.columns:
            df[col] = df[col].astype(int)
    return df


def cargar_experimental() -> pd.DataFrame:
    """
    Carga nsw_dw.dta — muestra Dehejia-Wahba (445 obs, 185 tratados).
    Dataset principal: tiene re74 y proviene del RCT NSW.
    """
    return _cargar_dta(RAW_DIR / "nsw_dw.dta")


def cargar_obs_cps1() -> pd.DataFrame:
    """
    Combina tratados de nsw_dw.dta con controles de cps_controls.dta.
    Produce el dataset observacional CPS1 (16 177 obs).
    """
    exp = cargar_experimental()
    tratados = exp[exp["treat"] == 1].copy()
    cps = _cargar_dta(RAW_DIR / "cps_controls.dta")
    cps["treat"] = 0
    return pd.concat([tratados, cps], ignore_index=True)


def cargar_obs_psid1() -> pd.DataFrame:
    """
    Combina tratados de nsw_dw.dta con controles de psid_controls.dta.
    Produce el dataset observacional PSID1 (2 675 obs).
    """
    exp = cargar_experimental()
    tratados = exp[exp["treat"] == 1].copy()
    psid = _cargar_dta(RAW_DIR / "psid_controls.dta")
    psid["treat"] = 0
    return pd.concat([tratados, psid], ignore_index=True)


def guardar_procesados() -> dict[str, pd.DataFrame]:
    """
    Genera y guarda en data/processed/ los tres datasets de análisis.
    Retorna dict con las tres versiones.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    datasets = {
        "experimental": cargar_experimental(),
        "obs_cps1": cargar_obs_cps1(),
        "obs_psid1": cargar_obs_psid1(),
    }
    for nombre, df in datasets.items():
        df.to_parquet(PROCESSED_DIR / f"{nombre}.parquet", index=False)
    return datasets


def smd(df: pd.DataFrame, covariables: list[str] = COVARIABLES) -> pd.DataFrame:
    """
    Calcula la Diferencia Estandarizada de Medias (SMD) entre grupos.

    SMD = (μ₁ - μ₀) / sqrt((σ₁² + σ₀²) / 2)

    Un |SMD| < 0.10 indica balance adecuado (Austin 2009).

    Returns
    -------
    pd.DataFrame con columnas: covariable, mean_treat, mean_control, SMD
    """
    trat = df[df["treat"] == 1]
    ctrl = df[df["treat"] == 0]
    filas = []
    for col in covariables:
        mu1, mu0 = trat[col].mean(), ctrl[col].mean()
        s1, s0 = trat[col].std(), ctrl[col].std()
        denom = np.sqrt((s1**2 + s0**2) / 2)
        smd_val = (mu1 - mu0) / denom if denom > 0 else np.nan
        filas.append(
            {
                "covariable": col,
                "mean_treat": round(mu1, 3),
                "mean_control": round(mu0, 3),
                "SMD": round(smd_val, 3),
            }
        )
    return pd.DataFrame(filas).set_index("covariable")


def tabla_descriptiva(df: pd.DataFrame, covariables: list[str] = COVARIABLES) -> pd.DataFrame:
    """
    Tabla descriptiva con media y desviación estándar por grupo de tratamiento.
    """
    rows = []
    for col in covariables:
        for t, label in [(1, "Tratados"), (0, "Controles")]:
            sub = df[df["treat"] == t][col]
            rows.append(
                {
                    "covariable": col,
                    "grupo": label,
                    "media": round(sub.mean(), 3),
                    "sd": round(sub.std(), 3),
                    "n": len(sub),
                }
            )
    return pd.DataFrame(rows)
