"""
EMELNORTE - SIGEERN
Rutas de Necesidades de Capacitación (Directores)
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import PlanCapacitacion, TemaCapacitacion, TemaSeleccionado, Direccion
from routes.auth import login_required, get_usuario_actual, rol_required
from config import db
from datetime import datetime

necesidades_bp = Blueprint('necesidades', __name__, url_prefix='/necesidades')


@necesidades_bp.route('/')
@rol_required('ANALISTA', 'DIRECTOR')
def lista():
    """Lista de necesidades registradas"""
    usuario = get_usuario_actual()

    # Obtener plan vigente
    anio_actual = datetime.now().year
    plan = PlanCapacitacion.query.filter_by(anio=anio_actual).first()

    if not plan:
        flash('No existe un plan de capacitación para el año vigente. Contacte al Analista.', 'warning')
        return redirect(url_for('auth.dashboard'))

    if usuario.es_director():
        # Director ve solo sus temas
        temas = TemaCapacitacion.query.filter_by(
            usuario_id=usuario.id,
            plan_id=plan.id,
            estado='ACTIVO'
        ).all()

        # Verificar límite de temas
        max_temas = usuario.direccion.max_temas if usuario.direccion else 5
        puede_agregar = len(temas) < max_temas
    else:
        # Analista ve todos los temas
        temas = plan.temas.filter(TemaCapacitacion.estado == 'ACTIVO').all()
        puede_agregar = False  # El analista agrega desde el detalle del plan

    return render_template('necesidades/lista.html',
                           temas=temas,
                           plan=plan,
                           puede_agregar=puede_agregar,
                           usuario=usuario)


@necesidades_bp.route('/nuevo', methods=['GET', 'POST'])
@rol_required('DIRECTOR')
def nuevo():
    """Registrar una nueva necesidad de capacitación"""
    usuario = get_usuario_actual()

    # Verificar que existe plan vigente
    anio_actual = datetime.now().year
    plan = PlanCapacitacion.query.filter_by(anio=anio_actual).first()

    if not plan:
        flash('No existe un plan de capacitación para el año vigente.', 'warning')
        return redirect(url_for('necesidades.lista'))

    # Verificar que el plan está en estado válido para agregar temas
    if plan.estado not in ['BORRADOR', 'EN_CORRECCION']:
        flash('El plan de capacitación no acepta nuevos temas en este momento.', 'warning')
        return redirect(url_for('necesidades.lista'))

    # Verificar límite de temas
    temas_actuales = TemaCapacitacion.query.filter_by(
        usuario_id=usuario.id,
        plan_id=plan.id,
        estado='ACTIVO'
    ).count()

    max_temas = usuario.direccion.max_temas if usuario.direccion else 5

    if temas_actuales >= max_temas:
        flash(f'Ha alcanzado el límite de {max_temas} temas para su dirección.', 'warning')
        return redirect(url_for('necesidades.lista'))

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        etapa_funcional = request.form.get('etapa_funcional')
        subetapa_funcional = request.form.get('subetapa_funcional')
        num_participantes = request.form.get('num_participantes', type=int)
        modalidad = request.form.get('modalidad')
        horas = request.form.get('horas', type=float)
        presupuesto_referencial = request.form.get('presupuesto_referencial', type=float)
        mes_ejecucion = request.form.get('mes_ejecucion', type=int)

        # Crear tema
        tema = TemaCapacitacion(
            nombre=nombre,
            etapa_funcional=etapa_funcional,
            subetapa_funcional=subetapa_funcional,
            num_participantes=num_participantes,
            modalidad=modalidad,
            horas=horas,
            presupuesto_referencial=presupuesto_referencial,
            mes_ejecucion=mes_ejecucion,
            usuario_id=usuario.id,
            plan_id=plan.id,
            estado='ACTIVO'
        )
        db.session.add(tema)
        db.session.flush()

        # Crear registro de selección (no seleccionado por defecto)
        tema_seleccionado = TemaSeleccionado(
            tema_id=tema.id,
            plan_id=plan.id,
            seleccionado=False
        )
        db.session.add(tema_seleccionado)
        db.session.commit()

        flash('Necesidad de capacitación registrada exitosamente.', 'success')
        return redirect(url_for('necesidades.lista'))

    return render_template('necesidades/nuevo.html',
                           plan=plan,
                           max_temas=max_temas,
                           temas_restantes=max_temas - temas_actuales - 1)


@necesidades_bp.route('/<int:tema_id>/editar', methods=['GET', 'POST'])
@rol_required('DIRECTOR')
def editar(tema_id):
    """Editar una necesidad registrada"""
    tema = TemaCapacitacion.query.get_or_404(tema_id)
    usuario = get_usuario_actual()

    # Verificar que el tema pertenece al usuario
    if tema.usuario_id != usuario.id:
        flash('No tiene permisos para editar este tema.', 'danger')
        return redirect(url_for('necesidades.lista'))

    # Verificar que el plan está en estado válido
    if tema.plan.estado not in ['BORRADOR', 'EN_CORRECCION']:
        flash('No se puede editar el tema en este estado del plan.', 'warning')
        return redirect(url_for('necesidades.lista'))

    if request.method == 'POST':
        tema.nombre = request.form.get('nombre')
        tema.etapa_funcional = request.form.get('etapa_funcional')
        tema.subetapa_funcional = request.form.get('subetapa_funcional')
        tema.num_participantes = request.form.get('num_participantes', type=int)
        tema.modalidad = request.form.get('modalidad')
        tema.horas = request.form.get('horas', type=float)
        tema.presupuesto_referencial = request.form.get('presupuesto_referencial', type=float)
        tema.mes_ejecucion = request.form.get('mes_ejecucion', type=int)

        db.session.commit()
        flash('Necesidad actualizada exitosamente.', 'success')
        return redirect(url_for('necesidades.lista'))

    return render_template('necesidades/editar.html', tema=tema)


@necesidades_bp.route('/<int:tema_id>/eliminar', methods=['POST'])
@rol_required('DIRECTOR')
def eliminar(tema_id):
    """Eliminar una necesidad (marcar como inactiva)"""
    tema = TemaCapacitacion.query.get_or_404(tema_id)
    usuario = get_usuario_actual()

    if tema.usuario_id != usuario.id:
        flash('No tiene permisos para eliminar este tema.', 'danger')
        return redirect(url_for('necesidades.lista'))

    if tema.plan.estado not in ['BORRADOR', 'EN_CORRECCION']:
        flash('No se puede eliminar el tema en este estado del plan.', 'warning')
        return redirect(url_for('necesidades.lista'))

    tema.estado = 'ELIMINADO'
    db.session.commit()

    flash('Necesidad eliminada.', 'success')
    return redirect(url_for('necesidades.lista'))