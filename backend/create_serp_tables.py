#!/usr/bin/env python3
# backend/update_db_serp_fields.py
"""
Добавление полей SERP отслеживания в таблицу keywords
Запуск: python3 update_db_serp_fields.py
"""

import sys
import pymysql
from config import Config
from datetime import datetime

def update_database():
    """Обновить структуру БД для SERP полей"""
    connection = None
    
    try:
        print(f"\n{'='*60}")
        print(f"🚀 Обновление БД: добавление SERP полей")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # Подключение к БД
        print(f"📊 Подключение к {Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}...")
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = connection.cursor()
        print("✅ Подключено\n")
        
        # Проверяем существующие колонки
        cursor.execute("SHOW COLUMNS FROM keywords")
        existing_columns = {row['Field'] for row in cursor.fetchall()}
        
        changes_made = []
        
        # 1. Добавляем last_serp_check
        if 'last_serp_check' not in existing_columns:
            print("➕ Добавление колонки last_serp_check...")
            cursor.execute("""
                ALTER TABLE keywords 
                ADD COLUMN last_serp_check DATETIME DEFAULT NULL 
                COMMENT 'Дата последней SERP проверки'
            """)
            changes_made.append('last_serp_check')
            print("   ✅ Добавлена\n")
        else:
            print("   ℹ️  last_serp_check уже существует")
        
        # 2. Добавляем serp_position
        if 'serp_position' not in existing_columns:
            print("➕ Добавление колонки serp_position...")
            cursor.execute("""
                ALTER TABLE keywords 
                ADD COLUMN serp_position INT DEFAULT NULL 
                COMMENT 'Позиция в SERP (rank_absolute)'
            """)
            changes_made.append('serp_position')
            print("   ✅ Добавлена\n")
        else:
            print("   ℹ️  serp_position уже существует")
        
        # 3. Проверяем и добавляем индексы
        cursor.execute("SHOW INDEX FROM keywords")
        existing_indexes = {row['Key_name'] for row in cursor.fetchall()}
        
        if 'idx_last_serp_check' not in existing_indexes:
            print("➕ Создание индекса idx_last_serp_check...")
            cursor.execute("ALTER TABLE keywords ADD INDEX idx_last_serp_check (last_serp_check)")
            changes_made.append('idx_last_serp_check')
            print("   ✅ Создан\n")
        else:
            print("   ℹ️  idx_last_serp_check уже существует")
        
        if 'idx_serp_position' not in existing_indexes:
            print("➕ Создание индекса idx_serp_position...")
            cursor.execute("ALTER TABLE keywords ADD INDEX idx_serp_position (serp_position)")
            changes_made.append('idx_serp_position')
            print("   ✅ Создан\n")
        else:
            print("   ℹ️  idx_serp_position уже существует")
        
        # Применяем изменения
        connection.commit()
        
        # Статистика
        print(f"\n{'='*60}")
        if changes_made:
            print(f"✅ Выполнено изменений: {len(changes_made)}")
            for item in changes_made:
                print(f"   • {item}")
        else:
            print("✅ Все изменения уже были применены ранее")
        
        # Проверка результата
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN last_serp_check IS NOT NULL THEN 1 ELSE 0 END) as checked,
                SUM(CASE WHEN serp_position IS NOT NULL THEN 1 ELSE 0 END) as with_position
            FROM keywords
        """)
        stats = cursor.fetchone()
        
        print(f"\n📈 Статистика keywords:")
        print(f"   Всего записей: {stats['total']}")
        print(f"   С SERP проверкой: {stats['checked']}")
        print(f"   С позицией: {stats['with_position']}")
        
        cursor.close()
        print(f"\n{'='*60}")
        print("✨ База данных успешно обновлена!")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {str(e)}")
        if connection:
            connection.rollback()
        return False
        
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    success = update_database()
    sys.exit(0 if success else 1)