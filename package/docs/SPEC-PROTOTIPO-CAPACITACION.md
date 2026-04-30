# EMELNORTE - SIGEERN
## Módulo de Gestión de Capacitación
### Documento de Especificación del Prototipo v1.0

---

## 1. INTRODUCCIÓN

### 1.1 Propósito del Documento

Este documento define la especificación técnica y funcional del prototipo del Módulo de Gestión de Capacitación para el Sistema Integrado de Gestión de EMELNORTE (SIGEERN). El propósito es establecer una base sólida para el desarrollo, documentando todas las decisiones de diseño, modelo de datos y funcionalidades antes de la implementación.

### 1.2 Alcance del Prototipo

El prototipo tiene como objetivo principal demostrar el flujo completo de:
- **Planificación de Capacitaciones**: Desde el registro del plan hasta la aprobación por parte del presidente
- **Ejecución de Capacitaciones**: Registro de capacitaciones ejecutadas con sus participantes

### 1.3 Funcionalidades Incluidas vs. Omitidas

#### Incluidas en el Prototipo
| ID | Requerimiento | Descripción |
|----|---------------|-------------|
| RN-01 | Registro del Plan | Crear plan de capacitación con año y monto referencial |
| RN-02 | Registro de Necesidades | Directores registran necesidades de capacitación |
| RN-03 | Límite de Temas | Restricción de máximo de temas por dirección |
| RN-04 | Gestión de Temas | Agregar, seleccionar, descartar temas y presupuestar |
| RN-05 | Alerta de Presupuesto | Notificación visual cuando se supera el presupuesto |
| RN-06 | Envío a Revisión | Enviar plan al Jefe de Personal |
| RN-07 | Revisión del Jefe | Revisar, aprobar, devolver con observaciones |
| RN-08 | Revisión del Director | Revisar plan y enviar al Presidente |
| RN-09 | Aprobación Final | Presidente aprueba y bloquea el plan |
| RN-10 | Ejecución | Registrar capacitaciones ejecutadas |
| RN-11 | Certificados | Adjuntar certificados de participantes |

#### Omitidas en el Prototipo
| ID | Requerimiento | Razón |
|----|---------------|-------|
| RN-12 | Reportes | Se implementarán en fase posterior |
| RN-13 | Notificaciones por correo | Se implementarán en fase posterior |

---

## 2. MODELO DE DATOS

### 2.1 Diagrama de Entidades

```
┌─────────────────┐       ┌─────────────────────────┐       ┌─────────────────┐
│   DIRECCION     │       │    PLAN_CAPACITACION    │       │    PRESIDENTE   │
├─────────────────┤       ├─────────────────────────┤       ├─────────────────┤
│ id              │       │ id                      │       │ id              │
│ nombre          │       │ anio                    │       │ nombre          │
│ abreviatura     │       │ monto_referencial       │       │ cedula          │
│ max_temas       │       │ monto_aprobado          │       │ correo          │
│ estado          │       │ estado                  │       └─────────────────┘
└─────────────────┘       │ fecha_creacion          │
         │                │ fecha_envio_jefe        │
         │                │ fecha_aprobacion        │
         │                │direccion_id(FK)         │
         │                └───────────┬─────────────┘
         │                            │
         │                            │
         ▼                            │
┌─────────────────┐                   │
│    USUARIO      │                   │
├─────────────────┤                   │
│ id              │◄──────────────────┘
│ nombre          │        ┌──────────┴───────────┐
│ cedula          │        │                       │
│ correo          │        ▼                       ▼
│ rol             │  ┌─────────────────┐  ┌─────────────────┐
│ direccion_id(FK)│  │TEMA_CAPACITACION│  │TEMA_SELECCIONADO│
└─────────────────┘  ├─────────────────┤  ├─────────────────┤
         │           │ id              │  │ id              │
         │           │ nombre          │  │seleccionado     │
         │           │ etapa_funcional │  │presupuesto_aprob│
         │           │ subetapa        │  │observacion       │
         │           │ num_participantes│ │tema_id(FK)      │
         │           │ modalidad        │  │plan_id(FK)      │
         │           │ horas            │  └─────────────────┘
         │           │ presupuesto_ref │
         │           │ mes_ejecucion    │
         │           │ usuario_id(FK)   │
         │           │ plan_id(FK)      │
         │           └─────────────────┘
         │
         │
         ▼
┌─────────────────────┐
│CAPACITACION_EJECUTADA│
├─────────────────────┤
│ id                  │
│ tema_id(FK)          │
│ fecha_inicio        │
│ fecha_fin           │
│ duracion_horas      │
│ valor_sin_iva       │
│ valor_con_iva       │
│ proceso_contratacion│
│ centro_costo        │
│ empresa_capacitadora│
│ tipo_certificacion  │
│ observaciones       │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│     PARTICIPANTE    │
├─────────────────────┤
│ id                  │
│ codigo              │
│ nombres             │
│ cedula              │
│ cargo               │
│ ruta_certificado    │
│ capacitacion_id(FK) │
└─────────────────────┘

┌─────────────────────┐
│  OBSERVACION_PLAN   │
├─────────────────────┤
│ id                  │
│ observacion         │
│ fecha               │
│ autor               │
│ tipo_observacion    │
│ plan_id(FK)         │
└─────────────────────┘
```

### 2.2 Definición de Entidades

#### 2.2.1 DIRECCION
| Campo | Tipo | Nullable | Descripción |
|-------|------|----------|-------------|
| id | SERIAL | NO | Identificador único |
| nombre | VARCHAR(100) | NO | Nombre completo de la dirección |
| abreviatura | VARCHAR(20) | NO | Sigla de la dirección |
| max_temas | INTEGER | NO | Máximo de temas permitidos (5 o 7) |
| estado | VARCHAR(20) | NO | ACTIVO, INACTIVO |
| fecha_creacion | TIMESTAMP | NO | Fecha de registro |

```sql
CREATE TABLE direccion (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    abreviatura VARCHAR(20) NOT NULL,
    max_temas INTEGER NOT NULL DEFAULT 5,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Datos iniciales
INSERT INTO direccion (nombre, abreviatura, max_temas) VALUES
('Dirección Comercial', 'DCO', 7),
('Dirección de Distribución', 'DDO', 7),
('Dirección Administrativa', 'DAD', 5),
('Dirección de Operaciones', 'DOP', 5),
('Dirección Financiera', 'DFI', 5),
('Talento Humano', 'DTH', 5);
```

#### 2.2.2 USUARIO
| Campo | Tipo | Nullable | Descripción |
|-------|------|----------|-------------|
| id | SERIAL | NO | Identificador único |
| nombre | VARCHAR(100) | NO | Nombre completo |
| cedula | VARCHAR(10) | NO | Número de cédula |
| correo | VARCHAR(100) | NO | Correo electrónico |
| rol | VARCHAR(30) | NO | ANALISTA, DIRECTOR, JEFE_PERSONAL, PRESIDENTE |
| direccion_id | INTEGER | SÍ | FK a dirección (null para presidente) |
| estado | VARCHAR(20) | NO | ACTIVO, INACTIVO |
| fecha_creacion | TIMESTAMP | NO | Fecha de registro |

```sql
CREATE TABLE usuario (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    cedula VARCHAR(10) NOT NULL UNIQUE,
    correo VARCHAR(100) NOT NULL,
    rol VARCHAR(30) NOT NULL,
    direccion_id INTEGER REFERENCES direccion(id),
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Datos iniciales para prototipo
INSERT INTO usuario (nombre, cedula, correo, rol, direccion_id) VALUES
('Ana López', '1712345678', 'ana.lopez@emelnorte.ec', 'ANALISTA', 6),
('Carlos Mendoza', '1723456789', 'carlos.mendoza@emelnorte.ec', 'DIRECTOR', 1),
('María García', '1734567890', 'maria.garcia@emelnorte.ec', 'DIRECTOR', 2),
('Pedro Sánchez', '1745678901', 'pedro.sanchez@emelnorte.ec', 'DIRECTOR', 3),
('Laura Torres', '1756789012', 'laura.torres@emelnorte.ec', 'JEFE_PERSONAL', 6),
('Roberto Díaz', '1767890123', 'roberto.diaz@emelnorte.ec', 'PRESIDENTE', NULL);
```

#### 2.2.3 PLAN_CAPACITACION
| Campo | Tipo | Nullable | Descripción |
|-------|------|----------|-------------|
| id | SERIAL | NO | Identificador único |
| anio | INTEGER | NO | Año del plan |
| monto_referencial | DECIMAL(12,2) | NO | Monto referencial asignado |
| monto_aprobado | DECIMAL(12,2) | SÍ | Monto aprobado por el presidente |
| estado | VARCHAR(30) | NO | BORRADOR, EN_REVISION, EN_CORRECCION, EN_APROBACION, APROBADO |
| observaciones | TEXT | SÍ | Observaciones generales |
| direccion_id | INTEGER | NO | FK a dirección (talento humano) |
| fecha_creacion | TIMESTAMP | NO | Fecha de creación |
| fecha_envio_jefe | TIMESTAMP | SÍ | Fecha de envío al jefe |
| fecha_envio_director | TIMESTAMP | SÍ | Fecha de envío al director |
| fecha_aprobacion | TIMESTAMP | SÍ | Fecha de aprobación final |

```sql
CREATE TABLE plan_capacitacion (
    id SERIAL PRIMARY KEY,
    anio INTEGER NOT NULL,
    monto_referencial DECIMAL(12,2) NOT NULL,
    monto_aprobado DECIMAL(12,2),
    estado VARCHAR(30) NOT NULL DEFAULT 'BORRADOR',
    observaciones TEXT,
    direccion_id INTEGER NOT NULL REFERENCES direccion(id),
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_envio_jefe TIMESTAMP,
    fecha_envio_director TIMESTAMP,
    fecha_aprobacion TIMESTAMP,
    UNIQUE(anio, direccion_id)
);
```

#### 2.2.4 TEMA_CAPACITACION
| Campo | Tipo | Nullable | Descripción |
|-------|------|----------|-------------|
| id | SERIAL | NO | Identificador único |
| nombre | VARCHAR(200) | NO | Nombre de la capacitación |
| etapa_funcional | VARCHAR(100) | NO | Etapa funcional |
| subetapa_funcional | VARCHAR(100) | NO | Subetapa funcional |
| num_participantes | INTEGER | NO | Número esperado de participantes |
| modalidad | VARCHAR(20) | NO | VIRTUAL, PRESENCIAL, MIXTO |
| horas | DECIMAL(5,2) | NO | Duración en horas |
| presupuesto_referencial | DECIMAL(12,2) | NO | Presupuesto estimado |
| mes_ejecucion | INTEGER | NO | Mes de ejecución (1-12) |
| usuario_id | INTEGER | NO | FK a usuario que registró |
| plan_id | INTEGER | NO | FK a plan de capacitación |
| estado | VARCHAR(20) | NO | ACTIVO, ELIMINADO |
| fecha_creacion | TIMESTAMP | NO | Fecha de registro |

```sql
CREATE TABLE tema_capacitacion (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    etapa_funcional VARCHAR(100) NOT NULL,
    subetapa_funcional VARCHAR(100) NOT NULL,
    num_participantes INTEGER NOT NULL,
    modalidad VARCHAR(20) NOT NULL,
    horas DECIMAL(5,2) NOT NULL,
    presupuesto_referencial DECIMAL(12,2) NOT NULL,
    mes_ejecucion INTEGER NOT NULL CHECK (mes_ejecucion BETWEEN 1 AND 12),
    usuario_id INTEGER NOT NULL REFERENCES usuario(id),
    plan_id INTEGER NOT NULL REFERENCES plan_capacitacion(id),
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### 2.2.5 TEMA_SELECCIONADO
| Campo | Tipo | Nullable | Descripción |
|-------|------|----------|-------------|
| id | SERIAL | NO | Identificador único |
| tema_id | INTEGER | NO | FK a tema de capacitación |
| plan_id | INTEGER | NO | FK a plan de capacitación |
| seleccionado | BOOLEAN | NO | Si está seleccionado para el plan |
| presupuesto_aprobado | DECIMAL(12,2) | SÍ | Presupuesto aprobado |
| observaciones | TEXT | SÍ | Observaciones del analista |

```sql
CREATE TABLE tema_seleccionado (
    id SERIAL PRIMARY KEY,
    tema_id INTEGER NOT NULL REFERENCES tema_capacitacion(id),
    plan_id INTEGER NOT NULL REFERENCES plan_capacitacion(id),
    seleccionado BOOLEAN NOT NULL DEFAULT FALSE,
    presupuesto_aprobado DECIMAL(12,2),
    observaciones TEXT,
    UNIQUE(tema_id, plan_id)
);
```

#### 2.2.6 CAPACITACION_EJECUTADA
| Campo | Tipo | Nullable | Descripción |
|-------|------|----------|-------------|
| id | SERIAL | NO | Identificador único |
| tema_seleccionado_id | INTEGER | NO | FK a tema seleccionado |
| fecha_inicio | DATE | NO | Fecha de inicio |
| fecha_fin | DATE | NO | Fecha de fin |
| duracion_horas | DECIMAL(5,2) | NO | Duración en horas |
| valor_sin_iva | DECIMAL(12,2) | NO | Valor sin IVA |
| valor_con_iva | DECIMAL(12,2) | NO | Valor con IVA |
| proceso_contratacion | VARCHAR(100) | NO | Proceso de contratación |
| centro_costo | VARCHAR(50) | NO | Centro de costo |
| etapa_funcional | VARCHAR(100) | NO | Etapa funcional |
| subetapa_funcional | VARCHAR(100) | NO | Subetapa funcional |
| empresa_capacitadora | VARCHAR(200) | NO | Nombre de la empresa |
| tipo_certificacion | VARCHAR(50) | NO | Tipo de certificación |
| observaciones | TEXT | SÍ | Observaciones adicionales |
| estado | VARCHAR(20) | NO | ACTIVO, FINALIZADO |
| fecha_creacion | TIMESTAMP | NO | Fecha de registro |

```sql
CREATE TABLE capacitacion_ejecutada (
    id SERIAL PRIMARY KEY,
    tema_seleccionado_id INTEGER NOT NULL REFERENCES tema_seleccionado(id),
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
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### 2.2.7 PARTICIPANTE
| Campo | Tipo | Nullable | Descripción |
|-------|------|----------|-------------|
| id | SERIAL | NO | Identificador único |
| codigo | VARCHAR(20) | NO | Código del empleado |
| nombres | VARCHAR(100) | NO | Nombres completos |
| cedula | VARCHAR(10) | NO | Número de cédula |
| cargo | VARCHAR(100) | NO | Cargo del empleado |
| ruta_certificado | VARCHAR(500) | SÍ | Ruta del archivo del certificado |
| capacitacion_id | INTEGER | NO | FK a capacitación ejecutada |
| estado | VARCHAR(20) | NO | ACTIVO, ELIMINADO |
| fecha_creacion | TIMESTAMP | NO | Fecha de registro |

```sql
CREATE TABLE participante (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    cedula VARCHAR(10) NOT NULL,
    cargo VARCHAR(100) NOT NULL,
    ruta_certificado VARCHAR(500),
    capacitacion_id INTEGER NOT NULL REFERENCES capacitacion_ejecutada(id),
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### 2.2.8 OBSERVACION_PLAN
| Campo | Tipo | Nullable | Descripción |
|-------|------|----------|-------------|
| id | SERIAL | NO | Identificador único |
| observacion | TEXT | NO | Contenido de la observación |
| autor | VARCHAR(100) | NO | Nombre de quien hizo la observación |
| tipo_observacion | VARCHAR(30) | NO | APROBACION, DEVOLUCION, OBSERVACION |
| plan_id | INTEGER | NO | FK a plan de capacitación |
| fecha_creacion | TIMESTAMP | NO | Fecha de la observación |

```sql
CREATE TABLE observacion_plan (
    id SERIAL PRIMARY KEY,
    observacion TEXT NOT NULL,
    autor VARCHAR(100) NOT NULL,
    tipo_observacion VARCHAR(30) NOT NULL,
    plan_id INTEGER NOT NULL REFERENCES plan_capacitacion(id),
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 2.3 Catálogo de Valores

#### 2.3.1 ETAPA_FUNCIONAL
```sql
CREATE TABLE etapa_funcional (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

INSERT INTO etapa_funcional (nombre) VALUES
('Administración y Gestión'),
('Operación y Mantenimiento'),
('Comercialización'),
('Desarrollo y Planificación'),
('Seguridad y Salud Ocupacional');
```

#### 2.3.2 SUBETAPA_FUNCIONAL
```sql
CREATE TABLE subetapa_funcional (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    etapa_funcional_id INTEGER NOT NULL REFERENCES etapa_funcional(id)
);

INSERT INTO subetapa_funcional (nombre, etapa_funcional_id) VALUES
('Gestión Administrativa', 1),
('Gestión Financiera', 1),
('Gestión de Talento Humano', 1),
('Mantenimiento Preventivo', 2),
('Mantenimiento Correctivo', 2),
('Operación del Sistema', 2),
('Atención al Cliente', 3),
('Facturación y Cobranza', 3),
('Lectura de Medidores', 3),
('Planificación Estratégica', 4),
('Gestión de Proyectos', 4),
('Prevención de Riesgos', 5),
('Capacitación en Seguridad', 5);
```

#### 2.3.3 MODALIDAD
Valores fijos: VIRTUAL, PRESENCIAL, MIXTO

#### 2.3.4 ESTADO_PLAN
Valores fijos: BORRADOR, EN_REVISION, EN_CORRECCION, EN_APROBACION, APROBADO

#### 2.3.5 ROL_USUARIO
Valores fijos: ANALISTA, DIRECTOR, JEFE_PERSONAL, PRESIDENTE

#### 2.3.6 TIPO_OBSERVACION
Valores fijos: APROBACION, DEVOLUCION, OBSERVACION

---

## 3. FUNCIONALIDADES DEL PROTOTIPO

### 3.1 Módulo de Planificación

#### 3.1.1 Crear Plan de Capacitación (RN-01)

**Actor**: Analista de Talento Humano

**Descripción**: El analista crea un nuevo plan de capacitación para un año específico.

**Pantalla**: `plan-nuevo.xhtml`

**Campos del formulario**:
| Campo | Tipo | Validación | Requerido |
|-------|------|------------|-----------|
| Año | Integer | >= año actual | Sí |
| Monto Referencial | Decimal | > 0 | Sí |

**Comportamiento**:
1. Validar que no exista un plan para el año seleccionado
2. Guardar el plan con estado inicial BORRADOR
3. Mostrar mensaje de confirmación
4. Redirigir a la lista de planes

**Estado resultante**: BORRADOR

#### 3.1.2 Registrar Necesidades de Capacitación (RN-02)

**Actor**: Director de Área

**Descripción**: Los directores registran las necesidades de capacitación de su dirección.

**Pantalla**: `necesidades-lista.xhtml` y `necesidad-nueva.xhtml`

**Campos del formulario**:
| Campo | Tipo | Validación | Fuente |
|-------|------|------------|--------|
| Dirección | Texto | Solo lectura | Usuario logueado |
| Etapa Funcional | Select | Válido | Catálogo etapa_funcional |
| Subetapa Funcional | Select | Dependiente de etapa | Catálogo subetapa_funcional |
| Nombre de Capacitación | Texto | Max 200 chars | Ingresado por usuario |
| Número de Participantes | Integer | > 0 | Ingresado por usuario |
| Modalidad | Select | VIRTUAL/PRESENCIAL/MIXTO | Ingresado por usuario |
| Tiempo en Horas | Decimal | > 0 | Ingresado por usuario |
| Presupuesto Referencial | Decimal | > 0 | Ingresado por usuario |
| Mes de Ejecución | Select | 1-12 | Ingresado por usuario |

**Comportamiento**:
1. Cargar dirección del usuario actual
2. Validar límite de temas según dirección (RN-03)
3. Asignar automáticamente al plan del año vigente
4. Permitir editar y eliminar temas mientras el plan esté en BORRADOR

**Regla de negocio RN-03**:
- DCO y DDO: máximo 7 temas
- Resto de direcciones: máximo 5 temas

#### 3.1.3 Gestionar Temas del Plan (RN-04)

**Actor**: Analista de Talento Humano

**Descripción**: El analista puede agregar temas adicionales, seleccionar/descartar temas y registrar presupuesto aprobado.

**Pantalla**: `plan-detalle.xhtml`

**Funcionalidades**:
1. **Ver todos los temas**: Lista consolidada de todas las direcciones
2. **Agregar tema manual**: El analista puede agregar temas no propuestos por direcciones
3. **Seleccionar/Descartar**: Checkbox para marcar temas seleccionados
4. **Presupuesto aprobado**: Campo editable por tema
5. **Total acumulado**: Cálculo automático de la suma de presupuestos aprobados

**Cálculos**:
```
Total Seleccionado = SUM(presupuesto_aprobado) WHERE seleccionado = true
Alerta = Total Seleccionado > monto_referencial
```

**Comportamiento RN-05**:
- Mostrar alerta visual (banner amarillo) cuando Total Seleccionado > Monto Referencial
- El analista puede continuar pero debe estar consciente del exceso

#### 3.1.4 Flujo de Aprobación

##### 3.1.4.1 Enviar a Revisión (RN-06)

**Actor**: Analista de Talento Humano

**Acción**: Botón "Enviar a Jefe de Personal"

**Comportamiento**:
1. Validar que haya al menos un tema seleccionado
2. Cambiar estado a EN_REVISION
3. Registrar fecha_envio_jefe
4. Mostrar mensaje de confirmación

**Estado resultante**: EN_REVISION

##### 3.1.4.2 Revisión del Jefe de Personal (RN-07)

**Actor**: Jefe de Personal

**Pantalla**: `plan-revision-jefe.xhtml`

**Opciones de acción**:
1. **Aprobar**: Cambia estado a EN_APROBACION, registra observación de aprobación
2. **Devolver**: Cambia estado a EN_CORRECCION, registra observación de devolución
3. **Agregar Observación**: Solo añade observación sin cambiar estado

**Comportamiento**:
- Mostrar plan completo con todos los temas
- Mostrar observaciones anteriores
- Permitir agregar nueva observación

**Estado resultante**: EN_APROBACION o EN_CORRECCION

##### 3.1.4.3 Revisión del Director (RN-08)

**Actor**: Director (genérico para prototipo)

**Pantalla**: `plan-revision-director.xhtml`

**Comportamiento**:
1. Visualizar plan completo con observaciones del jefe
2. Botón "Enviar al Presidente"
3. Cambiar estado a EN_APROBACION

**Estado resultante**: EN_APROBACION

##### 3.1.4.4 Aprobación Final del Presidente (RN-09)

**Actor**: Presidente

**Pantalla**: `plan-aprobacion.xhtml`

**Opciones de acción**:
1. **Aprobar**:
   - Cambiar estado a APROBADO
   - Registrar fecha_aprobacion
   - Registrar monto_aprobado (puede ser diferente al referencial)
   - **Bloquear plan**: No permitir más modificaciones

**Estado resultante**: APROBADO (permanente, sin edición)

### 3.2 Módulo de Ejecución

#### 3.2.1 Registrar Capacitación Ejecutada (RN-10)

**Actor**: Analista de Talento Humano

**Pantalla**: `ejecucion-nueva.xhtml` y `ejecucion-lista.xhtml`

**Campos del formulario**:
| Campo | Tipo | Validación | Fuente |
|-------|------|------------|--------|
| Tema de Capacitación | Select | Del plan aprobado | Temas seleccionados |
| Fecha de Inicio | Date | >= hoy | Ingresado |
| Fecha de Fin | Date | >= fecha_inicio | Ingresado |
| Duración en Horas | Decimal | > 0 | Calculado o ingresado |
| Valor sin IVA | Decimal | > 0 | Ingresado |
| Valor con IVA | Decimal | >= valor_sin_iva | Calculado o ingresado |
| Proceso de Contratación | Texto | Max 100 chars | Ingresado |
| Centro de Costo | Texto | Max 50 chars | Ingresado |
| Etapa Funcional | Select | Del tema | Auto |
| Subetapa Funcional | Select | Del tema | Auto |
| Empresa Capacitadora | Texto | Max 200 chars | Ingresado |
| Tipo de Certificación | Select | Opciones predefinidas | Ingresado |
| Observaciones | Textarea | Opcional | Ingresado |

**Cálculo automático**:
```
valor_con_iva = valor_sin_iva * 1.12 (asumiendo IVA 12%)
```

#### 3.2.2 Gestionar Participantes

**Pantalla**: `participantes.xhtml` (incluida en ejecución)

**Campos del formulario**:
| Campo | Tipo | Validación |
|-------|------|------------|
| Código | Texto | Requerido, único por capacitación |
| Nombres | Texto | Requerido |
| Cédula | Texto | Requerido, 10 dígitos |
| Cargo | Texto | Requerido |

**Comportamiento**:
1. Agregar participante a la lista temporal
2. Editar participante existente
3. Eliminar participante
4. Listar todos los participantes de la capacitación

#### 3.2.3 Adjuntar Certificados (RN-11)

**Actor**: Secretaria

**Pantalla**: `participantes.xhtml` (continuación)

**Funcionalidad**:
1. Botón "Adjuntar Certificado" por cada participante
2. Selector de archivo (PDF, JPG, PNG)
3. Visualización del archivo adjunto
4. Descarga del certificado

**Restricciones**:
- Formatos permitidos: PDF, JPG, PNG
- Tamaño máximo: 5 MB
- Almacenamiento: Sistema de archivos local

---

## 4. ESTRUCTURA DE PANTALLAS

### 4.1 Arquitectura de Navegación

```
                    ┌─────────────────┐
                    │     LOGIN        │
                    │   (Simulado)     │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌─────────┐   ┌───────────┐  ┌──────────┐
        │ ANALISTA│   │ DIRECTOR  │  │ PRESIDENTE│
        │         │   │           │  │          │
        └────┬────┘   └─────┬─────┘  └────┬─────┘
             │              │              │
             ▼              ▼              ▼
        ┌─────────────────────────────────────────┐
        │              MENÚ PRINCIPAL             │
        │  ┌──────────┐  ┌─────────────────────┐  │
        │  │Planifica-│  │     Ejecución       │  │
        │  │   ción   │  │                     │  │
        │  └──────────┘  └─────────────────────┘  │
        └─────────────────────────────────────────┘
```

### 4.2 Mapa de Pantallas por Rol

#### 4.2.1 Analista de Talento Humano

| Pantalla | Descripción | URL |
|----------|-------------|-----|
| Login Simulado | Selector de usuario | `/login.xhtml` |
| Dashboard | Resumen de planes | `/dashboard.xhtml` |
| Lista de Planes | Todos los planes | `/planes/lista.xhtml` |
| Crear Plan | Formulario nuevo plan | `/planes/nuevo.xhtml` |
| Detalle del Plan | Gestión de temas | `/planes/detalle.xhtml?id=X` |
| Revisión (Jefe) | Revisar planes recibidos | `/revision-jefe/lista.xhtml` |
| Revisión (Director) | Revisar planes recibidos | `/revision-director/lista.xhtml` |
| Lista de Ejecuciones | Capacitaciones ejecutadas | `/ejecucion/lista.xhtml` |
| Nueva Ejecución | Registrar capacitación | `/ejecucion/nueva.xhtml` |
| Participantes | Gestionar participantes | `/ejecucion/participantes.xhtml?id=X` |

#### 4.2.2 Director de Área

| Pantalla | Descripción | URL |
|----------|-------------|-----|
| Login Simulado | Selector de usuario | `/login.xhtml` |
| Mis Necesidades | Mis temas propuestos | `/necesidades/mis-temas.xhtml` |
| Nueva Necesidad | Registrar tema | `/necesidades/nuevo.xhtml` |
| Revisión Director | Planes para revisar | `/revision-director/lista.xhtml` |

#### 4.2.3 Jefe de Personal

| Pantalla | Descripción | URL |
|----------|-------------|-----|
| Login Simulado | Selector de usuario | `/login.xhtml` |
| Revisión Jefe | Planes para revisar | `/revision-jefe/lista.xhtml` |

#### 4.2.4 Presidente

| Pantalla | Descripción | URL |
|----------|-------------|-----|
| Login Simulado | Selector de usuario | `/login.xhtml` |
| Aprobación Final | Planes para aprobar | `/aprobacion/lista.xhtml` |

### 4.3 Wireframes Simplificados

#### 4.3.1 Login Simulado

```
┌─────────────────────────────────────────────────┐
│  SIGEERN - Módulo de Capacitación              │
├─────────────────────────────────────────────────┤
│                                                 │
│  Seleccione su usuario:                         │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │ [Ana López - Analista                ▼] │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  [Ingresar al Sistema]                          │
│                                                 │
└─────────────────────────────────────────────────┘
```

#### 4.3.2 Dashboard del Analista

```
┌─────────────────────────────────────────────────────────┐
│  SIGEERN - Dashboard                      [Cerrar Sesión]│
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Bienvenido: Ana López (Analista)                       │
│  Dirección: Talento Humano                             │
│                                                         │
│  ┌───────────────────┐  ┌───────────────────┐          │
│  │ Plans en Borador  │  │ Planes en Revisión│          │
│  │        2          │  │        1          │          │
│  └───────────────────┘  └───────────────────┘          │
│                                                         │
│  ┌───────────────────┐  ┌───────────────────┐          │
│  │ Planes Aprobados  │  │ Ejecuciones 2026  │          │
│  │        5          │  │        12         │          │
│  └───────────────────┘  └───────────────────┘          │
│                                                         │
│  [Crear Nuevo Plan]  [Ver Todos los Planes]           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### 4.3.3 Detalle del Plan (Gestión de Temas)

```
┌─────────────────────────────────────────────────────────────────────┐
│  SIGEERN - Plan de Capacitación 2026                  [Volver]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Estado: BORRADOR                      Monto Referencial: $50,000   │
│                                                                     │
│  ⚠️ ALERTA: El presupuesto seleccionado ($55,000) excede el      │
│     monto referencial en $5,000                                    │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  Temas Registrados                                                  │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ □ │ Tema                    │ Dirección  │ Ppto Ref │ Ppto Ap │ │
│  ├───┼─────────────────────────┼─────────────┼──────────┼─────────┤ │
│  │ ☑ │ Excel Avanzado          │ DCO         │ $2,000    │ $2,000  │ │
│  │ ☑ │ Gestión de Proyectos    │ DDO         │ $3,500    │ $3,000  │ │
│  │ ☑ │ Seguridad Eléctrica     │ DAD         │ $4,000    │ $4,000  │ │
│  │ ☐ │ Marketing Digital       │ DCO         │ $2,500    │ -       │ │
│  │ ☑ │ Liderazgo Efectivo      │ DFI         │ $1,800    │ $1,500  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Total Seleccionado: $10,500                                        │
│                                                                     │
│  [Agregar Tema Manual]                                              │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  Observaciones del Plan                                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ [Agregar observación...]                                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  [Guardar Cambios]  [Enviar a Jefe de Personal]                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 4.3.4 Nueva Capacitación Ejecutada

```
┌─────────────────────────────────────────────────────────────────────┐
│  Registrar Capacitación Ejecutada                       [Volver]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Datos de la Capacitación                                          │
│                                                                     │
│  Tema de Capacitación: [Excel Avanzado - 2026            ▼]        │
│                                                                     │
│  ┌──────────────────────────┐  ┌──────────────────────────┐        │
│  │ Fecha de Inicio:         │  │ Fecha de Fin:            │        │
│  │ [15/03/2026    📅]       │  │ [20/03/2026      📅]     │        │
│  └──────────────────────────┘  └──────────────────────────┘        │
│                                                                     │
│  ┌──────────────────────────┐  ┌──────────────────────────┐        │
│  │ Duración (horas):        │  │ Empresa Capacitadora:    │        │
│  │ [40           ]          │  │ [Instituto TEC          ]│        │
│  └──────────────────────────┘  └──────────────────────────┘        │
│                                                                     │
│  ┌──────────────────────────┐  ┌──────────────────────────┐        │
│  │ Valor sin IVA:           │  │ Valor con IVA:           │        │
│  │ [$1,500.00      ]        │  │ [$1,680.00     ] (auto)  │        │
│  └──────────────────────────┘  └──────────────────────────┘        │
│                                                                     │
│  ┌──────────────────────────┐  ┌──────────────────────────┐        │
│  │ Proceso Contratación:    │  │ Centro de Costo:        │        │
│  │ [Licitación     ▼]        │  │ [CC-001-DCO    ]        │        │
│  └──────────────────────────┘  └──────────────────────────┘        │
│                                                                     │
│  Etapa Funcional: Administración y Gestión                         │
│  Subetapa: Gestión Administrativa                                  │
│                                                                     │
│  Tipo de Certificación: [Certificado de Aprobación       ▼]        │
│                                                                     │
│  Observaciones:                                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ [Capacitación realizada en las instalaciones de la empresa]│    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  [Guardar]  [Guardar y Agregar Participantes]                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. ESTRUCTURA TÉCNICA DEL PROYECTO

### 5.1 Estructura de Directorios

```
modulo-capacitacion/
├── src/
│   └── main/
│       ├── java/
│       │   └── com/
│       │       └── emelnorte/
│       │           └── capacitacion/
│       │               ├── model/
│       │               │   ├── entities/
│       │               │   │   ├── PlanCapacitacion.java
│       │               │   │   ├── TemaCapacitacion.java
│       │               │   │   ├── TemaSeleccionado.java
│       │               │   │   ├── CapacitacionEjecutada.java
│       │               │   │   ├── Participante.java
│       │               │   │   ├── Usuario.java
│       │               │   │   ├── Direccion.java
│       │               │   │   ├── EtapaFuncional.java
│       │               │   │   ├── SubetapaFuncional.java
│       │               │   │   └── ObservacionPlan.java
│       │               │   └── enums/
│       │               │       ├── EstadoPlan.java
│       │               │       ├── Modalidad.java
│       │               │       ├── RolUsuario.java
│       │               │       └── TipoObservacion.java
│       │               ├── repository/
│       │               │   ├── PlanCapacitacionRepository.java
│       │               │   ├── TemaCapacitacionRepository.java
│       │               │   ├── TemaSeleccionadoRepository.java
│       │               │   ├── CapacitacionEjecutadaRepository.java
│       │               │   ├── ParticipanteRepository.java
│       │               │   ├── UsuarioRepository.java
│       │               │   └── DireccionRepository.java
│       │               ├── service/
│       │               │   ├── PlanCapacitacionService.java
│       │               │   ├── TemaCapacitacionService.java
│       │               │   ├── CapacitacionService.java
│       │               │   └── ParticipanteService.java
│       │               ├── controller/
│       │               │   ├── LoginController.java
│       │               │   ├── PlanController.java
│       │               │   ├── TemaController.java
│       │               │   ├── EjecucionController.java
│       │               │   └── ParticipanteController.java
│       │               └── util/
│       │                   ├── FacesUtil.java
│       │                   └── Constantes.java
│       ├── resources/
│       │   ├── META-INF/
│       │   │   └── persistence.xml
│       │   └── bundles/
│       │       └── messages.properties
│       └── webapp/
│           ├── WEB-INF/
│           │   ├── web.xml
│           │   └── beans.xml
│           ├── resources/
│           │   ├── css/
│           │   │   └── estilos.css
│           │   └── images/
│           ├── login.xhtml
│           ├── dashboard.xhtml
│           ├── plantillas/
│           │   └── template.xhtml
│           ├── planes/
│           │   ├── lista.xhtml
│           │   ├── nuevo.xhtml
│           │   └── detalle.xhtml
│           ├── necesidades/
│           │   ├── mis-temas.xhtml
│           │   └── nuevo.xhtml
│           ├── revision/
│           │   ├── jefe-lista.xhtml
│           │   └── director-lista.xhtml
│           ├── aprobacion/
│           │   └── lista.xhtml
│           └── ejecucion/
│               ├── lista.xhtml
│               ├── nuevo.xhtml
│               └── participantes.xhtml
├── pom.xml
└── README.md
```

### 5.2 Dependencias Maven (pom.xml)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.emelnorte</groupId>
    <artifactId>modulo-capacitacion</artifactId>
    <version>1.0.0-SNAPSHOT</version>
    <packaging>war</packaging>

    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <failOnMissingWebXml>false</failOnMissingWebXml>
    </properties>

    <dependencies>
        <!-- Java EE API -->
        <dependency>
            <groupId>javax</groupId>
            <artifactId>javaee-api</artifactId>
            <version>8.0</version>
            <scope>provided</scope>
        </dependency>

        <!-- PrimeFaces -->
        <dependency>
            <groupId>org.primefaces</groupId>
            <artifactId>primefaces</artifactId>
            <version>10.0.0</version>
        </dependency>

        <!-- PrimeFaces Themes -->
        <dependency>
            <groupId>org.primefaces.themes</groupId>
            <artifactId>bootstrap</artifactId>
            <version>10.0.0</version>
        </dependency>

        <!-- PostgreSQL JDBC Driver -->
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <version>42.3.3</version>
            <scope>provided</scope>
        </dependency>

        <!-- JPA/Hibernate -->
        <dependency>
            <groupId>org.hibernate</groupId>
            <artifactId>hibernate-core</artifactId>
            <version>5.6.5.Final</version>
        </dependency>

        <!-- Bean Validation -->
        <dependency>
            <groupId>org.hibernate.validator</groupId>
            <artifactId>hibernate-validator</artifactId>
            <version>7.0.2.Final</version>
        </dependency>

        <!-- OmniFaces (utilidades para JSF) -->
        <dependency>
            <groupId>org.omnifaces</groupId>
            <artifactId>omnifaces</artifactId>
            <version>3.6</version>
        </dependency>
    </dependencies>

    <build>
        <finalName>modulo-capacitacion</finalName>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.8.1</version>
                <configuration>
                    <source>11</source>
                    <target>11</target>
                </configuration>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-war-plugin</artifactId>
                <version>3.3.1</version>
                <configuration>
                    <failOnMissingWebXml>false</failOnMissingWebXml>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

### 5.3 Configuración de Persistencia (persistence.xml)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<persistence version="2.2"
    xmlns="http://xmlns.jcp.org/xml/ns/persistence"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://xmlns.jcp.org/xml/ns/persistence
    http://xmlns.jcp.org/xml/ns/persistence/persistence_2_2.xsd">

    <persistence-unit name="capacitacionPU"
        transaction-type="JTA">
        <provider>org.hibernate.jpa.HibernatePersistenceProvider</provider>

        <jta-data-source>java:jboss/datasources/CapacitacionDS</jta-data-source>

        <class>com.emelnorte.capacitacion.model.entities.PlanCapacitacion</class>
        <class>com.emelnorte.capacitacion.model.entities.TemaCapacitacion</class>
        <class>com.emelnorte.capacitacion.model.entities.TemaSeleccionado</class>
        <class>com.emelnorte.capacitacion.model.entities.CapacitacionEjecutada</class>
        <class>com.emelnorte.capacitacion.model.entities.Participante</class>
        <class>com.emelnorte.capacitacion.model.entities.Usuario</class>
        <class>com.emelnorte.capacitacion.model.entities.Direccion</class>
        <class>com.emelnorte.capacitacion.model.entities.EtapaFuncional</class>
        <class>com.emelnorte.capacitacion.model.entities.SubetapaFuncional</class>
        <class>com.emelnorte.capacitacion.model.entities.ObservacionPlan</class>

        <properties>
            <property name="hibernate.dialect"
                value="org.hibernate.dialect.PostgreSQLDialect"/>
            <property name="hibernate.hbm2ddl.auto" value="update"/>
            <property name="hibernate.show_sql" value="true"/>
            <property name="hibernate.format_sql" value="true"/>
        </properties>
    </persistence-unit>
</persistence>
```

### 5.4 Configuración de WildFly (standalone.xml snippet)

```xml
<datasources>
    <datasource jndi-name="java:jboss/datasources/CapacitacionDS"
        pool-name="CapacitacionDS">
        <connection-url>
            jdbc:postgresql://localhost:5432/emelnorte_capacitacion
        </connection-url>
        <driver>postgresql</driver>
        <security>
            <user-name>postgres</user-name>
            <password>postgres</password>
        </security>
    </datasource>
</datasources>
```

---

## 6. PLAN DE DESARROLLO DEL PROTOTIPO

### 6.1 Fases de Desarrollo

| Fase | Descripción | Duración Estimada | Entregable |
|------|-------------|-------------------|------------|
| 1 | Configuración del proyecto y base de datos | 1 día | Proyecto base con entidades |
| 2 | Login simulado y navegación | 0.5 día | Selector de usuarios funcional |
| 3 | CRUD de Planes de Capacitación | 1 día | Crear y listar planes |
| 4 | Registro de Necesidades (Directores) | 1 día | Formulario de registro de temas |
| 5 | Gestión de Temas (Analista) | 1.5 días | Selección y presupuestación |
| 6 | Flujo de Aprobación | 1 día | Revisión porroles |
| 7 | Ejecución de Capacitaciones | 1 día | Registro de ejecución |
| 8 | Participantes y Certificados | 1 día | Gestión de participantes |
| 9 | Pruebas y Ajustes | 1 día | Prototipo funcional |
| **Total** | | **9 días** | **Prototipo Completo** |

### 6.2 Priorización de Pantallas

Para el prototipo, se sugiere desarrollar en este orden:

1. **Sprint 1**: Proyecto base + Login + Dashboard
2. **Sprint 2**: CRUD Planes + Registro Necesidades
3. **Sprint 3**: Gestión de Temas + Flujo Aprobación
4. **Sprint 4**: Ejecución + Participantes + Polish

---

## 7. NOTAS IMPORTANTES

### 7.1 Simplificaciones del Prototipo

1. **Autenticación**: Login simulado con selector de usuario, sin seguridad real
2. **Notificaciones**: No se implementan envíos de correo
3. **Reportes**: No se generan reportes en esta fase
4. **Validación de archivos**: Básica, sinescaneo de malware
5. **Responsive**: Optimizado para escritorio, no mobile
6. **Multiusuario simultáneo**: No probado intensamente

### 7.2 Preparación para Producción (Post-Prototipo)

1. Integrar con sistema de autenticación de EMELNORTE (SSO/LDAP)
2. Implementar notificaciones por correo electrónico
3. Agregar validaciones de seguridad (inyección SQL, XSS)
4. Implementar logs de auditoría
5. Crear reportes formales
6. Optimizar consultas para grandes volúmenes de datos
7. Implementar backup automático de la base de datos

---

## 8. DOCUMENTOS RELACIONADOS

| Documento | Descripción |
|----------|-------------|
| Acta de Reunión BL-01 | Levantamiento de requerimientos |
| Especificación Técnica | Este documento |
| Manual de Usuario | Guía de uso del prototipo |
| Script SQL | DDL de la base de datos |

---

**Versión**: 1.0
**Fecha de creación**: Mayo 2026
**Autor**: MiniMax Agent
**Estado**: Para revisión

---

*Este documento sirve como especificación técnica para el desarrollo del prototipo del Módulo de Gestión de Capacitación de EMELNORTE. Cualquier cambio en el alcance o funcionalidades debe ser documentado como una nueva versión de este documento.*
