# Routes package
from routes.auth import auth_bp
from routes.planes import planes_bp
from routes.necesidades import necesidades_bp
from routes.revision import revision_bp

__all__ = ['auth_bp', 'planes_bp', 'necesidades_bp', 'revision_bp']