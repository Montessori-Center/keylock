# api/keywords.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
from flask import Blueprint, request, jsonify
from config import Config
import pymysql
import random

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
    
# Палитра цветов (такая же как на frontend)
BATCH_COLORS = [
    '#fff2cc', '#e1d5e7', '#dae8fc', '#d5e8d4', '#ffe6cc', '#f8cecc',
    '#e1fffe', '#fff2e6', '#f0e6ff', '#e6f3ff', '#ffe6f2', '#e6ffe6'
]

def get_random_batch_color():
    """Получить рандомный цвет для новой партии"""
    return random.choice(BATCH_COLORS)
    
@keywords_bp.route('/accept-changes', methods=['POST'])
def accept_changes():
    """Принять изменения - убрать подсветку новых слов"""
    connection = None
    try:
        data = request.json
        ad_group_id = data.get('ad_group_id')
        
        if not ad_group_id:
            return jsonify({'success': False, 'error': 'No ad_group_id provided'}), 400
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Сбрасываем флаг is_new для всех ключевых слов группы
        cursor.execute("""
            UPDATE keywords 
            SET is_new = FALSE 
            WHERE ad_group_id = %s AND is_new = TRUE
        """, (ad_group_id,))
        
        affected_rows = cursor.rowcount
        connection.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': f'Принято {affected_rows} новых изменений'
        })
        
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error in accept_changes: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection:
            connection.close()
            
@keywords_bp.route('/reject-changes', methods=['POST'])
def reject_changes():
    """Отклонить изменения - удалить новые ключевые слова"""
    connection = None
    try:
        data = request.json
        ad_group_id = data.get('ad_group_id')
        
        if not ad_group_id:
            return jsonify({'success': False, 'error': 'No ad_group_id provided'}), 400
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Удаляем все новые ключевые слова для данной группы
        cursor.execute("""
            DELETE FROM keywords 
            WHERE ad_group_id = %s AND is_new = TRUE
        """, (ad_group_id,))
        
        affected_rows = cursor.rowcount
        connection.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': f'Отклонено и удалено {affected_rows} новых ключевых слов'
        })
        
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error in reject_changes: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection:
            connection.close()

@keywords_bp.route('/list/<int:ad_group_id>', methods=['GET'])
def get_keywords(ad_group_id):
    """Получение списка ключевых слов для группы объявлений"""
    print(f"\n=== get_keywords called for ad_group_id: {ad_group_id} ===")
    
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # ОБНОВЛЕНО: добавлено поле batch_color в запрос
        query = """
            SELECT 
                id, keyword, criterion_type, max_cpc, max_cpm, status,
                comment, has_ads, has_school_sites, has_google_maps,
                has_our_site, intent_type, recommendation,
                avg_monthly_searches, three_month_change, yearly_change,
                competition, competition_percent, min_top_of_page_bid,
                max_top_of_page_bid, is_new, batch_color
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
                'max_top_of_page_bid': float(row['max_top_of_page_bid']) if row['max_top_of_page_bid'] else None,
                'is_new': bool(row.get('is_new', False)),
                'batch_color': row.get('batch_color')  # ДОБАВЛЕНО: цвет партии
            }
            keywords_data.append(keyword_dict)
            print(f"  - {keyword_dict['id']}: {keyword_dict['keyword']} (новое: {keyword_dict['is_new']}, цвет: {keyword_dict['batch_color']})")
        
        # Статистика включает новые изменения
        total_count = len(keywords_data)
        commercial_count = sum(1 for k in keywords_data if k.get('intent_type') == 'Коммерческий')
        keyword_texts = [k['keyword'].lower() for k in keywords_data]
        duplicates_count = len(keyword_texts) - len(set(keyword_texts))
        new_changes_count = sum(1 for k in keywords_data if k.get('is_new', False))
        
        cursor.close()
        
        result = {
            'success': True,
            'data': keywords_data,
            'stats': {
                'total': total_count,
                'commercial': commercial_count,
                'duplicates': duplicates_count,
                'newChanges': new_changes_count
            }
        }
        
        print(f"Returning {len(keywords_data)} keywords successfully (новых: {new_changes_count})")
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
                'duplicates': 0,
                'newChanges': 0
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
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        if action == 'delete':
            if not keyword_ids:
                return jsonify({'success': False, 'error': 'No keywords selected'}), 400
            placeholders = ','.join(['%s'] * len(keyword_ids))
            cursor.execute(f"UPDATE keywords SET status = 'Removed' WHERE id IN ({placeholders})", keyword_ids)
            connection.commit()
        
        elif action == 'pause':
            if not keyword_ids:
                return jsonify({'success': False, 'error': 'No keywords selected'}), 400
            placeholders = ','.join(['%s'] * len(keyword_ids))
            cursor.execute(f"UPDATE keywords SET status = 'Paused' WHERE id IN ({placeholders})", keyword_ids)
            connection.commit()
        
        elif action == 'activate':
            if not keyword_ids:
                return jsonify({'success': False, 'error': 'No keywords selected'}), 400
            placeholders = ','.join(['%s'] * len(keyword_ids))
            cursor.execute(f"UPDATE keywords SET status = 'Enabled' WHERE id IN ({placeholders})", keyword_ids)
            connection.commit()
        
        elif action == 'update_field':
            if not keyword_ids:
                return jsonify({'success': False, 'error': 'No keywords selected'}), 400
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
            if not keyword_ids:
                return jsonify({'success': False, 'error': 'No keywords selected'}), 400
            placeholders = ','.join(['%s'] * len(keyword_ids))
            cursor.execute(f"SELECT keyword FROM keywords WHERE id IN ({placeholders})", keyword_ids)
            copied_keywords = [row['keyword'] for row in cursor.fetchall()]
            cursor.close()
            return jsonify({
                'success': True,
                'copied': copied_keywords
            })
        
        elif action == 'copy_data':
            if not keyword_ids:
                return jsonify({'success': False, 'error': 'No keywords selected'}), 400
            placeholders = ','.join(['%s'] * len(keyword_ids))
            cursor.execute(f"""
                SELECT keyword, criterion_type, max_cpc, max_cpm, status, comment,
                       has_ads, has_school_sites, has_google_maps, has_our_site,
                       intent_type, recommendation, avg_monthly_searches,
                       three_month_change, yearly_change, competition, competition_percent,
                       min_top_of_page_bid, max_top_of_page_bid, ad_impression_share,
                       organic_average_position, organic_impression_share, labels
                FROM keywords 
                WHERE id IN ({placeholders})
            """, keyword_ids)
            
            copied_data = []
            for row in cursor.fetchall():
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
                    'max_top_of_page_bid': float(row['max_top_of_page_bid']) if row['max_top_of_page_bid'] else None,
                    'ad_impression_share': float(row['ad_impression_share']) if row['ad_impression_share'] else None,
                    'organic_average_position': float(row['organic_average_position']) if row['organic_average_position'] else None,
                    'organic_impression_share': float(row['organic_impression_share']) if row['organic_impression_share'] else None,
                    'labels': row['labels']
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
                pass

@keywords_bp.route('/paste', methods=['POST'])
def paste_keywords():
    """Вставка скопированных данных"""
    connection = None
    try:
        data = request.json
        ad_group_id = data.get('ad_group_id')
        paste_data = data.get('paste_data', [])
        paste_type = data.get('paste_type', 'keywords')
        
        print(f"Paste request: ad_group_id={ad_group_id}, paste_type={paste_type}, data_count={len(paste_data)}")
        
        if not ad_group_id:
            return jsonify({'success': False, 'error': 'No ad_group_id provided'}), 400
        
        if not paste_data:
            return jsonify({'success': False, 'error': 'No paste_data provided'}), 400
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Получаем campaign_id
        cursor.execute("SELECT campaign_id FROM ad_groups WHERE id = %s", (ad_group_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'success': False, 'error': 'Ad group not found'}), 404
        
        campaign_id = result['campaign_id']
        
        # ДОБАВЛЕНО: генерируем один цвет для всей партии
        batch_color = get_random_batch_color()
        
        added_count = 0
        skipped_count = 0
        
        if paste_type == 'keywords':
            # Простое копирование ключевых слов
            for keyword_text in paste_data:
                keyword_text = keyword_text.strip()
                if not keyword_text:
                    continue
                    
                cursor.execute(
                    "SELECT id FROM keywords WHERE ad_group_id = %s AND keyword = %s",
                    (ad_group_id, keyword_text)
                )
                if not cursor.fetchone():
                    # ОБНОВЛЕНО: добавлено поле batch_color
                    cursor.execute("""
                        INSERT INTO keywords (
                            campaign_id, ad_group_id, keyword, criterion_type, 
                            status, max_cpc, is_new, batch_color
                        ) VALUES (%s, %s, %s, 'Phrase', 'Enabled', 3.61, TRUE, %s)
                    """, (campaign_id, ad_group_id, keyword_text, batch_color))
                    added_count += 1
                    print(f"Added keyword: {keyword_text}")
                else:
                    skipped_count += 1
                    print(f"Skipped duplicate: {keyword_text}")
                    
        elif paste_type == 'full_data':
            # Вставка полных данных
            for data_string in paste_data:
                try:
                    data_string = data_string.strip()
                    if not data_string:
                        continue
                    
                    print(f"Processing data string: {data_string[:100]}...")
                    
                    # Парсим строку
                    criterion_types = ['Phrase', 'Broad', 'Exact']
                    keyword_end_pos = -1
                    criterion_type = None
                    
                    for ct in criterion_types:
                        pos = data_string.find(f' {ct} ')
                        if pos > 0:
                            keyword_end_pos = pos
                            criterion_type = ct
                            break
                    
                    if keyword_end_pos == -1:
                        print(f"Could not parse data string - no criterion type found: {data_string}")
                        continue
                    
                    keyword_text = data_string[:keyword_end_pos].strip()
                    remaining_data = data_string[keyword_end_pos + len(criterion_type) + 2:].strip()
                    
                    fields = remaining_data.split(' ')
                    
                    if not keyword_text:
                        print(f"Empty keyword, skipping")
                        continue
                    
                    # Проверяем что такого ключевого слова нет
                    cursor.execute(
                        "SELECT id FROM keywords WHERE ad_group_id = %s AND keyword = %s",
                        (ad_group_id, keyword_text)
                    )
                    if cursor.fetchone():
                        print(f"Keyword already exists: {keyword_text}")
                        skipped_count += 1
                        continue
                    
                    def convert_value(val):
                        if val == 'None' or val == '':
                            return None
                        if val == 'true':
                            return True
                        if val == 'false':
                            return False
                        try:
                            if '.' in val:
                                return float(val)
                            else:
                                return int(val)
                        except ValueError:
                            return val
                    
                    all_fields = [keyword_text, criterion_type] + fields
                    
                    while len(all_fields) < 23:
                        all_fields.append('None')
                    
                    # ОБНОВЛЕНО: добавлено поле batch_color
                    cursor.execute("""
                        INSERT INTO keywords (
                            campaign_id, ad_group_id, keyword, criterion_type, max_cpc, max_cpm,
                            status, comment, has_ads, has_school_sites, has_google_maps, has_our_site,
                            intent_type, recommendation, avg_monthly_searches, three_month_change, 
                            yearly_change, competition, competition_percent, min_top_of_page_bid, 
                            max_top_of_page_bid, ad_impression_share, organic_average_position, 
                            organic_impression_share, labels, is_new, batch_color
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        campaign_id,
                        ad_group_id,
                        keyword_text,
                        criterion_type,
                        convert_value(all_fields[2]),   # max_cpc
                        convert_value(all_fields[3]),   # max_cpm
                        convert_value(all_fields[4]),   # status
                        convert_value(all_fields[5]),   # comment
                        convert_value(all_fields[6]),   # has_ads
                        convert_value(all_fields[7]),   # has_school_sites
                        convert_value(all_fields[8]),   # has_google_maps
                        convert_value(all_fields[9]),   # has_our_site
                        convert_value(all_fields[10]),  # intent_type
                        convert_value(all_fields[11]),  # recommendation
                        convert_value(all_fields[12]),  # avg_monthly_searches
                        convert_value(all_fields[13]),  # three_month_change
                        convert_value(all_fields[14]),  # yearly_change
                        convert_value(all_fields[15]),  # competition
                        convert_value(all_fields[16]),  # competition_percent
                        convert_value(all_fields[17]),  # min_top_of_page_bid
                        convert_value(all_fields[18]),  # max_top_of_page_bid
                        convert_value(all_fields[19]),  # ad_impression_share
                        convert_value(all_fields[20]),  # organic_average_position
                        convert_value(all_fields[21]),  # organic_impression_share
                        convert_value(all_fields[22]) if len(all_fields) > 22 else None,  # labels
                        True,  # is_new = TRUE
                        batch_color  # ДОБАВЛЕНО: цвет партии
                    ))
                    added_count += 1
                    print(f"Added full data for keyword: {keyword_text}")
                    
                except Exception as e:
                    print(f"Error parsing data: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
        
        connection.commit()
        cursor.close()
        
        print(f"Paste completed: added {added_count} keywords, skipped {skipped_count} duplicates")
        
        return jsonify({
            'success': True,
            'message': f'Добавлено {added_count} ключевых слов{f", пропущено дублей: {skipped_count}" if skipped_count > 0 else ""}'
        })
        
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error in paste_keywords: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection:
            connection.close()

@keywords_bp.route('/add', methods=['POST'])
def add_keywords():
    """Добавление новых ключевых слов"""
    connection = None
    try:
        data = request.json
        ad_group_id = data.get('ad_group_id')
        keywords_text = data.get('keywords', '')
        
        if not ad_group_id:
            return jsonify({'success': False, 'error': 'No ad_group_id provided'}), 400
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Получаем campaign_id
        cursor.execute("SELECT campaign_id FROM ad_groups WHERE id = %s", (ad_group_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'success': False, 'error': 'Ad group not found'}), 404
        
        campaign_id = result['campaign_id']
        
        # Разбираем ключевые слова
        keywords = [k.strip() for k in keywords_text.replace('\n', ',').split(',') if k.strip()]
        
        # ДОБАВЛЕНО: генерируем один цвет для всей партии
        batch_color = get_random_batch_color()
        
        added_count = 0
        skipped_count = 0
        
        for keyword in keywords:
            # Проверяем существование
            cursor.execute(
                "SELECT id FROM keywords WHERE ad_group_id = %s AND keyword = %s",
                (ad_group_id, keyword)
            )
            
            if not cursor.fetchone():
                # ОБНОВЛЕНО: добавлено поле batch_color
                cursor.execute("""
                    INSERT INTO keywords (
                        campaign_id, ad_group_id, keyword, criterion_type, 
                        status, max_cpc, is_new, batch_color
                    ) VALUES (%s, %s, %s, 'Phrase', 'Enabled', 3.61, TRUE, %s)
                """, (campaign_id, ad_group_id, keyword, batch_color))
                added_count += 1
            else:
                skipped_count += 1
        
        connection.commit()
        cursor.close()
        
        message = f'Добавлено {added_count} ключевых слов'
        if skipped_count > 0:
            message += f', пропущено дублей: {skipped_count}'
        
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error in add_keywords: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection:
            connection.close()