"""Extrae datos anuales para comparar a Chile con sus pares.

Fuentes públicas, sin cuenta ni clave:
    - FMI, World Economic Outlook (API DataMapper): crecimiento, inflación,
      desempleo, deuda y balance fiscal del gobierno general.
    - Banco Mundial, Worldwide Governance Indicators: control de la corrupción.

Uso (desde la raíz del repositorio):
    python -m src.extract.internacional

Resultado:
    data/raw/internacional/<fuente>_<indicador>_<fecha>.json   respuestas crudas
    data/processed/internacional.csv                           formato largo y ordenado
"""
import json
import sys
from datetime import date

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import PROCESSED_DIR, RAW_DIR

RAW_INT_DIR = RAW_DIR / "internacional"
SALIDA = PROCESSED_DIR / "internacional.csv"

DESDE, HASTA = 2000, 2026

# Chile, los agregados y países de la región con metas de inflación.
ZONAS = {
    "CHL": "Chile",
    "WE": "América Latina y el Caribe",
    "WEOWORLD": "Mundo",
    "PER": "Perú",
    "COL": "Colombia",
    "MEX": "México",
    "BRA": "Brasil",
}
PAISES_WGI = ["CHL", "PER", "COL", "MEX", "BRA"]

IMF_URL = "https://www.imf.org/external/datamapper/api/v1/{codigo}"
IMF_INDICADORES = {
    "NGDP_RPCH": ("crecimiento_pib", "% anual"),
    "PCPIPCH": ("inflacion_promedio", "% anual"),
    "LUR": ("desempleo", "% de la fuerza laboral"),
    "GGXWDG_NGDP": ("deuda_gobierno_general", "% del PIB"),
    "GGXCNL_NGDP": ("balance_gobierno_general", "% del PIB"),
}

WB_URL = "https://api.worldbank.org/v2/country/{pais}/indicator/{codigo}"
WB_INDICADORES = {
    "GOV_WGI_CC.EST": ("control_corrupcion", "puntaje (-2,5 a 2,5)"),
    # Error estándar del puntaje: estimación ± 1,645 × error = intervalo de 90 %.
    # Cambios menores al ancho de ese intervalo no son concluyentes.
    "GOV_WGI_CC.SE": ("control_corrupcion_error", "puntaje (-2,5 a 2,5)"),
}


def _guardar_crudo(datos, nombre: str) -> None:
    RAW_INT_DIR.mkdir(parents=True, exist_ok=True)
    ruta = RAW_INT_DIR / f"{nombre}_{date.today():%Y%m%d}.json"
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")


def extraer_fmi(sesion: requests.Session) -> list[dict]:
    filas = []
    for codigo, (indicador, unidad) in IMF_INDICADORES.items():
        r = sesion.get(IMF_URL.format(codigo=codigo), timeout=120)
        r.raise_for_status()
        datos = r.json()
        _guardar_crudo(datos, f"fmi_{indicador}")
        valores = datos["values"][codigo]
        for zona in ZONAS:
            for anio, valor in valores.get(zona, {}).items():
                if DESDE <= int(anio) <= HASTA and valor is not None:
                    filas.append({
                        "fuente": "FMI, World Economic Outlook (octubre de 2026)",
                        "indicador": indicador, "unidad": unidad,
                        "zona": zona, "anio": int(anio), "valor": float(valor),
                    })
    return filas


def extraer_banco_mundial(sesion: requests.Session) -> list[dict]:
    filas = []
    # Una consulta por país y con source=3 (WGI): sin eso, la API responde 502 con frecuencia.
    for codigo, (indicador, unidad) in WB_INDICADORES.items():
        for pais in PAISES_WGI:
            nombre = f"bm_{indicador}_{pais}"
            cache = RAW_INT_DIR / f"{nombre}_{date.today():%Y%m%d}.json"
            if cache.exists():
                # La API del Banco Mundial falla seguido: se reutiliza lo ya descargado hoy.
                datos = json.loads(cache.read_text(encoding="utf-8"))
            else:
                url = WB_URL.format(pais=pais, codigo=codigo)
                try:
                    r = sesion.get(url, params={"source": 3, "format": "json", "per_page": 100}, timeout=120)
                    r.raise_for_status()
                    datos = r.json()
                    if len(datos) < 2 or not datos[1]:
                        raise RuntimeError("respuesta sin datos")
                except (requests.RequestException, RuntimeError) as e:
                    # El puntaje de Chile es obligatorio; lo demás se informa y se omite si falla.
                    if pais == "CHL" and codigo == "GOV_WGI_CC.EST":
                        raise
                    print(f"AVISO: sin datos de {codigo} para {pais} ({type(e).__name__})")
                    continue
                _guardar_crudo(datos, nombre)
            for obs in datos[1]:
                anio = int(obs["date"])
                if DESDE <= anio <= HASTA and obs["value"] is not None:
                    filas.append({
                        "fuente": "Banco Mundial, Worldwide Governance Indicators",
                        "indicador": indicador, "unidad": unidad,
                        "zona": obs["countryiso3code"], "anio": anio,
                        "valor": float(obs["value"]),
                    })
    return filas


def main() -> int:
    with requests.Session() as sesion:
        # Reintenta ante caídas o lentitud temporal de las APIs públicas.
        reintentos = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        sesion.mount("https://", HTTPAdapter(max_retries=reintentos))
        filas = extraer_fmi(sesion) + extraer_banco_mundial(sesion)

    df = pd.DataFrame(filas)
    df["nombre_zona"] = df["zona"].map(ZONAS)
    # El FMI publica estimaciones para el año en curso y proyecciones para los siguientes.
    df["es_proyeccion"] = df["anio"] >= date.today().year
    df = df.sort_values(["indicador", "zona", "anio"]).reset_index(drop=True)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(SALIDA, index=False, encoding="utf-8")
    print(f"{len(df)} filas -> {SALIDA}")
    print(df.groupby("indicador")["anio"].agg(["min", "max", "count"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
