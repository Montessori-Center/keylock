# api/dataforseo.py
from flask import Blueprint, request, jsonify
from app import db
from models.keyword import Keyword, AdGroup
from typing import Dict
from services.dataforseo_client import dataforseo_client
from sqlalchemy import and_

dataforseo_bp = Blueprint('dataforseo', __name__)

@dataforseo_bp.route('/get-keywords', methods=['POST'])
def get_new_keywords():
    """Получение новой выдачи ключевых слов через DataForSeo"""
    try:
        data = request.json
        seed_keywords = data.get('seed_keywords', [])
        ad_group_id = data.get('ad_group_id')
        location_code = data.get('location_code', 2804)  # Ukraine
        language_code = data.get('language_code', 'ru')
        limit = data.get('limit', 700)
        
        if not seed_keywords:
            return jsonify({'success': False, 'error': 'No seed keywords provided'}), 400
        
        # Получаем группу объявлений
        ad_group = AdGroup.query.get(ad_group_id)
        if not ad_group:
            return jsonify({'success': False, 'error': 'Ad group not found'}), 404
        
        # Логирование запроса
        print(f"DataForSeo request: {len(seed_keywords)} seed keywords, location={location_code}, lang={language_code}")
        
        # Запрос к DataForSeo (Live режим)
        try:
            response = dataforseo_client.get_keywords_for_keywords(
                keywords=seed_keywords,
                location_code=location_code,
                language_code=language_code,
                limit=limit,
                include_serp_info=True
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
            
        except Exception as e:
            print(f"DataForSeo API error: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'DataForSeo API error: {str(e)}'
            }), 500
        
        # Парсим ответ
        keywords_data = dataforseo_client.parse_keywords_response(response)
        
        print(f"Received {len(keywords_data)} keywords from DataForSeo")
        
        # Добавляем ключевые слова в БД
        added_count = 0
        skipped_count = 0
        errors = []
        
        for kw_data in keywords_data:
            try:
                # Проверяем, не существует ли уже
                existing = Keyword.query.filter(
                    and_(
                        Keyword.ad_group_id == ad_group_id,
                        Keyword.keyword == kw_data['keyword']
                    )
                ).first()
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Создаем новое ключевое слово
                keyword = Keyword(
                    campaign_id=ad_group.campaign_id,
                    ad_group_id=ad_group_id,
                    keyword=kw_data['keyword'],
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
                    
                    # CPC по умолчанию из DataForSeo или стандартное значение
                    max_cpc=kw_data.get('cpc', 3.61),
                    
                    # Определяем тип интента на основе SERP
                    intent_type=determine_intent_type(kw_data)
                )
                
                db.session.add(keyword)
                added_count += 1
                
            except Exception as e:
                errors.append(f"Error adding '{kw_data.get('keyword', 'unknown')}': {str(e)}")
                print(f"Error adding keyword: {e}")
        
        # Сохраняем в БД
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'Database error: {str(e)}'
            }), 500
        
        # Формируем ответ
        result = {
            'success': True,
            'message': f'Added {added_count} new keywords from {len(keywords_data)} results',
            'stats': {
                'total_results': len(keywords_data),
                'added': added_count,
                'skipped': skipped_count,
                'errors': len(errors)
            }
        }
        
        if errors:
            result['errors'] = errors[:10]  # Показываем первые 10 ошибок
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@dataforseo_bp.route('/check-balance', methods=['GET'])
def check_balance():
    """Проверка баланса и статуса аккаунта DataForSeo"""
    try:
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
        locations = dataforseo_client.get_locations(country)
        
        # Парсим популярные локации
        popular = [
            {'code': 2804, 'name': 'Ukraine'},
            {'code': 2840, 'name': 'United States'},
            {'code': 2643, 'name': 'Russia'},
            {'code': 2276, 'name': 'Germany'},
        ]
        
        return jsonify({
            'success': True,
            'popular': popular,
            'all': locations.get('tasks', [{}])[0].get('result', []) if locations else []
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def determine_intent_type(keyword_data: Dict) -> str:
    """Определение типа интента на основе данных ключевого слова"""
    
    keyword = keyword_data.get('keyword', '').lower()
    serp_types = keyword_data.get('serp_item_types', [])
    
    # Коммерческие индикаторы
    commercial_words = ['купить', 'цена', 'стоимость', 'заказать', 'магазин', 'shop', 'buy', 'price']
    
    # Транзакционные индикаторы
    transactional_words = ['скачать', 'download', 'регистрация', 'вход', 'login']
    
    # Информационные индикаторы
    informational_words = ['как', 'что', 'почему', 'зачем', 'когда', 'какой', 'how', 'what', 'why', 'when']
    
    # Навигационные индикаторы (бренды, сайты)
    navigational_words = ['сайт', 'официальный', 'website', 'official', '.com', '.ua']
    
    # Проверка SERP типов
    if 'shopping' in serp_types or 'paid' in serp_types:
        return 'Коммерческий'
    
    if 'local_pack' in serp_types or 'maps' in serp_types:
        return 'Коммерческий'
    
    # Проверка ключевых слов
    if any(word in keyword for word in commercial_words):
        return 'Коммерческий'
    
    if any(word in keyword for word in transactional_words):
        return 'Транзакционный'
    
    if any(word in keyword for word in navigational_words):
        return 'Навигационный'
    
    if any(word in keyword for word in informational_words):
        return 'Информационный'
    
    # По умолчанию
    return 'Информационный'