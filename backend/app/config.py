import os
from datetime import timedelta
from pathlib import Path

# Obtener el directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env')

class Config:
    # Configuración básica
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-carolina-2024'
    
    # Base de datos PostgreSQL
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '2458')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'distribuidora_carolina')
    
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?client_encoding=utf8'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de sesiones
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CORS - Permitir mismo origen
    CORS_ORIGINS = ['http://localhost:5000', 'http://127.0.0.1:5000']
    CORS_SUPPORTS_CREDENTIALS = True
    
    # Zona horaria
    TIMEZONE = 'America/La_Paz'