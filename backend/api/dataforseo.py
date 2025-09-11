# api/dataforseo.py
from flask import Blueprint, request, jsonify
from app import db
from models.keyword import Keyword, AdGroup
from typing import Dict
from services.dataforseo_client import get_dataforseo_client, DataForSeoClient
from sqlalchemy import and_

dataforseo_bp = Blueprint('dataforseo', __name__)

@dataforseo_bp.route('/get-keywords', methods=['POST'])
def get_new_keywords():
    """Получение новой выдачи ключевых слов через DataForSeo"""
    try:
        data = request.json
        seed_keywords = data.get('seed_keywords', [])
        ad_group_id = data.get('ad_group_id')
        
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
        
        if not seed_keywords:
            return jsonify({'success': False, 'error': 'No seed keywords provided'}), 400
        
        # Получаем группу объявлений
        ad_group = AdGroup.query.get(ad_group_id)
        if not ad_group:
            return jsonify({'success': False, 'error': 'Ad group not found'}), 404
        
        # Логирование запроса
        print(f"DataForSeo request parameters:")
        print(f"  - Seed keywords: {len(seed_keywords)}")
        print(f"  - Location: {location_name or f'code {location_code}'}")
        print(f"  - Language: {language_code}")
        print(f"  - Limit: {limit}")
        print(f"  - Date range: {date_from} to {date_to}")
        print(f"  - Include SERP: {include_serp_info}")
        print(f"  - Include Clickstream: {include_clickstream_data}")
        print(f"  - Sort by: {sort_by}")
        
        # Запрос к DataForSeo (Live режим)
        try:
            # Получаем клиент с проверкой настроек
            dataforseo_client = get_dataforseo_client()
            
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
            
            # Проверяем статус ответа
            if not response.get('tasks'):
                return jsonify({
                    'success': False,
                    'error': 'No data received from DataForSeo'
                }), 500
            
            # Проверяем первую задачу
            task = response['tasks'][0]
            if task.get('status_code') != 20000:
                return jsonify({
                    'success': False,
                    'error': f"DataForSeo error: {task.get('status_message', 'Unknown error')}"
                }), 500
            
            # Получаем стоимость запроса
            request_cost = task.get('cost', 0.05)
            
        except ValueError as credentials_error:
            return jsonify({
                'success': False,
                'error': f'DataForSeo API не настроен: {str(credentials_error)}'
            }), 400
        except Exception as e:
            print(f"DataForSeo API error: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'DataForSeo API error: {str(e)}'
            }), 500
        
        # Парсим ответ
        keywords_data = dataforseo_client.parse_keywords_response(response)
        
        print(f"Received {len(keywords_data)} keywords from DataForSeo")
        print(f"Request cost: ${request_cost}")
        
        # Добавляем ключевые слова в БД
        added_count = 0
updated_count = 0
errors = []

for kw_data in keywords_data:
    try:
        keyword_text = kw_data['keyword']
        
        # Проверяем, не существует ли уже
        existing = Keyword.query.filter(
            and_(
                Keyword.ad_group_id == ad_group_id,
                Keyword.keyword == keyword_text
            )
        ).first()
        
        if existing:
            # ОБНОВЛЯЕМ существующее ключевое слово ВСЕМИ свежими данными
            print(f"🔄 Обновляем существующее ключевое слово: {keyword_text}")
            
            # Основные метрики (заменяем на свежие)
            existing.avg_monthly_searches = kw_data.get('avg_monthly_searches', 0)
            existing.competition = kw_data.get('competition', 'Неизвестно')
            existing.competition_percent = kw_data.get('competition_percent', 0)
            existing.min_top_of_page_bid = kw_data.get('min_top_of_page_bid', 0)
            existing.max_top_of_page_bid = kw_data.get('max_top_of_page_bid', 0)
            existing.three_month_change = kw_data.get('three_month_change')
            existing.yearly_change = kw_data.get('yearly_change')
            
            # CPC - обновляем если есть свежее значение
            new_cpc = kw_data.get('cpc')
            if new_cpc and new_cpc > 0:
                existing.max_cpc = new_cpc
                print(f"  📊 Обновлен CPC: {existing.max_cpc}")
            
            # SERP данные - обновляем если включены в запросе
            if include_serp_info:
                existing.has_ads = kw_data.get('has_ads', False)
                existing.has_google_maps = kw_data.get('has_maps', False)
                
                # Определяем свежий тип интента
                new_intent = determine_intent_type(kw_data)
                existing.intent_type = new_intent
                print(f"  🎯 Обновлен тип интента: {new_intent}")
            
            # Обновляем временные метки
            from datetime import datetime
            existing.updated_at = datetime.utcnow()
            
            updated_count += 1
            continue
        
        # Создаем новое ключевое слово
        print(f"➕ Добавляем новое ключевое слово: {keyword_text}")
        
        keyword = Keyword(
            campaign_id=ad_group.campaign_id,
            ad_group_id=ad_group_id,
            keyword=keyword_text,
            criterion_type='Phrase',
            status='Enabled',
            
            # Метрики из DataForSeo
            avg_monthly_searches=kw_data.get('avg_monthly_searches', 0),
            competition=kw_data.get('competition', 'Неизвестно'),
            competition_percent=kw_data.get('competition_percent', 0),
            min_top_of_page_bid=kw_data.get('min_top_of_page_bid', 0),
            max_top_of_page_bid=kw_data.get('max_top_of_page_bid', 0),
            three_month_change=kw_data.get('three_month_change'),
            yearly_change=kw_data.get('yearly_change'),
            
            # CPC из DataForSeo
            max_cpc=kw_data.get('cpc', 3.61),
            
            # Данные из SERP (если включены)
            has_ads=kw_data.get('has_ads', False) if include_serp_info else False,
            has_google_maps=kw_data.get('has_maps', False) if include_serp_info else False,
            
            # Определяем тип интента
            intent_type=determine_intent_type(kw_data) if include_serp_info else 'Информационный'
        )
        
        db.session.add(keyword)
        added_count += 1
        
    except Exception as e:
        errors.append(f"Error processing '{kw_data.get('keyword', 'unknown')}': {str(e)}")
        print(f"❌ Error processing keyword: {e}")

# Сохраняем в БД
try:
    db.session.commit()
    print(f"✅ Сохранено в БД: добавлено {added_count}, обновлено {updated_count}")
except Exception as e:
    db.session.rollback()
    print(f"❌ Ошибка сохранения в БД: {str(e)}")
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
        'cost': request_cost
    },
    'cost': request_cost
}

if errors:
    result['errors'] = errors[:10]  # Показываем первые 10 ошибок

return jsonify(result)
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
        
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