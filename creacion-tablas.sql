-- Tabla de Área SNI
CREATE TABLE area_sni (
    id_area_sni SERIAL PRIMARY KEY,
    nombre_area_sni TEXT NOT NULL
);

-- Tabla de Estado
CREATE TABLE estado (
    id_estado SERIAL PRIMARY KEY,
    nombre_estado TEXT NOT NULL
);

-- Tabla de Nivel de Estudio
CREATE TABLE nivel_estudio (
    id_nivel_estudio SERIAL PRIMARY KEY,
    nombre_nivel TEXT NOT NULL
);

-- Tabla de Institución
CREATE TABLE institucion (
    id_institucion SERIAL PRIMARY KEY,
    nombre_institucion TEXT NOT NULL
);

-- Tabla de Programa
CREATE TABLE programa (
    id_programa SERIAL PRIMARY KEY,
    nombre_programa TEXT NOT NULL,
    id_institucion INTEGER REFERENCES institucion(id_institucion)
);

-- Tabla de Beca
CREATE TABLE beca (
    id_beca SERIAL PRIMARY KEY,
    nombre_beca TEXT NOT NULL  -- Nuevo campo de nombre de beca
);

-- Tabla de Becario
CREATE TABLE becario (
    id_becario SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    id_estado INTEGER REFERENCES estado(id_estado),
    id_nivel_estudio INTEGER REFERENCES nivel_estudio(id_nivel_estudio),
    id_area_sni INTEGER REFERENCES area_sni(id_area_sni)
);

-- Tabla de Becario_Beca (relación entre becario y beca)
CREATE TABLE becario_beca (
    id_becario INTEGER REFERENCES becario(id_becario),
    id_beca INTEGER REFERENCES beca(id_beca),
    fecha_inicio DATE,
    fecha_fin DATE,
    PRIMARY KEY (id_becario, id_beca)
);

-- Tabla de Montos de Beca
CREATE TABLE montos_beca (
    id_montos_beca SERIAL PRIMARY KEY,
    monto NUMERIC(10, 2) NOT NULL,
    id_beca INTEGER REFERENCES beca(id_beca)
);

-- Tabla de Becario_Institucion_Programa (relación entre becario, institución y programa)
CREATE TABLE becario_institucion_programa (
    id_becario INTEGER REFERENCES becario(id_becario),
    id_institucion INTEGER REFERENCES institucion(id_institucion),
    id_programa INTEGER REFERENCES programa(id_programa),
    PRIMARY KEY (id_becario, id_institucion, id_programa)
);