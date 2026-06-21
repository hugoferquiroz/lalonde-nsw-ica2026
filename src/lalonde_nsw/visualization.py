"""Visualizaciones para el proyecto LaLonde/NSW.

Todas las funciones devuelven (fig, ax) para integración en notebooks.
Efectos secundarios (plt.show, guardar archivos) quedan en el notebook.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns

BENCHMARK_ATT = 1794.0
BENCHMARK_SE = 632.0

_PALETTE = {"Tratados": "#2196F3", "Controles": "#FF5722"}


def love_plot(
    smd_antes: pd.DataFrame,
    smd_despues: pd.DataFrame | None = None,
    umbral: float = 0.1,
    titulo: str = "Love Plot — Balance de Covariables",
) -> tuple[plt.Figure, plt.Axes]:
    """
    Love plot de SMD antes (y opcionalmente después) del matching.

    Parameters
    ----------
    smd_antes : DataFrame con índice covariable y columna SMD.
    smd_despues : opcional, misma estructura tras matching.
    umbral : línea de referencia de balance adecuado.
    """
    fig, ax = plt.subplots(figsize=(9, max(5, len(smd_antes) * 0.5)))

    covs = smd_antes.index.tolist()
    y = np.arange(len(covs))

    ax.scatter(smd_antes["SMD"].abs(), y, color="#E53935", zorder=3,
               label="Antes del matching", s=60, marker="o")
    if smd_despues is not None:
        ax.scatter(smd_despues["SMD"].abs(), y, color="#43A047", zorder=3,
                   label="Después del matching", s=60, marker="D")

    ax.axvline(umbral, color="gray", linestyle="--", linewidth=1,
               label=f"|SMD| = {umbral}")
    ax.axvline(0, color="black", linewidth=0.5)
    ax.set_yticks(y)
    ax.set_yticklabels(covs)
    ax.set_xlabel("|SMD|")
    ax.set_title(titulo)
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    return fig, ax


def overlap_plot(
    df: pd.DataFrame,
    ps_col: str = "ps",
    tratamiento: str = "treat",
    titulo: str = "Overlap — Histograma de Propensity Score",
) -> tuple[plt.Figure, plt.Axes]:
    """
    Histogramas superpuestos del propensity score por grupo.
    Permite evaluar visualmente el soporte común.
    """
    fig, ax = plt.subplots(figsize=(9, 5))

    trat = df[df[tratamiento] == 1][ps_col]
    ctrl = df[df[tratamiento] == 0][ps_col]

    bins = np.linspace(0, 1, 40)
    ax.hist(trat, bins=bins, alpha=0.6, color=_PALETTE["Tratados"],
            label=f"Tratados (n={len(trat):,})", density=True)
    ax.hist(ctrl, bins=bins, alpha=0.6, color=_PALETTE["Controles"],
            label=f"Controles (n={len(ctrl):,})", density=True)

    ax.set_xlabel("Propensity Score estimado")
    ax.set_ylabel("Densidad")
    ax.set_title(titulo)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig, ax


def forest_plot(
    resultados: dict[str, dict],
    titulo: str = "Forest Plot — Estimaciones del ATT",
    benchmark_att: float = BENCHMARK_ATT,
    benchmark_se: float = BENCHMARK_SE,
) -> tuple[plt.Figure, plt.Axes]:
    """
    Forest plot con punto estimado e intervalo de confianza al 95%
    para cada estimador, más la línea de referencia del RCT.

    Parameters
    ----------
    resultados : dict {nombre_estimador: {"ATT": ..., "CI_lower": ..., "CI_upper": ...}}
    """
    nombres = list(resultados.keys())
    atts = [r["ATT"] for r in resultados.values()]
    ci_lo = [r["CI_lower"] for r in resultados.values()]
    ci_hi = [r["CI_upper"] for r in resultados.values()]

    y = np.arange(len(nombres))
    xerr_lo = [a - lo for a, lo in zip(atts, ci_lo)]
    xerr_hi = [hi - a for a, hi in zip(atts, ci_hi)]

    fig, ax = plt.subplots(figsize=(10, max(4, len(nombres) * 0.8 + 2)))

    ax.errorbar(
        atts, y,
        xerr=[xerr_lo, xerr_hi],
        fmt="o", color="#1565C0", ecolor="#1565C0",
        capsize=5, markersize=8, linewidth=1.5, label="Estimadores observacionales",
    )

    # Benchmark RCT
    ax.axvline(benchmark_att, color="#C62828", linestyle="-", linewidth=2,
               label=f"Benchmark RCT: ${benchmark_att:,.0f}")
    benchmark_ci_lo = benchmark_att - 1.96 * benchmark_se
    benchmark_ci_hi = benchmark_att + 1.96 * benchmark_se
    ax.axvspan(benchmark_ci_lo, benchmark_ci_hi, alpha=0.12, color="#C62828",
               label=f"IC 95% RCT: [{benchmark_ci_lo:,.0f}, {benchmark_ci_hi:,.0f}]")

    ax.axvline(0, color="black", linewidth=0.8, linestyle=":")
    ax.set_yticks(y)
    ax.set_yticklabels(nombres)
    ax.set_xlabel("ATT estimado (USD 1978)")
    ax.set_title(titulo)
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    return fig, ax


def distribucion_outcome(
    df: pd.DataFrame,
    outcome: str = "re78",
    tratamiento: str = "treat",
    titulo: str = "Distribución del Outcome por Grupo",
) -> tuple[plt.Figure, plt.Axes]:
    """
    Violin/box plot del outcome por grupo de tratamiento.
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    labels = {0: "Control", 1: "Tratados (NSW)"}
    df_plot = df.copy()
    df_plot["Grupo"] = df_plot[tratamiento].map(labels)

    sns.violinplot(
        data=df_plot, x="Grupo", y=outcome,
        palette={"Control": _PALETTE["Controles"], "Tratados (NSW)": _PALETTE["Tratados"]},
        inner="box", ax=ax,
    )
    ax.set_ylabel(f"{outcome} (USD 1978)")
    ax.set_title(titulo)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig, ax


def tabla_smd_styled(smd_df: pd.DataFrame) -> "pd.io.formats.style.Styler":
    """Aplica estilo de colores a la tabla SMD: verde si |SMD| < 0.1, rojo si no."""
    def colorear(val: float) -> str:
        if abs(val) < 0.1:
            return "background-color: #C8E6C9; color: #1B5E20"
        elif abs(val) < 0.25:
            return "background-color: #FFF9C4; color: #F57F17"
        else:
            return "background-color: #FFCDD2; color: #B71C1C"

    return smd_df.style.map(colorear, subset=["SMD"]).format(precision=3)
