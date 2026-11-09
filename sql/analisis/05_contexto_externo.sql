-- Contexto externo por gobierno: precio del cobre y tipo de cambio.
--
-- El cobre es el principal producto de exportación de Chile y su precio no
-- depende del gobierno de turno. Se muestra junto al crecimiento (consulta 01)
-- para no atribuir al gobierno lo que puede explicar el ciclo externo.
SELECT
    gobierno,
    MAX(ROUND(promedio, 2))           FILTER (WHERE indicador = 'cobre')       AS cobre_prom_usd_lb,
    MAX(ROUND(valor_heredado, 2))     FILTER (WHERE indicador = 'cobre')       AS cobre_heredado,
    MAX(ROUND(valor_final, 2))        FILTER (WHERE indicador = 'cobre')       AS cobre_final,
    MAX(var_12m_promedio)             FILTER (WHERE indicador = 'cobre')       AS cobre_var12m_prom,
    MAX(ROUND(valor_heredado, 0))     FILTER (WHERE indicador = 'tipo_cambio') AS dolar_heredado,
    MAX(ROUND(valor_final, 0))        FILTER (WHERE indicador = 'tipo_cambio') AS dolar_final,
    MAX(ROUND(promedio, 0))           FILTER (WHERE indicador = 'tipo_cambio') AS dolar_prom
FROM economia.v_resumen_gobierno
WHERE indicador IN ('cobre', 'tipo_cambio')
GROUP BY id_gobierno, gobierno
ORDER BY id_gobierno;
