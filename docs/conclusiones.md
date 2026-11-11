# Conclusiones: por qué Chile dejó de crecer y se endeudó

Este documento reúne lo que muestran los datos del proyecto y **por qué ocurrió**, según las
instituciones técnicas que lo estudiaron: el Banco Central, el FMI, la DIPRES, el Consejo
Fiscal Autónomo (CFA) y la Comisión Nacional de Evaluación y Productividad (CNEP). Las
causas no son una opinión del autor: cada una lleva su fuente. Las cifras salen de los datos
del proyecto y están verificadas por la auditoría (`python -m src.analysis.auditoria`).

## La conclusión en una frase

> **Entre 2006 y 2026, Chile pasó de crecer rápido y ahorrar a crecer poco y endeudarse. Fue
> un cambio estructural, que comenzó con el fin del auge del cobre y la caída de la
> productividad, y que ningún gobierno revirtió. Los gobiernos no causaron ese cambio, pero sí
> lo agravaron: todos gastaron, en forma permanente, más de lo que la economía generaba en
> forma permanente. Al mismo tiempo, la pobreza bajó con fuerza, porque los ingresos y las
> transferencias siguieron creciendo aun con poco crecimiento.**

---

## 1. Por qué Chile dejó de crecer

### Lo que muestran los datos

| | 2006–2013 | 2014–2025 |
|---|---:|---:|
| Crecimiento del PIB, mediana anual | 5,5 % | 1,9 % |
| Crecimiento del **PIB por habitante**, promedio anual | **3,4 %** | **1,0 %** |
| Años con caída del PIB por habitante | 1 (2009) | 4 (2017, 2019, 2020 y 2023) |

**Desde 2014 el ingreso por habitante casi se estancó.** No hubo una recesión formal salvo en
2020, pero en cuatro de esos doce años el ingreso promedio de cada chileno cayó. La
inmigración de 2015–2019 hizo crecer la población más rápido (1,3 % a 1,6 % al año), así que
el PIB total creció más que el ingreso de cada persona.

### Las causas, según las fuentes técnicas

**1. La productividad se estancó.** Es la causa de fondo. Según la CNEP, la productividad total
de factores lleva unos 16 años sin aportar al crecimiento: en 2024 varió entre −0,2 % y 0,1 %.
La CNEP atribuye el estancamiento a:
- La desaceleración de la productividad mundial.
- Una mala asignación de los recursos y la rigidez del mercado laboral.
- **Las deficiencias del Estado en la entrega de permisos para invertir.**
- En la minería, la caída de la ley del mineral (hay que mover más roca por cada tonelada de
  cobre) y la menor producción de Codelco.

**2. Terminó el auge del cobre y cayó la inversión.** Entre 2004 y 2012 el precio del cobre y la
inversión minera empujaron el crecimiento por sobre su ritmo sostenible. Según el FMI, la
desaceleración de 2014 vino de "la fuerte caída de la inversión privada, principalmente
consecuencia del fin del auge minero" (Press Release 15/373, 2015). La DIPRES fecha en 2013
el inicio del impacto del fin del superciclo en las finanzas públicas.

**3. La capacidad de crecer se redujo a la mitad.** En 2011 el comité de expertos de la DIPRES
estimaba un crecimiento tendencial de 4,8 % a 4,9 %. Hoy el Banco Central lo estima en
**1,9 %–2,0 % para 2024–2035**, con una productividad que aporta solo 0,35 % al año (IPoM de
diciembre de 2023 y de marzo de 2026). Con ese techo, crecer 2 % no es una crisis: es el ritmo
que la economía permite hoy.

**4. Hubo episodios de incertidumbre local que frenaron la inversión.**
- **2014:** el FMI menciona "la incertidumbre y los costos de ajuste asociados a la agenda de
  reformas estructurales".
- **2021:** el Banco Central atribuye la depreciación del peso a "factores idiosincráticos",
  como la elevada incertidumbre y el mayor riesgo percibido en Chile.

**En síntesis:** Chile crecía por el cobre y por una productividad que avanzaba. Las dos cosas
se acabaron entre 2008 y 2014, y nada las reemplazó.

---

## 2. Por qué Chile se endeudó

### Lo que muestran los datos

- La deuda bruta del Gobierno Central pasó de **6 % a 42 % del PIB**, y subió en los cinco
  períodos.
- La deuda neta pasó de **−19 % del PIB en 2008**, cuando el Fisco tenía más activos que
  deudas, a **26 %** a comienzos de 2026.
- El balance estructural fue negativo en casi todos los años desde 2008; solo hubo superávit
  estructural en 2015 y 2022.
- El FEES, el fondo para crisis, llegó a US$ 20.211 millones en 2008 y bajó a US$ 3.944
  millones en 2026.

### Las causas, según las fuentes técnicas

**1. Se gastó, en forma permanente, más de lo que entraba en forma permanente.** Es la causa
principal y atraviesa a todos los gobiernos.
- Entre 2008 y 2023, el gasto público promedió 23,8 % del PIB, frente a ingresos
  estructurales de 22 % (CFA, informe del 23 de abril de 2024).
- En los datos del proyecto, el balance efectivo fue negativo en 14 de los 17 años entre
  2009 y 2025. Solo hubo superávit en 2011, 2012 y 2022.

**2. El menor crecimiento redujo los ingresos estructurales.** Con menos crecimiento tendencial
y un precio de referencia del cobre más bajo, el Fisco espera recaudar menos. Así lo explicó
la DIPRES en 2015, al modificar la meta de Bachelet II (Decreto 1.378). **El bajo crecimiento y
la deuda se alimentan entre sí:** menos crecimiento significa menos recaudación, más déficit
y más deuda.

**3. Dos shocks extraordinarios obligaron a gastar.**
- La crisis de 2009, financiada en parte con el FEES.
- La pandemia de 2020–2021, que llevó el déficit estructural de 2021 a −10,7 %, el mayor desde
  que existe la regla (DIPRES).

**4. La regla fiscal no tenía con qué hacerse cumplir.** Según la DIPRES, sin cláusulas de escape
ni mecanismos de corrección, las metas "han sido modificadas a discreción de la autoridad":
la meta inicial de cada gobierno se cumplió en solo 9 de 21 años. Recién en 2022 se fijó por
primera vez un ancla de deuda (45 % del PIB), y en 2024 la ley agregó cláusulas de escape.

**5. La deuda se volvió más cara.** Piñera II fue el gobierno que más deuda sumó (12,6 puntos
del PIB), con las tasas reales más bajas del período: 0,9 % en UF a 10 años en promedio.
Desde 2022 las tasas subieron en todo el mundo (2,3 % real con Boric), y el gasto en intereses
pasó de 0,47 % del PIB en 2008 a 1,24 % en 2025, el más alto desde 2005. Ese gasto no financia
ningún servicio y reduce el espacio para todo lo demás.

**6. En los años recientes se sobrestimaron los ingresos.** Según el CFA, el incumplimiento de
2025 responde a "errores reiterados y significativos en la proyección de ingresos fiscales",
junto con gasto por sobre lo comprometido.

---

## 3. Aciertos y problemas de cada gobierno, y por qué

Criterios uniformes en [hallazgos.md](hallazgos.md), sección 9, y metas fiscales en
[metas_fiscales.md](metas_fiscales.md).

### Bachelet I (2006–2010)

**Aciertos:**
- Ahorró durante el auge del cobre: creó los fondos soberanos y dejó al Fisco como acreedor
  neto, con una deuda neta de −9,8 % del PIB.
- La pobreza bajó de 29,1 % a 25,3 %.
- Ese ahorro permitió gastar en la crisis sin endeudarse: el FMI destaca que Chile "resistió
  dos grandes shocks negativos consecutivos".

**Problemas:**
- No cumplió su meta fiscal en 2008 ni en 2009. En 2008 gastó por sobre lo presupuestado y en
  2009 aplicó un plan de estímulo deliberado contra la crisis (DIPRES).
- La inflación llegó a 9,9 % en 2008. Su origen fue "principalmente externo", por los precios
  de los alimentos y los combustibles (Banco Central).
- El desempleo subió con la recesión de 2009.

**Por qué:** le tocó la mejor parte del ciclo del cobre, y también la peor crisis mundial en
décadas.

### Piñera I (2010–2014)

**Aciertos:**
- El crecimiento más alto del período: 5,4 % anual, 0,6 puntos sobre sus pares.
- El desempleo bajó de 8,5 % a 6,2 %, el único gobierno que lo redujo.
- La pobreza bajó de 25,3 % a 14,4 %, la mayor reducción del período.
- La inflación estuvo en el rango meta el 67 % de los meses.
- Cumplió su meta fiscal vigente.

**Problemas:**
- La meta que cumplió se había flexibilizado al inicio: con la de su decreto inicial, que
  fijaba equilibrio, no la habría cumplido.
- La deuda neta subió, de −9,8 % a −6,2 % del PIB.

**Por qué:** parte del crecimiento fue rebote desde la recesión de 2009 y gasto de
reconstrucción tras el terremoto (FMI), con el precio del cobre en su máximo. El fin del auge
comenzó a sentirse en 2013.

### Bachelet II (2014–2018)

**Aciertos:**
- Chile creció levemente sobre sus pares (+0,1 punto), en años de recesión en Brasil y de caída
  del cobre.
- La pobreza bajó de 14,4 % a 8,6 % y los salarios reales subieron 1,8 % al año.

**Problemas:**
- El crecimiento por habitante fue el más bajo del período: 0,5 % al año.
- No cumplió su meta fiscal en 2017 (−2,0 % frente a −1,05 %), sin un shock extraordinario.
- La deuda neta pasó a ser positiva, y el FEES bajó levemente, de US$ 15.774 a 14.851 millones.
- La inflación estuvo fuera del rango meta en el 62 % de los meses.

**Por qué:** según el FMI, el fin del auge minero hizo caer la inversión, a lo que se sumaron
"la incertidumbre y los costos de ajuste" de las reformas. La DIPRES rebajó la meta fiscal en
2015 por la caída del cobre y del crecimiento tendencial.

### Piñera II (2018–2022)

**Aciertos:**
- En la crisis más profunda del período, Chile creció más que sus pares (+1,1 puntos).
- La inflación estuvo en el rango meta el 75 % de los meses.
- En 2018 el crecimiento fue "el más fuerte desde 2012" (FMI).

**Problemas:**
- En 2021, el mayor déficit estructural desde que existe la regla (−10,7 %).
- El FEES bajó de US$ 14.851 a 6.406 millones: llegó a 2.457 a fines de 2021 y se volvió a
  capitalizar antes del cambio de mando.
- La pobreza subió de 8,6 % a 10,8 % en la pandemia.
- Fue el que más deuda tomó: la deuda bruta pasó de 23,6 % a 36,2 % del PIB. Lo hizo con las
  tasas reales más bajas del período (0,9 %), lo que contuvo el gasto en intereses.
- Entregó la economía con la inflación subiendo (7,8 % en febrero de 2022).

**Por qué:** el estallido social de 2019 y la pandemia obligaron a gastos de emergencia. El
FMI calificó los retiros de fondos de pensiones, aprobados por el Congreso, de "mal
focalizados y regresivos". Según el Banco Central, la inflación de 2021 se explicó
"fundamentalmente por la extraordinaria expansión de la demanda interna".

### Boric (2022–2026)

**Aciertos:**
- En 2022 cumplió la meta fiscal, con el primer superávit estructural desde 2015.
- La pobreza bajó a 4,9 % en la medición comparable (17,3 % con la metodología nueva, desde
  20,5 % en 2022).
- La inflación volvió a la meta a comienzos de 2026 (FMI).

**Problemas:**
- No cumplió la meta fiscal en 2024 ni en 2025, sin un shock extraordinario: −3,6 % frente a
  −1,6 % en 2025.
- Creció 0,6 puntos bajo sus pares.
- La inflación estuvo fuera del rango meta en el 79 % de los meses, y los salarios reales cayeron
  en 2022.
- El gasto en intereses subió de 0,86 % a 1,24 % del PIB, por la deuda heredada y las tasas más
  altas (2,3 % real a 10 años, frente a 0,9 % con Piñera II).
- El FEES bajó de US$ 6.406 a 3.944 millones sin una crisis, y la deuda bruta subió de 36,2 %
  a 42,4 % del PIB. El total de los fondos se mantuvo solo porque el FRP recibe aportes
  obligatorios por ley.

**Por qué:** heredó una economía sobrecalentada, con la inflación en camino a 14,1 %, lo que
obligó al Banco Central a subir la tasa hasta 11,25 % y enfrió la economía en 2022–2023. En
lo fiscal, el CFA atribuye los incumplimientos a "errores reiterados" en la proyección de
ingresos y a gasto por sobre lo comprometido.

---

## 4. Lo que estos datos no permiten decir

- **No hay un "mejor gobierno".** Los criterios no pesan lo mismo, y la mayoría de las
  diferencias de crecimiento entre gobiernos están dentro de su incertidumbre.
- **Los resultados no son solo de cada gobierno.** El Banco Central es autónomo, el Congreso
  aprueba las leyes y el contexto externo pesa mucho en una economía pequeña y abierta.
- **Los datos revisados no son los que veían los gobiernos.** Por ejemplo, el déficit de 2009 se
  medía en −1,2 % en su momento y hoy se estima en −3,4 %.

## 5. Lo que queda pendiente para cualquier gobierno

Los dos problemas de fondo siguen abiertos y se refuerzan entre sí:
1. **Recuperar la productividad y la inversión,** porque sin eso el crecimiento seguirá cerca
   de 2 %. El FMI estima que con reformas pro inversión y cobre alto podría llegar a cerca de
   3 % en 2027–2030.
2. **Estabilizar la deuda,** que según el FMI y el CFA superaría el nivel prudente de 45 % del
   PIB hacia 2028–2029 sin una consolidación fiscal.

## Fuentes

- CNEP, Informe Anual 2024, sobre la productividad: https://cnep.cl/prensa/comunicados-de-prensa/productividad-en-chile-permanece-estancada-su-impacto-casi-nulo-en-el-crecimiento-para-2024-oscilaria-entre-02-y-01
- Banco Central de Chile, IPoM de diciembre de 2023, sobre el PIB tendencial: https://www.bcentral.cl/en/content/-/details/banco-central-publico-informe-de-politica-monetaria-ipom-de-diciembre-de-2023
- DIPRES, acta del Comité Consultivo del PIB Tendencial (estimación para 2011): https://www.dipres.gob.cl/597/articles-110631_doc_pdf.pdf
- FMI, Press Release 15/373 (2015): https://www.imf.org/external/np/sec/pr/2015/pr15373.htm
- FMI, Press Release 26/238 (2026): https://www.imf.org/en/news/articles/2026/07/06/pr26238-chile-imf-executive-board-concludes-2026-article-iv-consultation
- Consejo Fiscal Autónomo, *Informe sobre el ejercicio de sus funciones y atribuciones* (23 de abril de 2024), sobre el gasto y los ingresos estructurales de 2008–2023: https://cms.hacienda.cl/cfa/assets/documento/descargar/3f5997d3c7266/1713921901
- Consejo Fiscal Autónomo, sobre el incumplimiento de 2025: https://cfachile.cl/noticias/-cfa-advierte-que-la-gran-magnitud-del-incumplimiento-de-la-meta-de-balance
- DIPRES, *Cumplimiento de las metas de regla fiscal en Chile* (2022): http://www.dipres.gob.cl/598/articles-299473_doc_pdf.pdf
- Ministerio de Desarrollo Social, CASEN: https://www.desarrollosocialyfamilia.gob.cl/storage/docs/ids/Informe-desarrollo-social-2022.pdf
- La Tercera, sobre la CASEN 2024 y la mayor dependencia de subsidios de los hogares más pobres: https://www.latercera.com/pulso/noticia/casen-2024-tasa-de-pobreza-en-chile-cae-a-173-pero-los-mas-pobres-dependen-cada-vez-mas-de-subsidios/
- Hacienda, Estado de la Hacienda Pública, sobre el ancla de deuda del decreto de 2022: https://biblio.hacienda.cl/estado-de-la-hacienda-publica/politica-fiscal
- Las demás citas del Banco Central y del FMI están en [`data/reference/explicaciones.csv`](../data/reference/explicaciones.csv).
