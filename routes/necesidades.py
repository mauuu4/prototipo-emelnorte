"""
EMELNORTE - SIGEERN
Rutas de Necesidades de Capacitación - Solo para DIRECTOR de área (RN-02, RN-03)
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import PlanCapacitacion, TemaCapacitacion, TemaSeleccionado, Direccion, EnvioTemasDirector
from routes.auth import login_required, get_usuario_actual, rol_required
from config import db
from datetime import datetime

necesidades_bp = Blueprint('necesidades', __name__, url_prefix='/necesidades')



MESES = [
    (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
    (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
    (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
]


def get_plan_vigente():
    """Obtiene el plan del año actual"""
    anio_actual = datetime.now().year
    return PlanCapacitacion.query.filter_by(anio=anio_actual).first()


@necesidades_bp.route('/')
@rol_required('DIRECTOR')
def lista():
    """RN-02, RN-03: Lista de necesidades del director de área"""
    usuario = get_usuario_actual()

    plan = get_plan_vigente()
    if not plan:
        flash('No existe un Plan de Capacitación para el año vigente. Espere la notificación del Analista de Talento Humano.', 'warning')
        return redirect(url_for('auth.dashboard'))

    # Solo puede agregar si el plan está en BORRADOR
    puede_agregar_estado = plan.estado == 'BORRADOR'

    temas = TemaCapacitacion.query.filter_by(
        usuario_id=usuario.id,
        plan_id=plan.id,
        estado='ACTIVO'
    ).order_by(TemaCapacitacion.fecha_creacion).all()

    max_temas = usuario.direccion.max_temas if usuario.direccion else 5
    
    envio = EnvioTemasDirector.query.filter_by(plan_id=plan.id, usuario_id=usuario.id).first()
    temas_enviados = envio is not None
    
    puede_agregar = puede_agregar_estado and len(temas) < max_temas and not temas_enviados

    return render_template('necesidades/lista.html',
                           temas=temas,
                           plan=plan,
                           puede_agregar=puede_agregar,
                           puede_agregar_estado=puede_agregar_estado,
                           max_temas=max_temas,
                           temas_enviados=temas_enviados,
                           usuario=usuario,
                           meses=MESES)


@necesidades_bp.route('/nuevo', methods=['POST'])
@rol_required('DIRECTOR')
def nuevo():
    """RN-02: Registrar una nueva necesidad de capacitación (desde modal)"""
    usuario = get_usuario_actual()

    plan = get_plan_vigente()
    if not plan:
        flash('No existe un plan vigente.', 'warning')
        return redirect(url_for('necesidades.lista'))

    if plan.estado != 'BORRADOR':
        flash('El plan de capacitación ya no acepta nuevas necesidades.', 'warning')
        return redirect(url_for('necesidades.lista'))
        
    envio = EnvioTemasDirector.query.filter_by(plan_id=plan.id, usuario_id=usuario.id).first()
    if envio:
        flash('Ya ha enviado sus temas para este plan. No puede agregar más.', 'warning')
        return redirect(url_for('necesidades.lista'))

    # RN-03: Verificar límite de temas
    temas_actuales = TemaCapacitacion.query.filter_by(
        usuario_id=usuario.id, plan_id=plan.id, estado='ACTIVO'
    ).count()
    max_temas = usuario.direccion.max_temas if usuario.direccion else 5

    if temas_actuales >= max_temas:
        flash(f'Ha alcanzado el límite de {max_temas} temas para su dirección.', 'warning')
        return redirect(url_for('necesidades.lista'))

    nombre = request.form.get('nombre', '').strip()
    num_participantes = request.form.get('num_participantes', type=int)
    modalidad = request.form.get('modalidad')
    horas = request.form.get('horas', type=float)
    presupuesto_referencial = request.form.get('presupuesto_referencial', type=float)
    mes_ejecucion = request.form.get('mes_ejecucion', type=int)

    prioridad = request.form.get('prioridad', default='MEDIA')

    if not all([nombre, num_participantes, modalidad, horas, presupuesto_referencial, mes_ejecucion]):
        flash('Todos los campos son obligatorios.', 'danger')
        return redirect(url_for('necesidades.lista'))

    tema = TemaCapacitacion(
        nombre=nombre,
        num_participantes=num_participantes,
        modalidad=modalidad,
        horas=horas,
        presupuesto_referencial=presupuesto_referencial,
        mes_ejecucion=mes_ejecucion,
        usuario_id=usuario.id,
        plan_id=plan.id,
        es_del_analista=False,
        estado='ACTIVO',
        prioridad=prioridad
    )
    db.session.add(tema)
    db.session.flush()

    ts = TemaSeleccionado(
        tema_id=tema.id,
        plan_id=plan.id,
        seleccionado=False  # El Analista decide si lo selecciona
    )
    db.session.add(ts)
    db.session.commit()

    flash(f'Necesidad "{nombre}" registrada exitosamente.', 'success')
    return redirect(url_for('necesidades.lista'))


@necesidades_bp.route('/<int:tema_id>/editar', methods=['POST'])
@rol_required('DIRECTOR')
def editar(tema_id):
    """Editar una necesidad desde modal"""
    tema = TemaCapacitacion.query.get_or_404(tema_id)
    usuario = get_usuario_actual()

    if tema.usuario_id != usuario.id:
        flash('No tiene permisos para editar este tema.', 'danger')
        return redirect(url_for('necesidades.lista'))

    if tema.plan.estado != 'BORRADOR':
        flash('No se puede editar el tema en este estado del plan.', 'warning')
        return redirect(url_for('necesidades.lista'))
        
    envio = EnvioTemasDirector.query.filter_by(plan_id=tema.plan_id, usuario_id=usuario.id).first()
    if envio:
        flash('Ya ha enviado sus temas para este plan. No puede editar.', 'warning')
        return redirect(url_for('necesidades.lista'))

    tema.nombre = request.form.get('nombre', tema.nombre).strip()
    tema.num_participantes = request.form.get('num_participantes', type=int) or tema.num_participantes
    tema.modalidad = request.form.get('modalidad', tema.modalidad)
    tema.horas = request.form.get('horas', type=float) or tema.horas
    tema.presupuesto_referencial = request.form.get('presupuesto_referencial', type=float) or tema.presupuesto_referencial
    tema.mes_ejecucion = request.form.get('mes_ejecucion', type=int) or tema.mes_ejecucion

    tema.prioridad = request.form.get('prioridad') or tema.prioridad

    db.session.commit()
    flash('Necesidad actualizada exitosamente.', 'success')
    return redirect(url_for('necesidades.lista'))


@necesidades_bp.route('/<int:tema_id>/eliminar', methods=['POST'])
@rol_required('DIRECTOR')
def eliminar(tema_id):
    """Eliminar una necesidad"""
    tema = TemaCapacitacion.query.get_or_404(tema_id)
    usuario = get_usuario_actual()

    if tema.usuario_id != usuario.id:
        flash('No tiene permisos para eliminar este tema.', 'danger')
        return redirect(url_for('necesidades.lista'))

    if tema.plan.estado != 'BORRADOR':
        flash('No se puede eliminar el tema en este estado del plan.', 'warning')
        return redirect(url_for('necesidades.lista'))
        
    envio = EnvioTemasDirector.query.filter_by(plan_id=tema.plan_id, usuario_id=usuario.id).first()
    if envio:
        flash('Ya ha enviado sus temas para este plan. No puede eliminar.', 'warning')
        return redirect(url_for('necesidades.lista'))

    tema.estado = 'ELIMINADO'
    db.session.commit()
    flash('Necesidad eliminada.', 'success')
    return redirect(url_for('necesidades.lista'))


@necesidades_bp.route('/enviar-temas', methods=['POST'])
@rol_required('DIRECTOR')
def enviar_temas():
    """Enviar todos los temas registrados por el director"""
    usuario = get_usuario_actual()
    plan = get_plan_vigente()
    
    if not plan or plan.estado != 'BORRADOR':
        flash('No se pueden enviar los temas en este momento.', 'warning')
        return redirect(url_for('necesidades.lista'))
        
    temas_actuales = TemaCapacitacion.query.filter_by(
        usuario_id=usuario.id, plan_id=plan.id, estado='ACTIVO'
    ).count()
    max_temas = usuario.direccion.max_temas if usuario.direccion else 5
    
    if temas_actuales < max_temas:
        flash(f'Debe registrar el total de {max_temas} temas antes de enviar.', 'warning')
        return redirect(url_for('necesidades.lista'))
        
    envio = EnvioTemasDirector.query.filter_by(plan_id=plan.id, usuario_id=usuario.id).first()
    if envio:
        flash('Ya ha enviado sus temas anteriormente.', 'info')
        return redirect(url_for('necesidades.lista'))
        
    nuevo_envio = EnvioTemasDirector(
        plan_id=plan.id,
        usuario_id=usuario.id
    )
    db.session.add(nuevo_envio)
    db.session.commit()
    
    flash('Temas enviados exitosamente al Analista de Talento Humano.', 'success')
    return redirect(url_for('necesidades.lista'))

