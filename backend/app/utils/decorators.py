from functools import wraps
from flask import jsonify, session
from app.models.usuario import Usuario

def login_required(f):
    """Decorador para requerir autenticación con sesiones"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'No autorizado - Inicie sesión'}), 401
        
        # Verificar que el usuario existe
        user = Usuario.query.get(user_id)
        if not user or not user.activo:
            session.clear()
            return jsonify({'error': 'Usuario inválido'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorador para requerir rol de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'No autorizado'}), 401
        
        user = Usuario.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        if user.rol != 'admin':
            return jsonify({'error': 'Acceso denegado. Se requiere rol de administrador'}), 403
        
        return f(*args, **kwargs)
    return decorated_function