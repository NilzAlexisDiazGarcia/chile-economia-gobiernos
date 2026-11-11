"""Tests de consistencia de las metas fiscales (data/reference/metas_fiscales.csv).

Ejecutar desde la raíz del repositorio:
    python -m pytest -v
"""
import pandas as pd
import pytest

from src.config import REFERENCE_DIR
from src.transform.asignar_gobierno import cargar_gobiernos

METAS = pd.read_csv(REFERENCE_DIR / "metas_fiscales.csv")
GOBIERNOS = cargar_gobiernos()


def test_un_registro_por_gobierno_en_alcance():
    en_alcance = set(GOBIERNOS.loc[GOBIERNOS["en_alcance"], "id_gobierno"])
    assert set(METAS["id_gobierno"]) == en_alcance
    assert METAS["id_gobierno"].is_unique


@pytest.mark.parametrize("fila", METAS.to_dict("records"), ids=lambda f: str(f["id_gobierno"]))
def test_cumplimiento_coincide_con_las_cifras(fila):
    """Cumplir la meta significa un balance estructural igual o mejor que la meta."""
    cumple = fila["resultado"] >= fila["meta_vigente"]
    assert (fila["cumple_meta_vigente"] == "Sí") == cumple


@pytest.mark.parametrize("fila", METAS.to_dict("records"), ids=lambda f: str(f["id_gobierno"]))
def test_anio_evaluado_es_el_ultimo_completo_del_gobierno(fila):
    """El año evaluado es el anterior al cambio de mando: el último año completo del gobierno."""
    fin = GOBIERNOS.loc[GOBIERNOS["id_gobierno"] == fila["id_gobierno"], "fecha_fin"].iloc[0]
    assert fila["anio_evaluado"] == fin.year - 1


def test_cada_meta_tiene_fuente_con_enlace():
    assert METAS["url"].str.startswith("http").all()
    assert METAS[["decreto_inicial", "meta_inicial", "explicacion", "fuente"]].notna().all().all()
