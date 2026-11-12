"""Valores que debe mostrar el dashboard, recalculados sin DAX.

Reproduce en pandas la lógica de cada medida de Power BI (desfase 0, todos los períodos)
y genera la tabla de valores esperados por gobierno. La auditoría (src/analysis/auditoria.py)
la compara con lo que muestra el dashboard.

Uso (desde la raíz del repositorio):
    python -m src.analysis.valores_dashboard      # imprime y escribe docs/valores_dashboard.md
"""
import sys

import pandas as pd

from src.config import PROCESSED_DIR, REFERENCE_DIR, ROOT_DIR

OBS = pd.read_csv(PROCESSED_DIR / "observaciones.csv", parse_dates=["fecha"])
INT = pd.read_csv(PROCESSED_DIR / "internacional.csv")
GOB = pd.read_csv(REFERENCE_DIR / "gobiernos.csv", parse_dates=["fecha_inicio", "fecha_fin"])
EVENTOS = pd.read_csv(REFERENCE_DIR / "eventos.csv", parse_dates=["fecha_inicio", "fecha_fin"])
EN_ALCANCE = GOB.loc[GOB["en_alcance"], "id_gobierno"].tolist()
ETQ = dict(zip(GOB["id_gobierno"], GOB["etiqueta"]))
ANIOS = {2: (2006, 2009), 3: (2010, 2013), 4: (2014, 2017), 5: (2018, 2021), 6: (2022, 2025)}
PARES = ["PER", "COL", "MEX", "BRA"]


def fmt(x: float, dec: int = 1, signo: bool = False) -> str:
    """Formato de Power BI con cultura es-ES: coma decimal y redondeo comercial."""
    s = f"{x:+.{dec}f}" if signo else f"{x:.{dec}f}"
    return s.replace(".", ",")


def serie(ind: str) -> pd.DataFrame:
    return OBS[OBS["indicador"] == ind].sort_values("fecha")


def var12(ind: str) -> pd.DataFrame:
    s = serie(ind)[["fecha", "valor", "id_gobierno"]]
    prev = s[["fecha", "valor"]].assign(fecha=lambda d: d["fecha"] + pd.DateOffset(years=1))
    m = s.merge(prev, on="fecha", suffixes=("", "_ant"))
    return m.assign(var=(m["valor"] / m["valor_ant"] - 1) * 100)


def promedio(ind, g):
    return serie(ind).loc[lambda d: d["id_gobierno"] == g, "valor"].mean()


def final(ind, g):
    return serie(ind).loc[lambda d: d["id_gobierno"] == g, "valor"].iloc[-1]


def heredado(ind, g):
    return serie(ind).loc[lambda d: d["id_gobierno"] == g - 1, "valor"].iloc[-1]


def var_prom(ind, g):
    return var12(ind).loc[lambda d: d["id_gobierno"] == g, "var"].mean()


def pares(ind, g, col="dif"):
    a0, a1 = ANIOS[g]
    d = INT[(INT["indicador"] == ind) & INT["anio"].between(a0, a1)]
    ch = d[d["zona"] == "CHL"].set_index("anio")["valor"]
    pa = d[d["zona"].isin(PARES)].groupby("anio")["valor"].mean()
    return {"dif": (ch - pa).mean(), "chile": ch.mean(), "pares": pa.mean()}[col]


def eventos_del_periodo(g) -> list[str]:
    """Eventos que terminaron en los 12 meses previos a asumir, y los del período."""
    fila = GOB[GOB["id_gobierno"] == g].iloc[0]
    ini, fin = fila["fecha_inicio"], fila["fecha_fin"]
    antes = EVENTOS[(EVENTOS["fecha_fin"] < ini) & (EVENTOS["fecha_fin"] >= ini - pd.DateOffset(months=12))]
    durante = EVENTOS[(EVENTOS["fecha_inicio"] < fin) & (EVENTOS["fecha_fin"] >= ini)]
    return ([f"{e} (antes de asumir)" for e in antes.sort_values("fecha_inicio")["evento"]]
            + durante.sort_values("fecha_inicio")["evento"].tolist())


def ficha(g: int) -> dict[str, str]:
    """Lo que muestra cada tarjeta de la Ficha por gobierno."""
    ipc = serie("ipc").loc[lambda d: d["id_gobierno"] == g, "valor"]
    v = var12("pib").loc[lambda d: d["id_gobierno"] == g, "var"]
    def rec(ind, dec=1):
        return f"{fmt(heredado(ind, g), dec)}  →  {fmt(final(ind, g), dec)}"
    cambio_des = final("desempleo", g) - heredado("desempleo", g)
    return {
        "Crecimiento del PIB (% anual)": fmt(var_prom("pib", g)),
        "Rango trimestral del PIB (%)": f"{fmt(v.min())}  a  {fmt(v.max())}",
        "Inflación promedio (%)": fmt(ipc.mean()),
        "Meses en el rango meta": f"{ipc.between(2, 4).mean() * 100:.0f} %",
        "Desempleo (%): inicio → fin": rec("desempleo"),
        "Cambio del desempleo": ("+" if cambio_des > 0 else "") + fmt(cambio_des) + " pp",
        "Deuda bruta % PIB: inicio → fin": rec("deuda_bruta"),
        "Deuda neta % PIB: inicio → fin": rec("deuda_neta"),
        "Balance efectivo prom. % PIB": fmt(promedio("balance_fiscal", g)),
        "Balance estructural prom. % PIB": fmt(promedio("balance_estructural", g)),
        "TPM (%): inicio → fin": rec("tpm", 2),
        "Dólar (CLP): inicio → fin": rec("tipo_cambio", 0),
        "Cobre prom. (USD/lb)": fmt(promedio("cobre", g), 2),
        "Crecimiento vs. pares, FMI (pp)": fmt(pares("crecimiento_pib", g), 1, True) + " pp",
        "Inflación vs. pares, FMI (pp)": fmt(pares("inflacion_promedio", g), 1, True) + " pp",
        "Balance vs. pares, FMI (pp)": fmt(pares("balance_gobierno_general", g), 1, True),
        "Eventos del período": "; ".join(eventos_del_periodo(g)) or "Sin shocks puntuales registrados",
    }


def comparacion(g: int) -> dict[str, str]:
    """Lo que muestra cada columna de la matriz de Comparación."""
    return {
        "PIB, var. anual (%)": fmt(var_prom("pib", g)),
        "IMACEC, var. anual (%)": fmt(var_prom("imacec", g)),
        "Inflación prom. (%)": fmt(promedio("ipc", g)),
        "Desempleo prom. (%)": fmt(promedio("desempleo", g)),
        "Desempleo, cambio (pp)": fmt(final("desempleo", g) - heredado("desempleo", g)),
        "Deuda bruta, cambio (pp)": fmt(final("deuda_bruta", g) - heredado("deuda_bruta", g)),
        "Deuda neta, cambio (pp)": fmt(final("deuda_neta", g) - heredado("deuda_neta", g), 1, True),
        "Balance efectivo prom. (% PIB)": fmt(promedio("balance_fiscal", g)),
        "Balance estructural prom. (% PIB)": fmt(promedio("balance_estructural", g)),
        "Cobre prom. (USD/lb)": fmt(promedio("cobre", g), 2),
        "Dólar prom. (CLP)": f"{promedio('tipo_cambio', g):.0f}",
    }


def resumen() -> dict[str, str]:
    pib = var12("pib")
    a = pib.loc[pib["id_gobierno"].isin([2, 3]), "var"].mean()
    b = pib.loc[pib["id_gobierno"].isin([4, 5, 6]), "var"].mean()
    ipc = serie("ipc").loc[lambda d: d["id_gobierno"].isin(EN_ALCANCE), "valor"]
    return {
        "Crecimiento del PIB": f"{fmt(a)} % → {fmt(b)} %",
        "Deuda bruta": f"{heredado('deuda_bruta', 2):.0f} % → {final('deuda_bruta', 6):.0f} %",
        "Desempleo": f"{fmt(heredado('desempleo', 2))} % → {fmt(final('desempleo', 6))} %",
        "Meses con inflación entre 2 % y 4 %": f"{ipc.between(2, 4).mean() * 100:.0f} %",
    }


def escribir_markdown() -> str:
    lineas = ["# Valores que muestra el dashboard", "",
              "Generado por `python -m src.analysis.valores_dashboard` a partir de los datos, sin "
              "pasar por Power BI. Sirve para verificar el dashboard: con desfase 0 y sin filtrar el "
              "tipo de período, cada tarjeta debe mostrar exactamente estos valores.", "",
              "## Resumen", "", "| Tarjeta | Valor |", "|---|---|"]
    lineas += [f"| {k} | {v} |" for k, v in resumen().items()]
    for titulo, fn in [("Ficha por gobierno", ficha), ("Comparación (matriz)", comparacion)]:
        tabla = pd.DataFrame({ETQ[g]: fn(g) for g in EN_ALCANCE})
        lineas += ["", f"## {titulo}", "", "| | " + " | ".join(tabla.columns) + " |",
                   "|---|" + "---|" * len(tabla.columns)]
        lineas += [f"| {i} | " + " | ".join(str(x) for x in fila) + " |" for i, fila in tabla.iterrows()]
    return "\n".join(lineas) + "\n"


def main() -> int:
    texto = escribir_markdown()
    (ROOT_DIR / "docs" / "valores_dashboard.md").write_text(texto, encoding="utf-8")
    print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
