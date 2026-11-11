"""Tests de los datos internacionales y de su asignación a gobiernos.

Ejecutar desde la raíz del repositorio:
    python -m pytest -v
"""
import pandas as pd
import pytest

from src.config import PROCESSED_DIR, REFERENCE_DIR
from src.load.postgres import asignar_gobierno_anual
from src.transform.asignar_gobierno import cargar_gobiernos

GOBIERNOS = cargar_gobiernos()
ID = dict(zip(GOBIERNOS["etiqueta"], GOBIERNOS["id_gobierno"]))
ARCHIVO = PROCESSED_DIR / "internacional.csv"


# El cambio de mando es el 11 de marzo: el gobierno entrante tiene ~295 días del año.
@pytest.mark.parametrize("anio, gobierno", [
    (2009, "Bachelet I"),
    (2010, "Piñera I"),
    (2013, "Piñera I"),
    (2014, "Bachelet II"),
    (2018, "Piñera II"),
    (2021, "Piñera II"),
    (2022, "Boric"),
    (2025, "Boric"),
    (2026, "Kast"),
])
def test_asignacion_anual(anio, gobierno):
    asignado = asignar_gobierno_anual(pd.DataFrame({"anio": [anio]}), GOBIERNOS)[0]
    assert asignado == ID[gobierno]


def test_cada_gobierno_en_alcance_tiene_cuatro_anios():
    anios = pd.DataFrame({"anio": range(2006, 2026)})
    anios["id_gobierno"] = asignar_gobierno_anual(anios, GOBIERNOS)
    en_alcance = GOBIERNOS.loc[GOBIERNOS["en_alcance"], "id_gobierno"]
    conteo = anios["id_gobierno"].value_counts()
    assert all(conteo[i] == 4 for i in en_alcance)


@pytest.fixture(scope="module")
def internacional():
    if not ARCHIVO.exists():
        pytest.skip("Falta data/processed/internacional.csv: ejecuta src.extract.internacional")
    return pd.read_csv(ARCHIVO)


def test_sin_duplicados(internacional):
    assert not internacional.duplicated(["indicador", "zona", "anio"]).any()


def test_zonas_conocidas(internacional):
    zonas = set(pd.read_csv(REFERENCE_DIR / "zonas.csv")["zona"])
    assert set(internacional["zona"]) <= zonas


def test_chile_completo_en_el_periodo(internacional):
    """Chile debe tener dato en todos los años 2006-2025 de cada indicador."""
    chile = internacional[internacional["zona"] == "CHL"]
    for indicador, grupo in chile.groupby("indicador"):
        faltan = set(range(2006, 2026)) - set(grupo["anio"])
        assert not faltan, f"{indicador}: faltan los años {sorted(faltan)}"


def test_rangos_plausibles(internacional):
    """Valores fuera de estos rangos indican un error de extracción o de unidad."""
    rangos = {
        "crecimiento_pib": (-40, 50),
        "inflacion_promedio": (-5, 500),
        "desempleo": (0, 40),
        "deuda_gobierno_general": (0, 250),
        "balance_gobierno_general": (-30, 30),
        "control_corrupcion": (-2.5, 2.5),
    }
    for indicador, (minimo, maximo) in rangos.items():
        valores = internacional.loc[internacional["indicador"] == indicador, "valor"]
        assert valores.between(minimo, maximo).all(), indicador


def test_explicaciones_con_fuente_y_url():
    explicaciones = pd.read_csv(REFERENCE_DIR / "explicaciones.csv")
    assert explicaciones["id_explicacion"].is_unique
    assert explicaciones[["cita", "fuente", "url"]].notna().all().all()
    assert explicaciones["url"].str.startswith("https://").all()
    assert explicaciones["anio"].between(2006, 2025).all()
