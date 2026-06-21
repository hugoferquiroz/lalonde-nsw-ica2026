"""Extrae todos los resultados numéricos para el reporte E2."""
import warnings; warnings.filterwarnings('ignore')
import os; os.chdir('D:/lalonde-nsw-ica2026')
import pandas as pd, numpy as np
from lalonde_nsw.estimators import estimar_psm, estimar_aipw, estimar_dml
from lalonde_nsw.sensitivity import placebo_temporal, evalor_desde_att, analisis_rosenbaum_gamma
from lalonde_nsw.data import smd, COVARIABLES

df_exp   = pd.read_parquet('data/processed/experimental.parquet')
df_cps1  = pd.read_parquet('data/processed/obs_cps1.parquet')
df_psid1 = pd.read_parquet('data/processed/obs_psid1.parquet')

print("=== DESCRIPTIVAS ===")
for n, df in [('experimental', df_exp), ('cps1', df_cps1), ('psid1', df_psid1)]:
    t = (df.treat==1).sum(); c = (df.treat==0).sum()
    diff = df[df.treat==1].re78.mean() - df[df.treat==0].re78.mean()
    print(f"{n}: N={len(df)}, T={t}, C={c}, diff_naive={diff:.0f}")

print("\n=== SMD MAX ===")
for n, df in [('experimental', df_exp), ('cps1', df_cps1), ('psid1', df_psid1)]:
    s = smd(df)
    worst = s['SMD'].abs().idxmax()
    print(f"{n}: max_SMD={s['SMD'].abs().max():.3f} en {worst}")

print("\n=== ESTIMADORES ===")
rs = 42
psm_cps1   = estimar_psm(df_cps1,  random_state=rs)
psm_psid1  = estimar_psm(df_psid1, random_state=rs)
aipw_cps1  = estimar_aipw(df_cps1,  n_splits=5, random_state=rs)
aipw_psid1 = estimar_aipw(df_psid1, n_splits=5, random_state=rs)
dml_cps1   = estimar_dml(df_cps1,  n_splits=5, random_state=rs)
dml_psid1  = estimar_dml(df_psid1, n_splits=5, random_state=rs)

resultados = {
    'PSM-CPS1':   psm_cps1,
    'PSM-PSID1':  psm_psid1,
    'AIPW-CPS1':  aipw_cps1,
    'AIPW-PSID1': aipw_psid1,
    'DML-CPS1':   dml_cps1,
    'DML-PSID1':  dml_psid1,
}
for n, r in resultados.items():
    en_ic = "SI" if 555 <= r['ATT'] <= 3033 else "NO"
    print(f"{n}: ATT={r['ATT']:.0f} SE={r['SE']:.0f} CI=[{r['CI_lower']:.0f},{r['CI_upper']:.0f}] en_IC_RCT={en_ic}")

print("\n=== PLACEBO re74 ===")
covs_p = ['age','educ','black','hisp','married','nodegree','re75']
placebos = {}
for n, df, m in [('PSM-CPS1', df_cps1,'psm'),('PSM-PSID1',df_psid1,'psm'),
                  ('AIPW-CPS1',df_cps1,'aipw'),('AIPW-PSID1',df_psid1,'aipw')]:
    r = placebo_temporal(df, 're74', covariables=covs_p, metodo=m, random_state=rs)
    placebos[n] = r
    print(f"Placebo {n}: ATT={r['ATT_placebo']:.0f} p={r['p_valor']:.4f} sig={r['rechaza_H0']}")

print("\n=== E-VALUE ===")
media_c_psid1 = df_psid1[df_psid1.treat==0].re78.mean()
media_c_cps1  = df_cps1[df_cps1.treat==0].re78.mean()
print(f"Media re78 controles PSID1: {media_c_psid1:.0f}")
print(f"Media re78 controles CPS1:  {media_c_cps1:.0f}")
ev_psid1 = evalor_desde_att(aipw_psid1['ATT'], media_c_psid1, CI_lower=aipw_psid1['CI_lower'])
ev_cps1  = evalor_desde_att(aipw_cps1['ATT'],  media_c_cps1,  CI_lower=aipw_cps1['CI_lower'])
print(f"E-valor AIPW-PSID1: {ev_psid1['evalor']} (IC inferior: {ev_psid1.get('evalor_CI_lower','N/A')})")
print(f"E-valor AIPW-CPS1:  {ev_cps1['evalor']}  (IC inferior: {ev_cps1.get('evalor_CI_lower','N/A')})")

print("\n=== ROSENBAUM GAMMA (AIPW-PSID1) ===")
tab = analisis_rosenbaum_gamma(aipw_psid1['ATT'], aipw_psid1['SE'])
print(tab.to_string())
umbral = tab[tab['significativo (p<0.05)']].index.max()
print(f"Gamma critico: {umbral}")

print("\n=== SMD EXPERIMENTAL (tabla completa) ===")
print(smd(df_exp).to_string())
print("\n=== SMD CPS1 (tabla completa) ===")
print(smd(df_cps1).to_string())
print("\n=== SMD PSID1 (tabla completa) ===")
print(smd(df_psid1).to_string())
