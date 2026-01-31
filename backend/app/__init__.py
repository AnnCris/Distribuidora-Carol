from flask import Flask, send_from_directory
from flask_cors import CORS
from app.config import Config
from app.database import db
from flask_session import Session
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar base de datos
    db.init_app(app)
    
    # Inicializar sesiones
    Session(app)
    
    # Configurar CORS con soporte de credenciales
    CORS(app, 
         origins=Config.CORS_ORIGINS,
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
    
    # ⚠️ IMPORTANTE: Registrar blueprints ANTES de la ruta catch-all
    from app.routes.auth import auth_bp
    from app.routes.clientes import clientes_bp
    from app.routes.productos import productos_bp
    from app.routes.pedidos import pedidos_bp
    from app.routes.devoluciones import devoluciones_bp
    from app.routes.usuarios import usuarios_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(clientes_bp, url_prefix='/api/clientes')
    app.register_blueprint(productos_bp, url_prefix='/api/productos')
    app.register_blueprint(pedidos_bp, url_prefix='/api/pedidos')
    app.register_blueprint(devoluciones_bp, url_prefix='/api/devoluciones')
    app.register_blueprint(usuarios_bp, url_prefix='/api/usuarios')
    
    # Servir archivos estáticos del frontend (DESPUÉS de las rutas API)
    frontend_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'frontend')
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        # Si la ruta empieza con 'api/', no servir archivos estáticos
        if path.startswith('api/'):
            return {'error': 'Ruta API no encontrada'}, 404
        
        # Servir archivo estático si existe
        if path != "" and os.path.exists(os.path.join(frontend_folder, path)):
            return send_from_directory(frontend_folder, path)
        
        # Por defecto servir index.html
        return send_from_directory(frontend_folder, 'index.html')
    
    print("\n" + "="*60)
    print("✅ SERVIDOR INICIADO CORRECTAMENTE")
    print("="*60)
    
    return app