# migrations/add_serp_params.py
"""
Добавление полей параметров SERP в таблицу serp_logs
"""
import pymysql
from config import Config

def upgrade():
    """Добавление столбцов os, browser_screen_width, browser_screen_height"""
    connection = pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )
    
    cursor = connection.cursor()
    
    try:
        # Проверяем, есть ли столбец os
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'serp_logs' 
            AND COLUMN_NAME = 'os'
        """, (Config.DB_NAME,))
        
        if cursor.fetchone()[0] == 0:
            print("➕ Добавляем столбец 'os'")
            cursor.execute("""
                ALTER TABLE serp_logs 
                ADD COLUMN os VARCHAR(50) DEFAULT 'windows' AFTER device
            """)
        
        # Проверяем browser_screen_width
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'serp_logs' 
            AND COLUMN_NAME = 'browser_screen_width'
        """, (Config.DB_NAME,))
        
        if cursor.fetchone()[0] == 0:
            print("➕ Добавляем столбец 'browser_screen_width'")
            cursor.execute("""
                ALTER TABLE serp_logs 
                ADD COLUMN browser_screen_width INT DEFAULT 1920 AFTER analysis_result
            """)
        
        # Проверяем browser_screen_height
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'serp_logs' 
            AND COLUMN_NAME = 'browser_screen_height'
        """, (Config.DB_NAME,))
        
        if cursor.fetchone()[0] == 0:
            print("➕ Добавляем столбец 'browser_screen_height'")
            cursor.execute("""
                ALTER TABLE serp_logs 
                ADD COLUMN browser_screen_height INT DEFAULT 1080 AFTER browser_screen_width
            """)
        
        connection.commit()
        print("✅ Миграция выполнена успешно!")
        
    except Exception as e:
        connection.rollback()
        print(f"❌ Ошибка миграции: {e}")
        raise
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    upgrade()