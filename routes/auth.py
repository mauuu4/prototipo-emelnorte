"""
EMELNORTE - SIGEERN
Rutas de Autenticación (Simulada)
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import Usuario
from config import db

auth_bp = Blueprint('auth', __name__)


def get_usuario_actual():
    """Obtiene el usuario actual de la sesión"""
    if 'usuario_id' in session:
        return Usuario.query.get(session['usuario_id'])
    return None


def login_required(f):
    """Decorador para requerir autenticación"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debe iniciar sesión para acceder.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def rol_required(*roles):
    """Decorador para requerir un rol específico"""
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            usuario = get_usuario_actual()
            if not usuario:
                flash('Debe iniciar sesión.', 'warning')
                return redirect(url_for('auth.login'))
            if usuario.rol not in roles:
                flash('No tiene permisos para acceder a esta sección.', 'danger')
                return redirect(url_for('auth.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@auth_bp.route('/')
def index():
    """Página de inicio - redirige a login o dashboard"""
    if 'usuario_id' in session:
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de Login Simulado"""
    if request.method == 'POST':
        usuario_id = request.form.get('usuario_id')

        if usuario_id:
            usuario = Usuario.query.get(int(usuario_id))
            if usuario:
                session['usuario_id'] = usuario.id
                session['usuario_nombre'] = usuario.nombre
                session['usuario_rol'] = usuario.rol
                session['usuario_direccion_id'] = usuario.direccion_id
                flash(f'Bienvenido, {usuario.nombre} ({usuario.rol})', 'success')
                return redirect(url_for('auth.dashboard'))

        flash('Seleccione un usuario válido.', 'danger')

    # Obtener usuarios activos para el selector
    usuarios = Usuario.query.filter_by(estado='ACTIVO').all()
    return render_template('auth/login.html', usuarios=usuarios)


@auth_bp.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal"""
    from models import PlanCapacitacion, CapacitacionEjecutada
    from sqlalchemy import func

    usuario = get_usuario_actual()

    # Estadísticas según el rol
    if usuario.es_analista():
        planes_borrador = PlanCapacitacion.query.filter_by(estado='BORRADOR').count()
        planes_revision = PlanCapacitacion.query.filter_by(estado='EN_REVISION').count()
        planes_aprobados = PlanCapacitacion.query.filter_by(estado='APROBADO').count()
        ejecuciones = CapacitacionEjecutada.query.count()
    elif usuario.es_director():
        from models import TemaCapacitacion
        mis_temas = TemaCapacitacion.query.filter_by(usuario_id=usuario.id, estado='ACTIVO').count()
        planes_revision = PlanCapacitacion.query.filter_by(estado='EN_APROBACION').count()
        planes_borrador = 0
        planes_aprobados = 0
        ejecuciones = 0
    elif usuario.es_jefe_personal():
        planes_revision = PlanCapacitacion.query.filter_by(estado='EN_REVISION').count()
        planes_borrador = 0
        planes_aprobados = 0
        ejecuciones = 0
    elif usuario.es_presidente():
        planes_aprobacion = PlanCapacitacion.query.filter_by(estado='EN_APROBACION').count()
        planes_revision = 0
        planes_borrador = 0
        planes_aprobados = 0
        ejecuciones = 0
    else:
        planes_borrador = planes_revision = planes_aprobados = ejecuciones = 0

    return render_template('auth/dashboard.html',
                           usuario=usuario,
                           planes_borrador=planes_borrador,
                           planes_revision=planes_revision,
                           planes_aprobados=planes_aprobados,
                           ejecuciones=ejecuciones if usuario.es_analista() else 0,
                           planes_aprobacion=planes_aprobacion if usuario.es_presidente() else 0,
                           mis_temas=mis_temas if usuario.es_director() else 0)


@auth_bp.route('/cambiar-usuario')
@login_required
def cambiar_usuario():
    """Permite cambiar el usuario simulado"""
    session.clear()
    return redirect(url_for('auth.login'))