from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models.usuario import Usuario

def admin_required():
    """Decorador para requerir rol de administrador"""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            user_id = get_jwt_identity()
            user = Usuario.query.get(user_id)
            
            if not user:
                return jsonify({'error': 'Usuario no encontrado'}), 404
            
            if user.rol != 'admin':
                return jsonify({'error': 'Acceso denegado. Se requiere rol de administrador'}), 403
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper


def vendedor_o_admin_required():
    """Decorador para requerir rol de vendedor o administrador"""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            user_id = get_jwt_identity()
            user = Usuario.query.get(user_id)
            
            if not user:
                return jsonify({'error': 'Usuario no encontrado'}), 404
            
            if user.rol not in ['admin', 'vendedor']:
                return jsonify({'error': 'Acceso denegado'}), 403
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper