"""Cliente de la API de la Base de Datos Estadísticos (BDE) del Banco Central de Chile.

La API tiene dos funciones que usamos:
- SearchSeries: lista las series disponibles para una frecuencia.
- GetSeries:    devuelve las observaciones de una serie entre dos fechas.

Particularidad importante: la API responde HTTP 200 incluso cuando hay un error
(por ejemplo, credenciales inválidas). El resultado real viene en el campo
"Codigo" del JSON: 0 significa éxito; cualquier otro valor es un error.
"""
import json
from datetime import date
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import RAW_DIR, get_bcch_credentials

BASE_URL = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"
FRECUENCIAS_VALIDAS = {"DAILY", "MONTHLY", "QUARTERLY", "ANNUAL"}


class BCChError(Exception):
    """Error al consultar la API del Banco Central."""


class BCChClient:
    def __init__(self, timeout: int = 30):
        self.user, self.password = get_bcch_credentials()
        self.timeout = timeout
        self.session = self._crear_sesion()

    @staticmethod
    def _crear_sesion() -> requests.Session:
        """Sesión HTTP con reintentos automáticos ante fallas temporales."""
        reintentos = Retry(
            total=3,                                  # hasta 3 reintentos
            backoff_factor=2,                         # espera 2, 4, 8 segundos
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        sesion = requests.Session()
        sesion.mount("https://", HTTPAdapter(max_retries=reintentos))
        return sesion

    def _consultar(self, params: dict) -> dict:
        """Hace la petición GET y valida la respuesta. Nunca expone la clave."""
        params = {"user": self.user, "pass": self.password, **params}
        try:
            respuesta = self.session.get(BASE_URL, params=params, timeout=self.timeout)
            respuesta.raise_for_status()
            datos = respuesta.json()
        except requests.RequestException as e:
            # Los mensajes de requests incluyen la URL completa, y la API exige
            # la clave en la URL. Por eso NO propagamos el error original
            # ("from None"): solo su tipo, que no contiene datos sensibles.
            raise BCChError(f"Fallo de conexión con la API ({type(e).__name__})") from None
        except ValueError:
            raise BCChError("La API no devolvió un JSON válido") from None

        if datos.get("Codigo") != 0:
            raise BCChError(
                f"La API respondió con error {datos.get('Codigo')}: {datos.get('Descripcion')}"
            )
        return datos

    def buscar_series(self, frecuencia: str) -> pd.DataFrame:
        """Catálogo de todas las series disponibles para una frecuencia."""
        frecuencia = frecuencia.upper()
        if frecuencia not in FRECUENCIAS_VALIDAS:
            raise ValueError(f"Frecuencia inválida: {frecuencia}. Usa {FRECUENCIAS_VALIDAS}")
        datos = self._consultar({"function": "SearchSeries", "frequency": frecuencia})
        return pd.DataFrame(datos.get("SeriesInfos", []))

    def obtener_serie(self, codigo: str, desde: str, hasta: str | None = None) -> dict:
        """Respuesta cruda de GetSeries para una serie. Fechas en formato AAAA-MM-DD."""
        params = {"function": "GetSeries", "timeseries": codigo, "firstdate": desde}
        if hasta:
            params["lastdate"] = hasta
        return self._consultar(params)


def guardar_crudo(datos: dict, nombre: str, carpeta: Path = RAW_DIR / "bcch") -> Path:
    """Guarda la respuesta tal cual llegó, con la fecha de descarga en el nombre."""
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{nombre}_{date.today().isoformat()}.json"
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta
