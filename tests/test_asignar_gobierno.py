"""Tests de la regla de asignación por mayoría de días.

Ejecutar desde la raíz del repositorio:
    python -m pytest -v
"""
import pandas as pd
import pytest

from src.transform.asignar_gobierno import (
    agregar_fin_periodo,
    asignar_gobierno,
    cargar_gobiernos,
)

GOBIERNOS = cargar_gobiernos()
ID = dict(zip(GOBIERNOS["etiqueta"], GOBIERNOS["id_gobierno"]))


def asignar(fecha: str, frecuencia: str) -> pd.Series:
    """Asigna una sola observación y devuelve su fila."""
    df = pd.DataFrame({"fecha": [pd.Timestamp(fecha)], "frecuencia": [frecuencia]})
    return asignar_gobierno(agregar_fin_periodo(df), GOBIERNOS).iloc[0]


# (fecha, frecuencia, gobierno esperado, es_transicion esperado)
CASOS = [
    # Diario: asignación exacta. El 11 de marzo ya es del gobierno entrante.
    ("2010-03-10", "DAILY", "Bachelet I", False),
    ("2010-03-11", "DAILY", "Piñera I", False),
    # Mensual: marzo = 10 días del saliente, 21 del entrante.
    ("2010-02-01", "MONTHLY", "Bachelet I", False),
    ("2010-03-01", "MONTHLY", "Piñera I", True),
    ("2010-04-01", "MONTHLY", "Piñera I", False),
    # Trimestral: T1 = ~69 días del saliente, 21 del entrante.
    ("2010-01-01", "QUARTERLY", "Bachelet I", True),
    ("2010-04-01", "QUARTERLY", "Piñera I", False),
    # Anual: ~69 días del saliente, ~296 del entrante.
    ("2010-01-01", "ANNUAL", "Piñera I", True),
    ("2009-01-01", "ANNUAL", "Bachelet I", False),
    # Bordes del alcance del proyecto.
    ("2006-01-01", "QUARTERLY", "Lagos", True),
    ("2006-03-01", "MONTHLY", "Bachelet I", True),
    ("2026-03-01", "MONTHLY", "Kast", True),
    ("2026-01-01", "QUARTERLY", "Boric", True),
]


@pytest.mark.parametrize("fecha, frecuencia, gobierno, transicion", CASOS)
def test_regla_mayoria_de_dias(fecha, frecuencia, gobierno, transicion):
    fila = asignar(fecha, frecuencia)
    assert fila["id_gobierno"] == ID[gobierno]
    assert fila["es_transicion"] == transicion


def test_dias_del_periodo_suman_correctamente():
    fila = asignar("2010-03-01", "MONTHLY")
    assert fila["dias_periodo"] == 31
    assert fila["dias_gobierno"] == 21   # del 11 al 31 de marzo


def test_fecha_fuera_de_todo_gobierno_falla():
    with pytest.raises(ValueError, match="fuera de todo gobierno"):
        asignar("1990-01-01", "MONTHLY")


def test_frecuencia_desconocida_falla():
    df = pd.DataFrame({"fecha": [pd.Timestamp("2010-01-01")], "frecuencia": ["WEEKLY"]})
    with pytest.raises(ValueError, match="Frecuencias sin regla"):
        agregar_fin_periodo(df)
