"""
EMELNORTE - SIGEERN
Datos iniciales para el prototipo
"""

from config import db
from models import Direccion, Usuario, Empleado

def inicializar_datos():
    """Inicializa datos de prueba si la base está vacía"""

    if Usuario.query.count() > 0:
        # Aún si ya hay usuarios, seed empleados si faltan
        if Empleado.query.count() == 0:
            _seed_empleados()
        return

    print("\n" + "="*50)
    print("  Inicializando datos del prototipo...")
    print("="*50 + "\n")

    # ========================================
    # 1. DIRECCIONES
    # ========================================
    direcciones = [
        Direccion(id=1, nombre='Dirección Comercial',        abreviatura='DCO', max_temas=7),
        Direccion(id=2, nombre='Dirección de Distribución',  abreviatura='DDI', max_temas=7),
        Direccion(id=3, nombre='Dirección de Generación',    abreviatura='DGE', max_temas=5),
        Direccion(id=4, nombre='Dirección de TIC',           abreviatura='TIC', max_temas=5),
        Direccion(id=5, nombre='Dirección Financiera',       abreviatura='DFI', max_temas=5),
        Direccion(id=6, nombre='Dirección de Talento Humano',abreviatura='DTH', max_temas=5),
    ]

    for d in direcciones:
        db.session.add(d)
    db.session.flush()
    print("  [OK] Direcciones creadas")

    # ========================================
    # 2. USUARIOS
    # ========================================
    usuarios = [
        # ANALISTA - Crea el plan, selecciona temas, envía a revisión
        Usuario(
            id=1,
            nombre='Analista Talento Humano',
            cedula='1712345678',
            correo='analista.th@emelnorte.ec',
            rol='ANALISTA',
            direccion_id=6
        ),
        # DIRECTORES DE AREA - Registran necesidades de capacitación
        Usuario(
            id=2,
            nombre='Director Comercial',
            cedula='1723456789',
            correo='director.comercial@emelnorte.ec',
            rol='DIRECTOR',
            direccion_id=1   # DCO - max 7 temas
        ),
        Usuario(
            id=3,
            nombre='Director de Distribución',
            cedula='1734567890',
            correo='director.distribucion@emelnorte.ec',
            rol='DIRECTOR',
            direccion_id=2   # DDI - max 7 temas
        ),
        Usuario(
            id=4,
            nombre='Director de Generación',
            cedula='1745678901',
            correo='director.generacion@emelnorte.ec',
            rol='DIRECTOR',
            direccion_id=3   # DGE - max 5 temas
        ),
        Usuario(
            id=5,
            nombre='Director de TIC',
            cedula='1756111222',
            correo='director.tic@emelnorte.ec',
            rol='DIRECTOR',
            direccion_id=4   # TIC - max 5 temas
        ),
        Usuario(
            id=6,
            nombre='Director Financiero',
            cedula='1756222333',
            correo='director.financiero@emelnorte.ec',
            rol='DIRECTOR',
            direccion_id=5   # DFI - max 5 temas
        ),
        # DIRECTOR DE TH - Revisa el plan aprobado por Jefe y lo envía al Presidente (RN-08)
        Usuario(
            id=7,
            nombre='Director de Talento Humano',
            cedula='1767890123',
            correo='director.th@emelnorte.ec',
            rol='DIRECTOR',
            direccion_id=6   # DTH - id=6, es_director_th() = True
        ),
        # JEFE DE PERSONAL - Revisa y aprueba/devuelve el plan (RN-07)
        Usuario(
            id=8,
            nombre='Jefe de Personal',
            cedula='1756789012',
            correo='jefe.personal@emelnorte.ec',
            rol='JEFE_PERSONAL',
            direccion_id=6
        ),
        # PRESIDENTE - Aprobación final (RN-09)
        Usuario(
            id=9,
            nombre='Presidente Ejecutivo',
            cedula='1778901234',
            correo='presidente@emelnorte.ec',
            rol='PRESIDENTE',
            direccion_id=None
        ),
    ]

    for u in usuarios:
        db.session.add(u)
    db.session.flush()
    print("  [OK] Usuarios creados")

    db.session.commit()

    # ========================================
    # 3. EMPLEADOS (nómina de ejemplo)
    # ========================================
    _seed_empleados()

    # ========================================
    # 4. ESCENARIO PLAN 2025 COMPLETO
    # ========================================
    _seed_plan_2025()

    print("  [OK] Datos inicializados correctamente")
    print("="*50 + "\n")
    print("\n  USUARIOS PARA PRUEBA:")
    print("  " + "-" * 28)
    print("  1. Analista Talento Humano      ANALISTA       - Crea planes, selecciona temas")
    print("  2. Director Comercial           DIRECTOR(DCO)  - Registra necesidades (max 7)")
    print("  3. Director de Distribucion     DIRECTOR(DDI)  - Registra necesidades (max 7)")
    print("  4. Director Administrativo      DIRECTOR(DAD)  - Registra necesidades (max 5)")
    print("  5. Director de Operaciones      DIRECTOR(DOP)  - Registra necesidades (max 5)")
    print("  6. Director Financiero          DIRECTOR(DFI)  - Registra necesidades (max 5)")
    print("  7. Director de Talento Humano   DIRECTOR(DTH)  - Revisa plan, envia al Presidente")
    print("  8. Jefe de Personal             JEFE_PERSONAL  - Revisa/aprueba/devuelve plan")
    print("  9. Presidente Ejecutivo         PRESIDENTE     - Aprobacion final")
    print("\n")


def _seed_empleados():
    if Empleado.query.count() > 0:
        return
        
    empleados = [
        Empleado(codigo='EMP-001', nombres='Carlos Alberto Andrade Pérez', cedula='1001234567', cargo='Técnico Electricista', direccion='Dirección de Distribuchión'),
        Empleado(codigo='EMP-002', nombres='María Elena Suárez López', cedula='1002345678', cargo='Asistente Administrativa', direccion='Dirección Administrativa'),
        Empleado(codigo='EMP-003', nombres='Juan Pablo Rosero Castro', cedula='1003456789', cargo='Ingeniero Eléctrico', direccion='Dirección de Operaciones'),
        Empleado(codigo='EMP-004', nombres='Ana Lucia Fierro Medina', cedula='1004567890', cargo='Contadora', direccion='Dirección Financiera'),
        Empleado(codigo='EMP-005', nombres='Roberto Iván Mora Salazar', cedula='1005678901', cargo='Recaudador', direccion='Dirección Comercial'),
        Empleado(codigo='EMP-006', nombres='Gabriela Paola Vega Torres', cedula='1006789012', cargo='Analista de Sistemas', direccion='Dirección de Talento Humano'),
        Empleado(codigo='EMP-007', nombres='Diego Fernando Puente Almeida', cedula='1007890123', cargo='Técnico de Mantenimiento', direccion='Dirección de Distribuchión'),
        Empleado(codigo='EMP-008', nombres='Patricia Ximena Chávez Ruiz', cedula='1008901234', cargo='Secretaria Ejecutiva', direccion='Dirección Administrativa'),
        Empleado(codigo='EMP-009', nombres='Fernando Alejandro Borja Paz', cedula='1009012345', cargo='Liniero', direccion='Dirección de Operaciones'),
        Empleado(codigo='EMP-010', nombres='Verónica Susana Lima Gallegos', cedula='1010123456', cargo='Auditora Interna', direccion='Dirección Financiera'),
    ]
    for e in empleados:
        db.session.add(e)
    db.session.commit()
    print("  [OK] Empleados creados")


def _seed_plan_2025():
    from models import PlanCapacitacion, TemaCapacitacion, TemaSeleccionado, ObservacionPlan, CapacitacionEjecutada, Participante, Empleado, EmpresaCapacitadora, EvaluacionCapacitacion
    from datetime import date, timedelta
    import random
    
    if PlanCapacitacion.query.count() > 0:
        return
        
    print("  Creando escenario: Plan 2025 Masivo...")
    
    # 1. Crear el Plan
    plan = PlanCapacitacion(
        anio=2025,
        monto_referencial=100000.0,
        monto_aprobado=95000.0,
        estado='APROBADO',
        creado_por_id=1
    )
    db.session.add(plan)
    db.session.flush()
    
    # Mapeo de (director_user_id, num_temas, prefijo_nombre)
    config_temas = [
        (2, 7, 'Comercialización'), # Comercial
        (3, 7, 'Distribución'), # Distribucion
        (4, 5, 'Generación'), # Generacion
        (5, 5, 'Tecnología y Sistemas'), # TIC
        (6, 5, 'Finanzas y Presupuesto'), # Financiera
        (7, 5, 'Talento Humano') # TH
    ]
    
    temas = []
    
    # 2. Temas de directores
    for dir_id, num, prefix in config_temas:
        for i in range(num):
            t = TemaCapacitacion(
                nombre=f'Capacitación en {prefix} Nivel {i+1}',
                num_participantes=random.randint(5, 20),
                modalidad=random.choice(['VIRTUAL', 'PRESENCIAL', 'MIXTO']),
                horas=random.randint(10, 80),
                presupuesto_referencial=random.uniform(500, 3000),
                mes_ejecucion=random.randint(1, 12),
                usuario_id=dir_id,
                plan_id=plan.id
            )
            temas.append(t)
            
    # 3. Temas del analista (2 extras)
    for i in range(2):
        t = TemaCapacitacion(
            nombre=f'Curso General de Integración Corporativa {i+1}',
            num_participantes=50, modalidad='MIXTO', horas=20,
            presupuesto_referencial=2000.0, mes_ejecucion=1,
            usuario_id=1, plan_id=plan.id, es_del_analista=True
        )
        temas.append(t)
        
    for t in temas:
        db.session.add(t)
    db.session.flush()
    
    # 4. Seleccion (Selecciona ~85%, descarta ~15%)
    selecciones = []
    aprobados_count = 0
    for idx, t in enumerate(temas):
        # Descartar algunos aleatoriamente, pero no los del analista
        if t.es_del_analista or random.random() > 0.15:
            ts = TemaSeleccionado(tema_id=t.id, plan_id=plan.id, seleccionado=True, presupuesto_aprobado=t.presupuesto_referencial * 0.95, observaciones='Aprobado según POA')
            aprobados_count += 1
        else:
            ts = TemaSeleccionado(tema_id=t.id, plan_id=plan.id, seleccionado=False, presupuesto_aprobado=0.0, observaciones='Descartado por límite de presupuesto')
        selecciones.append(ts)
        
    for ts in selecciones:
        db.session.add(ts)
    db.session.flush()
    
    # 5. Observaciones
    obs = [
        ObservacionPlan(observacion='Plan revisado y ajustado conforme al presupuesto.', autor='Jefe de Personal', tipo_observacion='APROBACION', plan_id=plan.id),
        ObservacionPlan(observacion='Visto bueno para presidencia.', autor='Director de Talento Humano', tipo_observacion='APROBACION', plan_id=plan.id),
        ObservacionPlan(observacion='Plan Anual 2025 Aprobado.', autor='Presidente Ejecutivo', tipo_observacion='APROBACION', plan_id=plan.id),
    ]
    for o in obs:
        db.session.add(o)
    db.session.flush()
    
    # 5.5 Empresas Capacitadoras
    empresas = [
        EmpresaCapacitadora(ruc='1001001001001', razon_social='Escuela de Negocios y Liderazgo S.A.', especialidad='Habilidades Blandas'),
        EmpresaCapacitadora(ruc='2002002002001', razon_social='Instituto Técnico Energético Nacional', especialidad='Técnica / Electricidad'),
        EmpresaCapacitadora(ruc='3003003003001', razon_social='Soluciones TI Avanzadas CIA LTDA', especialidad='Tecnología'),
        EmpresaCapacitadora(ruc='4004004004001', razon_social='Centro de Capacitación Integral (CCI)', especialidad='Seguridad Integral'),
    ]
    for emp in empresas:
        db.session.add(emp)
    db.session.flush()

    # 6. Ejecuciones (60% de los seleccionados)
    temas_aprobados = [ts for ts in selecciones if ts.seleccionado]
    num_ejecuciones = int(len(temas_aprobados) * 0.60)
    
    ejecuciones = []
    base_date = date(2025, 1, 15)
    
    for i in range(num_ejecuciones):
        ts = temas_aprobados[i]
        d_start = base_date + timedelta(days=i*5)
        d_end = d_start + timedelta(days=3)
        ej = CapacitacionEjecutada(
            tema_seleccionado_id=ts.id,
            fecha_inicio=d_start, fecha_fin=d_end,
            duracion_horas=ts.tema.horas,
            valor_sin_iva=ts.presupuesto_aprobado,
            valor_con_iva=ts.presupuesto_aprobado * 1.12,
            proceso_contratacion=random.choice(['Ínfima Cuantía', 'Subasta Inversa', 'Contratación Directa']),
            centro_costo=f'CC-2025-{i+1}',
            empresa_id=random.choice(empresas).id,
            tipo_certificacion=f'Tipo {random.randint(1,2)}',
            observaciones='Ejecutada exitosamente.'
        )
        db.session.add(ej)
        ejecuciones.append(ej)
    db.session.flush()
    
    # Participantes para las ejecuciones y Evaluaciones
    emps = Empleado.query.all()
    if emps:
        for ej in ejecuciones:
            k = min(len(emps), random.randint(3, 8))
            participantes_ej = random.sample(emps, k)
            for e in participantes_ej:
                p = Participante(codigo=e.codigo, nombres=e.nombres, cedula=e.cedula, cargo=e.cargo, capacitacion_id=ej.id)
                db.session.add(p)
                db.session.flush()

                # Generar evaluación aleatoria para el participante (80% de probabilidad de que haya evaluado)
                if random.random() > 0.2:
                    ev = EvaluacionCapacitacion(
                        participante_id=p.id,
                        capacitacion_id=ej.id,
                        calificacion_curso=random.randint(3, 5),
                        calificacion_empresa=random.randint(3, 5),
                        comentarios='Buena capacitación.' if random.random() > 0.5 else 'Podría mejorar el material de apoyo.'
                    )
                    db.session.add(ev)

    db.session.commit()
    print(f"  [OK] Escenario masivo 2025 completado: {len(temas)} temas creados, {aprobados_count} aprobados, {num_ejecuciones} ejecutados.")

