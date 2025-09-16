# api/dataforseo.py
from flask import Blueprint, request, jsonify
from config import Config
import pymysql
from typing import Dict
from datetime import datetime
from services.dataforseo_client import get_dataforseo_client, DataForSeoClient
import sys

dataforseo_bp = Blueprint('dataforseo', __name__)

# Принудительный flush для логов
def log_print(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

@dataforseo_bp.route('/test', methods=['GET', 'POST'])
def test_endpoint():
    """Простой тест endpoint"""
    try:
        print("🧪 TEST ENDPOINT ВЫЗВАН!")
        print(f"   Method: {request.method}")
        if request.method == 'POST':
            data = request.get_json()
            print(f"   Data: {data}")
        
        return jsonify({
            'success': True,
            'message': 'Test endpoint работает!',
            'method': request.method,
            'timestamp': str(datetime.utcnow())
        })
    except Exception as e:
        print(f"❌ Test endpoint error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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

@dataforseo_bp.route('/get-keywords-simple', methods=['POST'])
def get_keywords_simple():
    """Простой тест без обращения к DataForSeo"""
    try:
        print("🧪 SIMPLE TEST ВЫЗВАН!")
        data = request.get_json()
        print(f"   Получены данные: {list(data.keys()) if data else 'None'}")
        
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
        print(f"❌ Simple test error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dataforseo_bp.route('/get-keywords', methods=['POST'])
def get_new_keywords():
    """Получение новой выдачи ключевых слов через DataForSeo"""
    connection = None
    
    # КРИТИЧЕСКОЕ ЛОГИРОВАНИЕ - ДОЛЖНО ПОЯВИТЬСЯ В ЛЮБОМ СЛУЧАЕ
    print("!" * 50)
    print("🚨 GET-KEYWORDS ENDPOINT ВЫЗВАН!")
    print(f"🚨 Method: {request.method}")
    print(f"🚨 Content-Type: {request.content_type}")
    print(f"🚨 Headers: {dict(request.headers)}")
    sys.stdout.flush()
    
    try:
        # Пробуем получить данные
        try:
            data = request.get_json()
            print(f"🚨 JSON DATA: {data}")
        except Exception as json_error:
            print(f"🚨 JSON ERROR: {json_error}")
            return jsonify({'success': False, 'error': f'JSON parse error: {str(json_error)}'}), 400
        
        if not data:
            print("🚨 NO DATA IN REQUEST")
            return jsonify({'success': False, 'error': 'No data in request'}), 400
        
        print("🚨 PROCESSING REQUEST...")
        sys.stdout.flush()
        
        log_print("=" * 50)
        log_print("🚀 Начало обработки запроса get-keywords")
        log_print("=" * 50)
        
        data = request.json
        log_print(f"📥 Получены данные: {list(data.keys()) if data else 'None'}")
        
        seed_keywords = data.get('seed_keywords', [])
        ad_group_id = data.get('ad_group_id')
        
        log_print(f"🔑 Seed keywords count: {len(seed_keywords)}")
        log_print(f"🔑 Первые 3 keywords: {seed_keywords[:3] if seed_keywords else 'Нет'}")
        log_print(f"🏷️  Ad group ID: {ad_group_id}")
        
        # Все параметры из frontend
        location_name = data.get('location_name')
        location_code = data.get('location_code', 2804)
        language_code = data.get('language_code', 'ru')
        limit = data.get('limit', 700)
        search_partners = data.get('search_partners', False)
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        include_seed_keyword = data.get('include_seed_keyword', True)
        include_clickstream_data = data.get('include_clickstream_data', False)
        include_serp_info = data.get('include_serp_info', False)
        sort_by = data.get('sort_by', 'relevance')
        
        log_print(f"📋 Параметры DataForSeo запроса:")
        log_print(f"  - Seed keywords: {seed_keywords[:2]}... ({len(seed_keywords)} total)")
        log_print(f"  - Location: {location_name or f'code {location_code}'}")
        log_print(f"  - Language: {language_code}")
        log_print(f"  - Limit: {limit}")
        log_print(f"  - Date range: {date_from} to {date_to}")
        log_print(f"  - Include SERP: {include_serp_info}")
        log_print(f"  - Include Clickstream: {include_clickstream_data}")
        log_print(f"  - Sort by: {sort_by}")
        
        if not seed_keywords:
            log_print("❌ Нет seed keywords")
            return jsonify({'success': False, 'error': 'No seed keywords provided'}), 400
        
        # Подключаемся к БД
        log_print("🔌 Подключение к БД...")
        connection = get_db_connection()
        cursor = connection.cursor()
        log_print("✅ Подключение к БД успешно")
        
        # Получаем группу объявлений
        log_print(f"🔍 Поиск группы объявлений с ID: {ad_group_id}")
        cursor.execute("SELECT * FROM ad_groups WHERE id = %s", (ad_group_id,))
        ad_group = cursor.fetchone()
        
        if not ad_group:
            log_print("❌ Группа объявлений не найдена")
            return jsonify({'success': False, 'error': 'Ad group not found'}), 404
        
        log_print(f"✅ Найдена группа: {ad_group['name']}")
        campaign_id = ad_group['campaign_id']
        
        # Запрос к DataForSeo (Live режим)
        try:
            log_print("🔌 Инициализация DataForSeo клиента...")
            # Получаем клиент с проверкой настроек
            dataforseo_client = get_dataforseo_client()
            log_print("✅ DataForSeo клиент готов")
            
            # ИСПРАВЛЕНИЕ: Инициализируем keywords_data до API запроса
            keywords_data = []
            
            log_print("📡 Отправка запроса к DataForSeo API...")
            response = dataforseo_client.get_keywords_for_keywords(
                keywords=seed_keywords,
                location_code=location_code,
                language_code=language_code,
                search_partners=search_partners,
                sort_by=sort_by,
                limit=limit,
                include_seed_keyword=include_seed_keyword,
                include_clickstream_data=include_clickstream_data,
                include_serp_info=include_serp_info
            )
            
            log_print(f"📨 Получен ответ от DataForSeo")
            log_print(f"📊 Структура ответа: {list(response.keys()) if response else 'None'}")
            
            # Проверяем статус ответа
            if not response.get('tasks'):
                log_print("❌ Нет tasks в ответе")
                log_print(f"📊 Полный ответ: {response}")
                return jsonify({
                    'success': False,
                    'error': 'No data received from DataForSeo'
                }), 500
            
            # Проверяем первую задачу
            task = response['tasks'][0]
            task_status = task.get('status_code')
            log_print(f"📋 Status code: {task_status}")
            log_print(f"📋 Status message: {task.get('status_message', 'No message')}")
            
            if task_status != 20000:
                error_msg = task.get('status_message', 'Unknown error')
                log_print(f"❌ DataForSeo ошибка: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': f"DataForSeo error: {error_msg}"
                }), 500
            
            # Получаем стоимость запроса
            request_cost = task.get('cost', 0.05)
            log_print(f"💰 Стоимость запроса: ${request_cost}")
            
        except ValueError as credentials_error:
            log_print(f"🔑 Ошибка credentials: {str(credentials_error)}")
            return jsonify({
                'success': False,
                'error': f'DataForSeo API не настроен: {str(credentials_error)}'
            }), 400
        except Exception as e:
            log_print(f"💥 DataForSeo API ошибка: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'DataForSeo API error: {str(e)}'
            }), 500
        
        # Парсим ответ
        log_print("🔄 Парсинг ответа DataForSeo...")
        
        # Основной парсинг с обработкой ошибок
        try:
            keywords_data = dataforseo_client.parse_keywords_response(response)
            log_print(f"📈 Получено ключевых слов после основного парсинга: {len(keywords_data)}")
        except Exception as parse_error:
            log_print(f"❌ Ошибка основного парсинга: {str(parse_error)}")
            import traceback
            traceback.print_exc()
            keywords_data = []  # Обеспечиваем что keywords_data всегда список
        
        # ЕСЛИ ПАРСИНГ НЕ РАБОТАЕТ - ПРОБУЕМ ПРОСТОЙ:
        if len(keywords_data) == 0:
            log_print("❌ ОСНОВНОЙ ПАРСИНГ НЕ РАБОТАЕТ! Попробуем простой парсинг...")
            
            # Простой парсинг напрямую
            simple_keywords = []
            if response.get('tasks') and len(response['tasks']) > 0:
                task = response['tasks'][0]
                if task.get('result') and len(task['result']) > 0:
                    result_items = task['result']
                    for item in result_items:
                        simple_keywords.append({
                            'keyword': item.get('keyword', 'Unknown'),
                            'avg_monthly_searches': item.get('search_volume', 0),
                            'competition': 'Средняя',  # Временно
                            'competition_percent': item.get('competition_index', 0),
                            'min_top_of_page_bid': item.get('low_top_of_page_bid', 0),
                            'max_top_of_page_bid': item.get('high_top_of_page_bid', 0),
                            'cpc': item.get('cpc', 0),
                            'has_ads': False,  # Временно
                            'has_maps': False,  # Временно
                        })
            
            log_print(f"🔧 Простой парсинг дал: {len(simple_keywords)} ключевых слов")
            if len(simple_keywords) > 0:
                log_print(f"   Пример: {simple_keywords[0]}")
                keywords_data = simple_keywords  # Используем простой парсинг
        
        if len(keywords_data) > 0:
            log_print(f"📝 Пример первого ключевого слова: {keywords_data[0].get('keyword', 'N/A')}")
        
        # Добавляем ключевые слова в БД
        added_count = 0
        updated_count = 0
        errors = []
        
        for kw_data in keywords_data:
            try:
                keyword_text = kw_data['keyword']
                
                # Проверяем, не существует ли уже
                cursor.execute(
                    "SELECT * FROM keywords WHERE ad_group_id = %s AND keyword = %s",
                    (ad_group_id, keyword_text)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # ОБНОВЛЯЕМ существующее ключевое слово ВСЕМИ свежими данными
                    log_print(f"🔄 Обновляем существующее ключевое слово: {keyword_text}")
                    
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
                            has_ads = %s,
                            has_google_maps = %s,
                            intent_type = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """
                    
                    # Данные для обновления
                    new_cpc = kw_data.get('cpc')
                    update_data = (
                        kw_data.get('avg_monthly_searches', 0),
                        kw_data.get('competition', 'Неизвестно'),
                        kw_data.get('competition_percent', 0),
                        kw_data.get('min_top_of_page_bid', 0),
                        kw_data.get('max_top_of_page_bid', 0),
                        kw_data.get('three_month_change'),
                        kw_data.get('yearly_change'),
                        new_cpc if new_cpc and new_cpc > 0 else existing['max_cpc'],
                        kw_data.get('has_ads', False) if include_serp_info else existing['has_ads'],
                        kw_data.get('has_maps', False) if include_serp_info else existing['has_google_maps'],
                        determine_intent_type(kw_data) if include_serp_info else existing['intent_type'],
                        existing['id']
                    )
                    
                    cursor.execute(update_query, update_data)
                    updated_count += 1
                    continue
                
                # Создаем новое ключевое слово
                log_print(f"➕ Добавляем новое ключевое слово: {keyword_text}")
                
                insert_query = """
                    INSERT INTO keywords (
                        campaign_id, ad_group_id, keyword, criterion_type, status,
                        avg_monthly_searches, competition, competition_percent,
                        min_top_of_page_bid, max_top_of_page_bid, three_month_change,
                        yearly_change, max_cpc, has_ads, has_google_maps, intent_type,
                        is_new
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    kw_data.get('has_ads', False) if include_serp_info else False,
                    kw_data.get('has_maps', False) if include_serp_info else False,
                    determine_intent_type(kw_data) if include_serp_info else 'Информационный',
                    True  # is_new = TRUE для новых слов
                )
                
                cursor.execute(insert_query, insert_data)
                added_count += 1
                
            except Exception as e:
                errors.append(f"Error processing '{kw_data.get('keyword', 'unknown')}': {str(e)}")
                log_print(f"❌ Error processing keyword: {e}")
        
        # Сохраняем в БД
        try:
            connection.commit()
            log_print(f"✅ Сохранено в БД: добавлено {added_count}, обновлено {updated_count}")
        except Exception as e:
            connection.rollback()
            log_print(f"❌ Ошибка сохранения в БД: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Database error: {str(e)}'
            }), 500
        
        # Формируем ответ
        result = {
            'success': True,
            'message': f'Обработано {len(keywords_data)} ключевых слов. Добавлено: {added_count}, обновлено свежими данными: {updated_count}',
            'stats': {
                'total_results': len(keywords_data),
                'added': added_count,
                'updated': updated_count,
                'errors': len(errors),
                'cost': request_cost if 'request_cost' in locals() else 0.05
            },
            'cost': request_cost if 'request_cost' in locals() else 0.05
        }
        
        if errors:
            result['errors'] = errors[:10]  # Показываем первые 10 ошибок
        
        log_print(f"✅ ФИНАЛЬНЫЙ РЕЗУЛЬТАТ: {result}")
        return jsonify(result)
        
    except Exception as e:
        log_print(f"💥 Неожиданная ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
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
        # Создаем временный клиент с переданными данными
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
        
        # Популярные локации с переводом
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
        
        # Основные языки с переводом
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

def determine_intent_type(keyword_data: Dict) -> str:
    """
    Определение типа интента на основе данных ключевого слова
    
    Args:
        keyword_data: Данные ключевого слова из DataForSeo
        
    Returns:
        Тип интента: Коммерческий, Информационный, Навигационный, Транзакционный
    """
    
    keyword = keyword_data.get('keyword', '').lower()
    serp_types = keyword_data.get('serp_item_types', [])
    
    # Анализ SERP элементов (приоритетный метод)
    if serp_types:
        # Коммерческие индикаторы в SERP
        commercial_serp_types = {'shopping', 'paid', 'google_ads', 'local_pack', 'maps'}
        if any(serp_type in commercial_serp_types for serp_type in serp_types):
            return 'Коммерческий'
        
        # Информационные индикаторы в SERP
        informational_serp_types = {'featured_snippet', 'people_also_ask', 'knowledge_graph', 'video'}
        if any(serp_type in informational_serp_types for serp_type in serp_types):
            return 'Информационный'
        
        # Навигационные индикаторы
        if 'knowledge_panel' in serp_types:
            return 'Навигационный'
    
    # Анализ ключевых слов (резервный метод)
    # Коммерческие индикаторы
    commercial_words = [
        'купить', 'цена', 'стоимость', 'заказать', 'магазин', 'недорого', 'дешево',
        'акция', 'скидка', 'распродажа', 'доставка', 'оплата', 'прайс',
        'buy', 'price', 'shop', 'store', 'cheap', 'discount', 'sale', 'order'
    ]
    
    # Транзакционные индикаторы
    transactional_words = [
        'скачать', 'download', 'регистрация', 'вход', 'login', 'signup',
        'подписка', 'оформить', 'получить', 'забронировать'
    ]
    
    # Информационные индикаторы
    informational_words = [
        'как', 'что', 'почему', 'зачем', 'когда', 'какой', 'где', 'кто',
        'инструкция', 'руководство', 'обзор', 'отзывы', 'рейтинг',
        'how', 'what', 'why', 'when', 'where', 'who', 'guide', 'tutorial'
    ]
    
    # Навигационные индикаторы (бренды, сайты)
    navigational_words = [
        'сайт', 'официальный', 'website', 'official', '.com', '.ua', '.ru',
        'facebook', 'instagram', 'youtube', 'google', 'вконтакте'
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
    
    # По умолчанию - информационный
    return 'Информационный'

@dataforseo_bp.route('/estimate-cost', methods=['POST'])
def estimate_cost():
    """Оценка стоимости запроса"""
    try:
        data = request.json
        include_serp = data.get('include_serp_info', False)
        include_clickstream = data.get('include_clickstream_data', False)
        
        # Базовая стоимость
        cost = 0.05
        if include_serp:
            cost += 0.02
        if include_clickstream:
            cost += 0.03
        
        return jsonify({
            'success': True,
            'estimated_cost': cost
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500