-- Indicadores alrededor de cada evento de contexto.
--
-- Para tratar todos los eventos con la misma regla:
--   antes   = los 12 meses previos al mes de inicio del evento
--   durante = desde el mes de inicio hasta 6 meses después del fin del evento
-- (los 6 meses extra capturan efectos que llegan con rezago, como en el
--  terremoto de 2010, cuyo evento dura un solo día).
WITH ventanas AS (
    SELECT
        evento,
        fecha_inicio,
        date_trunc('month', fecha_inicio)::date                          AS inicio_durante,
        (date_trunc('month', fecha_fin) + INTERVAL '6 months')::date     AS fin_durante,
        (date_trunc('month', fecha_inicio) - INTERVAL '12 months')::date AS inicio_antes
    FROM economia.dim_evento
)
SELECT
    w.evento,
    w.fecha_inicio,
    -- Crecimiento del IMACEC (variación a 12 meses, promedio)
    (SELECT ROUND(AVG(v.var_12m_pct), 2) FROM economia.v_variacion_12m v
      WHERE v.indicador = 'imacec' AND v.fecha >= w.inicio_antes AND v.fecha < w.inicio_durante)  AS imacec_antes,
    (SELECT ROUND(AVG(v.var_12m_pct), 2) FROM economia.v_variacion_12m v
      WHERE v.indicador = 'imacec' AND v.fecha >= w.inicio_durante AND v.fecha <= w.fin_durante)   AS imacec_durante,
    (SELECT MIN(v.var_12m_pct) FROM economia.v_variacion_12m v
      WHERE v.indicador = 'imacec' AND v.fecha >= w.inicio_durante AND v.fecha <= w.fin_durante)   AS imacec_peor_mes,
    -- Desocupación (promedio antes, máximo durante)
    (SELECT ROUND(AVG(o.valor), 2) FROM economia.fact_observacion o
      WHERE o.indicador = 'desempleo' AND o.fecha >= w.inicio_antes AND o.fecha < w.inicio_durante) AS desempleo_antes,
    (SELECT ROUND(MAX(o.valor), 2) FROM economia.fact_observacion o
      WHERE o.indicador = 'desempleo' AND o.fecha >= w.inicio_durante AND o.fecha <= w.fin_durante) AS desempleo_max_durante,
    -- Precio del cobre (promedio)
    (SELECT ROUND(AVG(o.valor), 2) FROM economia.fact_observacion o
      WHERE o.indicador = 'cobre' AND o.fecha >= w.inicio_antes AND o.fecha < w.inicio_durante)     AS cobre_antes,
    (SELECT ROUND(AVG(o.valor), 2) FROM economia.fact_observacion o
      WHERE o.indicador = 'cobre' AND o.fecha >= w.inicio_durante AND o.fecha <= w.fin_durante)     AS cobre_durante
FROM ventanas w
ORDER BY w.fecha_inicio;
