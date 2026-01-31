from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import db
from app.models.usuario import Usuario
from app.utils.validators import validate_required_fields
from app.utils.decorators import admin_required

usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/', methods=['GET'])
@jwt_required()
def listar_usuarios():
    """Listar todos los usuarios"""
    try:
        # Parámetros de filtrado
        activo = request.args.get('activo')
        rol = request.args.get('rol')
        
        query = Usuario.query
        
        # Filtros
        if activo is not None:
            query = query.filter_by(activo=activo.lower() == 'true')
        
        if rol:
            query = query.filter_by(rol=rol)
        
        usuarios = query.order_by(Usuario.nombre_completo).all()
        
        return jsonify({
            'usuarios': [usuario.to_dict() for usuario in usuarios],
            'total': len(usuarios)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al listar usuarios: {str(e)}'}), 500


@usuarios_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def obtener_usuario(id):
    """Obtener un usuario por ID"""
    try:
        usuario = Usuario.query.get(id)
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        return jsonify({'usuario': usuario.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener usuario: {str(e)}'}), 500


@usuarios_bp.route('/', methods=['POST'])
@jwt_required()
@admin_required()
@validate_required_fields(['nombre_completo', 'usuario', 'password', 'rol'])
def crear_usuario():
    """Crear un nuevo usuario (solo admin)"""
    try:
        data = request.get_json()
        
        # Validar que el usuario no exista
        usuario_existente = Usuario.query.filter_by(usuario=data['usuario']).first()
        if usuario_existente:
            return jsonify({'error': 'El nombre de usuario ya está en uso'}), 400
        
        # Validar longitud de contraseña
        if len(data['password']) < 6:
            return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
        
        # Validar rol
        if data['rol'] not in ['admin', 'vendedor']:
            return jsonify({'error': 'Rol inválido. Debe ser admin o vendedor'}), 400
        
        # Crear usuario
        nuevo_usuario = Usuario(
            nombre_completo=data['nombre_completo'],
            usuario=data['usuario'],
            rol=data['rol']
        )
        nuevo_usuario.set_password(data['password'])
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Usuario creado exitosamente',
            'usuario': nuevo_usuario.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear usuario: {str(e)}'}), 500


@usuarios_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@admin_required()
def actualizar_usuario(id):
    """Actualizar un usuario (solo admin)"""
    try:
        usuario = Usuario.query.get(id)
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        
        # Actualizar campos
        if 'nombre_completo' in data:
            usuario.nombre_completo = data['nombre_completo']
        
        if 'usuario' in data:
            # Verificar que el nuevo nombre de usuario no exista
            usuario_existente = Usuario.query.filter(
                Usuario.usuario == data['usuario'],
                Usuario.id != id
            ).first()
            
            if usuario_existente:
                return jsonify({'error': 'El nombre de usuario ya está en uso'}), 400
            
            usuario.usuario = data['usuario']
        
        if 'rol' in data:
            if data['rol'] not in ['admin', 'vendedor']:
                return jsonify({'error': 'Rol inválido'}), 400
            usuario.rol = data['rol']
        
        if 'activo' in data:
            usuario.activo = data['activo']
        
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Usuario actualizado exitosamente',
            'usuario': usuario.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar usuario: {str(e)}'}), 500


@usuarios_bp.route('/<int:id>/cambiar-password', methods=['PUT'])
@jwt_required()
@admin_required()
@validate_required_fields(['password_nueva'])
def cambiar_password_usuario(id):
    """Cambiar contraseña de un usuario (solo admin)"""
    try:
        usuario = Usuario.query.get(id)
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        password_nueva = data['password_nueva']
        
        # Validar longitud
        if len(password_nueva) < 6:
            return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
        
        usuario.set_password(password_nueva)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Contraseña actualizada exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al cambiar contraseña: {str(e)}'}), 500


@usuarios_bp.route('/<int:id>/toggle-activo', methods=['PATCH'])
@jwt_required()
@admin_required()
def toggle_activo_usuario(id):
    """Activar/Desactivar un usuario (solo admin)"""
    try:
        user_id = get_jwt_identity()
        
        # No permitir desactivarse a sí mismo
        if user_id == id:
            return jsonify({'error': 'No puedes desactivar tu propio usuario'}), 400
        
        usuario = Usuario.query.get(id)
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        usuario.activo = not usuario.activo
        db.session.commit()
        
        estado = 'activado' if usuario.activo else 'desactivado'
        
        return jsonify({
            'mensaje': f'Usuario {estado} exitosamente',
            'usuario': usuario.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al cambiar estado: {str(e)}'}), 500


@usuarios_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def eliminar_usuario(id):
    """Eliminar un usuario (solo admin)"""
    try:
        user_id = get_jwt_identity()
        
        # No permitir eliminarse a sí mismo
        if user_id == id:
            return jsonify({'error': 'No puedes eliminar tu propio usuario'}), 400
        
        usuario = Usuario.query.get(id)
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Verificar si tiene pedidos o devoluciones
        if len(usuario.pedidos) > 0 or len(usuario.devoluciones) > 0:
            return jsonify({
                'error': 'No se puede eliminar el usuario porque tiene pedidos o devoluciones registradas',
                'sugerencia': 'Considere desactivar el usuario en lugar de eliminarlo'
            }), 400
        
        db.session.delete(usuario)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Usuario eliminado exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar usuario: {str(e)}'}), 500