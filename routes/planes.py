"""
EMELNORTE - SIGEERN
Rutas de Planes de Capacitación
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import PlanCapacitacion, TemaCapacitacion, TemaSeleccionado, Usuario, Direccion
from routes.auth import login_required, get_usuario_actual, rol_required
from config import db
from datetime import datetime

planes_bp = Blueprint('planes', __name__, url_prefix='/planes')


@planes_bp.route('/')
@login_required
def lista():
    """Lista de planes de capacitación"""
    usuario = get_usuario_actual()

    # Filtrar según el rol
    if usuario.es_analista():
        planes = PlanCapacitacion.query.order_by(PlanCapacitacion.anio.desc()).all()
    else:
        # Otros roles solo ven planes en estados específicos
        planes = PlanCapacitacion.query.filter(
            PlanCapacitacion.estado.in_(['EN_REVISION', 'EN_APROBACION', 'APROBADO'])
        ).order_by(PlanCapacitacion.anio.desc()).all()

    return render_template('planes/lista.html', planes=planes, usuario=usuario)


@planes_bp.route('/nuevo', methods=['GET', 'POST'])
@rol_required('ANALISTA')
def nuevo():
    """Crear un nuevo plan de capacitación"""
    if request.method == 'POST':
        anio = request.form.get('anio', type=int)
        monto_referencial = request.form.get('monto_referencial', type=float)

        if not anio or not monto_referencial:
            flash('Todos los campos son obligatorios.', 'danger')
            return redirect(url_for('planes.nuevo'))

        # Verificar que no exista un plan para ese año
        plan_existente = PlanCapacitacion.query.filter_by(anio=anio).first()
        if plan_existente:
            flash(f'Ya existe un plan de capacitación para el año {anio}.', 'warning')
            return redirect(url_for('planes.lista'))

        # Crear el plan
        # Buscar la dirección de Talento Humano
        direccion_th = Direccion.query.filter_by(nombre='Talento Humano').first()

        plan = PlanCapacitacion(
            anio=anio,
            monto_referencial=monto_referencial,
            estado='BORRADOR',
            direccion_id=direccion_th.id if direccion_th else 1,
            fecha_creacion=datetime.utcnow()
        )
        db.session.add(plan)
        db.session.commit()

        flash(f'Plan de capacitación {anio} creado exitosamente.', 'success')
        return redirect(url_for('planes.detalle', plan_id=plan.id))

    anio_actual = datetime.now().year
    return render_template('planes/nuevo.html', anio_actual=anio_actual)


@planes_bp.route('/<int:plan_id>')
@login_required
def detalle(plan_id):
    """Detalle de un plan de capacitación"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)
    usuario = get_usuario_actual()

    # Obtener temas agrupados por dirección
    temas_por_direccion = {}
    for tema in plan.temas.filter(TemaCapacitacion.estado == 'ACTIVO'):
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

    return render_template('planes/detalle.html',
                           plan=plan,
                           temas_por_direccion=temas_por_direccion,
                           observaciones=observaciones,
                           total_seleccionado=total_seleccionado,
                           supera_presupuesto=supera_presupuesto,
                           usuario=usuario)


@planes_bp.route('/<int:plan_id>/tema/nuevo', methods=['GET', 'POST'])
@rol_required('ANALISTA')
def nuevo_tema(plan_id):
    """Agregar un tema manualmente al plan (Analista)"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)

    if plan.estado not in ['BORRADOR', 'EN_CORRECCION']:
        flash('No se pueden agregar temas a un plan que no está en borrador o corrección.', 'warning')
        return redirect(url_for('planes.detalle', plan_id=plan_id))

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        etapa_funcional = request.form.get('etapa_funcional')
        subetapa_funcional = request.form.get('subetapa_funcional')
        num_participantes = request.form.get('num_participantes', type=int)
        modalidad = request.form.get('modalidad')
        horas = request.form.get('horas', type=float)
        presupuesto_referencial = request.form.get('presupuesto_referencial', type=float)
        mes_ejecucion = request.form.get('mes_ejecucion', type=int)
        direccion_id = request.form.get('direccion_id', type=int)

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
            usuario_id=session['usuario_id'],  # Será el analista
            plan_id=plan_id,
            estado='ACTIVO'
        )
        db.session.add(tema)
        db.session.flush()  # Para obtener el ID

        # Crear registro de selección
        tema_seleccionado = TemaSeleccionado(
            tema_id=tema.id,
            plan_id=plan_id,
            seleccionado=True,  # Por defecto seleccionado
            presupuesto_aprobado=presupuesto_referencial
        )
        db.session.add(tema_seleccionado)
        db.session.commit()

        flash('Tema agregado exitosamente.', 'success')
        return redirect(url_for('planes.detalle', plan_id=plan_id))

    # Obtener direcciones para el selector
    direcciones = Direccion.query.filter_by(estado='ACTIVO').all()
    return render_template('planes/tema_nuevo.html', plan=plan, direcciones=direcciones)


@planes_bp.route('/<int:plan_id>/tema/<int:tema_id>/seleccionar', methods=['POST'])
@rol_required('ANALISTA')
def seleccionar_tema(plan_id, tema_id):
    """Seleccionar o deseleccionar un tema"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)

    if plan.estado not in ['BORRADOR', 'EN_CORRECCION']:
        flash('No se pueden modificar temas en este estado.', 'warning')
        return redirect(url_for('planes.detalle', plan_id=plan_id))

    tema = TemaCapacitacion.query.get_or_404(tema_id)
    ts = TemaSeleccionado.query.filter_by(tema_id=tema_id, plan_id=plan_id).first()

    if ts:
        ts.seleccionado = not ts.seleccionado
        db.session.commit()
        estado = 'seleccionado' if ts.seleccionado else 'deseleccionado'
        flash(f'Tema {estado}.', 'success')

    return redirect(url_for('planes.detalle', plan_id=plan_id))


@planes_bp.route('/<int:plan_id>/tema/<int:tema_id>/presupuesto', methods=['POST'])
@rol_required('ANALISTA')
def actualizar_presupuesto(plan_id, tema_id):
    """Actualizar el presupuesto aprobado de un tema"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)

    if plan.estado not in ['BORRADOR', 'EN_CORRECCION']:
        flash('No se pueden modificar temas en este estado.', 'warning')
        return redirect(url_for('planes.detalle', plan_id=plan_id))

    presupuesto = request.form.get('presupuesto_aprobado', type=float)
    ts = TemaSeleccionado.query.filter_by(tema_id=tema_id, plan_id=plan_id).first()

    if ts:
        ts.presupuesto_aprobado = presupuesto
        db.session.commit()
        flash('Presupuesto actualizado.', 'success')

    return redirect(url_for('planes.detalle', plan_id=plan_id))


@planes_bp.route('/<int:plan_id>/tema/<int:tema_id>/eliminar', methods=['POST'])
@rol_required('ANALISTA')
def eliminar_tema(plan_id, tema_id):
    """Eliminar un tema (marcado como inactivo)"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)

    if plan.estado not in ['BORRADOR', 'EN_CORRECCION']:
        flash('No se pueden eliminar temas en este estado.', 'warning')
        return redirect(url_for('planes.detalle', plan_id=plan_id))

    tema = TemaCapacitacion.query.get_or_404(tema_id)
    tema.estado = 'ELIMINADO'
    db.session.commit()

    flash('Tema eliminado.', 'success')
    return redirect(url_for('planes.detalle', plan_id=plan_id))


@planes_bp.route('/<int:plan_id>/observacion', methods=['POST'])
@login_required
def agregar_observacion(plan_id):
    """Agregar una observación al plan"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)
    observacion_texto = request.form.get('observacion')
    tipo = request.form.get('tipo_observacion', 'OBSERVACION')

    if observacion_texto:
        from models import ObservacionPlan
        obs = ObservacionPlan(
            observacion=observacion_texto,
            autor=session['usuario_nombre'],
            tipo_observacion=tipo,
            plan_id=plan_id
        )
        db.session.add(obs)
        db.session.commit()
        flash('Observación agregada.', 'success')

    return redirect(url_for('planes.detalle', plan_id=plan_id))


@planes_bp.route('/<int:plan_id>/enviar-revision', methods=['POST'])
@rol_required('ANALISTA')
def enviar_revision(plan_id):
    """Enviar plan a revisión del Jefe de Personal"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)

    if plan.estado not in ['BORRADOR', 'EN_CORRECCION']:
        flash('No se puede enviar este plan a revisión.', 'warning')
        return redirect(url_for('planes.detalle', plan_id=plan_id))

    # Verificar que haya al menos un tema seleccionado
    temas_seleccionados = TemaSeleccionado.query.filter_by(plan_id=plan_id, seleccionado=True).count()
    if temas_seleccionados == 0:
        flash('Debe seleccionar al menos un tema antes de enviar a revisión.', 'warning')
        return redirect(url_for('planes.detalle', plan_id=plan_id))

    plan.estado = 'EN_REVISION'
    plan.fecha_envio_jefe = datetime.utcnow()
    db.session.commit()

    flash('Plan enviado a revisión del Jefe de Personal.', 'success')
    return redirect(url_for('planes.detalle', plan_id=plan_id))


@planes_bp.route('/<int:plan_id>/aprobar-jefe', methods=['POST'])
@rol_required('JEFE_PERSONAL')
def aprobar_jefe(plan_id):
    """Aprobar plan y enviar al Director"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)

    if plan.estado != 'EN_REVISION':
        flash('Este plan no está en revisión.', 'warning')
        return redirect(url_for('revision.lista_jefe'))

    action = request.form.get('action')

    if action == 'aprobar':
        plan.estado = 'EN_APROBACION'
        plan.fecha_envio_director = datetime.utcnow()

        # Agregar observación de aprobación
        from models import ObservacionPlan
        obs = ObservacionPlan(
            observacion='Aprobado por Jefe de Personal. Enviado a Director.',
            autor=session['usuario_nombre'],
            tipo_observacion='APROBACION',
            plan_id=plan_id
        )
        db.session.add(obs)
        flash('Plan aprobado y enviado a Director para revisión.', 'success')

    elif action == 'devolver':
        plan.estado = 'EN_CORRECCION'
        observacion_texto = request.form.get('observacion_devolucion', '')
        if observacion_texto:
            from models import ObservacionPlan
            obs = ObservacionPlan(
                observacion=f'Devuelto para corrección: {observacion_texto}',
                autor=session['usuario_nombre'],
                tipo_observacion='DEVOLUCION',
                plan_id=plan_id
            )
            db.session.add(obs)
        flash('Plan devuelto al Analista para corrección.', 'warning')

    db.session.commit()
    return redirect(url_for('revision.lista_jefe'))


@planes_bp.route('/<int:plan_id>/aprobar-director', methods=['POST'])
@rol_required('DIRECTOR')
def aprobar_director(plan_id):
    """Enviar plan al Presidente para aprobación final"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)

    if plan.estado != 'EN_APROBACION':
        flash('Este plan no está en espera de aprobación del Director.', 'warning')
        return redirect(url_for('revision.lista_director'))

    # Agregar observación
    from models import ObservacionPlan
    obs = ObservacionPlan(
        observacion='Aprobado por Director. Enviado a Presidente para aprobación final.',
        autor=session['usuario_nombre'],
        tipo_observacion='APROBACION',
        plan_id=plan_id
    )
    db.session.add(obs)
    db.session.commit()

    flash('Plan enviado al Presidente para aprobación final.', 'success')
    return redirect(url_for('revision.lista_director'))


@planes_bp.route('/<int:plan_id>/aprobar-presidente', methods=['GET', 'POST'])
@rol_required('PRESIDENTE')
def aprobar_presidente(plan_id):
    """Aprobación final por el Presidente"""
    plan = PlanCapacitacion.query.get_or_404(plan_id)

    if request.method == 'POST':
        monto_aprobado = request.form.get('monto_aprobado', type=float, default=plan.monto_referencial)
        observaciones = request.form.get('observaciones', '')

        plan.estado = 'APROBADO'
        plan.monto_aprobado = monto_aprobado
        plan.observaciones = observaciones
        plan.fecha_aprobacion = datetime.utcnow()

        # Agregar observación
        from models import ObservacionPlan
        obs = ObservacionPlan(
            observacion=f'Aprobado definitivamente. Monto aprobado: ${monto_aprobado:,.2f}. {observaciones}',
            autor=session['usuario_nombre'],
            tipo_observacion='APROBACION',
            plan_id=plan_id
        )
        db.session.add(obs)
        db.session.commit()

        flash('Plan de Capacitación aprobado definitivamente y bloqueado.', 'success')
        return redirect(url_for('revision.lista_presidente'))

    return render_template('planes/aprobar_presidente.html', plan=plan)