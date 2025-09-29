# api/dataforseo.py - ПОЛНОСТЬЮ ПЕРЕРАБОТАННАЯ ВЕРСИЯ
from typing import Dict
from flask import Blueprint, request, jsonify
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
    """Применение SERP анализа к выбранным ключевым словам"""
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
        
        updated_count = 0
        errors = []
        total_cost = 0
        
        # Параметры SERP запроса
        serp_params = {
            'location_code': data.get('location_code', 2804),
            'language_code': data.get('language_code', 'ru'),
            'device': data.get('device', 'desktop'),
            'os': data.get('os', 'windows'),
            'depth': data.get('depth', 10)
        }
        
        for kw in keywords_data:
            try:
                log_print(f"🔍 Выполняем SERP для: {kw['keyword']}")
                
                # Выполняем SERP запрос
                serp_response = dataforseo_client.get_serp(
                    keyword=kw['keyword'],
                    **serp_params
                )
                
                # Парсим результаты
                serp_data = parse_serp_response(serp_response, kw['campaign_id'], connection)
                
                if serp_data:
                    # Обновляем данные в БД
                    cursor.execute("""
                        UPDATE keywords 
                        SET 
                            has_ads = %s,
                            has_school_sites = %s,
                            has_google_maps = %s,
                            has_our_site = %s,
                            intent_type = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """, (
                        serp_data['has_ads'],
                        serp_data['has_school_sites'],
                        serp_data['has_google_maps'],
                        serp_data['has_our_site'],
                        serp_data['intent_type'],
                        kw['id']
                    ))
                    
                    updated_count += 1
                    
                    # Считаем стоимость
                    if serp_response.get('tasks'):
                        total_cost += serp_response['tasks'][0].get('cost', 0.01)
                    
                    log_print(f"✅ Обновлено: {kw['keyword']}")
                    log_print(f"   - has_ads: {serp_data['has_ads']}")
                    log_print(f"   - has_school_sites: {serp_data['has_school_sites']}")
                    log_print(f"   - has_maps: {serp_data['has_google_maps']}")
                    log_print(f"   - has_our_site: {serp_data['has_our_site']}")
                    log_print(f"   - intent_type: {serp_data['intent_type']}")
                else:
                    errors.append(f"No data for '{kw['keyword']}'")
                    
            except Exception as e:
                log_print(f"❌ Error for '{kw['keyword']}': {str(e)}")
                errors.append(f"Error for '{kw['keyword']}': {str(e)}")
        
        connection.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': f'SERP анализ применен к {updated_count} из {len(keywords_data)} ключевых слов',
            'stats': {
                'total': len(keywords_data),
                'updated': updated_count,
                'errors': len(errors)
            },
            'errors': errors[:5] if errors else [],
            'cost': round(total_cost, 4)
        })
        
    except Exception as e:
        if connection:
            connection.rollback()
        log_print(f"❌ SERP analysis error: {str(e)}")
        import traceback
        traceback.print_exc()
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
        
def parse_serp_response(serp_response: Dict, campaign_id: int, connection) -> Dict:
    """
    Парсинг SERP ответа и определение всех необходимых полей
    """
    try:
        if not serp_response.get('tasks'):
            return None
        
        task = serp_response['tasks'][0]
        if task.get('status_code') != 20000:
            log_print(f"❌ SERP error: {task.get('status_message')}")
            return None
        
        if not task.get('result') or len(task['result']) == 0:
            return None
        
        result = task['result'][0]
        items = result.get('items', [])
        
        if not items:
            log_print("⚠️ No items in SERP response")
            return None
        
        # Инициализация результатов
        has_ads = False
        has_google_maps = False
        has_our_site = False
        has_school_sites = False
        
        # Счетчики для определения интента
        total_organic_sites = 0
        school_sites_count = 0
        
        # Получаем домен нашего сайта для кампании
        our_domain = get_campaign_domain(campaign_id, connection)
        log_print(f"📌 Наш домен для кампании {campaign_id}: {our_domain}")
        
        # Получаем список доменов школ-конкурентов
        school_domains = get_school_domains(connection)
        log_print(f"📚 Загружено доменов школ: {len(school_domains)}")
        
        # Анализируем каждый элемент SERP
        for item in items:
            item_type = item.get('type', '')
            
            # Проверка на рекламу
            if item_type in ['paid', 'google_ads', 'shopping', 'commercial_units']:
                has_ads = True
                log_print(f"   💰 Найдена реклама: {item_type}")
            
            # Проверка на Google Maps
            elif item_type in ['local_pack', 'maps', 'map', 'google_maps']:
                has_google_maps = True
                log_print(f"   🗺️ Найдены Google Maps: {item_type}")
            
            # Анализ органических результатов
            elif item_type == 'organic':
                total_organic_sites += 1
                
                # Получаем URL и домен
                url = item.get('url', '').lower()
                domain = item.get('domain', '').lower()
                
                # Убираем www. из домена для сравнения
                clean_domain = domain.replace('www.', '') if domain else ''
                
                # Проверяем наш сайт
                if our_domain and (our_domain in url or our_domain == clean_domain):
                    has_our_site = True
                    log_print(f"   ✅ Найден наш сайт: {domain}")
                
                # Проверка сайтов школ
                if clean_domain in school_domains:
                    school_sites_count += 1
                    has_school_sites = True
                    log_print(f"   🏫 Найден сайт школы: {domain}")
        
        # Определение типа интента по исправленной логике:
        # Коммерческий - если есть сайты школ и их >= 60% от органики
        # Информационный - в противном случае
        
        if has_school_sites and total_organic_sites > 0:
            school_percentage = (school_sites_count / total_organic_sites) * 100
            log_print(f"📊 Процент сайтов школ: {school_percentage:.1f}% ({school_sites_count}/{total_organic_sites})")
            
            if school_percentage >= 60:
                intent_type = 'Коммерческий'
            else:
                intent_type = 'Информационный'
        else:
            # Если нет сайтов школ - всегда информационный
            intent_type = 'Информационный'
        
        log_print(f"📊 SERP анализ завершен:")
        log_print(f"   - Органических сайтов: {total_organic_sites}")
        log_print(f"   - Сайтов школ: {school_sites_count}")
        log_print(f"   - Есть реклама: {has_ads}")
        log_print(f"   - Есть карты: {has_google_maps}")
        log_print(f"   - Есть наш сайт: {has_our_site}")
        log_print(f"   - Есть сайты школ: {has_school_sites}")
        log_print(f"   - Тип интента: {intent_type}")
        
        return {
            'has_ads': has_ads,
            'has_school_sites': has_school_sites,
            'has_google_maps': has_google_maps,
            'has_our_site': has_our_site,
            'intent_type': intent_type
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