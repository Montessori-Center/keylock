#!/usr/bin/env python3
# fix_serp_logs.py - запустите этот скрипт в папке backend

import pymysql
from config import Config

def fix_serp_logs_table():
    """Пересоздание таблицы serp_logs с правильной структурой"""
    connection = None
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = connection.cursor()
        
        print("🔧 Исправление таблицы serp_logs...")
        
        # Удаляем старую таблицу если существует
        cursor.execute("DROP TABLE IF EXISTS serp_logs")
        print("✅ Старая таблица удалена")
        
        # Создаем новую с правильной структурой (TEXT вместо JSON для MySQL 5.7)
        cursor.execute("""
        CREATE TABLE serp_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            keyword_id INT,
            keyword_text VARCHAR(500),
            location_code INT,
            language_code VARCHAR(10),
            device VARCHAR(50),
            depth INT,
            total_items INT DEFAULT 0,
            organic_count INT DEFAULT 0,
            paid_count INT DEFAULT 0,
            maps_count INT DEFAULT 0,
            shopping_count INT DEFAULT 0,
            has_ads BOOLEAN DEFAULT FALSE,
            has_maps BOOLEAN DEFAULT FALSE,
            has_our_site BOOLEAN DEFAULT FALSE,
            has_school_sites BOOLEAN DEFAULT FALSE,
            intent_type VARCHAR(50),
            school_percentage DECIMAL(5,2),
            cost DECIMAL(10,4),
            raw_response TEXT,
            parsed_items TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE SET NULL,
            INDEX idx_keyword_id (keyword_id),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Новая таблица serp_logs создана с TEXT полями")
        
        # Проверяем структуру
        cursor.execute("DESCRIBE serp_logs")
        columns = cursor.fetchall()
        print("\n📋 Структура таблицы serp_logs:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]}")
        
        connection.commit()
        cursor.close()
        
        print("\n✅ Таблица успешно пересоздана!")
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

def test_insert():
    """Тест вставки данных"""
    connection = None
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = connection.cursor()
        
        print("\n🧪 Тест вставки...")
        
        # Тестовая вставка
        cursor.execute("""
            INSERT INTO serp_logs (
                keyword_text, location_code, language_code,
                device, depth, total_items, organic_count,
                has_ads, has_our_site, intent_type,
                school_percentage, cost, raw_response, parsed_items
            ) VALUES (
                'тест', 2804, 'ru', 'desktop', 10, 10, 10,
                FALSE, TRUE, 'Информационный',
                0.0, 0.003, '{"test": "data"}', '{"organic": []}'
            )
        """)
        
        connection.commit()
        print("✅ Тестовая запись успешно вставлена")
        
        # Проверяем
        cursor.execute("SELECT COUNT(*) as cnt FROM serp_logs")
        result = cursor.fetchone()
        print(f"📊 Записей в таблице: {result[0]}")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Ошибка теста: {str(e)}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    fix_serp_logs_table()
    test_insert()