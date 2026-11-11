-- =============================================================================
-- Vistas de análisis. Son la capa que consumen las consultas y Power BI.
--
-- Se borran y se recrean en cada carga (en orden inverso de dependencia), así
-- un cambio de columnas no choca con la definición anterior.
--
-- Las vistas NO redondean: entregan los valores exactos. Se redondea solo al
-- presentar (consultas de sql/analisis/ y formato de Power BI). Redondear en
-- dos pasos produce errores: 2,98498 -> 2,9850 -> 2,99, cuando lo correcto es 2,98.
-- =============================================================================

DROP VIEW IF EXISTS economia.v_pbi_evaluacion;
DROP VIEW IF EXISTS economia.v_pbi_costo_deuda;
DROP VIEW IF EXISTS economia.v_costo_deuda_anual;
DROP VIEW IF EXISTS economia.v_fees_pib;
DROP VIEW IF EXISTS economia.v_pbi_comparacion;
DROP VIEW IF EXISTS economia.v_pbi_observacion;
DROP VIEW IF EXISTS economia.v_resumen_gobierno;
DROP VIEW IF EXISTS economia.v_variacion_12m;
DROP VIEW IF EXISTS economia.v_observacion;

-- -----------------------------------------------------------------------------
-- v_observacion: la tabla de hechos con los atributos de sus dimensiones.
-- punto_medio: día central del período. Como un período toca a lo más dos
-- gobiernos, el que tiene la mayoría de los días es siempre el que contiene el
-- punto medio. Sirve para reasignar con desfase (consulta 07).
-- -----------------------------------------------------------------------------
CREATE VIEW economia.v_observacion AS
SELECT
    o.indicador,
    i.frecuencia,
    i.unidad,
    o.fecha,
    o.fecha_fin_periodo,
    o.fecha + (o.fecha_fin_periodo - o.fecha) / 2 AS punto_medio,
    o.valor,
    o.id_gobierno,
    g.etiqueta  AS gobierno,
    g.en_alcance,
    o.es_transicion
FROM economia.fact_observacion o
JOIN economia.dim_indicador   i USING (indicador)
JOIN economia.dim_gobierno    g USING (id_gobierno);

-- -----------------------------------------------------------------------------
-- v_variacion_12m: variación porcentual respecto del mismo período del año
-- anterior, para los indicadores en niveles (PIB, IMACEC, cobre).
--
-- - Compararse con el mismo mes/trimestre del año anterior elimina la
--   estacionalidad sin usar series desestacionalizadas.
-- - LAG se calcula sobre la serie COMPLETA, antes de filtrar por gobierno:
--   así marzo 2010 se compara con marzo 2009 aunque sean de gobiernos distintos.
-- - La condición fecha_anterior = fecha - 1 año evita comparar con un período
--   equivocado si a la serie le faltara algún dato.
-- -----------------------------------------------------------------------------
CREATE VIEW economia.v_variacion_12m AS
WITH rezagos (indicador, periodos_por_anio) AS (
    VALUES ('pib', 4), ('imacec', 12), ('cobre', 12),
           ('remuneraciones_reales_hist', 12), ('remuneraciones_reales', 12)
),
serie AS (
    SELECT
        o.indicador,
        o.fecha,
        o.valor,
        o.id_gobierno,
        o.es_transicion,
        LAG(o.fecha, r.periodos_por_anio) OVER w AS fecha_anterior,
        LAG(o.valor, r.periodos_por_anio) OVER w AS valor_anterior
    FROM economia.fact_observacion o
    JOIN rezagos r USING (indicador)
    WINDOW w AS (PARTITION BY o.indicador ORDER BY o.fecha)
)
SELECT
    indicador,
    fecha,
    valor,
    valor_anterior,
    (valor / valor_anterior - 1) * 100 AS var_12m_pct,
    id_gobierno,
    es_transicion
FROM serie
WHERE fecha_anterior = (fecha - INTERVAL '1 year')::date;

-- -----------------------------------------------------------------------------
-- v_resumen_gobierno: una fila por gobierno (en alcance) e indicador.
--
-- valor_heredado: último dato del gobierno anterior, es decir, el punto de
-- partida que recibió cada gobierno. Comparar el valor final contra el heredado
-- (y no contra el primer dato propio) mide el cambio durante todo el mandato.
-- -----------------------------------------------------------------------------
CREATE VIEW economia.v_resumen_gobierno AS
WITH base AS (
    SELECT
        o.indicador,
        o.fecha,
        o.valor,
        o.id_gobierno,
        o.es_transicion,
        ROW_NUMBER() OVER (PARTITION BY o.indicador, o.id_gobierno ORDER BY o.fecha)      AS orden_asc,
        ROW_NUMBER() OVER (PARTITION BY o.indicador, o.id_gobierno ORDER BY o.fecha DESC) AS orden_desc
    FROM economia.fact_observacion o
),
heredado AS (
    SELECT g.id_gobierno, b.indicador, b.valor AS valor_heredado
    FROM economia.dim_gobierno g
    JOIN economia.dim_gobierno g_anterior ON g_anterior.fecha_fin = g.fecha_inicio
    JOIN base b ON b.id_gobierno = g_anterior.id_gobierno AND b.orden_desc = 1
),
variacion AS (
    SELECT
        id_gobierno,
        indicador,
        AVG(var_12m_pct)                                   AS var_12m_promedio,
        AVG(var_12m_pct) FILTER (WHERE NOT es_transicion)  AS var_12m_promedio_sin_transicion
    FROM economia.v_variacion_12m
    GROUP BY id_gobierno, indicador
)
SELECT
    g.id_gobierno,
    g.etiqueta                                       AS gobierno,
    b.indicador,
    COUNT(*)                                         AS n_obs,
    h.valor_heredado,
    MAX(b.valor) FILTER (WHERE b.orden_asc = 1)      AS valor_inicial,
    MAX(b.valor) FILTER (WHERE b.orden_desc = 1)     AS valor_final,
    MAX(b.valor) FILTER (WHERE b.orden_desc = 1)
        - h.valor_heredado                           AS cambio_vs_heredado,
    AVG(b.valor)                                     AS promedio,
    MIN(b.valor)                                     AS minimo,
    MAX(b.valor)                                     AS maximo,
    v.var_12m_promedio,
    v.var_12m_promedio_sin_transicion
FROM base b
JOIN economia.dim_gobierno g USING (id_gobierno)
LEFT JOIN heredado  h ON h.id_gobierno = b.id_gobierno AND h.indicador = b.indicador
LEFT JOIN variacion v ON v.id_gobierno = b.id_gobierno AND v.indicador = b.indicador
WHERE g.en_alcance
GROUP BY g.id_gobierno, g.etiqueta, b.indicador, h.valor_heredado,
         v.var_12m_promedio, v.var_12m_promedio_sin_transicion;

-- -----------------------------------------------------------------------------
-- v_pbi_observacion: tabla de hechos para Power BI.
--
-- Cada observación aparece 3 veces, una por desfase (0, 6 y 12 meses), con el
-- gobierno reasignado según ese desfase (misma lógica que la consulta 07).
-- En Power BI, un selector de desfase deja visible una sola de las tres copias.
-- Con desfase 0, id_gobierno y es_transicion coinciden con la regla principal.
-- -----------------------------------------------------------------------------
CREATE VIEW economia.v_pbi_observacion AS
WITH desfases (desfase_meses) AS (
    VALUES (0), (6), (12)
),
desplazado AS (
    SELECT
        o.indicador,
        o.fecha,
        o.valor,
        d.desfase_meses,
        (o.fecha             - make_interval(months => d.desfase_meses))::date AS inicio_desplazado,
        (o.fecha_fin_periodo - make_interval(months => d.desfase_meses))::date AS fin_desplazado,
        (o.punto_medio       - make_interval(months => d.desfase_meses))::date AS medio_desplazado
    FROM economia.v_observacion o
    CROSS JOIN desfases d
)
SELECT
    p.indicador,
    p.fecha,
    p.valor,
    v.var_12m_pct,
    p.desfase_meses,
    g.id_gobierno,
    -- Transición: algún cambio de mando cae dentro del período desplazado.
    EXISTS (
        SELECT 1 FROM economia.dim_gobierno c
        WHERE c.fecha_inicio > p.inicio_desplazado
          AND c.fecha_inicio < p.fin_desplazado
    ) AS es_transicion
FROM desplazado p
JOIN economia.dim_gobierno g
  ON daterange(g.fecha_inicio, g.fecha_fin, '[)') @> p.medio_desplazado
LEFT JOIN economia.v_variacion_12m v
  ON v.indicador = p.indicador AND v.fecha = p.fecha;

-- -----------------------------------------------------------------------------
-- v_pbi_comparacion: Chile frente a sus pares, una fila por año e indicador.
--
-- pares: promedio simple de los países marcados como pares en dim_zona (Perú,
-- Colombia, México y Brasil). Promedio simple y no ponderado: cada país cuenta
-- como una referencia, sin que Brasil o México pesen más por su tamaño.
-- n_pares: cuántos pares tienen dato ese año, para que el lector sepa sobre
-- cuántos países se calculó.
-- Se excluyen las proyecciones del FMI.
-- -----------------------------------------------------------------------------
CREATE VIEW economia.v_pbi_comparacion AS
SELECT
    f.indicador,
    f.anio,
    make_date(f.anio, 1, 1)                                   AS fecha,
    f.id_gobierno,
    MAX(f.unidad)                                             AS unidad,
    MAX(f.fuente)                                             AS fuente,
    MAX(f.valor) FILTER (WHERE f.zona = 'CHL')                AS chile,
    AVG(f.valor) FILTER (WHERE z.es_par)                      AS pares,
    COUNT(*)     FILTER (WHERE z.es_par)                      AS n_pares,
    MAX(f.valor) FILTER (WHERE f.zona = 'WE')                 AS america_latina,
    MAX(f.valor) FILTER (WHERE f.zona = 'WEOWORLD')           AS mundo,
    MAX(f.valor) FILTER (WHERE f.zona = 'CHL')
        - AVG(f.valor) FILTER (WHERE z.es_par)                AS diferencia_pares
FROM economia.fact_internacional f
JOIN economia.dim_zona z USING (zona)
WHERE NOT f.es_proyeccion
GROUP BY f.indicador, f.anio, f.id_gobierno
HAVING MAX(f.valor) FILTER (WHERE f.zona = 'CHL') IS NOT NULL;

-- -----------------------------------------------------------------------------
-- v_fees_pib: saldo mensual del FEES como porcentaje del PIB.
--
-- El saldo en dólares se pasa a pesos con el dólar observado promedio del mes y se
-- divide por el PIB nominal del año anterior, el último año completo en ese momento.
-- En porcentaje del PIB, un mismo saldo pesa menos a medida que la economía crece.
-- -----------------------------------------------------------------------------
CREATE VIEW economia.v_fees_pib AS
SELECT
    f.fecha,
    f.id_gobierno,
    f.valor                                                   AS fees_millones_usd,
    100 * f.valor * tc.dolar / (p.valor * 1000)               AS fees_pct_pib
FROM economia.fact_observacion f
JOIN LATERAL (
    SELECT AVG(t.valor) AS dolar FROM economia.fact_observacion t
     WHERE t.indicador = 'tipo_cambio' AND date_trunc('month', t.fecha) = f.fecha
) tc ON TRUE
JOIN economia.fact_observacion p
  ON p.indicador = 'pib_nominal'
 AND extract(year FROM p.fecha) = extract(year FROM f.fecha) - 1
WHERE f.indicador = 'fees';

-- -----------------------------------------------------------------------------
-- v_costo_deuda_anual: cuánto le cuesta al Fisco su deuda, año a año.
--
-- intereses_pct_pib: gasto en intereses del Gobierno Central (devengado) sobre el PIB
-- nominal del mismo año. No se calcula una tasa implícita (intereses sobre deuda) porque
-- el gasto en intereses puede incluir partidas que no están en la deuda bruta, y con la
-- deuda baja de 2006–2009 esa tasa sale distorsionada.
-- -----------------------------------------------------------------------------
CREATE VIEW economia.v_costo_deuda_anual AS
WITH anual AS (
    SELECT extract(year FROM fecha)::int                            AS anio,
           MAX(valor) FILTER (WHERE indicador = 'intereses_deuda')  AS intereses,   -- millones de pesos
           MAX(valor) FILTER (WHERE indicador = 'pib_nominal')      AS pib,         -- miles de millones
           MAX(id_gobierno) FILTER (WHERE indicador = 'pib_nominal') AS id_gobierno
    FROM economia.fact_observacion
    WHERE indicador IN ('intereses_deuda', 'pib_nominal')
    GROUP BY 1
)
SELECT
    a.anio,
    a.id_gobierno,
    100 * a.intereses / (a.pib * 1000)                              AS intereses_pct_pib
FROM anual a
WHERE a.intereses IS NOT NULL AND a.pib IS NOT NULL;

-- -----------------------------------------------------------------------------
-- v_pbi_costo_deuda: a qué tasa se endeudó cada gobierno.
--
-- tasa_pesos / tasa_uf: promedio de la tasa de mercado de los bonos a 10 años durante
--   el gobierno: lo que costaba emitir deuda nueva. La tasa en UF es real (descuenta la
--   inflación), así que se compara mejor entre gobiernos con inflaciones distintas.
-- intereses_ini / intereses_fin: gasto en intereses (% del PIB) del último año del
--   gobierno anterior y del último año propio. Lo mueven la deuda acumulada y las tasas.
-- -----------------------------------------------------------------------------
CREATE VIEW economia.v_pbi_costo_deuda AS
SELECT
    g.id_gobierno,
    (SELECT AVG(o.valor) FROM economia.fact_observacion o
      WHERE o.id_gobierno = g.id_gobierno AND o.indicador = 'tasa_bonos_10_pesos') AS tasa_pesos,
    (SELECT AVG(o.valor) FROM economia.fact_observacion o
      WHERE o.id_gobierno = g.id_gobierno AND o.indicador = 'tasa_bonos_10_uf')    AS tasa_uf,
    (SELECT c.intereses_pct_pib FROM economia.v_costo_deuda_anual c
      WHERE c.id_gobierno = g.id_gobierno - 1 ORDER BY c.anio DESC LIMIT 1)        AS intereses_ini,
    (SELECT c.intereses_pct_pib FROM economia.v_costo_deuda_anual c
      WHERE c.id_gobierno = g.id_gobierno ORDER BY c.anio DESC LIMIT 1)            AS intereses_fin,
    (SELECT MAX(c.anio) FROM economia.v_costo_deuda_anual c
      WHERE c.id_gobierno = g.id_gobierno)                                         AS anio_fin
FROM economia.dim_gobierno g
WHERE g.en_alcance;

-- -----------------------------------------------------------------------------
-- v_pbi_evaluacion: aciertos y problemas de cada gobierno con criterios uniformes.
--
-- Ocho criterios, los mismos para los cinco gobiernos, cada uno contra una referencia
-- explícita que no elige el autor. "quien_controla" indica qué actor maneja
-- principalmente cada variable: un mal resultado en inflación, que maneja el Banco
-- Central autónomo, no se lee igual que no cumplir la meta fiscal propia.
-- -----------------------------------------------------------------------------
CREATE VIEW economia.v_pbi_evaluacion AS
WITH r AS (
    SELECT id_gobierno, indicador, valor_heredado, valor_inicial, valor_final
    FROM economia.v_resumen_gobierno
),
num AS (
    SELECT
        g.id_gobierno,
        (SELECT AVG(c.diferencia_pares) FROM economia.v_pbi_comparacion c
          WHERE c.id_gobierno = g.id_gobierno AND c.indicador = 'crecimiento_pib')          AS crec_pares,
        (SELECT AVG(CASE WHEN o.valor BETWEEN 2 AND 4 THEN 1.0 ELSE 0.0 END)
           FROM economia.fact_observacion o
          WHERE o.id_gobierno = g.id_gobierno AND o.indicador = 'ipc')                     AS ipc_en_rango,
        (SELECT valor_heredado FROM r WHERE r.id_gobierno = g.id_gobierno AND indicador = 'desempleo')  AS des_ini,
        (SELECT valor_final    FROM r WHERE r.id_gobierno = g.id_gobierno AND indicador = 'desempleo')  AS des_fin,
        (SELECT valor_heredado FROM r WHERE r.id_gobierno = g.id_gobierno AND indicador = 'deuda_neta') AS dn_ini,
        (SELECT valor_final    FROM r WHERE r.id_gobierno = g.id_gobierno AND indicador = 'deuda_neta') AS dn_fin,
        -- Ahorro: solo el FEES, el fondo líquido para crisis, en % del PIB. El FRP no se usa
        -- porque recibe aportes obligatorios por ley y solo puede financiar pensiones. Ninguno
        -- se compara solo: la deuda neta descuenta estos activos de la deuda bruta.
        -- El FEES existe desde marzo de 2007: para Bachelet I se usa su primer saldo.
        COALESCE(
            (SELECT fp.fees_pct_pib FROM economia.v_fees_pib fp
              WHERE fp.id_gobierno = g.id_gobierno - 1 ORDER BY fp.fecha DESC LIMIT 1),
            (SELECT fp.fees_pct_pib FROM economia.v_fees_pib fp
              WHERE fp.id_gobierno = g.id_gobierno ORDER BY fp.fecha LIMIT 1))              AS fs_ini,
        (SELECT fp.fees_pct_pib FROM economia.v_fees_pib fp
          WHERE fp.id_gobierno = g.id_gobierno ORDER BY fp.fecha DESC LIMIT 1)             AS fs_fin,
        m.meta_vigente, m.resultado, m.cumple_meta_vigente, m.anio_evaluado,
        -- Pobreza: última medición del gobierno anterior (o la primera propia) y la última propia
        COALESCE(
            (SELECT p.pobreza_pct FROM economia.dim_pobreza p WHERE p.id_gobierno = g.id_gobierno - 1
              ORDER BY p.anio DESC LIMIT 1),
            (SELECT p.pobreza_pct FROM economia.dim_pobreza p WHERE p.id_gobierno = g.id_gobierno
              ORDER BY p.anio LIMIT 1))                                                    AS pob_ini,
        (SELECT p.pobreza_pct FROM economia.dim_pobreza p WHERE p.id_gobierno = g.id_gobierno
          ORDER BY p.anio DESC LIMIT 1)                                                    AS pob_fin,
        -- Salario real: variación anual promedio de los dos tramos del índice del INE
        (SELECT AVG(v.var_12m_pct) FROM economia.v_variacion_12m v
          WHERE v.id_gobierno = g.id_gobierno
            AND v.indicador IN ('remuneraciones_reales_hist', 'remuneraciones_reales'))   AS sal_real
    FROM economia.dim_gobierno g
    JOIN economia.dim_meta_fiscal m USING (id_gobierno)
    WHERE g.en_alcance
),
f AS (  -- formato con coma decimal
    SELECT *,
        replace(to_char(crec_pares, 'SG0.0'), '.', ',')     AS t_crec,
        replace(to_char(des_ini, 'FM990.0'), '.', ',')      AS t_des_ini,
        replace(to_char(des_fin, 'FM990.0'), '.', ',')      AS t_des_fin,
        replace(to_char(dn_ini, 'FM990.0'), '.', ',')       AS t_dn_ini,
        replace(to_char(dn_fin, 'FM990.0'), '.', ',')       AS t_dn_fin,
        replace(to_char(meta_vigente, 'FM990.0'), '.', ',') AS t_meta,
        replace(to_char(resultado, 'FM990.0'), '.', ',')    AS t_res,
        replace(to_char(fs_ini, 'FM990.0'), '.', ',')       AS t_fs_ini,
        replace(to_char(fs_fin, 'FM990.0'), '.', ',')       AS t_fs_fin,
        replace(to_char(pob_ini, 'FM990.0'), '.', ',')      AS t_pob_ini,
        replace(to_char(pob_fin, 'FM990.0'), '.', ',')      AS t_pob_fin,
        replace(to_char(sal_real, 'SG0.0'), '.', ',')       AS t_sal
    FROM num
)
SELECT id_gobierno, 1 AS orden, 'Crecimiento vs. pares (pp)' AS criterio,
       'Mixto: gobierno, ciclo y contexto externo' AS quien_controla,
       'Promedio de Perú, Colombia, México y Brasil (FMI)' AS referencia,
       t_crec || ' pp' AS resultado,
       crec_pares >= 0 AS favorable
FROM f
UNION ALL
SELECT id_gobierno, 2, 'Meses con inflación en la meta', 'Banco Central (autónomo)',
       'Rango de 2 % a 4 % la mayoría de los meses',
       round(ipc_en_rango * 100)::int || ' %', ipc_en_rango >= 0.5
FROM f
UNION ALL
SELECT id_gobierno, 3, 'Desempleo (%): recibió → entregó', 'Mixto: gobierno, ciclo y contexto externo',
       'Entregar menos desempleo del recibido',
       t_des_ini || ' → ' || t_des_fin, des_fin < des_ini
FROM f
UNION ALL
SELECT id_gobierno, 4, 'Meta fiscal propia (% PIB)', 'Gobierno',
       'Balance estructural del último año completo frente a la meta vigente',
       t_res || ' (meta ' || t_meta || ', ' || anio_evaluado || ')', cumple_meta_vigente = 'Sí'
FROM f
UNION ALL
SELECT id_gobierno, 5, 'Deuda neta (% PIB): recibió → entregó', 'Gobierno',
       'Entregar igual o menos deuda neta que la recibida (% del PIB)',
       t_dn_ini || ' → ' || t_dn_fin, dn_fin <= dn_ini
FROM f
UNION ALL
SELECT id_gobierno, 6, 'Fondo para crisis FEES (% PIB): recibió → entregó',
       'Gobierno (y rentabilidad y tipo de cambio)',
       'Entregar un FEES igual o mayor que el recibido, como % del PIB',
       t_fs_ini || ' → ' || t_fs_fin, fs_fin >= fs_ini
FROM f
UNION ALL
SELECT id_gobierno, 7, 'Pobreza (%, CASEN): recibió → entregó', 'Mixto: gobierno, crecimiento y transferencias',
       'Entregar menos pobreza por ingresos que la recibida',
       t_pob_ini || ' → ' || t_pob_fin, pob_fin < pob_ini
FROM f
UNION ALL
SELECT id_gobierno, 8, 'Salario real (% anual promedio)', 'Mixto: gobierno, inflación y mercado laboral',
       'Que los salarios suban más que los precios',
       t_sal || ' %', sal_real > 0
FROM f;
