# backend/api/settings.py
from flask import Blueprint, request, jsonify
from services.config_manager import config_manager
import pymysql
import os
import sys
import signal
import threading
import time

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/get', methods=['GET'])
def get_settings():
    """Получение настроек приложения"""
    try:
        settings = config_manager.load_settings()
        
        # Возвращаем все настройки (пароли будут скрыты на frontend)
        return jsonify({
            'success': True,
            'settings': settings
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def restart_app():
    """Функция для перезапуска приложения с задержкой"""
    time.sleep(2)  # Даем время отправить ответ клиенту
    print("\n🔄 Перезапуск приложения для применения новых настроек БД...")
    
    # Перезапуск через os.execv
    python = sys.executable
    os.execv(python, [python] + sys.argv)

@settings_bp.route('/save', methods=['POST'])
def save_settings():
    """Сохранение настроек приложения"""
    try:
        data = request.json
        print(f"📝 Сохранение настроек: {list(data.keys())}")
        
        # Загружаем существующие настройки
        current_settings = config_manager.load_settings()
        
        # Проверяем, изменились ли настройки БД
        db_settings_changed = False
        db_keys = ['db_host', 'db_port', 'db_name', 'db_user', 'db_password']
        
        for key in db_keys:
            if key in data and data[key] != current_settings.get(key):
                db_settings_changed = True
                print(f"🔄 Изменена настройка БД: {key}")
                break
        
        # Обновляем настройки
        current_settings.update(data)
        
        # Сохраняем
        if config_manager.save_settings(current_settings):
            if db_settings_changed:
                print("⚠️ Настройки БД изменены - будет выполнен перезапуск")
                return jsonify({
                    'success': True,
                    'message': 'Настройки сохранены.',
                    'requires_restart': True,
                    'restart_message': 'Настройки БД изменены. Требуется перезапуск приложения.\n\nВсе несохраненные изменения будут потеряны.\n\nПерезапустить сейчас?'
                })
            else:
                return jsonify({
                    'success': True,
                    'message': 'Настройки сохранены успешно!',
                    'requires_restart': False
                })
        else:
            return jsonify({'success': False, 'error': 'Ошибка сохранения файла'}), 500
            
    except Exception as e:
        print(f"❌ Ошибка сохранения настроек: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@settings_bp.route('/restart', methods=['POST'])
def restart_application():
    """Перезапуск приложения"""
    try:
        print("🔄 Получен запрос на перезапуск приложения")
        
        # Запускаем перезапуск в отдельном потоке
        restart_thread = threading.Thread(target=restart_app)
        restart_thread.daemon = True
        restart_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Перезапуск инициирован...'
        })
        
    except Exception as e:
        print(f"❌ Ошибка перезапуска: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@settings_bp.route('/test-db', methods=['POST'])
def test_db_connection():
    """Тест подключения к БД с переданными параметрами"""
    try:
        data = request.json
        print(f"🧪 Тестирование подключения к БД: {data['host']}:{data['port']}/{data['name']}")
        
        connection = pymysql.connect(
            host=data['host'],
            port=int(data['port']),
            user=data['user'],
            password=data['password'],
            database=data['name'],
            connect_timeout=5
        )
        connection.ping()
        
        # Проверяем количество таблиц
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        cursor.close()
        connection.close()
        
        print(f"✅ Подключение успешно, найдено таблиц: {len(tables)}")
        return jsonify({
            'success': True, 
            'message': f'Подключение успешно! Найдено таблиц: {len(tables)}'
        })
        
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {str(e)}")
        return jsonify({'success': False, 'message': f'Ошибка подключения: {str(e)}'})

@settings_bp.route('/test-dataforseo', methods=['POST'])
def test_dataforseo_connection():
    """Тест подключения к DataForSeo API"""
    try:
        data = request.json
        print(f"🧪 Тестирование DataForSeo API: {data['login']}")
        
        # Создаем временный клиент с переданными данными
        from services.dataforseo_client import DataForSeoClient
        temp_client = DataForSeoClient(data['login'], data['password'])
        status = temp_client.get_status()
        
        if status.get('tasks') and status['tasks'][0].get('result'):
            result = status['tasks'][0]['result'][0]
            balance = result.get('money', {}).get('balance', 0)
            print(f"✅ DataForSeo API работает, баланс: ${balance}")
            return jsonify({
                'success': True, 
                'message': f'API работает! Баланс: ${balance:.2f}'
            })
        else:
            print("❌ Неверные учетные данные DataForSeo")
            return jsonify({'success': False, 'message': 'Неверные учетные данные'})
            
    except Exception as e:
        print(f"❌ Ошибка DataForSeo API: {str(e)}")
        return jsonify({'success': False, 'message': f'Ошибка API: {str(e)}'})

@settings_bp.route('/current-db', methods=['GET'])
def get_current_db_info():
    """Получение информации о текущем подключении к БД"""
    try:
        from config import Config
        
        return jsonify({
            'success': True,
            'current_db': {
                'host': Config.DB_HOST,
                'port': Config.DB_PORT,
                'name': Config.DB_NAME,
                'user': Config.DB_USER
                # Пароль не возвращаем
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500