# backend/scripts/cleanup_trash.py
"""
Скрипт для автоматического удаления старых записей из корзины
Запускается через cron каждый день
"""

import sys
import os
from datetime import datetime, timedelta

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
import pymysql

AUTO_DELETE_DAYS = 30

def cleanup_old_trash():
    """Удаляет ключевые слова старше AUTO_DELETE_DAYS дней со статусом 'Removed'"""
    
    connection = None
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        
        cursor = connection.cursor()
        
        # Вычисляем дату отсечки
        cutoff_date = datetime.now() - timedelta(days=AUTO_DELETE_DAYS)
        
        print(f"🗑️  Starting trash cleanup for keywords older than {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Находим записи для удаления
        cursor.execute("""
            SELECT id, keyword, updated_at, ad_group_id
            FROM keywords 
            WHERE status = 'Removed' 
            AND updated_at < %s
        """, (cutoff_date,))
        
        keywords_to_delete = cursor.fetchall()
        
        if not keywords_to_delete:
            print("✅ No keywords to delete")
            return 0
        
        print(f"📋 Found {len(keywords_to_delete)} keywords to delete:")
        for kw in keywords_to_delete[:5]:  # Показываем первые 5
            print(f"   - ID {kw['id']}: {kw['keyword']} (deleted {kw['updated_at']})")
        if len(keywords_to_delete) > 5:
            print(f"   ... и ещё {len(keywords_to_delete) - 5}")
        
        # Удаляем записи
        keyword_ids = [kw['id'] for kw in keywords_to_delete]
        placeholders = ','.join(['%s'] * len(keyword_ids))
        
        cursor.execute(
            f"DELETE FROM keywords WHERE id IN ({placeholders}) AND status = 'Removed'",
            keyword_ids
        )
        
        deleted_count = cursor.rowcount
        connection.commit()
        
        print(f"✅ Deleted {deleted_count} keywords from trash")
        
        cursor.close()
        return deleted_count
        
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        if connection:
            connection.rollback()
        raise
        
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    try:
        deleted = cleanup_old_trash()
        print(f"\n{'='*50}")
        print(f"Cleanup completed: {deleted} keywords deleted")
        print(f"{'='*50}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{'='*50}")
        print(f"Cleanup failed: {str(e)}")
        print(f"{'='*50}")
        sys.exit(1)