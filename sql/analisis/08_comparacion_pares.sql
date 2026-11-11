-- Chile frente a sus pares por gobierno, con datos anuales del FMI y del Banco Mundial.
--
-- Pares: Perú, Colombia, México y Brasil, países de la región con metas de inflación.
-- Si toda la región crece poco, crecer poco no dice lo mismo que si la región crece
-- mucho: la diferencia con los pares separa una parte del contexto externo.
--
-- Datos anuales: cada año se asigna al gobierno que gobernó la mayor parte de él.
-- Por eso las cifras de Chile difieren levemente de las mensuales (consulta 01).
-- Deuda y balance son del gobierno general (FMI), no del Gobierno Central (DIPRES).
SELECT
    g.etiqueta                                             AS gobierno,
    c.indicador,
    ROUND(AVG(c.chile), 2)                                 AS chile,
    ROUND(AVG(c.pares), 2)                                 AS pares,
    MIN(c.n_pares)                                         AS n_pares_min,
    ROUND(AVG(c.america_latina), 2)                        AS america_latina,
    ROUND(AVG(c.mundo), 2)                                 AS mundo,
    ROUND(AVG(c.diferencia_pares), 2)                      AS chile_menos_pares
FROM economia.v_pbi_comparacion c
JOIN economia.dim_gobierno g USING (id_gobierno)
WHERE g.en_alcance
  AND c.indicador IN ('crecimiento_pib', 'inflacion_promedio', 'deuda_gobierno_general',
                      'balance_gobierno_general', 'control_corrupcion')
GROUP BY c.indicador, g.id_gobierno, g.etiqueta
ORDER BY c.indicador, g.id_gobierno;
