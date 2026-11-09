-- Finanzas públicas por gobierno: deuda bruta (% del PIB) recibida y entregada,
-- y balance fiscal (% del PIB) promedio de los años asignados a cada gobierno.
--
-- El primer año de cada gobierno se ejecuta con la Ley de Presupuestos aprobada
-- por el gobierno anterior (ver docs/metodologia.md, sección "Rezago").
SELECT
    gobierno,
    MAX(ROUND(valor_heredado, 1))     FILTER (WHERE indicador = 'deuda_bruta')    AS deuda_heredada,
    MAX(ROUND(valor_final, 1))        FILTER (WHERE indicador = 'deuda_bruta')    AS deuda_final,
    MAX(ROUND(cambio_vs_heredado, 1)) FILTER (WHERE indicador = 'deuda_bruta')    AS deuda_cambio_pp,
    MAX(ROUND(promedio, 2))           FILTER (WHERE indicador = 'balance_fiscal') AS balance_prom,
    MAX(ROUND(minimo, 2))             FILTER (WHERE indicador = 'balance_fiscal') AS balance_min,
    MAX(ROUND(maximo, 2))             FILTER (WHERE indicador = 'balance_fiscal') AS balance_max
FROM economia.v_resumen_gobierno
WHERE indicador IN ('deuda_bruta', 'balance_fiscal')
GROUP BY id_gobierno, gobierno
ORDER BY id_gobierno;
