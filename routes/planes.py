"""
EMELNORTE - SIGEERN
Rutas de Planes de Capacitación - Solo para ANALISTA (RN-01, RN-04, RN-05, RN-06)
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models import PlanCapacitacion, TemaCapacitacion, TemaSeleccionado, Usuario, Direccion, ObservacionPlan
from routes.auth import login_required, get_usuario_actual, rol_required
from config import db
from datetime import datetime

planes_bp = Blueprint('planes', __name__, url_prefix='/planes')

# ─────────────────────────────────────────────────────────────
# RN-01: Analista crea el plan (año + monto referencial)
# ─────────────────────────────────────────────────────────────

@planes_bp.route('/')
@rol_required('ANALISTA')
def lista():
    """Lista de planes de capacitación - Solo Analista"""
    usuario = get_usuario_actual()
    planes = PlanCapacitacion.query.order_by(PlanCapacitacion.anio.desc()).all()
    return render_template('planes/lista.html', planes=planes, usuario=usuario)


@planes_bp.route('/nuevo', methods=['POST'])
@rol_required('ANALISTA')
def nuevo():
    """Crear un nuevo plan (desde modal)"""
    anio = request.form.get('anio', type=int)
    monto_referencial = request.form.get('monto_referencial', type=float)

    if not anio or not monto_referencial:
        flash('Todos los campos son obligatorios.', 'danger')
        return redirect(url_for('planes.lista'))

    plan_existente = PlanCapacitacion.query.filter_by(anio=anio).first()
    if plan_existente:
        flash(f'Ya existe un Plan de Capacitación para el año {anio}.', 'warning')
        return redirect(url_for('planes.lista'))

    usuario = get_usuario_actual()
    plan = PlanCapacitacion(
        anio=anio,
        monto_referencial=monto_referencial,
        estado='BORRADOR',
        creado_por_id=usuario.id,
        fecha_creacion=datetime.utcnow()
    )
    db.session.add(plan)
    db.session.commit()

    flash(f'Plan de Capacitación {anio} creado exitosamente. Los directores serán notificados por correo para registrar sus necesidades.', 'success')
    return redirect(url_for('planes.detalle', plan_id=plan.id))


# ─────────────────────────────────────────────────────────────
# RN-04: Analista visualiza y gestiona el plan
# ─────────────────────────────────────────────────────────────

@planes_bp.route('/<int:plan_id>')
@rol_required('ANALISTA')
def detalle(plan_id):
    """Detalle completo del plan para el Analista (RN-04, RN-05)"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)
    usuario = get_usuario_actual()

    # Obtener usuarios que han enviado sus temas
    from models import EnvioTemasDirector
    usuarios_que_enviaron = [envio.usuario_id for envio in EnvioTemasDirector.query.filter_by(plan_id=plan.id).all()]

    temas_por_direccion = {}
    for tema in plan.temas.filter(TemaCapacitacion.estado == 'ACTIVO').order_by(TemaCapacitacion.fecha_creacion):
        # Mostrar todos los temas, incluso si el director no los ha enviado aún para propósitos de simulación y visibilidad

            
        if tema.usuario and tema.usuario.direccion:
            dir_nombre = tema.usuario.direccion.nombre
            if dir_nombre not in temas_por_direccion:
                temas_por_direccion[dir_nombre] = {
                    'direccion': tema.usuario.direccion,
                    'temas': [],
                    'max_temas': tema.usuario.direccion.max_temas
                }
            temas_por_direccion[dir_nombre]['temas'].append(tema)

    observaciones = plan.observaciones_list.order_by(ObservacionPlan.fecha_creacion.desc()).all()
    total_seleccionado = plan.get_total_seleccionado()
    supera_presupuesto = total_seleccionado > plan.monto_referencial if plan.monto_referencial else False
    direcciones = Direccion.query.filter_by(estado='ACTIVO').order_by(Direccion.nombre).all()
    
    # Obtener temas extra plan
    temas_extra = plan.temas.filter(TemaCapacitacion.estado == 'EXTRA_PLAN').order_by(TemaCapacitacion.fecha_creacion).all()
    
    return render_template('planes/detalle.html',
                           plan=plan,
                           temas_por_direccion=temas_por_direccion,
                           observaciones=observaciones,
                           total_seleccionado=total_seleccionado,
                           supera_presupuesto=supera_presupuesto,
                           usuario=usuario,
                           direcciones=direcciones,
                           temas_extra=temas_extra)


@planes_bp.route('/<int:plan_id>/actualizar-presupuesto-aprobado', methods=['POST'])
@rol_required('ANALISTA')
def actualizar_presupuesto_aprobado(plan_id):
    """RN-04: Registrar el valor del presupuesto referencial aprobado del plan"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)
    if not plan.is_editable():
        flash('El plan no puede modificarse en su estado actual.', 'warning')
        return redirect(url_for('planes.detalle', plan_id=plan_id))

    monto = request.form.get('monto_aprobado', type=float)
    if monto is not None:
        plan.monto_aprobado = monto
        db.session.commit()
        flash('Presupuesto aprobado actualizado.', 'success')
    return redirect(url_for('planes.detalle', plan_id=plan_id))


# ─────────────────────────────────────────────────────────────
# RN-04: Agregar temas adicionales (solo Analista)
# ─────────────────────────────────────────────────────────────

@planes_bp.route('/<int:plan_id>/tema/nuevo_ajax', methods=['POST'])
@rol_required('ANALISTA')
def nuevo_tema_ajax(plan_id):
    """Agregar un tema adicional al plan via AJAX"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)
    if not (plan.is_editable() or plan.estado == 'APROBADO'):
        return jsonify({'success': False, 'message': 'No se pueden agregar temas en el estado actual del plan.'})

    usuario = get_usuario_actual()
    nombre = request.form.get('nombre', '').strip()
    num_participantes = request.form.get('num_participantes', type=int)
    modalidad = request.form.get('modalidad')
    horas = request.form.get('horas', type=float)
    presupuesto_referencial = request.form.get('presupuesto_referencial', type=float)
    mes_ejecucion = request.form.get('mes_ejecucion', type=int)
    direccion_id = request.form.get('direccion_id', type=int)

    if not all([nombre, num_participantes, modalidad, horas, presupuesto_referencial, mes_ejecucion, direccion_id]):
        return jsonify({'success': False, 'message': 'Todos los campos son obligatorios.'})

    # Buscar un usuario de la direccion seleccionada para asociar el tema
    usuario_asociado_id = usuario.id
    from models import Usuario as U
    usr_dir = U.query.filter_by(direccion_id=direccion_id, rol='DIRECTOR').first()
    if usr_dir:
        usuario_asociado_id = usr_dir.id
    
    dir_obj = Direccion.query.get(direccion_id)

    tema = TemaCapacitacion(
        nombre=nombre,
        num_participantes=num_participantes,
        modalidad=modalidad,
        horas=horas,
        presupuesto_referencial=presupuesto_referencial,
        mes_ejecucion=mes_ejecucion,
        usuario_id=usuario_asociado_id,
        plan_id=plan_id,
        es_del_analista=True,
        estado='ACTIVO'
    )
    db.session.add(tema)
    db.session.flush()

    ts = TemaSeleccionado(
        tema_id=tema.id,
        plan_id=plan_id,
        seleccionado=True,
        presupuesto_aprobado=presupuesto_referencial
    )
    db.session.add(ts)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Tema agregado exitosamente',
        'tema': {
            'id': tema.id,
            'nombre': tema.nombre,
            'modalidad': tema.modalidad,
            'horas': tema.horas,
            'num_participantes': tema.num_participantes,
            'presupuesto_referencial': tema.presupuesto_referencial,
            'direccion_nombre': dir_obj.nombre if dir_obj else 'Desconocida'
        },
        'total_seleccionado': plan.get_total_seleccionado(),
        'temas_seleccionados_count': plan.get_temas_seleccionados_count()
    })

@planes_bp.route('/<int:plan_id>/tema/extra_ajax', methods=['POST'])
@rol_required('ANALISTA')
def nuevo_extra_ajax(plan_id):
    """Agregar un tema NO PLANIFICADO (Extra Plan) cuando el plan ya está APROBADO"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)
    if plan.estado != 'APROBADO':
        return jsonify({'success': False, 'message': 'El plan debe estar APROBADO para registrar temas no planificados.'})

    usuario = get_usuario_actual()
    nombre = request.form.get('nombre', '').strip()
    num_participantes = request.form.get('num_participantes', type=int)
    modalidad = request.form.get('modalidad')
    horas = request.form.get('horas', type=float)
    presupuesto_referencial = 0.0 # Es gratuito
    mes_ejecucion = request.form.get('mes_ejecucion', type=int)
    direccion_id = request.form.get('direccion_id', type=int)

    if not all([nombre, num_participantes, modalidad, horas, mes_ejecucion, direccion_id]):
        return jsonify({'success': False, 'message': 'Todos los campos son obligatorios.'})

    # Buscar usuario de la direccion seleccionada
    usuario_asociado_id = usuario.id
    from models import Usuario as U
    usr_dir = U.query.filter_by(direccion_id=direccion_id, rol='DIRECTOR').first()
    if usr_dir:
        usuario_asociado_id = usr_dir.id
    
    dir_obj = Direccion.query.get(direccion_id)

    tema = TemaCapacitacion(
        nombre=nombre + " (NO PLANIFICADO)",
        num_participantes=num_participantes,
        modalidad=modalidad,
        horas=horas,
        presupuesto_referencial=presupuesto_referencial,
        mes_ejecucion=mes_ejecucion,
        usuario_id=usuario_asociado_id,
        plan_id=plan_id,
        es_del_analista=True,
        estado='EXTRA_PLAN'
    )
    db.session.add(tema)
    db.session.flush()

    ts = TemaSeleccionado(
        tema_id=tema.id,
        plan_id=plan_id,
        seleccionado=True,
        presupuesto_aprobado=0.0,
        observaciones='TEMA EXTRA PLANIFICACION (GRATUITO)'
    )
    db.session.add(ts)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Tema Extra-Plan agregado exitosamente. Ya puede registrar su ejecución.',
        'tema': {
            'id': tema.id,
            'nombre': tema.nombre,
            'modalidad': tema.modalidad,
            'horas': tema.horas,
            'num_participantes': tema.num_participantes,
            'presupuesto_referencial': 0,
            'direccion_nombre': dir_obj.nombre if dir_obj else 'Desconocida'
        }
    })

@planes_bp.route('/<int:plan_id>/tema/<int:tema_id>/editar_ajax', methods=['POST'])
@rol_required('ANALISTA')
def editar_tema_ajax(plan_id, tema_id):
    """Editar un tema adicional al plan via AJAX"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)
    if not (plan.is_editable() or plan.estado == 'APROBADO'):
        return jsonify({'success': False, 'message': 'No se pueden editar temas en este estado.'})

    tema = TemaCapacitacion.query.get_or_404(tema_id)
    if not tema.es_del_analista:
        return jsonify({'success': False, 'message': 'Solo puede editar temas agregados manualmente.'})

    tema.nombre = request.form.get('nombre', tema.nombre).strip()
    tema.num_participantes = request.form.get('num_participantes', type=int) or tema.num_participantes
    tema.modalidad = request.form.get('modalidad') or tema.modalidad
    tema.horas = request.form.get('horas', type=float) or tema.horas
    tema.presupuesto_referencial = request.form.get('presupuesto_referencial', type=float) or tema.presupuesto_referencial
    tema.mes_ejecucion = request.form.get('mes_ejecucion', type=int) or tema.mes_ejecucion

    # Actualizar presupuesto aprobado si esta seleccionado
    ts = TemaSeleccionado.query.filter_by(tema_id=tema.id, plan_id=plan_id).first()
    if ts and ts.seleccionado:
        ts.presupuesto_aprobado = tema.presupuesto_referencial

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Tema actualizado exitosamente',
        'tema': {
            'id': tema.id,
            'nombre': tema.nombre,
            'modalidad': tema.modalidad,
            'horas': tema.horas,
            'num_participantes': tema.num_participantes,
            'presupuesto_referencial': tema.presupuesto_referencial
        },
        'total_seleccionado': plan.get_total_seleccionado(),
        'temas_seleccionados_count': plan.get_temas_seleccionados_count()
    })



# ─────────────────────────────────────────────────────────────
# RN-04: Seleccionar / Descartar temas
# ─────────────────────────────────────────────────────────────

@planes_bp.route('/<int:plan_id>/tema/<int:tema_id>/toggle', methods=['POST'])
@rol_required('ANALISTA')
def toggle_tema(plan_id, tema_id):
    """RN-04: Seleccionar o descartar un tema"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)
    if not plan.is_editable():
        flash('No se pueden modificar temas en el estado actual.', 'warning')
        return redirect(url_for('planes.detalle', plan_id=plan_id))

    ts = TemaSeleccionado.query.filter_by(tema_id=tema_id, plan_id=plan_id).first()
    if ts:
        ts.seleccionado = not ts.seleccionado
        if ts.seleccionado and not ts.presupuesto_aprobado:
            tema = TemaCapacitacion.query.get(tema_id)
            ts.presupuesto_aprobado = tema.presupuesto_referencial if tema else 0
        db.session.commit()
        estado = 'seleccionado' if ts.seleccionado else 'descartado'
        flash(f'Tema {estado}.', 'success')
    return redirect(url_for('planes.detalle', plan_id=plan_id))


@planes_bp.route('/<int:plan_id>/tema/<int:tema_id>/toggle_ajax', methods=['POST'])
@rol_required('ANALISTA')
def toggle_tema_ajax(plan_id, tema_id):
    """Ajax endpoint para seleccionar o descartar un tema sin recargar la página"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)
    if not plan.is_editable():
        return jsonify({'success': False, 'message': 'Plan no editable'})

    ts = TemaSeleccionado.query.filter_by(tema_id=tema_id, plan_id=plan_id).first()
    if ts:
        ts.seleccionado = not ts.seleccionado
        if ts.seleccionado and not ts.presupuesto_aprobado:
            tema = TemaCapacitacion.query.get(tema_id)
            ts.presupuesto_aprobado = tema.presupuesto_referencial if tema else 0
        db.session.commit()
        return jsonify({
            'success': True,
            'seleccionado': ts.seleccionado,
            'total_seleccionado': plan.get_total_seleccionado(),
            'temas_seleccionados_count': plan.get_temas_seleccionados_count()
        })
    return jsonify({'success': False, 'message': 'Tema no encontrado'})



@planes_bp.route('/<int:plan_id>/tema/<int:tema_id>/presupuesto', methods=['POST'])
@rol_required('ANALISTA')
def actualizar_presupuesto_tema(plan_id, tema_id):
    """RN-04: Actualizar presupuesto aprobado de un tema"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)
    if not plan.is_editable():
        flash('No se pueden modificar temas en el estado actual.', 'warning')
        return redirect(url_for('planes.detalle', plan_id=plan_id))

    presupuesto = request.form.get('presupuesto_aprobado', type=float)
    ts = TemaSeleccionado.query.filter_by(tema_id=tema_id, plan_id=plan_id).first()
    if ts and presupuesto is not None:
        ts.presupuesto_aprobado = presupuesto
        db.session.commit()
    return redirect(url_for('planes.detalle', plan_id=plan_id))


@planes_bp.route('/<int:plan_id>/tema/<int:tema_id>/eliminar', methods=['POST'])
@rol_required('ANALISTA')
def eliminar_tema(plan_id, tema_id):
    """RN-04: Eliminar un tema (solo temas agregados por el Analista)"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)
    if not plan.is_editable():
        flash('No se pueden eliminar temas en el estado actual.', 'warning')
        return redirect(url_for('planes.detalle', plan_id=plan_id))

    tema = TemaCapacitacion.query.get_or_404(tema_id)
    tema.estado = 'ELIMINADO'
    db.session.commit()
    flash('Tema eliminado.', 'success')
    return redirect(url_for('planes.detalle', plan_id=plan_id))


# ─────────────────────────────────────────────────────────────
# RN-06: Analista envía plan a revisión del Jefe de Personal
# ─────────────────────────────────────────────────────────────

@planes_bp.route('/<int:plan_id>/enviar-revision', methods=['POST'])
@rol_required('ANALISTA')
def enviar_revision(plan_id):
    """RN-06: Enviar plan a revisión → estado EN_REVISION"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)
    if plan.estado not in ['BORRADOR', 'EN_CORRECCION']:
        flash('No se puede enviar este plan a revisión en su estado actual.', 'warning')
        return redirect(url_for('planes.detalle', plan_id=plan_id))

    temas_sel = TemaSeleccionado.query.filter_by(plan_id=plan_id, seleccionado=True).count()
    if temas_sel == 0:
        flash('Debe seleccionar al menos un tema antes de enviar a revisión.', 'warning')
        return redirect(url_for('planes.detalle', plan_id=plan_id))

    plan.estado = 'EN_REVISION'
    plan.fecha_envio_jefe = datetime.utcnow()
    db.session.commit()
    flash('Plan enviado al Jefe de Personal para revisión. El estado cambió a "En Revisión".', 'success')
    return redirect(url_for('planes.detalle', plan_id=plan_id))


# ─────────────────────────────────────────────────────────────
# RN-07: Jefe de Personal aprueba o devuelve el plan
# ─────────────────────────────────────────────────────────────

@planes_bp.route('/<int:plan_id>/accion-jefe', methods=['POST'])
@rol_required('JEFE_PERSONAL')
def accion_jefe(plan_id):
    """RN-07: Jefe aprueba (envía a Director TH) o devuelve al Analista"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)
    if plan.estado != 'EN_REVISION':
        flash('Este plan no está en estado de revisión.', 'warning')
        return redirect(url_for('revision.lista_jefe'))

    action = request.form.get('action')
    observacion_texto = request.form.get('observacion', '').strip()

    if action == 'aprobar':
        plan.estado = 'EN_APROBACION'
        plan.fecha_envio_director = datetime.utcnow()
        obs_tipo = 'APROBACION'
        obs_texto = f'Plan aprobado por Jefe de Personal. Enviado al Director de Talento Humano. {observacion_texto}'.strip()
        flash('Plan aprobado. Se ha enviado un correo al Director de Talento Humano con el informe PDF firmado digitalmente adjunto.', 'success')

    elif action == 'devolver':
        if not observacion_texto:
            flash('Debe indicar el motivo de la devolución.', 'danger')
            return redirect(url_for('revision.ver_plan', plan_id=plan_id))
        plan.estado = 'EN_CORRECCION'
        obs_tipo = 'DEVOLUCION'
        obs_texto = f'Plan devuelto para corrección: {observacion_texto}'
        flash('Plan devuelto al Analista de Talento Humano para correcciones.', 'warning')

    elif action == 'observacion':
        if not observacion_texto:
            flash('Ingrese el texto de la observación.', 'danger')
            return redirect(url_for('revision.ver_plan', plan_id=plan_id))
        obs_tipo = 'OBSERVACION'
        obs_texto = observacion_texto

    if action in ['aprobar', 'devolver', 'observacion']:
        obs = ObservacionPlan(
            observacion=obs_texto,
            autor=session['usuario_nombre'],
            tipo_observacion=obs_tipo,
            plan_id=plan_id
        )
        db.session.add(obs)
        db.session.commit()

    if action == 'observacion':
        flash('Observación agregada.', 'success')
        return redirect(url_for('revision.ver_plan', plan_id=plan_id))

    return redirect(url_for('revision.lista_jefe'))


# ─────────────────────────────────────────────────────────────
# RN-08: Director TH revisa y envía al Presidente
# ─────────────────────────────────────────────────────────────

@planes_bp.route('/<int:plan_id>/enviar-presidente', methods=['POST'])
@rol_required('DIRECTOR')
def enviar_presidente(plan_id):
    """RN-08: Director TH envía plan al Presidente para aprobación final"""
    usuario = get_usuario_actual()
    if not usuario.es_director_th():
        flash('No tiene permisos para realizar esta acción.', 'danger')
        return redirect(url_for('auth.dashboard'))

    plan = PlanCapacitacion.query.get_or_404(plan_id)
    if plan.estado != 'EN_APROBACION':
        flash('El plan no está en estado de aprobación por el Director.', 'warning')
        return redirect(url_for('revision.lista_director'))

    obs = ObservacionPlan(
        observacion='Plan revisado por Director de Talento Humano. Enviado al Presidente para aprobación final.',
        autor=session['usuario_nombre'],
        tipo_observacion='APROBACION',
        plan_id=plan_id
    )
    db.session.add(obs)
    db.session.commit()

    flash('Plan firmado electrónicamente y enviado al Presidente Ejecutivo para aprobación final.', 'success')
    return redirect(url_for('revision.lista_director'))


# ─────────────────────────────────────────────────────────────
# RN-09: Presidente aprueba definitivamente
# ─────────────────────────────────────────────────────────────

@planes_bp.route('/<int:plan_id>/aprobar-final', methods=['POST'])
@rol_required('PRESIDENTE')
def aprobar_final(plan_id):
    """RN-09: Aprobación final del plan - queda bloqueado permanentemente"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)
    if plan.estado != 'EN_APROBACION':
        flash('El plan no está en estado de aprobación final.', 'warning')
        return redirect(url_for('revision.lista_presidente'))

    monto_aprobado = plan.monto_aprobado or plan.monto_referencial

    plan.estado = 'APROBADO'
    plan.monto_aprobado = monto_aprobado
    plan.fecha_aprobacion = datetime.utcnow()

    obs_texto = f'Plan Anual de Capacitación {plan.anio} APROBADO definitivamente. Monto aprobado: ${monto_aprobado:,.2f}.'

    obs = ObservacionPlan(
        observacion=obs_texto,
        autor=session['usuario_nombre'],
        tipo_observacion='APROBACION',
        plan_id=plan_id
    )
    db.session.add(obs)
    db.session.commit()

    flash(f'¡Plan {plan.anio} firmado electrónicamente y aprobado! El plan quedó bloqueado.', 'success')
    return redirect(url_for('revision.lista_presidente'))

@planes_bp.route('/<int:plan_id>/imprimir')
@login_required
def imprimir_plan(plan_id):
    """Vista optimizada para imprimir o guardar como PDF el plan"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)
    
    # Construir temas por dirección (solo seleccionados)
    temas_por_direccion = {}
    for tema in plan.temas.filter(TemaCapacitacion.estado == 'ACTIVO').order_by(TemaCapacitacion.fecha_creacion):
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

    return render_template('planes/imprimir.html',
                           plan=plan,
                           temas_por_direccion=temas_por_direccion,
                           total_seleccionado=plan.get_total_seleccionado())