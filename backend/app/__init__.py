from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.config import Config
from app.database import db

def create_app():
    """Factory para crear la aplicación Flask"""
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # CORS - Ultra simple
    CORS(app)
    
    # Deshabilitar strict_slashes
    app.url_map.strict_slashes = False
    
    # JWT
    jwt = JWTManager(app)
    
    # Base de datos
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    # Registrar blueprints
    from app.routes.auth import auth_bp
    from app.routes.usuarios import usuarios_bp
    from app.routes.clientes import clientes_bp
    from app.routes.productos import productos_bp
    from app.routes.pedidos import pedidos_bp
    from app.routes.devoluciones import devoluciones_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(usuarios_bp, url_prefix='/api/usuarios')
    app.register_blueprint(clientes_bp, url_prefix='/api/clientes')
    app.register_blueprint(productos_bp, url_prefix='/api/productos')
    app.register_blueprint(pedidos_bp, url_prefix='/api/pedidos')
    app.register_blueprint(devoluciones_bp, url_prefix='/api/devoluciones')
    
    # Manejadores JWT - NO redirigir automáticamente
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token expirado'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Token inválido'}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'No autorizado'}), 401
    
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'ok'}), 200
    
    return app