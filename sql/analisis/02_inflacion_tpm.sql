-- Inflación (IPC, variación a 12 meses) y Tasa de Política Monetaria por gobierno.
--
-- Recordatorio metodológico: la TPM la fija el Banco Central, que es autónomo.
-- Se muestra como contexto de la política monetaria vigente, no como decisión
-- del gobierno.
SELECT
    gobierno,
    MAX(ROUND(promedio, 2)) FILTER (WHERE indicador = 'ipc')            AS ipc_prom,
    MAX(ROUND(maximo, 2))         FILTER (WHERE indicador = 'ipc')      AS ipc_max,
    MAX(ROUND(valor_heredado, 2)) FILTER (WHERE indicador = 'tpm')      AS tpm_heredada,
    MAX(ROUND(valor_final, 2))    FILTER (WHERE indicador = 'tpm')      AS tpm_final,
    MAX(ROUND(minimo, 2))         FILTER (WHERE indicador = 'tpm')      AS tpm_min,
    MAX(ROUND(maximo, 2))         FILTER (WHERE indicador = 'tpm')      AS tpm_max
FROM economia.v_resumen_gobierno
WHERE indicador IN ('ipc', 'tpm')
GROUP BY id_gobierno, gobierno
ORDER BY id_gobierno;
