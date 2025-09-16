"""
Миграция для добавления поля is_new в таблицу keywords
Запуск: python3 add_is_new_field.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pymysql
from config import Config

def add_is_new_field():
    """Добавляет поле is_new в таблицу keywords"""
    try:
        print("🔧 Подключение к базе данных...")
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = connection.cursor()
        print(f"✅ Подключен к {Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}")
        
        # Проверяем, есть ли уже поле is_new
        print("🔍 Проверяем наличие поля is_new...")
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
            
            # Проверяем что поле добавилось
            cursor.execute("SHOW COLUMNS FROM keywords LIKE 'is_new'")
            result = cursor.fetchone()
            if result:
                print(f"✅ Подтверждение: поле is_new создано - {result}")
            else:
                print("❌ Ошибка: поле is_new не найдено после создания")
        else:
            print("ℹ️ Поле is_new уже существует")
            print(f"   Детали поля: {result}")
        
        # Показываем статистику
        cursor.execute("SELECT COUNT(*) as total FROM keywords")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as new_count FROM keywords WHERE is_new = TRUE")
        new_count = cursor.fetchone()[0]
        
        print(f"\n📊 Статистика keywords:")
        print(f"   Всего ключевых слов: {total}")
        print(f"   Новых (is_new=TRUE): {new_count}")
        
        cursor.close()
        connection.close()
        print("\n✅ Миграция завершена успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка добавления поля: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def check_database_structure():
    """Проверка структуры базы данных"""
    try:
        print("\n🔍 Проверка структуры базы данных...")
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = connection.cursor()
        
        # Показываем все поля таблицы keywords
        cursor.execute("DESCRIBE keywords")
        fields = cursor.fetchall()
        
        print("\n📋 Поля таблицы keywords:")
        for field in fields:
            field_name = field[0]
            field_type = field[1]
            is_null = field[2]
            default_val = field[4]
            print(f"   {field_name}: {field_type} {'NULL' if is_null == 'YES' else 'NOT NULL'} {f'DEFAULT {default_val}' if default_val else ''}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Ошибка проверки структуры: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Миграция: Добавление поля is_new в таблицу keywords")
    print("=" * 60)
    
    success = add_is_new_field()
    
    if success:
        check_database_structure()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Миграция выполнена успешно!")
        print("Теперь можно запускать приложение: python3 app.py")
    else:
        print("❌ Миграция не выполнена")
        print("Проверьте настройки подключения к БД")
    print("=" * 60)