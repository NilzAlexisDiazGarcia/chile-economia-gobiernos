"""Ejecuta las consultas de sql/analisis/ y muestra sus resultados como tablas.

Uso (desde la raíz del repositorio):
    python -m src.analysis.ejecutar_consultas            # todas
    python -m src.analysis.ejecutar_consultas 01 04      # solo las que empiezan con 01 y 04

Las mismas consultas se pueden ejecutar en pgAdmin o en psql; este script solo
evita tener que copiarlas una por una.
"""
import sys

import pandas as pd
import psycopg

from src.config import ROOT_DIR, get_pg_params

CARPETA = ROOT_DIR / "sql" / "analisis"


def main(prefijos: list[str]) -> int:
    archivos = sorted(CARPETA.glob("*.sql"))
    if prefijos:
        archivos = [a for a in archivos if a.name.startswith(tuple(prefijos))]

    with psycopg.connect(**get_pg_params()) as conexion:
        for archivo in archivos:
            cursor = conexion.execute(archivo.read_text(encoding="utf-8"))
            columnas = [col.name for col in cursor.description]
            tabla = pd.DataFrame(cursor.fetchall(), columns=columnas)
            print(f"\n=== {archivo.name} ===")
            with pd.option_context("display.width", 220, "display.max_columns", 20):
                print(tabla.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
