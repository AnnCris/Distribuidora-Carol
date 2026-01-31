from flask import Blueprint, request, jsonify, session
from app.database import db
from app.models.usuario import Usuario

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login de usuario"""
    try:
        data = request.get_json()
        
        print(f"📥 Datos recibidos: {data}")  # Debug
        
        if not data:
            return jsonify({'error': 'No se recibieron datos'}), 400
        
        email = data.get('email')
        password = data.get('password')
        
        print(f"👤 Email: {email}, Password: {'***' if password else 'None'}")  # Debug
        
        if not email or not password:
            return jsonify({'error': 'Complete todos los campos'}), 400
        
        # Buscar usuario
        usuario = Usuario.query.filter_by(email=email).first()
        
        if not usuario:
            print(f"❌ Usuario no encontrado: {email}")
            return jsonify({'error': 'Credenciales incorrectas'}), 401
        
        if not usuario.activo:
            print(f"❌ Usuario inactivo: {email}")
            return jsonify({'error': 'Usuario desactivado'}), 401
        
        # Verificar contraseña
        if not usuario.check_password(password):
            print(f"❌ Contraseña incorrecta para: {email}")
            return jsonify({'error': 'Credenciales incorrectas'}), 401
        
        # Guardar en sesión
        session.clear()
        session['user_id'] = usuario.id
        session['user_name'] = usuario.nombre
        session['user_role'] = usuario.rol
        session.permanent = True
        
        print(f"✅ Login exitoso: {usuario.email}")
        print(f"📝 Sesión creada: {dict(session)}")
        
        return jsonify({
            'mensaje': 'Login exitoso',
            'usuario': usuario.to_dict()
        }), 200
        
    except Exception as e:
        print(f"❌ Error en login: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error en el servidor: {str(e)}'}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout de usuario"""
    try:
        print(f"🚪 Cerrando sesión: {session.get('user_id')}")
        session.clear()
        return jsonify({'mensaje': 'Sesión cerrada exitosamente'}), 200
    except Exception as e:
        print(f"❌ Error en logout: {str(e)}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/validar', methods=['GET'])
def validar_sesion():
    """Validar si la sesión está activa"""
    try:
        user_id = session.get('user_id')
        
        print(f"🔍 Validando sesión: {dict(session)}")
        
        if not user_id:
            print("❌ No hay user_id en sesión")
            return jsonify({'valido': False}), 200
        
        usuario = Usuario.query.get(user_id)
        
        if not usuario or not usuario.activo:
            print(f"❌ Usuario no encontrado o inactivo: {user_id}")
            session.clear()
            return jsonify({'valido': False}), 200
        
        print(f"✅ Sesión válida para: {usuario.email}")
        
        return jsonify({
            'valido': True,
            'usuario': usuario.to_dict()
        }), 200
        
    except Exception as e:
        print(f"❌ Error validando sesión: {str(e)}")
        return jsonify({'valido': False}), 200


@auth_bp.route('/perfil', methods=['GET'])
def obtener_perfil():
    """Obtener perfil del usuario actual"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'No autenticado'}), 401
        
        usuario = Usuario.query.get(user_id)
        
        if not usuario:
            session.clear()
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        return jsonify({
            'usuario': usuario.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500