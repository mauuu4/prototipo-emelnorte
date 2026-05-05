"""
EMELNORTE - SIGEERN
Módulo de Gestión de Capacitación
Configuración de la aplicación Flask
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask import session

# Inicializar extensiones
db = SQLAlchemy()
csrf = CSRFProtect()

def create_app():
    """Factory function para crear la aplicación Flask"""

    app = Flask(__name__)

    # Configuración
    app.config['SECRET_KEY'] = 'emelnorte-capacitacion-secret-key-2026'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emelnorte_capacitacion.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'png', 'jpg', 'jpeg'}

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Inicializar extensiones
    db.init_app(app)
    csrf.init_app(app)

    # Registrar blueprints
    from routes.auth import auth_bp
    from routes.planes import planes_bp
    from routes.necesidades import necesidades_bp
    from routes.revision import revision_bp
    from routes.ejecucion import ejecucion_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(planes_bp)
    app.register_blueprint(necesidades_bp)
    app.register_blueprint(revision_bp)
    app.register_blueprint(ejecucion_bp)

    # Crear tablas y datos iniciales
    with app.app_context():
        db.create_all()
        from utils.data_init import inicializar_datos
        inicializar_datos()

    return app