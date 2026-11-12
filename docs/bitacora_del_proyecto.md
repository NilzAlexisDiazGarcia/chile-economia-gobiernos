# Bitácora del proyecto

Registro de cómo se construyó el proyecto, etapa por etapa: qué se hizo, qué se decidió y
por qué, qué problemas aparecieron y cómo se resolvieron. Complementa a
[metodologia.md](metodologia.md) (las reglas del análisis) y a [hallazgos.md](hallazgos.md)
(los resultados).

## Resumen

| Etapa | Resultado | Herramientas |
|---|---|---|
| 0. Diseño | Pregunta, alcance, reglas de asignación y de neutralidad | Markdown, Git |
| 1. Extracción | 20 series del Banco Central, crudas y sin modificar (11 en la primera versión) | Python, API BDE |
| 2. Limpieza | 18.568 observaciones en formato largo (12.231 en la primera versión), cada una con su gobierno | pandas, pytest |
| 3. Carga | Modelo estrella en PostgreSQL, con carga transaccional | PostgreSQL, psycopg |
| 4. Análisis | 4 vistas y 8 consultas de análisis | SQL |
| 5. Dashboard | Informe de 10 páginas (8 en la primera versión), versionado como texto | Power BI (.pbip, TMDL, PBIR) |
| 5b. Contexto comparado | Chile frente a sus pares y explicaciones oficiales | API del FMI y del Banco Mundial |
| 5c. Rigor económico | Balance estructural, deuda neta e incertidumbre de los promedios | Python, SQL, DAX |
| 5e. Balance de cada gobierno | Metas fiscales, fondos soberanos y ocho criterios uniformes | Investigación, SQL |
| 5f. Conclusiones | PIB por habitante, bienestar y las causas del menor crecimiento y la deuda | FMI, INE, CASEN |

---

## Etapa 0. Diseño del análisis

**Pregunta:** ¿cómo evolucionó la economía chilena durante cinco gobiernos (2006–2026),
considerando el contexto que enfrentó cada uno?

**Decisiones:**

1. **Cinco gobiernos completos:** Bachelet I, Piñera I, Bachelet II, Piñera II y Boric.
   Lagos y Kast se incluyen en la tabla de gobiernos con `en_alcance = false`, para que todo
   dato quede asignado a alguien y el filtro de alcance se aplique de forma explícita, en
   vez de descartar filas en silencio.
2. **El cambio de mando es el 11 de marzo,** con fechas `[inicio, fin)`: el 11 de marzo
   pertenece al gobierno entrante.
3. **Asignación por mayoría de días.** Un mes, trimestre o año que toca a dos gobiernos va
   al que gobernó más días de ese período, y se marca como "de transición" para poder
   excluirlo.
4. **Desfase sin imponer uno.** Las políticas tardan en notarse, pero no hay un rezago
   único. En vez de elegir uno, el reporte permite ver los resultados con 0, 6 o 12 meses.
5. **Neutralidad como requisito del diseño:**
   - Los mismos indicadores, reglas y fuentes para los cinco gobiernos.
   - Solo estadística descriptiva, sin conclusiones causales.
   - Orden cronológico, nunca de "mejor" a "peor".
   - Colores sin asociación partidaria: el tema evita el rojo y el azul como colores
     principales.

**Por qué importa:** en un análisis político la credibilidad depende de que las reglas se
fijen antes de ver los resultados y se apliquen igual a todos.

---

## Etapa 1. Extracción (`src/extract/`)

**Qué se hizo:** un cliente de la API de la Base de Datos Estadísticos (BDE) del Banco
Central (`bcch.py`) descarga las series definidas en `config/series.yaml` y guarda cada
respuesta **cruda y sin modificar** en `data/raw/bcch/`.

| Indicador | Frecuencia | Fuente original |
|---|---|---|
| PIB, IMACEC, IPC, TPM, tipo de cambio, cobre | Diaria, mensual o trimestral | Banco Central |
| Desempleo | Mensual | INE, vía Banco Central |
| Deuda bruta y balance fiscal | Trimestral y anual | DIPRES, vía Banco Central |
| Deuda neta y balance estructural (etapa 5c) | Trimestral y anual | DIPRES, vía Banco Central |

**Decisiones:**

- **Los códigos de serie se buscan con `SearchSeries` de la API** (`buscar_series.py`), no
  se copian de internet. Se eligieron series "empalmadas", que cubren 2005–2026 con un solo
  código y sin quiebres por cambio de año base.
- **Desde 2005,** un año antes del primer gobierno, para poder calcular variaciones a 12
  meses desde el inicio.
- **Datos fiscales vía Banco Central:** la DIPRES publica la deuda bruta solo en informes
  PDF. La BDE la tiene como serie continua. Se validó contra la DIPRES: el balance 2025 da
  −2,80 % del PIB en ambas fuentes.
- **Credenciales en `.env`,** fuera de Git. El código las lee desde variables de entorno.

**Problema resuelto:** la API responde HTTP 200 incluso cuando hay un error, por ejemplo
con credenciales inválidas. El error real viene en el campo `Codigo` del JSON. El cliente
revisa ese campo y falla con un mensaje claro, en vez de guardar una respuesta vacía.

---

## Etapa 2. Limpieza y asignación (`src/transform/`)

**Qué se hizo:** `clean.py` convierte las respuestas crudas en un solo archivo en formato
largo, `data/processed/observaciones.csv`, con 12.231 filas y una fila por indicador y
fecha. `asignar_gobierno.py` aplica la regla de mayoría de días.

**Decisiones:**

- **Formato largo** (indicador, fecha, valor): un indicador nuevo no cambia la estructura
  de la tabla.
- **Los datos faltantes no se rellenan.** Los días sin dato de las series diarias (fines de
  semana y feriados) se excluyen, no se reemplazan por cero.
- **El archivo solo se guarda si pasa las validaciones:** sin duplicados, sin nulos y con
  valores dentro de rangos de plausibilidad. Por ejemplo, un tipo de cambio fuera de 400 a
  1.200 pesos indica un error de serie o de unidad.
- **Tests de la regla de asignación** (`tests/test_asignar_gobierno.py`): casos límite como
  el 10 y el 11 de marzo, el mes de marzo (10 días contra 21), el primer trimestre y el año
  de transición.
- **El CSV limpio se versiona en Git** (664 KB, datos públicos). Así cualquiera puede cargar
  la base y abrir el dashboard sin una cuenta de la API.

---

## Etapa 3. Carga en PostgreSQL (`src/load/postgres.py`, `sql/01_schema.sql`)

**Qué se hizo:** un modelo estrella en el esquema `economia`, con tres dimensiones
(gobierno, indicador y evento) y una tabla de hechos (observaciones).

**Decisiones:**

- **La base valida las reglas por su cuenta:**
  - Una restricción `EXCLUDE` impide que dos gobiernos se superpongan en el tiempo.
  - Las restricciones `CHECK` validan fechas, frecuencias y días.
  - Las claves foráneas impiden observaciones sin gobierno o sin indicador.
- **Recarga completa dentro de una transacción:** vaciar, insertar con `COPY` y verificar
  los conteos antes del `COMMIT`. Si algo falla, la base queda exactamente como estaba;
  nunca a medio cargar.
- **`COPY` en vez de un `INSERT` por fila:** es más rápido, y los valores viajan separados
  del texto SQL, así que no hay riesgo de inyección.
- **Script idempotente:** se puede ejecutar muchas veces con el mismo resultado.

---

## Etapa 4. Análisis SQL (`sql/02_views.sql`, `sql/analisis/`)

**Qué se hizo:** cuatro vistas reutilizables y ocho consultas de análisis.

| Vista | Para qué sirve |
|---|---|
| `v_observacion` | Hechos con los atributos de sus dimensiones |
| `v_variacion_12m` | Variación respecto del mismo período del año anterior (PIB, IMACEC, cobre) |
| `v_resumen_gobierno` | Una fila por gobierno e indicador: heredado, final, promedio, mínimo y máximo |
| `v_pbi_observacion` | Tabla para Power BI, con 3 copias de cada dato, una por desfase (0, 6 y 12 meses) |

**Decisiones:**

- **Variación a 12 meses en vez de promedios de nivel:** el nivel del PIB crece con el
  tiempo y un promedio de nivel siempre favorecería al gobierno más reciente.
- **`LAG` sobre la serie completa,** antes de filtrar por gobierno: marzo de 2010 se compara
  con marzo de 2009 aunque sean de gobiernos distintos.
- **"Heredado" contra "final":** el punto de partida de cada gobierno es el último dato del
  anterior. Así se mide el cambio durante todo el mandato.
- **El desfase se resuelve en SQL:** cada dato se reasigna al gobierno de 6 o 12 meses
  antes, usando el punto medio del período. En Power BI basta un selector.

**Problema resuelto: doble redondeo.** Las primeras vistas redondeaban a 4 decimales y las
consultas volvían a redondear a 2. Eso produce errores: 2,98498 → 2,9850 → 2,99, cuando lo
correcto es 2,98. Desde entonces las vistas no redondean, y solo se redondea al presentar.

---

## Etapa 5. Dashboard en Power BI (`dashboard/`)

**Qué se hizo:** un informe de 8 páginas conectado a PostgreSQL.

| Página | Qué responde |
|---|---|
| Resumen | El cambio de régimen en cuatro cifras y la tendencia de la deuda |
| Comparación | Los indicadores principales de los cinco gobiernos, lado a lado |
| Ficha por gobierno | Qué recibió y qué entregó cada gobierno, y en qué contexto |
| Series en el tiempo | Cada indicador mes a mes, con los eventos de contexto |
| Contexto externo | Cobre, dólar y actividad |
| Chile frente a sus pares | Si cada resultado fue propio de Chile o compartido con la región |
| Sensibilidad al desfase | Cuánto cambian las conclusiones según el rezago supuesto |
| Metodología | Las reglas del análisis y sus límites |

**Decisiones:**

- **Formato `.pbip` en vez de `.pbix`:** el modelo (TMDL) y las páginas (PBIR) quedan como
  archivos de texto. Git puede mostrar qué cambió en cada medida o gráfico, cosa que no
  puede hacer con un binario. El proyecto no guarda datos ni claves.
- **Medidas DAX organizadas:** seis carpetas temáticas, una descripción por medida y formato
  numérico propio.
- **Referencias externas para comparar sin opinar:**
  - La meta de inflación del Banco Central (3 %, rango de 2 % a 4 %).
  - Lo heredado contra lo entregado por cada gobierno.
  - El promedio de los países pares.
- **Eventos con un criterio uniforme:** shocks de alcance global o nacional con fechas de
  una fuente oficial. Por ese criterio se agregó el alza mundial de inflación de 2021–2023,
  para que todos los períodos tengan su contexto documentado.
- **Las páginas nuevas se generaron con código:** un script escribe los archivos PBIR de
  cada página y gráfico. Así el diseño es idéntico en todas las páginas: márgenes, tamaños,
  colores por gobierno y orden cronológico.

**Problemas resueltos:**

| Problema | Causa | Solución |
|---|---|---|
| Una columna mostraba "True/False" | Columna booleana de la base | Paso en Power Query que la convierte en "Período compartido" o "de un solo gobierno" |
| El proyecto no abría: "Item 'Indicador' already exists" | Power BI no distingue mayúsculas: `indicador` e `Indicador` eran el mismo nombre | Se renombró la columna calculada a `Nombre Indicador` |
| Error de referencia cíclica al actualizar | Power Query usaba una lista guardada de la base, anterior a las tablas nuevas | "Actualizar todo" en el editor de Power Query |
| Las barras se ordenaban de mayor a menor | Orden por defecto de Power BI | Orden explícito por gobierno, en orden cronológico, para no sugerir un ranking |
| Las listas de eventos salían en una sola línea | La tarjeta nueva no respeta los saltos de línea | Tarjeta clásica con ajuste de texto; las citas pasaron a una tabla |

---

## Etapa 5b. Contexto comparado (`src/extract/internacional.py`)

**Motivo:** comparar a cada gobierno solo con Chile no distingue si un mal resultado fue
propio o compartido con toda la región. Si toda la región crece poco, crecer poco no dice
lo mismo que si la región crece mucho.

**Qué se hizo:**

- **Datos anuales del FMI** (World Economic Outlook, octubre de 2026) para Chile, América
  Latina, el mundo y cuatro pares: Perú, Colombia, México y Brasil, países de la región con
  metas de inflación.
- **Control de la corrupción del Banco Mundial** (Worldwide Governance Indicators).
- **Siete citas textuales** del Banco Central y del FMI que explican cada período, con
  fuente y enlace (`data/reference/explicaciones.csv`). Cada cita se verificó en el
  documento original.
- **Tablas y vista nuevas:** `dim_zona`, `fact_internacional`, `dim_explicacion` y la vista
  `v_pbi_comparacion`, con la consulta `08_comparacion_pares.sql` y 15 tests nuevos (31 en
  total).

**Decisiones:**

- **Se compara con el promedio de los pares, no con el agregado de América Latina:** la
  inflación de Argentina y Venezuela distorsiona el agregado regional (13,3 % en 2022–2025).
- **El desempleo no se compara entre países:** cada país lo mide distinto, y con alta
  informalidad, como en México, el desempleo medido es bajo.
- **No hay ranking de gobiernos.** Ningún período destaca en todos los indicadores frente a
  sus pares, así que un puntaje único dependería de pesos arbitrarios. El reporte muestra
  las diferencias indicador por indicador.
- **La corrupción se mide con un índice, no con una lista de casos:** una lista elegida por
  el autor introduce sesgo. El índice se presenta como contexto, con sus límites: mide
  percepción, y sus cambios pequeños no son concluyentes.

**Problemas resueltos:**

- **La API del Banco Mundial fallaba seguido** (errores 502 y 504):
  - Se piden los datos de a un país y con el parámetro de la fuente.
  - Se reintenta automáticamente.
  - Se reutiliza lo ya descargado en el día.
  - Si falla un país par, se informa y se sigue; si falla Chile, el proceso se detiene.
- **Los datos de Colombia no se pudieron descargar al principio.** Una descarga posterior los
  completó; si la API falla, el extractor reutiliza la última descarga disponible.

---

## Etapa 5c. Revisión económica

**Motivo:** una revisión del proyecto con criterio de economista encontró tres vacíos que un
profesional del rubro notaría:

| Vacío | Por qué importa | Solución |
|---|---|---|
| Solo había balance efectivo | Depende del ciclo y del cobre; mezcla la gestión fiscal con la suerte | Se agregó el **balance estructural**, la meta de la regla fiscal chilena |
| Solo había deuda bruta | Chile tiene fondos soberanos; la deuda bruta exagera el endeudamiento | Se agregó la **deuda neta**, que descuenta los activos del Fisco |
| Los promedios no mostraban su incertidumbre | Con cuatro años por gobierno, un año extremo cambia todo | Rango trimestral en la Ficha, y error estándar y comparaciones entre pares en los hallazgos |

**Lo que mostró:**

- **Superávit efectivo y estructural:** en promedio, el superávit efectivo de Bachelet I
  (+3,67 % del PIB) fue un déficit estructural pequeño (−0,40 %); la diferencia la explican los ingresos del
  cobre.
- **Deuda neta:** pasó de −19 % del PIB en 2008, cuando el Fisco era acreedor neto, a 26 % a
  comienzos de 2026.
- **Incertidumbre:** de 10 comparaciones de crecimiento entre pares de gobiernos, solo 2
  superan su incertidumbre: Piñera I frente a Bachelet II y frente a Boric. Esto refuerza la
  decisión de no ordenar a los gobiernos.

Las dos series nuevas vienen de la misma API del Banco Central (fuente original: DIPRES),
con tests y verificación en la auditoría. Las mejoras de menor prioridad, como el tipo de
cambio real, la inversión o los salarios, quedaron documentadas como extensiones en
[metodologia.md](metodologia.md).

## Etapa 5e. Balance de cada gobierno

**Motivo:** el análisis mostraba los datos y sus límites, pero no concluía. La neutralidad no
exige callar los aciertos y los problemas de cada gobierno, sino medirlos a todos con las
mismas reglas, fijadas antes de mirar los resultados.

**Qué se hizo:**
- **Investigación de las metas fiscales** de los cinco gobiernos en fuentes primarias: los
  decretos, la revisión histórica de la DIPRES (2022), la Biblioteca del Congreso y el CFA. Al
  contrastar las fuentes se corrigieron dos datos de la prensa: el decreto inicial de Piñera I
  fijaba equilibrio (0 %), no −1 %, y la meta de 2021 modificada fue −4,7 %, no −4,3 %.
- **Saldos de los fondos soberanos** (FEES y FRP) desde 2007, de la API del Banco Central.
- **Seis criterios uniformes** en la vista `v_pbi_evaluacion`, con quién controla cada variable.
- **Página nueva en el dashboard,** "Balance de cada gobierno", segunda después del Resumen.
- **Tests de consistencia** (cumplir la meta equivale a un resultado igual o mejor que ella) y
  una verificación nueva en la auditoría, que recalcula las 30 evaluaciones sin SQL.

**Resultado principal:** con la meta vigente, solo Piñera I cumplió su meta fiscal; con la
meta del decreto inicial, ninguno de los tres que la fijaron para su último año. Ambas
lecturas se muestran, junto con el contexto de cada incumplimiento.

## Etapa 5f. Conclusiones: por qué Chile creció menos y se endeudó

**Motivo:** el análisis describía bien qué pasó, pero no explicaba por qué. Una revisión con
criterio de economista identificó además dos vacíos que podían cambiar conclusiones.

**Qué se hizo:**
- **PIB por habitante:** se calculó con el PIB y la población del FMI. Cambia la lectura: el
  ingreso por habitante creció 3,4 % al año entre 2006 y 2013, y 1,0 % entre 2014 y 2025, con
  caídas en 2017, 2019, 2020 y 2023. La inmigración de 2015–2019 hacía crecer el PIB total más
  que el ingreso de cada persona.
- **Bienestar:** la pobreza por ingresos de la CASEN, en la serie comparable, y el índice real de
  remuneraciones del INE. La pobreza bajó de 29,1 % a 4,9 % y subió solo en la pandemia.
- **Las causas, cada una con su fuente técnica:**
  - Para el crecimiento: la productividad (CNEP), el fin del auge del cobre (FMI) y la caída
    del crecimiento tendencial (DIPRES y Banco Central).
  - Para la deuda: el gasto permanente mayor que el ingreso permanente (CFA), la relación
    entre bajo crecimiento y recaudación (DIPRES), los shocks y las metas cambiadas a
    discreción (DIPRES).
- **El documento [conclusiones.md](conclusiones.md)** y una página nueva en el dashboard, con la
  tesis, los gráficos que la respaldan y las causas.
- **Dos criterios más** en la evaluación (pobreza y salario real) y nuevas verificaciones en
  la auditoría.

**Problema resuelto:** la auditoría falló al buscar el archivo crudo de `remuneraciones_reales`,
porque el patrón de búsqueda también calzaba con `remuneraciones_reales_hist`. Se usó el mismo
patrón estricto que la limpieza: la fecha justo después del nombre.

**Corrección del criterio de ahorro:** el balance evaluaba el total de los fondos soberanos
(FEES + FRP), y marcaba a Boric como favorable porque el total pasó de US$ 13.537 a 14.272
millones. Era engañoso por dos razones:
- **El FRP sube casi solo:** la ley obliga a hacerle aportes y solo puede financiar pensiones.
  En cambio, el FEES, el colchón que el gobierno puede usar, bajó de US$ 6.406 a 3.944 millones.
- **Un fondo puede crecer con deuda.** La deuda bruta subió de 36,2 % a 42,4 % del PIB en el
  mismo período.

El criterio pasó a ser el FEES. Con eso, Bachelet II, Piñera II y Boric quedan desfavorables.
La tabla de arcas fiscales suma la deuda bruta, y el texto aclara que la medida de solvencia es
la deuda neta, que descuenta los fondos.

## Etapa 5g. Costo de la deuda y mejoras de la revisión final

- **A qué tasa se endeudó cada gobierno:** tasas de mercado de los bonos a 10 años en pesos y en
  UF, y gasto en intereses como % del PIB (series nuevas de la BDE). Piñera II sumó más deuda
  con las tasas reales más bajas (0,9 %); con Boric las tasas subieron (2,3 %) y los intereses
  llegaron a 1,24 % del PIB en 2025, el máximo desde 2005.
- **FEES en % del PIB:** el criterio de ahorro deja de usar dólares nominales. Los resultados
  (✓ o ✗) no cambian.
- **Fuente primaria del CFA:** se reemplazó una nota de prensa por el informe del CFA del 23 de
  abril de 2024. El conteo de años con déficit se recalculó con los datos del proyecto: 14 de
  los 17 años entre 2009 y 2025 (la cifra anterior, 13 de 16 desde 2008, no coincidía).
- **Generador de páginas en el repositorio:** `dashboard/generador/`.
- **Auditoría:** nueva sección J; 52 de 52 verificaciones correctas.

## Etapa 5h. Revisión externa y repaso final

Una revisión externa del proyecto, contrastada punto por punto con los datos y con fuentes
primarias, llevó a estas correcciones:

- **Tesis sin causas propias:** la frase "los gobiernos no causaron ese cambio, pero sí lo
  agravaron" afirmaba una causa que el método no demuestra, y "todos gastaron más de lo que
  generaban" no se cumplía en 2006–2007. La tesis actual atribuye las causas a sus fuentes y
  deja como resultado propio lo que muestran los datos: los cinco gobiernos terminaron con
  déficit estructural y la deuda neta subió en cuatro. "Dejó de crecer" pasó a "creció menos".
- **Meta inicial del mismo año:** Piñera I y Bachelet II fijaron su meta inicial para 2014 y
  2018, el año siguiente a su último año completo, así que figuran como "No aplica".
- **Fecha corregida:** el Decreto 1.357 de Piñera I es de octubre de 2011, no de 2010.
- **Fechas de referencia:** la pobreza muestra el año de cada CASEN, y el pie del Balance
  explica de qué fecha es cada dato "recibido".
- **Un error de redacción:** el balance de Bachelet II decía que la inflación terminó peor
  que como la recibió; bajó de 3,2 % a 2,0 %. Lo que subió fue el desempleo.
- **Cifras desactualizadas** del README y de esta bitácora (series, filas, cifras
  verificadas y páginas), y guías antiguas marcadas como históricas.
- **Dígitos perdidos en el PDF:** un reemplazo de espacios antes de "%" borró el dígito
  anterior en 17 textos del generador ("4,□ %" en vez de "4,3 %"). Se recuperaron desde la
  versión previa y un test rechaza desde entonces caracteres de control en el informe.
- **Un decimal en todo el informe:** 22 medidas mostraban dos decimales y el resto, uno.
  Ahora todas usan uno, salvo la TPM (se mueve de a 0,25), el cobre en USD/lb, el gasto en
  intereses y el índice de corrupción. Cada cifra se redondea desde el valor completo: el
  crecimiento de Piñera II es 2,647 → 2,6, no 2,65 → 2,7. Power BI muestra −0,006 como
  "-0,0". Los valores verificados del dashboard se leyeron del PDF exportado.

## Verificación de cifras

Cada afirmación de [hallazgos.md](hallazgos.md) se revisó contra los datos antes de
publicarla. Tres borradores se corrigieron al verificarlos:

| Borrador | Lo que mostraron los datos |
|---|---|
| "El superávit de 2006–2008 no se volvió a registrar" | Hubo superávit en 2011, 2012 y 2022, todos bajo 1,3 % del PIB |
| "Tres gobiernos recibieron la economía saliendo de una crisis" | Fueron dos, en 2010 y en 2022 |
| "Inflación de 4 % a 5 % en 2014–2016" | Llegó hasta 5,7 % |

Las cifras del dashboard coinciden con las consultas SQL. Por ejemplo, el crecimiento del
PIB de Piñera I es 5,43 % en ambos.

### Auditoría de exactitud (`src/analysis/auditoria.py`)

Un script verifica cada cifra por un camino distinto al que la produjo. Resultado actual:
**52 de 52 verificaciones correctas.**

| Verificación | Qué compara | Resultado |
|---|---|---|
| A. Crudo → limpio | Cada valor del CSV contra la respuesta original de la API (20 series) | Idénticos, con el código de serie correcto |
| B. Asignación | La regla de mayoría de días, reimplementada con el punto medio del período | 0 diferencias en 18.568 filas |
| C. Base de datos | PostgreSQL contra los CSV | Idénticos |
| D. Fuentes independientes | Chile contra el FMI (2006–2025) y la inflación contra 14 cifras publicadas por el INE | Diferencias de 0,23 pp o menos; las excepciones están explicadas |
| E. Recálculo sin SQL | 96 métricas por gobierno calculadas en pandas contra las vistas SQL | Idénticas |
| F. Documentos | 142 cifras de las tablas de hallazgos, las afirmaciones de la Síntesis y 15 diferencias contra los pares | Todas coinciden |
| G. Dashboard | 89 valores leídos en Power BI (Resumen, Comparación y dos Fichas), contra la lógica de cada medida reproducida en Python (`valores_dashboard.py`) | Todos coinciden |
| H. Balance de cada gobierno | Las 40 evaluaciones (ocho criterios por cinco gobiernos), recalculadas en pandas contra la vista SQL | Todas coinciden |
| I. Datos fiscales | Balance estructural de la BDE contra la DIPRES y el CFA (20 años), 4 saldos de los fondos soberanos y los resultados de las metas fiscales | Coinciden; las diferencias de 2009 y 2022 se deben a la versión de las cifras y están explicadas |
| J. Costo de la deuda | 20 valores de tasas e intereses recalculados sin SQL, y 6 cifras citadas en los documentos | Todos coinciden |

**Hallazgo de la auditoría: la serie de inflación no era la oficial.** La primera versión
usaba un IPC "empalmado" por el Banco Central a la canasta de 2023. Al contrastarlo con las
cifras publicadas por el INE, difería hasta 1,3 pp en los años de cambio de base del IPC.
Por ejemplo, diciembre de 2009 daba −2,6 %, cuando la cifra oficial es −1,4 %. Se reemplazó
por la serie oficial (`F074.IPC.IND.Z.EP09.C.M`), que coincide con las 14 cifras publicadas
que se revisaron. Cambiaron las cifras de inflación de los cinco períodos; las mayores
diferencias fueron estas:

| Cifra | Antes | Después |
|---|---|---|
| Inflación promedio de Bachelet I | 4,03 % | 4,33 % |
| Inflación promedio de Boric | 6,59 % | 6,72 % |
| Meses en el rango meta de Boric | 27 % | 21 % |
| Meses en el rango meta de Piñera II | 73 % | 75 % |

Ninguna conclusión cambió.

**Diferencias con el FMI que se investigaron y se explican:**

- **Desempleo de 2009:** el FMI informa 11,1 %, pero el INE publicó un promedio de 9,7 % y el
  proyecto tiene 9,64 %. La cifra atípica es la del FMI.
- **Inflación en los años de cambio de base (2014 y 2024):** el FMI calcula el promedio con
  el índice de la canasta nueva, mientras el proyecto promedia las variaciones mensuales
  oficiales. Por ejemplo, el INE informó 4,5 % en febrero de 2024, igual que el proyecto, y
  una cifra "referencial" de 3,6 % con la canasta nueva.

**Auditoría final del dashboard, con criterio económico.** Además de verificar que cada
número coincida, se revisó si cada dato cuenta bien lo que pasó. Se corrigieron tres
problemas que no eran errores de cálculo:

| Problema | Por qué inducía a error | Corrección |
|---|---|---|
| La TPM se mostraba con un decimal | El Banco Central la mueve en pasos de 0,25: "4,8 %" nunca existió; era 4,75 % | Dos decimales |
| La Ficha de Piñera I decía "sin eventos" | Asumió 12 días después del terremoto y saliendo de la recesión de 2009 | Se muestran también los eventos de los 12 meses previos, marcados "antes de asumir" |
| Las tarjetas "vs. pares" no decían su fuente | Usan años calendario del FMI, no los trimestres del Banco Central de la tarjeta vecina | La etiqueta dice "FMI" |

Los valores que debe mostrar cada tarjeta, para los cinco gobiernos, están en
[valores_dashboard.md](valores_dashboard.md).

**Citas oficiales:** las 13 frases citadas del Banco Central y del FMI se verificaron palabra
por palabra en los documentos originales, con su página.

---

## Cómo reproducir todo

```bash
python -m src.extract.run_bcch            # requiere cuenta de la API del Banco Central
python -m src.transform.clean
python -m src.extract.internacional
python -m src.load.postgres
python -m src.analysis.ejecutar_consultas
python -m src.analysis.auditoria
python -m src.analysis.valores_dashboard
python -m pytest
```

Sin cuenta de la API, basta con los dos últimos pasos de carga: los CSV limpios están
versionados. Después se abre `dashboard/chile_economia.pbip` y se hace clic en
**Inicio → Actualizar**.

---

## Límites del análisis

- **Es descriptivo:** no estima cuánto de cada resultado se debe a las políticas de cada
  gobierno, al ciclo externo o a las decisiones del Banco Central, que es autónomo.
- **Hay eventos superpuestos:** el estallido social y la pandemia se superponen en 2020, y
  sus efectos no se pueden separar.
- **Hay efecto base:** después de una caída fuerte, la variación del año siguiente sale muy
  alta (2021 contra 2020).
- **El último gobierno tiene menos datos:** con desfase, sus meses finales todavía no se
  publican.
- **El cobre está en dólares nominales:** los niveles de períodos distantes no son
  directamente comparables, y las variaciones sí.
