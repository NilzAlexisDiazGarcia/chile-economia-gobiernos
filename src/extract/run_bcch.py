"""Extrae todas las series del Banco Central definidas en config/series.yaml.

Uso (desde la raíz del repositorio):
    python -m src.extract.run_bcch

Resultado:
    data/raw/bcch/<indicador>_<fecha>.json   respuesta cruda de la API, sin modificar
    logs/extraccion_bcch.log                 registro de cada ejecución
"""
import logging
import sys

import yaml

from src.config import CONFIG_DIR, LOGS_DIR
from src.extract.bcch import BCChClient, BCChError, guardar_crudo


def configurar_log() -> logging.Logger:
    LOGS_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        handlers=[
            logging.FileHandler(LOGS_DIR / "extraccion_bcch.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("extraccion_bcch")


def main() -> int:
    log = configurar_log()
    config = yaml.safe_load((CONFIG_DIR / "series.yaml").read_text(encoding="utf-8"))
    desde = config["periodo_extraccion"]["desde"]
    hasta = config["periodo_extraccion"]["hasta"]

    cliente = BCChClient()
    errores = 0

    for indicador, meta in config["bcch"].items():
        try:
            datos = cliente.obtener_serie(meta["codigo"], desde, hasta)
            obs = datos["Series"]["Obs"]
            if not obs:
                raise BCChError("la serie no devolvió observaciones")
            ruta = guardar_crudo(datos, indicador)
            log.info(
                "OK    %-12s %-34s %5d obs  %s -> %s  (%s)",
                indicador, meta["codigo"], len(obs),
                obs[0]["indexDateString"], obs[-1]["indexDateString"], ruta.name,
            )
        except (BCChError, KeyError) as e:
            # Un indicador que falla no detiene a los demás; se registra y se sigue.
            errores += 1
            log.error("FALLA %-12s %-34s %s", indicador, meta["codigo"], e)

    log.info("Fin: %d series, %d errores", len(config["bcch"]), errores)
    return 1 if errores else 0   # código de salida distinto de 0 = algo falló


if __name__ == "__main__":
    sys.exit(main())
