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

## 4. Fuente de la inflación

Se usa la variación a 12 meses del IPC **oficial publicada por el INE** (serie
`F074.IPC.IND.Z.EP09.C.M` de la BDE), y no el empalme del Banco Central a la canasta de
2023. El empalme modifica la variación anual en los años de cambio de base del IPC, hasta
en 1,3 pp. La meta del Banco Central se evalúa contra la cifra oficial. La auditoría de
datos (`python -m src.analysis.auditoria`) contrasta la serie con cifras publicadas por el
INE.

## 5. Contexto

Los eventos de `data/reference/eventos.csv` y el precio del cobre se muestran junto a los
indicadores como contexto. El análisis no estima cuánto de cada resultado se debe a
estos factores.

**Comparación con pares** (detalle en [contexto_comparado.md](contexto_comparado.md)):

- **Fuentes:** datos anuales del FMI (World Economic Outlook, octubre de 2026) y del Banco
  Mundial (control de la corrupción, WGI).
- **Pares:** Perú, Colombia, México y Brasil, países de la región con metas de inflación.
  Se usa su promedio simple.
- **Asignación anual:** cada año va al gobierno que gobernó la mayor parte de él, con la
  misma regla de mayoría de días. Por eso las cifras anuales de Chile difieren levemente de
  las mensuales: por ejemplo, el crecimiento de Bachelet II es 1,80 % con datos anuales y
  1,90 % con datos trimestrales.
- **Lo que no se compara:**
  - El desempleo entre países, porque cada país lo mide distinto.
  - La inflación contra el agregado de América Latina, que distorsionan Argentina y
    Venezuela.
- **Deuda y balance:** el FMI los mide para el gobierno general, y el resto del proyecto
  para el Gobierno Central.
- **Explicaciones oficiales:** `data/reference/explicaciones.csv` reúne citas textuales del
  Banco Central y del FMI, con su fuente y enlace. Explican cada período en palabras de
  esas instituciones, no del autor.

**Balance de cada gobierno** (vista `v_pbi_evaluacion`, detalle en [metas_fiscales.md](metas_fiscales.md)):

- **Ocho criterios uniformes,** cada uno favorable si cumple una referencia fijada de antemano:
  - Crecimiento sobre el promedio de los pares.
  - Inflación en el rango meta la mayoría de los meses.
  - Desempleo entregado menor que el recibido.
  - Balance estructural del último año completo igual o mejor que la meta vigente.
  - Deuda neta entregada igual o menor que la recibida.
  - FEES, el fondo para crisis, entregado igual o mayor que el recibido. No se usa el total de
    los fondos soberanos porque el FRP recibe aportes obligatorios por ley y solo financia
    pensiones, y porque un fondo puede crecer con deuda: la solvencia se mide con la deuda
    neta, que descuenta estos activos de la deuda bruta.
  - Pobreza por ingresos entregada menor que la recibida (CASEN, serie comparable).
  - Salario real con variación anual promedio positiva.
- **La meta fiscal se compara con la del propio gobierno:** la vigente al final y la de su
  decreto inicial. Las cifras son de la DIPRES con la metodología actual (2006–2021) y del
  CFA (2022–2025).
- **Cada criterio indica quién lo controla principalmente:** el gobierno, el Banco Central o
  una mezcla con el ciclo y el contexto externo.
- **No hay puntaje total,** porque los criterios no son comparables entre sí.

## 6. Métricas del análisis SQL

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
- **Pocos datos por gobierno:** cada gobierno tiene cuatro años. Las diferencias de
  crecimiento entre varios de ellos son menores que su incertidumbre (sección 1 de
  [hallazgos.md](hallazgos.md)), y por eso el reporte no ordena a los gobiernos.
- **Desempleo en trimestres móviles:** el INE mide el desempleo en promedios móviles de tres
  meses, así que el dato de cada mes refleja también los dos anteriores. La encuesta cambió
  de metodología en 2010 y se recalibró en 2020; se usa la serie histórica empalmada.
- **Balance estructural:** su metodología de cálculo cambió durante el período. Se usa la
  serie que publica la DIPRES.
- **Cobre y dólar en términos nominales:** los niveles de períodos distantes no son
  directamente comparables; las variaciones sí.

- **PIB por habitante:** se calcula con el crecimiento del PIB y de la población del FMI,
  porque la inmigración de 2015–2019 elevó el crecimiento de la población.
- **Pobreza:** la CASEN se mide cada dos o tres años. Cada medición se asigna al gobierno del
  año de la encuesta, y se usa la serie comparable (metodología de 2013).

**Extensiones posibles, fuera del alcance actual:**

| Extensión | Para qué serviría | Disponibilidad |
|---|---|---|
| Tipo de cambio real | Medir competitividad, descontando la inflación de Chile y del exterior | Serie `F073.TCR.IND.199101.M` en la BDE |
| Cobre en dólares reales | Comparar niveles entre períodos distantes | Requiere el IPC de EE.UU. |
| Inversión (formación bruta de capital fijo) | El FMI atribuye la desaceleración de 2014 a su caída | Cuentas nacionales en la BDE |
| Desigualdad y pobreza multidimensional | Completar la medición del bienestar | Encuesta CASEN |
| Contrafactual formal (control sintético) | Estimar qué habría pasado sin cada gobierno | Requiere un panel amplio de países |

## 7. Neutralidad

- Los mismos indicadores, reglas y fuentes para los cinco gobiernos.
- Solo estadísticas descriptivas, sin juicios de valor ni conclusiones causales.
- Las limitaciones quedan documentadas en este archivo.
