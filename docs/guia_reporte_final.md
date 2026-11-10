# Guía del reporte final

Especificación de diseño para llevar el dashboard a su versión final. Complementa
[guia_dashboard.md](guia_dashboard.md), que explica la conexión y el modelo.

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
"Sensibilidad al desfase" (**Ver → Sincronizar segmentaciones**).

## 3. Páginas

Orden final: Resumen · Comparación · Ficha por gobierno · Series en el tiempo · Contexto
externo · Sensibilidad al desfase · Metodología.

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

### 3.6 Sensibilidad al desfase (nueva)

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

### 3.7 Metodología (página 4 actual)

- Agrega la "Síntesis" de [hallazgos.md](hallazgos.md) arriba del texto actual.
- Agrega una línea: "Eventos: shocks de alcance global o nacional con fechas documentadas
  por una fuente oficial (ver data/reference/eventos.csv)."

## 4. Revisión final antes de exportar

- [ ] Ningún nombre técnico a la vista (`etiqueta`, `descripcion`, `desfase_meses`, `True/False`).
- [ ] Ningún subtítulo automático.
- [ ] El mismo color para cada gobierno en todas las páginas.
- [ ] Desfase 0 seleccionado en todas las páginas, salvo en Sensibilidad.
- [ ] La Ficha, con Piñera I, muestra crecimiento 5,43 y desempleo "8,5 → 6,2".
- [ ] **Archivo → Exportar → PDF** como `dashboard/chile_economia.pdf`.
- [ ] Capturas nuevas en `dashboard/capturas/` (una por página).
