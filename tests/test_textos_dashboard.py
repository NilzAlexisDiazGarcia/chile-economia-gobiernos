"""Los textos del dashboard no deben tener caracteres de control.

Un reemplazo con la secuencia "\\1" sin cadena cruda convirtió dígitos en el carácter U+0001,
que Power BI muestra como un cuadro (por ejemplo, "4,□ %" en vez de "4,3 %").

Ejecutar desde la raíz del repositorio:
    python -m pytest -v
"""
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
DASHBOARD = RAIZ / "dashboard"
ARCHIVOS = sorted(
    [DASHBOARD / "generador" / "generar_paginas.py"]
    + list((DASHBOARD / "chile_economia.Report" / "definition").rglob("*.json"))
    + list((DASHBOARD / "chile_economia.SemanticModel" / "definition").rglob("*.tmdl"))
)
# Caracteres de control, salvo tabulación y saltos de línea, y su forma escapada en JSON.
CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]|\\u000[0-8bcef]|\\u001[0-9a-f]", re.IGNORECASE)


def test_hay_archivos_que_revisar():
    assert len(ARCHIVOS) > 10


@pytest.mark.parametrize("ruta", ARCHIVOS, ids=lambda r: str(r.relative_to(DASHBOARD)))
def test_sin_caracteres_de_control(ruta):
    texto = ruta.read_text(encoding="utf-8")
    hallados = [texto[max(m.start() - 30, 0):m.end() + 5] for m in CONTROL.finditer(texto)]
    assert not hallados, hallados[:3]
