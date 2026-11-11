"""Etapa 2: limpia las series crudas y las deja en un solo archivo en formato largo.

Uso (desde la raíz del repositorio):
    python -m src.transform.clean

Entrada:  data/raw/bcch/<indicador>_<AAAA-MM-DD>.json  (el más reciente de cada indicador)
Salida:   data/processed/observaciones.csv
          logs/limpieza.log

Formato largo: una fila por (indicador, fecha). Columnas:
    indicador, frecuencia, fecha, fecha_fin_periodo, valor,
    id_gobierno, dias_gobierno, dias_periodo, es_transicion
"""
import json
import logging
import sys
from pathlib import Path

import pandas as pd
import yaml

from src.config import CONFIG_DIR, LOGS_DIR, PROCESSED_DIR, RAW_DIR
from src.transform.asignar_gobierno import (
    agregar_fin_periodo,
    asignar_gobierno,
    cargar_gobiernos,
)

# Rangos de plausibilidad: no son "valores esperados", sino límites amplios que
# solo un error de datos (unidad equivocada, serie equivocada) debería romper.
RANGOS_VALIDOS = {
    "pib": (20_000, 80_000),        # miles de millones de pesos encadenados, trimestral
    "imacec": (40, 150),            # índice 2018 = 100
    "ipc": (-5, 20),                # variación 12 meses, %
    "tpm": (0, 15),                 # %
    "desempleo": (3, 20),           # %
    "tipo_cambio": (400, 1_200),    # pesos por dólar
    "cobre": (1, 7),                # dólares por libra
    "deuda_bruta": (0, 100),        # % del PIB
    "balance_fiscal": (-15, 15),    # % del PIB
    "balance_estructural": (-15, 15),  # % del PIB
    "deuda_neta": (-50, 100),       # % del PIB; negativo = Fisco acreedor neto
    "fees": (0, 40_000),            # millones de dólares
    "frp": (0, 40_000),             # millones de dólares
    "fondos_soberanos": (0, 80_000),  # millones de dólares
}

log = logging.getLogger("limpieza")


def configurar_log() -> None:
    LOGS_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        handlers=[
            logging.FileHandler(LOGS_DIR / "limpieza.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def ruta_mas_reciente(indicador: str, carpeta: Path = RAW_DIR / "bcch") -> Path:
    """Archivo crudo más reciente de un indicador.

    El patrón exige una fecha justo después del nombre, para que "ipc" no tome por
    error un futuro "ipc_sae_2026-11-09.json". Las fechas ISO (AAAA-MM-DD) ordenan
    bien como texto, así que el último de la lista ordenada es el más reciente.
    """
    archivos = sorted(carpeta.glob(f"{indicador}_????-??-??.json"))
    if not archivos:
        raise FileNotFoundError(f"No hay archivo crudo para '{indicador}'. Ejecuta run_bcch.")
    return archivos[-1]


def parsear_serie(datos: dict, indicador: str, frecuencia: str) -> pd.DataFrame:
    """Convierte la respuesta cruda de la API en un DataFrame limpio."""
    crudo = pd.DataFrame(datos["Series"]["Obs"])

    df = pd.DataFrame({
        "indicador": indicador,
        "frecuencia": frecuencia,
        # La API usa día-mes-año. Con format explícito, pandas no adivina:
        # "03-01-2005" es 3 de enero y no 1 de marzo.
        "fecha": pd.to_datetime(crudo["indexDateString"], format="%d-%m-%Y"),
        # Los valores llegan como texto; "NaN" (texto) pasa a NaN numérico.
        "valor": pd.to_numeric(crudo["value"], errors="coerce"),
        "estado": crudo["statusCode"],
    })

    # Días sin dato (fines de semana y feriados en series diarias): la API los
    # marca con estado "ND" y valor "NaN". No representan un valor de 0 ni deben
    # rellenarse: simplemente no hubo publicación ese día.
    sin_dato = (df["estado"] != "OK") | df["valor"].isna()
    if sin_dato.any():
        log.info("      %-14s descarta %5d filas sin dato (estados: %s)",
                 indicador, sin_dato.sum(), df.loc[sin_dato, "estado"].value_counts().to_dict())
    return df.loc[~sin_dato].drop(columns="estado").reset_index(drop=True)


def validar(df: pd.DataFrame) -> list[str]:
    """Revisa la calidad del resultado. Devuelve la lista de problemas encontrados."""
    problemas = []

    duplicados = df.duplicated(subset=["indicador", "fecha"]).sum()
    if duplicados:
        problemas.append(f"{duplicados} filas duplicadas (indicador, fecha)")

    nulos = df[["fecha", "valor", "id_gobierno"]].isna().sum()
    for columna, cantidad in nulos[nulos > 0].items():
        problemas.append(f"{cantidad} nulos en la columna {columna}")

    for indicador, (minimo, maximo) in RANGOS_VALIDOS.items():
        valores = df.loc[df["indicador"] == indicador, "valor"]
        if valores.empty:
            problemas.append(f"'{indicador}' no tiene filas")
            continue
        fuera = valores[(valores < minimo) | (valores > maximo)]
        if not fuera.empty:
            problemas.append(
                f"'{indicador}': {len(fuera)} valores fuera de [{minimo}, {maximo}] "
                f"(ej.: {fuera.iloc[0]})"
            )
    return problemas


def main() -> int:
    configurar_log()
    config = yaml.safe_load((CONFIG_DIR / "series.yaml").read_text(encoding="utf-8"))
    gobiernos = cargar_gobiernos()

    partes = []
    for indicador, meta in config["bcch"].items():
        ruta = ruta_mas_reciente(indicador)
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        serie = parsear_serie(datos, indicador, meta["frecuencia"])
        log.info("OK    %-14s %5d filas  (desde %s)", indicador, len(serie), ruta.name)
        partes.append(serie)

    df = pd.concat(partes, ignore_index=True)
    df = agregar_fin_periodo(df)
    df = asignar_gobierno(df, gobiernos)
    df = df.sort_values(["indicador", "fecha"]).reset_index(drop=True)

    problemas = validar(df)
    for problema in problemas:
        log.error("VALIDACIÓN: %s", problema)
    if problemas:
        log.error("No se guarda el resultado: hay %d problemas de calidad", len(problemas))
        return 1

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    salida = PROCESSED_DIR / "observaciones.csv"
    df.to_csv(salida, index=False, encoding="utf-8", date_format="%Y-%m-%d")
    log.info("Guardado %s: %d filas, %d indicadores", salida.name, len(df), df["indicador"].nunique())

    # Resumen: filas por indicador y gobierno, para revisar a simple vista.
    resumen = (
        df.merge(gobiernos[["id_gobierno", "etiqueta"]], on="id_gobierno")
        .pivot_table(index="indicador", columns="etiqueta", values="valor",
                     aggfunc="count", fill_value=0)
        [gobiernos["etiqueta"]]
    )
    log.info("Filas por indicador y gobierno:\n%s", resumen.to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
