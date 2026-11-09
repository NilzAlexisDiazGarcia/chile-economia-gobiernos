"""Asigna cada observación al gobierno que gobernó la mayoría de los días de su período.

Regla (ver docs/metodologia.md):
- Cada observación representa un período [fecha, fecha_fin_periodo), con fin exclusivo.
- Se cuentan los días de ese período que caen dentro de cada gobierno.
- Gana el gobierno con más días. Con períodos de hasta un año y cambios de mando
  cada 4 años, un período toca como máximo dos gobiernos, así que "más días" es
  siempre "mayoría". No hay empates: marzo se reparte 10/21 días, el primer
  trimestre 69-70/21 y el año 69-70/295-296.
- Si el período toca más de un gobierno, se marca es_transicion = True.
"""
import pandas as pd

from src.config import REFERENCE_DIR

# Cuánto dura cada período según su frecuencia. La API fecha cada observación con
# el PRIMER día del período (ej.: el IMACEC de marzo 2010 viene como 01-03-2010).
DURACION_PERIODO = {
    "DAILY": pd.Timedelta(days=1),     # duración fija: Timedelta basta

    "MONTHLY": pd.DateOffset(months=1),
    "QUARTERLY": pd.DateOffset(months=3),
    "ANNUAL": pd.DateOffset(years=1),
}


def cargar_gobiernos() -> pd.DataFrame:
    """Lee la tabla de referencia de gobiernos, ordenada cronológicamente."""
    gobiernos = pd.read_csv(
        REFERENCE_DIR / "gobiernos.csv", parse_dates=["fecha_inicio", "fecha_fin"]
    )
    return gobiernos.sort_values("fecha_inicio").reset_index(drop=True)


def agregar_fin_periodo(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega la columna fecha_fin_periodo (exclusiva) según la frecuencia de cada fila."""
    desconocidas = set(df["frecuencia"]) - set(DURACION_PERIODO)
    if desconocidas:
        raise ValueError(f"Frecuencias sin regla de duración: {desconocidas}")

    df = df.copy()
    df["fecha_fin_periodo"] = pd.NaT
    for frecuencia, duracion in DURACION_PERIODO.items():
        filas = df["frecuencia"] == frecuencia
        if not filas.any():
            continue
        df.loc[filas, "fecha_fin_periodo"] = df.loc[filas, "fecha"] + duracion
    df["fecha_fin_periodo"] = pd.to_datetime(df["fecha_fin_periodo"])
    return df


def asignar_gobierno(df: pd.DataFrame, gobiernos: pd.DataFrame) -> pd.DataFrame:
    """Agrega id_gobierno, dias_gobierno, dias_periodo y es_transicion.

    Requiere las columnas fecha y fecha_fin_periodo.
    """
    df = df.copy()
    inicio, fin = df["fecha"], df["fecha_fin_periodo"]

    # Matriz de días: una fila por observación, una columna por gobierno.
    # Días de intersección entre [inicio, fin) y [inicio_gob, fin_gob):
    #     max(0, min(fin, fin_gob) - max(inicio, inicio_gob))
    dias = pd.DataFrame(index=df.index)
    for gob in gobiernos.itertuples():
        inicio_comun = inicio.where(inicio > gob.fecha_inicio, gob.fecha_inicio)
        fin_comun = fin.where(fin < gob.fecha_fin, gob.fecha_fin)
        dias[gob.id_gobierno] = (fin_comun - inicio_comun).dt.days.clip(lower=0)

    sin_gobierno = dias.max(axis=1) == 0
    if sin_gobierno.any():
        fechas = df.loc[sin_gobierno, "fecha"].dt.date.unique()[:5]
        raise ValueError(f"Hay observaciones fuera de todo gobierno, ej.: {fechas}")

    df["id_gobierno"] = dias.idxmax(axis=1).astype(int)
    df["dias_gobierno"] = dias.max(axis=1).astype(int)
    df["dias_periodo"] = (fin - inicio).dt.days
    df["es_transicion"] = (dias > 0).sum(axis=1) > 1
    return df
