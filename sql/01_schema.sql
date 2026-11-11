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

-- =============================================================================
-- Comparación internacional (datos anuales del FMI y del Banco Mundial)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Dimensión: zonas (Chile, países pares y agregados regionales)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS economia.dim_zona (
    zona         VARCHAR(10)  PRIMARY KEY,         -- código del FMI (ISO3 o agregado)
    nombre_zona  VARCHAR(60)  NOT NULL UNIQUE,
    tipo         VARCHAR(10)  NOT NULL
        CONSTRAINT ck_zona_tipo CHECK (tipo IN ('pais', 'agregado')),
    es_par       BOOLEAN      NOT NULL             -- entra en el promedio de pares
);

-- -----------------------------------------------------------------------------
-- Hechos: una fila por indicador, zona y año
-- id_gobierno: gobierno de Chile que gobernó la mayor parte de ese año, con la
-- misma regla de mayoría de días que las observaciones mensuales.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS economia.fact_internacional (
    indicador      VARCHAR(40)   NOT NULL,
    zona           VARCHAR(10)   NOT NULL REFERENCES economia.dim_zona (zona),
    anio           SMALLINT      NOT NULL,
    valor          NUMERIC(14,6) NOT NULL,
    unidad         VARCHAR(60)   NOT NULL,
    fuente         VARCHAR(100)  NOT NULL,
    es_proyeccion  BOOLEAN       NOT NULL,
    id_gobierno    SMALLINT      NOT NULL REFERENCES economia.dim_gobierno (id_gobierno),

    CONSTRAINT pk_internacional PRIMARY KEY (indicador, zona, anio)
);

-- -----------------------------------------------------------------------------
-- Dimensión: explicaciones oficiales (citas textuales del Banco Central y el FMI)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS economia.dim_explicacion (
    id_explicacion  SMALLINT     PRIMARY KEY,
    anio            SMALLINT     NOT NULL,
    tema            VARCHAR(60)  NOT NULL,
    cita            TEXT         NOT NULL,
    fuente          VARCHAR(200) NOT NULL,
    url             TEXT         NOT NULL,
    id_gobierno     SMALLINT     NOT NULL REFERENCES economia.dim_gobierno (id_gobierno)
);

-- -----------------------------------------------------------------------------
-- Dimensión: metas fiscales de cada gobierno (decretos de política fiscal)
-- Fuente: DIPRES, "Cumplimiento de las metas de regla fiscal en Chile" (2022), y CFA.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS economia.dim_meta_fiscal (
    id_gobierno           SMALLINT     PRIMARY KEY REFERENCES economia.dim_gobierno (id_gobierno),
    decreto_inicial       VARCHAR(60)  NOT NULL,
    meta_inicial          TEXT         NOT NULL,
    modificaciones        TEXT         NOT NULL,
    anio_evaluado         SMALLINT     NOT NULL,
    meta_vigente          NUMERIC(5,2) NOT NULL,   -- % del PIB, último año completo
    resultado             NUMERIC(5,2) NOT NULL,   -- % del PIB, metodología de la fuente
    cumple_meta_vigente   VARCHAR(2)   NOT NULL CHECK (cumple_meta_vigente IN ('Sí', 'No')),
    -- 'No aplica': el decreto inicial no fijaba meta para el último año completo
    cumple_meta_inicial   VARCHAR(10)  NOT NULL CHECK (cumple_meta_inicial IN ('Sí', 'No', 'No aplica')),
    anios_cumplidos       VARCHAR(60)  NOT NULL,
    anios_incumplidos     VARCHAR(60)  NOT NULL,
    shock_extraordinario  VARCHAR(80)  NOT NULL,
    explicacion           TEXT         NOT NULL,
    fuente                VARCHAR(200) NOT NULL,
    url                   TEXT         NOT NULL
);

-- -----------------------------------------------------------------------------
-- Pobreza por ingresos (CASEN, Ministerio de Desarrollo Social), serie comparable
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS economia.dim_pobreza (
    anio          SMALLINT     PRIMARY KEY,
    pobreza_pct   NUMERIC(4,1) NOT NULL CHECK (pobreza_pct BETWEEN 0 AND 100),
    metodologia   TEXT         NOT NULL,
    fuente        VARCHAR(200) NOT NULL,
    url           TEXT         NOT NULL,
    id_gobierno   SMALLINT     NOT NULL REFERENCES economia.dim_gobierno (id_gobierno)
);
