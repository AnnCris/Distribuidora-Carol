import os
from app import create_app
from app.config import Config

app = create_app()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("✅ SERVIDOR INICIADO CORRECTAMENTE")
    print("="*60)
    print("🚀 Iniciando servidor de Distribuidora Carolina...")
    print(f"🌐 Frontend: http://localhost:5000")
    print(f"🌐 API: http://localhost:5000/api")
    print(f"🗄️  Base de datos: {Config.DB_NAME}")
    print(f"🔌 PostgreSQL: {Config.DB_HOST}:{Config.DB_PORT}")
    print("="*60)
    print("⚠️  Presiona CTRL+C para detener el servidor")
    print("="*60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )