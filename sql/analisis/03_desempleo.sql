-- Tasa de desocupación por gobierno: la que recibió, la que dejó, su promedio y
-- su rango.
--
-- La serie no está desestacionalizada. valor_heredado y valor_final son siempre
-- un mes de febrero (último mes completo antes de cada cambio de mando), así que
-- la comparación entre ambos no está afectada por la estacionalidad.
SELECT
    gobierno,
    ROUND(valor_heredado, 2)            AS desempleo_heredado,
    ROUND(valor_final, 2)               AS desempleo_final,
    ROUND(cambio_vs_heredado, 2)        AS cambio_pp,
    ROUND(promedio, 2)                  AS desempleo_prom,
    ROUND(minimo, 2)                    AS desempleo_min,
    ROUND(maximo, 2)                    AS desempleo_max
FROM economia.v_resumen_gobierno
WHERE indicador = 'desempleo'
ORDER BY id_gobierno;
