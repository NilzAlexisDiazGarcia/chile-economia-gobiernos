# Diccionario de datos

## `data/processed/observaciones.csv`

Generado por `python -m src.transform.clean`. Formato largo: una fila por indicador y fecha.

| Columna | Tipo | Descripción |
|---|---|---|
| `indicador` | texto | Clave del indicador en `config/series.yaml` (ej.: `imacec`, `tpm`) |
| `frecuencia` | texto | `DAILY`, `MONTHLY`, `QUARTERLY` o `ANNUAL` |
| `fecha` | fecha | Primer día del período que representa el dato |
| `valor` | decimal | Valor del indicador, en la unidad indicada en `series.yaml` |
| `fecha_fin_periodo` | fecha | Día siguiente al último del período (fin **exclusivo**) |
| `id_gobierno` | entero | Gobierno asignado por la regla de mayoría de días (ver `gobiernos.csv`) |
| `dias_gobierno` | entero | Días del período que caen dentro del gobierno asignado |
| `dias_periodo` | entero | Días totales del período |
| `es_transicion` | booleano | `True` si el período contiene un cambio de mando |

**Reglas de limpieza aplicadas:**

- Fechas convertidas desde el formato `dd-mm-aaaa` de la API.
- Valores convertidos de texto a número.
- Se excluyen las observaciones sin dato (estado `ND`): fines de semana y feriados en las
  series diarias. No se rellenan ni se reemplazan por cero.
- Se usa el archivo crudo más reciente de cada indicador.
- El resultado solo se guarda si pasa las validaciones: sin duplicados, sin nulos y con
  valores dentro de rangos de plausibilidad (`RANGOS_VALIDOS` en `src/transform/clean.py`).

## `data/reference/gobiernos.csv`

| Columna | Descripción |
|---|---|
| `id_gobierno` | Identificador, en orden cronológico |
| `presidente`, `etiqueta` | Nombre completo y etiqueta corta para gráficos |
| `fecha_inicio` | Día del cambio de mando (inclusivo) |
| `fecha_fin` | Día del siguiente cambio de mando (exclusivo) |
| `en_alcance` | `true` para los cinco gobiernos analizados |

## `data/reference/eventos.csv`

| Columna | Descripción |
|---|---|
| `evento`, `tipo` | Nombre y categoría del evento de contexto |
| `fecha_inicio`, `fecha_fin` | Período del evento |
| `precision_fecha` | `exacta` o `aproximada` |
| `nota`, `fuente` | Justificación de las fechas y su fuente |

## `data/processed/internacional.csv`

Generado por `python -m src.extract.internacional`. Datos anuales del FMI y del Banco Mundial.

| Columna | Descripción |
|---|---|
| `fuente` | Fuente y edición de los datos |
| `indicador`, `unidad` | Clave del indicador (ej.: `crecimiento_pib`) y su unidad |
| `zona`, `nombre_zona` | Código y nombre del país o agregado (ver `zonas.csv`) |
| `anio`, `valor` | Año y valor |
| `es_proyeccion` | `True` si el FMI lo publica como proyección; se excluye del análisis |

## Otras tablas de referencia (`data/reference/`)

| Archivo | Contenido |
|---|---|
| `zonas.csv` | Chile, sus cuatro pares, América Latina y el mundo; `es_par` marca los pares |
| `explicaciones.csv` | Citas textuales del Banco Central y del FMI por año y tema, con fuente y enlace |
| `metas_fiscales.csv` | Decreto inicial, meta inicial, modificaciones, meta vigente y resultado del último año completo de cada gobierno. `cumple_meta_inicial` vale "No aplica" cuando el decreto fijaba la meta para el año siguiente |
| `pobreza_casen.csv` | Pobreza por ingresos de cada CASEN con la metodología de 2013 (serie comparable), con fuente y enlace |
