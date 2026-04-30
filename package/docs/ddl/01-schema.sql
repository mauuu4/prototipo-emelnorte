-- ============================================================================
-- EMELNORTE - SIGEERN
-- Módulo de Gestión de Capacitación
-- Script de Base de Datos - PostgreSQL
-- Versión: 1.0
-- ============================================================================

-- ============================================================================
-- 1. CREACIÓN DE LA BASE DE DATOS
-- ============================================================================

-- Crear base de datos (ejecutar como superusuario)
-- CREATE DATABASE emelnorte_capacitacion;

-- ============================================================================
-- 2. SECUENCIAS (SERIAL)
-- ============================================================================

CREATE SEQUENCE direccion_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE usuario_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE plan_capacitacion_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE tema_capacitacion_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE tema_seleccionado_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE capacitacion_ejecutada_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE participante_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE observacion_plan_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE etapa_funcional_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE subetapa_funcional_id_seq START WITH 1 INCREMENT BY 1;

-- ============================================================================
-- 3. TABLAS DE CATÁLOGO
-- ============================================================================

-- Tabla: DIRECCION
CREATE TABLE direccion (
    id INTEGER NOT NULL DEFAULT NEXTVAL('direccion_id_seq'),
    nombre VARCHAR(100) NOT NULL,
    abreviatura VARCHAR(20) NOT NULL,
    max_temas INTEGER NOT NULL DEFAULT 5,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_direccion PRIMARY KEY (id),
    CONSTRAINT uq_direccion_abreviatura UNIQUE (abreviatura)
);

-- Tabla: ETAPA_FUNCIONAL
CREATE TABLE etapa_funcional (
    id INTEGER NOT NULL DEFAULT NEXTVAL('etapa_funcional_id_seq'),
    nombre VARCHAR(100) NOT NULL,
    CONSTRAINT pk_etapa_funcional PRIMARY KEY (id),
    CONSTRAINT uq_etapa_funcional_nombre UNIQUE (nombre)
);

-- Tabla: SUBETAPA_FUNCIONAL
CREATE TABLE subetapa_funcional (
    id INTEGER NOT NULL DEFAULT NEXTVAL('subetapa_funcional_id_seq'),
    nombre VARCHAR(100) NOT NULL,
    etapa_funcional_id INTEGER NOT NULL,
    CONSTRAINT pk_subetapa_funcional PRIMARY KEY (id),
    CONSTRAINT uq_subetapa_nombre UNIQUE (nombre),
    CONSTRAINT fk_subetapa_etapa FOREIGN KEY (etapa_funcional_id)
        REFERENCES etapa_funcional(id) ON DELETE RESTRICT
);

-- ============================================================================
-- 4. TABLAS PRINCIPALES
-- ============================================================================

-- Tabla: USUARIO
CREATE TABLE usuario (
    id INTEGER NOT NULL DEFAULT NEXTVAL('usuario_id_seq'),
    nombre VARCHAR(100) NOT NULL,
    cedula VARCHAR(10) NOT NULL,
    correo VARCHAR(100) NOT NULL,
    rol VARCHAR(30) NOT NULL,
    direccion_id INTEGER,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_usuario PRIMARY KEY (id),
    CONSTRAINT uq_usuario_cedula UNIQUE (cedula),
    CONSTRAINT fk_usuario_direccion FOREIGN KEY (direccion_id)
        REFERENCES direccion(id) ON DELETE SET NULL,
    CONSTRAINT chk_usuario_rol CHECK (rol IN ('ANALISTA', 'DIRECTOR', 'JEFE_PERSONAL', 'PRESIDENTE')),
    CONSTRAINT chk_usuario_estado CHECK (estado IN ('ACTIVO', 'INACTIVO'))
);

-- Tabla: PLAN_CAPACITACION
CREATE TABLE plan_capacitacion (
    id INTEGER NOT NULL DEFAULT NEXTVAL('plan_capacitacion_id_seq'),
    anio INTEGER NOT NULL,
    monto_referencial DECIMAL(12,2) NOT NULL,
    monto_aprobado DECIMAL(12,2),
    estado VARCHAR(30) NOT NULL DEFAULT 'BORRADOR',
    observaciones TEXT,
    direccion_id INTEGER NOT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_envio_jefe TIMESTAMP,
    fecha_envio_director TIMESTAMP,
    fecha_aprobacion TIMESTAMP,
    CONSTRAINT pk_plan_capacitacion PRIMARY KEY (id),
    CONSTRAINT fk_plan_direccion FOREIGN KEY (direccion_id)
        REFERENCES direccion(id) ON DELETE RESTRICT,
    CONSTRAINT uq_plan_anio_direccion UNIQUE (anio, direccion_id),
    CONSTRAINT chk_plan_estado CHECK (estado IN ('BORRADOR', 'EN_REVISION', 'EN_CORRECCION', 'EN_APROBACION', 'APROBADO')),
    CONSTRAINT chk_plan_monto CHECK (monto_referencial > 0)
);

-- Tabla: TEMA_CAPACITACION
CREATE TABLE tema_capacitacion (
    id INTEGER NOT NULL DEFAULT NEXTVAL('tema_capacitacion_id_seq'),
    nombre VARCHAR(200) NOT NULL,
    etapa_funcional VARCHAR(100) NOT NULL,
    subetapa_funcional VARCHAR(100) NOT NULL,
    num_participantes INTEGER NOT NULL,
    modalidad VARCHAR(20) NOT NULL,
    horas DECIMAL(5,2) NOT NULL,
    presupuesto_referencial DECIMAL(12,2) NOT NULL,
    mes_ejecucion INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    plan_id INTEGER NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_tema_capacitacion PRIMARY KEY (id),
    CONSTRAINT fk_tema_usuario FOREIGN KEY (usuario_id)
        REFERENCES usuario(id) ON DELETE RESTRICT,
    CONSTRAINT fk_tema_plan FOREIGN KEY (plan_id)
        REFERENCES plan_capacitacion(id) ON DELETE CASCADE,
    CONSTRAINT chk_tema_modalidad CHECK (modalidad IN ('VIRTUAL', 'PRESENCIAL', 'MIXTO')),
    CONSTnk_tema_mes CHECK (mes_ejecucion BETWEEN 1 AND 12),
    CONSTRAINT chk_tema_participantes CHECK (num_participantes > 0),
    CONSTRAINT chk_tema_horas CHECK (horas > 0),
    CONSTRAINT chk_tema_presupuesto CHECK (presupuesto_referencial >= 0)
);

-- Tabla: TEMA_SELECCIONADO
CREATE TABLE tema_seleccionado (
    id INTEGER NOT NULL DEFAULT NEXTVAL('tema_seleccionado_id_seq'),
    tema_id INTEGER NOT NULL,
    plan_id INTEGER NOT NULL,
    seleccionado BOOLEAN NOT NULL DEFAULT FALSE,
    presupuesto_aprobado DECIMAL(12,2),
    observaciones TEXT,
    CONSTRAINT pk_tema_seleccionado PRIMARY KEY (id),
    CONSTRAINT fk_ts_tema FOREIGN KEY (tema_id)
        REFERENCES tema_capacitacion(id) ON DELETE CASCADE,
    CONSTRAINT fk_ts_plan FOREIGN KEY (plan_id)
        REFERENCES plan_capacitacion(id) ON DELETE CASCADE,
    CONSTRAINT uq_ts_tema_plan UNIQUE (tema_id, plan_id)
);

-- Tabla: CAPACITACION_EJECUTADA
CREATE TABLE capacitacion_ejecutada (
    id INTEGER NOT NULL DEFAULT NEXTVAL('capacitacion_ejecutada_id_seq'),
    tema_seleccionado_id INTEGER NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    duracion_horas DECIMAL(5,2) NOT NULL,
    valor_sin_iva DECIMAL(12,2) NOT NULL,
    valor_con_iva DECIMAL(12,2) NOT NULL,
    proceso_contratacion VARCHAR(100) NOT NULL,
    centro_costo VARCHAR(50) NOT NULL,
    etapa_funcional VARCHAR(100) NOT NULL,
    subetapa_funcional VARCHAR(100) NOT NULL,
    empresa_capacitadora VARCHAR(200) NOT NULL,
    tipo_certificacion VARCHAR(50) NOT NULL,
    observaciones TEXT,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_capacitacion_ejecutada PRIMARY KEY (id),
    CONSTRAINT fk_ce_tema_seleccionado FOREIGN KEY (tema_seleccionado_id)
        REFERENCES tema_seleccionado(id) ON DELETE RESTRICT,
    CONSTRAINT chk_ce_fechas CHECK (fecha_fin >= fecha_inicio),
    CONSTRAINT chk_ce_duracion CHECK (duracion_horas > 0),
    CONSTRAINT chk_ce_valores CHECK (valor_con_iva >= valor_sin_iva)
);

-- Tabla: PARTICIPANTE
CREATE TABLE participante (
    id INTEGER NOT NULL DEFAULT NEXTVAL('participante_id_seq'),
    codigo VARCHAR(20) NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    cedula VARCHAR(10) NOT NULL,
    cargo VARCHAR(100) NOT NULL,
    ruta_certificado VARCHAR(500),
    capacitacion_id INTEGER NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_participante PRIMARY KEY (id),
    CONSTRAINT fk_participante_capacitacion FOREIGN KEY (capacitacion_id)
        REFERENCES capacitacion_ejecutada(id) ON DELETE CASCADE,
    CONSTRAINT uq_participante_codigo_cap UNIQUE (codigo, capacitacion_id)
);

-- Tabla: OBSERVACION_PLAN
CREATE TABLE observacion_plan (
    id INTEGER NOT NULL DEFAULT NEXTVAL('observacion_plan_id_seq'),
    observacion TEXT NOT NULL,
    autor VARCHAR(100) NOT NULL,
    tipo_observacion VARCHAR(30) NOT NULL,
    plan_id INTEGER NOT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_observacion_plan PRIMARY KEY (id),
    CONSTRAINT fk_op_plan FOREIGN KEY (plan_id)
        REFERENCES plan_capacitacion(id) ON DELETE CASCADE,
    CONSTRAINT chk_op_tipo CHECK (tipo_observacion IN ('APROBACION', 'DEVOLUCION', 'OBSERVACION'))
);

-- ============================================================================
-- 5. ÍNDICES
-- ============================================================================

CREATE INDEX idx_plan_anio ON plan_capacitacion(anio);
CREATE INDEX idx_plan_estado ON plan_capacitacion(estado);
CREATE INDEX idx_tema_plan ON tema_capacitacion(plan_id);
CREATE INDEX idx_tema_usuario ON tema_capacitacion(usuario_id);
CREATE INDEX idx_ts_plan ON tema_seleccionado(plan_id);
CREATE INDEX idx_ce_tema_seleccionado ON capacitacion_ejecutada(tema_seleccionado_id);
CREATE INDEX idx_participante_capacitacion ON participante(capacitacion_id);
CREATE INDEX idx_observacion_plan ON observacion_plan(plan_id);
CREATE INDEX idx_subetapa_etapa ON subetapa_funcional(etapa_funcional_id);

-- ============================================================================
-- 6. DATOS INICIALES
-- ============================================================================

-- Direcciones
INSERT INTO direccion (id, nombre, abreviatura, max_temas) VALUES
(1, 'Dirección Comercial', 'DCO', 7),
(2, 'Dirección de Distribución', 'DDO', 7),
(3, 'Dirección Administrativa', 'DAD', 5),
(4, 'Dirección de Operaciones', 'DOP', 5),
(5, 'Dirección Financiera', 'DFI', 5),
(6, 'Talento Humano', 'DTH', 5);

-- Reiniciar secuencias después de inserts con IDs explícitos
SELECT setval('direccion_id_seq', (SELECT MAX(id) FROM direccion));

-- Etapas Funcionales
INSERT INTO etapa_funcional (id, nombre) VALUES
(1, 'Administración y Gestión'),
(2, 'Operación y Mantenimiento'),
(3, 'Comercialización'),
(4, 'Desarrollo y Planificación'),
(5, 'Seguridad y Salud Ocupacional');

SELECT setval('etapa_funcional_id_seq', (SELECT MAX(id) FROM etapa_funcional));

-- Subetapas Funcionales
INSERT INTO subetapa_funcional (id, nombre, etapa_funcional_id) VALUES
(1, 'Gestión Administrativa', 1),
(2, 'Gestión Financiera', 1),
(3, 'Gestión de Talento Humano', 1),
(4, 'Mantenimiento Preventivo', 2),
(5, 'Mantenimiento Correctivo', 2),
(6, 'Operación del Sistema', 2),
(7, 'Atención al Cliente', 3),
(8, 'Facturación y Cobranza', 3),
(9, 'Lectura de Medidores', 3),
(10, 'Planificación Estratégica', 4),
(11, 'Gestión de Proyectos', 4),
(12, 'Prevención de Riesgos', 5),
(13, 'Capacitación en Seguridad', 5);

SELECT setval('subetapa_funcional_id_seq', (SELECT MAX(id) FROM subetapa_funcional));

-- Usuarios para el prototipo
INSERT INTO usuario (id, nombre, cedula, correo, rol, direccion_id) VALUES
(1, 'Ana López', '1712345678', 'ana.lopez@emelnorte.ec', 'ANALISTA', 6),
(2, 'Carlos Mendoza', '1723456789', 'carlos.mendoza@emelnorte.ec', 'DIRECTOR', 1),
(3, 'María García', '1734567890', 'maria.garcia@emelnorte.ec', 'DIRECTOR', 2),
(4, 'Pedro Sánchez', '1745678901', 'pedro.sanchez@emelnorte.ec', 'DIRECTOR', 3),
(5, 'Laura Torres', '1756789012', 'laura.torres@emelnorte.ec', 'JEFE_PERSONAL', 6),
(6, 'Roberto Díaz', '1767890123', 'roberto.diaz@emelnorte.ec', 'PRESIDENTE', NULL);

SELECT setval('usuario_id_seq', (SELECT MAX(id) FROM usuario));

-- ============================================================================
-- 7. DATOS DE EJEMPLO (Para pruebas del prototipo)
-- ============================================================================

-- Plan de Capacitación 2026 (Borrador)
INSERT INTO plan_capacitacion (id, anio, monto_referencial, estado, direccion_id) VALUES
(1, 2026, 50000.00, 'BORRADOR', 6);

SELECT setval('plan_capacitacion_id_seq', (SELECT MAX(id) FROM plan_capacitacion));

-- Temas de Capacitación de ejemplo
INSERT INTO tema_capacitacion (nombre, etapa_funcional, subetapa_funcional, num_participantes, modalidad, horas, presupuesto_referencial, mes_ejecucion, usuario_id, plan_id) VALUES
('Excel Avanzado para Análisis de Datos', 'Administración y Gestión', 'Gestión Administrativa', 15, 'PRESENCIAL', 40, 2500.00, 3, 2, 1),
('Gestión de Proyectos con PMBOK', 'Desarrollo y Planificación', 'Gestión de Proyectos', 10, 'VIRTUAL', 30, 3500.00, 4, 2, 1),
('Seguridad en Instalaciones Eléctricas', 'Seguridad y Salud Ocupacional', 'Prevención de Riesgos', 20, 'PRESENCIAL', 20, 1800.00, 5, 3, 1),
('Atención al Cliente Telefónico', 'Comercialización', 'Atención al Cliente', 25, 'MIXTO', 24, 1200.00, 3, 3, 1),
('Mantenimiento de Transformadores', 'Operación y Mantenimiento', 'Mantenimiento Preventivo', 8, 'PRESENCIAL', 48, 4500.00, 6, 4, 1);

SELECT setval('tema_capacitacion_id_seq', (SELECT MAX(id) FROM tema_capacitacion));

-- Temas Seleccionados
INSERT INTO tema_seleccionado (tema_id, plan_id, seleccionado, presupuesto_aprobado) VALUES
(1, 1, true, 2500.00),
(2, 1, true, 3000.00),
(3, 1, true, 1800.00),
(4, 1, false, NULL),
(5, 1, true, 4500.00);

SELECT setval('tema_seleccionado_id_seq', (SELECT MAX(id) FROM tema_seleccionado));

-- Plan 2025 (Aprobado - para referencia)
INSERT INTO plan_capacitacion (id, anio, monto_referencial, monto_aprobado, estado, direccion_id, fecha_creacion, fecha_aprobacion) VALUES
(2, 2025, 45000.00, 42000.00, 'APROBADO', 6, '2025-01-15 10:00:00', '2025-02-28 14:30:00');

SELECT setval('plan_capacitacion_id_seq', (SELECT MAX(id) FROM plan_capacitacion));

-- ============================================================================
-- 8. VISTAS ÚTILES
-- ============================================================================

-- Vista: Resumen de temas por plan
CREATE OR REPLACE VIEW v_resumen_temas_plan AS
SELECT
    p.id AS plan_id,
    p.anio,
    p.estado,
    COUNT(DISTINCT tc.id) AS total_temas,
    COUNT(DISTINCT CASE WHEN ts.seleccionado = true THEN tc.id END) AS temas_seleccionados,
    COALESCE(SUM(CASE WHEN ts.seleccionado = true THEN tc.presupuesto_referencial ELSE 0 END), 0) AS total_presupuesto_ref,
    COALESCE(SUM(CASE WHEN ts.seleccionado = true THEN ts.presupuesto_aprobado ELSE 0 END), 0) AS total_presupuesto_aprob
FROM plan_capacitacion p
LEFT JOIN tema_capacitacion tc ON tc.plan_id = p.id AND tc.estado = 'ACTIVO'
LEFT JOIN tema_seleccionado ts ON ts.tema_id = tc.id AND ts.plan_id = p.id
GROUP BY p.id, p.anio, p.estado;

-- Vista: Detalle de temas por dirección
CREATE OR REPLACE VIEW v_temas_por_direccion AS
SELECT
    d.nombre AS direccion,
    d.abreviatura,
    d.max_temas,
    COUNT(tc.id) AS temas_registrados,
    d.max_temas - COUNT(tc.id) AS temas_disponibles
FROM direccion d
LEFT JOIN usuario u ON u.direccion_id = d.id
LEFT JOIN tema_capacitacion tc ON tc.usuario_id = u.id AND tc.estado = 'ACTIVO'
WHERE d.estado = 'ACTIVO'
GROUP BY d.id, d.nombre, d.abreviatura, d.max_temas;

-- ============================================================================
-- 9. FUNCIONES ÚTILES
-- ============================================================================

-- Función: Verificar si se puede agregar más temas a una dirección
CREATE OR REPLACE FUNCTION fn_puede_agregar_tema(p_direccion_id INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    v_max_temas INTEGER;
    v_temas_actuales INTEGER;
BEGIN
    SELECT max_temas INTO v_max_temas FROM direccion WHERE id = p_direccion_id;

    SELECT COUNT(*) INTO v_temas_actuales
    FROM tema_capacitacion tc
    JOIN usuario u ON u.id = tc.usuario_id
    WHERE u.direccion_id = p_direccion_id
    AND tc.plan_id = (SELECT MAX(id) FROM plan_capacitacion WHERE anio = EXTRACT(YEAR FROM CURRENT_DATE))
    AND tc.estado = 'ACTIVO';

    RETURN v_temas_actuales < v_max_temas;
END;
$$ LANGUAGE plpgsql;

-- Función: Calcular total presupuesto seleccionado
CREATE OR REPLACE FUNCTION fn_total_presupuesto_seleccionado(p_plan_id INTEGER)
RETURNS DECIMAL(12,2) AS $$
DECLARE
    v_total DECIMAL(12,2);
BEGIN
    SELECT COALESCE(SUM(ts.presupuesto_aprobado), 0) INTO v_total
    FROM tema_seleccionado ts
    WHERE ts.plan_id = p_plan_id
    AND ts.seleccionado = true;

    RETURN v_total;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 10. PERMISOS (Ajustar según necesidad)
-- ============================================================================

-- Para el prototipo, se puede usar el usuario postgres
-- En producción, crear un usuario específico con permisos limitados

-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================
