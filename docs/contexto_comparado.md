# Contexto comparado: Chile frente a sus pares

> Los datos se cargan en PostgreSQL (`fact_internacional`, vista `v_pbi_comparacion`) y
> alimentan la página "Chile frente a sus pares" del dashboard. Las cifras salen de la
> consulta `sql/analisis/08_comparacion_pares.sql`.

Este documento responde a una pregunta que los datos de Chile por sí solos no pueden
contestar: **¿a cada gobierno le fue mejor o peor que a países comparables en los mismos
años?** Si toda la región crece poco, crecer poco no dice lo mismo que si la región crece
mucho. Comparar con pares separa una parte del contexto externo del resultado local. Aun
así, no mide el efecto de las políticas de cada gobierno: sigue siendo una descripción.

## Datos y reglas

| Fuente | Indicadores | Cobertura |
|---|---|---|
| FMI, World Economic Outlook (octubre de 2026) | Crecimiento del PIB, inflación promedio, desempleo, deuda bruta y balance del gobierno general | 2000–2025 (2026 es proyección y se excluye) |
| Banco Mundial, Worldwide Governance Indicators | Control de la corrupción (−2,5 a 2,5) | 2000–2025 |

- **Zonas:** Chile, América Latina y el Caribe, el mundo y cuatro pares regionales con metas
  de inflación: Perú, Colombia, México y Brasil.
- **Asignación anual:** cada año va al gobierno que gobernó la mayor parte de él. Como el
  cambio de mando es el 11 de marzo, el año en que asume un gobierno es suyo (unos 295
  días). Bachelet I: 2006–2009; Piñera I: 2010–2013; Bachelet II: 2014–2017; Piñera II:
  2018–2021; Boric: 2022–2025.
- **Datos del FMI, no del Banco Central:** el FMI mide deuda y balance del **gobierno
  general**, y el resto del proyecto los mide para el Gobierno Central. Por eso las cifras
  difieren algo de las de [hallazgos.md](hallazgos.md). Se usan solo para comparar países,
  con una misma definición para todos.
- **Inflación:** el agregado de América Latina incluye a Argentina y Venezuela, cuya
  inflación muy alta lo distorsiona (13,3 % en 2022–2025). La comparación usa el promedio de
  los cuatro pares.
- **Corrupción:** el promedio de pares usa los cuatro países. Una primera descarga no trajo
  Colombia por fallas de la API del Banco Mundial; se completó después.

Para reproducir:

```bash
python -m src.extract.internacional
python -m src.load.postgres
python -m src.analysis.ejecutar_consultas 08
```

## 1. Crecimiento: tres períodos sobre los pares, uno similar y uno bajo

| Gobierno | Chile | América Latina | Mundo | Pares (4) | Chile − pares (pp) |
|---|---:|---:|---:|---:|---:|
| Bachelet I | 3,48 | 3,10 | 3,30 | 3,79 | −0,31 |
| Piñera I | 5,40 | 4,08 | 4,05 | 4,77 | +0,63 |
| Bachelet II | 1,80 | 0,65 | 3,55 | 1,69 | +0,11 |
| Piñera II | 2,45 | 0,48 | 2,65 | 1,36 | +1,09 |
| Boric | 2,03 | 2,93 | 3,53 | 2,64 | −0,61 |

Variación anual promedio del PIB real, en porcentaje.

- **Comparar con pares cambia la lectura de dos períodos:**
  - En cifras absolutas, Bachelet II tiene el crecimiento más bajo de los cinco. Pero la
    región creció aún menos (0,65 %, con Brasil en recesión), y Chile quedó levemente sobre sus
    pares.
  - Piñera II incluye la caída de 2020, pero esa caída fue mundial. Frente a sus pares, es
    el período con la mayor diferencia a favor de Chile (+1,09 pp).
- **Dos períodos quedaron bajo sus pares:** Bachelet I (−0,31 pp) y Boric (−0,61 pp).
  Durante el de Boric, la región creció más que Chile.
- **Desde 2014, Chile crece menos que el mundo en todos los períodos.** Es una señal del
  menor crecimiento de largo plazo que describe el FMI en la sección 5.

## 2. Inflación: bajo los pares en tres períodos, sobre ellos en dos

| Gobierno | Chile | Mundo | Pares (4) | Chile − pares (pp) |
|---|---:|---:|---:|---:|
| Bachelet I | 4,50 | 4,25 | 4,37 | +0,13 |
| Piñera I | 2,38 | 4,03 | 3,81 | −1,44 |
| Bachelet II | 3,75 | 2,98 | 4,73 | −0,98 |
| Piñera II | 3,03 | 3,80 | 3,65 | −0,63 |
| Boric | 6,83 | 6,33 | 6,06 | +0,77 |

Inflación promedio anual, en porcentaje.

- **El alza de 2022–2023 fue mundial.** Aun así, Chile quedó 0,77 pp sobre sus pares. El
  Banco Central lo atribuye sobre todo a factores locales (sección 5).
- **La inflación de 2014–2016,** que dejó a Bachelet II fuera del rango meta en muchos
  meses, fue menor que la de sus pares (−0,98 pp).

## 3. Desempleo: no se compara entre países

El FMI publica el desempleo de cada país, pero **los niveles no son comparables**: cada
país lo mide de forma distinta, y donde la informalidad es alta, como en México, el
desempleo medido es bajo aunque el mercado laboral sea débil. Por eso el reporte no
compara el desempleo de Chile con el de sus pares, y lo analiza solo frente a lo que
recibió cada gobierno ([hallazgos.md](hallazgos.md), sección 4). Los datos quedan en
`fact_internacional` por si se quiere revisar la dirección de los cambios.

## 4. Deuda y balance: Chile partió con mucho espacio y lo fue usando

| Gobierno | Deuda Chile | Deuda pares | Balance Chile | Balance pares |
|---|---:|---:|---:|---:|
| Bachelet I | 4,9 | 41,7 | +3,78 | −1,23 |
| Piñera I | 11,1 | 40,2 | +0,30 | −1,71 |
| Bachelet II | 19,3 | 49,1 | −2,23 | −3,79 |
| Piñera II | 30,7 | 58,2 | −4,70 | −4,69 |
| Boric | 40,2 | 58,8 | −1,63 | −4,74 |

Gobierno general, promedio anual en % del PIB.

- **Chile sigue teniendo menos deuda que sus pares,** pero la diferencia se redujo de 37 pp
  a 19 pp. La deuda subió más rápido en Chile que en la región.
- **El balance de Chile fue mejor que el de sus pares en cuatro de los cinco períodos.** La
  excepción es Piñera II, que incluye el gasto de la pandemia y quedó igual que sus pares.
- **En 2022–2025, el déficit de Chile (−1,6 %) fue menor que el de sus pares (−4,7 %),**
  después de los déficits de la pandemia.

## 5. Por qué pasó: lo que dijeron el Banco Central y el FMI en su momento

Explicaciones de las instituciones técnicas, **en sus propias palabras**, en el año
correspondiente. Estas citas no salen del análisis propio, y no son juicios sobre
los gobiernos.

| Período | Tema | Explicación oficial | Fuente |
|---|---|---|---|
| 2008 | Inflación | "El origen de nuestro problema inflacionario es externo, pero la situación actual responde también a desarrollos internos, en particular una mayor propagación." | Banco Central de Chile, Boletín Mensual de septiembre de 2008, presentación de política monetaria, p. 14 |
| 2009–2010 | Recesión y terremoto | Chile "withstood two consecutive large negative shocks" (la crisis financiera global y el terremoto). La reconstrucción "should continue to boost growth". | FMI, Public Information Notice 10/136, 29 de septiembre de 2010 |
| 2014 | Desaceleración | "the sharp fall in private investment, mainly the consequence of the end of the mining boom". También menciona la "uncertainty and adjustment costs associated with the structural reform agenda". | FMI, Press Release 15/373, 6 de agosto de 2015 |
| 2018 | Recuperación | "Economic growth in the first half of 2018 has been the strongest since 2012", tras la desaceleración que empezó con la caída del cobre en 2011. | FMI, Press Release 18/414, 9 de noviembre de 2018 |
| 2020 | Pandemia | "Economic activity contracted by 6 percent in 2020". Sobre los retiros de fondos de pensiones: "poorly targeted, regressive, and have weakened the pension system". | FMI, Staff Concluding Statement, 9 de marzo de 2021 |
| 2021 | Inflación | La inflación se explica "fundamentalmente por la extraordinaria expansión de la demanda interna y la depreciación del peso causada por factores idiosincráticos", que se suman a fenómenos globales. | Banco Central de Chile, IPoM de diciembre de 2021, Resumen, p. 3 |
| 2021 | Dólar | La depreciación del peso respondió a "factores idiosincráticos": la incertidumbre y el mayor riesgo percibido en Chile, "a pesar del alto precio del cobre". | Banco Central de Chile, IPoM de diciembre de 2021, p. 44 |
| 2024 | Inflación y crecimiento | Crecimiento "close to its potential pace". La inflación volvería a la meta de 3 % a comienzos de 2026. Elevar el crecimiento potencial es "essential to raise living standards". | FMI, Press Release 25/027, 5 de febrero de 2025 |

- **Sobre la inflación de 2021:** el IPoM la atribuye a factores locales y globales. La
  expansión de la demanda se dio con las transferencias del Estado y los tres retiros de
  fondos de pensiones (julio y diciembre de 2020, y abril de 2021). Los retiros fueron leyes
  aprobadas por el Congreso.

## 6. Control de la corrupción

| Gobierno | Chile | Pares (4) |
|---|---:|---:|
| Bachelet I | 1,42 | −0,27 |
| Piñera I | 1,49 | −0,28 |
| Bachelet II | 1,19 | −0,53 |
| Piñera II | 1,16 | −0,52 |
| Boric | 1,11 | −0,58 |

Banco Mundial, puntaje de −2,5 a 2,5 (más alto = mejor control), promedio por gobierno.

- **Chile está muy sobre sus pares en todos los períodos,** con una diferencia estable cercana
  a 1,7 puntos.
- **El puntaje de Chile bajó entre 2014 y 2015** (de 1,39 a 1,15) y desde entonces se mantiene
  cerca de 1,1. En la región también bajó.
- **Cómo leerlo:**
  - Es un índice de **percepción**, construido con encuestas y evaluaciones de expertos.
    No cuenta casos.
  - Cada año se estandariza contra el resto del mundo, y tiene márgenes de error. Los cambios
    pequeños entre años no son concluyentes.
  - Que se revelen casos puede bajar la percepción aunque refleje instituciones que
    investigan mejor.
  - La baja de 2014–2015 coincide con la revelación de casos de financiamiento irregular de
    la política. Esos casos involucraron a empresas y a políticos de distintos sectores, y
    los hechos ocurrieron antes de 2014. Atribuir la baja al gobierno de turno sería un error.

## 7. Qué cambia en la lectura del proyecto

1. **Los cinco gobiernos enfrentaron contextos muy distintos.** Comparar con pares permite
   decir cuánto se alejó Chile de lo que pasaba en la región en ese momento.
2. **Ningún gobierno destaca en todos los indicadores frente a sus pares:**
   - Piñera I: crecimiento e inflación a favor.
   - Bachelet II: crecimiento levemente a favor e inflación a favor, con más deuda.
   - Piñera II: crecimiento e inflación a favor, con el déficit más alto.
   - Boric: balance fiscal mucho mejor que el de sus pares (+3,1 pp), con crecimiento e
     inflación en contra.
   - Bachelet I: el mejor balance, absoluto y frente a sus pares, con un crecimiento algo
     bajo el de sus pares.
3. **Por eso el reporte no construye un ranking.** Muestra las diferencias frente a los pares
   indicador por indicador, para que cada lector vea en qué destacó cada período sin un
   número final que diga cuál fue "el mejor".

## Fuentes

- FMI, World Economic Outlook, octubre de 2026 (API DataMapper): https://www.imf.org/external/datamapper
- Banco Mundial, Worldwide Governance Indicators (API, fuente 3): https://api.worldbank.org/v2/sources/3
- Banco Central de Chile, Boletín Mensual, septiembre de 2008: https://si3.bcentral.cl/estadisticas/Principal1/informes/boletin/pdf/BM092008.pdf
- Banco Central de Chile, IPoM de diciembre de 2021: https://www.bcentral.cl/documents/33528/3314166/IPoM_Diciembre_2021.pdf
- FMI, PIN 10/136 (2010): https://www.imf.org/external/np/sec/pn/2010/pn10136.htm
- FMI, PR 15/373 (2015): https://www.imf.org/external/np/sec/pr/2015/pr15373.htm
- FMI, PR 18/414 (2018): https://www.imf.org/en/news/articles/2018/11/09/pr18414-chile-imf-executive-board-concludes-2018-article-iv-consultation
- FMI, Staff Concluding Statement (2021): https://www.imf.org/en/News/Articles/2021/03/09/mcs030921-chile-staff-concluding-statement-of-the-2021-article-iv-mission
- FMI, PR 25/027 (2025): https://www.imf.org/en/News/Articles/2025/02/04/pr25027-chile-imf-executive-board-concludes-2024-article-iv-consultation
