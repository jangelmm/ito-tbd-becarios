CREATE TABLE catalogo_estado (
    id_estado SERIAL PRIMARY KEY,
    estado TEXT NOT NULL UNIQUE
);

CREATE TABLE catalogo_nivel_estudio (
    id_nivel_estudio SERIAL PRIMARY KEY,
    nivel_estudio TEXT NOT NULL UNIQUE
);

CREATE TABLE catalogo_area_sni (
    id_area_sni SERIAL PRIMARY KEY,
    area_sni TEXT NOT NULL UNIQUE
);

CREATE TABLE beca (
    id_beca SERIAL PRIMARY KEY,
    fk_nivel_estudio INTEGER,
    CONSTRAINT fk_beca_nivel_estudio FOREIGN KEY (fk_nivel_estudio) REFERENCES catalogo_nivel_estudio(id_nivel_estudio)
);

CREATE TABLE becario (
    id_becario SERIAL PRIMARY KEY,
    nombre_becario TEXT NOT NULL
);

CREATE TABLE programa (
    id_programa SERIAL PRIMARY KEY,
    nombre_programa TEXT NOT NULL UNIQUE,
    fk_area_sni INTEGER,
    CONSTRAINT fk_programa_area_sni FOREIGN KEY (fk_area_sni) REFERENCES catalogo_area_sni(id_area_sni)
);

CREATE TABLE institucion (
    id_institucion SERIAL PRIMARY KEY,
    nombre_institucion TEXT NOT NULL UNIQUE,
    fk_estado INTEGER,
    CONSTRAINT fk_institucion_estado FOREIGN KEY (fk_estado) REFERENCES catalogo_estado(id_estado)
);

CREATE TABLE convocatoria (
    id_convocatoria SERIAL PRIMARY KEY,
    nombre_convocatoria TEXT NOT NULL UNIQUE
);

CREATE TABLE pago (
    id_pago SERIAL PRIMARY KEY,
    fk_becario INTEGER,
    fk_beca INTEGER,
    inicio DATE,
    fin DATE,
    total NUMERIC,
    CONSTRAINT fk_pago_becario FOREIGN KEY (fk_becario) REFERENCES becario(id_becario),
    CONSTRAINT fk_pago_beca FOREIGN KEY (fk_beca) REFERENCES beca(id_beca)
);

CREATE TABLE becario_institucion_programa (
    fk_institucion INTEGER,
    fk_becario INTEGER,
    fk_programa INTEGER,
    CONSTRAINT fk_becario_institucion FOREIGN KEY (fk_institucion) REFERENCES institucion(id_institucion),
    CONSTRAINT fk_becario_programa FOREIGN KEY (fk_programa) REFERENCES programa(id_programa),
    CONSTRAINT fk_becario_institucion_programa_becario FOREIGN KEY (fk_becario) REFERENCES becario(id_becario)
);

CREATE TABLE becario_beca (
    monto NUMERIC,
    periodo TEXT,
    fk_becario INTEGER,
    fk_beca INTEGER,
    CONSTRAINT fk_becario_beca_becario FOREIGN KEY (fk_becario) REFERENCES becario(id_becario),
    CONSTRAINT fk_becario_beca_beca FOREIGN KEY (fk_beca) REFERENCES beca(id_beca)
);
