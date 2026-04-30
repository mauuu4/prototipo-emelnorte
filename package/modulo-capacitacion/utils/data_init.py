"""
EMELNORTE - SIGEERN
Datos iniciales para el prototipo
"""

from config import db
from models import Direccion, Usuario, PlanCapacitacion, TemaCapacitacion, TemaSeleccionado


def inicializar_datos():
    """Inicializa datos de prueba si la base está vacía"""

    # Verificar si ya existen datos
    if Usuario.query.count() > 0:
        return

    print("\n" + "="*50)
    print("  Inicializando datos del prototipo...")
    print("="*50 + "\n")

    # ========================================
    # 1. DIRECCIONES
    # ========================================
    direcciones = [
        Direccion(id=1, nombre='Dirección Comercial', abreviatura='DCO', max_temas=7),
        Direccion(id=2, nombre='Dirección de Distribución', abreviatura='DDO', max_temas=7),
        Direccion(id=3, nombre='Dirección Administrativa', abreviatura='DAD', max_temas=5),
        Direccion(id=4, nombre='Dirección de Operaciones', abreviatura='DOP', max_temas=5),
        Direccion(id=5, nombre='Dirección Financiera', abreviatura='DFI', max_temas=5),
        Direccion(id=6, nombre='Talento Humano', abreviatura='DTH', max_temas=5),
    ]

    for d in direcciones:
        db.session.add(d)

    db.session.flush()
    print("  ✓ Direcciones creadas")

    # ========================================
    # 2. USUARIOS
    # ========================================
    usuarios = [
        Usuario(
            id=1,
            nombre='Ana López',
            cedula='1712345678',
            correo='ana.lopez@emelnorte.ec',
            rol='ANALISTA',
            direccion_id=6
        ),
        Usuario(
            id=2,
            nombre='Carlos Mendoza',
            cedula='1723456789',
            correo='carlos.mendoza@emelnorte.ec',
            rol='DIRECTOR',
            direccion_id=1  # DCO
        ),
        Usuario(
            id=3,
            nombre='María García',
            cedula='1734567890',
            correo='maria.garcia@emelnorte.ec',
            rol='DIRECTOR',
            direccion_id=2  # DDO
        ),
        Usuario(
            id=4,
            nombre='Pedro Sánchez',
            cedula='1745678901',
            correo='pedro.sanchez@emelnorte.ec',
            rol='DIRECTOR',
            direccion_id=3  # DAD
        ),
        Usuario(
            id=5,
            nombre='Laura Torres',
            cedula='1756789012',
            correo='laura.torres@emelnorte.ec',
            rol='JEFE_PERSONAL',
            direccion_id=6
        ),
        Usuario(
            id=6,
            nombre='Roberto Díaz',
            cedula='1767890123',
            correo='roberto.diaz@emelnorte.ec',
            rol='PRESIDENTE',
            direccion_id=None
        ),
    ]

    for u in usuarios:
        db.session.add(u)

    db.session.flush()
    print("  ✓ Usuarios creados")

    # ========================================
    # 3. PLAN DE CAPACITACIÓN 2026 (Borrador)
    # ========================================
    plan = PlanCapacitacion(
        id=1,
        anio=2026,
        monto_referencial=50000.00,
        estado='BORRADOR',
        direccion_id=6
    )
    db.session.add(plan)
    db.session.flush()
    print("  ✓ Plan de Capacitación 2026 creado")

    # ========================================
    # 4. TEMAS DE CAPACITACIÓN DE EJEMPLO
    # ========================================
    temas_ejemplo = [
        # Temas del Director de Comercial (DCO)
        TemaCapacitacion(
            nombre='Excel Avanzado para Análisis de Datos',
            etapa_funcional='Administración y Gestión',
            subetapa_funcional='Gestión Administrativa',
            num_participantes=15,
            modalidad='PRESENCIAL',
            horas=40,
            presupuesto_referencial=2500.00,
            mes_ejecucion=3,
            usuario_id=2,  # Carlos Mendoza - Director DCO
            plan_id=1
        ),
        TemaCapacitacion(
            nombre='Gestión de Proyectos con Metodología Ágil',
            etapa_funcional='Desarrollo y Planificación',
            subetapa_funcional='Gestión de Proyectos',
            num_participantes=10,
            modalidad='VIRTUAL',
            horas=30,
            presupuesto_referencial=3500.00,
            mes_ejecucion=4,
            usuario_id=2,
            plan_id=1
        ),
        # Temas del Director de Distribución (DDO)
        TemaCapacitacion(
            nombre='Seguridad en Instalaciones Eléctricas',
            etapa_funcional='Seguridad y Salud Ocupacional',
            subetapa_funcional='Prevención de Riesgos',
            num_participantes=20,
            modalidad='PRESENCIAL',
            horas=20,
            presupuesto_referencial=1800.00,
            mes_ejecucion=5,
            usuario_id=3,  # María García - Director DDO
            plan_id=1
        ),
        TemaCapacitacion(
            nombre='Atención al Cliente Telefónico',
            etapa_funcional='Comercialización',
            subetapa_funcional='Atención al Cliente',
            num_participantes=25,
            modalidad='MIXTO',
            horas=24,
            presupuesto_referencial=1200.00,
            mes_ejecucion=3,
            usuario_id=3,
            plan_id=1
        ),
        # Temas del Director Administrativo (DAD)
        TemaCapacitacion(
            nombre='Mantenimiento de Transformadores de Distribución',
            etapa_funcional='Operación y Mantenimiento',
            subetapa_funcional='Mantenimiento Preventivo',
            num_participantes=8,
            modalidad='PRESENCIAL',
            horas=48,
            presupuesto_referencial=4500.00,
            mes_ejecucion=6,
            usuario_id=4,  # Pedro Sánchez - Director DAD
            plan_id=1
        ),
    ]

    for tema in temas_ejemplo:
        db.session.add(tema)

    db.session.flush()
    print("  ✓ Temas de ejemplo creados")

    # ========================================
    # 5. TEMAS SELECCIONADOS (seleccionados por Analista)
    # ========================================
    temas_seleccionados = [
        # Excel - seleccionado
        TemaSeleccionado(tema_id=1, plan_id=1, seleccionado=True, presupuesto_aprobado=2500.00),
        # Gestión de Proyectos - seleccionado
        TemaSeleccionado(tema_id=2, plan_id=1, seleccionado=True, presupuesto_aprobado=3000.00),
        # Seguridad - seleccionado
        TemaSeleccionado(tema_id=3, plan_id=1, seleccionado=True, presupuesto_aprobado=1800.00),
        # Atención al Cliente - NO seleccionado
        TemaSeleccionado(tema_id=4, plan_id=1, seleccionado=False),
        # Mantenimiento Transformadores - seleccionado
        TemaSeleccionado(tema_id=5, plan_id=1, seleccionado=True, presupuesto_aprobado=4500.00),
    ]

    for ts in temas_seleccionados:
        db.session.add(ts)

    print("  ✓ Temas seleccionados configurados")

    # ========================================
    # 6. PLAN 2025 (Aprobado - para referencia)
    # ========================================
    plan_2025 = PlanCapacitacion(
        id=2,
        anio=2025,
        monto_referencial=45000.00,
        monto_aprobado=42000.00,
        estado='APROBADO',
        direccion_id=6
    )
    db.session.add(plan_2025)
    print("  ✓ Plan de Capacitación 2025 (aprobado) creado")

    # Commit final
    db.session.commit()

    print("\n" + "="*50)
    print("  ✓ Datos inicializados correctamente")
    print("="*50 + "\n")

    print("\n  USUARIOS PARA PRUEBA:")
    print("  ─" * 30)
    print("  1. Ana López     - ANALISTA        - ve todo, crea planes")
    print("  2. Carlos Mendoza - DIRECTOR (DCO)  - registra necesidades")
    print("  3. María García  - DIRECTOR (DDO)   - registra necesidades")
    print("  4. Pedro Sánchez  - DIRECTOR (DAD)   - registra necesidades")
    print("  5. Laura Torres   - JEFE_PERSONAL    - revisa y aprueba")
    print("  6. Roberto Díaz   - PRESIDENTE       - aprobación final")
    print("\n")