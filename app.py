"""
EMELNORTE - SIGEERN
Módulo de Gestión de Capacitación
Punto de entrada de la aplicación
"""

from config import create_app

app = create_app()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  EMELNORTE - SIGEERN")
    print("  Módulo de Gestión de Capacitación")
    print("  Prototipo v1.0")
    print("="*60)
    print("\n  Servidor iniciado en: http://localhost:5000")
    print("  Presiona Ctrl+C para detener\n")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)