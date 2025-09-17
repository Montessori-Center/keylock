# backend/add_batch_color_field.py - скрипт для добавления поля batch_color
import pymysql
from config import Config

def add_batch_color_field():
    """Добавляет поле batch_color в таблицу keywords"""
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = connection.cursor()
        
        # Проверяем есть ли поле batch_color
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'keywords' 
            AND COLUMN_NAME = 'batch_color'
        """, (Config.DB_NAME,))
        
        result = cursor.fetchone()
        
        if not result:
            print("🎨 Поле batch_color не найдено, добавляю...")
            
            cursor.execute("""
                ALTER TABLE keywords 
                ADD COLUMN batch_color VARCHAR(10) DEFAULT NULL
                COMMENT 'Цвет партии для новых записей'
            """)
            connection.commit()
            print("✅ Поле batch_color успешно добавлено")
        else:
            print("✅ Поле batch_color уже существует")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    add_batch_color_field()