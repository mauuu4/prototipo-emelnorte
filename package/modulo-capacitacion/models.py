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

    def puede_agregar_tema(self, plan_id):
        """Verifica si la dirección puede agregar más temas a un plan"""
        from models import TemaCapacitacion
        temas_actuales = TemaCapacitacion.query.filter_by(
            usuario_id=None  # Se filtrará por dirección del usuario
        ).join(Usuario).filter(
            Usuario.direccion_id == self.id,
            TemaCapacitacion.plan_id == plan_id,
            TemaCapacitacion.estado == 'ACTIVO'
        ).count()
        return temas_actuales < self.max_temas


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

    def es_jefe_personal(self):
        return self.rol == 'JEFE_PERSONAL'

    def es_presidente(self):
        return self.rol == 'PRESIDENTE'


class PlanCapacitacion(db.Model):
    """Modelo para Planes de Capacitación"""
    __tablename__ = 'planes_capacitacion'

    id = db.Column(db.Integer, primary_key=True)
    anio = db.Column(db.Integer, nullable=False)
    monto_referencial = db.Column(db.Float, nullable=False)
    monto_aprobado = db.Column(db.Float, nullable=True)
    estado = db.Column(db.String(30), nullable=False, default='BORRADOR')
    observaciones = db.Column(db.Text, nullable=True)
    direccion_id = db.Column(db.Integer, db.ForeignKey('direcciones.id'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_envio_jefe = db.Column(db.DateTime, nullable=True)
    fecha_envio_director = db.Column(db.DateTime, nullable=True)
    fecha_aprobacion = db.Column(db.DateTime, nullable=True)

    # Relaciones
    direccion = db.relationship('Direccion', backref=db.backref('planes', lazy='dynamic'))
    temas = db.relationship('TemaCapacitacion', backref='plan', lazy='dynamic', cascade='all, delete-orphan')
    temas_seleccionados = db.relationship('TemaSeleccionado', backref='plan', lazy='dynamic', cascade='all, delete-orphan')
    observaciones_list = db.relationship('ObservacionPlan', backref='plan', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<PlanCapacitacion {self.anio}>'

    def get_temas_count(self):
        """Cuenta los temas activos del plan"""
        return self.temas.filter(TemaCapacitacion.estado == 'ACTIVO').count()

    def get_total_seleccionado(self):
        """Calcula el total del presupuesto de temas seleccionados"""
        total = 0
        for ts in self.temas_seleccionados:
            if ts.seleccionado and ts.presupuesto_aprobado:
                total += ts.presupuesto_aprobado
        return total

    def supera_presupuesto(self):
        """Verifica si el total seleccionado supera el presupuesto referencial"""
        return self.get_total_seleccionado() > self.monto_referencial

    def get_temas_por_direccion(self):
        """Agrupa temas por dirección"""
        from collections import defaultdict
        temas_por_dir = defaultdict(list)

        for tema in self.temas.filter(TemaCapacitacion.estado == 'ACTIVO'):
            if tema.usuario and tema.usuario.direccion:
                temas_por_dir[tema.usuario.direccion].append(tema)

        return dict(temas_por_dir)


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


class CapacitacionEjecutada(db.Model):
    """Modelo para Capacitaciones Ejecutadas"""
    __tablename__ = 'capacitaciones_ejecutadas'

    id = db.Column(db.Integer, primary_key=True)
    tema_seleccionado_id = db.Column(db.Integer, db.ForeignKey('temas_seleccionados.id'), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    duracion_horas = db.Column(db.Float, nullable=False)
    valor_sin_iva = db.Column(db.Float, nullable=False)
    valor_con_iva = db.Column(db.Float, nullable=False)
    proceso_contratacion = db.Column(db.String(100), nullable=False)
    centro_costo = db.Column(db.String(50), nullable=False)
    etapa_funcional = db.Column(db.String(100), nullable=False)
    subetapa_funcional = db.Column(db.String(100), nullable=False)
    empresa_capacitadora = db.Column(db.String(200), nullable=False)
    tipo_certificacion = db.Column(db.String(50), nullable=False)
    observaciones = db.Column(db.Text, nullable=True)
    estado = db.Column(db.String(20), nullable=False, default='ACTIVO')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    tema_seleccionado = db.relationship('TemaSeleccionado', backref='capacitaciones')
    participantes = db.relationship('Participante', backref='capacitacion', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<CapacitacionEjecutada {self.id}>'

    def get_total_participantes(self):
        """Cuenta los participantes activos"""
        return self.participantes.filter(Participante.estado == 'ACTIVO').count()


class Participante(db.Model):
    """Modelo para Participantes de una capacitación"""
    __tablename__ = 'participantes'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    cedula = db.Column(db.String(10), nullable=False)
    cargo = db.Column(db.String(100), nullable=False)
    ruta_certificado = db.Column(db.String(500), nullable=True)
    capacitacion_id = db.Column(db.Integer, db.ForeignKey('capacitaciones_ejecutadas.id'), nullable=False)
    estado = db.Column(db.String(20), nullable=False, default='ACTIVO')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Participante {self.nombres}>'


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


# Importar después de definir las clases para evitar importación circular
from models import Usuario, TemaCapacitacion, Participante