"""Auditoría de exactitud de los datos: cada cifra se verifica por un camino independiente.

Uso (desde la raíz del repositorio, con PostgreSQL cargado):
    python -m src.analysis.auditoria

Verificaciones:
    A. Crudo -> limpio: cada valor del CSV es idéntico al que entregó la API.
    B. Asignación: la regla de mayoría de días, reimplementada con otro método.
    C. Limpio -> base de datos: PostgreSQL contiene exactamente el CSV.
    D. Fuente independiente: las series de Chile contra los datos del FMI.
    E. Recálculo sin SQL: las métricas por gobierno, calculadas en pandas, contra las vistas SQL.
    F. Documentos: cada cifra de hallazgos.md y contexto_comparado.md contra el recálculo.
    G. Dashboard: los valores que muestra Power BI contra el cálculo sin DAX.
    H. Balance de cada gobierno: los ocho criterios, recalculados sin SQL.
    I. Datos fiscales: balance estructural y fondos soberanos contra la DIPRES, el CFA y Hacienda.

Termina con código 1 si alguna verificación falla.
"""
import json
import sys

import pandas as pd
import psycopg
import yaml

from src.config import CONFIG_DIR, PROCESSED_DIR, RAW_DIR, REFERENCE_DIR, get_pg_params

resultados: list[tuple[str, bool, str]] = []


def registrar(nombre: str, ok: bool, detalle: str = "") -> None:
    resultados.append((nombre, ok, detalle))
    print(f"[{'OK ' if ok else 'FALLA'}] {nombre}" + (f"  ({detalle})" if detalle else ""))


def cerca(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol


# -----------------------------------------------------------------------------
# Carga de insumos
# -----------------------------------------------------------------------------
OBS = pd.read_csv(PROCESSED_DIR / "observaciones.csv", parse_dates=["fecha", "fecha_fin_periodo"])
GOB = pd.read_csv(REFERENCE_DIR / "gobiernos.csv", parse_dates=["fecha_inicio", "fecha_fin"])
INT = pd.read_csv(PROCESSED_DIR / "internacional.csv")
CONFIG = yaml.safe_load((CONFIG_DIR / "series.yaml").read_text(encoding="utf-8"))["bcch"]
ETQ = dict(zip(GOB["id_gobierno"], GOB["etiqueta"]))
EN_ALCANCE = GOB.loc[GOB["en_alcance"], "id_gobierno"].tolist()


def serie(ind: str) -> pd.DataFrame:
    return OBS[OBS["indicador"] == ind].sort_values("fecha").reset_index(drop=True)


# -----------------------------------------------------------------------------
# A. Crudo -> limpio
# -----------------------------------------------------------------------------
def auditar_crudo() -> None:
    for ind, meta in CONFIG.items():
        ruta = sorted((RAW_DIR / "bcch").glob(f"{ind}_[0-9]*.json"))[-1]  # fecha justo tras el nombre
        crudo = json.loads(ruta.read_text(encoding="utf-8"))
        codigo_ok = crudo["Series"]["seriesId"] == meta["codigo"]
        obs = pd.DataFrame(crudo["Series"]["Obs"])
        obs = obs[obs["statusCode"] == "OK"].copy()
        obs["fecha"] = pd.to_datetime(obs["indexDateString"], format="%d-%m-%Y")
        obs["valor"] = pd.to_numeric(obs["value"], errors="coerce")
        obs = obs.dropna(subset=["valor"])
        limpio = serie(ind)
        unido = obs.merge(limpio, on="fecha", how="outer", suffixes=("_api", "_csv"), indicator=True)
        solo_uno = (unido["_merge"] != "both").sum()
        dif = (unido["valor_api"] - unido["valor_csv"]).abs().max()
        registrar(f"A. {ind}: crudo = limpio", codigo_ok and solo_uno == 0 and dif < 1e-9,
                  f"código {'coincide' if codigo_ok else 'NO coincide'}, {len(limpio)} filas, "
                  f"{solo_uno} sin par, dif. máx. {dif:.1e}")


# -----------------------------------------------------------------------------
# B. Asignación por un método distinto (punto medio, en vez de contar días)
# -----------------------------------------------------------------------------
def gobierno_en(fecha: pd.Timestamp) -> int:
    fila = GOB[(GOB["fecha_inicio"] <= fecha) & (fecha < GOB["fecha_fin"])]
    return int(fila["id_gobierno"].iloc[0])


def auditar_asignacion() -> None:
    medio = OBS["fecha"] + (OBS["fecha_fin_periodo"] - OBS["fecha"]) / 2
    esperado = medio.map(gobierno_en)
    distintos = (esperado != OBS["id_gobierno"]).sum()
    cambios = GOB["fecha_inicio"].tolist()
    transicion = OBS.apply(lambda r: any(r["fecha"] < c < r["fecha_fin_periodo"] for c in cambios), axis=1)
    dist_trans = (transicion != OBS["es_transicion"]).sum()
    registrar("B. Asignación por punto medio = mayoría de días", distintos == 0,
              f"{distintos} diferencias en {len(OBS)} filas")
    registrar("B. Marca de transición recalculada", dist_trans == 0, f"{dist_trans} diferencias")


# -----------------------------------------------------------------------------
# C. Limpio -> base de datos
# -----------------------------------------------------------------------------
def consulta(sql: str) -> pd.DataFrame:
    with psycopg.connect(**get_pg_params()) as c:
        cur = c.execute(sql)
        return pd.DataFrame(cur.fetchall(), columns=[d.name for d in cur.description])


def auditar_base() -> None:
    bd = consulta("SELECT indicador, fecha, valor::float AS valor, id_gobierno, es_transicion "
                  "FROM economia.fact_observacion")
    bd["fecha"] = pd.to_datetime(bd["fecha"])
    u = OBS.merge(bd, on=["indicador", "fecha"], how="outer", suffixes=("_csv", "_bd"), indicator=True)
    sin_par = (u["_merge"] != "both").sum()
    dif = (u["valor_csv"] - u["valor_bd"]).abs().max()
    gob = (u["id_gobierno_csv"] != u["id_gobierno_bd"]).sum()
    registrar("C. PostgreSQL = CSV (valores y gobierno)", sin_par == 0 and dif < 1e-6 and gob == 0,
              f"{len(bd)} filas, {sin_par} sin par, dif. máx. {dif:.1e}, {gob} gobiernos distintos")
    bi = consulta("SELECT indicador, zona, anio, valor::float AS valor FROM economia.fact_internacional")
    u = INT.merge(bi, on=["indicador", "zona", "anio"], how="outer", indicator=True, suffixes=("_csv", "_bd"))
    registrar("C. PostgreSQL = CSV internacional",
              (u["_merge"] != "both").sum() == 0 and (u["valor_csv"] - u["valor_bd"]).abs().max() < 1e-6,
              f"{len(bi)} filas")


# -----------------------------------------------------------------------------
# D. Contraste con una fuente independiente (FMI)
# -----------------------------------------------------------------------------
def anual_bcch() -> pd.DataFrame:
    pib = serie("pib").assign(anio=lambda d: d["fecha"].dt.year).groupby("anio")["valor"].agg(["sum", "count"])
    pib = pib[pib["count"] == 4]["sum"]
    out = pd.DataFrame({"crecimiento_pib": (pib / pib.shift(1) - 1) * 100})
    for ind, nombre in [("ipc", "inflacion_promedio"), ("desempleo", "desempleo")]:
        s = serie(ind).assign(anio=lambda d: d["fecha"].dt.year).groupby("anio")["valor"].agg(["mean", "count"])
        out[nombre] = s.loc[s["count"] == 12, "mean"]
    return out


# Cifras oficiales del INE (variación 12 meses), tal como se publicaron, para contrastar la serie.
IPC_PUBLICADO = {
    "2008-10": 9.9, "2008-12": 7.1, "2009-12": -1.4, "2010-12": 3.0, "2013-12": 3.0,
    "2014-10": 5.7, "2014-12": 4.6, "2018-12": 2.6, "2022-08": 14.1, "2022-12": 12.8, "2023-12": 3.9,
    "2024-02": 4.5, "2024-03": 3.7, "2024-12": 4.5,
}


def auditar_ipc_publicado() -> None:
    s = serie("ipc").set_index("fecha")["valor"]
    malos = {m: (v, float(s[m].iloc[0])) for m, v in IPC_PUBLICADO.items() if not cerca(float(s[m].iloc[0]), v, 0.05)}
    registrar(f"D. IPC: {len(IPC_PUBLICADO)} meses contra lo publicado por el INE", not malos,
              "todos coinciden" if not malos else str(malos))


def auditar_fmi() -> None:
    bcch = anual_bcch()
    fmi = INT[(INT["zona"] == "CHL") & ~INT["es_proyeccion"]].pivot(index="anio", columns="indicador", values="valor")
    # Diferencias ya investigadas, con la cifra oficial chilena que las resuelve.
    excepciones = {("desempleo", 2009): (9.7, "el FMI informa 11,1; el INE publicó un promedio de 9,7 "
                                              "(Diario Financiero, enero de 2010)"),
                   }
    # Años de cambio de base del IPC (2009, 2014, 2019 y 2024): el FMI calcula el promedio anual
    # con el índice de la canasta nueva y el proyecto promedia las variaciones oficiales mensuales
    # que publicó el INE. Esos años se verifican mes a mes contra el INE (IPC_PUBLICADO).
    cambio_base = {("inflacion_promedio", y): None for y in (2009, 2014, 2019, 2024)}
    tolerancias = {"crecimiento_pib": 0.3, "inflacion_promedio": 0.3, "desempleo": 0.5}
    for (ind, anio), (oficial, nota) in excepciones.items():
        registrar(f"D. {ind} {anio}: contra la cifra oficial chilena", cerca(bcch.loc[anio, ind], oficial, 0.1),
                  f"proyecto {bcch.loc[anio, ind]:.2f}, oficial {oficial}; {nota}")
    for ind, tol in tolerancias.items():
        a = pd.concat([bcch[ind], fmi[ind]], axis=1, keys=["bcch", "fmi"]).loc[2006:2025].dropna()
        a = a.drop(index=[y for (i_, y) in {**excepciones, **cambio_base} if i_ == ind], errors="ignore")
        d = (a["bcch"] - a["fmi"]).abs()
        registrar(f"D. {ind}: Banco Central vs FMI, 2006-2025", (d <= tol).all(),
                  f"{len(a)} años, dif. máx. {d.max():.2f} pp en {d.idxmax()} (tolerancia {tol})")


# -----------------------------------------------------------------------------
# E. Métricas por gobierno recalculadas en pandas (sin SQL)
# -----------------------------------------------------------------------------
def var12(ind: str) -> pd.DataFrame:
    s = serie(ind)[["fecha", "valor", "id_gobierno", "es_transicion"]]
    prev = s[["fecha", "valor"]].assign(fecha=lambda d: d["fecha"] + pd.DateOffset(years=1))
    m = s.merge(prev, on="fecha", suffixes=("", "_ant"))
    m["var"] = (m["valor"] / m["valor_ant"] - 1) * 100
    return m


def resumen_pandas() -> pd.DataFrame:
    filas = []
    for ind in CONFIG:
        s = serie(ind)
        v = var12(ind) if ind in ("pib", "imacec", "cobre", "remuneraciones_reales_hist", "remuneraciones_reales") else None
        for g in EN_ALCANCE:
            sg = s[s["id_gobierno"] == g]
            if sg.empty:  # tramos de series que no cubren todo el período (índice de salarios)
                continue
            anterior = s[s["id_gobierno"] == g - 1]
            filas.append({
                "id_gobierno": g, "indicador": ind,
                "promedio": sg["valor"].mean(), "minimo": sg["valor"].min(), "maximo": sg["valor"].max(),
                "valor_final": sg["valor"].iloc[-1],
                # Sin datos del gobierno anterior (fondos soberanos antes de 2007): sin heredado.
                "valor_heredado": anterior["valor"].iloc[-1] if len(anterior) else None,
                "var_12m_promedio": v.loc[v["id_gobierno"] == g, "var"].mean() if v is not None else None,
            })
    return pd.DataFrame(filas)


def auditar_resumen(pd_res: pd.DataFrame) -> None:
    sql = consulta("SELECT id_gobierno, indicador, promedio::float, minimo::float, maximo::float, "
                   "valor_final::float, valor_heredado::float, var_12m_promedio::float "
                   "FROM economia.v_resumen_gobierno")
    u = pd_res.merge(sql, on=["id_gobierno", "indicador"], suffixes=("_pd", "_sql"))
    peor = 0.0
    for c in ["promedio", "minimo", "maximo", "valor_final", "valor_heredado", "var_12m_promedio"]:
        d = (u[f"{c}_pd"].astype(float) - u[f"{c}_sql"].astype(float)).abs().max(skipna=True)
        peor = max(peor, d if pd.notna(d) else 0)
    # La base guarda 6 decimales (NUMERIC(14,6)): diferencias menores a 1e-5 son de almacenamiento.
    registrar("E. Métricas por gobierno: pandas = vista SQL", len(u) == len(pd_res) == len(sql) and peor < 1e-5,
              f"{len(u)} combinaciones gobierno-indicador, dif. máx. {peor:.1e}")


def desfase_pandas(meses: int) -> pd.Series:
    v = var12("imacec")
    s = serie("imacec").set_index("fecha")
    medio = s.loc[v["fecha"], "fecha_fin_periodo"].values
    medio = v["fecha"] + (pd.to_datetime(medio) - v["fecha"]) / 2 - pd.DateOffset(months=meses)
    v = v.assign(gob=medio.map(gobierno_en))
    return v[v["gob"].isin(EN_ALCANCE)].groupby("gob")["var"].mean()


# -----------------------------------------------------------------------------
# F. Cifras publicadas en los documentos
# -----------------------------------------------------------------------------
def auditar_documentos(res: pd.DataFrame) -> None:
    r = res.set_index(["indicador", "id_gobierno"])
    G = {e: i for i, e in ETQ.items()}

    def val(ind, g, col):
        return float(r.loc[(ind, G[g]), col])

    # Tablas de hallazgos.md (valor publicado, valor recalculado, tolerancia de redondeo)
    chequeos = []
    pub = {
        "pib": [3.23, 5.43, 1.90, 2.65, 1.64], "imacec": [3.35, 5.38, 1.85, 2.64, 1.77],
    }
    gobs = ["Bachelet I", "Piñera I", "Bachelet II", "Piñera II", "Boric"]
    for ind, valores in pub.items():
        for g, p in zip(gobs, valores):
            chequeos.append((f"{ind} var. 12m {g}", p, val(ind, g, "var_12m_promedio"), 0.005))
    for g, (prom, mx, tmin, tmax) in zip(gobs, [(4.33, 9.9, 0.50, 8.25), (2.54, 4.4, 0.50, 5.25),
                                                  (3.64, 5.7, 2.50, 4.25), (3.29, 7.8, 0.50, 5.50),
                                                  (6.72, 14.1, 4.50, 11.25)]):
        chequeos += [(f"IPC prom. {g}", prom, val("ipc", g, "promedio"), 0.005),
                     (f"IPC máx. {g}", mx, val("ipc", g, "maximo"), 0.005),
                     (f"TPM mín. {g}", tmin, val("tpm", g, "minimo"), 0.005),
                     (f"TPM máx. {g}", tmax, val("tpm", g, "maximo"), 0.005)]
    for g, (her, fin, mx) in zip(gobs, [(7.80, 8.53, 10.76), (8.53, 6.18, 9.23), (6.18, 7.01, 7.33),
                                         (7.01, 7.50, 13.09), (7.50, 8.33, 9.00)]):
        chequeos += [(f"Desempleo heredado {g}", her, val("desempleo", g, "valor_heredado"), 0.005),
                     (f"Desempleo final {g}", fin, val("desempleo", g, "valor_final"), 0.005),
                     (f"Desempleo máx. {g}", mx, val("desempleo", g, "maximo"), 0.005)]
    for g, (her, fin, bal) in zip(gobs, [(6.4, 6.5, 3.67), (6.5, 12.7, 0.20), (12.7, 23.6, -2.32),
                                          (23.6, 36.2, -4.88), (36.2, 42.4, -1.73)]):
        chequeos += [(f"Deuda heredada {g}", her, val("deuda_bruta", g, "valor_heredado"), 0.05),
                     (f"Deuda final {g}", fin, val("deuda_bruta", g, "valor_final"), 0.05),
                     (f"Balance prom. {g}", bal, val("balance_fiscal", g, "promedio"), 0.005)]
    for g, (cp, cv, dol) in zip(gobs, [(2.98, 22.3, 533), (3.59, 8.8, 495), (2.65, -1.1, 640),
                                        (3.23, 13.9, 734), (4.19, 3.3, 905)]):
        chequeos += [(f"Cobre prom. {g}", cp, val("cobre", g, "promedio"), 0.005),
                     (f"Cobre var. 12m {g}", cv, val("cobre", g, "var_12m_promedio"), 0.05),
                     (f"Dólar prom. {g}", dol, val("tipo_cambio", g, "promedio"), 0.5)]
    # Deuda neta y balance estructural (sección 5)
    for g, (nh, nf, be) in zip(gobs, [(-1.6, -9.8, -0.40), (-9.8, -6.2, -0.99), (-6.2, 5.0, -0.78),
                                       (5.0, 19.7, -4.03), (19.7, 26.1, -2.33)]):
        chequeos += [(f"Deuda neta heredada {g}", nh, val("deuda_neta", g, "valor_heredado"), 0.05),
                     (f"Deuda neta final {g}", nf, val("deuda_neta", g, "valor_final"), 0.05),
                     (f"Balance estructural prom. {g}", be, val("balance_estructural", g, "promedio"), 0.005)]
    # Incertidumbre del crecimiento anual (sección 1): promedio y error estándar por gobierno
    pib_t = serie("pib").assign(anio=lambda d: d["fecha"].dt.year).groupby("anio")["valor"].agg(["sum", "count"])
    pib_t = pib_t.loc[pib_t["count"] == 4, "sum"]
    anual = (pib_t / pib_t.shift(1) - 1) * 100
    for g, (a0, prom, ee) in zip(gobs, [(2006, 3.47, 1.60), (2010, 5.38, 0.70), (2014, 1.76, 0.16),
                                         (2018, 2.46, 3.63), (2022, 2.00, 0.47)]):
        x = anual.loc[a0:a0 + 3]
        chequeos += [(f"PIB anual prom. {g}", prom, x.mean(), 0.005),
                     (f"PIB anual error est. {g}", ee, x.std() / 2, 0.005)]
    # Sensibilidad al desfase (sección 2)
    for meses, valores in [(6, [3.36, 4.83, 2.21, 2.51, 1.29]), (12, [3.53, 4.20, 2.25, 2.11, 1.54])]:
        calc = desfase_pandas(meses)
        for g, p in zip(gobs, valores):
            chequeos.append((f"IMACEC desfase {meses} {g}", p, float(calc[G[g]]), 0.005))
    # Crecimiento por habitante (sección 10) y bienestar (sección 11)
    pc = INT[(INT["zona"] == "CHL") & (INT["indicador"] == "crecimiento_pib_per_capita")].set_index("anio")["valor"]
    for g, (a0, p_pc) in zip(gobs, [(2006, 2.45), (2010, 4.33), (2014, 0.53), (2018, 1.20), (2022, 1.19)]):
        chequeos.append((f"PIB por habitante {g}", p_pc, pc.loc[a0:a0 + 3].mean(), 0.005))
    chequeos += [("PIB por habitante 2006-2013", 3.4, pc.loc[2006:2013].mean(), 0.05),
                 ("PIB por habitante 2014-2025", 1.0, pc.loc[2014:2025].mean(), 0.05)]
    sal = pd.concat([var12("remuneraciones_reales_hist"), var12("remuneraciones_reales")])
    for g, (p_ini, p_fin, p_sal) in zip(gobs, [(29.1, 25.3, 2.4), (25.3, 14.4, 3.2), (14.4, 8.6, 1.8),
                                                (8.6, 10.8, 1.3), (10.8, 4.9, 1.5)]):
        chequeos += [(f"Pobreza recibida {g}", p_ini, pobreza_ini(G[g]), 0.001),
                     (f"Pobreza entregada {g}", p_fin, pobreza_fin(G[g]), 0.001),
                     (f"Salario real {g}", p_sal, sal.loc[sal["id_gobierno"] == G[g], "var"].mean(), 0.05)]
    # Inflación en rango meta (sección 3)
    ipc = serie("ipc")
    en_rango = ipc["valor"].between(2, 4)
    for g, p in zip(gobs, [38, 67, 38, 75, 21]):
        m = ipc["id_gobierno"] == G[g]
        chequeos.append((f"% meses en rango {g}", p, 100 * en_rango[m].mean(), 0.5))
        chequeos.append((f"Inflación − meta {g}", {"Bachelet I": 1.33, "Piñera I": -0.46, "Bachelet II": 0.64,
                                                   "Piñera II": 0.29, "Boric": 3.72}[g],
                         ipc.loc[m, "valor"].mean() - 3, 0.005))
    malos = [(n, p, c) for n, p, c, t in chequeos if not cerca(p, c, t)]
    registrar(f"F. hallazgos.md: {len(chequeos)} cifras de las tablas", not malos,
              "todas coinciden" if not malos else "; ".join(f"{n}: publicado {p}, calculado {c:.3f}" for n, p, c in malos))

    # Afirmaciones de la Síntesis
    pib = var12("pib")
    a = pib.loc[pib["id_gobierno"].isin([2, 3]), "var"].mean()
    b = pib.loc[pib["id_gobierno"].isin([4, 5, 6]), "var"].mean()
    bal = serie("balance_fiscal").assign(anio=lambda d: d["fecha"].dt.year).set_index("anio")["valor"]
    sup_desde_2009 = sorted(bal[(bal.index >= 2009) & (bal > 0)].index.tolist())
    afirm = [
        ("PIB 2006-2014 = 4,3 %", cerca(a, 4.3, 0.05), f"{a:.2f}"),
        ("PIB 2014-2026 = 2,1 %", cerca(b, 2.1, 0.05), f"{b:.2f}"),
        ("Deuda de 6 % a 42 % (heredada por Bachelet I, entregada por Boric)",
         cerca(val("deuda_bruta", "Bachelet I", "valor_heredado"), 6, 0.5)
         and cerca(val("deuda_bruta", "Boric", "valor_final"), 42, 0.5),
         f"{val('deuda_bruta', 'Bachelet I', 'valor_heredado'):.1f} -> {val('deuda_bruta', 'Boric', 'valor_final'):.1f}"),
        ("Superávit desde 2009 solo en 2011, 2012 y 2022", sup_desde_2009 == [2011, 2012, 2022], str(sup_desde_2009)),
        ("Esos superávits bajo 1,3 %", bal.loc[[2011, 2012, 2022]].max() < 1.3, f"máx. {bal.loc[[2011, 2012, 2022]].max():.2f}"),
        ("Superávits 2006-2008", True, ", ".join(f"{y}: {bal[y]:.2f}" for y in (2006, 2007, 2008))),
        ("Inflación en rango en 48 % de los meses",
         cerca(100 * en_rango[ipc["id_gobierno"].isin(EN_ALCANCE)].mean(), 48, 0.5),
         f"{100 * en_rango[ipc['id_gobierno'].isin(EN_ALCANCE)].mean():.1f} %"),
        ("Máximos de inflación en 2008 y 2022",
         ipc.loc[ipc["valor"][ipc["id_gobierno"] == 2].idxmax(), "fecha"].year == 2008
         and ipc.loc[ipc["valor"][ipc["id_gobierno"] == 6].idxmax(), "fecha"].year == 2022,
         f"{ipc.loc[ipc['valor'][ipc['id_gobierno'] == 2].idxmax(), 'fecha']:%m-%Y} y "
         f"{ipc.loc[ipc['valor'][ipc['id_gobierno'] == 6].idxmax(), 'fecha']:%m-%Y}"),
    ]
    for n, ok, det in afirm:
        registrar(f"F. Síntesis: {n}", ok, det)

    # contexto_comparado.md y sección 8 de hallazgos: Chile − pares, recalculado desde el CSV
    i = INT[~INT["es_proyeccion"]].copy()
    i["gob"] = i["anio"].map(lambda y: next(g for g, (a_, b_) in
                                           {2: (2006, 2009), 3: (2010, 2013), 4: (2014, 2017),
                                            5: (2018, 2021), 6: (2022, 2025)}.items() if a_ <= y <= b_)
                            if 2006 <= y <= 2025 else None)
    i = i.dropna(subset=["gob"])
    pares = ["PER", "COL", "MEX", "BRA"]

    def dif(ind, g):
        d = i[(i["indicador"] == ind) & (i["gob"] == g)]
        ch = d[d["zona"] == "CHL"].set_index("anio")["valor"]
        pa = d[d["zona"].isin(pares)].groupby("anio")["valor"].mean()
        return (ch - pa).mean()
    pub_pares = {"crecimiento_pib": [-0.31, 0.63, 0.11, 1.09, -0.61],
                 "inflacion_promedio": [0.13, -1.44, -0.98, -0.63, 0.77],
                 "balance_gobierno_general": [5.01, 2.01, 1.57, -0.01, 3.11]}
    malos = []
    total = 0
    for ind, valores in pub_pares.items():
        for g, p in zip([2, 3, 4, 5, 6], valores):
            total += 1
            c = dif(ind, g)
            if not cerca(p, c, 0.005):
                malos.append(f"{ind} {ETQ[g]}: publicado {p}, calculado {c:.3f}")
    registrar(f"F. Chile − pares: {total} cifras", not malos, "todas coinciden" if not malos else "; ".join(malos))


# Valores leídos en el dashboard de Power BI (capturas del 11-11-2026, desfase 0).
# Se excluyen la TPM y los eventos, cuyo formato cambió después de esas capturas.
DASHBOARD_LEIDO = {
    "ficha": {
        2: {"Crecimiento del PIB (% anual)": "3,23", "Rango trimestral del PIB (%)": "-2,8  a  6,3",
            "Inflación promedio (%)": "4,33", "Meses en el rango meta": "38%",
            "Desempleo (%): inicio → fin": "7,8  →  8,5", "Cambio del desempleo": "+0,7 pp",
            "Deuda bruta % PIB: inicio → fin": "6,4  →  6,5", "Deuda neta % PIB: inicio → fin": "-1,6  →  -9,8",
            "Balance efectivo prom. % PIB": "3,67", "Balance estructural prom. % PIB": "-0,40",
            "Dólar (CLP): inicio → fin": "531  →  513", "Cobre prom. (USD/lb)": "2,98",
            "Crecimiento vs. pares, FMI (pp)": "-0,3 pp", "Inflación vs. pares, FMI (pp)": "+0,1 pp",
            "Balance vs. pares, FMI (pp)": "+5,01"},
        5: {"Crecimiento del PIB (% anual)": "2,65", "Rango trimestral del PIB (%)": "-15,0  a  18,4",
            "Inflación promedio (%)": "3,29", "Meses en el rango meta": "75%",
            "Desempleo (%): inicio → fin": "7,0  →  7,5", "Cambio del desempleo": "+0,5 pp",
            "Deuda bruta % PIB: inicio → fin": "23,6  →  36,2", "Deuda neta % PIB: inicio → fin": "5,0  →  19,7",
            "Balance efectivo prom. % PIB": "-4,88", "Balance estructural prom. % PIB": "-4,03",
            "Dólar (CLP): inicio → fin": "605  →  804", "Cobre prom. (USD/lb)": "3,23",
            "Crecimiento vs. pares, FMI (pp)": "+1,1 pp", "Inflación vs. pares, FMI (pp)": "-0,6 pp",
            "Balance vs. pares, FMI (pp)": "-0,01"},
    },
    "comparacion": {
        "PIB, var. anual (%)": ["3,23", "5,43", "1,90", "2,65", "1,64"],
        "IMACEC, var. anual (%)": ["3,35", "5,38", "1,85", "2,64", "1,77"],
        "Inflación prom. (%)": ["4,33", "2,54", "3,64", "3,29", "6,72"],
        "Desempleo prom. (%)": ["8,13", "7,02", "6,63", "8,58", "8,41"],
        "Desempleo, cambio (pp)": ["0,73", "-2,35", "0,83", "0,49", "0,83"],
        "Deuda bruta, cambio (pp)": ["0,15", "6,22", "10,86", "12,62", "6,21"],
        "Balance efectivo prom. (% PIB)": ["3,67", "0,20", "-2,32", "-4,88", "-1,73"],
        "Cobre prom. (USD/lb)": ["2,98", "3,59", "2,65", "3,23", "4,19"],
        "Dólar prom. (CLP)": ["533", "495", "640", "734", "905"],
    },
    "resumen": {"Crecimiento del PIB": "4,3 % → 2,1 %", "Deuda bruta": "6 % → 42 %",
                "Desempleo": "7,8 % → 8,3 %", "Meses con inflación entre 2 % y 4 %": "48%"},
}


def auditar_dashboard() -> None:
    from src.analysis import valores_dashboard as vd
    malos, total = [], 0
    for g, campos in DASHBOARD_LEIDO["ficha"].items():
        esperado = vd.ficha(g)
        for k, leido in campos.items():
            total += 1
            if esperado[k].replace(" ", "") != leido.replace(" ", ""):
                malos.append(f"Ficha {ETQ[g]} {k}: dashboard {leido}, cálculo {esperado[k]}")
    for k, leidos in DASHBOARD_LEIDO["comparacion"].items():
        for g, leido in zip(EN_ALCANCE, leidos):
            total += 1
            calc = vd.comparacion(g)[k]
            if calc != leido:
                malos.append(f"Comparación {ETQ[g]} {k}: dashboard {leido}, cálculo {calc}")
    for k, leido in DASHBOARD_LEIDO["resumen"].items():
        total += 1
        if vd.resumen()[k] != leido:
            malos.append(f"Resumen {k}: dashboard {leido}, cálculo {vd.resumen()[k]}")
    registrar(f"G. Dashboard: {total} valores leídos en Power BI contra el cálculo sin DAX", not malos,
              "todos coinciden" if not malos else "; ".join(malos))


POBREZA = pd.read_csv(REFERENCE_DIR / "pobreza_casen.csv")
POBREZA["id_gobierno"] = POBREZA["anio"].map(lambda a: gobierno_en(pd.Timestamp(f"{a}-07-01")))


def pobreza_ini(g):
    """Última medición del gobierno anterior; si no hay, la primera del propio gobierno."""
    previa = POBREZA[POBREZA["id_gobierno"] == g - 1]
    propia = POBREZA[POBREZA["id_gobierno"] == g]
    return (previa if len(previa) else propia.iloc[:1])["pobreza_pct"].iloc[-1]


def pobreza_fin(g):
    return POBREZA.loc[POBREZA["id_gobierno"] == g, "pobreza_pct"].iloc[-1]


def auditar_evaluacion() -> None:
    """La evaluación de aciertos y problemas, recalculada sin SQL a partir de los datos."""
    from src.analysis import valores_dashboard as vd
    sql = consulta("SELECT id_gobierno, orden, favorable FROM economia.v_pbi_evaluacion")
    esperado = {}
    metas = pd.read_csv(REFERENCE_DIR / "metas_fiscales.csv").set_index("id_gobierno")
    ipc = serie("ipc")
    salarios = pd.concat([var12("remuneraciones_reales_hist"), var12("remuneraciones_reales")])
    for g in EN_ALCANCE:
        fs = serie("fees")
        fs_ini = fs.loc[fs["id_gobierno"] == g - 1, "valor"]
        fs_ini = fs_ini.iloc[-1] if len(fs_ini) else fs.loc[fs["id_gobierno"] == g, "valor"].iloc[0]
        esperado.update({
            (g, 1): vd.pares("crecimiento_pib", g) >= 0,
            (g, 2): ipc.loc[ipc["id_gobierno"] == g, "valor"].between(2, 4).mean() >= 0.5,
            (g, 3): vd.final("desempleo", g) < vd.heredado("desempleo", g),
            (g, 4): metas.loc[g, "resultado"] >= metas.loc[g, "meta_vigente"],
            (g, 5): vd.final("deuda_neta", g) <= vd.heredado("deuda_neta", g),
            (g, 6): vd.final("fees", g) >= fs_ini,
            (g, 7): pobreza_fin(g) < pobreza_ini(g),
            (g, 8): salarios.loc[salarios["id_gobierno"] == g, "var"].mean() > 0,
        })
    malos = [f"{ETQ[r.id_gobierno]} criterio {r.orden}" for r in sql.itertuples()
             if bool(r.favorable) != bool(esperado[(r.id_gobierno, r.orden)])]
    registrar(f"H. Balance de cada gobierno: {len(sql)} evaluaciones recalculadas", not malos and len(sql) == 40,
              "todas coinciden" if not malos else ", ".join(malos))


# Balance estructural publicado por la DIPRES, con la metodología actual: "Cumplimiento de las
# metas de regla fiscal en Chile: revisión histórica" (diciembre de 2022), cuadros 5.2 a 5.5.
# 2022-2025: CFA y DIPRES (cierres oficiales informados en cada año).
BE_DIPRES = {2006: 1.4, 2007: 1.1, 2008: -1.0, 2009: -3.4, 2010: -2.1, 2011: -1.0, 2012: -0.4,
             2013: -0.5, 2014: -0.5, 2015: 0.5, 2016: -1.1, 2017: -2.0, 2018: -1.4, 2019: -1.4,
             2020: -2.7, 2021: -10.7, 2022: 0.2, 2023: -2.7, 2024: -3.3, 2025: -3.6}
# Diferencias conocidas entre la serie de la BDE y la cifra publicada: la BDE usa una
# compilación de cuentas nacionales más reciente para el PIB del denominador.
BE_DIFERENCIAS = {2009: "BDE -3,1; DIPRES -3,4 (PIB de la compilación de referencia 2003)",
                  2022: "BDE 0,5; cierre informado 0,2 (diferencia de versión de las cifras; la fuente no la explica)"}

# Saldos de los fondos soberanos publicados por Hacienda y la DIPRES (millones de US$, fin de año).
FONDOS_PUBLICADOS = {("fees", "2008-12"): 20211, ("frp", "2008-12"): 2507,
                     ("fees", "2021-12"): 2457, ("frp", "2021-12"): 7473}


def auditar_fiscal() -> None:
    be = serie("balance_estructural").assign(anio=lambda d: d["fecha"].dt.year).set_index("anio")["valor"]
    malos = {a: (round(be[a], 2), v) for a, v in BE_DIPRES.items()
             if a not in BE_DIFERENCIAS and abs(be[a] - v) > 0.15}
    registrar(f"I. Balance estructural de la BDE contra la DIPRES y el CFA ({len(BE_DIPRES)} años)", not malos,
              "coinciden salvo " + "; ".join(f"{a}: {t}" for a, t in BE_DIFERENCIAS.items())
              if not malos else str(malos))
    malos = []
    for (ind, mes), publicado in FONDOS_PUBLICADOS.items():
        v = serie(ind).set_index("fecha")["valor"][mes].iloc[0]
        if abs(v - publicado) > 1:
            malos.append(f"{ind} {mes}: BDE {v:.0f}, publicado {publicado}")
    registrar(f"I. Fondos soberanos: {len(FONDOS_PUBLICADOS)} saldos contra lo publicado por Hacienda y la DIPRES",
              not malos, "todos coinciden" if not malos else "; ".join(malos))
    metas = pd.read_csv(REFERENCE_DIR / "metas_fiscales.csv")
    malos = [f"{r.id_gobierno}: {r.resultado} vs {BE_DIPRES[r.anio_evaluado]}" for r in metas.itertuples()
             if abs(r.resultado - BE_DIPRES[r.anio_evaluado]) > 0.05]
    registrar("I. Resultados de metas_fiscales.csv contra la DIPRES y el CFA", not malos,
              "todos coinciden" if not malos else "; ".join(malos))


def main() -> int:
    print("== A. Crudo -> limpio"); auditar_crudo()
    print("== B. Asignación"); auditar_asignacion()
    print("== C. Base de datos"); auditar_base()
    print("== D. Fuentes independientes (INE y FMI)"); auditar_ipc_publicado(); auditar_fmi()
    print("== E. Recálculo sin SQL")
    res = resumen_pandas(); auditar_resumen(res)
    print("== F. Documentos"); auditar_documentos(res)
    print("== G. Dashboard"); auditar_dashboard()
    print("== H. Balance de cada gobierno"); auditar_evaluacion()
    print("== I. Datos fiscales contra fuentes publicadas"); auditar_fiscal()
    fallas = [r for r in resultados if not r[1]]
    print(f"\n{len(resultados) - len(fallas)} de {len(resultados)} verificaciones correctas.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
