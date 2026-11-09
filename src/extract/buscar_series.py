"""Descarga el catálogo de series del Banco Central y busca por texto.

Uso (desde la raíz del repositorio):
    python -m src.extract.buscar_series                          # descarga los catálogos
    python -m src.extract.buscar_series --texto imacec           # busca en todos
    python -m src.extract.buscar_series --texto cobre --frecuencia DAILY
"""
import argparse
from datetime import date

import pandas as pd

from src.config import RAW_DIR
from src.extract.bcch import FRECUENCIAS_VALIDAS, BCChClient

CARPETA = RAW_DIR / "bcch" / "catalogo"


def descargar_catalogos(cliente: BCChClient) -> pd.DataFrame:
    """Descarga (o reutiliza la descarga de hoy) el catálogo de cada frecuencia."""
    CARPETA.mkdir(parents=True, exist_ok=True)
    partes = []
    for frecuencia in sorted(FRECUENCIAS_VALIDAS):
        ruta = CARPETA / f"catalogo_{frecuencia}_{date.today().isoformat()}.csv"
        if ruta.exists():
            df = pd.read_csv(ruta)
        else:
            df = cliente.buscar_series(frecuencia)
            df.to_csv(ruta, index=False, encoding="utf-8")
        print(f"{frecuencia:<10} {len(df):>6} series  -> {ruta.name}")
        partes.append(df)
    return pd.concat(partes, ignore_index=True)


def buscar(catalogo: pd.DataFrame, texto: str, frecuencia: str | None = None) -> pd.DataFrame:
    """Filtra el catálogo por texto en el título (sin distinguir mayúsculas)."""
    resultado = catalogo[catalogo["spanishTitle"].str.contains(texto, case=False, na=False)]
    if frecuencia:
        resultado = resultado[resultado["frequencyCode"] == frecuencia.upper()]
    columnas = ["seriesId", "frequencyCode", "spanishTitle", "firstObservation", "lastObservation"]
    return resultado[columnas]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--texto", help="Texto a buscar en el título de la serie")
    parser.add_argument("--frecuencia", choices=sorted(FRECUENCIAS_VALIDAS))
    args = parser.parse_args()

    catalogo = descargar_catalogos(BCChClient())
    if args.texto:
        with pd.option_context("display.max_rows", 200, "display.max_colwidth", 120, "display.width", 250):
            print(buscar(catalogo, args.texto, args.frecuencia).to_string(index=False))


if __name__ == "__main__":
    main()
