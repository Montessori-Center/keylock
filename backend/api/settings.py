# backend/api/settings.py
from flask import Blueprint, request, jsonify
from urllib.parse import urlparse
from services.config_manager import config_manager
from config import Config
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
        login = data.get('login', '').strip()
        password = data.get('password', '').strip()
        
        if not login or not password:
            return jsonify({
                'success': False, 
                'message': 'Логин и пароль обязательны для тестирования'
            })
        
        print(f"🧪 Тестирование DataForSeo API: {login}")
        
        # Создаем временный клиент с переданными данными
        from services.dataforseo_client import DataForSeoClient
        
        try:
            temp_client = DataForSeoClient(login, password)
        except ValueError as e:
            return jsonify({'success': False, 'message': f'Ошибка инициализации: {str(e)}'})
        
        # Проверяем статус аккаунта
        try:
            status = temp_client.get_status()
        except Exception as e:
            return jsonify({'success': False, 'message': f'Ошибка запроса к API: {str(e)}'})
        
        # Проверяем структуру ответа
        if not status.get('tasks') or len(status['tasks']) == 0:
            return jsonify({'success': False, 'message': 'Пустой ответ от API'})
        
        task = status['tasks'][0]
        
        # Проверяем код статуса
        if task.get('status_code') != 20000:
            error_msg = task.get('status_message', 'Unknown API error')
            print(f"❌ DataForSeo API error: {error_msg}")
            return jsonify({'success': False, 'message': f'API Error: {error_msg}'})
        
        # Извлекаем данные аккаунта
        if not task.get('result') or len(task['result']) == 0:
            return jsonify({'success': False, 'message': 'Нет данных в ответе API'})
        
        result = task['result'][0]
        money_info = result.get('money', {})
        balance = money_info.get('balance', 0)
        currency = money_info.get('currency', 'USD')
        
        # Получаем информацию о тарифах (опционально)
        rates_info = result.get('rates', {})
        keywords_rate = rates_info.get('keywords_data', {}).get('google_ads', {}).get('keywords_for_keywords', {}).get('live', 'N/A')
        
        print(f"✅ DataForSeo API работает, баланс: {balance} {currency}")
        
        return jsonify({
            'success': True, 
            'message': f'✅ API работает!\nБаланс: {balance:.2f} {currency}\nТариф Keywords for Keywords: ${keywords_rate}',
            'balance': balance,
            'currency': currency,
            'rates': {
                'keywords_for_keywords': keywords_rate
            }
        })
            
    except Exception as e:
        print(f"❌ Неожиданная ошибка DataForSeo API: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'message': f'Неожиданная ошибка: {str(e)}'
        })

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
        
@settings_bp.route('/campaign-sites', methods=['GET'])
def get_campaign_sites():
    """Получение списка кампаний и их сайтов"""
    connection = None
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = connection.cursor()
        
        # Получаем все кампании с их сайтами
        cursor.execute("""
            SELECT 
                c.id as campaign_id,
                c.name as campaign_name,
                cs.site_url,
                cs.domain
            FROM campaigns c
            LEFT JOIN campaign_sites cs ON c.id = cs.campaign_id
            ORDER BY c.id
        """)
        
        results = cursor.fetchall()
        cursor.close()
        
        campaigns = []
        for row in results:
            campaigns.append({
                'id': row['campaign_id'],
                'name': row['campaign_name'],
                'site_url': row['site_url'] or '',
                'domain': row['domain'] or ''
            })
        
        return jsonify({
            'success': True,
            'campaigns': campaigns
        })
        
    except Exception as e:
        print(f"❌ Error getting campaign sites: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection:
            connection.close()

@settings_bp.route('/campaign-sites', methods=['POST'])
def save_campaign_sites():
    """Сохранение сайтов кампаний"""
    connection = None
    try:
        data = request.json
        campaigns = data.get('campaigns', [])
        
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = connection.cursor()
        
        for campaign in campaigns:
            campaign_id = campaign['id']
            site_url = campaign.get('site_url', '').strip()
            
            # Извлекаем домен из URL
            domain = ''
            if site_url:
                from urllib.parse import urlparse
                try:
                    parsed = urlparse(site_url)
                    domain = parsed.netloc or parsed.path
                    # Убираем www. если есть
                    if domain.startswith('www.'):
                        domain = domain[4:]
                except:
                    domain = site_url
            
            # Обновляем или вставляем запись
            if site_url:
                cursor.execute("""
                    INSERT INTO campaign_sites (campaign_id, site_url, domain)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    site_url = VALUES(site_url),
                    domain = VALUES(domain)
                """, (campaign_id, site_url, domain))
            else:
                # Если URL пустой, удаляем запись
                cursor.execute("""
                    DELETE FROM campaign_sites 
                    WHERE campaign_id = %s
                """, (campaign_id,))
        
        connection.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Сайты кампаний сохранены'
        })
        
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"❌ Error saving campaign sites: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection:
            connection.close()

@settings_bp.route('/campaign-site/<int:campaign_id>', methods=['GET'])
def get_campaign_site(campaign_id):
    """Получение сайта для конкретной кампании"""
    connection = None
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT site_url, domain
            FROM campaign_sites
            WHERE campaign_id = %s
        """, (campaign_id,))
        
        result = cursor.fetchone()
        cursor.close()
        
        return jsonify({
            'success': True,
            'site_url': result['site_url'] if result else '',
            'domain': result['domain'] if result else ''
        })
        
    except Exception as e:
        print(f"❌ Error getting campaign site: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection:
            connection.close()
            
@settings_bp.route('/school-sites', methods=['GET'])
def get_school_sites():
    """Получение списка сайтов школ-конкурентов"""
    connection = None
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT id, name, domain, full_url, is_active, category, notes
            FROM school_sites
            ORDER BY name
        """)
        
        results = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'success': True,
            'schools': results
        })
        
    except Exception as e:
        print(f"❌ Error getting school sites: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection:
            connection.close()
            
@settings_bp.route('/school-sites', methods=['POST'])
def save_school_site():
    """Добавление/обновление сайта школы"""
    connection = None
    try:
        data = request.json
        school_id = data.get('id')
        name = data.get('name', '').strip()
        domain = data.get('domain', '').strip().lower()
        full_url = data.get('full_url', '').strip()
        is_active = data.get('is_active', True)
        category = data.get('category', '').strip()
        notes = data.get('notes', '').strip()
        
        if not name or not domain:
            return jsonify({'success': False, 'error': 'Название и домен обязательны'}), 400
        
        # Убираем www. из домена
        if domain.startswith('www.'):
            domain = domain[4:]
        
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = connection.cursor()
        
        if school_id:
            # Обновление существующей записи
            cursor.execute("""
                UPDATE school_sites 
                SET name = %s, domain = %s, full_url = %s, 
                    is_active = %s, category = %s, notes = %s
                WHERE id = %s
            """, (name, domain, full_url, is_active, category, notes, school_id))
        else:
            # Создание новой записи
            cursor.execute("""
                INSERT INTO school_sites (name, domain, full_url, is_active, category, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, domain, full_url, is_active, category, notes))
        
        connection.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Сайт школы сохранен'
        })
        
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"❌ Error saving school site: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection:
            connection.close()
            
@settings_bp.route('/school-sites/<int:school_id>', methods=['DELETE'])
def delete_school_site(school_id):
    """Удаление сайта школы"""
    connection = None
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = connection.cursor()
        
        cursor.execute("DELETE FROM school_sites WHERE id = %s", (school_id,))
        
        connection.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Сайт школы удален'
        })
        
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"❌ Error deleting school site: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection:
            connection.close()