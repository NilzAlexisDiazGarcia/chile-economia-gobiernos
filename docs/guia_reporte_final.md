# Guía del reporte final

Especificación de diseño para llevar el dashboard a su versión final. Complementa
[guia_dashboard.md](guia_dashboard.md), que explica la conexión y el modelo.

> **Estado:** las 8 páginas ya están construidas según esta especificación. Las páginas
> nuevas se generaron con código, directo en los archivos PBIR, y las existentes se
> ajustaron al mismo diseño. Quedan pendientes dos pasos manuales en Power BI:
> - El navegador de páginas.
> - Las líneas constantes X de los eventos en "Series en el tiempo" y "Contexto externo".
>
> Esta guía queda como referencia del diseño y para hacer cambios a mano.

**Antes de empezar:** abre `dashboard/chile_economia.pbip` y haz clic en **Inicio →
Actualizar**. El modelo cambió (columnas y medidas nuevas) y Power BI tiene que recargar
los datos.

## 1. Qué cambió en el modelo

Los cambios se hicieron directo en los archivos TMDL, así que no hay que crear medidas a mano.

- **Medidas en carpetas:** `1. Base`, `2. Indicadores`, `3. Ficha por gobierno`,
  `4. Resumen ejecutivo` y `5. Textos y formato`. Cada medida tiene descripción (pasa el
  mouse sobre ella en el panel Datos) y formato numérico propio.
- **`Observaciones[Tipo de período]`** reemplaza a "False/True". Sus valores son
  "Período de un solo gobierno" y "Período compartido (transición)".
- **`Indicadores[Nombre]`:** nombre corto de cada indicador, ordenado por tema. Úsalo en
  segmentadores y leyendas en vez de `descripcion`.
- **Columnas técnicas ocultas:** `indicador`, `valor`, `var_12m_pct` e `id_gobierno`.
- **Fechas** de Eventos y Gobiernos en formato `dd-mm-aaaa`.
- **Evento nuevo:** "Alza mundial de inflación" (2021–2023).
- **Tabla `Comparacion`:** Chile frente a sus pares por año, con datos del FMI y del Banco
  Mundial. Sus medidas están en la carpeta `6. Comparación con pares`. No depende del
  desfase, porque los datos son anuales.
- **Tabla `Explicaciones`:** citas textuales del Banco Central y del FMI de cada período.
  La medida `Explicacion del Periodo` las muestra para el gobierno seleccionado.

**Si al actualizar aparece un error en `Comparacion` o `Explicaciones`:** primero corre
`python -m src.load.postgres`, que crea la vista `v_pbi_comparacion` y la tabla
`dim_explicacion`. Si el error sigue, envíame el mensaje exacto.

## 2. Sistema de diseño (igual en todas las páginas)

Un reporte se ve profesional cuando todas las páginas siguen las mismas reglas.

**Lienzo:** 1920 × 1080. Fondo de página `#F5F5F5`. Objetos visuales con fondo blanco,
borde redondeado de 8 px y sin sombra.

**Cuadrícula:** margen de 40 px a cada lado y 20 px entre objetos. Para alinear, usa
**Formato → Alinear** con varios objetos seleccionados, y fija posiciones exactas en
**Formato → General → Propiedades → Tamaño y posición**.

| Zona | Posición (y) | Contenido |
|---|---|---|
| Encabezado | 20 – 120 | Título de página (28 pt, negrita) a la izquierda; `Texto Desfase` debajo (14 pt, gris); navegador de páginas a la derecha |
| Controles | 130 – 200 | Segmentadores |
| Contenido | 210 – 1020 | Objetos visuales |
| Pie | 1030 – 1070 | Medida `Fuente` (10 pt, gris `#6B6B6B`) |

**Tipografía:** Segoe UI. Título de página 28 pt negrita, título de objeto visual 16 pt,
texto 13 pt, notas 10 pt. Color de texto `#2B2B2B`; secundario `#6B6B6B`.

**Color por gobierno:** siempre el mismo en todas las páginas.

| Bachelet I | Piñera I | Bachelet II | Piñera II | Boric |
|---|---|---|---|---|
| `#4A6D7C` | `#B08D57` | `#6B8E5A` | `#8A6F9A` | `#C2703D` |

En gráficos de líneas con leyenda de gobierno salen solos, porque siguen el orden del
tema. En gráficos de barras: **Formato → Columnas → Color → fx → Valor del campo →
`Color Gobierno`**.

**Títulos:** describen el dato, nunca lo juzgan. Desactiva los **subtítulos automáticos**
("Valor Promedio por fecha y etiqueta"): **Formato → General → Título → Subtítulo**.

**Navegación:** **Insertar → Botones → Navegador → Navegador de páginas**, en el
encabezado de cada página. Crea un botón por página y se actualiza solo.

**Segmentador de desfase:** sincronizado en todas las páginas **excepto** en
"Sensibilidad al desfase" y "Chile frente a sus pares" (**Ver → Sincronizar segmentaciones**).

## 3. Páginas

Orden final: Resumen · Comparación · Ficha por gobierno · Series en el tiempo · Contexto
externo · Chile frente a sus pares · Sensibilidad al desfase · Metodología.

### 3.1 Resumen (nueva, primera página)

Es lo primero que ve un reclutador. Debe entenderse en 10 segundos.

- **Título:** "Economía de Chile, 2006–2026: cinco gobiernos, un mismo período de cambio".
- **Cuatro tarjetas grandes** (tarjeta nueva, valor 32 pt, una al lado de la otra):

| Tarjeta | Medida | Etiqueta de la tarjeta |
|---|---|---|
| Crecimiento del PIB | `Crecimiento PIB Antes y Despues 2014` | Promedio anual, 2006–2014 → 2014–2026 |
| Deuda bruta | `Deuda 2006 a 2026` | % del PIB, marzo 2006 → marzo 2026 |
| Desempleo | `Desempleo 2006 a 2026` | Tasa, marzo 2006 → marzo 2026 |
| Inflación en el rango meta | `% Meses Inflacion en Rango` | Meses con inflación entre 2 % y 4 % |

- **Gráfico de líneas** (ancho completo): eje X `fecha`, eje Y `Valor Promedio`, leyenda
  `Gobiernos[etiqueta]`, filtro del objeto visual `Indicadores[Nombre]` = "Deuda bruta".
  Título: "Deuda bruta del Gobierno Central (% del PIB)". Muestra que la tendencia
  atraviesa a todos los gobiernos.
- **Cuadro de texto** "Lo que muestran los datos": los tres puntos de la sección
  "Síntesis" de [hallazgos.md](hallazgos.md).

### 3.2 Comparación (página 1 actual)

- Cambia el segmentador de transición al campo `Tipo de período`.
- Agrega el navegador de páginas en el encabezado.
- Barras con `Color Gobierno`.
- **Formato condicional** en la matriz, para guiar la lectura sin juzgar: en
  `Inflación prom. (%)`, **fx → Color de fondo → Reglas**: entre 2 y 4 en gris muy claro
  (`#EDEDED`) y sin color fuera del rango. Así se marca la meta del Banco Central, que es
  una referencia externa, y no un "mejor" o "peor".

### 3.3 Ficha por gobierno (nueva)

La pieza central: cada gobierno con lo que recibió, lo que entregó y el contexto que tuvo.

- **Segmentador de gobierno** (`Gobiernos[etiqueta]`), en mosaico, selección única, en la
  zona de controles.
- **Encabezado:** tarjeta con `Titulo Ficha` (24 pt), sin etiqueta.
- **Fila 1, cuatro tarjetas:**

| Tarjeta | Valor | Etiqueta de referencia |
|---|---|---|
| Crecimiento del PIB (%) | `Crecimiento PIB %` | — |
| Inflación promedio (%) | `Inflacion Promedio %` | `% Meses Inflacion en Rango` con el texto "de los meses en el rango meta" |
| Desempleo (%) | `Desempleo Recibio Entrego` | `Desempleo Cambio Texto` |
| Deuda bruta (% del PIB) | `Deuda Recibio Entrego` | `Deuda Cambio Texto` |

- **Fila 2, cuatro tarjetas:** TPM (`TPM Recibio Entrego` + `TPM Cambio Texto`), balance
  fiscal (`Balance Fiscal Promedio %`), cobre (`Cobre Promedio USD lb` + `Cobre Var 12m %`)
  y dólar (`Dolar Recibio Entrego`).
- **Fila 3, dos tarjetas "Frente a sus pares":** `Texto Crecimiento vs Pares` (etiqueta
  "Crecimiento del PIB vs. Perú, Colombia, México y Brasil") y `Texto Inflacion vs Pares`
  (etiqueta "Inflación vs. los mismos países").
- **Cuadro "Qué dijeron el Banco Central y el FMI"** bajo el de eventos: tarjeta con
  `Explicacion del Periodo` (11 pt, ajuste de texto activado).
- **Cuadro "Contexto del período"** a la derecha: tarjeta con `Eventos del Periodo`
  (13 pt, ajuste de texto activado), con el título "Eventos externos y nacionales del período".
- **Dos gráficos abajo:**
  - **IMACEC:** eje X `fecha`, eje Y `Crecimiento IMACEC %`. Título "Crecimiento mensual
    del IMACEC durante el mandato (%)". Línea constante Y en 0.
  - **Inflación:** eje X `fecha`, eje Y `Inflacion Promedio %`. Título "Inflación anual vs.
    meta del Banco Central (%)". En **Análisis → Línea constante Y**, una línea en 3
    rotulada "Meta 3 %" y dos líneas punteadas en 2 y 4.

Como todo depende del segmentador, la misma página sirve para los cinco gobiernos.

### 3.4 Series en el tiempo (página 2 actual)

- Segmentador de indicador: cambia `descripcion` por **`Indicadores[Nombre]`**, en lista
  desplegable.
- **Títulos dinámicos:** **Formato → General → Título → Texto → fx → Valor del campo**.
  Usa `Titulo Serie` en el gráfico de arriba y `Titulo Var 12m` en el de abajo.
- **Eventos en los gráficos:** en el panel **Análisis** (lupa), **Línea constante X**, una
  línea por evento, gris punteada, con la etiqueta de datos activada:

| Fecha | Etiqueta |
|---|---|
| 15-09-2008 | Crisis financiera |
| 27-02-2010 | Terremoto |
| 18-10-2019 | Estallido social |
| 03-03-2020 | Pandemia |
| 01-03-2021 | Alza mundial de inflación |

- Tabla de eventos con los encabezados renombrados (Evento, Inicio, Fin, Nota), más
  pequeña y al pie de la página.

### 3.5 Contexto externo (página 3 actual)

- Título de página: "Contexto externo: cobre, dólar y actividad".
- Quita la tabla de eventos y agrega las mismas líneas constantes X al gráfico de líneas.
- Barras de cobre con `Color Gobierno` y etiquetas de datos. Agrega al lado otras barras
  con `Dolar Promedio CLP`.
- Título del gráfico de cobre: "Precio promedio del cobre (USD nominales por libra)".

### 3.6 Chile frente a sus pares (nueva)

Responde si cada resultado fue propio de Chile o compartido con la región. Va después de
Contexto externo.

- Título de página: "Chile frente a sus pares: Perú, Colombia, México y Brasil".
- **Esta página no lleva el segmentador de desfase:** los datos son anuales.
- **Dos gráficos de barras, uno al lado del otro**, eje X `Gobiernos[etiqueta]`, color
  `Color Gobierno`, etiquetas de datos y línea constante Y en 0:
  - `Crecimiento vs Pares pp`, con el título "Crecimiento del PIB: Chile menos el promedio
    de sus pares (pp)".
  - `Inflacion vs Pares pp`, con el título "Inflación: Chile menos el promedio de sus pares
    (pp)".
- **Gráfico de líneas abajo:** eje X `Comparacion[anio]`, valores
  `Crecimiento Chile Anual %`, `Crecimiento Pares %` y `Crecimiento Mundo %`. Título
  "Crecimiento anual del PIB: Chile, pares y mundo (%)". Chile en línea gruesa oscura
  (`#2B2B2B`), y pares y mundo en gris claro, para que Chile resalte.
- **Matriz a la derecha:** filas `Gobiernos[etiqueta]`, valores `Deuda Chile FMI %`,
  `Deuda Pares %`, `Balance vs Pares pp`, `Control Corrupcion Chile` y
  `Control Corrupcion Pares`. Renombra los encabezados: "Deuda Chile (% PIB)", "Deuda pares
  (% PIB)", "Balance vs. pares (pp)", "Control de la corrupción, Chile" y "… pares".
- **Cuadro de texto de lectura**, bajo los gráficos de barras:
  "Barras sobre 0: Chile creció más (o tuvo más inflación) que el promedio de sus pares.
  La comparación separa una parte del contexto externo, pero no mide el efecto de las
  políticas de cada gobierno. El control de la corrupción es un índice de percepción del
  Banco Mundial (−2,5 a 2,5): los cambios pequeños no son concluyentes."
- **Pie de página:** `Fuente Comparacion` en vez de `Fuente`.

**Verificación:** `Crecimiento vs Pares pp` debe dar +0,63 en Piñera I y −0,61 en Boric;
`Inflacion vs Pares pp` debe dar −1,44 en Piñera I y +0,77 en Boric.

### 3.7 Sensibilidad al desfase (nueva)

Demuestra que el análisis revisa sus propios supuestos.

- **Esta página no lleva el segmentador de desfase:** desmárcala en Sincronizar segmentaciones.
- **Gráfico de columnas agrupadas:** eje X `Gobiernos[etiqueta]`, eje Y
  `Crecimiento IMACEC %`, leyenda `desfase_meses`, con etiquetas de datos. Título
  "Crecimiento promedio del IMACEC según el desfase supuesto (%)".
- **Matriz:** filas `Gobiernos[etiqueta]`, columnas `desfase_meses`, valores
  `Crecimiento IMACEC %` y `Desempleo Cambio pp`.
- **Cuadro de texto:** "Si los resultados se atribuyen al gobierno de 6 o 12 meses antes,
  las cifras cambian, pero el período más alto y el más bajo se mantienen. La diferencia
  entre los dos primeros baja de 2,0 a 0,7 puntos con 12 meses de desfase."

### 3.8 Metodología (página 4 actual)

- Agrega la "Síntesis" de [hallazgos.md](hallazgos.md) arriba del texto actual.
- Agrega una línea: "Eventos: shocks de alcance global o nacional con fechas documentadas
  por una fuente oficial (ver data/reference/eventos.csv)."
- Agrega un párrafo: "Comparación con pares: datos anuales del FMI (World Economic Outlook,
  octubre de 2026) y del Banco Mundial (WGI). Cada año se asigna al gobierno que gobernó la
  mayor parte de él, por eso las cifras anuales de Chile difieren levemente de las
  mensuales del Banco Central. Deuda y balance corresponden al gobierno general, una
  definición distinta de la del Gobierno Central que usa el resto del reporte."

## 4. Revisión final antes de exportar

- [ ] Ningún nombre técnico a la vista (`etiqueta`, `descripcion`, `desfase_meses`, `True/False`).
- [ ] Ningún subtítulo automático.
- [ ] El mismo color para cada gobierno en todas las páginas.
- [ ] Desfase 0 seleccionado en todas las páginas, salvo en Sensibilidad y en Chile frente a sus pares.
- [ ] La Ficha, con Piñera I, muestra crecimiento 5,43 y desempleo "8,5 → 6,2".
- [ ] La página de pares, con Piñera I, muestra +0,63 en crecimiento y −1,44 en inflación.
- [ ] **Archivo → Exportar → PDF** como `dashboard/chile_economia.pdf`.
- [ ] Capturas nuevas en `dashboard/capturas/` (una por página).
