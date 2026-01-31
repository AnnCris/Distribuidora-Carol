import re
from functools import wraps
from flask import jsonify, request

def validate_required_fields(required_fields):
    """Validar campos requeridos en el request"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No se enviaron datos'}), 400
            
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            
            if missing_fields:
                return jsonify({
                    'error': 'Campos requeridos faltantes',
                    'campos': missing_fields
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_celular(celular):
    """Validar formato de celular boliviano"""
    if not celular:
        return True
    
    # Formato: 7XXXXXXX o 6XXXXXXX (8 dígitos)
    pattern = r'^[67]\d{7}$'
    return bool(re.match(pattern, celular))

def validate_precio(precio):
    """Validar que el precio sea positivo"""
    try:
        precio_float = float(precio)
        return precio_float > 0
    except (ValueError, TypeError):
        return False

def validate_cantidad(cantidad):
    """Validar que la cantidad sea positiva"""
    try:
        cantidad_float = float(cantidad)
        return cantidad_float > 0
    except (ValueError, TypeError):
        return False
    

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