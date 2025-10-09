# backend/api/competitors.py
from flask import Blueprint, request, jsonify
import pymysql
from config import Config
from datetime import datetime

competitors_bp = Blueprint('competitors', __name__)

def get_db_connection():
    """Создание подключения к БД"""
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

@competitors_bp.route('/list', methods=['GET'])
def get_competitors():
    """Получение списка всех конкурентов с расчётом конкурентности"""
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Получаем список конкурентов с расчётом конкурентности
        # Конкурентность = количество уникальных ключевых слов, в последнем SERP которых встречается домен
        cursor.execute("""
            SELECT 
                c.id,
                c.domain,
                c.org_type,
                c.notes,
                c.last_seen_at,
                c.created_at,
                c.updated_at,
                COUNT(DISTINCT sca.serp_analysis_id) as appearances_count,
                (
                    SELECT COUNT(DISTINCT sa.keyword_id)
                    FROM serp_competitor_appearances sca2
                    JOIN serp_analysis_history sa ON sca2.serp_analysis_id = sa.id
                    WHERE sca2.competitor_id = c.id
                    AND sa.id IN (
                        SELECT MAX(id) 
                        FROM serp_analysis_history 
                        GROUP BY keyword_id
                    )
                ) as competitiveness
            FROM competitor_schools c
            LEFT JOIN serp_competitor_appearances sca ON c.id = sca.competitor_id
            GROUP BY c.id, c.domain, c.org_type, c.notes, c.last_seen_at, c.created_at, c.updated_at
            ORDER BY competitiveness DESC, c.domain ASC
        """)
        
        competitors = cursor.fetchall()
        
        # Преобразуем datetime в строки
        for comp in competitors:
            if comp.get('last_seen_at'):
                comp['last_seen_at'] = comp['last_seen_at'].isoformat()
            if comp.get('created_at'):
                comp['created_at'] = comp['created_at'].isoformat()
            if comp.get('updated_at'):
                comp['updated_at'] = comp['updated_at'].isoformat()
        
        cursor.close()
        
        return jsonify({
            'success': True,
            'competitors': competitors
        })
        
    except Exception as e:
        print(f"❌ Error getting competitors: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
        
    finally:
        if connection:
            connection.close()

@competitors_bp.route('/add', methods=['POST'])
def add_competitor():
    """Добавление нового конкурента"""
    connection = None
    try:
        data = request.json
        domain = data.get('domain', '').strip().lower()
        org_type = data.get('org_type', 'Школа')
        notes = data.get('notes', '')
        
        if not domain:
            return jsonify({'success': False, 'error': 'Домен не указан'}), 400
        
        # Убираем протокол и www
        domain = domain.replace('http://', '').replace('https://', '').replace('www.', '')
        # Убираем путь, оставляя только домен
        if '/' in domain:
            domain = domain.split('/')[0]
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Проверяем существование
        cursor.execute("SELECT id FROM competitor_schools WHERE domain = %s", (domain,))
        existing = cursor.fetchone()
        
        if existing:
            return jsonify({'success': False, 'error': 'Такой домен уже существует'}), 400
        
        # Добавляем
        cursor.execute("""
            INSERT INTO competitor_schools (domain, org_type, notes, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (domain, org_type, notes))
        
        connection.commit()
        new_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Конкурент добавлен',
            'id': new_id
        })
        
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"❌ Error adding competitor: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
        
    finally:
        if connection:
            connection.close()

@competitors_bp.route('/update', methods=['POST'])
def update_competitor():
    """Обновление данных конкурента"""
    connection = None
    try:
        data = request.json
        competitor_id = data.get('id')
        field = data.get('field')
        value = data.get('value')
        
        if not competitor_id or not field:
            return jsonify({'success': False, 'error': 'Недостаточно данных'}), 400
        
        # Разрешённые поля для обновления
        allowed_fields = ['org_type', 'notes', 'domain']
        if field not in allowed_fields:
            return jsonify({'success': False, 'error': 'Недопустимое поле'}), 400
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Если обновляем домен, проверяем уникальность
        if field == 'domain':
            value = value.strip().lower().replace('http://', '').replace('https://', '').replace('www.', '')
            if '/' in value:
                value = value.split('/')[0]
            
            cursor.execute(
                "SELECT id FROM competitor_schools WHERE domain = %s AND id != %s",
                (value, competitor_id)
            )
            if cursor.fetchone():
                return jsonify({'success': False, 'error': 'Такой домен уже существует'}), 400
        
        # Обновляем
        query = f"UPDATE competitor_schools SET {field} = %s, updated_at = NOW() WHERE id = %s"
        cursor.execute(query, (value, competitor_id))
        connection.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Данные обновлены'
        })
        
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"❌ Error updating competitor: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
        
    finally:
        if connection:
            connection.close()

@competitors_bp.route('/delete', methods=['POST'])
def delete_competitors():
    """Удаление конкурентов"""
    connection = None
    try:
        data = request.json
        ids = data.get('ids', [])
        
        if not ids:
            return jsonify({'success': False, 'error': 'Не указаны ID для удаления'}), 400
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Удаляем
        placeholders = ','.join(['%s'] * len(ids))
        query = f"DELETE FROM competitor_schools WHERE id IN ({placeholders})"
        cursor.execute(query, ids)
        
        connection.commit()
        deleted_count = cursor.rowcount
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': f'Удалено записей: {deleted_count}'
        })
        
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"❌ Error deleting competitors: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
        
    finally:
        if connection:
            connection.close()

@competitors_bp.route('/stats', methods=['GET'])
def get_competitor_stats():
    """Получение статистики по конкурентам"""
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN org_type = 'Школа' THEN 1 ELSE 0 END) as schools,
                SUM(CASE WHEN org_type = 'База репетиторов' THEN 1 ELSE 0 END) as tutor_bases,
                SUM(CASE WHEN org_type = 'Не школа' THEN 1 ELSE 0 END) as not_schools,
                SUM(CASE WHEN org_type = 'Партнёр' THEN 1 ELSE 0 END) as partners
            FROM competitor_schools
        """)
        
        stats = cursor.fetchone()
        cursor.close()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        print(f"❌ Error getting stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
        
    finally:
        if connection:
            connection.close()

@competitors_bp.route('/update-competitiveness', methods=['POST'])
def update_competitiveness():
    """
    Пересчёт конкурентности для всех конкурентов
    Вызывается после выполнения SERP-анализа
    """
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Пересчитываем конкурентность для всех доменов
        cursor.execute("""
            UPDATE competitor_schools c
            SET competitiveness = (
                SELECT COUNT(DISTINCT sa.keyword_id)
                FROM serp_competitor_appearances sca
                JOIN serp_analysis_history sa ON sca.serp_analysis_id = sa.id
                WHERE sca.competitor_id = c.id
                AND sa.id IN (
                    SELECT MAX(id) 
                    FROM serp_analysis_history 
                    GROUP BY keyword_id
                )
            ),
            last_seen_at = (
                SELECT MAX(sa.analysis_date)
                FROM serp_competitor_appearances sca
                JOIN serp_analysis_history sa ON sca.serp_analysis_id = sa.id
                WHERE sca.competitor_id = c.id
            ),
            updated_at = NOW()
        """)
        
        connection.commit()
        updated_count = cursor.rowcount
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': f'Обновлено записей: {updated_count}'
        })
        
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"❌ Error updating competitiveness: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
        
    finally:
        if connection:
            connection.close()