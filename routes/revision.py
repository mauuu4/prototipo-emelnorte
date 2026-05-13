"""
EMELNORTE - SIGEERN
Rutas de Revisión y Aprobación
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import PlanCapacitacion, TemaCapacitacion, TemaSeleccionado, ObservacionPlan
from routes.auth import login_required, get_usuario_actual, rol_required
from config import db

revision_bp = Blueprint('revision', __name__, url_prefix='/revision')


@revision_bp.route('/jefe')
@rol_required('JEFE_PERSONAL')
def lista_jefe():
    """RN-07: Planes en estado EN_REVISION para el Jefe de Personal"""
    planes = PlanCapacitacion.query.filter_by(estado='EN_REVISION').order_by(
        PlanCapacitacion.fecha_envio_jefe.desc()
    ).all()
    return render_template('revision/lista_jefe.html', planes=planes)


@revision_bp.route('/director')
@rol_required('DIRECTOR')
def lista_director():
    """RN-08: Planes en estado EN_APROBACION para el Director de TH"""
    usuario = get_usuario_actual()
    if not usuario.es_director_th():
        flash('Esta sección es solo para el Director de Talento Humano.', 'danger')
        return redirect(url_for('auth.dashboard'))

    planes = PlanCapacitacion.query.filter(
        PlanCapacitacion.estado.in_(['EN_APROBACION', 'APROBADO'])
    ).order_by(PlanCapacitacion.fecha_envio_director.desc()).all()
    return render_template('revision/lista_director.html', planes=planes, usuario=usuario)


@revision_bp.route('/presidente')
@rol_required('PRESIDENTE')
def lista_presidente():
    """RN-09: Planes para aprobación final del Presidente"""
    planes = PlanCapacitacion.query.filter(
        PlanCapacitacion.estado.in_(['EN_APROBACION', 'APROBADO'])
    ).order_by(PlanCapacitacion.fecha_envio_director.desc()).all()
    return render_template('revision/lista_presidente.html', planes=planes)


@revision_bp.route('/<int:plan_id>/ver')
@login_required
def ver_plan(plan_id):
    """Vista del plan según el rol del usuario actual"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)
    usuario = get_usuario_actual()

    # Control de acceso por estado del plan y rol
    if usuario.es_jefe_personal() and plan.estado not in ['EN_REVISION', 'EN_CORRECCION', 'EN_APROBACION', 'APROBADO']:
        flash('No tiene acceso a este plan en su estado actual.', 'warning')
        return redirect(url_for('revision.lista_jefe'))
    elif usuario.es_director_th() and plan.estado not in ['EN_APROBACION', 'APROBADO']:
        flash('No tiene acceso a este plan en su estado actual.', 'warning')
        return redirect(url_for('revision.lista_director'))
    elif usuario.es_presidente() and plan.estado not in ['EN_APROBACION', 'APROBADO']:
        flash('No tiene acceso a este plan en su estado actual.', 'warning')
        return redirect(url_for('revision.lista_presidente'))

    # Construir temas por dirección (SOLO TEMAS SELECCIONADOS)
    temas_por_direccion = {}
    for tema in plan.temas.filter(TemaCapacitacion.estado == 'ACTIVO').order_by(TemaCapacitacion.fecha_creacion):
        # Filtrar solo temas seleccionados
        ts = tema.tema_seleccionado
        if not ts or not ts.seleccionado:
            continue
            
        if tema.usuario and tema.usuario.direccion:
            dir_nombre = tema.usuario.direccion.nombre
            if dir_nombre not in temas_por_direccion:
                temas_por_direccion[dir_nombre] = {
                    'direccion': tema.usuario.direccion,
                    'temas': [],
                }
            temas_por_direccion[dir_nombre]['temas'].append(tema)

    observaciones = plan.observaciones_list.order_by(ObservacionPlan.fecha_creacion.desc()).all()
    total_seleccionado = plan.get_total_seleccionado()
    supera_presupuesto = total_seleccionado > plan.monto_referencial if plan.monto_referencial else False

    return render_template('revision/ver_plan.html',
                           plan=plan,
                           temas_por_direccion=temas_por_direccion,
                           observaciones=observaciones,
                           total_seleccionado=total_seleccionado,
                           supera_presupuesto=supera_presupuesto,
                           usuario=usuario)