from app import create_app
from app.config import Config
import os
from flask import send_from_directory

app = create_app()

# Servir archivos estáticos del frontend
@app.route('/')
def index():
    """Redirigir a index.html del frontend"""
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    return send_from_directory(frontend_path, 'index.html')

@app.route('/<path:path>')
def serve_frontend(path):
    """Servir archivos del frontend"""
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    
    # Si el archivo existe, servirlo
    if os.path.exists(os.path.join(frontend_path, path)):
        response = send_from_directory(frontend_path, path)
        
        # AGREGAR HEADERS ANTI-CACHÉ PARA ARCHIVOS JS Y CSS
        if path.endswith('.js') or path.endswith('.css'):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        return response
    
    # Si no existe y no es una ruta de API, servir index.html
    if not path.startswith('api/'):
        return send_from_directory(frontend_path, 'index.html')
    
    return {'error': 'Not found'}, 404

if __name__ == '__main__':
    print("🚀 Iniciando servidor de Distribuidora Carolina...")
    print(f"🌐 Frontend: http://localhost:{os.getenv('PORT', 5000)}")
    print(f"🌐 API: http://localhost:{os.getenv('PORT', 5000)}/api")
    print(f"🗄️  Base de datos: {Config.DB_NAME}")
    print(f"⏰ Zona horaria: {Config.TIMEZONE}")
    print("\n💡 IMPORTANTE:")
    print("   - Si es la primera vez, ejecuta: python init_db.py")
    print("   - Usuario: admin")
    print("   - Contraseña: admin123\n")
    
    app.run(
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 5000)),
        debug=Config.DEBUG
    )