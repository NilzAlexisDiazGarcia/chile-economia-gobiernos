-- Crecimiento económico por gobierno: variación a 12 meses promedio del PIB
-- (trimestral) y del IMACEC (mensual), con y sin los períodos de transición.
--
-- Pregunta: ¿a qué ritmo promedio creció la actividad durante cada gobierno?
-- Nota: es un promedio de tasas anuales, no un crecimiento acumulado.
SELECT
    gobierno,
    MAX(ROUND(var_12m_promedio, 2))                FILTER (WHERE indicador = 'pib')    AS pib_var12m_prom,
    MAX(ROUND(var_12m_promedio_sin_transicion, 2)) FILTER (WHERE indicador = 'pib')    AS pib_sin_transicion,
    MAX(ROUND(var_12m_promedio, 2))                FILTER (WHERE indicador = 'imacec') AS imacec_var12m_prom,
    MAX(ROUND(var_12m_promedio_sin_transicion, 2)) FILTER (WHERE indicador = 'imacec') AS imacec_sin_transicion
FROM economia.v_resumen_gobierno
WHERE indicador IN ('pib', 'imacec')
GROUP BY id_gobierno, gobierno
ORDER BY id_gobierno;
