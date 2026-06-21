"""Tests para el módulo dag.py — usan solo datos sintéticos."""
import pytest
from pgmpy.base import DAG

from lalonde_nsw.dag import (
    CONJUNTO_AJUSTE,
    COVARIABLES,
    RESULTADO,
    TRATAMIENTO,
    construir_dag_nsw,
    obtener_conjunto_ajuste,
)


def test_dag_construye_sin_errores():
    dag = construir_dag_nsw()
    assert isinstance(dag, DAG)


def test_dag_tiene_arista_causal():
    dag = construir_dag_nsw()
    assert (TRATAMIENTO, RESULTADO) in dag.edges()


def test_dag_sin_ciclos():
    import networkx as nx
    dag = construir_dag_nsw()
    assert nx.is_directed_acyclic_graph(dag)


def test_dag_contiene_todos_los_nodos():
    dag = construir_dag_nsw()
    nodos = set(dag.nodes())
    esperados = set(COVARIABLES) | {"re74", "re75", TRATAMIENTO, RESULTADO}
    assert esperados <= nodos


def test_conjunto_ajuste_cubre_covariables():
    ajuste = obtener_conjunto_ajuste()
    for cov in COVARIABLES:
        assert cov in ajuste
    assert "re74" in ajuste
    assert "re75" in ajuste


def test_conjunto_ajuste_no_incluye_tratamiento_ni_resultado():
    ajuste = obtener_conjunto_ajuste()
    assert TRATAMIENTO not in ajuste
    assert RESULTADO not in ajuste
