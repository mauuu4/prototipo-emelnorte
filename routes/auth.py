"""
EMELNORTE - SIGEERN
Rutas de Autenticación (Simulada)
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import Usuario, PlanCapacitacion, Participante, EvaluacionCapacitacion
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
                session['es_director_th'] = (usuario.rol == 'DIRECTOR' and usuario.direccion_id == 6)
                flash(f'Bienvenido, {usuario.nombre}', 'success')
                return redirect(url_for('auth.dashboard'))
        flash('Seleccione un usuario válido.', 'danger')

    usuarios = Usuario.query.filter_by(estado='ACTIVO').order_by(Usuario.rol, Usuario.nombre).all()
    return render_template('auth/login.html', usuarios=usuarios)


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal - cada rol ve solo su información"""
    usuario = get_usuario_actual()
    
    if usuario.es_empleado():
        return redirect(url_for('empleado.perfil'))

    stats = {}

    if usuario.es_analista():
        # RN-01, RN-04, RN-05, RN-06
        plan_activo = PlanCapacitacion.query.order_by(PlanCapacitacion.anio.desc()).first()
        stats['plan_activo'] = plan_activo
        stats['total_planes'] = PlanCapacitacion.query.count()
        stats['planes_borrador'] = PlanCapacitacion.query.filter_by(estado='BORRADOR').count()
        stats['planes_revision'] = PlanCapacitacion.query.filter_by(estado='EN_REVISION').count()
        stats['planes_aprobados'] = PlanCapacitacion.query.filter_by(estado='APROBADO').count()

    elif usuario.es_director_th():
        # RN-08: Director TH recibe plan del Jefe y lo envía al Presidente
        stats['planes_pendientes'] = PlanCapacitacion.query.filter_by(estado='EN_APROBACION').count()
        stats['planes_aprobados'] = PlanCapacitacion.query.filter_by(estado='APROBADO').count()

    elif usuario.es_director_area():
        # RN-02, RN-03: Director de área registra necesidades
        from models import TemaCapacitacion
        from datetime import datetime
        plan_vigente = PlanCapacitacion.query.filter_by(anio=datetime.now().year).first()
        stats['plan_vigente'] = plan_vigente
        if plan_vigente:
            stats['mis_temas'] = TemaCapacitacion.query.filter_by(
                usuario_id=usuario.id, plan_id=plan_vigente.id, estado='ACTIVO'
            ).count()
            stats['max_temas'] = usuario.direccion.max_temas if usuario.direccion else 5
            stats['temas_restantes'] = stats['max_temas'] - stats['mis_temas']

    elif usuario.es_jefe_personal():
        # RN-07: Jefe revisa, aprueba o devuelve
        stats['planes_en_revision'] = PlanCapacitacion.query.filter_by(estado='EN_REVISION').count()
        stats['planes_devueltos'] = PlanCapacitacion.query.filter_by(estado='EN_CORRECCION').count()

    elif usuario.es_presidente():
        # RN-09: Presidente aprueba definitivamente
        stats['planes_pendientes'] = PlanCapacitacion.query.filter_by(estado='EN_APROBACION').count()
        stats['planes_aprobados'] = PlanCapacitacion.query.filter_by(estado='APROBADO').count()

    # Verificar evaluaciones pendientes para el usuario (si es empleado / participante)
    participaciones = Participante.query.filter_by(cedula=usuario.cedula, estado='ACTIVO').all()
    evaluaciones_pendientes = []
    for p in participaciones:
        if p.capacitacion and p.capacitacion.estado == 'FINALIZADO' or p.capacitacion.estado == 'ACTIVO':
            evaluacion = EvaluacionCapacitacion.query.filter_by(participante_id=p.id, capacitacion_id=p.capacitacion_id).first()
            if not evaluacion:
                evaluaciones_pendientes.append(p)
    
    stats['evaluaciones_pendientes'] = evaluaciones_pendientes

    return render_template('auth/dashboard.html', usuario=usuario, stats=stats)


@auth_bp.route('/guardar-evaluacion', methods=['POST'])
@login_required
def guardar_evaluacion():
    participante_id = request.form.get('participante_id')
    capacitacion_id = request.form.get('capacitacion_id')
    calificacion_curso = request.form.get('calificacion_curso')
    calificacion_empresa = request.form.get('calificacion_empresa')
    comentarios = request.form.get('comentarios')

    if not participante_id or not capacitacion_id or not calificacion_curso or not calificacion_empresa:
        flash('Por favor complete todos los campos de la evaluación.', 'danger')
        return redirect(url_for('auth.dashboard'))

    nueva_eval = EvaluacionCapacitacion(
        participante_id=participante_id,
        capacitacion_id=capacitacion_id,
        calificacion_curso=int(calificacion_curso),
        calificacion_empresa=int(calificacion_empresa),
        comentarios=comentarios
    )
    db.session.add(nueva_eval)
    db.session.commit()
    
    flash('¡Gracias por evaluar la capacitación! Su retroalimentación es muy valiosa.', 'success')
    return redirect(url_for('auth.dashboard'))


@auth_bp.route('/cambiar-usuario')
@login_required
def cambiar_usuario():
    session.clear()
    return redirect(url_for('auth.login'))