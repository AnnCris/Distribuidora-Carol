from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

db = SQLAlchemy()

def init_db(app):
    """Inicializar base de datos"""
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        print("✅ Base de datos inicializada correctamente")

def get_bolivia_time():
    """Obtener hora actual de Bolivia"""
    bolivia_tz = pytz.timezone('America/La_Paz')
    return datetime.now(bolivia_tz)