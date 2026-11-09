# Metodología

## 1. Períodos de gobierno

El cambio de mando presidencial ocurre el 11 de marzo. En `data/reference/gobiernos.csv`,
`fecha_inicio` es **inclusiva** y `fecha_fin` es **exclusiva**: el 11 de marzo pertenece
al gobierno entrante.

La tabla también incluye el gobierno anterior (Lagos) y el siguiente (Kast) con
`en_alcance = false`. Así, **toda** observación queda asignada a un gobierno (incluido el
año base 2005 y los datos posteriores al 2026-03-10), y el filtro de alcance se aplica de
forma explícita en el análisis, en vez de descartar filas en silencio durante la limpieza.

## 2. Asignación de datos a gobiernos

| Frecuencia | Regla |
|---|---|
| Diaria | Asignación exacta según la fecha |
| Mensual, trimestral y anual | Se asigna al gobierno que gobernó **la mayoría de los días** del período |

En la práctica:

- Marzo (10 días del saliente, 21 del entrante): gobierno **entrante**.
- Primer trimestre (unos 69 de 90 días del saliente): gobierno **saliente**.
- Año de transición (unos 70 días del saliente, 295 del entrante): gobierno **entrante**.

Todo período que contiene un 11 de marzo de cambio de mando se marca con
`es_transicion = true`, para poder excluirlo del análisis.

## 3. Rezago de las políticas

Que un dato caiga dentro de un gobierno **no significa** que sea consecuencia de sus
decisiones. No existe un rezago único; depende del instrumento:

| Canal | Rezago aproximado | Observación |
|---|---|---|
| Expectativas (tipo de cambio, bolsa) | Inmediato o anticipado | Los mercados pueden reaccionar a la elección (diciembre), antes de la asunción |
| Política fiscal | ~10 meses o más | El primer año de cada gobierno se ejecuta con la Ley de Presupuestos aprobada por el gobierno anterior |
| Política monetaria (TPM) | 12–24 meses sobre la inflación | La TPM la decide el Banco Central, que es **autónomo** del gobierno |
| Reformas estructurales | Varios años | Su efecto puede extenderse a gobiernos posteriores |

**Decisión:** la asignación de datos no se modifica por el rezago. En el dashboard se
agregará un parámetro de desfase (0, 6 o 12 meses) para ver cómo cambian las
comparaciones según el supuesto de rezago, sin imponer uno.

## 4. Contexto

Los eventos de `data/reference/eventos.csv` y el precio del cobre se muestran junto a los
indicadores como contexto. El análisis no estima cuánto de cada resultado se debe a
estos factores.

## 5. Neutralidad

- Los mismos indicadores, reglas y fuentes para los cinco gobiernos.
- Solo estadísticas descriptivas, sin juicios de valor ni conclusiones causales.
- Las limitaciones quedan documentadas en este archivo.
