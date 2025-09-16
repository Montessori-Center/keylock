import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pymysql
from config import Config

def add_is_new_field():
    """Добавляет поле is_new в таблицу keywords"""
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = connection.cursor()
        
        # Проверяем, есть ли уже поле
        cursor.execute("SHOW COLUMNS FROM keywords LIKE 'is_new'")
        result = cursor.fetchone()
        
        if not result:
            print("📝 Добавляем поле is_new в таблицу keywords...")
            cursor.execute("""
                ALTER TABLE keywords 
                ADD COLUMN is_new BOOLEAN DEFAULT FALSE 
                AFTER labels
            """)
            connection.commit()
            print("✅ Поле is_new добавлено успешно")
        else:
            print("ℹ️ Поле is_new уже существует")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Ошибка добавления поля: {e}")

if __name__ == "__main__":
    add_is_new_field()