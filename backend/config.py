# backend/config.py
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

# ПЕРЕКЛЮЧАТЕЛЬ: использовать ли сохраненные настройки из файла
USE_SAVED_SETTINGS = True

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Database - с переключателем источника настроек
    if USE_SAVED_SETTINGS:
        # Пытаемся загрузить из файла настроек
        try:
            import sys
            import json
            from pathlib import Path
            from cryptography.fernet import Fernet
            
            # Путь к файлам конфигурации
            config_dir = Path(__file__).parent / 'config'
            config_file = config_dir / 'app_config.enc'
            key_file = config_dir / 'app.key'
            
            if config_file.exists() and key_file.exists():
                # Читаем ключ шифрования
                with open(key_file, 'rb') as f:
                    key = f.read()
                cipher = Fernet(key)
                
                # Читаем и расшифровываем настройки
                with open(config_file, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = cipher.decrypt(encrypted_data)
                settings = json.loads(decrypted_data.decode())
                
                # Используем сохраненные настройки БД
                DB_HOST = settings.get('db_host', 'localhost')
                DB_PORT = int(settings.get('db_port', 3306))
                DB_NAME = settings.get('db_name', 'keyword_lock')
                DB_USER = settings.get('db_user', 'root')
                DB_PASSWORD = settings.get('db_password', '')
                
                print(f"✅ Используются сохраненные настройки БД: {DB_HOST}:{DB_PORT}/{DB_NAME}")
            else:
                raise FileNotFoundError("Файлы настроек не найдены")
                
        except Exception as e:
            print(f"⚠️ Ошибка загрузки сохраненных настроек: {e}")
            print("📋 Используются настройки из .env файла")
            
            # Fallback на .env
            DB_HOST = os.environ.get('DB_HOST', 'localhost')
            DB_PORT = int(os.environ.get('DB_PORT', 3306))
            DB_NAME = os.environ.get('DB_NAME', 'keyword_lock')
            DB_USER = os.environ.get('DB_USER', 'root')
            DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    else:
        # Используем .env напрямую
        DB_HOST = os.environ.get('DB_HOST', 'localhost')
        DB_PORT = int(os.environ.get('DB_PORT', 3306))
        DB_NAME = os.environ.get('DB_NAME', 'keyword_lock')
        DB_USER = os.environ.get('DB_USER', 'root')
        DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
        print(f"📋 Используются настройки из .env: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    # URL encode password if it contains special characters
    DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD) if DB_PASSWORD else ''
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # DataForSeo API - тоже можем сделать динамическими
    if USE_SAVED_SETTINGS:
        try:
            # Используем те же настройки что загрузили выше
            if 'settings' in locals():
                DATAFORSEO_LOGIN = settings.get('dataforseo_login', 'developer@montessori.ua')
                DATAFORSEO_PASSWORD = settings.get('dataforseo_password', 'dcd79673da5095cb')
                print(f"✅ Используются сохраненные настройки DataForSeo: {DATAFORSEO_LOGIN}")
            else:
                raise Exception("Настройки не загружены")
        except:
            # Fallback на стандартные значения
            DATAFORSEO_LOGIN = 'developer@montessori.ua'
            DATAFORSEO_PASSWORD = 'dcd79673da5095cb'
            print("📋 Используются стандартные настройки DataForSeo")
    else:
        # Используем стандартные значения
        DATAFORSEO_LOGIN = 'developer@montessori.ua'
        DATAFORSEO_PASSWORD = 'dcd79673da5095cb'
    
    # Encryption key for sensitive data
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY') or 'generate-strong-key-for-production'
    
    # CORS - обновленный для HTTPS
    cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    CORS_ORIGINS = [origin.strip() for origin in cors_origins]
    
    # Добавляем все варианты домена для HTTPS
    CORS_ORIGINS.extend([
        'https://keylock.interschool.online',
        'https://www.keylock.interschool.online',
        'http://keylock.interschool.online',
        'http://www.keylock.interschool.online',
        'http://127.0.0.1:3000',
        'http://localhost:3000'
    ])
    
    # Убираем дубли
    CORS_ORIGINS = list(set(CORS_ORIGINS))