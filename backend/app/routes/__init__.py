# Este archivo asegura que las rutas se importen correctamente
from flask import Blueprint

def init_routes(app):
    """Inicializar todas las rutas"""
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