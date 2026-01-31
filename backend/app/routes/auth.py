from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.database import db, get_bolivia_time
from app.models.usuario import Usuario
from app.utils.validators import validate_required_fields

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
@validate_required_fields(['usuario', 'password'])
def login():
    """Iniciar sesión y obtener token JWT"""
    try:
        data = request.get_json()
        usuario = data.get('usuario')
        password = data.get('password')
        
        # Buscar usuario
        user = Usuario.query.filter_by(usuario=usuario).first()
        
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Verificar si está activo
        if not user.activo:
            return jsonify({'error': 'Usuario desactivado. Contacte al administrador'}), 403
        
        # Verificar contraseña
        if not user.check_password(password):
            return jsonify({'error': 'Contraseña incorrecta'}), 401
        
        # Actualizar último acceso
        user.ultimo_acceso = get_bolivia_time()
        db.session.commit()
        
        # Crear token JWT
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'mensaje': 'Inicio de sesión exitoso',
            'token': access_token,
            'usuario': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al iniciar sesión: {str(e)}'}), 500


@auth_bp.route('/perfil', methods=['GET'])
@jwt_required()
def obtener_perfil():
    """Obtener información del usuario autenticado"""
    try:
        user_id = get_jwt_identity()
        user = Usuario.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        return jsonify({
            'usuario': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener perfil: {str(e)}'}), 500


@auth_bp.route('/cambiar-password', methods=['PUT'])
@jwt_required()
@validate_required_fields(['password_actual', 'password_nueva'])
def cambiar_password():
    """Cambiar contraseña del usuario autenticado"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        password_actual = data.get('password_actual')
        password_nueva = data.get('password_nueva')
        
        # Validar longitud de nueva contraseña
        if len(password_nueva) < 6:
            return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
        
        user = Usuario.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Verificar contraseña actual
        if not user.check_password(password_actual):
            return jsonify({'error': 'Contraseña actual incorrecta'}), 401
        
        # Cambiar contraseña
        user.set_password(password_nueva)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Contraseña cambiada exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al cambiar contraseña: {str(e)}'}), 500


@auth_bp.route('/validar-token', methods=['GET'])
@jwt_required()
def validar_token():
    """Validar si el token JWT es válido"""
    try:
        user_id = get_jwt_identity()
        user = Usuario.query.get(user_id)
        
        if not user or not user.activo:
            return jsonify({'valido': False, 'error': 'Token inválido'}), 401
        
        return jsonify({
            'valido': True,
            'usuario': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'valido': False, 'error': str(e)}), 401