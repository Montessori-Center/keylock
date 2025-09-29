# app.py - исправленная версия
from flask import Flask, request, make_response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from config import Config
from sqlalchemy import text
from datetime import datetime
import pymysql
import sys

db = SQLAlchemy()

def check_and_create_database():
    """Проверка и создание БД если нужно"""
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        cursor = connection.cursor()
        
        cursor.execute(f"SHOW DATABASES LIKE '{Config.DB_NAME}'")
        result = cursor.fetchone()
        
        if not result:
            print(f"📦 Creating database {Config.DB_NAME}...")
            cursor.execute(f"CREATE DATABASE {Config.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ Database {Config.DB_NAME} created")
        
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions with app
    db.init_app(app)
    
    # Динамические CORS настройки
    config_instance = Config()
    cors_origins = config_instance.CORS_ORIGINS
    
    print(f"🌐 CORS Origins: {cors_origins}")
    
    # CORS setup - упрощенная конфигурация для aaPanel
    if "*" in cors_origins:
        # Development mode - разрешаем все
        CORS(app, resources={r"/api/*": {"origins": "*"}})
    else:
        # Production mode - конкретные домены
        CORS(app, 
             resources={r"/api/*": {
                 "origins": cors_origins,
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization"]
             }})
    
    # Import models BEFORE registering blueprints
    with app.app_context():
        # Импортируем модели
        from models.keyword import Campaign, AdGroup, Keyword, AppSetting
    
    # Register blueprints
    from api.keywords import keywords_bp
    from api.dataforseo import dataforseo_bp
    from api.settings import settings_bp
    
    app.register_blueprint(keywords_bp, url_prefix='/api/keywords')
    app.register_blueprint(dataforseo_bp, url_prefix='/api/dataforseo')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    
    # Create tables within app context
    with app.app_context():
        try:
            db.create_all()
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if tables:
                print(f"✅ Database ready. Tables: {', '.join(tables)}")
            else:
                print("⚠️ No tables found. Run: python3 init_db.py")
                
        except Exception as e:
            print(f"⚠️ Database initialization issue: {e}")
            
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add('Access-Control-Allow-Headers', "*")
            response.headers.add('Access-Control-Allow-Methods', "*")
            return response
    
    @app.route('/api/health')
    def health_check():
        db_status = "disconnected"
        tables_count = 0
        
        try:
            # Используем text() для SQL выражений в новых версиях SQLAlchemy
            result = db.session.execute(text("SELECT 1"))
            db_status = "connected"
            
            # Считаем таблицы
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            tables_count = len(tables)
            
        except Exception as e:
            db_status = f"error: {str(e)[:50]}"
        
        return {
            'status': 'ok',
            'database': db_status,
            'tables_count': tables_count,
            'cors_origins': Config.CORS_ORIGINS
        }
    
    @app.route('/')
    def index():
        try:
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            db_info = f"✅ Connected. Tables: {len(tables)}"
        except:
            db_info = "❌ Not connected"
        
        return f'''
        <h1>Keyword Lock Backend</h1>
        <p>Database: {db_info}</p>
        <p>Allowed CORS origins: {Config.CORS_ORIGINS}</p>
        <ul>
            <li><a href="/api/health">/api/health</a> - Health check</li>
            <li><a href="/api/keywords/list/1">/api/keywords/list/1</a> - Test keywords</li>
        </ul>
        '''
    
    return app
    
    @app.route('/api/test')
    def test_endpoint():
        return {
            'status': 'ok',
         'message': 'Flask API works!',
            'timestamp': datetime.utcnow().isoformat()
        }

    @app.route('/test')  
    def simple_test():
        return "Flask is working!"

if __name__ == '__main__':
    # Проверяем подключение к БД, но не останавливаем приложение при ошибке
    if not check_and_create_database():
        print("\n⚠️ Could not connect to MySQL")
        print("🔄 Continuing anyway - settings can be changed in UI")
    
    app = create_app()
    
    print("=" * 50)
    print("🚀 Starting Keyword Lock Backend")
    print(f"📍 Server: http://0.0.0.0:5000")
    print(f"🌐 CORS Origins: {Config.CORS_ORIGINS}")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)