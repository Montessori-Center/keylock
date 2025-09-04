# config.py
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Database
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_NAME = os.environ.get('DB_NAME', 'keyword_lock')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    
    # URL encode password if it contains special characters
    DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD) if DB_PASSWORD else ''
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # DataForSeo API
    DATAFORSEO_LOGIN = 'developer@montessori.ua'
    DATAFORSEO_PASSWORD = 'dcd79673da5095cb'
    
    # Encryption key for sensitive data
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY') or 'generate-strong-key-for-production'
    
    # CORS - правильный парсинг списка доменов
    cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    CORS_ORIGINS = [origin.strip() for origin in cors_origins]
    
    # Добавляем все возможные варианты домена
    if 'keylock.interschool.online' in os.environ.get('CORS_ORIGINS', ''):
        CORS_ORIGINS.extend([
            'http://keylock.interschool.online',
            'http://keylock.interschool.online:3000',
            'https://keylock.interschool.online',
            'https://keylock.interschool.online:3000'
        ])