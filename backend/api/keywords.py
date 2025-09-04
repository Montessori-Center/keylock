# api/keywords.py - версия с прямым подключением к БД
from flask import Blueprint, request, jsonify
from config import Config
import pymysql

keywords_bp = Blueprint('keywords', __name__)

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

@keywords_bp.route('/list/<int:ad_group_id>', methods=['GET'])
def get_keywords(ad_group_id):
    """Получение списка ключевых слов для группы объявлений"""
    print(f"\n=== get_keywords called for ad_group_id: {ad_group_id} ===")
    
    connection = None
    try:
        # Прямое подключение к БД
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Запрос ключевых слов
        query = """
            SELECT 
                id, keyword, criterion_type, max_cpc, max_cpm, status,
                comment, has_ads, has_school_sites, has_google_maps,
                has_our_site, intent_type, recommendation,
                avg_monthly_searches, three_month_change, yearly_change,
                competition, competition_percent, min_top_of_page_bid,
                max_top_of_page_bid
            FROM keywords 
            WHERE ad_group_id = %s 
            AND status != 'Removed'
        """
        
        cursor.execute(query, (ad_group_id,))
        keywords = cursor.fetchall()
        
        print(f"Found {len(keywords)} keywords for ad_group_id {ad_group_id}")
        
        # Преобразуем данные для frontend
        keywords_data = []
        for row in keywords:
            # Преобразуем Decimal в float и bool значения
            keyword_dict = {
                'id': row['id'],
                'keyword': row['keyword'],
                'criterion_type': row['criterion_type'],
                'max_cpc': float(row['max_cpc']) if row['max_cpc'] else None,
                'max_cpm': float(row['max_cpm']) if row['max_cpm'] else None,
                'status': row['status'],
                'comment': row['comment'],
                'has_ads': bool(row['has_ads']),
                'has_school_sites': bool(row['has_school_sites']),
                'has_google_maps': bool(row['has_google_maps']),
                'has_our_site': bool(row['has_our_site']),
                'intent_type': row['intent_type'],
                'recommendation': row['recommendation'],
                'avg_monthly_searches': row['avg_monthly_searches'],
                'three_month_change': float(row['three_month_change']) if row['three_month_change'] else None,
                'yearly_change': float(row['yearly_change']) if row['yearly_change'] else None,
                'competition': row['competition'],
                'competition_percent': float(row['competition_percent']) if row['competition_percent'] else None,
                'min_top_of_page_bid': float(row['min_top_of_page_bid']) if row['min_top_of_page_bid'] else None,
                'max_top_of_page_bid': float(row['max_top_of_page_bid']) if row['max_top_of_page_bid'] else None
            }
            keywords_data.append(keyword_dict)
            print(f"  - {keyword_dict['id']}: {keyword_dict['keyword']}")
        
        # Статистика
        total_count = len(keywords_data)
        commercial_count = sum(1 for k in keywords_data if k.get('intent_type') == 'Коммерческий')
        keyword_texts = [k['keyword'].lower() for k in keywords_data]
        duplicates_count = len(keyword_texts) - len(set(keyword_texts))
        
        cursor.close()
        
        result = {
            'success': True,
            'data': keywords_data,
            'stats': {
                'total': total_count,
                'commercial': commercial_count,
                'duplicates': duplicates_count
            }
        }
        
        print(f"Returning {len(keywords_data)} keywords successfully")
        return jsonify(result)
        
    except Exception as e:
        print(f"!!! ERROR in get_keywords: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e),
            'data': [],
            'stats': {
                'total': 0,
                'commercial': 0,
                'duplicates': 0
            }
        })
    finally:
        if connection:
            connection.close()

@keywords_bp.route('/bulk-action', methods=['POST'])
def bulk_action():
    """Массовые действия над ключевыми словами"""
    connection = None
    try:
        data = request.json
        action = data.get('action')
        keyword_ids = data.get('keyword_ids', [])
        
        if not keyword_ids and action not in ['paste']:
            return jsonify({'success': False, 'error': 'No keywords selected'}), 400
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        if action == 'delete':
            placeholders = ','.join(['%s'] * len(keyword_ids))
            cursor.execute(f"UPDATE keywords SET status = 'Removed' WHERE id IN ({placeholders})", keyword_ids)
            connection.commit()
        
        elif action == 'pause':
            placeholders = ','.join(['%s'] * len(keyword_ids))
            cursor.execute(f"UPDATE keywords SET status = 'Paused' WHERE id IN ({placeholders})", keyword_ids)
            connection.commit()
        
        elif action == 'activate':
            placeholders = ','.join(['%s'] * len(keyword_ids))
            cursor.execute(f"UPDATE keywords SET status = 'Enabled' WHERE id IN ({placeholders})", keyword_ids)
            connection.commit()
        
        elif action == 'update_field':
            field = data.get('field')
            value = data.get('value')
            
            allowed_fields = ['criterion_type', 'max_cpc', 'comment', 'intent_type', 'recommendation']
            if field not in allowed_fields:
                return jsonify({'success': False, 'error': f'Field {field} not allowed'}), 400
            
            placeholders = ','.join(['%s'] * len(keyword_ids))
            query = f"UPDATE keywords SET {field} = %s WHERE id IN ({placeholders})"
            cursor.execute(query, [value] + keyword_ids)
            connection.commit()
        
        elif action == 'copy':
            placeholders = ','.join(['%s'] * len(keyword_ids))
            cursor.execute(f"SELECT keyword FROM keywords WHERE id IN ({placeholders})", keyword_ids)
            copied_keywords = [row['keyword'] for row in cursor.fetchall()]
            cursor.close()
            # НЕ закрываем connection здесь - он закроется в finally
            return jsonify({
                'success': True,
                'copied': copied_keywords
            })
        
        elif action == 'copy_data':
            placeholders = ','.join(['%s'] * len(keyword_ids))
            cursor.execute(f"""
                SELECT keyword, criterion_type, max_cpc, max_cpm, status, comment,
                       has_ads, has_school_sites, has_google_maps, has_our_site,
                       intent_type, recommendation, avg_monthly_searches,
                       three_month_change, yearly_change, competition, competition_percent,
                       min_top_of_page_bid, max_top_of_page_bid
                FROM keywords 
                WHERE id IN ({placeholders})
            """, keyword_ids)
            
            copied_data = []
            for row in cursor.fetchall():
                # Преобразуем Decimal в float для JSON сериализации
                data_dict = {
                    'keyword': row['keyword'],
                    'criterion_type': row['criterion_type'],
                    'max_cpc': float(row['max_cpc']) if row['max_cpc'] else None,
                    'max_cpm': float(row['max_cpm']) if row['max_cpm'] else None,
                    'status': row['status'],
                    'comment': row['comment'],
                    'has_ads': row['has_ads'],
                    'has_school_sites': row['has_school_sites'],
                    'has_google_maps': row['has_google_maps'],
                    'has_our_site': row['has_our_site'],
                    'intent_type': row['intent_type'],
                    'recommendation': row['recommendation'],
                    'avg_monthly_searches': row['avg_monthly_searches'],
                    'three_month_change': float(row['three_month_change']) if row['three_month_change'] else None,
                    'yearly_change': float(row['yearly_change']) if row['yearly_change'] else None,
                    'competition': row['competition'],
                    'competition_percent': float(row['competition_percent']) if row['competition_percent'] else None,
                    'min_top_of_page_bid': float(row['min_top_of_page_bid']) if row['min_top_of_page_bid'] else None,
                    'max_top_of_page_bid': float(row['max_top_of_page_bid']) if row['max_top_of_page_bid'] else None
                }
                copied_data.append(data_dict)
            
            cursor.close()
            return jsonify({
                'success': True,
                'copied_data': copied_data
            })
        
        else:
            return jsonify({'success': False, 'error': f'Unknown action: {action}'}), 400
        
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': f'Action {action} applied to {len(keyword_ids)} keywords'
        })
        
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error in bulk_action: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection:
            try:
                connection.close()
            except:
                pass  # Игнорируем если уже закрыто

@keywords_bp.route('/paste', methods=['POST'])
def paste_keywords():
    """Вставка скопированных данных"""
    connection = None
    try:
        data = request.json
        ad_group_id = data.get('ad_group_id')
        paste_data = data.get('paste_data', [])
        paste_type = data.get('paste_type', 'keywords')
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Получаем campaign_id
        cursor.execute("SELECT campaign_id FROM ad_groups WHERE id = %s", (ad_group_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'success': False, 'error': 'Ad group not found'}), 404
        
        campaign_id = result['campaign_id']
        added_count = 0
        
        if paste_type == 'keywords':
            for keyword_text in paste_data:
                cursor.execute(
                    "SELECT id FROM keywords WHERE ad_group_id = %s AND keyword = %s",
                    (ad_group_id, keyword_text)
                )
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO keywords (
                            campaign_id, ad_group_id, keyword, criterion_type, 
                            status, max_cpc
                        ) VALUES (%s, %s, %s, 'Phrase', 'Enabled', 3.61)
                    """, (campaign_id, ad_group_id, keyword_text))
                    added_count += 1
        
        connection.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': f'Pasted {added_count} keywords'
        })
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error in paste_keywords: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection:
            connection.close()