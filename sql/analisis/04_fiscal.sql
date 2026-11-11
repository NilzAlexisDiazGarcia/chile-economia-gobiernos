-- Finanzas públicas por gobierno (todo en % del PIB):
--   - Deuda bruta y deuda neta del Gobierno Central, recibida y entregada. La deuda neta
--     descuenta los activos financieros del Fisco (fondos soberanos, entre otros); un valor
--     negativo significa que el Fisco es acreedor neto.
--   - Balance efectivo y balance estructural, promedio de los años asignados a cada
--     gobierno. El estructural descuenta el efecto del ciclo y del precio del cobre, y es la
--     meta de la regla fiscal chilena.
--
-- El primer año de cada gobierno se ejecuta con la Ley de Presupuestos aprobada
-- por el gobierno anterior (ver docs/metodologia.md, sección "Rezago").
SELECT
    gobierno,
    MAX(ROUND(valor_heredado, 1))     FILTER (WHERE indicador = 'deuda_bruta')         AS deuda_bruta_heredada,
    MAX(ROUND(valor_final, 1))        FILTER (WHERE indicador = 'deuda_bruta')         AS deuda_bruta_final,
    MAX(ROUND(cambio_vs_heredado, 1)) FILTER (WHERE indicador = 'deuda_bruta')         AS deuda_bruta_cambio_pp,
    MAX(ROUND(valor_heredado, 1))     FILTER (WHERE indicador = 'deuda_neta')          AS deuda_neta_heredada,
    MAX(ROUND(valor_final, 1))        FILTER (WHERE indicador = 'deuda_neta')          AS deuda_neta_final,
    MAX(ROUND(promedio, 2))           FILTER (WHERE indicador = 'balance_fiscal')      AS balance_efectivo_prom,
    MAX(ROUND(promedio, 2))           FILTER (WHERE indicador = 'balance_estructural') AS balance_estructural_prom,
    MAX(ROUND(minimo, 2))             FILTER (WHERE indicador = 'balance_estructural') AS balance_estructural_min
FROM economia.v_resumen_gobierno
WHERE indicador IN ('deuda_bruta', 'deuda_neta', 'balance_fiscal', 'balance_estructural')
GROUP BY id_gobierno, gobierno
ORDER BY id_gobierno;
