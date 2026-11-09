-- =============================================================================
-- Vistas de análisis. Son la capa que consumen las consultas y Power BI.
--
-- Se borran y se recrean en cada carga (en orden inverso de dependencia), así
-- un cambio de columnas no choca con la definición anterior.
-- =============================================================================

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
    VALUES ('pib', 4), ('imacec', 12), ('cobre', 12)
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
    ROUND((valor / valor_anterior - 1) * 100, 2) AS var_12m_pct,
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
        ROUND(AVG(var_12m_pct), 2)                                   AS var_12m_promedio,
        ROUND(AVG(var_12m_pct) FILTER (WHERE NOT es_transicion), 2)  AS var_12m_promedio_sin_transicion
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
    ROUND(AVG(b.valor), 4)                           AS promedio,
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
