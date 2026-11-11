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
-- n_pares: cuántos pares tienen dato ese año (el Banco Mundial no entregó
-- Colombia), para que el lector sepa sobre cuántos países se calculó.
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
