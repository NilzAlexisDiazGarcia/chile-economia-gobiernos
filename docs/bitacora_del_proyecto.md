# Bitácora del proyecto

Registro de cómo se construyó el proyecto, etapa por etapa: qué se hizo, qué se decidió y
por qué, qué problemas aparecieron y cómo se resolvieron. Complementa a
[metodologia.md](metodologia.md) (las reglas del análisis) y a [hallazgos.md](hallazgos.md)
(los resultados).

## Resumen

| Etapa | Resultado | Herramientas |
|---|---|---|
| 0. Diseño | Pregunta, alcance, reglas de asignación y de neutralidad | Markdown, Git |
| 1. Extracción | 11 series del Banco Central, crudas y sin modificar | Python, API BDE |
| 2. Limpieza | 12.231 observaciones en formato largo, cada una con su gobierno | pandas, pytest |
| 3. Carga | Modelo estrella en PostgreSQL, con carga transaccional | PostgreSQL, psycopg |
| 4. Análisis | 4 vistas y 8 consultas de análisis | SQL |
| 5. Dashboard | Informe de 8 páginas, versionado como texto | Power BI (.pbip, TMDL, PBIR) |
| 5b. Contexto comparado | Chile frente a sus pares y explicaciones oficiales | API del FMI y del Banco Mundial |
| 5c. Rigor económico | Balance estructural, deuda neta e incertidumbre de los promedios | Python, SQL, DAX |

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
- **Los datos de Colombia no se pudieron descargar.** El promedio de pares en corrupción
  usa tres países, y así se indica en el reporte.

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

- **Superávit efectivo y estructural:** el superávit efectivo de Bachelet I (+3,67 % del PIB)
  fue un déficit estructural pequeño (−0,40 %); la diferencia la explican los ingresos del
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
**31 de 31 verificaciones correctas.**

| Verificación | Qué compara | Resultado |
|---|---|---|
| A. Crudo → limpio | Cada valor del CSV contra la respuesta original de la API (11 series) | Idénticos, con el código de serie correcto |
| B. Asignación | La regla de mayoría de días, reimplementada con el punto medio del período | 0 diferencias en 12.231 filas |
| C. Base de datos | PostgreSQL contra los CSV | Idénticos |
| D. Fuentes independientes | Chile contra el FMI (2006–2025) y la inflación contra 14 cifras publicadas por el INE | Diferencias de 0,23 pp o menos; las excepciones están explicadas |
| E. Recálculo sin SQL | 55 métricas por gobierno calculadas en pandas contra las vistas SQL | Idénticas |
| F. Documentos | 120 cifras de las tablas de hallazgos, las afirmaciones de la Síntesis y 15 diferencias contra los pares | Todas coinciden |

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
