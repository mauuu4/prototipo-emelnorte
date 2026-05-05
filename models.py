"""
EMELNORTE - SIGEERN
Módulo de Gestión de Capacitación
Modelos de base de datos (SQLAlchemy)
"""

from datetime import datetime
from config import db
import enum

# ============================================================
# ENUMS
# ============================================================

class EstadoPlan(enum.Enum):
    BORRADOR = "BORRADOR"
    EN_REVISION = "EN_REVISION"
    EN_CORRECCION = "EN_CORRECCION"
    EN_APROBACION = "EN_APROBACION"
    APROBADO = "APROBADO"

class Modalidad(enum.Enum):
    VIRTUAL = "VIRTUAL"
    PRESENCIAL = "PRESENCIAL"
    MIXTO = "MIXTO"

class RolUsuario(enum.Enum):
    ANALISTA = "ANALISTA"
    DIRECTOR = "DIRECTOR"
    JEFE_PERSONAL = "JEFE_PERSONAL"
    PRESIDENTE = "PRESIDENTE"

class TipoObservacion(enum.Enum):
    APROBACION = "APROBACION"
    DEVOLUCION = "DEVOLUCION"
    OBSERVACION = "OBSERVACION"

# ============================================================
# MODELOS
# ============================================================

class Direccion(db.Model):
    """Modelo para Direcciones de EMELNORTE"""
    __tablename__ = 'direcciones'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    abreviatura = db.Column(db.String(20), nullable=False, unique=True)
    max_temas = db.Column(db.Integer, nullable=False, default=5)
    estado = db.Column(db.String(20), nullable=False, default='ACTIVO')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    usuarios = db.relationship('Usuario', backref='direccion', lazy='dynamic')

    def __repr__(self):
        return f'<Direccion {self.nombre}>'


class Usuario(db.Model):
    """Modelo para Usuarios del sistema"""
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    cedula = db.Column(db.String(10), nullable=False, unique=True)
    correo = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.String(30), nullable=False)  # ANALISTA, DIRECTOR, JEFE_PERSONAL, PRESIDENTE
    direccion_id = db.Column(db.Integer, db.ForeignKey('direcciones.id'), nullable=True)
    estado = db.Column(db.String(20), nullable=False, default='ACTIVO')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    temas = db.relationship('TemaCapacitacion', backref='usuario', lazy='dynamic')

    def __repr__(self):
        return f'<Usuario {self.nombre}>'

    def es_analista(self):
        return self.rol == 'ANALISTA'

    def es_director(self):
        return self.rol == 'DIRECTOR'

    def es_director_th(self):
        """Director de Talento Humano (revisor antes del presidente)"""
        return self.rol == 'DIRECTOR' and self.direccion_id == 6

    def es_director_area(self):
        """Director de area (registra necesidades de capacitacion)"""
        return self.rol == 'DIRECTOR' and self.direccion_id != 6

    def es_jefe_personal(self):
        return self.rol == 'JEFE_PERSONAL'

    def es_presidente(self):
        return self.rol == 'PRESIDENTE'


class PlanCapacitacion(db.Model):
    """Modelo para Planes de Capacitación - UN SOLO PLAN POR AÑO (global)"""
    __tablename__ = 'planes_capacitacion'

    id = db.Column(db.Integer, primary_key=True)
    anio = db.Column(db.Integer, nullable=False, unique=True)
    monto_referencial = db.Column(db.Float, nullable=False)
    monto_aprobado = db.Column(db.Float, nullable=True)
    estado = db.Column(db.String(30), nullable=False, default='BORRADOR')
    creado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_envio_jefe = db.Column(db.DateTime, nullable=True)
    fecha_envio_director = db.Column(db.DateTime, nullable=True)
    fecha_aprobacion = db.Column(db.DateTime, nullable=True)

    # Relaciones
    creado_por = db.relationship('Usuario', backref='planes_creados')
    temas = db.relationship('TemaCapacitacion', backref='plan', lazy='dynamic', cascade='all, delete-orphan')
    temas_seleccionados = db.relationship('TemaSeleccionado', backref='plan', lazy='dynamic', cascade='all, delete-orphan')
    observaciones_list = db.relationship('ObservacionPlan', backref='plan', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<PlanCapacitacion {self.anio}>'

    def get_temas_count(self):
        """Cuenta los temas activos del plan"""
        return self.temas.filter(TemaCapacitacion.estado == 'ACTIVO').count()

    def get_temas_seleccionados_count(self):
        """Cuenta los temas seleccionados"""
        return TemaSeleccionado.query.filter_by(plan_id=self.id, seleccionado=True).count()

    def get_total_seleccionado(self):
        """Calcula el total del presupuesto de temas seleccionados"""
        total = 0
        for ts in self.temas_seleccionados.filter_by(seleccionado=True):
            if ts.presupuesto_aprobado:
                total += ts.presupuesto_aprobado
        return total

    def supera_presupuesto(self):
        """Verifica si el total seleccionado supera el presupuesto referencial"""
        if not self.monto_referencial:
            return False
        return self.get_total_seleccionado() > self.monto_referencial

    def get_temas_por_direccion(self):
        """Agrupa temas activos por dirección"""
        from collections import defaultdict
        temas_por_dir = defaultdict(list)
        for tema in self.temas.filter(TemaCapacitacion.estado == 'ACTIVO'):
            if tema.usuario and tema.usuario.direccion:
                temas_por_dir[tema.usuario.direccion].append(tema)
        return dict(temas_por_dir)

    def is_editable(self):
        """El plan solo es editable en estados BORRADOR o EN_CORRECCION"""
        return self.estado in ['BORRADOR', 'EN_CORRECCION']

    def is_blocked(self):
        """El plan está bloqueado si está APROBADO"""
        return self.estado == 'APROBADO'


class TemaCapacitacion(db.Model):
    """Modelo para Temas/Necesidades de Capacitación"""
    __tablename__ = 'temas_capacitacion'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    etapa_funcional = db.Column(db.String(100), nullable=False)
    subetapa_funcional = db.Column(db.String(100), nullable=False)
    num_participantes = db.Column(db.Integer, nullable=False)
    modalidad = db.Column(db.String(20), nullable=False)  # VIRTUAL, PRESENCIAL, MIXTO
    horas = db.Column(db.Float, nullable=False)
    presupuesto_referencial = db.Column(db.Float, nullable=False)
    mes_ejecucion = db.Column(db.Integer, nullable=False)  # 1-12
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('planes_capacitacion.id'), nullable=False)
    es_del_analista = db.Column(db.Boolean, default=False)  # True si fue agregado por el Analista
    estado = db.Column(db.String(20), nullable=False, default='ACTIVO')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    tema_seleccionado = db.relationship('TemaSeleccionado', backref='tema', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<TemaCapacitacion {self.nombre}>'

    def get_nombre_mes(self):
        """Retorna el nombre del mes"""
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        return meses[self.mes_ejecucion] if 1 <= self.mes_ejecucion <= 12 else ''

    def get_direccion_nombre(self):
        """Retorna nombre de la dirección del usuario que registró el tema"""
        if self.usuario and self.usuario.direccion:
            return self.usuario.direccion.nombre
        return 'Sin Dirección'


class TemaSeleccionado(db.Model):
    """Modelo para la selección y presupuesto aprobado de temas"""
    __tablename__ = 'temas_seleccionados'

    id = db.Column(db.Integer, primary_key=True)
    tema_id = db.Column(db.Integer, db.ForeignKey('temas_capacitacion.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('planes_capacitacion.id'), nullable=False)
    seleccionado = db.Column(db.Boolean, default=False)
    presupuesto_aprobado = db.Column(db.Float, nullable=True)
    observaciones = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<TemaSeleccionado tema={self.tema_id} seleccionado={self.seleccionado}>'


class ObservacionPlan(db.Model):
    """Modelo para Observaciones de un plan"""
    __tablename__ = 'observaciones_plan'

    id = db.Column(db.Integer, primary_key=True)
    observacion = db.Column(db.Text, nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    tipo_observacion = db.Column(db.String(30), nullable=False)  # APROBACION, DEVOLUCION, OBSERVACION
    plan_id = db.Column(db.Integer, db.ForeignKey('planes_capacitacion.id'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ObservacionPlan {self.tipo_observacion} por {self.autor}>'


class Empleado(db.Model):
    """Modelo para Empleados de EMELNORTE (nómina para búsqueda en participantes)"""
    __tablename__ = 'empleados'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False, unique=True)
    nombres = db.Column(db.String(150), nullable=False)
    cedula = db.Column(db.String(15), nullable=False, unique=True)
    cargo = db.Column(db.String(150), nullable=True)
    direccion = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(20), nullable=False, default='ACTIVO')

    def __repr__(self):
        return f'<Empleado {self.codigo} - {self.nombres}>'

    def to_dict(self):
        return {
            'codigo': self.codigo,
            'nombres': self.nombres,
            'cedula': self.cedula,
            'cargo': self.cargo or '',
            'direccion': self.direccion or ''
        }


class CapacitacionEjecutada(db.Model):
    """Modelo para Capacitaciones Ejecutadas (Etapa de Ejecución)"""
    __tablename__ = 'capacitaciones_ejecutadas'

    id = db.Column(db.Integer, primary_key=True)
    tema_seleccionado_id = db.Column(db.Integer, db.ForeignKey('temas_seleccionados.id'), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    duracion_horas = db.Column(db.Float, nullable=False)
    valor_sin_iva = db.Column(db.Float, nullable=False)
    valor_con_iva = db.Column(db.Float, nullable=False)
    proceso_contratacion = db.Column(db.String(100), nullable=True)
    centro_costo = db.Column(db.String(100), nullable=True)
    etapa_funcional = db.Column(db.String(100), nullable=True)
    subetapa_funcional = db.Column(db.String(100), nullable=True)
    empresa_capacitadora = db.Column(db.String(200), nullable=True)
    tipo_certificacion = db.Column(db.String(100), nullable=True)
    observaciones = db.Column(db.Text, nullable=True)
    estado = db.Column(db.String(20), nullable=False, default='ACTIVO')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    tema_seleccionado = db.relationship('TemaSeleccionado', backref='capacitacion_ejecutada')
    participantes = db.relationship('Participante', backref='capacitacion', lazy='dynamic',
                                    cascade='all, delete-orphan')

    def __repr__(self):
        return f'<CapacitacionEjecutada id={self.id}>'

    def get_participantes_activos(self):
        return self.participantes.filter_by(estado='ACTIVO').all()

    def get_nombre_tema(self):
        if self.tema_seleccionado and self.tema_seleccionado.tema:
            return self.tema_seleccionado.tema.nombre
        return 'Sin tema'


class Participante(db.Model):
    """Modelo para Participantes de una Capacitación Ejecutada"""
    __tablename__ = 'participantes'

    id = db.Column(db.Integer, primary_key=True)
    capacitacion_id = db.Column(db.Integer, db.ForeignKey('capacitaciones_ejecutadas.id'), nullable=False)
    codigo = db.Column(db.String(20), nullable=False)
    nombres = db.Column(db.String(150), nullable=False)
    cedula = db.Column(db.String(15), nullable=False)
    cargo = db.Column(db.String(150), nullable=True)
    ruta_certificado = db.Column(db.String(300), nullable=True)
    estado = db.Column(db.String(20), nullable=False, default='ACTIVO')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Participante {self.nombres}>'