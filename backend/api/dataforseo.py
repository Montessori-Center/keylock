# api/dataforseo.py - ПОЛНОСТЬЮ ПЕРЕРАБОТАННАЯ ВЕРСИЯ
import sys
import json
import time
import uuid
from typing import Dict
from flask import Blueprint, request, jsonify, Response, stream_with_context
from config import Config
import pymysql
from datetime import datetime
from services.dataforseo_client import get_dataforseo_client, DataForSeoClient
from api.keywords import get_random_batch_color

dataforseo_bp = Blueprint('dataforseo', __name__)

# Глобальное хранилище прогресса задач
SERP_PROGRESS = {}

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

def update_progress(task_id: str, current: int, total: int, keyword: str = '', status: str = 'processing'):
    """Обновляет прогресс задачи"""
    SERP_PROGRESS[task_id] = {
        'current': current,
        'total': total,
        'keyword': keyword,
        'status': status,
        'timestamp': time.time()
    }
    log_print(f"📊 Progress updated: {current}/{total} - {keyword}")

def get_progress(task_id: str) -> Dict:
    """Получает прогресс задачи"""
    return SERP_PROGRESS.get(task_id, {
        'current': 0,
        'total': 0,
        'keyword': '',
        'status': 'not_found'
    })

def cleanup_progress(task_id: str):
    """Очищает прогресс задачи"""
    if task_id in SERP_PROGRESS:
        del SERP_PROGRESS[task_id]
        log_print(f"🧹 Progress cleaned up for task {task_id}")
        
@dataforseo_bp.route('/apply-serp-sse', methods=['GET'])
def apply_serp_sse():
    """SSE endpoint для получения прогресса SERP анализа"""
    task_id = request.args.get('task_id')
    
    if not task_id:
        return jsonify({'error': 'task_id required'}), 400
    
    def generate():
        """Генератор событий SSE"""
        log_print(f"🔄 SSE stream started for task {task_id}")
        
        # Ждем появления задачи (макс 5 сек)
        wait_time = 0
        while task_id not in SERP_PROGRESS and wait_time < 5:
            time.sleep(0.1)
            wait_time += 0.1
        
        if task_id not in SERP_PROGRESS:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Task not found'})}\n\n"
            return
        
        # Отправляем события прогресса
        last_current = -1
        max_wait = 300  # 5 минут максимум
        start_time = time.time()
        
        while True:
            if time.time() - start_time > max_wait:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Timeout'})}\n\n"
                break
            
            progress = get_progress(task_id)
            
            # Отправляем только если прогресс изменился
            if progress['current'] != last_current:
                last_current = progress['current']
                
                if progress['status'] == 'processing':
                    event_data = {
                        'type': 'progress',
                        'current': progress['current'],
                        'total': progress['total'],
                        'keyword': progress['keyword']
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
                    
                elif progress['status'] == 'complete':
                    event_data = {
                        'type': 'complete',
                        'message': progress.get('message', 'Completed'),
                        'result': progress.get('result', {})
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
                    cleanup_progress(task_id)
                    break
                    
                elif progress['status'] == 'error':
                    event_data = {
                        'type': 'error',
                        'message': progress.get('error', 'Unknown error')
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
                    cleanup_progress(task_id)
                    break
            
            time.sleep(0.5)  # Проверяем каждые 0.5 секунды
        
        log_print(f"🔚 SSE stream ended for task {task_id}")
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
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
    """Применение SERP анализа с поддержкой прогресса через SSE"""
    
    try:
        data = request.json
        keyword_ids = data.get('keyword_ids', [])
        task_id = data.get('task_id') or str(uuid.uuid4())
        
        log_print(f"\n{'='*50}")
        log_print(f"🚀 SERP Analysis started: task_id={task_id}")
        log_print(f"   Keywords: {len(keyword_ids)}")
        log_print(f"{'='*50}")
        
        if not keyword_ids:
            return jsonify({'success': False, 'error': 'No keywords selected'}), 400
        
        # ИЗМЕНЕНО: Для 1 слова - синхронно без прогресса, для 2+ - Task-версия
        if len(keyword_ids) == 1:
            # Live-анализ для одного слова (быстро, без модалки)
            try:
                result = process_serp_sync(task_id, keyword_ids, data)
                return jsonify(result), 200
            except Exception as e:
                log_print(f"❌ Live analysis error: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'SERP analysis failed: {str(e)}'
                }), 500
        else:
            # Task-версия для 2+ слов (с прогрессом через SSE)
            import threading
            
            # Инициализируем прогресс
            update_progress(task_id, 0, len(keyword_ids), '', 'processing')
            
            thread = threading.Thread(
                target=process_serp_async,
                args=(task_id, keyword_ids, data)
            )
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'success': True,
                'task_id': task_id,
                'message': 'SERP analysis started',
                'use_sse': True
            }), 200
            
    except Exception as e:
        log_print(f"❌ Error in apply_serp_analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500
            
def process_serp_sync(task_id: str, keyword_ids: list, params: dict) -> dict:
    """
    Синхронная обработка SERP с обновлением прогресса
    ИСПРАВЛЕНО: Добавлено сохранение our_organic_position и our_actual_position
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Получаем данные ключевых слов
        placeholders = ','.join(['%s'] * len(keyword_ids))
        cursor.execute(f"""
            SELECT k.id, k.keyword, k.campaign_id 
            FROM keywords k
            WHERE k.id IN ({placeholders})
        """, keyword_ids)
        keywords_data = cursor.fetchall()
        
        if not keywords_data:
            return {'success': False, 'error': 'Keywords not found'}
        
        # Получаем клиент DataForSeo
        try:
            dataforseo_client = get_dataforseo_client()
        except ValueError as e:
            return {'success': False, 'error': f'DataForSeo API не настроен: {str(e)}'}
        
        # Параметры SERP запроса
        serp_params = {
            'location_code': params.get('location_code', 2804),
            'language_code': params.get('language_code', 'ru'),
            'device': params.get('device', 'desktop'),
            'os': params.get('os', 'windows'),
            'depth': params.get('depth', 100),
            'calculate_rectangles': params.get('calculate_rectangles', False),
            'browser_screen_width': params.get('browser_screen_width', 1920),
            'browser_screen_height': params.get('browser_screen_height', 1080),
            'se_domain': params.get('se_domain', 'google.com.ua')
        }
        
        updated_count = 0
        errors = []
        total_cost = 0.0
        results_summary = {
            'with_ads': 0,
            'with_maps': 0,
            'with_our_site': 0,
            'with_school_sites': 0,
            'commercial_intent': 0
        }
        
        # Обрабатываем ключевые слова с обновлением прогресса
        for idx, kw in enumerate(keywords_data):
            try:
                log_print(f"\n🔍 Анализ [{idx+1}/{len(keywords_data)}]: {kw['keyword']}")
                
                # Обновляем прогресс ПЕРЕД обработкой каждого слова
                update_progress(task_id, idx, len(keywords_data), kw['keyword'], 'processing')
                
                # Выполняем SERP запрос
                serp_response = dataforseo_client.get_serp(
                    keyword=kw['keyword'],
                    **serp_params
                )
                
                # Парсим результаты (используем исправленную parse_serp_response)
                serp_data = parse_serp_response(
                    serp_response, 
                    kw['campaign_id'], 
                    connection,
                    keyword_id=kw['id'],
                    keyword_text=kw['keyword']
                )
                
                if serp_data:
                    # ИСПРАВЛЕНО: Обновляем данные С ПОЗИЦИЯМИ
                    cursor.execute("""
                        UPDATE keywords 
                        SET 
                            has_ads = %s,
                            has_school_sites = %s,
                            has_google_maps = %s,
                            has_our_site = %s,
                            intent_type = %s,
                            our_organic_position = %s,
                            our_actual_position = %s,
                            last_serp_check = NOW(),
                            updated_at = NOW()
                        WHERE id = %s
                    """, (
                        serp_data['has_ads'],
                        serp_data['has_school_sites'],
                        serp_data['has_google_maps'],
                        serp_data['has_our_site'],
                        serp_data['intent_type'],
                        serp_data.get('our_organic_position'),  # НОВОЕ
                        serp_data.get('our_actual_position'),   # НОВОЕ
                        kw['id']
                    ))
                    
                    updated_count += 1
                    
                    # Логируем результаты
                    log_print(f"   ✅ Обновлено в БД")
                    if serp_data.get('has_our_site'):
                        log_print(f"   📍 Позиции: органическая={serp_data.get('our_organic_position')}, фактическая={serp_data.get('our_actual_position')}")
                    
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
                        task_cost = serp_response['tasks'][0].get('cost', 0)
                        total_cost += task_cost
                        log_print(f"   💰 Стоимость: ${task_cost:.4f}")
                else:
                    error_msg = f"Нет данных для '{kw['keyword']}'"
                    errors.append(error_msg)
                    log_print(f"   ⚠️ {error_msg}")
                
                # Обновляем прогресс ПОСЛЕ обработки
                update_progress(task_id, idx + 1, len(keywords_data), kw['keyword'], 'processing')
                
            except Exception as e:
                error_msg = f"Ошибка для '{kw['keyword']}': {str(e)}"
                log_print(f"   ❌ {error_msg}")
                errors.append(error_msg)
                import traceback
                traceback.print_exc()
                
                # Всё равно обновляем прогресс при ошибке
                update_progress(task_id, idx + 1, len(keywords_data), kw['keyword'], 'processing')
        
        # Сохраняем изменения
        connection.commit()
        
        # Формируем итоговое сообщение
        message = f'SERP анализ завершен! Обработано: {updated_count} из {len(keywords_data)} слов'
        
        log_print(f"\n📊 Результаты:")
        log_print(f"   Обработано: {updated_count}/{len(keywords_data)}")
        log_print(f"   Ошибок: {len(errors)}")
        log_print(f"   Стоимость: ${total_cost:.4f}")
        log_print(f"   С рекламой: {results_summary['with_ads']}")
        log_print(f"   С картами: {results_summary['with_maps']}")
        log_print(f"   С нашим сайтом: {results_summary['with_our_site']}")
        log_print(f"   С сайтами школ: {results_summary['with_school_sites']}")
        log_print(f"   Коммерческий интент: {results_summary['commercial_intent']}")
        
        return {
            'success': True,
            'message': message,
            'updated': updated_count,
            'total': len(keywords_data),
            'errors': errors[:10] if errors else [],
            'cost': round(total_cost, 4),
            'summary': results_summary
        }
        
    except Exception as e:
        if connection:
            try:
                connection.rollback()
            except:
                pass
        log_print(f"❌ Error in process_serp_sync: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if connection:
            try:
                connection.close()
            except:
                pass
            
def process_serp_async(task_id: str, keyword_ids: list, params: dict):
    """Асинхронная обработка SERP для больших объемов (2+ слов)"""
    try:
        log_print(f"🔄 Async SERP processing started for task {task_id}")
        
        # Вызываем синхронную функцию в отдельном потоке
        result = process_serp_sync(task_id, keyword_ids, params)
        
        # Обновляем финальный статус
        SERP_PROGRESS[task_id].update({
            'status': 'complete',
            'result': result,
            'message': result.get('message', 'Completed')
        })
        
        log_print(f"✅ Async SERP processing completed for task {task_id}")
        
    except Exception as e:
        log_print(f"❌ Async SERP error for task {task_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        SERP_PROGRESS[task_id].update({
            'status': 'error',
            'error': str(e),
            'message': f'Error: {str(e)}'
        })
        

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
    """
    Получение SERP логов с расширенной фильтрацией
    
    Parameters:
    - limit: количество записей (по умолчанию 50)
    - keyword_id: фильтр по конкретному keyword_id
    - keyword_ids: список keyword_id через запятую (для фильтрации нескольких слов)
    - latest_only: если true, возвращает только последний лог для каждого keyword_id
    """
    connection = None
    try:
        # Получаем параметры
        limit = request.args.get('limit', 50, type=int)
        keyword_id = request.args.get('keyword_id', None, type=int)
        keyword_ids_str = request.args.get('keyword_ids', None, type=str)
        latest_only = request.args.get('latest_only', 'false', type=str).lower() == 'true'
        
        log_print(f"📊 get_serp_logs called: limit={limit}, keyword_id={keyword_id}, keyword_ids={keyword_ids_str}, latest_only={latest_only}")
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Формируем SQL запрос
        if latest_only and keyword_ids_str:
            # Получаем только последние логи для указанных слов
            keyword_ids_list = [int(kid.strip()) for kid in keyword_ids_str.split(',') if kid.strip()]
            
            # Подзапрос для получения MAX(id) для каждого keyword_id
            placeholders = ','.join(['%s'] * len(keyword_ids_list))
            query = f"""
                SELECT sl.* FROM serp_logs sl
                INNER JOIN (
                    SELECT keyword_id, MAX(id) as max_id
                    FROM serp_logs
                    WHERE keyword_id IN ({placeholders})
                    GROUP BY keyword_id
                ) latest ON sl.id = latest.max_id
                ORDER BY sl.created_at DESC
            """
            cursor.execute(query, tuple(keyword_ids_list))
            
        elif keyword_ids_str:
            # Все логи для указанных слов
            keyword_ids_list = [int(kid.strip()) for kid in keyword_ids_str.split(',') if kid.strip()]
            placeholders = ','.join(['%s'] * len(keyword_ids_list))
            query = f"""
                SELECT * FROM serp_logs 
                WHERE keyword_id IN ({placeholders})
                ORDER BY created_at DESC 
                LIMIT %s
            """
            cursor.execute(query, tuple(keyword_ids_list + [limit]))
            
        elif keyword_id:
            # Все логи для одного слова
            cursor.execute("""
                SELECT * FROM serp_logs 
                WHERE keyword_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (keyword_id, limit))
            
        else:
            # Все последние логи
            cursor.execute("""
                SELECT * FROM serp_logs 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (limit,))
        
        logs = cursor.fetchall()
        log_print(f"📋 Found {len(logs)} logs in DB")
        
        # Форматируем логи для фронтенда
        formatted_logs = []
        for log in logs:
            try:
                # Парсим JSON поля
                analysis_result = {}
                organic_results = []
                paid_results = []
                
                # Сначала пробуем получить из analysis_result (новый формат)
                if log.get('analysis_result'):
                    try:
                        analysis_result = json.loads(log['analysis_result'])
                    except:
                        log_print(f"⚠️ Не удалось распарсить analysis_result для log_id={log['id']}")
                
                # Если analysis_result пустой, пытаемся восстановить из старых полей
                if not analysis_result:
                    analysis_result = {
                        'has_ads': log.get('has_ads', False),
                        'has_google_maps': log.get('has_maps', False),
                        'has_our_site': log.get('has_our_site', False),
                        'our_organic_position': None,  # В старых записях может не быть
                        'our_actual_position': None,
                        'has_school_sites': log.get('has_school_sites', False),
                        'school_percentage': log.get('school_percentage', 0),
                        'intent_type': log.get('intent_type', 'Информационный'),
                        'total_organic': log.get('organic_count', 0),
                        'paid_count': log.get('paid_count', 0),
                        'maps_count': log.get('maps_count', 0)
                    }
                
                # Парсим parsed_items
                if log.get('parsed_items'):
                    try:
                        parsed_items = json.loads(log['parsed_items'])
                        organic_results = parsed_items.get('organic', [])
                        paid_results = parsed_items.get('paid', [])
                    except:
                        log_print(f"⚠️ Не удалось распарсить parsed_items для log_id={log['id']}")
                
                formatted_log = {
                    'id': log['id'],
                    'keyword_id': log['keyword_id'],
                    'keyword_text': log['keyword_text'],
                    'created_at': log['created_at'].isoformat() if log.get('created_at') else None,
                    'cost': float(log.get('cost', 0)),
                    'analysis_result': {
                        'has_ads': analysis_result.get('has_ads', False),
                        'has_google_maps': analysis_result.get('has_google_maps', False),
                        'has_our_site': analysis_result.get('has_our_site', False),
                        'our_organic_position': analysis_result.get('our_organic_position'),
                        'our_actual_position': analysis_result.get('our_actual_position'),
                        'has_school_sites': analysis_result.get('has_school_sites', False),
                        'school_percentage': analysis_result.get('school_percentage', 0),
                        'intent_type': analysis_result.get('intent_type', 'Информационный'),
                        'total_organic': analysis_result.get('total_organic', 0),
                        'paid_count': analysis_result.get('paid_count', 0),
                        'maps_count': analysis_result.get('maps_count', 0)
                    },
                    'organic_results': organic_results,
                    'paid_results': paid_results,
                    'raw_response': log.get('raw_response'),
                    'parsed_items': parsed_items,
                    'our_domain': None
                }
                
                formatted_logs.append(formatted_log)
                
            except Exception as e:
                log_print(f"⚠️ Error formatting log {log.get('id')}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        cursor.close()
        
        log_print(f"📊 Returning {len(formatted_logs)} SERP logs")
        
        return jsonify({
            'success': True,
            'count': len(formatted_logs),
            'logs': formatted_logs,
            'filters_applied': {
                'keyword_id': keyword_id,
                'keyword_ids': keyword_ids_str,
                'latest_only': latest_only
            }
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
        
@dataforseo_bp.route('/debug-serp/<int:log_id>', methods=['GET'])
def debug_serp_log(log_id):
    """DEBUG: Полный дамп raw_response для диагностики"""
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("SELECT raw_response FROM serp_logs WHERE id = %s", (log_id,))
        log = cursor.fetchone()
        
        if not log:
            return jsonify({'success': False, 'error': 'Log not found'}), 404
        
        raw_response = log.get('raw_response')
        
        if not raw_response:
            return jsonify({'success': False, 'error': 'No raw_response'}), 404
        
        # Парсим и анализируем
        if isinstance(raw_response, str):
            raw_response = json.loads(raw_response)
        
        items = raw_response['tasks'][0]['result'][0]['items']
        
        # Собираем статистику по типам
        type_stats = {}
        for item in items:
            item_type = item.get('type', 'unknown')
            if item_type not in type_stats:
                type_stats[item_type] = {
                    'count': 0,
                    'examples': []
                }
            type_stats[item_type]['count'] += 1
            
            # Сохраняем первые 2 примера каждого типа
            if len(type_stats[item_type]['examples']) < 2:
                type_stats[item_type]['examples'].append({
                    'rank_absolute': item.get('rank_absolute'),
                    'domain': item.get('domain'),
                    'title': item.get('title', '')[:80]
                })
        
        cursor.close()
        
        return jsonify({
            'success': True,
            'log_id': log_id,
            'total_items': len(items),
            'type_statistics': type_stats,
            'full_items': items[:5]  # Первые 5 элементов полностью
        })
        
    except Exception as e:
        log_print(f"❌ Debug error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection:
            connection.close()

@dataforseo_bp.route('/locations', methods=['GET'])
def get_locations():
    """Получение списка доступных локаций"""
    try:
        country = request.args.get('country')
        dataforseo_client = get_dataforseo_client()
        locations = dataforseo_client.get_locations(country)
        
        popular = [
            {'code': 1012852, 'name': 'Kyiv, Kyiv city, Ukraine', 'name_ru': 'Киев, Украина', 'se_domain': 'google.com.ua'},
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
            {'code': 'uk', 'name': 'Українська'},
            {'code': 'ru', 'name': 'Русский'},
            {'code': 'en', 'name': 'English'},
            {'code': 'de', 'name': 'Deutsch'},
            {'code': 'fr', 'name': 'Français'},
            {'code': 'es', 'name': 'Español'},
            {'code': 'it', 'name': 'Italiano'},
            {'code': 'pl', 'name': 'Polski'},
        ]
        
        # Полный список всех языков
        all_languages = [
            {'code': 'af', 'name': 'Afrikaans'},
            {'code': 'ak', 'name': 'Akan'},
            {'code': 'sq', 'name': 'Albanian'},
            {'code': 'am', 'name': 'Amharic'},
            {'code': 'ar', 'name': 'Arabic'},
            {'code': 'hy', 'name': 'Armenian'},
            {'code': 'az', 'name': 'Azeri'},
            {'code': 'ban', 'name': 'Balinese'},
            {'code': 'eu', 'name': 'Basque'},
            {'code': 'be', 'name': 'Belarusian'},
            {'code': 'bn', 'name': 'Bengali'},
            {'code': 'bs', 'name': 'Bosnian'},
            {'code': 'bg', 'name': 'Bulgarian'},
            {'code': 'my', 'name': 'Burmese'},
            {'code': 'ca', 'name': 'Catalan'},
            {'code': 'ceb', 'name': 'Cebuano'},
            {'code': 'ny', 'name': 'Chichewa'},
            {'code': 'zh-CN', 'name': 'Chinese (Simplified)'},
            {'code': 'zh-TW', 'name': 'Chinese (Traditional)'},
            {'code': 'hr', 'name': 'Croatian'},
            {'code': 'cs', 'name': 'Czech'},
            {'code': 'da', 'name': 'Danish'},
            {'code': 'nl', 'name': 'Dutch'},
            {'code': 'en', 'name': 'English'},
            {'code': 'es-419', 'name': 'Español (Latinoamérica)'},
            {'code': 'et', 'name': 'Estonian'},
            {'code': 'ee', 'name': 'Ewe'},
            {'code': 'fo', 'name': 'Faroese'},
            {'code': 'fa', 'name': 'Farsi'},
            {'code': 'fil', 'name': 'Filipino'},
            {'code': 'fi', 'name': 'Finnish'},
            {'code': 'fr', 'name': 'Français'},
            {'code': 'fy', 'name': 'Frisian'},
            {'code': 'gaa', 'name': 'Ga'},
            {'code': 'gl', 'name': 'Galician'},
            {'code': 'lg', 'name': 'Ganda'},
            {'code': 'ka', 'name': 'Georgian'},
            {'code': 'de', 'name': 'Deutsch'},
            {'code': 'el', 'name': 'Greek'},
            {'code': 'gu', 'name': 'Gujarati'},
            {'code': 'ht', 'name': 'Haitian'},
            {'code': 'ha', 'name': 'Hausa'},
            {'code': 'he', 'name': 'Hebrew'},
            {'code': 'iw', 'name': 'Hebrew (old)'},
            {'code': 'hi', 'name': 'Hindi'},
            {'code': 'hu', 'name': 'Hungarian'},
            {'code': 'is', 'name': 'Icelandic'},
            {'code': 'bem', 'name': 'IciBemba'},
            {'code': 'ig', 'name': 'Igbo'},
            {'code': 'id', 'name': 'Indonesian'},
            {'code': 'ga', 'name': 'Irish'},
            {'code': 'it', 'name': 'Italiano'},
            {'code': 'ja', 'name': 'Japanese'},
            {'code': 'kn', 'name': 'Kannada'},
            {'code': 'kk', 'name': 'Kazakh'},
            {'code': 'km', 'name': 'Khmer'},
            {'code': 'rw', 'name': 'Kinyarwanda'},
            {'code': 'rn', 'name': 'Kirundi'},
            {'code': 'kg', 'name': 'Kongo'},
            {'code': 'ko', 'name': 'Korean'},
            {'code': 'mfe', 'name': 'Kreol morisien'},
            {'code': 'crs', 'name': 'Kreol Seselwa'},
            {'code': 'kri', 'name': 'Krio'},
            {'code': 'ckb', 'name': 'Kurdish'},
            {'code': 'ky', 'name': 'Kyrgyz'},
            {'code': 'lo', 'name': 'Lao'},
            {'code': 'lv', 'name': 'Latvian'},
            {'code': 'ln', 'name': 'Lingala'},
            {'code': 'lt', 'name': 'Lithuanian'},
            {'code': 'ach', 'name': 'Luo'},
            {'code': 'mk', 'name': 'Macedonian'},
            {'code': 'mg', 'name': 'Malagasy'},
            {'code': 'ms', 'name': 'Malay'},
            {'code': 'ml', 'name': 'Malayam'},
            {'code': 'mt', 'name': 'Maltese'},
            {'code': 'mi', 'name': 'Maori'},
            {'code': 'mr', 'name': 'Marathi'},
            {'code': 'mn', 'name': 'Mongolian'},
            {'code': 'sr-ME', 'name': 'Montenegro'},
            {'code': 'ne', 'name': 'Nepali'},
            {'code': 'nso', 'name': 'Northern Sotho'},
            {'code': 'no', 'name': 'Norwegian'},
            {'code': 'nyn', 'name': 'Nyankole'},
            {'code': 'om', 'name': 'Oromo'},
            {'code': 'ps', 'name': 'Pashto'},
            {'code': 'pcm', 'name': 'Pidgin'},
            {'code': 'pl', 'name': 'Polski'},
            {'code': 'pt', 'name': 'Português'},
            {'code': 'pt-BR', 'name': 'Português (Brasil)'},
            {'code': 'pt-PT', 'name': 'Português (Portugal)'},
            {'code': 'pa', 'name': 'Punjabi'},
            {'code': 'qu', 'name': 'Quechua'},
            {'code': 'ro', 'name': 'Romanian'},
            {'code': 'rm', 'name': 'Romansh'},
            {'code': 'ru', 'name': 'Русский'},
            {'code': 'sr', 'name': 'Serbian'},
            {'code': 'sr-Latn', 'name': 'Serbian (Latin)'},
            {'code': 'st', 'name': 'Sesotho'},
            {'code': 'sn', 'name': 'Shona'},
            {'code': 'loz', 'name': 'Silozi'},
            {'code': 'sd', 'name': 'Sindhi'},
            {'code': 'si', 'name': 'Sinhalese'},
            {'code': 'sk', 'name': 'Slovak'},
            {'code': 'sl', 'name': 'Slovenian'},
            {'code': 'so', 'name': 'Somali'},
            {'code': 'es', 'name': 'Español'},
            {'code': 'sw', 'name': 'Swahili'},
            {'code': 'sv', 'name': 'Swedish'},
            {'code': 'tg', 'name': 'Tajik'},
            {'code': 'ta', 'name': 'Tamil'},
            {'code': 'te', 'name': 'Telugu'},
            {'code': 'th', 'name': 'Thai'},
            {'code': 'ti', 'name': 'Tigrinya'},
            {'code': 'to', 'name': 'Tonga (Tonga Islands)'},
            {'code': 'lua', 'name': 'Tshiluba'},
            {'code': 'tn', 'name': 'Tswana'},
            {'code': 'tum', 'name': 'Tumbuka'},
            {'code': 'tr', 'name': 'Turkish'},
            {'code': 'tk', 'name': 'Turkmen'},
            {'code': 'uk', 'name': 'Українська'},
            {'code': 'ur', 'name': 'Urdu'},
            {'code': 'uz', 'name': 'Uzbek'},
            {'code': 'vi', 'name': 'Vietnamese'},
            {'code': 'wo', 'name': 'Wolof'},
            {'code': 'xh', 'name': 'Xhosa'},
            {'code': 'yo', 'name': 'Yoruba'},
            {'code': 'zu', 'name': 'Zulu'},
        ]
        
        return jsonify({
            'success': True,
            'main': main_languages,
            'all': all_languages
        })

    except ValueError as e:
        return jsonify({'success': False, 'error': f'DataForSeo API не настроен: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def parse_serp_response(serp_response: Dict, campaign_id: int, connection, keyword_id: int = None, keyword_text: str = None) -> Dict:
    """
    Парсинг SERP ответа с детальным логированием
    ИСПРАВЛЕНО: 
    - Правильное определение типов элементов
    - Логирование ВСЕХ типов для диагностики
    - Поддержка всех типов из документации DataForSEO
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
        items = result.get('items', [])
        
        if not items:
            log_print("⚠️ No items in SERP response")
            return None
        
        log_print(f"\n🔍 АНАЛИЗ SERP ДЛЯ: {keyword_text}")
        log_print(f"📊 Всего элементов: {len(items)}")
        
        # Инициализация результатов
        has_ads = False
        has_google_maps = False
        has_our_site = False
        has_school_sites = False
        
        # Позиции нашего сайта
        our_organic_position = None
        our_actual_position = None
        
        # Детальные данные
        organic_results = []
        paid_results = []
        maps_results = []
        all_items_parsed = []
        
        # Счетчики
        total_organic_sites = 0
        school_sites_count = 0
        organic_position_counter = 0
        
        # Счетчик типов для диагностики
        from collections import Counter
        type_counter = Counter()
        
        # Получаем домен нашего сайта
        our_domain = get_campaign_domain(campaign_id, connection)
        school_domains = get_school_domains(connection)
        
        log_print(f"📌 Наш домен: {our_domain or 'НЕ УКАЗАН'}")
        log_print(f"\n{'=' * 70}")
        log_print("📋 ДЕТАЛЬНЫЙ РАЗБОР ЭЛЕМЕНТОВ:")
        log_print(f"{'=' * 70}\n")
        
        # Обрабатываем каждый элемент
        for idx, item in enumerate(items):
            item_type = item.get('type', 'unknown')
            rank_absolute = item.get('rank_absolute', idx + 1)
            rank_group = item.get('rank_group', idx + 1)
            
            # Считаем типы
            type_counter[item_type] += 1
            
            # Общие данные
            domain = (item.get('domain', '') or '').lower()
            url = (item.get('url', '') or '').lower()
            title = item.get('title') or ''
            
            log_print(f"#{idx+1:2d} | Type: {item_type:20s} | rank_abs: {rank_absolute:3d} | rank_group: {rank_group:3d}")
            
            # РЕКЛАМНЫЕ БЛОКИ
            # Согласно документации: paid, shopping, google_flights, google_hotels
            if item_type in ['paid', 'shopping', 'google_flights', 'google_hotels', 'ads', 'ad']:
                has_ads = True
                clean_domain = domain.replace('www.', '').strip()
                
                paid_results.append({
                    'actual_position': rank_absolute,
                    'domain': clean_domain,
                    'title': title[:100] if title else '',
                    'url': url,
                    'ad_type': item_type  # Сохраняем тип для debug
                })
                log_print(f"     💰 [РЕКЛАМА type={item_type}] Domain: {clean_domain}")
                log_print(f"     Title: {title[:60]}")
            
            # GOOGLE MAPS / LOCAL PACK
            # Согласно документации: local_pack
            elif item_type in ['local_pack', 'map', 'maps', 'google_maps']:
                has_google_maps = True
                maps_results.append({
                    'rank_absolute': rank_absolute,
                    'type': item_type,
                    'title': title[:100] if title else ''
                })
                log_print(f"     🗺️ [КАРТЫ] Type: {item_type}")
                
                # Local pack может содержать несколько мест
                if item.get('items'):
                    log_print(f"     📍 Мест в блоке: {len(item.get('items', []))}")
                    for place_idx, place in enumerate(item.get('items', [])[:3], 1):
                        place_title = place.get('title', 'No title')
                        log_print(f"        {place_idx}. {place_title}")
            
            # ОРГАНИЧЕСКИЕ РЕЗУЛЬТАТЫ
            elif item_type == 'organic':
                organic_position_counter += 1
                total_organic_sites += 1
                
                clean_domain = domain.replace('www.', '').strip()
                description = item.get('description') or ''
                
                # КРИТИЧНО: Создаём объект с гарантированными полями
                organic_item = {
                    'organic_position': organic_position_counter,
                    'actual_position': rank_absolute,
                    'domain': clean_domain,
                    'title': title[:100] if title else '',
                    'url': url,
                    'description': description[:200] if description else ''
                }
                
                organic_results.append(organic_item)
                
                log_print(f"     🌐 [ОРГАНИКА #{organic_position_counter}] Domain: {clean_domain}")
                log_print(f"     Title: {title[:60]}")
                
                # Проверка нашего сайта
                if our_domain:
                    clean_our_domain = our_domain.replace('www.', '').strip().lower()
                    is_our_site = False
                    
                    # Множественные проверки
                    if clean_our_domain == clean_domain:
                        is_our_site = True
                        log_print(f"        ✅ ТОЧНОЕ СОВПАДЕНИЕ ДОМЕНА")
                    elif clean_our_domain in url:
                        is_our_site = True
                        log_print(f"        ✅ ДОМЕН НАЙДЕН В URL")
                    elif clean_domain.endswith('.' + clean_our_domain) or clean_our_domain.endswith('.' + clean_domain):
                        is_our_site = True
                        log_print(f"        ✅ SUBDOMAIN MATCH")
                    
                    if is_our_site:
                        has_our_site = True
                        if our_organic_position is None:
                            our_organic_position = organic_position_counter
                            our_actual_position = rank_absolute
                            log_print(f"        🎯 ЭТО НАШ САЙТ!")
                            log_print(f"        📍 Органическая позиция: {our_organic_position}")
                            log_print(f"        📍 Фактическая позиция: {our_actual_position}")
                
                # Проверка сайтов школ
                if clean_domain in school_domains:
                    school_sites_count += 1
                    has_school_sites = True
                    log_print(f"        🏫 САЙТ ШКОЛЫ-КОНКУРЕНТА")
            
            # ВСЕ ОСТАЛЬНЫЕ ТИПЫ (для информации)
            else:
                log_print(f"     ℹ️ [{item_type.upper()}]")
                if title:
                    log_print(f"     Title: {title[:60]}")
            
            log_print()  # Пустая строка для разделения
        
        # Определяем интент
        intent_type = 'Коммерческий' if has_ads else 'Информационный'
        school_percentage = (school_sites_count / total_organic_sites * 100) if total_organic_sites > 0 else 0
        
        # ИТОГИ
        log_print(f"\n{'=' * 70}")
        log_print("📊 ИТОГИ АНАЛИЗА:")
        log_print(f"{'=' * 70}")
        log_print(f"   Всего элементов: {len(items)}")
        log_print(f"   Типы найденных элементов: {dict(type_counter)}")
        log_print(f"   Органических результатов: {total_organic_sites}")
        log_print(f"   Рекламных блоков: {len(paid_results)}")
        log_print(f"   Карты Google: {'ДА' if has_google_maps else 'НЕТ'} ({len(maps_results)} шт.)")
        log_print(f"   Наш сайт: {'ДА' if has_our_site else 'НЕТ'}")
        if has_our_site:
            log_print(f"   📍 Органическая позиция (среди органики): {our_organic_position}")
            log_print(f"   📍 Фактическая позиция (на странице): {our_actual_position}")
        else:
            log_print(f"   ⚠️ Домен '{our_domain}' не найден в органической выдаче")
        log_print(f"   Сайты школ: {'ДА' if has_school_sites else 'НЕТ'} ({school_percentage:.1f}%)")
        log_print(f"   Интент: {intent_type}")
        log_print(f"{'=' * 70}\n")
        
        # Формируем JSON
        parsed_items_json = json.dumps({
            'organic': organic_results,
            'paid': paid_results,
            'maps': maps_results  # ← ВОТ ОНО ЕСТЬ!
        }, ensure_ascii=False)
        
        analysis_result_json = json.dumps({
            'has_ads': has_ads,
            'has_google_maps': has_google_maps,
            'has_our_site': has_our_site,
            'our_organic_position': our_organic_position,
            'our_actual_position': our_actual_position,
            'has_school_sites': has_school_sites,
            'school_percentage': round(school_percentage, 1),
            'intent_type': intent_type,
            'total_organic': total_organic_sites,
            'paid_count': len(paid_results),
            'maps_count': len(maps_results)
        }, ensure_ascii=False)
        
        # Сохраняем в БД
        if connection and keyword_id:
            try:
                cursor = connection.cursor()
                
                request_data = task.get('data', {})
                if isinstance(request_data, list) and len(request_data) > 0:
                    request_params = request_data[0]
                else:
                    request_params = {}
                
                insert_query = """
                    INSERT INTO serp_logs (
                        keyword_id, keyword_text, location_code, language_code,
                        device, depth, total_items, organic_count, paid_count,
                        maps_count, shopping_count, has_ads, has_maps,
                        has_our_site, has_school_sites, intent_type,
                        school_percentage, cost, raw_response, parsed_items,
                        analysis_result
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                
                insert_values = (
                    keyword_id,
                    keyword_text or '',
                    request_params.get('location_code', 0),
                    request_params.get('language_code', ''),
                    request_params.get('device', 'desktop'),
                    request_params.get('depth', 0),
                    len(items),
                    total_organic_sites,
                    len(paid_results),
                    len(maps_results),
                    0,
                    has_ads,
                    has_google_maps,
                    has_our_site,
                    has_school_sites,
                    intent_type,
                    school_percentage,
                    task.get('cost', 0),
                    json.dumps(serp_response, ensure_ascii=False),
                    parsed_items_json,
                    analysis_result_json
                )
                
                cursor.execute(insert_query, insert_values)
                inserted_id = cursor.lastrowid
                connection.commit()
                cursor.close()
                
                log_print(f"💾 Сохранено в БД (serp_logs), ID: {inserted_id}\n")
                
            except Exception as e:
                log_print(f"❌ Ошибка сохранения в БД: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Возвращаем результат
        return {
            'has_ads': has_ads,
            'has_school_sites': has_school_sites,
            'has_google_maps': has_google_maps,
            'has_our_site': has_our_site,
            'our_organic_position': our_organic_position,
            'our_actual_position': our_actual_position,
            'intent_type': intent_type,
            'stats': {
                'total_organic': total_organic_sites,
                'paid_count': len(paid_results),
                'maps_count': len(maps_results),
                'school_percentage': round(school_percentage, 1)
            }
        }
        
    except Exception as e:
        log_print(f"❌ Error parsing SERP: {str(e)}")
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