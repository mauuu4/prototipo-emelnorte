"""
EMELNORTE - SIGEERN
Rutas de Revisión y Aprobación
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import PlanCapacitacion, ObservacionPlan
from routes.auth import login_required, get_usuario_actual, rol_required
from config import db

revision_bp = Blueprint('revision', __name__, url_prefix='/revision')


@revision_bp.route('/jefe')
@rol_required('JEFE_PERSONAL')
def lista_jefe():
    """Lista de planes en revisión para el Jefe de Personal"""
    planes = PlanCapacitacion.query.filter_by(estado='EN_REVISION').order_by(
        PlanCapacitacion.fecha_envio_jefe.desc()
    ).all()
    return render_template('revision/lista_jefe.html', planes=planes)


@revision_bp.route('/director')
@rol_required('DIRECTOR')
def lista_director():
    """Lista de planes en aprobación para el Director"""
    planes = PlanCapacitacion.query.filter_by(estado='EN_APROBACION').order_by(
        PlanCapacitacion.fecha_envio_director.desc()
    ).all()
    return render_template('revision/lista_director.html', planes=planes)


@revision_bp.route('/presidente')
@rol_required('PRESIDENTE')
def lista_presidente():
    """Lista de planes para aprobación del Presidente"""
    planes = PlanCapacitacion.query.filter(
        PlanCapacitacion.estado.in_(['EN_APROBACION', 'APROBADO'])
    ).order_by(PlanCapacitacion.fecha_envio_director.desc()).all()

    return render_template('revision/lista_presidente.html', planes=planes)


@revision_bp.route('/<int:plan_id>/ver')
@login_required
def ver_plan(plan_id):
    """Ver detalle de un plan (para revisión)"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)
    usuario = get_usuario_actual()

    # Obtener temas agrupados por dirección
    temas_por_direccion = {}
    for tema in plan.temas.filter_by(estado='ACTIVO'):
        if tema.usuario and tema.usuario.direccion:
            dir_nombre = tema.usuario.direccion.nombre
            if dir_nombre not in temas_por_direccion:
                temas_por_direccion[dir_nombre] = {
                    'direccion': tema.usuario.direccion,
                    'temas': [],
                    'max_temas': tema.usuario.direccion.max_temas
                }
            temas_por_direccion[dir_nombre]['temas'].append(tema)

    # Obtener observaciones
    observaciones = plan.observaciones_list.order_by(db.desc('fecha_creacion')).all()

    # Calcular totales
    total_seleccionado = plan.get_total_seleccionado()
    supera_presupuesto = total_seleccionado > plan.monto_referencial

    return render_template('revision/ver_plan.html',
                           plan=plan,
                           temas_por_direccion=temas_por_direccion,
                           observaciones=observaciones,
                           total_seleccionado=total_seleccionado,
                           supera_presupuesto=supera_presupuesto,
                           usuario=usuario)