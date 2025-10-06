# api/dataforseo.py - ПОЛНОСТЬЮ ПЕРЕРАБОТАННАЯ ВЕРСИЯ
import sys
import json
from typing import Dict
from flask import Blueprint, request, jsonify, Response
from config import Config
import pymysql
from typing import Dict
from datetime import datetime
from services.dataforseo_client import get_dataforseo_client, DataForSeoClient
from api.keywords import get_random_batch_color

dataforseo_bp = Blueprint('dataforseo', __name__)

# Принудительный flush для логов
def log_print(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

def get_db_connection():
    """Создаёт прямое подключение к БД"""
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

@dataforseo_bp.route('/test', methods=['GET', 'POST'])
def test_endpoint():
    """Простой тест endpoint"""
    try:
        log_print("🧪 TEST ENDPOINT ВЫЗВАН!")
        log_print(f"   Method: {request.method}")
        if request.method == 'POST':
            data = request.get_json()
            log_print(f"   Data: {data}")
        
        return jsonify({
            'success': True,
            'message': 'Test endpoint работает!',
            'method': request.method,
            'timestamp': str(datetime.utcnow())
        })
    except Exception as e:
        log_print(f"❌ Test endpoint error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dataforseo_bp.route('/get-keywords-simple', methods=['POST'])
def get_keywords_simple():
    """Простой тест без обращения к DataForSeo"""
    try:
        log_print("🧪 SIMPLE TEST ВЫЗВАН!")
        data = request.get_json()
        log_print(f"   Получены данные: {list(data.keys()) if data else 'None'}")
        
        # Имитируем работу
        import time
        time.sleep(1)
        
        return jsonify({
            'success': True,
            'message': 'Простой тест прошел успешно!',
            'received_keys': list(data.keys()) if data else [],
            'stats': {
                'total_results': 5,
                'added': 3,
                'updated': 2,
                'errors': 0,
                'cost': 0.00
            }
        })
    except Exception as e:
        log_print(f"❌ Simple test error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dataforseo_bp.route('/get-keywords', methods=['POST'])
def get_new_keywords():
    """Получение новой выдачи ключевых слов через DataForSeo"""
    connection = None
    
    log_print("=" * 50)
    log_print("🚀 GET-KEYWORDS ENDPOINT ВЫЗВАН!")
    log_print("=" * 50)
    
    try:
        # Получаем данные запроса
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data in request'}), 400
        
        seed_keywords = data.get('seed_keywords', [])
        ad_group_id = data.get('ad_group_id')
        
        log_print(f"🔑 Seed keywords count: {len(seed_keywords)}")
        log_print(f"🏷️  Ad group ID: {ad_group_id}")
        
        # Параметры API согласно документации
        location_code = data.get('location_code', 2804)
        language_code = data.get('language_code', 'ru')
        limit = data.get('limit', 700)
        search_partners = data.get('search_partners', False)
        include_seed_keyword = data.get('include_seed_keyword', True)
        sort_by = data.get('sort_by', 'relevance')
        date_from = data.get('date_from', '2024-01-01')
        date_to = data.get('date_to')
        
        if not seed_keywords:
            return jsonify({'success': False, 'error': 'No seed keywords provided'}), 400
        
        # Подключаемся к БД
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Получаем группу объявлений
        cursor.execute("SELECT * FROM ad_groups WHERE id = %s", (ad_group_id,))
        ad_group = cursor.fetchone()
        
        if not ad_group:
            return jsonify({'success': False, 'error': 'Ad group not found'}), 404
        
        campaign_id = ad_group['campaign_id']
        
        # Запрос к DataForSeo
        try:
            dataforseo_client = get_dataforseo_client()
            
            response = dataforseo_client.get_keywords_for_keywords(
                keywords=seed_keywords,
                location_code=location_code,
                language_code=language_code,
                search_partners=search_partners,
                sort_by=sort_by,
                limit=limit,
                include_seed_keyword=include_seed_keyword,
                date_from=date_from,
                date_to=date_to
            )
            
            # Проверяем ответ
            if not response.get('tasks'):
                return jsonify({
                    'success': False,
                    'error': 'No data received from DataForSeo'
                }), 500
            
            task = response['tasks'][0]
            if task.get('status_code') != 20000:
                error_msg = task.get('status_message', 'Unknown error')
                return jsonify({
                    'success': False,
                    'error': f"DataForSeo error: {error_msg}"
                }), 500
            
            request_cost = task.get('cost', 0.05)
            log_print(f"💰 Стоимость запроса: ${request_cost}")
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'DataForSeo API не настроен: {str(e)}'
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'DataForSeo API error: {str(e)}'
            }), 500
        
        # Парсим ответ
        try:
            keywords_data = dataforseo_client.parse_keywords_response(response)
            log_print(f"📈 Получено ключевых слов: {len(keywords_data)}")
        except Exception as e:
            log_print(f"❌ Ошибка парсинга: {str(e)}")
            keywords_data = []
        
        # Генерируем цвет для новой партии
        batch_color = get_random_batch_color()
        
        # Добавляем ключевые слова в БД
        added_count = 0
        updated_count = 0
        errors = []
        
        for kw_data in keywords_data:
            try:
                keyword_text = kw_data['keyword']
                
                # Проверяем существование
                cursor.execute(
                    "SELECT * FROM keywords WHERE ad_group_id = %s AND keyword = %s",
                    (ad_group_id, keyword_text)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Обновляем существующее (только основные данные)
                    update_query = """
                        UPDATE keywords SET 
                            avg_monthly_searches = %s,
                            competition = %s,
                            competition_percent = %s,
                            min_top_of_page_bid = %s,
                            max_top_of_page_bid = %s,
                            three_month_change = %s,
                            yearly_change = %s,
                            max_cpc = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """
                    
                    update_data = (
                        kw_data.get('avg_monthly_searches', 0),
                        kw_data.get('competition', 'Неизвестно'),
                        kw_data.get('competition_percent', 0),
                        kw_data.get('min_top_of_page_bid', 0),
                        kw_data.get('max_top_of_page_bid', 0),
                        kw_data.get('three_month_change'),
                        kw_data.get('yearly_change'),
                        kw_data.get('cpc', existing['max_cpc']),
                        existing['id']
                    )
                    
                    cursor.execute(update_query, update_data)
                    updated_count += 1
                else:
                    # Создаем новое
                    insert_query = """
                        INSERT INTO keywords (
                            campaign_id, ad_group_id, keyword, criterion_type, status,
                            avg_monthly_searches, competition, competition_percent,
                            min_top_of_page_bid, max_top_of_page_bid, three_month_change,
                            yearly_change, max_cpc, intent_type, is_new, batch_color,
                            has_ads, has_school_sites, has_google_maps, has_our_site
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    insert_data = (
                        campaign_id,
                        ad_group_id,
                        keyword_text,
                        'Phrase',
                        'Enabled',
                        kw_data.get('avg_monthly_searches', 0),
                        kw_data.get('competition', 'Неизвестно'),
                        kw_data.get('competition_percent', 0),
                        kw_data.get('min_top_of_page_bid', 0),
                        kw_data.get('max_top_of_page_bid', 0),
                        kw_data.get('three_month_change'),
                        kw_data.get('yearly_change'),
                        kw_data.get('cpc', 3.61),
                        'Информационный',  # Значение по умолчанию, будет определено через SERP
                        True,  # is_new
                        batch_color,  # batch_color
                        False,  # has_ads - по умолчанию
                        False,  # has_school_sites - по умолчанию
                        False,  # has_google_maps - по умолчанию
                        False   # has_our_site - по умолчанию
                    )
                    
                    cursor.execute(insert_query, insert_data)
                    added_count += 1
                    
            except Exception as e:
                errors.append(f"Error processing '{kw_data.get('keyword', 'unknown')}': {str(e)}")
        
        # Сохраняем в БД
        connection.commit()
        
        result = {
            'success': True,
            'message': f'Обработано {len(keywords_data)} ключевых слов. Добавлено: {added_count}, обновлено: {updated_count}',
            'stats': {
                'total_results': len(keywords_data),
                'added': added_count,
                'updated': updated_count,
                'errors': len(errors),
                'cost': request_cost
            },
            'cost': request_cost
        }
        
        if errors:
            result['errors'] = errors[:10]
        
        return jsonify(result)
        
    except Exception as e:
        if connection:
            connection.rollback()
        log_print(f"💥 Неожиданная ошибка: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection:
            connection.close()

@dataforseo_bp.route('/apply-serp', methods=['POST'])
def apply_serp_analysis():
    """Применение SERP анализа с оптимизацией для больших объемов"""
    connection = None
    
    try:
        data = request.json
        keyword_ids = data.get('keyword_ids', [])
        
        if not keyword_ids:
            return jsonify({'success': False, 'error': 'No keywords selected'}), 400
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Получаем ключевые слова
        placeholders = ','.join(['%s'] * len(keyword_ids))
        cursor.execute(f"""
            SELECT k.id, k.keyword, k.campaign_id 
            FROM keywords k
            WHERE k.id IN ({placeholders})
        """, keyword_ids)
        keywords_data = cursor.fetchall()
        
        # Получаем DataForSeo клиент
        try:
            dataforseo_client = get_dataforseo_client()
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'DataForSeo API не настроен: {str(e)}'
            }), 400
        
        # Параметры SERP запроса
        serp_params = {
            'location_code': data.get('location_code', 2804),
            'language_code': data.get('language_code', 'ru'),
            'device': data.get('device', 'desktop'),
            'os': data.get('os', 'windows'),
            'depth': data.get('depth', 100),
            'se_domain': data.get('se_domain', 'google.com.ua')
        }
        
        # Определяем стратегию: live для <10, batch для >=10
        if len(keywords_data) < 10:
            # Используем текущий live подход
            return _process_serp_live(keywords_data, serp_params, connection, dataforseo_client)
        else:
            # Используем batch подход через task_post
            return _process_serp_batch(keywords_data, serp_params, connection, dataforseo_client)
            
    except Exception as e:
        if connection:
            connection.rollback()
        log_print(f"❌ Error in apply_serp_analysis: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection:
            connection.close()

def _process_serp_batch(keywords_data, serp_params, connection, dataforseo_client):
    """Обработка SERP через task_post для больших объемов"""
    
    log_print(f"🚀 Batch SERP для {len(keywords_data)} ключевых слов")
    
    # Шаг 1: Создаем задачи через task_post
    task_ids = []
    batch_size = 100  # Максимум задач в одном запросе
    
    for i in range(0, len(keywords_data), batch_size):
        batch = keywords_data[i:i+batch_size]
        
        # Подготавливаем данные для batch запроса
        tasks = []
        for kw in batch:
            task_data = {
                "keyword": kw['keyword'],
                "tag": f"keyword_id_{kw['id']}",  # Тег для идентификации
                **serp_params
            }
            tasks.append(task_data)
        
        # Отправляем batch запрос
        response = dataforseo_client.post_serp_tasks(tasks)
        
        if response.get('tasks'):
            for task in response['tasks']:
                if task.get('id'):
                    task_ids.append({
                        'task_id': task['id'],
                        'keyword_id': int(task.get('data', {}).get('tag', '').replace('keyword_id_', '')),
                        'keyword': next((kw['keyword'] for kw in batch if str(kw['id']) in task.get('data', {}).get('tag', '')), '')
                    })
        
        log_print(f"📋 Создано {len(task_ids)} задач")
    
    # Шаг 2: Ждем выполнения задач
    import time
    max_wait = 120  # Максимум 2 минуты ожидания
    start_time = time.time()
    completed_tasks = []
    
    while len(completed_tasks) < len(task_ids) and time.time() - start_time < max_wait:
        time.sleep(2)  # Проверяем каждые 2 секунды
        
        # Проверяем статус задач
        ready_tasks = dataforseo_client.get_tasks_ready()
        
        for task_info in task_ids:
            if task_info['task_id'] not in [t['task_id'] for t in completed_tasks]:
                # Проверяем готовность конкретной задачи
                if task_info['task_id'] in ready_tasks:
                    completed_tasks.append(task_info)
                    log_print(f"✅ Задача готова: {task_info['keyword'][:30]}...")
        
        # Отправляем прогресс на frontend через SSE или WebSocket
        progress_percent = (len(completed_tasks) / len(task_ids)) * 100
        log_print(f"⏳ Прогресс: {len(completed_tasks)}/{len(task_ids)} ({progress_percent:.0f}%)")
    
    # Шаг 3: Получаем результаты
    updated_count = 0
    errors = []
    total_cost = 0
    
    for task_info in completed_tasks:
        try:
            # Получаем результат задачи
            result = dataforseo_client.get_task_result(task_info['task_id'])
            
            # Парсим и обновляем БД
            serp_data = parse_serp_response(
                result,
                keywords_data[0]['campaign_id'],
                connection,
                keyword_id=task_info['keyword_id'],
                keyword_text=task_info['keyword']
            )
            
            if serp_data:
                cursor = connection.cursor()
                cursor.execute("""
                    UPDATE keywords 
                    SET 
                        has_ads = %s,
                        has_school_sites = %s,
                        has_google_maps = %s,
                        has_our_site = %s,
                        intent_type = %s,
                        last_serp_check = NOW(),
                        updated_at = NOW()
                    WHERE id = %s
                """, (
                    serp_data['has_ads'],
                    serp_data['has_school_sites'],
                    serp_data['has_google_maps'],
                    serp_data['has_our_site'],
                    serp_data['intent_type'],
                    task_info['keyword_id']
                ))
                cursor.close()
                updated_count += 1
                
                # Считаем стоимость
                if result.get('cost'):
                    total_cost += result['cost']
                    
        except Exception as e:
            errors.append(f"Ошибка для '{task_info['keyword']}': {str(e)}")
    
    connection.commit()
    
    return jsonify({
        'success': True,
        'message': f'Batch SERP завершен! Обработано: {updated_count} из {len(keywords_data)} слов',
        'updated': updated_count,
        'total': len(keywords_data),
        'errors': errors[:10] if errors else [],
        'cost': round(total_cost, 4),
        'method': 'batch_task_post'
    })

def _process_serp_live(keywords_data, serp_params, connection, dataforseo_client):
    connection = None
    
    try:
        data = request.json
        keyword_ids = data.get('keyword_ids', [])
        
        if not keyword_ids:
            return jsonify({'success': False, 'error': 'No keywords selected'}), 400
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Получаем ключевые слова с campaign_id
        placeholders = ','.join(['%s'] * len(keyword_ids))
        cursor.execute(f"""
            SELECT k.id, k.keyword, k.campaign_id 
            FROM keywords k
            WHERE k.id IN ({placeholders})
        """, keyword_ids)
        keywords_data = cursor.fetchall()
        
        if not keywords_data:
            return jsonify({'success': False, 'error': 'Keywords not found'}), 404
        
        # Получаем DataForSeo клиент
        try:
            dataforseo_client = get_dataforseo_client()
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'DataForSeo API не настроен: {str(e)}'
            }), 400
        
        # Параметры SERP запроса
        serp_params = {
            'location_code': data.get('location_code', 2804),
            'language_code': data.get('language_code', 'ru'),
            'device': data.get('device', 'desktop'),
            'os': data.get('os', 'windows'),
            'depth': data.get('depth', 100),
            'calculate_rectangles': data.get('calculate_rectangles', False),
            'browser_screen_width': data.get('browser_screen_width', 1920),
            'browser_screen_height': data.get('browser_screen_height', 1080),
            'se_domain': data.get('se_domain', 'google.com.ua')
        }
        
        updated_count = 0
        errors = []
        total_cost = 0
        results_summary = {
            'with_ads': 0,
            'with_maps': 0,
            'with_our_site': 0,
            'with_school_sites': 0,
            'commercial_intent': 0
        }
        
        for idx, kw in enumerate(keywords_data):
            try:
                log_print(f"\n🔍 Анализ [{idx+1}/{len(keywords_data)}]: {kw['keyword']}")
                
                # Выполняем SERP запрос
                serp_response = dataforseo_client.get_serp(
                    keyword=kw['keyword'],
                    **serp_params
                )
                
                # Парсим результаты
                serp_data = parse_serp_response(
                    serp_response, 
                    kw['campaign_id'], 
                    connection,
                    keyword_id=kw['id'],
                    keyword_text=kw['keyword']
                )
                
                if serp_data:
                    # Находим позицию нашего сайта
                    our_position = 0
                    if serp_response.get('tasks') and serp_response['tasks'][0].get('result'):
                        items = serp_response['tasks'][0]['result'][0].get('items', [])
                        for item in items:
                            if item.get('type') == 'organic':
                                domain = item.get('domain', '').lower().replace('www.', '')
                                # TODO: получать домен динамически из campaign_sites
                                if domain == 'montessori.ua':
                                    our_position = item.get('rank_absolute', 0)
                                    break
                    
                    # Обновляем данные в БД с позицией и датой
                    cursor.execute("""
                        UPDATE keywords 
                        SET 
                            has_ads = %s,
                            has_school_sites = %s,
                            has_google_maps = %s,
                            has_our_site = %s,
                            intent_type = %s,
                            last_serp_check = NOW(),
                            serp_position = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """, (
                        serp_data['has_ads'],
                        serp_data['has_school_sites'],
                        serp_data['has_google_maps'],
                        serp_data['has_our_site'],
                        serp_data['intent_type'],
                        our_position if our_position > 0 else None,
                        kw['id']
                    ))
                    
                    updated_count += 1
                    
                    # Обновляем статистику
                    if serp_data['has_ads']:
                        results_summary['with_ads'] += 1
                    if serp_data['has_google_maps']:
                        results_summary['with_maps'] += 1
                    if serp_data['has_our_site']:
                        results_summary['with_our_site'] += 1
                    if serp_data['has_school_sites']:
                        results_summary['with_school_sites'] += 1
                    if serp_data['intent_type'] == 'Коммерческий':
                        results_summary['commercial_intent'] += 1
                    
                    # Считаем стоимость
                    if serp_response.get('tasks'):
                        task_cost = serp_response['tasks'][0].get('cost', 0.003)
                        total_cost += task_cost
                    
                    log_print(f"   ✅ Обновлено")
                else:
                    error_msg = f"Нет данных для '{kw['keyword']}'"
                    errors.append(error_msg)
                    log_print(f"   ⚠️ {error_msg}")
                    
            except Exception as e:
                error_msg = f"Ошибка для '{kw['keyword']}': {str(e)}"
                errors.append(error_msg)
                log_print(f"   ❌ {error_msg}")
                import traceback
                traceback.print_exc()
        
        connection.commit()
        cursor.close()
        
        # Формируем ответ
        message = f'SERP анализ завершен! Обработано: {updated_count} из {len(keywords_data)} слов'
        
        log_print(f"\n📊 Результаты SERP анализа:")
        log_print(f"   Обработано: {updated_count}/{len(keywords_data)}")
        log_print(f"   Ошибок: {len(errors)}")
        log_print(f"   Стоимость: ${total_cost:.4f}")
        
        return jsonify({
            'success': True,
            'message': message,
            'updated': updated_count,
            'total': len(keywords_data),
            'errors': errors[:10] if errors else [],
            'cost': round(total_cost, 4),
            'summary': results_summary
        })
        
    except Exception as e:
        if connection:
            connection.rollback()
        log_print(f"❌ Error in apply_serp_analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
        
    finally:
        if connection:
            connection.close()
            
@dataforseo_bp.route('/serp-logs', methods=['GET'])
def get_serp_logs():
    """Получение последних SERP анализов для отладки"""
    connection = None
    try:
        limit = request.args.get('limit', 20, type=int)
        keyword_id = request.args.get('keyword_id', None, type=int)
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        if keyword_id:
            # Логи для конкретного ключевого слова
            cursor.execute("""
                SELECT * FROM serp_logs 
                WHERE keyword_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (keyword_id, limit))
        else:
            # Последние логи
            cursor.execute("""
                SELECT * FROM serp_logs 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (limit,))
        
        logs = cursor.fetchall()
        
        # Форматируем для удобного просмотра
        formatted_logs = []
        for log in logs:
            try:
                # Безопасный парсинг JSON
                raw_response = {}
                parsed_items = {}
                
                if log.get('raw_response'):
                    try:
                        raw_response = json.loads(log['raw_response'])
                    except:
                        raw_response = {}
                
                if log.get('parsed_items'):
                    try:
                        parsed_items = json.loads(log['parsed_items'])
                    except:
                        parsed_items = {}
                
                formatted_log = {
                    'id': log['id'],
                    'keyword': log.get('keyword_text', ''),
                    'created_at': log['created_at'].isoformat() if log.get('created_at') else None,
                    'summary': {
                        'total_items': log.get('total_items', 0),
                        'organic': log.get('organic_count', 0),
                        'paid': log.get('paid_count', 0),
                        'maps': log.get('maps_count', 0)
                    },
                    'flags': {
                        'has_ads': bool(log.get('has_ads')),
                        'has_maps': bool(log.get('has_maps')),
                        'has_our_site': bool(log.get('has_our_site')),
                        'has_school_sites': bool(log.get('has_school_sites'))
                    },
                    'intent': log.get('intent_type', 'Информационный'),
                    'school_percentage': float(log.get('school_percentage', 0)),
                    'cost': float(log.get('cost', 0)),
                    'raw_response': raw_response,
                    'parsed_items': parsed_items
                }
                formatted_logs.append(formatted_log)
            except Exception as e:
                log_print(f"⚠️ Error formatting log {log.get('id')}: {str(e)}")
                continue
        
        cursor.close()
        
        log_print(f"📊 Returning {len(formatted_logs)} SERP logs")
        
        return jsonify({
            'success': True,
            'count': len(formatted_logs),
            'logs': formatted_logs
        })
        
    except Exception as e:
        log_print(f"❌ Error getting SERP logs: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection:
            connection.close()


@dataforseo_bp.route('/serp-logs/<int:log_id>', methods=['GET'])
def get_serp_log_details(log_id):
    """Получение детальной информации о конкретном SERP анализе"""
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("SELECT * FROM serp_logs WHERE id = %s", (log_id,))
        log = cursor.fetchone()
        
        if not log:
            return jsonify({'success': False, 'error': 'Log not found'}), 404
        
        # Детальный разбор
        parsed_items = {}
        if log.get('parsed_items'):
            try:
                parsed_items = json.loads(log['parsed_items'])
            except:
                parsed_items = {}
        
        detailed_report = {
            'id': log['id'],
            'keyword': log.get('keyword_text', ''),
            'created_at': log['created_at'].isoformat() if log.get('created_at') else None,
            'parameters': {
                'location_code': log.get('location_code', 0),
                'language_code': log.get('language_code', ''),
                'device': log.get('device', ''),
                'depth': log.get('depth', 0)
            },
            'summary': {
                'total_items': log.get('total_items', 0),
                'organic_count': log.get('organic_count', 0),
                'paid_count': log.get('paid_count', 0),
                'maps_count': log.get('maps_count', 0)
            },
            'analysis_result': {
                'has_ads': bool(log.get('has_ads')),
                'has_maps': bool(log.get('has_maps')),
                'has_our_site': bool(log.get('has_our_site')),
                'has_school_sites': bool(log.get('has_school_sites')),
                'intent_type': log.get('intent_type', 'Информационный'),
                'school_percentage': float(log.get('school_percentage', 0))
            },
            'cost': float(log.get('cost', 0)),
            'organic_results': parsed_items.get('organic', []),
            'paid_results': parsed_items.get('paid', []),
            'all_items': parsed_items.get('all_items', [])
        }
        
        cursor.close()
        
        return jsonify({
            'success': True,
            'report': detailed_report
        })
        
    except Exception as e:
        log_print(f"❌ Error getting SERP log details: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection:
            connection.close()

@dataforseo_bp.route('/test-connection', methods=['POST'])
def test_dataforseo_connection():
    """Тест подключения к DataForSeo API"""
    try:
        data = request.json
        temp_client = DataForSeoClient(data['login'], data['password'])
        status = temp_client.get_status()
        
        if status.get('tasks') and status['tasks'][0].get('result'):
            balance = status['tasks'][0]['result'][0].get('money', {}).get('balance', 0)
            return jsonify({
                'success': True, 
                'message': f'API работает. Баланс: ${balance}'
            })
        else:
            return jsonify({'success': False, 'message': 'Неверные учетные данные'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка API: {str(e)}'})
        
@dataforseo_bp.route('/check-serp-cost', methods=['POST'])
def check_serp_cost():
    """Проверка стоимости SERP анализа перед выполнением"""
    try:
        data = request.json
        keyword_ids = data.get('keyword_ids', [])
        depth = data.get('depth', 100)
        
        # Расчет стоимости
        base_cost = 0.003  # $0.003 за SERP regular до 100 результатов
        
        # Множитель для глубины
        if depth <= 20:
            depth_multiplier = 1
        elif depth <= 50:
            depth_multiplier = 1.5
        elif depth <= 100:
            depth_multiplier = 2
        else:
            depth_multiplier = 3  # для depth > 100
        
        estimated_cost = len(keyword_ids) * base_cost * depth_multiplier
        
        # Проверка баланса
        try:
            dataforseo_client = get_dataforseo_client()
            status = dataforseo_client.get_status()
            
            current_balance = 0
            if status.get('tasks') and status['tasks'][0].get('result'):
                current_balance = status['tasks'][0]['result'][0].get('money', {}).get('balance', 0)
            
            can_proceed = current_balance >= estimated_cost
            
            return jsonify({
                'success': True,
                'estimated_cost': round(estimated_cost, 4),
                'current_balance': round(current_balance, 2),
                'can_proceed': can_proceed,
                'keywords_count': len(keyword_ids),
                'depth': depth,
                'message': f"Анализ {len(keyword_ids)} ключевых слов будет стоить примерно ${estimated_cost:.4f}"
            })
            
        except Exception as e:
            # Если не можем проверить баланс, все равно показываем стоимость
            return jsonify({
                'success': True,
                'estimated_cost': round(estimated_cost, 4),
                'current_balance': None,
                'can_proceed': True,
                'keywords_count': len(keyword_ids),
                'depth': depth,
                'message': f"Анализ {len(keyword_ids)} ключевых слов будет стоить примерно ${estimated_cost:.4f}",
                'warning': 'Не удалось проверить баланс'
            })
            
    except Exception as e:
        log_print(f"❌ Error checking SERP cost: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dataforseo_bp.route('/check-balance', methods=['GET'])
def check_balance():
    """Проверка баланса и статуса аккаунта DataForSeo"""
    try:
        dataforseo_client = get_dataforseo_client()
        status = dataforseo_client.get_status()
        
        if status.get('tasks') and status['tasks'][0].get('result'):
            result = status['tasks'][0]['result'][0]
            return jsonify({
                'success': True,
                'balance': {
                    'money': result.get('money', {}).get('balance', 0),
                    'currency': 'USD'
                },
                'rates': {
                    'keywords_for_keywords': result.get('rates', {}).get('keywords_data', {}).get('google_ads', {}).get('keywords_for_keywords', {}).get('live', 0.05),
                    'serp': result.get('rates', {}).get('serp', {}).get('live', {}).get('regular', 0.01)
                }
            })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'DataForSeo API не настроен: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dataforseo_bp.route('/locations', methods=['GET'])
def get_locations():
    """Получение списка доступных локаций"""
    try:
        country = request.args.get('country')
        dataforseo_client = get_dataforseo_client()
        locations = dataforseo_client.get_locations(country)
        
        popular = [
            {'code': 2804, 'name': 'Ukraine', 'name_ru': 'Украина'},
            {'code': 2840, 'name': 'United States', 'name_ru': 'США'},
            {'code': 2643, 'name': 'Russia', 'name_ru': 'Россия'},
            {'code': 2276, 'name': 'Germany', 'name_ru': 'Германия'},
            {'code': 2826, 'name': 'United Kingdom', 'name_ru': 'Великобритания'},
            {'code': 2250, 'name': 'France', 'name_ru': 'Франция'},
            {'code': 2616, 'name': 'Poland', 'name_ru': 'Польша'},
            {'code': 2724, 'name': 'Spain', 'name_ru': 'Испания'},
            {'code': 2380, 'name': 'Italy', 'name_ru': 'Италия'},
            {'code': 2124, 'name': 'Canada', 'name_ru': 'Канада'},
        ]
        
        return jsonify({
            'success': True,
            'popular': popular,
            'all': locations.get('tasks', [{}])[0].get('result', []) if locations else []
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': f'DataForSeo API не настроен: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
        
@dataforseo_bp.route('/test-serp', methods=['POST'])
def test_serp_single():
    """Тестовый SERP анализ одного ключевого слова"""
    try:
        data = request.json
        test_keyword = data.get('keyword', 'уроки музыки киев')
        
        log_print(f"🧪 ТЕСТ SERP для: {test_keyword}")
        
        # Получаем DataForSeo клиент
        try:
            dataforseo_client = get_dataforseo_client()
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'DataForSeo API не настроен: {str(e)}'
            }), 400
        
        # Минимальные параметры для теста
        serp_response = dataforseo_client.get_serp(
            keyword=test_keyword,
            location_code=2804,  # Ukraine
            language_code='ru',
            device='desktop',
            os='windows',
            depth=10,  # Только топ-10 для теста
            se_domain='google.com.ua'
        )
        
        # Проверяем ответ
        if not serp_response.get('tasks'):
            return jsonify({
                'success': False,
                'error': 'No response from DataForSeo'
            })
        
        task = serp_response['tasks'][0]
        
        # Проверяем статус
        if task.get('status_code') != 20000:
            return jsonify({
                'success': False,
                'error': task.get('status_message', 'Unknown error'),
                'status_code': task.get('status_code')
            })
        
        # Получаем результаты
        if not task.get('result'):
            return jsonify({
                'success': False,
                'error': 'No results in response'
            })
        
        result = task['result'][0]
        items = result.get('items', [])
        
        # Формируем простой отчет
        report = {
            'keyword': test_keyword,
            'items_count': len(items),
            'cost': task.get('cost', 0),
            'types_found': [],
            'organic_domains': [],
            'has_ads': False,
            'has_maps': False
        }
        
        for item in items:
            item_type = item.get('type', '')
            
            if item_type not in report['types_found']:
                report['types_found'].append(item_type)
            
            if item_type == 'organic':
                domain = item.get('domain', '')
                if domain:
                    report['organic_domains'].append({
                        'position': item.get('rank_absolute', 0),
                        'domain': domain,
                        'title': item.get('title', '')[:50]
                    })
            elif item_type in ['paid', 'google_ads']:
                report['has_ads'] = True
            elif item_type in ['local_pack', 'maps']:
                report['has_maps'] = True
        
        log_print("✅ ТЕСТ SERP успешен!")
        log_print(f"   Найдено элементов: {report['items_count']}")
        log_print(f"   Типы: {', '.join(report['types_found'])}")
        log_print(f"   Стоимость: ${report['cost']}")
        
        return jsonify({
            'success': True,
            'message': 'SERP API работает корректно!',
            'report': report,
            'raw_response_preview': {
                'status_code': task.get('status_code'),
                'status_message': task.get('status_message'),
                'cost': task.get('cost'),
                'result_count': result.get('items_count', 0),
                'se_results_count': result.get('se_results_count', 0)
            }
        })
        
    except Exception as e:
        log_print(f"❌ Test SERP error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dataforseo_bp.route('/languages', methods=['GET'])
def get_languages():
    """Получение списка доступных языков"""
    try:
        dataforseo_client = get_dataforseo_client()
        languages = dataforseo_client.get_languages()
        
        main_languages = [
            {'code': 'ru', 'name': 'Русский'},
            {'code': 'uk', 'name': 'Украинский'},
            {'code': 'en', 'name': 'Английский'},
            {'code': 'de', 'name': 'Немецкий'},
            {'code': 'fr', 'name': 'Французский'},
            {'code': 'es', 'name': 'Испанский'},
            {'code': 'it', 'name': 'Итальянский'},
            {'code': 'pl', 'name': 'Польский'},
        ]
        
        return jsonify({
            'success': True,
            'main': main_languages,
            'all': languages.get('tasks', [{}])[0].get('result', []) if languages else []
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': f'DataForSeo API не настроен: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
        
def parse_serp_response(serp_response: Dict, campaign_id: int, connection, keyword_id: int = None, keyword_text: str = None) -> Dict:
    """
    Парсинг SERP ответа с детальным логированием и сохранением в БД
    """
    try:
        if not serp_response.get('tasks'):
            log_print("❌ No tasks in SERP response")
            return None
        
        task = serp_response['tasks'][0]
        if task.get('status_code') != 20000:
            log_print(f"❌ SERP API error: {task.get('status_message')}")
            return None
        
        if not task.get('result') or len(task['result']) == 0:
            log_print("❌ No result in SERP response")
            return None
        
        result = task['result'][0]
        
        # Метаинформация о выдаче
        item_types = result.get('item_types', [])
        items_count = result.get('items_count', 0)
        se_results_count = result.get('se_results_count', 0)
        
        log_print(f"📊 SERP метаданные:")
        log_print(f"   - Всего элементов: {items_count}")
        log_print(f"   - SE результатов: {se_results_count}")
        log_print(f"   - Типы элементов: {', '.join(item_types) if item_types else 'none'}")
        
        items = result.get('items', [])
        
        if not items:
            log_print("⚠️ No items in SERP response")
            return None
        
        # Инициализация результатов
        has_ads = False
        has_google_maps = False
        has_our_site = False
        has_school_sites = False
        
        # Детальные счетчики и данные для сохранения
        organic_results = []
        paid_results = []
        maps_results = []
        all_items_parsed = []
        
        # Счетчики
        total_organic_sites = 0
        school_sites_count = 0
        school_domains_found = []
        
        # Получаем домен нашего сайта
        our_domain = get_campaign_domain(campaign_id, connection)
        log_print(f"📌 Наш домен для кампании {campaign_id}: {our_domain or 'НЕ УКАЗАН'}")
        
        # Получаем список доменов школ
        school_domains = get_school_domains(connection)
        log_print(f"📚 Загружено доменов школ-конкурентов: {len(school_domains)}")
        if school_domains:
            log_print(f"   Домены школ: {', '.join(list(school_domains)[:5])}")
        
        # ДЕТАЛЬНЫЙ АНАЛИЗ каждого элемента
        log_print("\n🔍 ДЕТАЛЬНЫЙ АНАЛИЗ ВЫДАЧИ:")
        log_print("-" * 50)
        
        for idx, item in enumerate(items):
            item_type = item.get('type', '')
            position = item.get('rank_absolute', idx + 1)
            
            # Сохраняем ВСЕ элементы для полной картины
            item_parsed = {
                'position': position,
                'type': item_type,
                'domain': item.get('domain', ''),
                'url': item.get('url', ''),
                'title': (item.get('title', '') or '')[:100]
            }
            
            # Добавляем в общий список ВСЕГДА
            all_items_parsed.append(item_parsed)
            
            # Далее идет специфичная обработка по типам...
            # РЕКЛАМНЫЕ БЛОКИ
            if item_type in ['paid', 'google_ads', 'shopping', 'commercial_units']:
                has_ads = True
                paid_results.append(item_parsed)
                log_print(f"   #{position} [РЕКЛАМА] {item.get('domain', 'unknown')}")
                log_print(f"        URL: {(item.get('url', '') or '')[:80]}")
            
            # GOOGLE MAPS
            elif item_type in ['local_pack', 'maps', 'map', 'google_maps']:
                has_google_maps = True
                maps_results.append(item_parsed)
                log_print(f"   #{position} [КАРТЫ] Google Maps блок")
                if item.get('items'):
                    log_print(f"        Мест в блоке: {len(item.get('items', []))}")
            
            # ОРГАНИЧЕСКИЕ РЕЗУЛЬТАТЫ
            elif item_type == 'organic':
                total_organic_sites += 1
                
                url = (item.get('url', '') or '').lower()
                domain = (item.get('domain', '') or '').lower()
                title = item.get('title') or ''
                description = item.get('description') or ''
                
                # Очищаем домен
                clean_domain = domain.replace('www.', '') if domain else ''
                
                organic_results.append({
                    'position': position,
                    'domain': clean_domain,
                    'title': title[:100] if title else '',
                    'url': url,
                    'description': description[:200] if description else ''
                })
                
                log_print(f"   #{position} [ОРГАНИКА] {clean_domain}")
                log_print(f"        Title: {title[:60] if title else 'No title'}")
                log_print(f"        URL: {url[:80]}")
                
                # Проверяем наш сайт
                if our_domain:
                    if our_domain in url or our_domain == clean_domain:
                        has_our_site = True
                        log_print(f"        ✅ ЭТО НАШ САЙТ!")
                
                # Проверка сайтов школ
                if clean_domain in school_domains:
                    school_sites_count += 1
                    school_domains_found.append(clean_domain)
                    has_school_sites = True
                    log_print(f"        🏫 ЭТО САЙТ ШКОЛЫ-КОНКУРЕНТА!")
            
            # ДРУГИЕ ТИПЫ - тоже логируем подробнее
            else:
                log_print(f"   #{position} [{item_type.upper()}]")
                
                # Специфичная информация по типам
                if item_type == 'people_also_ask':
                    questions = item.get('items', [])
                    log_print(f"        Вопросов: {len(questions)}")
                    if questions:
                        for q in questions[:3]:  # Первые 3 вопроса
                            log_print(f"        - {q.get('title', '')[:60]}")
                            
                elif item_type == 'video':
                    videos = item.get('items', [])
                    log_print(f"        Видео блок ({len(videos)} видео)")
                    if videos:
                        for v in videos[:2]:  # Первые 2 видео
                            log_print(f"        - {v.get('title', '')[:50]}")
                            
                elif item_type == 'ai_overview':
                    log_print(f"        AI Overview блок")
                    text = item.get('text', '')
                    if text:
                        log_print(f"        Текст: {text[:100]}...")
                        
                elif item_type == 'images':
                    log_print(f"        Блок изображений")
                    
                elif item_type == 'related_searches':
                    searches = item.get('items', [])
                    log_print(f"        Похожие запросы: {len(searches)}")
                    if searches:
                        for s in searches[:3]:  # Первые 3 запроса
                            log_print(f"        - {s.get('title', '')}")
                            
                elif item_type == 'people_also_search':
                    log_print(f"        Люди также ищут")
                    
                elif item_type == 'knowledge_graph':
                    log_print(f"        Knowledge Graph")
                    kg_title = item.get('title', '')
                    if kg_title:
                        log_print(f"        Title: {kg_title}")
                        
                elif item_type == 'featured_snippet':
                    log_print(f"        Featured Snippet")
                    domain = item.get('domain', '')
                    if domain:
                        log_print(f"        Источник: {domain}")
        
        log_print("-" * 50)
        
        # Определение интента
        intent_type = 'Информационный'
        school_percentage = 0
        
        if has_school_sites and total_organic_sites > 0:
            school_percentage = (school_sites_count / total_organic_sites) * 100
            log_print(f"\n📊 Анализ интента:")
            log_print(f"   Органических сайтов: {total_organic_sites}")
            log_print(f"   Сайтов школ: {school_sites_count}")
            log_print(f"   Процент школ: {school_percentage:.1f}%")
            
            if school_percentage >= 60:
                intent_type = 'Коммерческий'
                log_print(f"   → Интент: КОММЕРЧЕСКИЙ (школ >= 60%)")
            else:
                log_print(f"   → Интент: ИНФОРМАЦИОННЫЙ (школ < 60%)")
        
        # СОХРАНЯЕМ В БД для отладки
        if keyword_id and connection:
            try:
                cursor = connection.cursor()
                
                # Подготавливаем JSON данные
                import json
                raw_response_json = json.dumps({
                    'status_code': task.get('status_code'),
                    'items_count': items_count,
                    'se_results_count': se_results_count,
                    'item_types': item_types
                }, ensure_ascii=False)
                
                parsed_items_json = json.dumps({
                    'organic': organic_results,
                    'paid': paid_results,
                    'maps': maps_results,
                    'all_items': all_items_parsed
                }, ensure_ascii=False)
                
                # Получаем параметры запроса из data
                request_data = task.get('data', {})
                if isinstance(request_data, list) and len(request_data) > 0:
                    request_params = request_data[0]
                else:
                    request_params = {}
                
                # Сохраняем в таблицу serp_logs
                insert_query = """
                    INSERT INTO serp_logs (
                        keyword_id, keyword_text, location_code, language_code,
                        device, depth, total_items, organic_count, paid_count,
                        maps_count, shopping_count, has_ads, has_maps,
                        has_our_site, has_school_sites, intent_type,
                        school_percentage, cost, raw_response, parsed_items
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s
                    )
                """
                
                insert_values = (
                    keyword_id,
                    keyword_text or '',
                    request_params.get('location_code', 0),
                    request_params.get('language_code', ''),
                    request_params.get('device', 'desktop'),
                    request_params.get('depth', 0),
                    items_count,
                    total_organic_sites,
                    len(paid_results),
                    len(maps_results),
                    0,  # shopping_count
                    has_ads,
                    has_google_maps,
                    has_our_site,
                    has_school_sites,
                    intent_type,
                    school_percentage,
                    task.get('cost', 0),
                    raw_response_json,
                    parsed_items_json
                )
                
                cursor.execute(insert_query, insert_values)
                inserted_id = cursor.lastrowid
                connection.commit()
                cursor.close()
                
                log_print(f"💾 SERP данные сохранены в БД (serp_logs), ID: {inserted_id}")
                
            except Exception as e:
                log_print(f"⚠️ Ошибка сохранения в serp_logs: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Итоговая сводка
        log_print("\n" + "=" * 50)
        log_print(f"📊 ИТОГИ SERP АНАЛИЗА:")
        log_print(f"   Органика: {total_organic_sites}")
        log_print(f"   Реклама: {len(paid_results)}")
        log_print(f"   Карты: {len(maps_results)}")
        log_print(f"   Наш сайт: {'ДА' if has_our_site else 'НЕТ'}")
        log_print(f"   Сайты школ: {'ДА' if has_school_sites else 'НЕТ'}")
        log_print(f"   Интент: {intent_type}")
        log_print("=" * 50)
        
        return {
            'has_ads': has_ads,
            'has_school_sites': has_school_sites,
            'has_google_maps': has_google_maps,
            'has_our_site': has_our_site,
            'intent_type': intent_type,
            'stats': {
                'total_organic': total_organic_sites,
                'paid_count': len(paid_results),
                'maps_count': len(maps_results),
                'school_percentage': round(school_percentage, 1)
            }
        }
        
    except Exception as e:
        log_print(f"❌ Error parsing SERP response: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
        
def get_campaign_domain(campaign_id: int, connection) -> str:
    """
    Получает домен сайта для кампании из таблицы campaign_sites
    """
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT domain 
            FROM campaign_sites 
            WHERE campaign_id = %s
        """, (campaign_id,))
        
        result = cursor.fetchone()
        cursor.close()
        
        if result and result['domain']:
            domain = result['domain'].lower()
            # Убираем www. если есть
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        
        return None
        
    except Exception as e:
        log_print(f"❌ Error getting campaign domain: {e}")
        return None


def get_school_domains(connection) -> set:
    """
    Получает список доменов школ-конкурентов из БД
    """
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT domain 
            FROM school_sites 
            WHERE is_active = TRUE
        """)
        
        results = cursor.fetchall()
        cursor.close()
        
        # Создаем set доменов для быстрой проверки
        domains = set()
        for row in results:
            if row['domain']:
                domain = row['domain'].lower()
                # Убираем www. если есть
                if domain.startswith('www.'):
                    domain = domain[4:]
                domains.add(domain)
        
        return domains
        
    except Exception as e:
        log_print(f"⚠️ Error getting school domains: {e}")
        # Если таблицы нет, возвращаем пустой set
        return set()