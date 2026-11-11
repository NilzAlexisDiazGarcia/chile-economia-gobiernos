"""Etapa 3: carga las tablas de referencia, las observaciones y los datos
internacionales en PostgreSQL.

Uso (desde la raíz del repositorio):
    python -m src.load.postgres

Estrategia: "recarga completa" dentro de UNA transacción.
    1. Crea el esquema y las tablas si no existen (sql/01_schema.sql).
    2. Vacía las tablas (TRUNCATE).
    3. Inserta todo de nuevo.
    4. Verifica que los conteos de la base coincidan con los archivos.
Si cualquier paso falla, la transacción se revierte (ROLLBACK) y la base queda
exactamente como estaba antes: nunca a medio cargar.
"""
import logging
import sys

import pandas as pd
import psycopg
import yaml

from src.config import (
    CONFIG_DIR,
    LOGS_DIR,
    PROCESSED_DIR,
    REFERENCE_DIR,
    ROOT_DIR,
    get_pg_params,
)
from src.transform.asignar_gobierno import agregar_fin_periodo, asignar_gobierno

log = logging.getLogger("carga")

COLUMNAS_OBSERVACION = [
    "indicador", "fecha", "valor", "fecha_fin_periodo", "id_gobierno",
    "dias_gobierno", "dias_periodo", "es_transicion",
]


def configurar_log() -> None:
    LOGS_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        handlers=[
            logging.FileHandler(LOGS_DIR / "carga.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def leer_indicadores() -> pd.DataFrame:
    """Arma la dimensión de indicadores a partir de config/series.yaml."""
    config = yaml.safe_load((CONFIG_DIR / "series.yaml").read_text(encoding="utf-8"))
    filas = [
        {
            "indicador": clave,
            "descripcion": meta["descripcion"],
            "unidad": meta["unidad"],
            "frecuencia": meta["frecuencia"],
            "codigo_serie": meta["codigo"],
            "fuente": "Banco Central de Chile (API BDE)",
            "fuente_original": meta.get("fuente_original", "Banco Central de Chile"),
        }
        for clave, meta in config["bcch"].items()
    ]
    return pd.DataFrame(filas)


def asignar_gobierno_anual(df: pd.DataFrame, gobiernos: pd.DataFrame) -> pd.Series:
    """Gobierno de Chile que gobernó la mayor parte de cada año (columna anio).

    Reutiliza la regla de mayoría de días de las observaciones mensuales, tratando
    cada año como una observación de frecuencia anual.
    """
    anios = pd.DataFrame({
        "fecha": pd.to_datetime(df["anio"].astype(str) + "-01-01"),
        "frecuencia": "ANNUAL",
    })
    return asignar_gobierno(agregar_fin_periodo(anios), gobiernos)["id_gobierno"].values


def leer_internacional(gobiernos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Datos del FMI y del Banco Mundial, y citas oficiales, con su gobierno asignado."""
    internacional = pd.read_csv(PROCESSED_DIR / "internacional.csv")[
        ["indicador", "zona", "anio", "valor", "unidad", "fuente", "es_proyeccion"]
    ]
    internacional["id_gobierno"] = asignar_gobierno_anual(internacional, gobiernos)
    explicaciones = pd.read_csv(REFERENCE_DIR / "explicaciones.csv")
    explicaciones["id_gobierno"] = asignar_gobierno_anual(explicaciones, gobiernos)
    return internacional, explicaciones


def insertar(cursor: psycopg.Cursor, tabla: str, df: pd.DataFrame) -> None:
    """Carga un DataFrame con COPY, el método de carga masiva de PostgreSQL.

    COPY envía todas las filas en un solo flujo, en vez de un INSERT por fila.
    Los valores viajan como datos, separados del texto SQL, así que no hay riesgo
    de inyección SQL aunque un campo contenga comillas o punto y coma.
    """
    columnas = ", ".join(df.columns)
    # pandas usa NaN/NaT para los vacíos; PostgreSQL necesita None (NULL).
    filas = df.astype(object).where(df.notna(), None).itertuples(index=False, name=None)
    with cursor.copy(f"COPY economia.{tabla} ({columnas}) FROM STDIN") as copy:
        for fila in filas:
            copy.write_row(fila)
    log.info("Cargadas %6d filas en economia.%s", len(df), tabla)


def main() -> int:
    configurar_log()

    gobiernos = pd.read_csv(REFERENCE_DIR / "gobiernos.csv", parse_dates=["fecha_inicio", "fecha_fin"])
    eventos = pd.read_csv(REFERENCE_DIR / "eventos.csv", parse_dates=["fecha_inicio", "fecha_fin"])
    indicadores = leer_indicadores()
    zonas = pd.read_csv(REFERENCE_DIR / "zonas.csv")
    internacional, explicaciones = leer_internacional(gobiernos)
    observaciones = pd.read_csv(
        PROCESSED_DIR / "observaciones.csv", parse_dates=["fecha", "fecha_fin_periodo"]
    )[COLUMNAS_OBSERVACION]

    esperado = {
        "dim_gobierno": len(gobiernos),
        "dim_evento": len(eventos),
        "dim_indicador": len(indicadores),
        "fact_observacion": len(observaciones),
        "dim_zona": len(zonas),
        "fact_internacional": len(internacional),
        "dim_explicacion": len(explicaciones),
    }

    try:
        # El bloque "with" abre una transacción: si termina sin error hace COMMIT;
        # si sale por una excepción hace ROLLBACK automáticamente.
        with psycopg.connect(**get_pg_params()) as conexion, conexion.cursor() as cursor:
            cursor.execute((ROOT_DIR / "sql" / "01_schema.sql").read_text(encoding="utf-8"))
            cursor.execute((ROOT_DIR / "sql" / "02_views.sql").read_text(encoding="utf-8"))
            log.info("Esquema economia y vistas verificados")

            # Un solo TRUNCATE para todas las tablas: PostgreSQL acepta vaciar
            # juntas tablas relacionadas por claves foráneas sin usar CASCADE.
            cursor.execute(
                "TRUNCATE economia.fact_observacion, economia.dim_indicador, "
                "economia.dim_gobierno, economia.dim_evento, economia.fact_internacional, "
                "economia.dim_zona, economia.dim_explicacion"
            )

            # Orden: primero las dimensiones, después los hechos que las referencian.
            insertar(cursor, "dim_gobierno", gobiernos)
            insertar(cursor, "dim_indicador", indicadores)
            insertar(cursor, "dim_evento", eventos)
            insertar(cursor, "fact_observacion", observaciones)
            insertar(cursor, "dim_zona", zonas)
            insertar(cursor, "fact_internacional", internacional)
            insertar(cursor, "dim_explicacion", explicaciones)

            # Verificación antes del COMMIT: si algo no cuadra, se revierte todo.
            for tabla, filas_esperadas in esperado.items():
                cursor.execute(f"SELECT count(*) FROM economia.{tabla}")
                filas_cargadas = cursor.fetchone()[0]
                if filas_cargadas != filas_esperadas:
                    raise RuntimeError(
                        f"{tabla}: se esperaban {filas_esperadas} filas y hay {filas_cargadas}"
                    )
            log.info("Conteos verificados. Confirmando la transacción (COMMIT)")

    except psycopg.Error as e:
        # Los mensajes de psycopg no incluyen la clave, solo host, base y usuario.
        log.error("Error de PostgreSQL, no se cargó nada: %s", e)
        return 1
    except RuntimeError as e:
        log.error("Verificación fallida, no se cargó nada: %s", e)
        return 1

    log.info("Carga completa: %s", esperado)
    return 0


if __name__ == "__main__":
    sys.exit(main())
