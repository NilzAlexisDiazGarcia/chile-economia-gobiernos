-- Sensibilidad al rezago: ¿cambia la comparación entre gobiernos si suponemos
-- que las políticas tardan 6 o 12 meses en reflejarse?
--
-- Con desfase de N meses, un dato se atribuye al gobierno que gobernaba N meses
-- ANTES de ese dato. Se usa el punto medio del período: el gobierno que lo
-- contiene es el que tiene la mayoría de los días, así que con desfase 0 se
-- reproduce exactamente la regla principal del proyecto.
--
-- Esta consulta NO elige un desfase "correcto": muestra cuánto dependen los
-- resultados del supuesto.
--
-- Ojo con el último gobierno: con desfase, sus meses finales todavía no tienen
-- dato publicado, así que su promedio se calcula con menos meses (ver la última
-- columna) y no es del todo comparable con el de los demás.
WITH desfases (meses) AS (
    VALUES (0), (6), (12)
),
reasignado AS (
    SELECT
        d.meses,
        g.id_gobierno,
        g.etiqueta AS gobierno,
        v.indicador,
        v.var_12m_pct
    FROM economia.v_variacion_12m v
    JOIN economia.v_observacion  o USING (indicador, fecha)
    CROSS JOIN desfases d
    JOIN economia.dim_gobierno   g
      ON daterange(g.fecha_inicio, g.fecha_fin, '[)')
         @> (o.punto_medio - make_interval(months => d.meses))::date
    WHERE v.indicador = 'imacec'
      AND g.en_alcance
)
SELECT
    gobierno,
    ROUND(AVG(var_12m_pct) FILTER (WHERE meses = 0), 2)  AS imacec_desfase_0,
    ROUND(AVG(var_12m_pct) FILTER (WHERE meses = 6), 2)  AS imacec_desfase_6,
    ROUND(AVG(var_12m_pct) FILTER (WHERE meses = 12), 2) AS imacec_desfase_12,
    COUNT(*) FILTER (WHERE meses = 12)                   AS meses_con_desfase_12
FROM reasignado
GROUP BY id_gobierno, gobierno
ORDER BY id_gobierno;
