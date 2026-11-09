"""Configuración central del proyecto: rutas y credenciales.

Las credenciales se leen desde variables de entorno (archivo .env),
nunca se escriben en el código.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Raíz del repositorio: este archivo está en src/, así que subimos un nivel.
ROOT_DIR = Path(__file__).resolve().parent.parent

# Carga el archivo .env (si existe) en las variables de entorno del proceso.
load_dotenv(ROOT_DIR / ".env")

# Rutas del proyecto
CONFIG_DIR = ROOT_DIR / "config"
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REFERENCE_DIR = DATA_DIR / "reference"
LOGS_DIR = ROOT_DIR / "logs"


def get_required_env(name: str) -> str:
    """Devuelve una variable de entorno obligatoria o falla con un mensaje claro."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Falta la variable de entorno {name}. "
            "Copia .env.example como .env y completa los valores."
        )
    return value


def get_bcch_credentials() -> tuple[str, str]:
    """Credenciales de la API del Banco Central (usuario, clave)."""
    return get_required_env("BCCH_USER"), get_required_env("BCCH_PASS")
