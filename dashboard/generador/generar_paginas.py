"""Genera las páginas del reporte de Power BI (formato PBIR) a partir de código.

Las páginas del reporte se escriben en JSON, así que este script las genera de forma
reproducible: mismas posiciones, colores y textos cada vez que se ejecuta.

- Crea seis páginas desde cero: Resumen, Conclusiones, Balance de cada gobierno, Ficha por
  gobierno, Chile frente a sus pares y Sensibilidad al desfase.
- Ajusta las cuatro páginas hechas a mano en Power BI Desktop (Comparación, Series en el
  tiempo, Contexto externo y Metodología). Parte siempre de su versión original, guardada en
  dashboard/generador/paginas_base/, así que se puede ejecutar varias veces con el mismo
  resultado.

Uso, desde la raíz del repositorio y con Power BI cerrado:
    python dashboard/generador/generar_paginas.py
Después, en Power BI: Inicio → Transformar datos → Actualizar todo.
"""
import json
import secrets
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent / "paginas_base"
DEF = RAIZ / "dashboard/chile_economia.Report/definition"
PAGES = DEF / "pages"
SCHEMA_V = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json"
SCHEMA_P = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"

FONDO_PAGINA = "#F5F5F5"
TEXTO = "#2B2B2B"
GRIS = "#6B6B6B"
MARGEN = 40


def nid():
    return secrets.token_hex(10)


def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def s(texto):  # literal de texto
    return lit("'" + texto.replace("'", "''") + "'")


def color(hexa):
    return {"solid": {"color": s(hexa)}}


def medida(entidad, nombre):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": entidad}}, "Property": nombre}}


def columna(entidad, nombre):
    return {"Column": {"Expression": {"SourceRef": {"Entity": entidad}}, "Property": nombre}}


def proy(campo, etiqueta=None, activa=None):
    tipo = "Measure" if "Measure" in campo else "Column"
    ent = campo[tipo]["Expression"]["SourceRef"]["Entity"]
    prop = campo[tipo]["Property"]
    p = {"field": campo, "queryRef": f"{ent}.{prop}", "nativeQueryRef": etiqueta or prop}
    if etiqueta:
        p["displayName"] = etiqueta
    if activa:
        p["active"] = True
    return p


def filtro_in(entidad, prop, valores, alias="t"):
    return {
        "Version": 2,
        "From": [{"Name": alias, "Entity": entidad, "Type": 0}],
        "Where": [{"Condition": {"In": {
            "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop}}],
            "Values": [[{"Literal": {"Value": v}}] for v in valores],
        }}}],
    }


def contenedor(titulo=None, titulo_medida=None, fondo=True):
    """Formato común del contenedor: título, sin subtítulo, fondo blanco y borde redondeado."""
    vco = {"subTitle": [{"properties": {"show": lit("false")}}]}
    if titulo or titulo_medida:
        props = {"show": lit("true"), "fontSize": lit("16D"), "fontColor": color(TEXTO)}
        props["text"] = {"expr": titulo_medida} if titulo_medida else s(titulo)
        vco["title"] = [{"properties": props}]
    else:
        vco["title"] = [{"properties": {"show": lit("false")}}]
    if fondo:
        vco["background"] = [{"properties": {"show": lit("true"), "color": color("#FFFFFF"),
                                             "transparency": lit("0D")}}]
        vco["border"] = [{"properties": {"show": lit("true"), "color": color("#E3E3E3"),
                                         "radius": lit("8D")}}]
        vco["dropShadow"] = [{"properties": {"show": lit("false")}}]
        vco["padding"] = [{"properties": {"top": lit("12D"), "bottom": lit("12D"),
                                          "left": lit("16D"), "right": lit("16D")}}]
    else:
        vco["background"] = [{"properties": {"show": lit("false")}}]
        vco["border"] = [{"properties": {"show": lit("false")}}]
        vco["dropShadow"] = [{"properties": {"show": lit("false")}}]
    return vco


class Pagina:
    def __init__(self, nombre, nombre_visible, alto=1080):
        self.id = nombre
        self.alto = alto
        self.nombre = nombre_visible
        self.visuales = []
        self.z = 0
        self.filtros_pagina = None

    def agregar(self, tipo, x, y, w, h, query=None, objects=None, vco=None, filtros=None):
        self.z += 1000
        v = {"visualType": tipo}
        if query:
            v["query"] = query
        if objects:
            v["objects"] = objects
        if vco:
            v["visualContainerObjects"] = vco
        v["drillFilterOtherVisuals"] = True
        cont = {
            "$schema": SCHEMA_V,
            "name": nid(),
            "position": {"x": x, "y": y, "z": self.z, "height": h, "width": w, "tabOrder": self.z},
            "visual": v,
        }
        if filtros:
            cont["filterConfig"] = {"filters": filtros}
        self.visuales.append(cont)
        return cont

    # ---- piezas reutilizables -------------------------------------------------
    def texto(self, x, y, w, h, parrafos, fondo=False):
        """parrafos: lista de listas de (texto, estilo) o de str."""
        ps = []
        for p in parrafos:
            if isinstance(p, str):
                p = [(p, {})]
            ps.append({"textRuns": [{"value": t, **({"textStyle": e} if e else {})} for t, e in p]})
        return self.agregar("textbox", x, y, w, h,
                            objects={"general": [{"properties": {"paragraphs": ps}}]},
                            vco=contenedor(fondo=fondo))

    def titulo_pagina(self, texto):
        self.texto(MARGEN, 20, 1840, 56, [[(texto, {"fontWeight": "bold", "fontSize": "28pt",
                                                     "color": TEXTO})]])

    def tarjeta_larga(self, x, y, w, h, campo, titulo, tam=12):
        """Tarjeta clásica con ajuste de texto: muestra listas de varias líneas."""
        objs = {
            "labels": [{"properties": {"fontSize": lit(f"{tam}D"), "color": color(TEXTO)}}],
            "categoryLabels": [{"properties": {"show": lit("false")}}],
            "wordWrap": [{"properties": {"show": lit("true")}}],
        }
        return self.agregar("card", x, y, w, h,
                            query={"queryState": {"Values": {"projections": [proy(campo, titulo)]}}},
                            objects=objs, vco=contenedor(titulo=titulo))

    def tabla(self, x, y, w, h, columnas, titulo, anchos=None, tam=11, orden=None):
        """columnas: lista de (campo, encabezado)."""
        objs = {
            "values": [{"properties": {"fontSize": lit(f"{tam}D"), "wordWrap": lit("true")}}],
            "columnHeaders": [{"properties": {"fontSize": lit(f"{tam}D"), "wordWrap": lit("true")}}],
            "grid": [{"properties": {"gridHorizontal": lit("true")}}],
        }
        if anchos:
            objs["columnWidth"] = [
                {"properties": {"value": lit(f"{a}D")},
                 "selector": {"metadata": proy(c, e)["queryRef"]}}
                for (c, e), a in zip(columnas, anchos)]
        query = {"queryState": {"Values": {"projections": [proy(c, e) for c, e in columnas]}}}
        if orden:
            query["sortDefinition"] = {"sort": [{"field": orden, "direction": "Ascending"}]}
        return self.agregar("tableEx", x, y, w, h, query=query, objects=objs, vco=contenedor(titulo=titulo))

    def subtitulo(self, texto):
        self.texto(MARGEN, 78, 1300, 40, [[(texto, {"fontSize": "14pt", "color": GRIS})]])

    def tarjeta(self, x, y, w, h, campo, etiqueta=None, tam=28, titulo=None, alinear=None, tam_etiqueta=12):
        objs = {
            "value": [{"properties": {"fontSize": lit(f"{tam}D"), "fontColor": color(TEXTO)},
                       "selector": {"id": "default"}}],
            "label": [{"properties": {"show": lit("true" if etiqueta else "false"),
                                      "fontColor": color(GRIS), "fontSize": lit(f"{tam_etiqueta}D")},
                       "selector": {"id": "default"}}],
        }
        return self.agregar("cardVisual", x, y, w, h,
                            query={"queryState": {"Data": {"projections": [proy(campo, etiqueta)]}}},
                            objects=objs, vco=contenedor(titulo=titulo))

    def subtitulo_desfase(self):
        self.tarjeta(MARGEN, 78, 1300, 44, medida("Observaciones", "Texto Desfase"), tam=13)
        self.visuales[-1]["visual"]["visualContainerObjects"] = contenedor(fondo=False)

    def pie(self, medida_fuente="Fuente"):
        ent = "Comparacion" if medida_fuente == "Fuente Comparacion" else "Observaciones"
        self.tarjeta(MARGEN, 1030, 1840, 40, medida(ent, medida_fuente), tam=10)
        self.visuales[-1]["visual"]["visualContainerObjects"] = contenedor(fondo=False)

    def segmentador_desfase(self, x=1380, y=130, w=500, h=70):
        campo = columna("Observaciones", "desfase_meses")
        return self.agregar(
            "slicer", x, y, w, h,
            query={"queryState": {"Values": {"projections": [proy(campo, activa=True)]}},
                   "sortDefinition": {"sort": [{"field": campo, "direction": "Ascending"}]}},
            objects={
                "data": [{"properties": {"mode": s("Basic")}}],
                "general": [{"properties": {"orientation": lit("1D"),
                                            "filter": {"filter": filtro_in("Observaciones", "desfase_meses", ["0L"], "o")}}}],
                "selection": [{"properties": {"strictSingleSelect": lit("true")}}],
                "header": [{"properties": {"text": s("Desfase supuesto (meses)")}}],
            },
            vco=contenedor(fondo=False),
        )

    def sincronizar(self, visual):
        visual["visual"]["syncGroup"] = {"groupName": "desfase_meses", "fieldChanges": True,
                                         "filterChanges": True}

    def guardar(self, fondo=True):
        carpeta = PAGES / self.id
        if carpeta.exists():
            shutil.rmtree(carpeta)
        (carpeta / "visuals").mkdir(parents=True)
        pagina = {"$schema": SCHEMA_P, "name": self.id, "displayName": self.nombre,
                  "displayOption": "FitToPage", "height": self.alto, "width": 1920}
        if fondo:
            pagina["objects"] = fondo_pagina()
        if self.filtros_pagina:
            pagina["filterConfig"] = {"filters": self.filtros_pagina}
        escribir(carpeta / "page.json", pagina)
        for v in self.visuales:
            (carpeta / "visuals" / v["name"]).mkdir()
            escribir(carpeta / "visuals" / v["name"] / "visual.json", v)


def fondo_pagina():
    return {"background": [{"properties": {"color": color(FONDO_PAGINA), "transparency": lit("0D")}}]}


def escribir(ruta, datos):
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def leer(ruta):
    return json.loads(ruta.read_text(encoding="utf-8"))


GOB = columna("Gobiernos", "etiqueta")
ORDEN_GOB = {"sort": [{"field": GOB, "direction": "Ascending"}]}
COLOR_GOB = [{"properties": {"fill": {"solid": {"color": {"expr": medida("Observaciones", "Color Gobierno")}}}},
              "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}}]


def linea_ref(valores):
    """valores: lista de (valor, etiqueta, estilo)."""
    out = []
    for i, (v, etq, estilo) in enumerate(valores, 1):
        out.append({"properties": {
            "show": lit("true"), "value": lit(f"{v}D"), "lineColor": color("#8C8C8C"),
            "style": s(estilo), "transparency": lit("20D"), "displayName": s(etq),
            "dataLabelShow": lit("true" if etq else "false"),
        }, "selector": {"id": str(i)}})
    return out


def barras_gobierno(pag, x, y, w, h, campo_y, etiqueta_y, titulo, ref0=True):
    objs = {"dataPoint": COLOR_GOB, "labels": [{"properties": {"show": lit("true")}}]}
    if ref0:
        objs["y1AxisReferenceLine"] = linea_ref([(0, "", "solid")])
    return pag.agregar(
        "clusteredColumnChart", x, y, w, h,
        query={"queryState": {"Category": {"projections": [proy(GOB, "Gobierno", activa=True)]},
                              "Y": {"projections": [proy(campo_y, etiqueta_y)]}},
               "sortDefinition": ORDEN_GOB},
        objects=objs, vco=contenedor(titulo=titulo))


# =============================================================================
# 1. Resumen
# =============================================================================
def pagina_resumen():
    p = Pagina("a1b2c3d4e5f6a7b8c901", "Resumen")
    p.titulo_pagina("Economía de Chile, 2006–2026: cinco gobiernos, un mismo período de cambio")
    p.subtitulo_desfase()
    p.sincronizar(p.segmentador_desfase())
    O = "Observaciones"
    w = (1840 - 3 * 20) / 4
    tarjetas = [
        ("Crecimiento PIB Antes y Despues 2014", "Crecimiento del PIB (% anual): 2006–14 → 2014–26"),
        ("Deuda 2006 a 2026", "Deuda bruta (% del PIB): 2006 → 2026"),
        ("Desempleo 2006 a 2026", "Desempleo (%): 2006 → 2026"),
        ("% Meses Inflacion en Rango", "Meses con inflación entre 2 % y 4 %"),
    ]
    for i, (m, etq) in enumerate(tarjetas):
        p.tarjeta(MARGEN + i * (w + 20), 210, w, 170, medida(O, m), etq, tam=32)
    fecha = columna(O, "fecha")
    p.agregar(
        "lineChart", MARGEN, 400, 1100, 610,
        query={"queryState": {"Category": {"projections": [proy(fecha, "Fecha", activa=True)]},
                              "Series": {"projections": [proy(GOB, "Gobierno")]},
                              "Y": {"projections": [proy(medida(O, "Valor Promedio"), "Deuda bruta (% del PIB)")]}}},
        vco=contenedor(titulo="Deuda bruta del Gobierno Central (% del PIB)"),
        filtros=[{"name": nid(), "field": columna("Indicadores", "indicador"), "type": "Categorical",
                  "filter": filtro_in("Indicadores", "indicador", ["'deuda_bruta'"], "i"),
                  "howCreated": "User"}])
    neg = {"fontWeight": "bold", "fontSize": "14pt", "color": TEXTO}
    nor = {"fontSize": "13pt", "color": TEXTO}
    p.texto(1160, 400, 720, 610, [
        [("Lo que muestran los datos", {"fontWeight": "bold", "fontSize": "18pt", "color": TEXTO})],
        "",
        [("1. Menos crecimiento. ", neg), ("El PIB creció 4,3 % anual en promedio entre 2006 y 2014, "
          "y 2,1 % entre 2014 y 2026. Ningún período posterior a 2014 promedia más de 3 %.", nor)],
        "",
        [("2. Más deuda. ", neg), ("La deuda bruta pasó de 6 % a 42 % del PIB y subió en los cinco "
          "períodos. Desde 2009 solo hubo superávit fiscal en 2011, 2012 y 2022.", nor)],
        "",
        [("3. Inflación más volátil. ", neg), ("Estuvo dentro del rango meta del Banco Central en el "
          "48 % de los meses. Sus dos máximos (2008 y 2022) coinciden con alzas mundiales de precios.", nor)],
        "",
        [("Lo que distingue a cada gobierno es el punto de partida y el contexto. El reporte no "
          "estima cuánto de cada resultado se debe a las políticas de cada gobierno.",
          {"fontSize": "12pt", "color": GRIS, "fontStyle": "italic"})],
    ], fondo=True)
    p.pie()
    return p


# =============================================================================
# 2. Ficha por gobierno
# =============================================================================
def pagina_ficha():
    p = Pagina("b2c3d4e5f6a7b8c9d012", "Ficha por gobierno")
    O, C = "Observaciones", "Comparacion"
    p.titulo_pagina("Ficha por gobierno: qué recibió, qué entregó y en qué contexto")
    p.subtitulo_desfase()
    p.agregar(
        "slicer", MARGEN, 130, 1100, 70,
        query={"queryState": {"Values": {"projections": [proy(GOB, "Gobierno", activa=True)]}},
               "sortDefinition": ORDEN_GOB},
        objects={
            "data": [{"properties": {"mode": s("Basic")}}],
            "general": [{"properties": {"orientation": lit("1D"),
                                        "filter": {"filter": filtro_in("Gobiernos", "etiqueta", ["'Bachelet I'"], "g")}}}],
            "selection": [{"properties": {"strictSingleSelect": lit("true")}}],
            "header": [{"properties": {"text": s("Gobierno")}}],
        },
        vco=contenedor(fondo=False))
    p.sincronizar(p.segmentador_desfase())
    p.tarjeta(MARGEN, 210, 1840, 56, medida(O, "Titulo Ficha"), tam=20)

    w = (1180 - 3 * 20) / 4
    filas = [
        (280, 100, 22, [("Crecimiento PIB %", O, "Crecimiento del PIB (% anual)"),
                        ("Rango Crecimiento PIB", O, "Rango trimestral del PIB (%)"),
                        ("Inflacion Promedio %", O, "Inflación promedio (%)"),
                        ("% Meses Inflacion en Rango", O, "Meses en el rango meta")]),
        (390, 100, 22, [("Desempleo Recibio Entrego", O, "Desempleo (%): inicio → fin"),
                        ("Desempleo Cambio Texto", O, "Cambio del desempleo"),
                        ("Deuda Recibio Entrego", O, "Deuda bruta % PIB: inicio → fin"),
                        ("Deuda Neta Recibio Entrego", O, "Deuda neta % PIB: inicio → fin")]),
        (500, 100, 22, [("Balance Fiscal Promedio %", O, "Balance efectivo prom. % PIB"),
                        ("Balance Estructural Promedio %", O, "Balance estructural prom. % PIB"),
                        ("TPM Recibio Entrego", O, "TPM (%): inicio → fin"),
                        ("Dolar Recibio Entrego", O, "Dólar (CLP): inicio → fin")]),
        (610, 100, 22, [("Cobre Promedio USD lb", O, "Cobre prom. (USD/lb)"),
                        ("Texto Crecimiento vs Pares", C, "Crecimiento vs. pares, FMI (pp)"),
                        ("Texto Inflacion vs Pares", C, "Inflación vs. pares, FMI (pp)"),
                        ("Balance vs Pares pp", C, "Balance vs. pares, FMI (pp)")]),
    ]
    for y, h, tam, tarjetas in filas:
        for i, (m, ent, etq) in enumerate(tarjetas):
            p.tarjeta(MARGEN + i * (w + 20), y, w, h, medida(ent, m), etq, tam=tam, tam_etiqueta=11)

    fecha = columna(O, "fecha")
    wg = (1180 - 20) / 2
    p.agregar(
        "lineChart", MARGEN, 725, wg, 285,
        query={"queryState": {"Category": {"projections": [proy(fecha, "Fecha", activa=True)]},
                              "Y": {"projections": [proy(medida(O, "Crecimiento IMACEC %"), "IMACEC, var. anual (%)")]}}},
        objects={"y1AxisReferenceLine": linea_ref([(0, "", "solid")]),
                 "dataPoint": [{"properties": {"fill": color("#2B2B2B")}}]},
        vco=contenedor(titulo="Crecimiento mensual del IMACEC durante el mandato (%)"))
    p.agregar(
        "lineChart", MARGEN + wg + 20, 725, wg, 285,
        query={"queryState": {"Category": {"projections": [proy(fecha, "Fecha", activa=True)]},
                              "Y": {"projections": [proy(medida(O, "Inflacion Promedio %"), "Inflación anual (%)")]}}},
        objects={"y1AxisReferenceLine": linea_ref([(3, "", "solid"), (2, "", "dashed"), (4, "", "dashed")]),
                 "dataPoint": [{"properties": {"fill": color("#2B2B2B")}}]},
        vco=contenedor(titulo="Inflación anual vs. meta del Banco Central: 3 %, rango 2 % a 4 %"))

    p.tarjeta_larga(1240, 280, 640, 200, medida(O, "Eventos del Periodo"),
                    "Eventos externos y nacionales del período", tam=12)
    E = "Explicaciones"
    p.tabla(1240, 500, 640, 510,
            [(columna(E, "anio"), "Año"), (columna(E, "tema"), "Tema"),
             (columna(E, "cita"), "Qué dijeron"), (columna(E, "fuente"), "Fuente")],
            "Qué dijeron el Banco Central y el FMI", anchos=[50, 100, 290, 150], tam=10,
            orden=columna(E, "anio"))
    p.pie()
    return p


# =============================================================================
# 3. Chile frente a sus pares
# =============================================================================
def pagina_pares():
    p = Pagina("c3d4e5f6a7b8c9d0e123", "Chile frente a sus pares")
    C = "Comparacion"
    p.titulo_pagina("Chile frente a sus pares: Perú, Colombia, México y Brasil")
    p.subtitulo("Datos anuales del FMI. Cada año se asigna al gobierno que gobernó la mayor parte de él.")
    barras_gobierno(p, MARGEN, 140, 900, 430, medida(C, "Crecimiento vs Pares pp"), "Chile − pares (pp)",
                    "Crecimiento del PIB: Chile menos el promedio de sus pares (pp)")
    barras_gobierno(p, 980, 140, 900, 430, medida(C, "Inflacion vs Pares pp"), "Chile − pares (pp)",
                    "Inflación: Chile menos el promedio de sus pares (pp)")
    p.texto(MARGEN, 585, 1840, 90, [[(
        "Barras sobre 0: Chile creció más (o tuvo más inflación) que el promedio de sus pares. La "
        "comparación separa una parte del contexto externo, pero no mide el efecto de las políticas de "
        "cada gobierno. El control de la corrupción es un índice de percepción del Banco Mundial "
        "(−2,5 a 2,5): los cambios pequeños no son concluyentes.", {"fontSize": "12pt", "color": GRIS})]])
    anio = columna(C, "anio")
    series = [("Crecimiento Chile Anual %", "Chile", "#2B2B2B", 3),
              ("Crecimiento Pares %", "Pares (promedio)", "#9E9E9E", 2),
              ("Crecimiento Mundo %", "Mundo", "#C8C8C8", 2)]
    dp, ls = [], []
    for m, _, col, ancho in series:
        dp.append({"properties": {"fill": color(col)}, "selector": {"metadata": f"{C}.{m}"}})
        ls.append({"properties": {"strokeWidth": lit(f"{ancho}D")}, "selector": {"metadata": f"{C}.{m}"}})
    p.agregar(
        "lineChart", MARGEN, 690, 1100, 320,
        query={"queryState": {"Category": {"projections": [proy(anio, "Año", activa=True)]},
                              "Y": {"projections": [proy(medida(C, m), etq) for m, etq, _, _ in series]}}},
        objects={"dataPoint": dp, "lineStyles": ls,
                 "y1AxisReferenceLine": linea_ref([(0, "", "solid")]),
                 "categoryAxis": [{"properties": {"axisType": s("Categorical")}}]},
        vco=contenedor(titulo="Crecimiento anual del PIB: Chile, pares y mundo (%)"))
    valores = [("Deuda Chile FMI %", "Deuda Chile"), ("Deuda Pares %", "Deuda pares"),
               ("Balance vs Pares pp", "Balance vs. pares"),
               ("Control Corrupcion Chile", "Corrup. Chile"), ("Control Corrupcion Pares", "Corrup. pares")]
    p.agregar(
        "pivotTable", 1160, 690, 720, 320,
        query={"queryState": {"Rows": {"projections": [proy(GOB, "Gobierno", activa=True)]},
                              "Values": {"projections": [proy(medida(C, m), etq) for m, etq in valores]}},
               "sortDefinition": ORDEN_GOB},
        objects={"subTotals": [{"properties": {"rowSubtotals": lit("false")}}],
                 "values": [{"properties": {"fontSize": lit("12D")}}],
                 "rowHeaders": [{"properties": {"fontSize": lit("12D")}}],
                 "columnHeaders": [{"properties": {"fontSize": lit("11D"), "wordWrap": lit("true")}}]},
        vco=contenedor(titulo="Deuda (% PIB), balance (pp) y control de la corrupción (−2,5 a 2,5)"))
    p.pie("Fuente Comparacion")
    return p


# =============================================================================
# 4. Sensibilidad al desfase
# =============================================================================
def pagina_sensibilidad():
    p = Pagina("d4e5f6a7b8c9d0e1f234", "Sensibilidad al desfase")
    O = "Observaciones"
    p.titulo_pagina("Sensibilidad al desfase: ¿cambian los resultados?")
    p.subtitulo("Si las políticas tardan en notarse, cada dato se atribuye al gobierno de 0, 6 o 12 meses antes.")
    des = columna(O, "desfase_meses")
    grises = {"0L": "#2B2B2B", "6L": "#8C8C8C", "12L": "#C8C8C8"}
    dp = [{"properties": {"fill": color(c)},
           "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": des,
                                                             "Right": {"Literal": {"Value": v}}}}}]}}
          for v, c in grises.items()]
    p.agregar(
        "clusteredColumnChart", MARGEN, 140, 1840, 470,
        query={"queryState": {"Category": {"projections": [proy(GOB, "Gobierno", activa=True)]},
                              "Series": {"projections": [proy(des, "Desfase (meses)")]},
                              "Y": {"projections": [proy(medida(O, "Crecimiento IMACEC %"), "IMACEC, var. anual (%)")]}},
               "sortDefinition": ORDEN_GOB},
        objects={"dataPoint": dp, "labels": [{"properties": {"show": lit("true")}}],
                 "legend": [{"properties": {"show": lit("true"), "showTitle": lit("true"),
                                            "titleText": s("Desfase (meses)")}}]},
        vco=contenedor(titulo="Crecimiento promedio del IMACEC según el desfase supuesto (%)"))
    p.agregar(
        "pivotTable", MARGEN, 630, 1100, 380,
        query={"queryState": {"Rows": {"projections": [proy(GOB, "Gobierno", activa=True)]},
                              "Columns": {"projections": [proy(des, "Desfase (meses)")]},
                              "Values": {"projections": [proy(medida(O, "Crecimiento IMACEC %"), "IMACEC (%)"),
                                                         proy(medida(O, "Desempleo Cambio pp"), "Desempleo, cambio (pp)")]}},
               "sortDefinition": ORDEN_GOB},
        objects={"subTotals": [{"properties": {"rowSubtotals": lit("false"), "columnSubtotals": lit("false")}}],
                 "values": [{"properties": {"fontSize": lit("12D")}}],
                 "rowHeaders": [{"properties": {"fontSize": lit("12D")}}]},
        vco=contenedor(titulo="Detalle por gobierno y desfase"))
    nor = {"fontSize": "13pt", "color": TEXTO}
    p.texto(1160, 630, 720, 380, [
        [("Cómo leer esta página", {"fontWeight": "bold", "fontSize": "16pt", "color": TEXTO})],
        "",
        [("Si los resultados se atribuyen al gobierno de 6 o 12 meses antes, las cifras cambian, "
          "pero el período más alto (2010–2014) y el más bajo (2022–2026) se mantienen.", nor)],
        "",
        [("Con 12 meses de desfase, la diferencia entre los dos primeros baja de 2,0 a 0,7 puntos, y "
          "Bachelet II y Piñera II intercambian posiciones.", nor)],
        "",
        [("El reporte no elige un desfase \"correcto\": muestra cuánto dependen las conclusiones de "
          "ese supuesto.", {"fontSize": "12pt", "color": GRIS, "fontStyle": "italic"})],
    ], fondo=True)
    p.pie()
    return p


# =============================================================================
# 5. Balance de cada gobierno
# =============================================================================
def pagina_balance():
    p = Pagina("e5f6a7b8c9d0e1f2a345", "Balance de cada gobierno", alto=1550)
    p.filtros_pagina = [{"name": nid(), "field": columna("Observaciones", "desfase_meses"),
                         "type": "Categorical",
                         "filter": filtro_in("Observaciones", "desfase_meses", ["0L"], "o"),
                         "howCreated": "User"}]
    E, M, O = "Evaluacion", "MetasFiscales", "Observaciones"
    p.titulo_pagina("Balance de cada gobierno: aciertos y problemas, con las mismas reglas para todos")
    p.subtitulo("✓ favorable · ✗ desfavorable, frente a una referencia externa o a la meta que fijó cada "
                "gobierno. Sin desfase.")
    crit = columna(E, "criterio")
    p.agregar(
        "pivotTable", MARGEN, 130, 1840, 395,
        query={"queryState": {"Rows": {"projections": [proy(crit, "Criterio", activa=True)]},
                              "Columns": {"projections": [proy(GOB, "Gobierno")]},
                              "Values": {"projections": [proy(medida(E, "Resultado Evaluacion"), "Resultado")]}},
               "sortDefinition": {"sort": [{"field": crit, "direction": "Ascending"}]}},
        objects={"subTotals": [{"properties": {"rowSubtotals": lit("false"), "columnSubtotals": lit("false")}}],
                 "values": [{"properties": {"fontSize": lit("13D")}}],
                 "rowHeaders": [{"properties": {"fontSize": lit("13D")}}],
                 "columnHeaders": [{"properties": {"fontSize": lit("13D")}}]},
        vco=contenedor(titulo="Resultado de cada gobierno en ocho criterios"))
    p.tabla(MARGEN, 540, 1840, 280,
            [(GOB, "Gobierno"), (columna(M, "decreto_inicial"), "Decreto inicial"),
             (columna(M, "meta_inicial"), "Meta que se fijó al asumir"),
             (columna(M, "Meta y resultado"), "Último año completo"),
             (columna(M, "cumple_meta_vigente"), "Cumplió la meta vigente"),
             (columna(M, "cumple_meta_inicial"), "Cumplió la meta inicial"),
             (columna(M, "anios_cumplidos"), "Años en que cumplió"),
             (columna(M, "shock_extraordinario"), "Shock extraordinario")],
            "Metas fiscales: lo que cada gobierno prometió y lo que entregó (balance estructural, % del PIB)",
            anchos=[95, 175, 390, 300, 105, 105, 150, 270], tam=10, orden=GOB)
    p.agregar(
        "pivotTable", MARGEN, 835, 900, 325,
        query={"queryState": {"Rows": {"projections": [proy(GOB, "Gobierno", activa=True)]},
                              "Values": {"projections": [
                                  proy(medida(O, "FEES Recibio Entrego"), "FEES (fondo para crisis)"),
                                  proy(medida(O, "FRP Recibio Entrego"), "FRP (pensiones)"),
                                  proy(medida(O, "Fondos Soberanos Recibio Entrego"), "Total fondos"),
                                  proy(medida(O, "Deuda Bruta Recibio Entrego"), "Deuda bruta (% PIB)"),
                                  proy(medida(O, "Deuda Neta Recibio Entrego"), "Deuda neta (% PIB)")]}},
               "sortDefinition": ORDEN_GOB},
        objects={"subTotals": [{"properties": {"rowSubtotals": lit("false")}}],
                 "values": [{"properties": {"fontSize": lit("11D")}}],
                 "rowHeaders": [{"properties": {"fontSize": lit("11D")}}],
                 "columnHeaders": [{"properties": {"fontSize": lit("11D"), "wordWrap": lit("true")}}]},
        vco=contenedor(titulo="Arcas fiscales: recibió → dejó (fondos en millones de US$; deuda en % del PIB)"))
    neg = {"fontWeight": "bold", "fontSize": "11pt", "color": TEXTO}
    nor = {"fontSize": "10pt", "color": TEXTO}
    p.texto(960, 835, 450, 325, [
        [("Cómo se evalúa", {"fontWeight": "bold", "fontSize": "13pt", "color": TEXTO})],
        [("Crecimiento: ", neg), ("sobre el promedio de Perú, Colombia, México y Brasil.", nor)],
        [("Inflación: ", neg), ("en el rango de 2 % a 4 % la mayoría de los meses. La controla el Banco Central.", nor)],
        [("Desempleo: ", neg), ("entregar menos del recibido.", nor)],
        [("Meta fiscal: ", neg), ("balance estructural del último año igual o mejor que la meta vigente.", nor)],
        [("Deuda neta: ", neg), ("entregar igual o menos deuda, descontados los fondos.", nor)],
        [("FEES: ", neg), ("entregar igual o más fondo para crisis, en % del PIB. El FRP no cuenta: recibe "
          "aportes por ley.", nor)],
        [("Pobreza y salarios: ", neg), ("menos pobreza (CASEN) y salarios que suban más que los precios.", nor)],
        [("La meta fiscal, la deuda y los fondos dependen principalmente del gobierno.",
          {"fontSize": "10pt", "color": GRIS, "fontStyle": "italic"})],
    ], fondo=True)
    p.texto(1430, 835, 450, 325, [
        [("Lo que muestran los datos", {"fontWeight": "bold", "fontSize": "13pt", "color": TEXTO})],
        [("Meta fiscal: ", neg), ("con la meta vigente, solo Piñera I cumplió; con la meta del decreto "
          "inicial, ninguno de los tres que la fijaron para su último año. Todos modificaron su meta.", nor)],
        [("Contexto: ", neg), ("los incumplimientos de 2009 y 2021 coincidieron con la crisis financiera y la "
          "pandemia; los de 2017 y 2024–2025, no.", nor)],
        [("Ahorro y deuda: ", neg), ("el FEES bajó en Bachelet II, Piñera II y Boric, y la deuda bruta subió en "
          "todos. Un fondo puede crecer con deuda; por eso manda la deuda neta.", nor)],
    ], fondo=True)
    # Costo de endeudarse: a qué tasa se endeudó cada gobierno
    CD = "CostoDeuda"
    p.agregar(
        "pivotTable", MARGEN, 1175, 900, 270,
        query={"queryState": {"Rows": {"projections": [proy(GOB, "Gobierno", activa=True)]},
                              "Values": {"projections": [
                                  proy(medida(CD, "Tasa Bonos Pesos %"), "Tasa en pesos a 10 años (%)"),
                                  proy(medida(CD, "Tasa Bonos UF %"), "Tasa real en UF a 10 años (%)"),
                                  proy(medida(CD, "Intereses Recibio Entrego"), "Intereses (% PIB): recibió → dejó")]}},
               "sortDefinition": ORDEN_GOB},
        objects={"subTotals": [{"properties": {"rowSubtotals": lit("false")}}],
                 "values": [{"properties": {"fontSize": lit("13D")}}],
                 "rowHeaders": [{"properties": {"fontSize": lit("13D")}}],
                 "columnHeaders": [{"properties": {"fontSize": lit("13D"), "wordWrap": lit("true")}}]},
        vco=contenedor(titulo="Costo de endeudarse: tasa promedio de los bonos del período y gasto en intereses"))
    neg_g = {"fontWeight": "bold", "fontSize": "13pt", "color": TEXTO}
    nor_g = {"fontSize": "12pt", "color": TEXTO}
    p.texto(960, 1175, 920, 270, [
        [("A qué tasa se endeudó cada gobierno", {"fontWeight": "bold", "fontSize": "15pt", "color": TEXTO})],
        [("Piñera II fue el que más deuda tomó, ", neg_g), ("de 23,6 % a 36,2 % del PIB, con las tasas reales más "
          "bajas del período (0,9 % en UF), en años de tasas mundiales mínimas.", nor_g)],
        [("Boric heredó esa deuda y la siguió aumentando con tasas más altas, ", neg_g), ("cuando las tasas "
          "subieron en todo el mundo en 2022–2023. El gasto en intereses llegó a 1,24 % del PIB en 2025, el "
          "mayor del período.", nor_g)],
        [("Cómo leerlo: ", neg_g), ("las tasas las fija el mercado; el gobierno influye a través de cuánto se "
          "endeuda y de la confianza fiscal. La tasa en UF descuenta la inflación, y es la que mejor se compara "
          "entre gobiernos.", nor_g)],
    ], fondo=True)
    p.texto(MARGEN, 1460, 1840, 75, [[(
        "Fuente: DIPRES (Cumplimiento de las metas de regla fiscal, 2022), Consejo Fiscal Autónomo, Banco Central "
        "de Chile (BDE), FMI y CASEN. Elaboración propia. Recibió: último dato del gobierno anterior (desempleo y FEES: "
        "febrero; deuda: primer trimestre del año del cambio de mando; pobreza: última CASEN, con su año). "
        "Meta inicial \"No aplica\": el decreto la fijaba para el año siguiente al último completo.",
        {"fontSize": "10pt", "color": TEXTO, "fontWeight": "bold"})]],
        fondo=True)
    return p


# =============================================================================
# 6. Conclusiones
# =============================================================================
def pagina_conclusiones():
    p = Pagina("f6a7b8c9d0e1f2a3b456", "Conclusiones")
    p.filtros_pagina = [{"name": nid(), "field": columna("Observaciones", "desfase_meses"),
                         "type": "Categorical",
                         "filter": filtro_in("Observaciones", "desfase_meses", ["0L"], "o"),
                         "howCreated": "User"}]
    O, C = "Observaciones", "Comparacion"
    p.titulo_pagina("Conclusiones: por qué Chile creció menos y se endeudó")
    p.texto(MARGEN, 85, 1840, 125, [[(
        "Entre 2006 y 2026, Chile pasó de crecer rápido y ahorrar a crecer menos y endeudarse. Según el Banco "
        "Central, el FMI, la DIPRES y la CNEP, fue un cambio estructural, que comenzó con el fin del auge del cobre "
        "y la caída de la productividad. Ningún gobierno lo revirtió: los cinco terminaron su período con déficit "
        "estructural, y la deuda neta subió en cuatro de ellos. Al mismo tiempo, la pobreza bajó con fuerza.", {"fontSize": "15pt", "color": TEXTO, "fontWeight": "bold"})]], fondo=True)
    anio = columna(C, "anio")
    p.agregar(
        "columnChart", MARGEN, 225, 900, 455,
        query={"queryState": {"Category": {"projections": [proy(anio, "Año", activa=True)]},
                              "Series": {"projections": [proy(GOB, "Gobierno")]},
                              "Y": {"projections": [proy(medida(C, "Crecimiento per Capita Chile %"),
                                                         "PIB por habitante (% anual)")]}}},
        objects={"y1AxisReferenceLine": linea_ref([(0, "", "solid")]),
                 "categoryAxis": [{"properties": {"axisType": s("Categorical")}}],
                 "labels": [{"properties": {"show": lit("false")}}]},
        vco=contenedor(titulo="El ingreso por habitante casi se estancó: 3,4 % anual en 2006–2013 y 1,0 % en 2014–2025"))
    fecha = columna(O, "fecha")
    p.agregar(
        "lineChart", 980, 225, 900, 455,
        query={"queryState": {"Category": {"projections": [proy(fecha, "Fecha", activa=True)]},
                              "Series": {"projections": [proy(GOB, "Gobierno")]},
                              "Y": {"projections": [proy(medida(O, "Valor Promedio"), "Deuda neta (% del PIB)")]}}},
        objects={"y1AxisReferenceLine": linea_ref([(0, "", "solid")])},
        vco=contenedor(titulo="Chile pasó de acreedor neto a deudor neto: deuda neta de −19 % a 26 % del PIB"),
        filtros=[{"name": nid(), "field": columna("Indicadores", "indicador"), "type": "Categorical",
                  "filter": filtro_in("Indicadores", "indicador", ["'deuda_neta'"], "i"), "howCreated": "User"}])
    neg = {"fontWeight": "bold", "fontSize": "12pt", "color": TEXTO}
    nor = {"fontSize": "12pt", "color": TEXTO}
    tit = {"fontWeight": "bold", "fontSize": "15pt", "color": TEXTO}
    w = (1840 - 2 * 20) / 3
    p.texto(MARGEN, 695, w, 317, [
        [("Por qué creció menos", tit)],
        [("1. La productividad se estancó: ", neg), ("lleva unos 16 años sin aportar al crecimiento (CNEP), por la "
          "desaceleración mundial, la rigidez laboral, los permisos para invertir y la menor ley del mineral.", nor)],
        [("2. Terminó el auge del cobre: ", neg), ("la inversión minera cayó desde 2013–2014 (FMI).", nor)],
        [("3. La capacidad de crecer se redujo a la mitad: ", neg), ("de cerca de 5 % estimado en 2011 a 2 % hoy "
          "(DIPRES y Banco Central).", nor)],
        [("4. Hubo incertidumbre local: ", neg), ("por las reformas de 2014 (FMI) y en 2021 (Banco Central).", nor)],
    ], fondo=True)
    p.texto(MARGEN + w + 20, 695, w, 317, [
        [("Por qué se endeudó", tit)],
        [("1. Gasto permanente mayor que el ingreso permanente: ", neg), ("23,8 % y 22 % del PIB en 2008–2023 (CFA); "
          "déficit en 14 de 17 años desde 2009.", nor)],
        [("2. El menor crecimiento redujo la recaudación esperada: ", neg), ("crecer poco y endeudarse se "
          "alimentan entre sí (DIPRES).", nor)],
        [("3. Dos shocks: ", neg), ("la crisis de 2009 y la pandemia (déficit estructural de −10,7 % en 2021).", nor)],
        [("4. Metas fiscales cambiadas a discreción: ", neg), ("la meta inicial de cada gobierno se cumplió en 9 de 21 "
          "años (DIPRES).", nor)],
        [("5. Deuda más cara: ", neg), ("intereses de 0,47 % del PIB en 2008 a 1,24 % en 2025 (BCCh).", nor)],
        [("6. Ingresos sobrestimados: ", neg), ("en 2024–2025, según el CFA.", nor)],
    ], fondo=True)
    p.texto(MARGEN + 2 * (w + 20), 695, w, 317, [
        [("Lo que mejoró y lo que queda pendiente", tit)],
        [("La pobreza bajó de 29,1 % a 4,9 % ", neg), ("entre 2006 y 2024 (CASEN, serie comparable). Bajó en todos "
          "los gobiernos salvo en la pandemia, y los salarios reales subieron casi todos los años.", nor)],
        [("Pendiente para cualquier gobierno: ", neg), ("recuperar la productividad y la inversión, porque sin eso "
          "el crecimiento seguirá cerca de 2 %, y estabilizar la deuda, que superaría el nivel prudente de 45 % del "
          "PIB hacia 2028–2029 sin consolidación fiscal (FMI y CFA).", nor)],
        [("Según las fuentes, el cambio de fondo fue estructural y ningún gobierno lo revirtió. El detalle de cada gobierno está en la página "
          "siguiente.", {"fontSize": "10pt", "color": GRIS, "fontStyle": "italic"})],
    ], fondo=True)
    p.texto(MARGEN, 1022, 1840, 52, [[(
        "Fuente: CNEP, Banco Central de Chile, FMI, DIPRES, Consejo Fiscal Autónomo y Ministerio de Desarrollo "
        "Social (CASEN). Detalle de cada fuente en docs/conclusiones.md.",
        {"fontSize": "10pt", "color": TEXTO, "fontWeight": "bold"})]], fondo=True)
    return p


# =============================================================================
# Ajustes a páginas existentes
# =============================================================================
def visual_de(pagina, nombre):
    return PAGES / pagina / "visuals" / nombre / "visual.json"


def ajustar_existentes():
    """Lleva las cuatro páginas originales al mismo sistema de diseño de las nuevas.

    Parte siempre del estado original de esas páginas (respaldo), así es idempotente.
    """
    def mover(v, x, y, w, h):
        v["position"].update({"x": x, "y": y, "width": w, "height": h})

    def extras(pid, pag):
        """Escribe los visuales nuevos de pag dentro de una página existente."""
        for v in pag.visuales:
            (PAGES / pid / "visuals" / v["name"]).mkdir()
            escribir(PAGES / pid / "visuals" / v["name"] / "visual.json", v)

    def cabecera(pid, titulo, desfase=True):
        pag = Pagina(pid, "")
        pag.z = 20000
        pag.titulo_pagina(titulo)
        if desfase:
            pag.subtitulo_desfase()
        return pag

    def editar(pid, nombre, fn):
        r = visual_de(pid, nombre)
        v = leer(r)
        fn(v)
        escribir(r, v)

    def slicer_desfase(v):
        mover(v, 1380, 130, 500, 70)
        v["visual"].setdefault("objects", {})["header"] = [{"properties": {"text": s("Desfase supuesto (meses)")}}]
        v["visual"]["visualContainerObjects"] = contenedor(fondo=False)

    for pid in ["62247b640a13465c1685", "48ac0870d81460b400b6", "ad2b1cab32d000514230", "a94af317d61089c4dec0"]:
        ruta = PAGES / pid / "page.json"
        pg = leer(ruta)
        pg["objects"] = fondo_pagina()
        escribir(ruta, pg)

    # ---- Comparación ---------------------------------------------------------
    P = "62247b640a13465c1685"

    def titulo_comp(v):
        mover(v, MARGEN, 20, 1840, 56)
        v["visual"]["objects"]["general"][0]["properties"]["paragraphs"] = [{"textRuns": [{
            "value": "Comparación de indicadores por gobierno, 2006–2026",
            "textStyle": {"fontWeight": "bold", "fontSize": "28pt", "color": TEXTO}}]}]
    editar(P, "88789733ae00c3c9125c", titulo_comp)

    def desfase_txt(v):
        mover(v, MARGEN, 78, 1300, 44)
        v["visual"]["objects"] = {
            "value": [{"properties": {"fontSize": lit("13D"), "fontColor": color(TEXTO)}, "selector": {"id": "default"}}],
            "label": [{"properties": {"show": lit("false")}, "selector": {"id": "default"}}]}
        v["visual"]["visualContainerObjects"] = contenedor(fondo=False)
    editar(P, "a1f628580210c309c911", desfase_txt)
    editar(P, "625ffbfaab75193d7460", slicer_desfase)

    def tipo_periodo(v):
        mover(v, MARGEN, 130, 800, 70)
        v["visual"]["objects"]["header"] = [{"properties": {"text": s("Tipo de período")}}]
        v["visual"]["visualContainerObjects"] = contenedor(fondo=False)
    editar(P, "6416550845b72cbc0007", tipo_periodo)

    def matriz(v):
        mover(v, MARGEN, 210, 1840, 330)
        O_ = "Observaciones"
        vals = v["visual"]["query"]["queryState"]["Values"]["projections"]
        for pr in vals:
            if pr["field"]["Measure"]["Property"] == "Balance Fiscal Promedio %":
                pr["displayName"] = pr["nativeQueryRef"] = "Balance efectivo prom. (% PIB)"
        pos = next(k for k, pr in enumerate(vals) if pr["field"]["Measure"]["Property"] == "Balance Fiscal Promedio %")
        vals.insert(pos + 1, proy(medida(O_, "Balance Estructural Promedio %"), "Balance estructural prom. (% PIB)"))
        pos = next(k for k, pr in enumerate(vals) if pr["field"]["Measure"]["Property"] == "Deuda Cambio pp")
        vals[pos]["displayName"] = vals[pos]["nativeQueryRef"] = "Deuda bruta, cambio (pp)"
        vals.insert(pos + 1, proy(medida(O_, "Deuda Neta Cambio pp"), "Deuda neta, cambio (pp)"))
        o = v["visual"]["objects"]
        o["values"] = [{"properties": {"fontSize": lit("12D")}}]
        o["rowHeaders"] = [{"properties": {"fontSize": lit("12D")}}]
        o["columnHeaders"] = [{"properties": {"fontSize": lit("11D"), "wordWrap": lit("true")}}]
        # Encabezados cortos: 11 columnas deben caber en el ancho de la página
        cortos = {"PIB, var. anual (%)": "PIB (%)", "IMACEC, var. anual (%)": "IMACEC (%)",
                  "Inflación prom. (%)": "Inflación (%)", "Desempleo prom. (%)": "Desempleo (%)",
                  "Desempleo, cambio (pp)": "Desempleo, cambio (pp)",
                  "Deuda bruta, cambio (pp)": "Deuda bruta, cambio (pp)",
                  "Deuda neta, cambio (pp)": "Deuda neta, cambio (pp)",
                  "Balance efectivo prom. (% PIB)": "Balance efectivo (% PIB)",
                  "Balance estructural prom. (% PIB)": "Balance estructural (% PIB)",
                  "Cobre prom. (USD/lb)": "Cobre (USD/lb)"}
        for pr in v["visual"]["query"]["queryState"]["Values"]["projections"]:
            nuevo = cortos.get(pr.get("displayName"))
            if nuevo:
                pr["displayName"] = pr["nativeQueryRef"] = nuevo
        v["visual"]["visualContainerObjects"] = contenedor(
            titulo="Promedios y cambios por gobierno (crecimiento e inflación: variación anual promedio)")
        return
        v["visual"]["visualContainerObjects"] = contenedor(titulo="Promedios y cambios por gobierno")
    editar(P, "d5150034bab510692127", matriz)

    def barras(v):
        mover(v, MARGEN, 560, 1840, 450)
        v["visual"]["objects"]["dataPoint"] = COLOR_GOB
        v["visual"]["query"]["sortDefinition"] = ORDEN_GOB
        v["visual"]["visualContainerObjects"] = contenedor(titulo="Crecimiento promedio del IMACEC por gobierno (%)")
    editar(P, "bd242dcd033140446088", barras)

    def pie_existente(v):
        mover(v, MARGEN, 1030, 1840, 40)
        v["visual"]["visualContainerObjects"] = contenedor(fondo=False)
    editar(P, "aeedcc4e1ba0605b45b5", pie_existente)

    # ---- Series en el tiempo -------------------------------------------------
    P = "48ac0870d81460b400b6"
    pag = cabecera(P, "Series en el tiempo: cada indicador, gobierno por gobierno")
    pag.pie()
    extras(P, pag)
    editar(P, "6629003a335016473863", slicer_desfase)

    def indicador(v):
        mover(v, MARGEN, 130, 600, 70)
        nombre = columna("Indicadores", "Nombre")
        v["visual"]["query"]["queryState"]["Values"]["projections"] = [proy(nombre, "Indicador", activa=True)]
        o = v["visual"]["objects"]
        o["data"] = [{"properties": {"mode": s("Dropdown")}}]
        o["general"] = [{"properties": {"filter": {"filter": filtro_in("Indicadores", "Nombre", ["'IMACEC'"], "i")}}}]
        o["header"] = [{"properties": {"text": s("Indicador")}}]
        v["visual"]["visualContainerObjects"] = contenedor(fondo=False)
    editar(P, "84ffabd4112cae56082e", indicador)

    def linea(y, m):
        def fn(v):
            mover(v, MARGEN, y, 1840, 280)
            v["visual"]["visualContainerObjects"] = contenedor(titulo_medida=medida("Observaciones", m))
        return fn
    editar(P, "6cfacbe486602908e32e", linea(210, "Titulo Serie"))
    editar(P, "3726c6a30a508ca634c8", linea(505, "Titulo Var 12m"))

    def eventos(v):
        mover(v, MARGEN, 800, 1840, 215)
        nombres = {"evento": "Evento", "fecha_inicio": "Inicio", "fecha_fin": "Fin", "nota": "Nota"}
        for pr in v["visual"]["query"]["queryState"]["Values"]["projections"]:
            etq = nombres[pr["field"]["Column"]["Property"]]
            pr["displayName"] = etq
            pr["nativeQueryRef"] = etq
        o = v["visual"].setdefault("objects", {})
        o["values"] = [{"properties": {"fontSize": lit("10D")}}]
        o["columnHeaders"] = [{"properties": {"fontSize": lit("10D")}}]
        v["visual"]["query"]["sortDefinition"] = {"sort": [{"field": columna("Eventos", "fecha_inicio"),
                                                            "direction": "Ascending"}]}
        v["visual"]["visualContainerObjects"] = contenedor(titulo="Eventos de contexto")
    editar(P, "c10a471eb2d846b3481a", eventos)

    # ---- Contexto externo ----------------------------------------------------
    P = "ad2b1cab32d000514230"
    tabla = PAGES / P / "visuals" / "35f824bb0a8c6556e5b5"
    if tabla.exists():
        shutil.rmtree(tabla)
    pag = cabecera(P, "Contexto externo: cobre, dólar y actividad")
    barras_gobierno(pag, 980, 630, 900, 380, medida("Observaciones", "Dolar Promedio CLP"), "Dólar (CLP)",
                    "Dólar promedio (pesos chilenos por dólar)", ref0=False)
    pag.pie()
    extras(P, pag)
    editar(P, "ef1ccf328a000a020d1a", slicer_desfase)

    def linea_ctx(v):
        mover(v, MARGEN, 210, 1840, 400)
        nombres = {"Crecimiento IMACEC %": "IMACEC, var. anual (%)",
                   "Cobre Var 12m %": "Cobre, var. anual (%), eje derecho"}
        for rol in ("Y", "Y2"):
            for pr in v["visual"]["query"]["queryState"].get(rol, {}).get("projections", []):
                etq = nombres.get(pr["field"]["Measure"]["Property"])
                if etq:
                    pr["displayName"] = etq
                    pr["nativeQueryRef"] = etq
        v["visual"]["visualContainerObjects"] = contenedor(titulo="Variación anual: IMACEC y precio del cobre (%)")
    editar(P, "e5dc281e146713dc0ac4", linea_ctx)

    def cobre(v):
        mover(v, MARGEN, 630, 900, 380)
        v["visual"].setdefault("objects", {})["dataPoint"] = COLOR_GOB
        v["visual"]["objects"]["labels"] = [{"properties": {"show": lit("true")}}]
        v["visual"]["query"]["sortDefinition"] = ORDEN_GOB
        v["visual"]["visualContainerObjects"] = contenedor(titulo="Precio promedio del cobre (USD nominales por libra)")
    editar(P, "9e3599fd9291d6ad2984", cobre)

    # ---- Metodología ---------------------------------------------------------
    P = "a94af317d61089c4dec0"

    def metodologia(v):
        mover(v, MARGEN, 20, 1840, 1000)
        ps = v["visual"]["objects"]["general"][0]["properties"]["paragraphs"]
        # quita los párrafos vacíos que siguen al título
        while len(ps) > 1 and all(not tr.get("value") for tr in ps[1]["textRuns"]):
            ps.pop(1)
        ps.insert(1, {"textRuns": [{"value": ""}]})
        for p_ in ps:
            for tr in p_["textRuns"]:
                st = tr.get("textStyle")
                if st and st.get("fontSize") == "20pt":
                    st["fontSize"] = "15pt"
        b = {"fontWeight": "bold", "fontSize": "15pt"}
        n = {"fontSize": "15pt"}
        ps.extend([
            {"textRuns": [{"value": ""}]},
            {"textRuns": [{"value": "Eventos.", "textStyle": b},
                          {"value": " Shocks de alcance global o nacional con fechas documentadas por una fuente "
                                    "oficial (data/reference/eventos.csv).", "textStyle": n}]},
            {"textRuns": [{"value": ""}]},
            {"textRuns": [{"value": "Comparación con pares.", "textStyle": b},
                          {"value": " Datos anuales del FMI (World Economic Outlook, octubre de 2026) y del Banco "
                                    "Mundial (WGI). Pares: Perú, Colombia, México y Brasil. Cada año se asigna al "
                                    "gobierno que gobernó la mayor parte de él; por eso las cifras anuales de Chile "
                                    "difieren levemente de las mensuales. Deuda y balance corresponden al gobierno "
                                    "general, una definición distinta de la del Gobierno Central.", "textStyle": n}]},
            {"textRuns": [{"value": ""}]},
            {"textRuns": [{"value": "Explicaciones oficiales.", "textStyle": b},
                          {"value": " Las citas de la Ficha por gobierno son textuales, del Banco Central de Chile y "
                                    "del FMI, con su fuente (data/reference/explicaciones.csv).", "textStyle": n}]},
        ])
        v["visual"]["visualContainerObjects"] = contenedor(fondo=True)
    editar(P, "74a9a6d6011a394482a5", metodologia)


def restaurar_base():
    """Vuelve las páginas hechas a mano a su versión original antes de ajustarlas."""
    for origen in BASE.iterdir():
        destino = PAGES / origen.name
        if origen.is_dir():
            if destino.exists():
                shutil.rmtree(destino)
            shutil.copytree(origen, destino)
        else:
            shutil.copy2(origen, destino)


def main():
    restaurar_base()
    nuevas = [pagina_resumen(), pagina_conclusiones(), pagina_balance(), pagina_ficha(), pagina_pares(),
              pagina_sensibilidad()]
    for p in nuevas:
        p.guardar()
    ajustar_existentes()
    orden = [
        "a1b2c3d4e5f6a7b8c901",  # Resumen
        "f6a7b8c9d0e1f2a3b456",  # Conclusiones
        "e5f6a7b8c9d0e1f2a345",  # Balance de cada gobierno
        "62247b640a13465c1685",  # Comparación
        "b2c3d4e5f6a7b8c9d012",  # Ficha por gobierno
        "48ac0870d81460b400b6",  # Series en el tiempo
        "ad2b1cab32d000514230",  # Contexto externo
        "c3d4e5f6a7b8c9d0e123",  # Chile frente a sus pares
        "d4e5f6a7b8c9d0e1f234",  # Sensibilidad al desfase
        "a94af317d61089c4dec0",  # Metodología
    ]
    pj = leer(PAGES / "pages.json")
    pj["pageOrder"] = orden
    pj["activePageName"] = orden[0]
    escribir(PAGES / "pages.json", pj)
    print("Páginas generadas:", [p.nombre for p in nuevas])


if __name__ == "__main__":
    main()
