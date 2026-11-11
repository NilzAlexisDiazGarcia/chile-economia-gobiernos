# Metas fiscales y arcas fiscales por gobierno

> Los datos están en `data/reference/metas_fiscales.csv` y alimentan la página "Balance de
> cada gobierno" del dashboard.

## Por qué este criterio

La regla fiscal chilena obliga a cada gobierno a publicar, al asumir, un decreto con su
**meta de balance estructural**: cuánto déficit o superávit se compromete a tener una vez
descontado el efecto del ciclo económico y del precio del cobre. Es el único indicador en
que cada gobierno fijó su propia vara. Por eso es la forma más neutral de evaluar su gestión
fiscal: se lo compara con **lo que él mismo prometió**, no con un criterio del autor.

**Regla aplicada a los cinco gobiernos por igual:** se compara el balance estructural del
**último año completo** de cada gobierno con la meta que su decreto fijaba para ese año o
para el fin del período. Se informan la meta inicial, las modificaciones posteriores y el
motivo oficial de cada cambio.

## Metas y resultados

Cifras de balance estructural de la DIPRES, con la **metodología actual** para todos los
años: *Cumplimiento de las metas de regla fiscal en Chile: revisión histórica* (diciembre de
2022). Para 2022–2025 se usan las del Consejo Fiscal Autónomo (CFA) y la DIPRES. Se evalúa
contra dos referencias: **la meta vigente**, después de las modificaciones, y **la meta del
decreto inicial**, la que cada gobierno fijó al asumir. La meta inicial se evalúa solo cuando
el decreto fijaba un valor para ese mismo año: para Bachelet I (1 % cada año), Piñera II
(−1,2 % para 2021, por la senda de 0,2 pp por año) y Boric (−1,05 % para 2025, por la senda
de 0,75 pp por año). Piñera I y Bachelet II la fijaron para el año siguiente a su último año
completo (2014 y 2018), así que no se les asigna un "cumplió" o "no cumplió".

| Gobierno | Decreto inicial y su meta | Modificaciones | Último año completo: meta vigente → resultado | Cumplió la meta vigente | Cumplió la meta inicial |
|---|---|---|---|---|---|
| Bachelet I | Decreto 1259 (2006): superávit de 1 % del PIB al año | 0,5 % para 2008; 0 % por la crisis (2009) | 2009: 0 % → **−3,4 %** | No | No |
| Piñera I | Decreto 637 (junio de 2010): equilibrio (0 %) en 2014 (fin del período) | Decreto 1.357 (octubre de 2011): converger a −1 % en 2014, tras la corrección metodológica de la Comisión Corbo | 2013: −1 % (senda) → **−0,5 %** | **Sí** | No aplica: su meta era para 2014 |
| Bachelet II | Decreto 892 (2014): equilibrio (0 %) en 2018 | Decreto 1.378 (octubre de 2015): bajar el déficit 0,25 pp por año, hasta −0,8 % en 2018, por el menor precio del cobre y el menor crecimiento | 2017: senda de −1,05 % → **−2,0 %** | No | No aplica: su meta era para 2018 |
| Piñera II | Decreto 743 (julio de 2018): de −1,8 % en 2018 a −1 % en 2022 (−1,2 % para 2021) | Decreto 253 (marzo de 2020): −2,5 % para 2021. Decreto 1.579 (septiembre de 2020): −4,7 % para 2021, por la pandemia | 2021: −4,7 % → **−10,7 %** | No (cláusula de escape "de facto") | No |
| Boric | Decreto de 2022: de −3,3 % en 2022 a −0,3 % en 2026 (−0,75 pp por año) | Decreto de 2024: −1,9 % para 2024, −1,1 % para 2025 y −0,5 % para 2026. Modificación de 2025: −1,6 % para 2025 | 2025: −1,6 % → **−3,6 %** | No | No |

**Año por año, con la meta vigente** (DIPRES y CFA):

| Gobierno | Años en que cumplió | Años en que no cumplió |
|---|---|---|
| Bachelet I | 2006, 2007 | 2008, 2009 |
| Piñera I | 2011, 2012, 2013 | 2010 (año del terremoto) |
| Bachelet II | 2014, 2015, 2016 | 2017 |
| Piñera II | 2018, 2019, 2020 | 2021 |
| Boric | 2022 | 2024, 2025; 2023 en disputa* |

(\*) **2023:** el decreto fijaba −2,1 % y el resultado fue −2,7 %. Hacienda sostiene que la
cumplió, porque compara contra la meta actualizada en su informe de finanzas públicas.

**Conclusiones verificables:**

1. **Con la meta vigente al final del período, solo Piñera I cumplió.** Su meta se había
   modificado al inicio del gobierno, cuando la Comisión Corbo corrigió la forma de medir el
   balance y el déficit de 2009 pasó de −1,2 % a −3,1 %.
2. **Con la meta del decreto inicial, ninguno de los tres que la fijaron para su último año
   cumplió** (Bachelet I, Piñera II y Boric). Según la DIPRES, en 21 años de regla fiscal se
   cumplió la meta vigente en 14 años, pero la meta inicial de cada gobierno solo en 9. El
   Diario Financiero cuenta a Piñera I como el único que cumplió su meta inicial, porque toma
   como inicial el −1 % del Decreto 1.357 de 2011; con el Decreto 637 de 2010, la meta era el
   equilibrio en 2014.
3. **Todos los gobiernos modificaron su meta.** La DIPRES advierte que, sin cláusulas de
   escape formales, las metas "han sido modificadas a discreción de la autoridad".

## Por qué no se cumplieron, según las fuentes oficiales

| Gobierno | Explicación oficial (DIPRES y CFA) | ¿Hubo un shock extraordinario? |
|---|---|---|
| Bachelet I | 2008: gasto por sobre lo presupuestado, para fortalecer la inversión pública, compensar la inflación a los más vulnerables y atender emergencias. 2009: plan de estímulo fiscal contra la crisis, financiado con el ahorro del FEES acumulado en 2006–2008 | Sí, en 2009: crisis financiera global |
| Piñera I | Cumplió en 2011–2013. En 2010 no cumplió, por el gasto del Plan de Reconstrucción tras el terremoto. Su meta se había flexibilizado en 2011, cuando la corrección metodológica elevó el déficit medido | Sí, en 2010: terremoto |
| Bachelet II | Cumplió en 2014–2016, gracias a ajustes cíclicos amplios. En 2017 no cumplió: menores ingresos estructurales y gasto por sobre lo presupuestado. La meta se había rebajado en 2015 por la caída del cobre y del PIB tendencial | No: deterioro gradual del contexto |
| Piñera II | Cumplió en 2018–2020, con metas modificadas en 2020. En 2021, el mayor déficit estructural desde que existe la regla, por el gasto de la pandemia: una cláusula de escape "de facto", porque la ley no la contemplaba | Sí: estallido social y pandemia |
| Boric | Cumplió en 2022. En 2024 y 2025 no cumplió: según el CFA, por errores reiterados en la proyección de ingresos, gasto por sobre lo comprometido y medidas correctivas poco efectivas; un desvío "elevado en términos históricos para un año sin eventos extraordinarios" | No |

## Arcas fiscales: el ahorro que recibió y el que dejó cada gobierno

Saldos de los fondos soberanos en el último mes completo antes de cada cambio de mando, en
millones de dólares de cada año:

| Gobierno | FEES (fondo para crisis): recibió → dejó | FRP (reserva para pensiones): recibió → dejó | Total: recibió → dejó | Deuda bruta: recibió → dejó (% PIB) | Deuda neta: recibió → dejó (% PIB) |
|---|---|---|---|---|---|
| Bachelet I | — → 11.237 | — → 3.406 | — → 14.643 | 6,4 → 6,5 | −1,6 → −9,8 |
| Piñera I | 11.237 → 15.774 | 3.406 → 7.499 | 14.643 → 23.273 | 6,5 → 12,7 | −9,8 → −6,2 |
| Bachelet II | 15.774 → 14.851 | 7.499 → 10.049 | 23.273 → 24.900 | 12,7 → 23,6 | −6,2 → 5,0 |
| Piñera II | 14.851 → 6.406 | 10.049 → 7.130 | 24.900 → 13.537 | 23,6 → 36,2 | 5,0 → 19,7 |
| Boric | 6.406 → 3.944 | 7.130 → 10.328 | 13.537 → 14.272 | 36,2 → 42,4 | 19,7 → 26,1 |

- **Bachelet I:** los fondos se crearon con la Ley de Responsabilidad Fiscal de 2006, y la serie
  del Banco Central comienza en marzo de 2007, cuando el total era de US$ 7.751
  millones y llegó a US$ 22.718 millones a fines de 2008. En 2009 se usaron unos US$ 9.000
  millones del FEES para enfrentar la crisis.
- **Piñera II:** el FEES bajó de US$ 12.233 millones a fines de 2019 a US$ 2.457 millones a
  fines de 2021, por su uso en la pandemia. Antes del cambio de mando se volvió a
  capitalizar, y llegó a US$ 6.406 millones en febrero de 2022.
- **Boric:** el FEES siguió bajando, de US$ 6.406 a 3.944 millones, sin una crisis, mientras el
  FRP subió. La ley obliga a hacer aportes al FRP y a usarlo para financiar pensiones, así que
  el total de los fondos no muestra cuánto ahorro disponible quedó.

**En porcentaje del PIB,** que es como se evalúa en el balance, el FEES pasó de 4,7 % a 6,2 % con
Bachelet I, de 6,2 % a 6,4 % con Piñera I, de 6,4 % a 4,9 % con Bachelet II, de 4,9 % a 2,2 % con
Piñera II y de 2,2 % a 1,0 % con Boric.

**Cómo leer estas cifras:**
- **Los fondos no se leen solos.** Un fondo puede crecer con plata pedida prestada. Por eso
  la columna clave es la deuda neta, que es la deuda bruta menos los activos financieros del
  Fisco, incluidos estos fondos. Subió en cuatro de los cinco gobiernos.
- **Por eso el balance evalúa el FEES y no el total:** el FEES es el colchón que el gobierno
  puede usar; el FRP sube por aportes obligatorios.
- **Los saldos cambian por depósitos y retiros, y también por la rentabilidad** de las
  inversiones. Una baja no significa siempre un retiro.
- **Usar el FEES en una crisis es su propósito.** Fue creado para eso, así que una baja en
  2009 o en 2020 no es por sí sola una mala gestión.
- **Están en dólares nominales,** y son más comparables como porcentaje del PIB.

## Fuentes

- Biblioteca del Congreso Nacional, *Balance Estructural en Chile: conceptos, evolución e
  institucionalidad* (septiembre de 2021). Incluye las metas y los decretos 637 de 2010, 892
  de 2014, 1378 de 2015 y 743 de 2018.
- Diario Financiero, "Decreto de política fiscal, solo un gobierno ha cumplido con su meta
  inicial desde 2007" (12 de junio de 2026):
  https://www.df.cl/senal-df/factor-economico/decreto-de-politica-fiscal-solo-un-gobierno-ha-cumplido-con-su-meta
- Consejo Fiscal Autónomo, sobre el incumplimiento de la meta de 2025 (4 de marzo de 2026):
  https://cfachile.cl/noticias/-cfa-advierte-que-la-gran-magnitud-del-incumplimiento-de-la-meta-de-balance
- Consejo Fiscal Autónomo, sobre el decreto de 2024, con meta de 0,5 % para 2026:
  https://cfachile.cl/noticias/cfa-valora-fijacion-de-metas-anuales-en-decreto-de-politica-fiscal-pero-alerta
- Ministerio de Hacienda, *Estado de la Hacienda Pública*, sobre el decreto de 2022 (senda
  de 0,75 pp por año y ancla de deuda de 45 %): https://biblio.hacienda.cl/estado-de-la-hacienda-publica/politica-fiscal
- Clapes UC, columna de exautoridades del primer gobierno de Piñera sobre el cumplimiento de
  su meta: https://clapesuc.cl/en-los-medios/exautoridades-del-primer-gobierno-de-pinera-salen-a-refutar-datos-de-dipres
- DIPRES, *Cumplimiento de las metas de regla fiscal en Chile: revisión histórica*
  (diciembre de 2022): http://www.dipres.gob.cl/598/articles-299473_doc_pdf.pdf
- Ministerio de Hacienda, sobre el recálculo del déficit de 2009:
  https://old.hacienda.cl/sala-de-prensa/archivo-2014-2018/noticias/ministro-de-hacienda-deficit-fiscal.html
- Ministerio de Hacienda, sobre el cumplimiento de 2023:
  https://www.hacienda.cl/noticias-y-eventos/presentaciones/presentacion-ministro-marcel-por-regla-fiscal-fen-
- BCN Ley Chile, Decreto 1259: https://www.bcn.cl/leychile/navegar?idNorma=257223
- Banco Central de Chile, BDE: saldos mensuales del FEES (`F051.C17.STO.C.Z.USD.M`), del FRP
  (`F051.C15.STO.C.Z.USD.M`) y del total de los fondos soberanos (`F051.C19.STO.C.Z.USD.M`).

## Verificación

- **El déficit de 2009 medido en la época (−1,2 %) y recalculado (−3,1 %):** confirmado por
  el Ministerio de Hacienda. La cifra actual de la DIPRES es −3,4 %.
- **El decreto de Bachelet I:** Decreto 1259 (BCN Ley Chile), con superávit de 1 % del PIB al año.
- **Las metas de Piñera II para 2021:** −1,2 % original, −2,5 % (Decreto 253) y −4,7 %
  (Decreto 1.579), según el CFA y la DIPRES.
- **El decreto inicial de Piñera I:** el 637 fijaba equilibrio (0 %) en 2014; la meta de −1 %
  viene del Decreto 1.357, firmado el 30 de septiembre y publicado el 21 de octubre de 2011
  (BCN Ley Chile). Una versión anterior de este documento lo fechaba en 2010.
- **Cifras distintas según la versión:** el Diario Financiero (junio de 2026) informa −11,4 %
  para 2021 y −3,7 % para 2025, con actualizaciones posteriores; aquí se usan las de la DIPRES
  (2022) y el CFA (marzo de 2026): −10,7 % y −3,6 %. Esto corrige la versión anterior de este documento, que atribuía la meta de
  −1 % al Decreto 637.
