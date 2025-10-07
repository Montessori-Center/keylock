#!/usr/bin/env python3
# backend/database/migrate_serp_positions.py
"""
Миграция для добавления полей SERP позиций
Запуск: python3 migrate_serp_positions.py
"""

import pymysql
import sys
from config import Config

def log(message):
    """Логирование с flush"""
    print(message)
    sys.stdout.flush()

def run_migration():
    """Выполняет миграцию БД"""
    connection = None
    
    try:
        # Подключаемся к БД
        log("📡 Подключение к БД...")
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        
        cursor = connection.cursor()
        log("✅ Подключено к БД")
        
        # Проверяем, существуют ли уже поля
        log("\n🔍 Проверка существующих полей...")
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'keywords'
            AND COLUMN_NAME IN ('our_organic_position', 'our_actual_position', 'last_serp_check')
        """, (Config.DB_NAME,))
        
        existing_columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
        log(f"   Существующие поля: {existing_columns if existing_columns else 'нет'}")
        
        # Добавляем поля в таблицу keywords
        log("\n📝 Добавление полей в таблицу keywords...")
        
        if 'our_organic_position' not in existing_columns:
            log("   ➕ Добавляем our_organic_position...")
            cursor.execute("""
                ALTER TABLE keywords
                ADD COLUMN our_organic_position INT DEFAULT NULL 
                COMMENT 'Органическая позиция нашего сайта (среди органических результатов)'
            """)
            log("   ✅ our_organic_position добавлен")
        else:
            log("   ⏭️  our_organic_position уже существует")
        
        if 'our_actual_position' not in existing_columns:
            log("   ➕ Добавляем our_actual_position...")
            cursor.execute("""
                ALTER TABLE keywords
                ADD COLUMN our_actual_position INT DEFAULT NULL 
                COMMENT 'Фактическая позиция на странице (с учетом рекламы и карт)'
            """)
            log("   ✅ our_actual_position добавлен")
        else:
            log("   ⏭️  our_actual_position уже существует")
        
        if 'last_serp_check' not in existing_columns:
            log("   ➕ Добавляем last_serp_check...")
            cursor.execute("""
                ALTER TABLE keywords
                ADD COLUMN last_serp_check DATETIME DEFAULT NULL 
                COMMENT 'Дата последней SERP проверки'
            """)
            log("   ✅ last_serp_check добавлен")
        else:
            log("   ⏭️  last_serp_check уже существует")
        
        # Проверяем поле analysis_result в serp_logs
        log("\n🔍 Проверка таблицы serp_logs...")
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'serp_logs'
            AND COLUMN_NAME = 'analysis_result'
        """, (Config.DB_NAME,))
        
        has_analysis_result = cursor.fetchone()
        
        if not has_analysis_result:
            log("   ➕ Добавляем analysis_result в serp_logs...")
            cursor.execute("""
                ALTER TABLE serp_logs
                ADD COLUMN analysis_result JSON DEFAULT NULL 
                COMMENT 'Результаты анализа в JSON формате'
            """)
            log("   ✅ analysis_result добавлен")
        else:
            log("   ⏭️  analysis_result уже существует")
        
        # Создаем индексы для быстрого поиска
        log("\n📇 Создание индексов...")
        
        try:
            cursor.execute("""
                CREATE INDEX idx_our_organic_position ON keywords(our_organic_position)
            """)
            log("   ✅ Индекс idx_our_organic_position создан")
        except pymysql.err.OperationalError as e:
            if "Duplicate key name" in str(e):
                log("   ⏭️  Индекс idx_our_organic_position уже существует")
            else:
                raise
        
        try:
            cursor.execute("""
                CREATE INDEX idx_last_serp_check ON keywords(last_serp_check)
            """)
            log("   ✅ Индекс idx_last_serp_check создан")
        except pymysql.err.OperationalError as e:
            if "Duplicate key name" in str(e):
                log("   ⏭️  Индекс idx_last_serp_check уже существует")
            else:
                raise
        
        try:
            cursor.execute("""
                CREATE INDEX idx_keyword_id ON serp_logs(keyword_id)
            """)
            log("   ✅ Индекс idx_keyword_id создан")
        except pymysql.err.OperationalError as e:
            if "Duplicate key name" in str(e):
                log("   ⏭️  Индекс idx_keyword_id уже существует")
            else:
                raise
        
        # Применяем изменения
        connection.commit()
        
        # Проверяем финальную структуру
        log("\n🔍 Проверка финальной структуры таблицы keywords...")
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'keywords'
            AND COLUMN_NAME IN ('our_organic_position', 'our_actual_position', 'last_serp_check')
            ORDER BY COLUMN_NAME
        """, (Config.DB_NAME,))
        
        columns_info = cursor.fetchall()
        for col in columns_info:
            log(f"   ✅ {col['COLUMN_NAME']}: {col['COLUMN_TYPE']} - {col['COLUMN_COMMENT']}")
        
        cursor.close()
        
        log("\n" + "="*50)
        log("🎉 Миграция успешно завершена!")
        log("="*50)
        
        return True
        
    except Exception as e:
        log(f"\n❌ Ошибка миграции: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if connection:
            connection.close()
            log("\n🔌 Подключение к БД закрыто")


if __name__ == '__main__':
    log("="*50)
    log("🚀 Запуск миграции SERP позиций")
    log("="*50)
    
    success = run_migration()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)