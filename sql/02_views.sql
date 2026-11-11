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

-- -----------------------------------------------------------------------------
-- v_pbi_evaluacion: aciertos y problemas de cada gobierno con criterios uniformes.
--
-- Seis criterios, los mismos para los cinco gobiernos, cada uno contra una referencia
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
        -- Los fondos existen desde marzo de 2007: para Bachelet I se usa su primer saldo.
        (SELECT COALESCE(valor_heredado, valor_inicial) FROM r
          WHERE r.id_gobierno = g.id_gobierno AND indicador = 'fondos_soberanos')          AS fs_ini,
        (SELECT valor_final FROM r WHERE r.id_gobierno = g.id_gobierno AND indicador = 'fondos_soberanos') AS fs_fin,
        m.meta_vigente, m.resultado, m.cumple_meta_vigente, m.anio_evaluado
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
        replace(to_char(fs_ini, 'FM999G999'), ',', '.')     AS t_fs_ini,
        replace(to_char(fs_fin, 'FM999G999'), ',', '.')     AS t_fs_fin
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
SELECT id_gobierno, 6, 'Fondos soberanos (US$ mill.): recibió → entregó', 'Gobierno (y rentabilidad de los mercados)',
       'Entregar igual o más ahorro que el recibido (FEES + FRP)',
       t_fs_ini || ' → ' || t_fs_fin, fs_fin >= fs_ini
FROM f;
