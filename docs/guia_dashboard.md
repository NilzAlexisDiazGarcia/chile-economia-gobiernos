# Guía para construir el dashboard en Power BI

Antes de empezar: PostgreSQL debe estar corriendo y la base cargada
(`python -m src.load.postgres`).

## 1. Guardar como proyecto (.pbip)

En Power BI Desktop: **Archivo → Opciones y configuración → Opciones → Características
en versión preliminar** y activa **"Guardar como Power BI Project (.pbip)"** si aparece
(en versiones recientes ya viene activado). Reinicia Power BI.

El formato `.pbip` guarda el informe y el modelo como archivos de texto. Git puede mostrar
qué cambió entre versiones, cosa que no puede hacer con un `.pbix`, que es un binario.

## 2. Conectarse a PostgreSQL

1. **Inicio → Obtener datos → Más… → Base de datos PostgreSQL.**
2. Servidor: `localhost` · Base de datos: `economia_chile` · Modo: **Importar**.
3. Credenciales: pestaña **Base de datos**, usuario `postgres` y la clave de tu `.env`.
   Power BI guarda la clave en tu equipo, **no** dentro del proyecto.
4. Si aparece un aviso sobre conexión sin cifrar, acéptalo: el servidor es local y no
   tiene SSL configurado. Para un servidor remoto habría que configurar SSL.
5. En el navegador, marca estas cuatro tablas:
   - `economia.v_pbi_observacion`
   - `economia.dim_gobierno`
   - `economia.dim_indicador`
   - `economia.dim_evento`
6. Haz clic en **Transformar datos** (no en Cargar).

## 3. Power Query

1. Renombra las consultas: `Observaciones`, `Gobiernos`, `Indicadores`, `Eventos`.
2. Revisa los tipos de dato de cada columna:

| Tabla | Columna | Tipo |
|---|---|---|
| Observaciones | `fecha` | Fecha |
| Observaciones | `valor`, `var_12m_pct` | Número decimal |
| Observaciones | `desfase_meses`, `id_gobierno` | Número entero |
| Observaciones | `es_transicion` | Verdadero/Falso |
| Gobiernos | `fecha_inicio`, `fecha_fin` | Fecha |
| Gobiernos | `en_alcance` | Verdadero/Falso |

3. **Cerrar y aplicar.**

## 4. Modelo

En la **Vista de modelo**, revisa que existan estas relaciones. Si Power BI no las detectó,
créalas arrastrando una columna sobre la otra.

| Desde (varios) | Hacia (uno) | Dirección del filtro |
|---|---|---|
| `Observaciones[id_gobierno]` | `Gobiernos[id_gobierno]` | Única |
| `Observaciones[indicador]` | `Indicadores[indicador]` | Única |

`Eventos` queda **sin relación**: se cruza con las observaciones por rangos de fechas, y
una relación de Power BI solo une valores exactos.

Además:

- En `Gobiernos`, selecciona `etiqueta` → **Herramientas de columnas → Ordenar por columna
  → `id_gobierno`**. Así los gobiernos aparecen en orden cronológico y no alfabético.
- Oculta las columnas técnicas (`id_gobierno` en `Observaciones`) para que no aparezcan
  en el panel de campos.

## 5. Tema y medidas

1. **Vista → Temas → Buscar temas** → `dashboard/tema.json`.
2. **Inicio → Especificar datos** → crea una tabla vacía llamada `Medidas`.
3. Las medidas ya vienen en el proyecto. Su código está en
   `dashboard/chile_economia.SemanticModel/definition/tables/Observaciones.tmdl`, organizado
   en carpetas y con una descripción por medida. Para cambiarlas, edítalas en Power BI o en
   ese archivo, con Power BI cerrado.
4. Borra la columna vacía de la tabla `Medidas`. Power BI la mostrará como tabla de medidas.

## 6. Filtros del informe

En el panel **Filtros → Filtros en todas las páginas**:

- `Gobiernos[en_alcance]` = **Verdadero**.

Y en cada página, un segmentador de `Observaciones[desfase_meses]`:

- **Selección única** activada, con valor 0 por defecto.
- **Vista → Sincronizar segmentaciones**, para que el desfase sea el mismo en todas las
  páginas.

## 7. Páginas

### Página 1: Resumen por gobierno

- **Matriz.** Filas: `Gobiernos[etiqueta]`. Valores: `Crecimiento PIB %`,
  `Crecimiento IMACEC %`, `Inflacion Promedio %`, `Desempleo Promedio %`,
  `Desempleo Cambio pp`, `Deuda Cambio pp`, `Balance Fiscal Promedio %`,
  `Cobre Promedio USD lb`.
- **Tarjeta** con `Texto Desfase`, como subtítulo.
- **Segmentadores:** `desfase_meses` y `es_transicion` (rotúlalo "Incluir períodos de
  transición").

**Verificación:** con desfase 0 y sin filtrar las transiciones, la matriz debe coincidir
con las consultas SQL. Por ejemplo, Piñera I tiene un crecimiento del PIB de 5,43 y Boric
un cambio de deuda de +6,2 pp. Si no coinciden, revisa las relaciones y los tipos de dato.

### Página 2: Series en el tiempo

- **Segmentador** de `Indicadores[descripcion]`, con selección única.
- **Gráfico de líneas 1:** eje X `Observaciones[fecha]`, eje Y `Valor Promedio`,
  leyenda `Gobiernos[etiqueta]`. Cada gobierno queda como un tramo de color distinto.
- **Gráfico de líneas 2:** lo mismo con `Var 12m Promedio`. Solo tiene datos para PIB,
  IMACEC y cobre.
- **Tabla** de `Eventos` (evento, fecha_inicio, fecha_fin, nota) debajo de los gráficos.

### Página 3: Contexto externo

- **Gráfico de líneas:** eje X `Observaciones[fecha]`, valores `Crecimiento IMACEC %` y
  `Cobre Var 12m %`. Muestra el ciclo de actividad junto al ciclo del cobre.
- **Gráfico de columnas:** `Cobre Promedio USD lb` por `Gobiernos[etiqueta]`.
- **Tabla** de eventos con sus notas.

### Página 4: Metodología

Cuadros de texto con:

- La regla de asignación (mayoría de días, 11 de marzo) y qué significa el desfase.
- Que la TPM la decide el Banco Central autónomo.
- Las limitaciones (sección 6 de `docs/metodologia.md`).
- La medida `Fuente`.

## 8. Reglas de neutralidad en el diseño

- **Colores sin asociación partidaria.** El tema evita el rojo y el azul como colores
  principales.
- **Orden cronológico**, nunca por resultado. No se ordenan los gobiernos de "mejor" a
  "peor".
- **Títulos descriptivos, no evaluativos:** "Variación anual promedio del PIB" y no
  "Gobierno con mejor crecimiento".
- **Mismo eje para todos** al comparar gobiernos.
- **El desfase y las transiciones siempre visibles,** para que el lector sepa qué supuesto
  está viendo.

## 9. Guardar y versionar

1. **Archivo → Guardar como →** carpeta `dashboard/`, nombre `chile_economia`, tipo
   **Power BI Project (.pbip)**. Se crean `chile_economia.pbip` y las carpetas
   `chile_economia.Report` (páginas y objetos visuales) y `chile_economia.SemanticModel`
   (tablas, relaciones y medidas en formato TMDL).
2. Toma capturas de cada página y guárdalas en `dashboard/capturas/`; irán en el README.
   Para que salga solo el lienzo: cierra los paneles Formato, Compilar y Datos (flechas
   **»**), haz clic en una zona vacía del lienzo y usa **Windows + Shift + S** con recorte
   rectangular. La captura queda en el portapapeles: guárdala desde la notificación de
   Recortes con **Ctrl+S**.
3. Revisa con `git status` que **no** aparezcan `cache.abf` ni `localSettings.json`, que
   están en el `.gitignore`. El proyecto no guarda datos ni claves: al abrirlo, Power BI
   pide las credenciales de PostgreSQL y recarga los datos desde las vistas.
