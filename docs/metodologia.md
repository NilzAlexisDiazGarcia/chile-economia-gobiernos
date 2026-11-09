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

## 5. Métricas del análisis SQL

| Métrica | Definición | Por qué |
|---|---|---|
| Variación a 12 meses | `valor / valor del mismo período del año anterior − 1` | Compara meses o trimestres equivalentes, así la estacionalidad se cancela |
| Valor heredado | Último dato del gobierno anterior | Es el punto de partida que recibió cada gobierno |
| Cambio vs. heredado | Valor final − valor heredado | Mide el cambio durante todo el mandato, no desde el primer dato propio |
| Promedio sin transición | Igual que el promedio, excluyendo los períodos que comparten dos gobiernos | Muestra si los períodos compartidos alteran el resultado |

Para los niveles (PIB, IMACEC, cobre) se comparan **tasas de variación**, nunca promedios
de nivel, porque el nivel crece con el tiempo y siempre favorecería al gobierno más
reciente.

**Limitaciones conocidas de las consultas:**

- **Eventos superpuestos:** la ventana del estallido social (octubre 2019 a septiembre 2020)
  incluye el inicio de la pandemia. Sus efectos no se pueden separar con estos datos.
- **Efecto base:** después de una caída fuerte, la variación a 12 meses del año siguiente
  sale muy alta solo porque se compara contra un mes deprimido (por ejemplo, 2021 contra 2020).
- **Desfase en el último gobierno:** con desfase de 6 o 12 meses, los meses finales de
  Boric todavía no tienen datos publicados, así que su promedio usa menos meses.

## 6. Neutralidad

- Los mismos indicadores, reglas y fuentes para los cinco gobiernos.
- Solo estadísticas descriptivas, sin juicios de valor ni conclusiones causales.
- Las limitaciones quedan documentadas en este archivo.
