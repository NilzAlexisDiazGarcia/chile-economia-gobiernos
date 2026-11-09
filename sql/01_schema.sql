-- =============================================================================
-- Esquema de la base economia_chile
-- Modelo estrella: tres dimensiones (gobierno, indicador, evento) y una tabla
-- de hechos con las observaciones.
--
-- Es idempotente: se puede ejecutar varias veces sin error (IF NOT EXISTS).
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS economia;

-- -----------------------------------------------------------------------------
-- Dimensión: gobiernos
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS economia.dim_gobierno (
    id_gobierno   SMALLINT     PRIMARY KEY,
    presidente    VARCHAR(100) NOT NULL,
    etiqueta      VARCHAR(30)  NOT NULL UNIQUE,
    fecha_inicio  DATE         NOT NULL,          -- inclusiva
    fecha_fin     DATE         NOT NULL,          -- exclusiva
    en_alcance    BOOLEAN      NOT NULL,

    CONSTRAINT ck_gobierno_fechas CHECK (fecha_fin > fecha_inicio),

    -- Dos gobiernos no pueden superponerse en el tiempo. daterange usa el mismo
    -- criterio [inicio, fin) que el resto del proyecto, así que dos mandatos
    -- consecutivos (uno termina el 11 de marzo y el otro empieza ese día) no chocan.
    CONSTRAINT ex_gobierno_sin_superposicion
        EXCLUDE USING gist (daterange(fecha_inicio, fecha_fin, '[)') WITH &&)
);

-- -----------------------------------------------------------------------------
-- Dimensión: indicadores (catálogo de series)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS economia.dim_indicador (
    indicador        VARCHAR(30)  PRIMARY KEY,    -- clave en config/series.yaml
    descripcion      VARCHAR(200) NOT NULL,
    unidad           VARCHAR(60)  NOT NULL,
    frecuencia       VARCHAR(10)  NOT NULL
        CONSTRAINT ck_indicador_frecuencia
        CHECK (frecuencia IN ('DAILY', 'MONTHLY', 'QUARTERLY', 'ANNUAL')),
    codigo_serie     VARCHAR(60)  NOT NULL UNIQUE,
    fuente           VARCHAR(60)  NOT NULL,       -- de dónde se extrajo
    fuente_original  VARCHAR(60)  NOT NULL        -- quién produce el dato
);

-- -----------------------------------------------------------------------------
-- Dimensión: eventos de contexto
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS economia.dim_evento (
    id_evento        SMALLINT     PRIMARY KEY,
    evento           VARCHAR(100) NOT NULL,
    tipo             VARCHAR(30)  NOT NULL,
    fecha_inicio     DATE         NOT NULL,
    fecha_fin        DATE         NOT NULL,
    precision_fecha  VARCHAR(10)  NOT NULL
        CONSTRAINT ck_evento_precision
        CHECK (precision_fecha IN ('exacta', 'aproximada')),
    nota             TEXT,
    fuente           TEXT,

    CONSTRAINT ck_evento_fechas CHECK (fecha_fin >= fecha_inicio)
);

-- -----------------------------------------------------------------------------
-- Hechos: una fila por indicador y fecha
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS economia.fact_observacion (
    indicador          VARCHAR(30)   NOT NULL
        REFERENCES economia.dim_indicador (indicador),
    fecha              DATE          NOT NULL,    -- primer día del período
    valor              NUMERIC(14,6) NOT NULL,
    fecha_fin_periodo  DATE          NOT NULL,    -- exclusiva
    id_gobierno        SMALLINT      NOT NULL
        REFERENCES economia.dim_gobierno (id_gobierno),
    dias_gobierno      SMALLINT      NOT NULL,
    dias_periodo       SMALLINT      NOT NULL,
    es_transicion      BOOLEAN       NOT NULL,

    CONSTRAINT pk_observacion PRIMARY KEY (indicador, fecha),
    CONSTRAINT ck_observacion_periodo CHECK (fecha_fin_periodo > fecha),
    CONSTRAINT ck_observacion_dias CHECK (dias_gobierno BETWEEN 1 AND dias_periodo)
);

-- La clave primaria (indicador, fecha) ya crea un índice que sirve para filtrar
-- por indicador. Este índice acelera las consultas que agrupan por gobierno.
CREATE INDEX IF NOT EXISTS ix_observacion_gobierno
    ON economia.fact_observacion (id_gobierno, indicador);
