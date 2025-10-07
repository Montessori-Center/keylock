#!/usr/bin/env python3
# backend/migrations/check_serp_logs.py
"""
Проверка и исправление структуры таблицы serp_logs
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
import pymysql

def check_and_fix_serp_logs():
    """Проверка и исправление структуры таблицы serp_logs"""
    
    print("=" * 60)
    print("🔍 ПРОВЕРКА СТРУКТУРЫ ТАБЛИЦЫ serp_logs")
    print("=" * 60)
    
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
        
        print(f"\n✅ Подключение к БД: {Config.DB_NAME}")
        
        # Проверяем существование таблицы
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'serp_logs'
        """, (Config.DB_NAME,))
        
        table_exists = cursor.fetchone()['count'] > 0
        
        if not table_exists:
            print("\n❌ Таблица serp_logs НЕ СУЩЕСТВУЕТ!")
            print("Создаём таблицу...")
            
            cursor.execute("""
                CREATE TABLE serp_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    keyword_id INT NOT NULL,
                    keyword_text VARCHAR(500),
                    raw_response LONGTEXT,
                    parsed_items LONGTEXT,
                    analysis_result TEXT,
                    cost DECIMAL(10, 4) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_keyword_id (keyword_id),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            connection.commit()
            print("✅ Таблица serp_logs создана")
        else:
            print("\n✅ Таблица serp_logs существует")
        
        # Получаем структуру таблицы
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'serp_logs'
            ORDER BY ORDINAL_POSITION
        """, (Config.DB_NAME,))
        
        columns = cursor.fetchall()
        
        print("\n📋 Текущие колонки:")
        existing_columns = []
        for col in columns:
            existing_columns.append(col['COLUMN_NAME'])
            print(f"   - {col['COLUMN_NAME']}: {col['COLUMN_TYPE']}")
        
        # Проверяем необходимые колонки
        required_columns = {
            'id': 'INT AUTO_INCREMENT PRIMARY KEY',
            'keyword_id': 'INT NOT NULL',
            'keyword_text': 'VARCHAR(500)',
            'raw_response': 'LONGTEXT',
            'parsed_items': 'LONGTEXT',
            'analysis_result': 'TEXT',
            'cost': 'DECIMAL(10, 4) DEFAULT 0',
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
        }
        
        missing_columns = []
        for col_name in required_columns:
            if col_name not in existing_columns:
                missing_columns.append(col_name)
        
        if missing_columns:
            print(f"\n⚠️  Отсутствуют колонки: {', '.join(missing_columns)}")
            print("Добавляем недостающие колонки...")
            
            for col_name in missing_columns:
                if col_name == 'id':
                    continue  # ID не добавляем отдельно
                
                col_type = required_columns[col_name]
                print(f"   ➕ Добавление {col_name}...")
                
                try:
                    cursor.execute(f"ALTER TABLE serp_logs ADD COLUMN {col_name} {col_type}")
                    print(f"      ✅ Колонка {col_name} добавлена")
                except Exception as e:
                    print(f"      ⚠️  Ошибка: {str(e)}")
            
            connection.commit()
            print("\n✅ Структура таблицы обновлена")
        else:
            print("\n✅ Все необходимые колонки присутствуют")
        
        # Проверяем количество записей
        cursor.execute("SELECT COUNT(*) as count FROM serp_logs")
        count = cursor.fetchone()['count']
        print(f"\n📊 Всего записей в serp_logs: {count}")
        
        if count > 0:
            # Показываем последние 3 записи
            cursor.execute("""
                SELECT id, keyword_id, keyword_text, 
                       CHAR_LENGTH(analysis_result) as analysis_len,
                       created_at
                FROM serp_logs 
                ORDER BY created_at DESC 
                LIMIT 3
            """)
            recent = cursor.fetchall()
            
            print("\n📋 Последние записи:")
            for row in recent:
                print(f"   ID: {row['id']}, "
                      f"Keyword: {row['keyword_text']}, "
                      f"Analysis: {row['analysis_len']} bytes, "
                      f"Date: {row['created_at']}")
        
        cursor.close()
        
        print("\n" + "=" * 60)
        print("✅ ПРОВЕРКА ЗАВЕРШЕНА")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    try:
        success = check_and_fix_serp_logs()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Проверка прервана")
        sys.exit(1)