# Hallazgos

Observaciones descriptivas que salen de las consultas de `sql/analisis/`. Describen **qué
pasó en cada período**, no **por qué**: el análisis no separa el efecto de las políticas de
cada gobierno del ciclo externo, los eventos y las decisiones del Banco Central autónomo.
Las reglas de asignación y las limitaciones están en [metodologia.md](metodologia.md).

Salvo que se diga otra cosa, las cifras usan la asignación principal (mayoría de días, sin
desfase) e incluyen los períodos de transición.

## Síntesis

Entre 2006 y 2026 la economía chilena cambió de régimen, y ese cambio atraviesa a los
cinco gobiernos:

1. **Menos crecimiento.** El PIB creció 4,3 % anual en promedio entre 2006 y 2014, y
   2,1 % entre 2014 y 2026. Ningún período posterior a 2014 promedia más de 3 %.
2. **Más deuda.** La deuda bruta del Gobierno Central pasó de 6 % a 42 % del PIB y subió
   en los cinco períodos. Los superávits fiscales de 2006–2008 (entre 4 % y 8 % del PIB) no
   se repitieron: desde 2009 solo hubo superávit en 2011, 2012 y 2022, todos bajo 1,3 %.
3. **Inflación más volátil.** La inflación estuvo dentro del rango meta del Banco Central
   (2 % a 4 %) en el 48 % de los meses. Sus dos máximos (2008 y 2022) coinciden con alzas
   mundiales de precios.

Lo que distingue a cada gobierno es **el punto de partida y el contexto**: dos de ellos
enfrentaron las mayores contracciones del período (2009 y 2020), los precios del cobre
fueron muy distintos entre un período y otro, y dos gobiernos recibieron la economía
saliendo de una crisis (en 2010 y en 2022). El reporte muestra ese contexto junto a cada
resultado y no estima cuánto de cada resultado se debe a las políticas de cada gobierno.

## 1. Crecimiento: el promedio más alto se registró en 2010–2014, en un contexto de rebote

| Gobierno | PIB, var. anual prom. (%) | IMACEC, var. anual prom. (%) |
|---|---:|---:|
| Bachelet I | 3,23 | 3,35 |
| Piñera I | 5,43 | 5,38 |
| Bachelet II | 1,90 | 1,85 |
| Piñera II | 2,65 | 2,64 |
| Boric | 1,64 | 1,77 |

- El período 2010–2014 empieza justo después de la recesión de 2009 y del terremoto de
  febrero de 2010. Parte de su crecimiento corresponde a la recuperación desde una base baja
  y a la reconstrucción.
- Desde 2014, ningún período promedia más de 3 % de crecimiento anual.
- En Piñera II, el promedio de 2,64 % junta la caída de 2020 (−16 % en el peor mes) con el
  rebote de 2021 (+20 %). Un promedio esconde esa volatilidad; el gráfico de la página 2 del
  dashboard la muestra.

## 2. El supuesto de desfase cambia las cifras, pero no el orden de los extremos

Variación anual promedio del IMACEC según cuántos meses se demora la economía en reflejar
a un gobierno:

| Gobierno | Sin desfase | 6 meses | 12 meses |
|---|---:|---:|---:|
| Bachelet I | 3,35 | 3,36 | 3,53 |
| Piñera I | 5,38 | 4,83 | 4,20 |
| Bachelet II | 1,85 | 2,21 | 2,25 |
| Piñera II | 2,64 | 2,51 | 2,11 |
| Boric | 1,77 | 1,29 | 1,54 |

- Con 12 meses de desfase, la diferencia entre el período más alto y el siguiente baja de
  2,0 a 0,7 puntos, y Bachelet II y Piñera II intercambian posiciones.
- El período 2010–2014 sigue arriba y el de Boric abajo con los tres supuestos.
- Con desfase de 12 meses, Boric tiene 43 meses de datos y no 48: los últimos aún no se
  publican.

## 3. Inflación: el máximo de la serie se registró en 2022

| Gobierno | IPC prom. (%) | IPC máx. (%) | TPM mín.–máx. (%) |
|---|---:|---:|---|
| Bachelet I | 4,33 | 9,9 | 0,50–8,25 |
| Piñera I | 2,54 | 4,4 | 0,50–5,25 |
| Bachelet II | 3,64 | 5,7 | 2,50–4,25 |
| Piñera II | 3,29 | 7,8 | 0,50–5,50 |
| Boric | 6,72 | 14,1 | 4,50–11,25 |

El IPC es la variación a 12 meses oficial publicada por el INE, con un decimal.

- Los dos máximos de inflación (9,9 % en octubre de 2008 y 14,1 % en agosto de 2022) coinciden con alzas
  internacionales de precios: de alimentos y energía en 2008, y posteriores a la pandemia
  en 2022.
- La Tasa de Política Monetaria la fija el Banco Central, que es autónomo. Su máximo
  (11,25 %) se dio en el mismo período que el máximo de inflación.

Meses con inflación dentro del rango meta del Banco Central (3 % ± 1 punto):

| Gobierno | Meses en rango | Inflación prom. − meta (pp) |
|---|---:|---:|
| Bachelet I | 38 % | +1,33 |
| Piñera I | 67 % | −0,46 |
| Bachelet II | 38 % | +0,64 |
| Piñera II | 75 % | +0,29 |
| Boric | 21 % | +3,72 |

- La meta es una referencia externa a los gobiernos: la fija y la persigue el Banco Central.
  Por eso sirve para comparar períodos sin usar un criterio propio.
- En los períodos con menos meses en el rango, la inflación estuvo sobre la meta: en 2008
  (alza mundial de alimentos y energía), en 2014–2016 (hasta 5,7 %, en años de
  depreciación del peso) y en 2021–2023 (alza mundial de inflación).

## 4. Desempleo: el máximo fue en 2020 y la única baja neta ocurrió en 2010–2014

| Gobierno | Heredado (%) | Final (%) | Cambio (pp) | Máximo (%) |
|---|---:|---:|---:|---:|
| Bachelet I | 7,80 | 8,53 | +0,73 | 10,76 |
| Piñera I | 8,53 | 6,18 | −2,35 | 9,23 |
| Bachelet II | 6,18 | 7,01 | +0,83 | 7,33 |
| Piñera II | 7,01 | 7,50 | +0,49 | 13,09 |
| Boric | 7,50 | 8,33 | +0,83 | 9,00 |

- El máximo de la serie (13,1 %) se registró en 2020, durante la pandemia.
- Piñera I es el único período que termina con menos desempleo que el que recibió. Empezó
  desde un nivel alto, posterior a la crisis de 2009.

## 5. Deuda pública: subió en los cinco períodos

| Gobierno | Deuda heredada (% PIB) | Deuda final (% PIB) | Cambio (pp) | Balance prom. (% PIB) |
|---|---:|---:|---:|---:|
| Bachelet I | 6,4 | 6,5 | +0,1 | +3,67 |
| Piñera I | 6,5 | 12,7 | +6,2 | +0,20 |
| Bachelet II | 12,7 | 23,6 | +10,9 | −2,32 |
| Piñera II | 23,6 | 36,2 | +12,6 | −4,88 |
| Boric | 36,2 | 42,4 | +6,2 | −1,73 |

- La deuda bruta pasó de 6 % a 42 % del PIB en veinte años. Es una tendencia que atraviesa a
  todos los gobiernos, no un quiebre puntual.
- El alza más grande (+12,6 pp) y el déficit promedio más profundo (−4,9 % del PIB)
  incluyen el gasto de la pandemia en 2020 y 2021.
- Bachelet I es el único período con superávit promedio, en años de precios del cobre
  altos. Aun así, incluye el déficit de 2009 (−4,4 %).

## 6. Contexto externo: el cobre y el dólar

| Gobierno | Cobre prom. (USD/lb) | Cobre var. anual prom. (%) | Dólar prom. (CLP) |
|---|---:|---:|---:|
| Bachelet I | 2,98 | 22,3 | 533 |
| Piñera I | 3,59 | 8,8 | 495 |
| Bachelet II | 2,65 | −1,1 | 640 |
| Piñera II | 3,23 | 13,9 | 734 |
| Boric | 4,19 | 3,3 | 905 |

- Bachelet II es el único período con precio del cobre en baja en promedio. También es el de
  menor precio promedio.
- El precio del cobre está en dólares nominales, sin ajustar por inflación de EE.UU. Por eso
  los niveles de períodos distantes no son directamente comparables. La variación anual sí lo es.
- El dólar subió de 531 a 916 pesos entre 2006 y 2026, con el mayor salto en 2018–2022.

## 7. Eventos: la pandemia generó la mayor caída de actividad

| Evento | IMACEC antes (%) | IMACEC peor mes (%) | Desempleo máx. (%) |
|---|---:|---:|---:|
| Crisis financiera global (2008) | 5,19 | −3,67 | 10,76 |
| Terremoto 27F (2010) | −0,84 | 0,31 | 9,23 |
| Estallido social (2019) | 2,33 | −15,98 | 13,09 |
| Pandemia COVID-19 (2020) | 0,81 | −15,98 | 13,09 |
| Alza mundial de inflación (2021–2023) | −6,87 | −2,87 | 10,35 |

- El peor mes del estallido y de la pandemia es el mismo porque sus ventanas se superponen.
  Ese −16 % corresponde a la pandemia: el análisis no puede separar ambos efectos.
- El IMACEC "antes" del alza mundial de inflación es negativo porque esos 12 meses son los
  de la pandemia.
- El terremoto ocurrió cuando la economía venía saliendo de la recesión. Por eso el IMACEC
  "antes" es negativo.

## 8. Frente a sus pares, la lectura de dos períodos cambia

Diferencia entre Chile y el promedio de Perú, Colombia, México y Brasil, con datos anuales
del FMI (detalle y fuentes en [contexto_comparado.md](contexto_comparado.md)):

| Gobierno | Crecimiento del PIB (pp) | Inflación (pp) | Balance fiscal (pp) |
|---|---:|---:|---:|
| Bachelet I | −0,31 | +0,13 | +5,01 |
| Piñera I | +0,63 | −1,44 | +2,01 |
| Bachelet II | +0,11 | −0,98 | +1,57 |
| Piñera II | +1,09 | −0,63 | −0,01 |
| Boric | −0,61 | +0,77 | +3,11 |

- **Bachelet II** tiene el crecimiento más bajo en cifras absolutas, pero la región creció
  aún menos, y Chile quedó levemente sobre sus pares.
- **Piñera II** incluye la caída de 2020, que fue mundial. Frente a sus pares es el período
  con la mayor diferencia de crecimiento a favor de Chile.
- **Boric** tuvo crecimiento e inflación en contra frente a sus pares, y un déficit fiscal
  bastante menor que el de ellos.
- **Ningún período destaca en todos los indicadores.** Por eso el reporte no construye un
  ranking.

## Cómo reproducir estas cifras

```bash
python -m src.load.postgres
python -m src.analysis.ejecutar_consultas
```
