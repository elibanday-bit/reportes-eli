"""Calcula cumplimiento, nivel, gasto y estado por asesor desde la base y genera la página web.
Uso: python scripts/build_web.py [ruta_base.xlsx]
Salida: output/estatus-comisiones-s37-s40.html y output/asesores.json
No necesita Excel ni LibreOffice: replica en pandas la lógica del modelo Excel."""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "ANALISIS_ESTADO-PROYECCION.xlsx"
WEEKS = [37, 38, 39, 40]
PESO_PM, PESO_CM, UMBRAL_CERCA = 0.7, 0.3, 0.7

df = pd.read_excel(BASE, sheet_name="base").dropna(subset=["Código PS"]).reset_index(drop=True)
tab = pd.read_excel(BASE, sheet_name="tablas", header=1, usecols="B:D").dropna()
LEVELS = sorted([(float(r.Cumplimiento), r.Niveles, float(r.Acelerador)) for r in tab.itertuples()], reverse=True)

wk = lambda p: df[[f"{p} S{w}" for w in WEEKS]].fillna(0)
vac = df[[f"Vac S{w}" for w in WEEKS]].fillna(0).to_numpy()
mb = wk("MOD B").to_numpy()

# PM = UG + WA + CAD + RN (cerrado a S40)
venta_pm = wk("UG").sum(axis=1) + wk("WA").sum(axis=1) + wk("CAD").sum(axis=1) + df["RN"].fillna(0)
# CM = MOD B: S37-S38 completos; S39-S40 proyectados con ritmo por semana activa x disponibilidad
den = vac[:, 0] + vac[:, 1]
ritmo = np.divide(mb[:, 0] + mb[:, 1], den, out=np.zeros_like(den, dtype=float), where=den != 0)
cm_proy = mb[:, 0] + mb[:, 1] + np.maximum(mb[:, 2], ritmo * vac[:, 2]) + np.maximum(mb[:, 3], ritmo * vac[:, 3])
cm_real = mb.sum(axis=1)

meta_pm = df["META PM TOTAL"].fillna(0)
meta_cm = df["META CM"].fillna(0)
safe = lambda a, b: np.divide(a, b, out=np.zeros(len(b)), where=np.asarray(b) != 0)
p_pm = safe(venta_pm.to_numpy(dtype=float), meta_pm.to_numpy(dtype=float))
p_cm_real = safe(cm_real.astype(float), meta_cm.to_numpy(dtype=float))
p_cm_proy = safe(cm_proy.astype(float), meta_cm.to_numpy(dtype=float))
c_hoy = PESO_PM * p_pm + PESO_CM * p_cm_real
c_proy = PESO_PM * p_pm + PESO_CM * p_cm_proy

def nivel(c):
    for th, n, a in LEVELS:
        if c >= th - 1e-9:
            return n, a
    return "No activa", 0.0

carta = df["CARTA"].fillna(0).to_numpy(dtype=float)
rows = []
for i, r in df.iterrows():
    n, a = nivel(c_proy[i])
    est = "Activa" if c_proy[i] >= LEVELS[-1][0] - 1e-9 else ("Cerca" if c_proy[i] >= UMBRAL_CERCA - 1e-9 else "No activa")
    rows.append([r["Código PS"], r["POOL"], str(r["LIDER GRUPO"]).title(), float(r["HC"] or 0) if pd.notna(r["HC"]) else 0.0,
                 int(venta_pm[i]), int(meta_pm[i]), float(p_pm[i]), float(p_cm_proy[i]), float(c_hoy[i]), float(c_proy[i]),
                 n, round(a * carta[i], 1), est, round(carta[i], 1)])

(ROOT / "output").mkdir(exist_ok=True)
data = json.dumps(rows, ensure_ascii=False)
(ROOT / "output" / "asesores.json").write_text(data, encoding="utf-8")
html = (ROOT / "web" / "template.html").read_text(encoding="utf-8").replace("__DATA__", data)
(ROOT / "output" / "estatus-comisiones-s37-s40.html").write_text(html, encoding="utf-8")

act = sum(r[12] == "Activa" for r in rows)
print(f"Asesores: {len(rows)} | Activan: {act} | Gasto proyectado: S/ {sum(r[11] for r in rows):,.0f}")
