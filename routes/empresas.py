"""
EMELNORTE - SIGEERN
Rutas de Empresas Capacitadoras
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import EmpresaCapacitadora
from routes.auth import rol_required
from config import db

empresas_bp = Blueprint('empresas', __name__, url_prefix='/empresas')

@empresas_bp.route('/')
@rol_required('ANALISTA')
def lista():
    """Lista de empresas capacitadoras"""
    empresas = EmpresaCapacitadora.query.filter_by(estado='ACTIVO').order_by(EmpresaCapacitadora.razon_social).all()
    return render_template('empresas/lista.html', empresas=empresas)


@empresas_bp.route('/nuevo', methods=['POST'])
@rol_required('ANALISTA')
def nuevo():
    """Registrar una nueva empresa"""
    ruc = request.form.get('ruc', '').strip()
    razon_social = request.form.get('razon_social', '').strip()
    contacto_nombre = request.form.get('contacto_nombre', '').strip()
    contacto_telefono = request.form.get('contacto_telefono', '').strip()
    correo = request.form.get('correo', '').strip()
    especialidad = request.form.get('especialidad', '').strip()

    if not ruc or not razon_social:
        flash('RUC y Razón Social son obligatorios.', 'danger')
        return redirect(url_for('empresas.lista'))

    existente = EmpresaCapacitadora.query.filter_by(ruc=ruc).first()
    if existente:
        if existente.estado == 'ELIMINADO':
            existente.estado = 'ACTIVO'
            existente.razon_social = razon_social
            existente.contacto_nombre = contacto_nombre
            existente.contacto_telefono = contacto_telefono
            existente.correo = correo
            existente.especialidad = especialidad
            db.session.commit()
            flash('Empresa reactivada y actualizada exitosamente.', 'success')
            return redirect(url_for('empresas.lista'))
            
        flash('Ya existe una empresa registrada con ese RUC.', 'warning')
        return redirect(url_for('empresas.lista'))

    empresa = EmpresaCapacitadora(
        ruc=ruc,
        razon_social=razon_social,
        contacto_nombre=contacto_nombre,
        contacto_telefono=contacto_telefono,
        correo=correo,
        especialidad=especialidad
    )
    db.session.add(empresa)
    db.session.commit()

    flash('Empresa capacitadora registrada exitosamente.', 'success')
    return redirect(url_for('empresas.lista'))


@empresas_bp.route('/<int:empresa_id>/editar', methods=['POST'])
@rol_required('ANALISTA')
def editar(empresa_id):
    """Editar datos de una empresa"""
    empresa = EmpresaCapacitadora.query.get_or_404(empresa_id)

    ruc = request.form.get('ruc', '').strip()
    razon_social = request.form.get('razon_social', '').strip()

    if not ruc or not razon_social:
        flash('RUC y Razón Social son obligatorios.', 'danger')
        return redirect(url_for('empresas.lista'))

    # Check if RUC belongs to another company
    otra = EmpresaCapacitadora.query.filter(EmpresaCapacitadora.ruc == ruc, EmpresaCapacitadora.id != empresa.id).first()
    if otra:
        flash('El RUC ingresado pertenece a otra empresa.', 'danger')
        return redirect(url_for('empresas.lista'))

    empresa.ruc = ruc
    empresa.razon_social = razon_social
    empresa.contacto_nombre = request.form.get('contacto_nombre', '').strip()
    empresa.contacto_telefono = request.form.get('contacto_telefono', '').strip()
    empresa.correo = request.form.get('correo', '').strip()
    empresa.especialidad = request.form.get('especialidad', '').strip()

    db.session.commit()
    flash('Empresa actualizada correctamente.', 'success')
    return redirect(url_for('empresas.lista'))


@empresas_bp.route('/<int:empresa_id>/eliminar', methods=['POST'])
@rol_required('ANALISTA')
def eliminar(empresa_id):
    """Dar de baja una empresa"""
    empresa = EmpresaCapacitadora.query.get_or_404(empresa_id)
    empresa.estado = 'ELIMINADO'
    db.session.commit()
    flash('Empresa eliminada.', 'success')
    return redirect(url_for('empresas.lista'))
