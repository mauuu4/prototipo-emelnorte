"""
EMELNORTE - SIGEERN
Rutas de Ejecución de Capacitaciones
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_from_directory, current_app
from models import (
    PlanCapacitacion, TemaCapacitacion, TemaSeleccionado,
    CapacitacionEjecutada, Participante, Direccion, Empleado, EmpresaCapacitadora, EvaluacionCapacitacion
)
from routes.auth import login_required, get_usuario_actual, rol_required
from config import db
from datetime import datetime, date
from werkzeug.utils import secure_filename
import os

ejecucion_bp = Blueprint('ejecucion', __name__, url_prefix='/ejecucion')


@ejecucion_bp.route('/api/empleados')
@rol_required('ANALISTA')
def api_empleados():
    """API para buscar empleados por código, cédula o nombres (autocompletado)"""
    from flask import jsonify
    from sqlalchemy import or_
    q = request.args.get('q', '').strip()
    
    if len(q) < 2:
        return jsonify([])
        
    empleados = Empleado.query.filter(
        Empleado.estado == 'ACTIVO',
        or_(
            Empleado.codigo.ilike(f'%{q}%'),
            Empleado.cedula.ilike(f'%{q}%'),
            Empleado.nombres.ilike(f'%{q}%')
        )
    ).limit(10).all()
    return jsonify([e.to_dict() for e in empleados])


@ejecucion_bp.route('/api/empleado/<codigo>')
@rol_required('ANALISTA')
def api_empleado_detalle(codigo):
    """Retorna datos de un empleado por código exacto"""
    from flask import jsonify
    e = Empleado.query.filter_by(codigo=codigo.upper(), estado='ACTIVO').first()
    if not e:
        return jsonify(None), 404
    return jsonify(e.to_dict())


@ejecucion_bp.route('/')
@rol_required('ANALISTA')
def lista():
    """Dashboard de Ejecución de Capacitaciones"""
    # Obtener planes aprobados para el filtro de años
    planes_aprobados = PlanCapacitacion.query.filter_by(estado='APROBADO').order_by(PlanCapacitacion.anio.desc()).all()
    
    if not planes_aprobados:
        return render_template('ejecucion/lista.html', temas=[], anio_actual=None, planes=[])
        
    # Determinar el año seleccionado (por defecto el más reciente)
    anio_seleccionado = request.args.get('anio', type=int)
    if not anio_seleccionado:
        anio_seleccionado = planes_aprobados[0].anio
        
    plan_actual = next((p for p in planes_aprobados if p.anio == anio_seleccionado), planes_aprobados[0])
    
    # Obtener todos los temas seleccionados de este plan, ordenados por mes
    temas_seleccionados = TemaSeleccionado.query.filter_by(
        plan_id=plan_actual.id, 
        seleccionado=True
    ).join(TemaCapacitacion).order_by(TemaCapacitacion.mes_ejecucion, TemaCapacitacion.nombre).all()
    
    # Agrupar temas por mes
    from collections import OrderedDict
    temas_por_mes = OrderedDict()
    
    for ts in temas_seleccionados:
        mes_num = ts.tema.mes_ejecucion
        mes_nombre = ts.tema.get_nombre_mes()
        if not mes_nombre: mes_nombre = "Sin Mes Definido"
        
        # Guardamos una tupla (numero_mes, nombre_mes) como clave para poder ordenar luego si fuera necesario
        clave_mes = (mes_num, mes_nombre)
        
        if clave_mes not in temas_por_mes:
            temas_por_mes[clave_mes] = []
        temas_por_mes[clave_mes].append(ts)
    
    return render_template(
        'ejecucion/lista.html', 
        temas_por_mes=temas_por_mes, 
        anio_actual=anio_seleccionado, 
        planes=planes_aprobados
    )


@ejecucion_bp.route('/nuevo', methods=['GET', 'POST'])
@rol_required('ANALISTA')
def nuevo():
    """Registrar una nueva capacitación ejecutada"""
    if request.method == 'POST':
        tema_seleccionado_id = request.form.get('tema_seleccionado_id', type=int)

        # Validar que el tema está en un plan aprobado
        ts = TemaSeleccionado.query.get(tema_seleccionado_id)
        if not ts or not ts.plan or ts.plan.estado != 'APROBADO':
            flash('Debe seleccionar un tema de un plan aprobado.', 'warning')
            return redirect(url_for('ejecucion.nuevo'))

        fecha_inicio = datetime.strptime(request.form.get('fecha_inicio'), '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(request.form.get('fecha_fin'), '%Y-%m-%d').date()
        duracion_horas = request.form.get('duracion_horas', type=float)
        valor_sin_iva = request.form.get('valor_sin_iva', type=float)
        valor_con_iva = valor_sin_iva * 1.12  # IVA 12%
        proceso_contratacion = request.form.get('proceso_contratacion')
        centro_costo = request.form.get('centro_costo')
        empresa_id = request.form.get('empresa_id', type=int)
        tipo_certificacion = request.form.get('tipo_certificacion')
        observaciones = request.form.get('observaciones')
        participantes_data = request.form.get('participantes_json') # JSON con los participantes

        # Obtener datos del tema
        tema = ts.tema

        capacitacion = CapacitacionEjecutada(
            tema_seleccionado_id=tema_seleccionado_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            duracion_horas=duracion_horas,
            valor_sin_iva=valor_sin_iva,
            valor_con_iva=round(valor_con_iva, 2),
            proceso_contratacion=proceso_contratacion,
            centro_costo=centro_costo,
            empresa_id=empresa_id,
            tipo_certificacion=tipo_certificacion,
            observaciones=observaciones,
            estado='ACTIVO'
        )
        db.session.add(capacitacion)
        db.session.flush() # Para obtener capacitacion.id

        # Insertar participantes
        import json
        if participantes_data:
            try:
                lista_participantes = json.loads(participantes_data)
                for p in lista_participantes:
                    codigo = p.get('codigo')
                    
                    # Manejar subida de certificado PDF
                    ruta_cert = None
                    file = request.files.get(f'cert_pdf_{codigo}')
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        # Ensure static/uploads exists
                        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'certificados')
                        os.makedirs(upload_folder, exist_ok=True)
                        file_path = os.path.join(upload_folder, f"{capacitacion.id}_{codigo}_{filename}")
                        file.save(file_path)
                        ruta_cert = f"uploads/certificados/{capacitacion.id}_{codigo}_{filename}"

                    participante = Participante(
                        codigo=codigo,
                        nombres=p.get('nombres'),
                        cedula=p.get('cedula'),
                        cargo=p.get('cargo'),
                        ruta_certificado=ruta_cert,
                        capacitacion_id=capacitacion.id,
                        estado='ACTIVO'
                    )
                    db.session.add(participante)
            except Exception as e:
                db.session.rollback()
                flash('Error al procesar los participantes. Verifica los datos.', 'danger')
                return redirect(url_for('ejecucion.nuevo'))

        db.session.commit()

        flash('Capacitación ejecutada y participantes registrados exitosamente.', 'success')
        return redirect(url_for('ejecucion.lista'))

    # Obtener temas de planes aprobados
    temas_seleccionados = TemaSeleccionado.query.join(PlanCapacitacion).filter(
        PlanCapacitacion.estado == 'APROBADO',
        TemaSeleccionado.seleccionado == True
    ).all()
    
    tema_preseleccionado_id = request.args.get('tema_id', type=int)

    empresas = EmpresaCapacitadora.query.filter_by(estado='ACTIVO').order_by(EmpresaCapacitadora.razon_social).all()
    return render_template('ejecucion/nuevo.html', temas_seleccionados=temas_seleccionados, tema_preseleccionado_id=tema_preseleccionado_id, empresas=empresas)


@ejecucion_bp.route('/<int:capacitacion_id>')
@rol_required('ANALISTA')
def detalle(capacitacion_id):
    """Detalle de una capacitación ejecutada"""
    capacitacion = CapacitacionEjecutada.query.get_or_404(capacitacion_id)
    return render_template('ejecucion/detalle.html', capacitacion=capacitacion)


@ejecucion_bp.route('/<int:capacitacion_id>/participantes')
@rol_required('ANALISTA')
def participantes(capacitacion_id):
    """Gestión de participantes de una capacitación"""
    capacitacion = CapacitacionEjecutada.query.get_or_404(capacitacion_id)
    return render_template('ejecucion/participantes.html', capacitacion=capacitacion)


@ejecucion_bp.route('/<int:capacitacion_id>/participante/nuevo', methods=['POST'])
@rol_required('ANALISTA')
def agregar_participante(capacitacion_id):
    """Agregar un participante a la capacitación"""
    capacitacion = CapacitacionEjecutada.query.get_or_404(capacitacion_id)

    codigo = request.form.get('codigo')
    nombres = request.form.get('nombres')
    cedula = request.form.get('cedula')
    cargo = request.form.get('cargo')

    # Verificar que no exista otro participante con el mismo código en esta capacitación
    existente = Participante.query.filter_by(
        capacitacion_id=capacitacion_id,
        codigo=codigo
    ).first()

    if existente:
        flash('Ya existe un participante con ese código.', 'warning')
        return redirect(url_for('ejecucion.participantes', capacitacion_id=capacitacion_id))

    participante = Participante(
        codigo=codigo,
        nombres=nombres,
        cedula=cedula,
        cargo=cargo,
        capacitacion_id=capacitacion_id,
        estado='ACTIVO'
    )
    db.session.add(participante)
    db.session.commit()

    flash('Participante agregado.', 'success')
    return redirect(url_for('ejecucion.participantes', capacitacion_id=capacitacion_id))


@ejecucion_bp.route('/<int:capacitacion_id>/participante/<int:participante_id>/eliminar', methods=['POST'])
@rol_required('ANALISTA')
def eliminar_participante(capacitacion_id, participante_id):
    """Eliminar un participante"""
    participante = Participante.query.get_or_404(participante_id)
    participante.estado = 'ELIMINADO'
    db.session.commit()
    flash('Participante eliminado.', 'success')
    return redirect(url_for('ejecucion.participantes', capacitacion_id=capacitacion_id))


@ejecucion_bp.route('/<int:capacitacion_id>/participante/<int:participante_id>/subir-certificado', methods=['POST'])
@rol_required('ANALISTA', 'SECRETARIA')
def subir_certificado(capacitacion_id, participante_id):
    """Subir certificado de un participante"""
    participante = Participante.query.get_or_404(participante_id)

    if 'archivo' not in request.files:
        flash('No se seleccionó ningún archivo.', 'warning')
        return redirect(url_for('ejecucion.participantes', capacitacion_id=capacitacion_id))

    file = request.files['archivo']

    if file.filename == '':
        flash('No se seleccionó ningún archivo.', 'warning')
        return redirect(url_for('ejecucion.participantes', capacitacion_id=capacitacion_id))

    # Verificar extensión
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        flash('Tipo de archivo no permitido. Use PDF, PNG, JPG o JPEG.', 'danger')
        return redirect(url_for('ejecucion.participantes', capacitacion_id=capacitacion_id))

    # Guardar archivo
    filename = secure_filename(f"cert_{participante_id}_{file.filename}")
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Actualizar ruta en base de datos
    participante.ruta_certificado = filename
    db.session.commit()

    flash('Certificado subido exitosamente.', 'success')
    return redirect(url_for('ejecucion.participantes', capacitacion_id=capacitacion_id))


@ejecucion_bp.route('/descargar-certificado/<int:participante_id>')
@login_required
def descargar_certificado(participante_id):
    """Descargar el certificado de un participante"""
    participante = Participante.query.get_or_404(participante_id)

    if not participante.ruta_certificado:
        flash('Este participante no tiene certificado adjunto.', 'warning')
        return redirect(url_for('ejecucion.participantes', capacitacion_id=participante.capacitacion_id))

    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        participante.ruta_certificado,
        as_attachment=True
    )


@ejecucion_bp.route('/evaluar/<int:capacitacion_id>/<int:participante_id>', methods=['GET', 'POST'])
def evaluar(capacitacion_id, participante_id):
    """Formulario público para que el participante evalúe la capacitación y empresa"""
    capacitacion = CapacitacionEjecutada.query.get_or_404(capacitacion_id)
    participante = Participante.query.get_or_404(participante_id)

    # Validar que el participante pertenezca a esta capacitacion
    if participante.capacitacion_id != capacitacion_id:
        return "Acceso no autorizado", 403

    # Verificar si ya evaluó
    if participante.evaluacion:
        return render_template('ejecucion/evaluacion_gracias.html', mensaje="Usted ya ha enviado la evaluación para este curso. ¡Gracias!")

    if request.method == 'POST':
        calificacion_curso = request.form.get('calificacion_curso', type=int)
        calificacion_empresa = request.form.get('calificacion_empresa', type=int)
        comentarios = request.form.get('comentarios', '').strip()

        if not calificacion_curso or not calificacion_empresa:
            flash('Debe seleccionar todas las calificaciones.', 'danger')
            return redirect(url_for('ejecucion.evaluar', capacitacion_id=capacitacion_id, participante_id=participante_id))

        ev = EvaluacionCapacitacion(
            participante_id=participante_id,
            capacitacion_id=capacitacion_id,
            calificacion_curso=calificacion_curso,
            calificacion_empresa=calificacion_empresa,
            comentarios=comentarios
        )
        db.session.add(ev)
        db.session.commit()
        return render_template('ejecucion/evaluacion_gracias.html', mensaje="Evaluación guardada exitosamente. Sus respuestas nos ayudan a mejorar.")

    return render_template('ejecucion/evaluar.html', capacitacion=capacitacion, participante=participante)
