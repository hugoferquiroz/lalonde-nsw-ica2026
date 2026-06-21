"""Construcción y validación del DAG causal NSW con pgmpy."""
from pgmpy.base import DAG

COVARIABLES = ["age", "educ", "black", "hisp", "married", "nodegree"]
PROXIES_U = ["re74", "re75"]
TRATAMIENTO = "treat"
RESULTADO = "re78"
CONJUNTO_AJUSTE = COVARIABLES + PROXIES_U


def construir_dag_nsw() -> DAG:
    """
    Construye el DAG observado del estudio LaLonde/NSW.

    Aristas justificadas por:
    - LaLonde (1986): criterios de elegibilidad NSW
    - Dehejia & Wahba (1999): covariables de balance
    - Teoría económica del capital humano

    La variable latente U (habilidad no observada) no es modelable directamente;
    re74 y re75 actúan como proxies parciales. Su efecto se analiza en E3.

    Returns
    -------
    DAG sin ciclos con el DAG del modelo causal NSW.
    """
    aristas = []
    for c in COVARIABLES:
        aristas.append((c, TRATAMIENTO))
        aristas.append((c, RESULTADO))
    for p in PROXIES_U:
        aristas.append((p, TRATAMIENTO))
        aristas.append((p, RESULTADO))
    aristas.append((TRATAMIENTO, RESULTADO))

    dag = DAG(aristas)
    # DAG base de pgmpy lanza error en __init__ si hay ciclos; validación adicional:
    import networkx as nx
    assert nx.is_directed_acyclic_graph(dag), "DAG inválido: contiene ciclos"
    return dag


def obtener_conjunto_ajuste() -> list[str]:
    """Devuelve el conjunto de ajuste mínimo que satisface el criterio backdoor."""
    return CONJUNTO_AJUSTE.copy()


def verificar_criterio_backdoor(dag: DAG) -> bool:
    """
    Verifica que CONJUNTO_AJUSTE bloquea todos los caminos backdoor de treat → re78.

    Usa d-separación condicional al conjunto de ajuste. Devuelve True si la
    identificabilidad del ATT está garantizada bajo CIA en el DAG observado.
    """
    from pgmpy.inference import CausalInference

    ci = CausalInference(dag)
    # active_trail_nodes vacío para (treat, re78) dado CONJUNTO_AJUSTE
    # indica d-separación (backdoor bloqueado)
    active = dag.active_trail_nodes(
        {TRATAMIENTO}, observed=CONJUNTO_AJUSTE
    )
    # si re78 no está en el trail activo de treat dado el ajuste, están d-separados
    return RESULTADO not in active.get(TRATAMIENTO, set())
