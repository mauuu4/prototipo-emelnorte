"""
EMELNORTE - SIGEERN
Rutas del Portal del Empleado (Autogestión)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import Usuario, Participante, EvaluacionCapacitacion, CapacitacionEjecutada
from routes.auth import login_required, get_usuario_actual, rol_required
from config import db

empleado_bp = Blueprint('empleado', __name__, url_prefix='/empleado')


@empleado_bp.route('/perfil')
@login_required
@rol_required('EMPLEADO')
def perfil():
    usuario = get_usuario_actual()
    
    # Obtener todas las participaciones de este empleado usando su cédula
    participaciones = Participante.query.filter_by(cedula=usuario.cedula, estado='ACTIVO').all()
    
    # Separar historial y encuestas pendientes
    historial = []
    pendientes_eval = []
    
    for p in participaciones:
        cap = p.capacitacion
        if cap:
            # Buscar si ya evaluó
            evaluacion = EvaluacionCapacitacion.query.filter_by(participante_id=p.id, capacitacion_id=cap.id).first()
            
            item = {
                'participacion': p,
                'capacitacion': cap,
                'tema_nombre': cap.get_nombre_tema(),
                'empresa': cap.empresa.razon_social if cap.empresa else 'Interna',
                'evaluacion': evaluacion
            }
            
            historial.append(item)
            
            if not evaluacion and cap.estado in ['FINALIZADO', 'ACTIVO']:
                pendientes_eval.append(item)
                
    # Ordenar historial por fecha de inicio descendente
    historial.sort(key=lambda x: x['capacitacion'].fecha_inicio, reverse=True)

    return render_template('empleado/perfil.html', 
                           usuario=usuario, 
                           historial=historial,
                           pendientes_eval=pendientes_eval)


@empleado_bp.route('/evaluar', methods=['POST'])
@login_required
@rol_required('EMPLEADO')
def evaluar():
    participante_id = request.form.get('participante_id', type=int)
    capacitacion_id = request.form.get('capacitacion_id', type=int)
    calificacion_curso = request.form.get('calificacion_curso', type=int)
    calificacion_empresa = request.form.get('calificacion_empresa', type=int)
    comentarios = request.form.get('comentarios', '')

    if not all([participante_id, capacitacion_id, calificacion_curso, calificacion_empresa]):
        flash('Debe completar todas las calificaciones de estrellas.', 'danger')
        return redirect(url_for('empleado.perfil'))

    # Verificar que el participante sea de este usuario
    usuario = get_usuario_actual()
    part = Participante.query.get_or_404(participante_id)
    if part.cedula != usuario.cedula:
        flash('Error de seguridad.', 'danger')
        return redirect(url_for('empleado.perfil'))

    nueva_eval = EvaluacionCapacitacion(
        participante_id=participante_id,
        capacitacion_id=capacitacion_id,
        calificacion_curso=calificacion_curso,
        calificacion_empresa=calificacion_empresa,
        comentarios=comentarios
    )
    db.session.add(nueva_eval)
    db.session.commit()
    
    flash('¡Gracias por evaluar la capacitación! Su retroalimentación es muy valiosa.', 'success')
    return redirect(url_for('empleado.perfil'))


@empleado_bp.route('/descargar_certificado/<int:participante_id>')
@login_required
@rol_required('EMPLEADO')
def descargar_certificado(participante_id):
    # Simulacion de descarga de certificado
    usuario = get_usuario_actual()
    part = Participante.query.get_or_404(participante_id)
    
    if part.cedula != usuario.cedula:
        flash('No tiene permisos para descargar este certificado.', 'danger')
        return redirect(url_for('empleado.perfil'))
        
    flash(f'Simulando la descarga del certificado PDF para "{part.capacitacion.get_nombre_tema()}"...', 'info')
    return redirect(url_for('empleado.perfil'))
