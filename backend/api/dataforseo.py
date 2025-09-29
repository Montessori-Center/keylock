# api/dataforseo.py - ПОЛНОСТЬЮ ПЕРЕРАБОТАННАЯ ВЕРСИЯ
from flask import Blueprint, request, jsonify
from config import Config
import pymysql
from typing import Dict
from datetime import datetime
from services.dataforseo_client import get_dataforseo_client, DataForSeoClient
from api.keywords import get_random_batch_color
import sys

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
                            intent_type = %s,
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
                        kw_data.get('intent_type', 'Информационный'),
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
                            yearly_change, max_cpc, intent_type, is_new, batch_color
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                        kw_data.get('intent_type', 'Информационный'),
                        True,  # is_new
                        batch_color  # batch_color
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
    """Применение SERP анализа к выбранным ключевым словам"""
    connection = None
    try:
        data = request.json
        keyword_ids = data.get('keyword_ids', [])
        params = data.get('params', {})
        
        if not keyword_ids:
            return jsonify({'success': False, 'error': 'No keywords selected'}), 400
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Получаем ключевые слова
        placeholders = ','.join(['%s'] * len(keyword_ids))
        cursor.execute(f"""
            SELECT id, keyword, campaign_id 
            FROM keywords 
            WHERE id IN ({placeholders})
        """, keyword_ids)
        keywords_data = cursor.fetchall()
        
        if not keywords_data:
            return jsonify({'success': False, 'error': 'Keywords not found'}), 404
        
        campaign_id = keywords_data[0]['campaign_id']
        
        dataforseo_client = get_dataforseo_client()
        updated_count = 0
        errors = []
        total_cost = 0
        
        for kw in keywords_data:
            try:
                # Выполняем SERP запрос
                serp_response = dataforseo_client.get_serp(
                    keyword=kw['keyword'],
                    location_code=params.get('location_code', 2804),
                    language_code=params.get('language_code', 'ru'),
                    device=params.get('device', 'desktop'),
                    os=params.get('os', 'windows'),
                    depth=params.get('depth', 10)
                )
                
                # Анализируем результаты
                if serp_response.get('tasks') and serp_response['tasks'][0].get('result'):
                    task = serp_response['tasks'][0]
                    items = task['result'][0].get('items', [])
                    
                    # Считаем стоимость
                    total_cost += task.get('cost', 0.01)
                    
                    has_ads = any(item.get('type') == 'paid' for item in items)
                    has_maps = any(item.get('type') in ['maps', 'local_pack'] for item in items)
                    has_our_site = check_our_site_in_serp(items, campaign_id)
                    intent_type = determine_intent_from_serp(items)
                    
                    # Обновляем в БД
                    cursor.execute("""
                        UPDATE keywords 
                        SET 
                            has_ads = %s,
                            has_google_maps = %s,
                            has_our_site = %s,
                            intent_type = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """, (has_ads, has_maps, has_our_site, intent_type, kw['id']))
                    
                    updated_count += 1
                    
            except Exception as e:
                errors.append(f"Error for '{kw['keyword']}': {str(e)}")
        
        connection.commit()
        
        return jsonify({
            'success': True,
            'message': f'SERP анализ применен к {updated_count} ключевым словам',
            'updated': updated_count,
            'errors': errors[:10] if errors else [],
            'cost': total_cost
        })
        
    except Exception as e:
        if connection:
            connection.rollback()
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

def check_our_site_in_serp(serp_items, campaign_id):
    """Проверяет наличие нашего сайта в SERP выдаче"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT domain 
            FROM campaign_sites 
            WHERE campaign_id = %s
        """, (campaign_id,))
        
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if not result or not result['domain']:
            return False
        
        our_domain = result['domain'].lower()
        
        for item in serp_items:
            if item.get('type') in ['organic', 'paid', 'local_pack', 'maps']:
                url = item.get('url', '').lower()
                domain = item.get('domain', '').lower()
                
                if our_domain in url or our_domain == domain:
                    return True
        
        return False
        
    except Exception as e:
        log_print(f"❌ Error checking our site: {e}")
        return False

def determine_intent_from_serp(serp_items):
    """Определяет интент на основе типов элементов в SERP"""
    commercial_signals = 0
    informational_signals = 0
    
    for item in serp_items:
        item_type = item.get('type', '')
        
        if item_type in ['paid', 'shopping', 'local_pack']:
            commercial_signals += 1
        elif item_type in ['featured_snippet', 'people_also_ask', 'knowledge_graph']:
            informational_signals += 1
    
    if commercial_signals > informational_signals:
        return 'Коммерческий'
    elif informational_signals > 0:
        return 'Информационный'
    else:
        return 'Смешанный'

def determine_intent_type(keyword_data: Dict) -> str:
    """Определение типа интента на основе данных ключевого слова"""
    keyword = keyword_data.get('keyword', '').lower()
    serp_types = keyword_data.get('serp_item_types', [])
    
    # Анализ SERP элементов (приоритетный метод)
    if serp_types:
        commercial_serp_types = {'shopping', 'paid', 'google_ads', 'local_pack', 'maps'}
        if any(serp_type in commercial_serp_types for serp_type in serp_types):
            return 'Коммерческий'
        
        informational_serp_types = {'featured_snippet', 'people_also_ask', 'knowledge_graph', 'video'}
        if any(serp_type in informational_serp_types for serp_type in serp_types):
            return 'Информационный'
        
        if 'knowledge_panel' in serp_types:
            return 'Навигационный'
    
    # Анализ ключевых слов (резервный метод)
    commercial_words = [
        'купить', 'цена', 'стоимость', 'заказать', 'магазин', 'недорого',
        'акция', 'скидка', 'распродажа', 'доставка', 'оплата', 'прайс'
    ]
    
    transactional_words = [
        'скачать', 'download', 'регистрация', 'вход', 'login',
        'подписка', 'оформить', 'получить', 'забронировать'
    ]
    
    informational_words = [
        'как', 'что', 'почему', 'зачем', 'когда', 'какой', 'где', 'кто',
        'инструкция', 'руководство', 'обзор', 'отзывы', 'рейтинг'
    ]
    
    navigational_words = [
        'сайт', 'официальный', 'website', '.com', '.ua', '.ru',
        'facebook', 'instagram', 'youtube', 'google'
    ]
    
    # Проверка по ключевым словам
    if any(word in keyword for word in commercial_words):
        return 'Коммерческий'
    
    if any(word in keyword for word in transactional_words):
        return 'Транзакционный'
    
    if any(word in keyword for word in navigational_words):
        return 'Навигационный'
    
    if any(word in keyword for word in informational_words):
        return 'Информационный'
    
    return 'Информационный'