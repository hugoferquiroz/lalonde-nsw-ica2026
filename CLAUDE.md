# Contexto del proyecto – LaLonde NSW ICA 2026

## Identificación del proyecto

- **Curso:** Inferencia Causal Aplicada con Python – Maestría en Ingeniería Estadística, UNI
- **Docente:** Dr. Jaime Lincovil Curivil (jlincovilc@uni.edu.pe)
- **Estudiante:** Hugo Marlon Fernandez Quiroz (hugo.fernandez.q@uni.pe)
- **Propuesta:** Categoría 3, N.º 4 – Datasets Benchmark: LaLonde / NSW
- **Semestre:** 2026-I

## Pregunta causal y estimando

**Pregunta principal:** ¿Pueden los métodos observacionales modernos (AIPW, DML, Control Sintético) replicar el efecto causal del programa de capacitación laboral NSW sobre los ingresos reales de 1978, estimado mediante un RCT?

**Estimando primario:** ATT (Average Treatment Effect on the Treated)

```
ATT = E[Y(1) - Y(0) | T = 1]
```

- `T` = participación en NSW (1 = tratado, 0 = control)
- `Y` = `re78` (ingresos reales 1978, USD nominales)
- **Benchmark RCT:** ATT_LaLonde = $1,794 (SE ≈ $632) — LaLonde (1986)
- **Nivel GCE:** Nivel 1 (intervención) y Nivel 3 (contrafactual)

## Estado actual del proyecto

| Etapa | Estado | Fecha límite | Peso |
|-------|--------|-------------|------|
| E1 – Planificación | ✅ Completada | 15 mayo 2026 | 20% |
| E2 – Ejecución Primaria | 🔄 En curso | 26 junio 2026 | 30% |
| E3 – Finalización | ⏳ Pendiente | 24 julio 2026 | 50% |

**Tarea inmediata (E2):** implementar estimación inicial con datos reales (PSM + AIPW),
validar supuestos de overlap e ignorabilidad, producir primer análisis de sensibilidad.

## Estructura de módulos

| Archivo | Responsabilidad |
|---------|----------------|
| `src/lalonde_nsw/dag.py` | Construcción del DAG con pgmpy, validación de d-separación |
| `src/lalonde_nsw/data.py` | Carga de CSV crudos, limpieza, SMD de balance |
| `src/lalonde_nsw/estimators.py` | PSM, AIPW, DML (EconML), Synthetic Control |
| `src/lalonde_nsw/sensitivity.py` | Placebo temporal, E-value, Rosenbaum Γ |
| `src/lalonde_nsw/visualization.py` | Love plots, histogramas de overlap, forest plots |

## Datos

Fuente: https://users.nber.org/~rdehejia/nswdata.html  
Licencia: CC BY-NC. Citar: LaLonde (1986), Dehejia & Wahba (1999, 2002).  
Formato preferido: `.dta` (Stata), leer con `pyreadstat.read_dta()`.

`data/raw/` → **NO versionar** (en .gitignore). Archivos disponibles:

### Archivos experimentales (NSW)

| Archivo | N | treat=1 | treat=0 | Tiene re74 | Descripción |
|---------|---|---------|---------|------------|-------------|
| `nsw.dta` | 722 | 297 | 425 | ❌ | Muestra LaLonde completa. Sin re74. |
| `nsw_dw.dta` | 445 | 185 | 260 | ✅ | **Muestra Dehejia-Wahba. Dataset principal del proyecto.** |

### Grupos de control observacionales (solo controles, treat=0)

| Archivo | N controles | Tiene re74 | Descripción |
|---------|-------------|------------|-------------|
| `cps_controls.dta` | 15,992 | ✅ | **CPS1 — grupo control principal observacional** |
| `cps_controls2.dta` | 2,369 | ✅ | CPS2 — subconjunto filtrado de CPS1 |
| `cps_controls3.dta` | 429 | ✅ | CPS3 — subconjunto más restringido de CPS1 |
| `psid_controls.dta` | 2,490 | ✅ | **PSID1 — grupo control observacional secundario** |
| `psid_controls2.dta` | 253 | ✅ | PSID2 — subconjunto filtrado de PSID1 |
| `psid_controls3.dta` | 128 | ✅ | PSID3 — subconjunto más restringido de PSID1 |

### Datasets de análisis que construir en `data/processed/`

```
nsw_dw.dta  (185 tratados + 260 controles experimentales)  → benchmark RCT
nsw_dw.dta[treat==1] + cps_controls.dta                   → obs_cps1  (16,177 obs)
nsw_dw.dta[treat==1] + psid_controls.dta                  → obs_psid1 (2,675 obs)
```

### Columnas en los archivos .dta

| Columna en .dta | Nombre interno del proyecto | Tipo | Descripción |
|----------------|-----------------------------|------|-------------|
| `data_id` | — (descartar) | str | Identificador de fuente |
| `treat` | `treat` | int (0/1) | Participación en NSW |
| `age` | `age` | int | Edad en años |
| `education` | `educ` | int | Años de escolaridad (**renombrar al cargar**) |
| `black` | `black` | int (0/1) | Raza afroamericana |
| `hispanic` | `hisp` | int (0/1) | Etnia hispana (**renombrar al cargar**) |
| `married` | `married` | int (0/1) | Estado civil casado |
| `nodegree` | `nodegree` | int (0/1) | Sin diploma de secundaria |
| `re74` | `re74` | float | Ingresos reales 1974 (USD). Ausente en `nsw.dta`. |
| `re75` | `re75` | float | Ingresos reales 1975 (USD) |
| `re78` | `re78` | float | **Variable de resultado**: ingresos reales 1978 (USD) |

**Renombres obligatorios al cargar cualquier .dta:**
```python
df = df.rename(columns={"education": "educ", "hispanic": "hisp"})
df = df.drop(columns=["data_id"], errors="ignore")
```

### Notas críticas sobre los datos

- `nsw.dta` **no tiene `re74`** (muestra LaLonde original). Usar `nsw_dw.dta` como dataset principal.
- En PSID3 la media de Hispanic está mal en la Tabla 1 de Dehejia & Wahba (1999): debe ser 0.12, no 0.18.
- CPS2 y CPS3 son subconjuntos aproximados; Dehejia & Wahba no pudieron replicar exactamente los filtros de LaLonde.
- `data/processed/` → generado por scripts; puede versionarse.
- `data/synthetic/dgp_nsw.py` → DGP sintético con ATT_verdadero=1794; usado en tests.

## Convenciones de código

- Python ≥ 3.10, type hints en **todas** las funciones públicas
- Funciones puras en `src/`; efectos secundarios (I/O, plots) **solo** en notebooks
- `RANDOM_STATE = 42` en todo el código; documentar con comentario inline
- Variable de tratamiento: `treat` (1 = NSW, 0 = control)
- Variable de resultado: `re78` (ingresos reales 1978, USD nominales de 1978)
- Covariables base: `age`, `educ`, `black`, `hisp`, `married`, `nodegree`, `re74`, `re75`
- Efectos reportados siempre con IC al 95%
- Todas las funciones devuelven `dict` con claves: `ATT`, `SE`, `CI_lower`, `CI_upper`

## Estimadores del pipeline (en orden de implementación)

1. **PSM** – Propensity Score Matching (`sklearn` LogisticRegression + NearestNeighbors 1:1)
2. **AIPW** – Augmented IPW doblemente robusto (`econml.dr.LinearDRLearner`)
3. **DML** – Double/Debiased ML con cross-fitting (`econml.dml.LinearDML`, 5 folds)
4. **SynC** – Synthetic Control (`pysyncon` o implementación propia)
5. **DiD** – Diferencias en Diferencias (descomposición Goodman-Bacon)

## Flujo de notebooks

```
E1/01_dag_validacion
        ↓
E2/02_datos_eda_balance → E2/03_estimacion_psm_aipw
                        → E2/04_estimacion_dml_sync
                                ↓
                        E3/05_sensibilidad_robustez
                                ↓
                        E3/06_resultados_finales
```

## Rúbrica de evaluación (escala 0–20)

El proyecto se evalúa sobre 8 dimensiones. Al escribir código o análisis, tener en cuenta
el descriptor de desempeño máximo de cada dimensión:

| Dimensión | Criterio | Qué se espera al máximo |
|-----------|----------|------------------------|
| **Formulación causal** | Claridad de pregunta y nivel GCE | Pregunta ubicada en Nivel GCE 1/3; estimando ATT formalmente definido |
| **Especificación DAG** | Rigor en supuestos y aristas | DAG con todas las variables; aristas justificadas; d-separación validada con pgmpy |
| **Identificación** | Criterio backdoor aplicado | Identificabilidad algebraica del ATT demostrada; conjunto de ajuste mínimo definido |
| **Implementación** | Calidad del código y librerías | Notebook modular y reproducible; DoWhy/EconML; cross-fitting; semillas documentadas |
| **Validación y sensibilidad** | Exhaustividad en robustez | ≥ 3 pruebas: placebo temporal, E-value o Rosenbaum Γ, estrés distribucional |
| **Interpretación** | Comunicación de resultados | IC al 95%; distinción significancia estadística vs. relevancia práctica |
| **Originalidad y contexto** | Pertinencia para Sur Global | Implicancias de política para Latinoamérica/Perú |
| **Transparencia y ética** | Documentación de supuestos y IA | Fuentes de datos, sesgos potenciales, uso de IA declarado |

### Pruebas de sensibilidad requeridas (mínimo 3 en E3)

1. **Placebo temporal:** estimar efecto sobre `re74` o `re75` como outcome (debe ser ~0)
2. **E-value** (VanderWeele & Ding, 2017): cuán grande debe ser U para anular el efecto
3. **Rosenbaum Γ:** umbral de sesgo oculto que invalida la inferencia
4. *(Opcional)* Estrés distribucional: trim de overlap al 10/90 percentil del PS

## Entregables del curso

| Entregable | Archivo | Estado |
|------------|---------|--------|
| E1 – Planificación | `reports/E1_LaLonde_NSW_Planificacion.docx` | ✅ Entregado |
| E2 – Reporte intermedio | `reports/E2_reporte_intermedio.pdf` | 🔄 En curso |
| E3 – Informe final | `reports/E3_informe_final/main.tex` | ⏳ Pendiente |

## Comandos útiles

```bash
# Instalar en modo editable con dependencias de desarrollo
pip install -e ".[dev]"

# Correr tests (solo usan DGP sintético, nunca datos crudos)
pytest tests/ -v

# Limpiar outputs de notebooks antes de commitear
jupyter nbconvert --clear-output --inplace notebooks/**/*.ipynb

# Verificar balance después de matching
python -c "from lalonde_nsw.data import estadisticas_balance; print('OK')"
```

## Tests

Correr con `pytest tests/` desde la raíz del proyecto.
Los tests usan **únicamente** `data/synthetic/dgp_nsw.py`, nunca datos crudos.
Cada estimador debe pasar: `|ATT_estimado - ATT_verdadero| < 500` sobre el DGP sintético.

## Referencias clave

- LaLonde, R.J. (1986). *AER* 76(4): 604-620 — paper original y benchmark
- Dehejia, R.H. & Wahba, S. (1999). *JASA* 94(448): 1053-1062 — PSM en NSW
- Chernozhukov et al. (2018). *Econometrics Journal* — DML con cross-fitting
- VanderWeele & Ding (2017). *Annals of Internal Medicine* — E-value
- Pearl (2009). *Causality* Cap. 3 — criterio backdoor
- Bareinboim et al. (2022). *PNAS* — Jerarquía GCE
