from flask import Blueprint, request, jsonify, session
from app.database import db
from app.models.usuario import Usuario
from app.utils.decorators import login_required, admin_required

usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/', methods=['GET'])
@admin_required
def listar_usuarios():
    """Listar todos los usuarios (solo administradores)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        activo = request.args.get('activo')
        rol = request.args.get('rol')
        buscar = request.args.get('buscar', '').strip()
        
        query = Usuario.query
        
        # Filtro por estado activo
        if activo is not None:
            activo_bool = activo.lower() in ['true', '1', 'si', 'yes']
            query = query.filter_by(activo=activo_bool)
        
        # Filtro por rol
        if rol:
            if rol not in ['admin', 'vendedor']:
                return jsonify({
                    'error': 'Rol inválido',
                    'roles_validos': ['admin', 'vendedor']
                }), 400
            query = query.filter_by(rol=rol)
        
        # Búsqueda por nombre o email
        if buscar:
            query = query.filter(
                db.or_(
                    Usuario.nombre.ilike(f'%{buscar}%'),
                    Usuario.email.ilike(f'%{buscar}%')
                )
            )
        
        # Paginación
        usuarios_paginados = query.order_by(Usuario.nombre).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'usuarios': [usuario.to_dict() for usuario in usuarios_paginados.items],
            'total': usuarios_paginados.total,
            'pagina_actual': page,
            'total_paginas': usuarios_paginados.pages,
            'por_pagina': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al listar usuarios: {str(e)}'}), 500


@usuarios_bp.route('/<int:id>', methods=['GET'])
@admin_required
def obtener_usuario(id):
    """Obtener un usuario por ID"""
    try:
        usuario = Usuario.query.get(id)
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        return jsonify({
            'usuario': usuario.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener usuario: {str(e)}'}), 500


@usuarios_bp.route('/', methods=['POST'])
@admin_required
def crear_usuario():
    """Crear un nuevo usuario (solo administradores)"""
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        if not data or not data.get('nombre') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Nombre, email y contraseña son requeridos'}), 400
        
        # Validar que el email no exista
        if Usuario.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'El email ya está registrado'}), 400
        
        # Validar rol
        rol = data.get('rol', 'vendedor')
        if rol not in ['admin', 'vendedor']:
            return jsonify({
                'error': 'Rol inválido',
                'roles_validos': ['admin', 'vendedor']
            }), 400
        
        # Validar longitud de contraseña
        if len(data['password']) < 6:
            return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
        
        # Crear usuario
        nuevo_usuario = Usuario(
            nombre=data['nombre'].strip(),
            email=data['email'].strip().lower(),
            rol=rol
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
@admin_required
def actualizar_usuario(id):
    """Actualizar un usuario (solo administradores)"""
    try:
        usuario = Usuario.query.get(id)
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        
        # Actualizar nombre
        if 'nombre' in data:
            if not data['nombre'] or not data['nombre'].strip():
                return jsonify({'error': 'El nombre no puede estar vacío'}), 400
            usuario.nombre = data['nombre'].strip()
        
        # Actualizar email
        if 'email' in data:
            email_nuevo = data['email'].strip().lower()
            if not email_nuevo:
                return jsonify({'error': 'El email no puede estar vacío'}), 400
            
            # Verificar que el email no esté en uso por otro usuario
            usuario_existente = Usuario.query.filter_by(email=email_nuevo).first()
            if usuario_existente and usuario_existente.id != id:
                return jsonify({'error': 'El email ya está registrado'}), 400
            
            usuario.email = email_nuevo
        
        # Actualizar rol
        if 'rol' in data:
            if data['rol'] not in ['admin', 'vendedor']:
                return jsonify({
                    'error': 'Rol inválido',
                    'roles_validos': ['admin', 'vendedor']
                }), 400
            
            # No permitir que el usuario actual se quite el rol de admin si es el único admin
            user_id = session.get('user_id')
            if usuario.id == user_id and usuario.rol == 'admin' and data['rol'] != 'admin':
                total_admins = Usuario.query.filter_by(rol='admin', activo=True).count()
                if total_admins <= 1:
                    return jsonify({'error': 'No puede quitarse el rol de administrador siendo el único administrador activo'}), 400
            
            usuario.rol = data['rol']
        
        # Actualizar contraseña (opcional)
        if 'password' in data and data['password']:
            if len(data['password']) < 6:
                return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
            usuario.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Usuario actualizado exitosamente',
            'usuario': usuario.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar usuario: {str(e)}'}), 500


@usuarios_bp.route('/<int:id>/toggle-activo', methods=['PATCH'])
@admin_required
def toggle_activo(id):
    """Activar o desactivar un usuario"""
    try:
        usuario = Usuario.query.get(id)
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # No permitir desactivar al único administrador activo
        user_id = session.get('user_id')
        if usuario.activo and usuario.rol == 'admin':
            total_admins_activos = Usuario.query.filter_by(rol='admin', activo=True).count()
            if total_admins_activos <= 1:
                return jsonify({'error': 'No puede desactivar al único administrador activo'}), 400
        
        # No permitir que el usuario se desactive a sí mismo
        if usuario.id == user_id:
            return jsonify({'error': 'No puede desactivarse a sí mismo'}), 400
        
        usuario.activo = not usuario.activo
        db.session.commit()
        
        estado = 'activado' if usuario.activo else 'desactivado'
        
        return jsonify({
            'mensaje': f'Usuario {estado} exitosamente',
            'usuario': usuario.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al cambiar estado del usuario: {str(e)}'}), 500


@usuarios_bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def eliminar_usuario(id):
    """Eliminar un usuario (solo administradores)"""
    try:
        usuario = Usuario.query.get(id)
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # No permitir eliminar al único administrador
        if usuario.rol == 'admin':
            total_admins = Usuario.query.filter_by(rol='admin').count()
            if total_admins <= 1:
                return jsonify({'error': 'No puede eliminar al único administrador del sistema'}), 400
        
        # No permitir que el usuario se elimine a sí mismo
        user_id = session.get('user_id')
        if usuario.id == user_id:
            return jsonify({'error': 'No puede eliminarse a sí mismo'}), 400
        
        # Verificar si tiene pedidos o devoluciones asociados
        if usuario.pedidos.count() > 0:
            return jsonify({
                'error': 'No se puede eliminar el usuario porque tiene pedidos registrados',
                'sugerencia': 'Puede desactivar el usuario en su lugar'
            }), 400
        
        if usuario.devoluciones.count() > 0:
            return jsonify({
                'error': 'No se puede eliminar el usuario porque tiene devoluciones registradas',
                'sugerencia': 'Puede desactivar el usuario en su lugar'
            }), 400
        
        db.session.delete(usuario)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Usuario eliminado exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar usuario: {str(e)}'}), 500


@usuarios_bp.route('/cambiar-password', methods=['PATCH'])
@login_required
def cambiar_password():
    """Cambiar contraseña del usuario actual"""
    try:
        user_id = session.get('user_id')
        usuario = Usuario.query.get(user_id)
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        
        if not data or not data.get('password_actual') or not data.get('password_nueva'):
            return jsonify({'error': 'Contraseña actual y nueva contraseña son requeridas'}), 400
        
        # Verificar contraseña actual
        if not usuario.check_password(data['password_actual']):
            return jsonify({'error': 'La contraseña actual es incorrecta'}), 400
        
        # Validar nueva contraseña
        if len(data['password_nueva']) < 6:
            return jsonify({'error': 'La nueva contraseña debe tener al menos 6 caracteres'}), 400
        
        # Verificar que no sea igual a la actual
        if data['password_actual'] == data['password_nueva']:
            return jsonify({'error': 'La nueva contraseña debe ser diferente a la actual'}), 400
        
        # Cambiar contraseña
        usuario.set_password(data['password_nueva'])
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Contraseña cambiada exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al cambiar contraseña: {str(e)}'}), 500


@usuarios_bp.route('/perfil', methods=['PUT'])
@login_required
def actualizar_perfil():
    """Actualizar perfil del usuario actual"""
    try:
        user_id = session.get('user_id')
        usuario = Usuario.query.get(user_id)
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        
        # Actualizar nombre
        if 'nombre' in data:
            if not data['nombre'] or not data['nombre'].strip():
                return jsonify({'error': 'El nombre no puede estar vacío'}), 400
            usuario.nombre = data['nombre'].strip()
        
        # Actualizar email
        if 'email' in data:
            email_nuevo = data['email'].strip().lower()
            if not email_nuevo:
                return jsonify({'error': 'El email no puede estar vacío'}), 400
            
            # Verificar que el email no esté en uso
            usuario_existente = Usuario.query.filter_by(email=email_nuevo).first()
            if usuario_existente and usuario_existente.id != user_id:
                return jsonify({'error': 'El email ya está registrado'}), 400
            
            usuario.email = email_nuevo
        
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Perfil actualizado exitosamente',
            'usuario': usuario.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar perfil: {str(e)}'}), 500


@usuarios_bp.route('/roles', methods=['GET'])
@login_required
def listar_roles():
    """Listar roles disponibles"""
    try:
        roles = [
            {'valor': 'admin', 'nombre': 'Administrador'},
            {'valor': 'vendedor', 'nombre': 'Vendedor'}
        ]
        
        return jsonify({
            'roles': roles
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al listar roles: {str(e)}'}), 500


@usuarios_bp.route('/estadisticas', methods=['GET'])
@admin_required
def estadisticas_usuarios():
    """Obtener estadísticas de usuarios"""
    try:
        total_usuarios = Usuario.query.count()
        usuarios_activos = Usuario.query.filter_by(activo=True).count()
        usuarios_inactivos = Usuario.query.filter_by(activo=False).count()
        total_admins = Usuario.query.filter_by(rol='admin').count()
        total_vendedores = Usuario.query.filter_by(rol='vendedor').count()
        
        return jsonify({
            'total_usuarios': total_usuarios,
            'activos': usuarios_activos,
            'inactivos': usuarios_inactivos,
            'administradores': total_admins,
            'vendedores': total_vendedores
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener estadísticas: {str(e)}'}), 500