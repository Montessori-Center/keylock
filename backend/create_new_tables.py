#!/usr/bin/env python3
# backend/migrations/add_position_fields.py
"""
Миграция: Добавление полей для отслеживания позиций сайта в SERP
- our_organic_position: органическая позиция (среди органики)
- our_actual_position: фактическая позиция (с учётом рекламы/карт)
- last_serp_check: дата последней проверки SERP
"""

import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
import pymysql

def run_migration():
    """Выполнение миграции"""
    
    print("=" * 60)
    print("🔄 МИГРАЦИЯ: Добавление полей позиций в таблицу keywords")
    print("=" * 60)
    
    connection = None
    try:
        # Подключаемся к БД
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
        
        # Проверяем, существуют ли уже эти поля
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'keywords'
            AND COLUMN_NAME IN ('our_organic_position', 'our_actual_position', 'last_serp_check')
        """, (Config.DB_NAME,))
        
        existing_columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
        
        if len(existing_columns) == 3:
            print("\n⚠️  Все поля уже существуют. Миграция не требуется.")
            cursor.close()
            return True
        
        print(f"\n📋 Существующие поля: {existing_columns if existing_columns else 'отсутствуют'}")
        print(f"📋 Нужно добавить: {3 - len(existing_columns)} полей")
        
        # Добавляем поля, которых нет
        migrations_applied = []
        
        if 'our_organic_position' not in existing_columns:
            print("\n➕ Добавление поля 'our_organic_position'...")
            cursor.execute("""
                ALTER TABLE keywords 
                ADD COLUMN our_organic_position INT DEFAULT NULL 
                COMMENT 'Органическая позиция нашего сайта (среди органики)'
            """)
            migrations_applied.append('our_organic_position')
            print("   ✅ Поле 'our_organic_position' добавлено")
        
        if 'our_actual_position' not in existing_columns:
            print("\n➕ Добавление поля 'our_actual_position'...")
            cursor.execute("""
                ALTER TABLE keywords 
                ADD COLUMN our_actual_position INT DEFAULT NULL 
                COMMENT 'Фактическая позиция нашего сайта (с учётом рекламы/карт)'
            """)
            migrations_applied.append('our_actual_position')
            print("   ✅ Поле 'our_actual_position' добавлено")
        
        if 'last_serp_check' not in existing_columns:
            print("\n➕ Добавление поля 'last_serp_check'...")
            cursor.execute("""
                ALTER TABLE keywords 
                ADD COLUMN last_serp_check TIMESTAMP NULL DEFAULT NULL 
                COMMENT 'Последняя проверка SERP'
            """)
            migrations_applied.append('last_serp_check')
            print("   ✅ Поле 'last_serp_check' добавлено")
        
        # Создаём индекс для быстрого поиска по last_serp_check
        print("\n➕ Создание индекса для 'last_serp_check'...")
        try:
            cursor.execute("""
                CREATE INDEX idx_last_serp_check ON keywords(last_serp_check)
            """)
            print("   ✅ Индекс 'idx_last_serp_check' создан")
        except pymysql.err.OperationalError as e:
            if "Duplicate key name" in str(e):
                print("   ℹ️  Индекс уже существует, пропускаем")
            else:
                raise
        
        connection.commit()
        cursor.close()
        
        print("\n" + "=" * 60)
        print("✅ МИГРАЦИЯ УСПЕШНО ЗАВЕРШЕНА")
        print("=" * 60)
        print(f"\n📊 Добавлено полей: {len(migrations_applied)}")
        if migrations_applied:
            for field in migrations_applied:
                print(f"   - {field}")
        
        # Проверяем структуру таблицы
        print("\n📋 Проверка структуры таблицы keywords:")
        cursor = connection.cursor()
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'keywords'
            AND COLUMN_NAME IN ('our_organic_position', 'our_actual_position', 'last_serp_check')
            ORDER BY ORDINAL_POSITION
        """, (Config.DB_NAME,))
        
        columns = cursor.fetchall()
        for col in columns:
            print(f"   ✓ {col['COLUMN_NAME']}: {col['COLUMN_TYPE']} "
                  f"{'NULL' if col['IS_NULLABLE'] == 'YES' else 'NOT NULL'} "
                  f"({col['COLUMN_COMMENT']})")
        
        cursor.close()
        
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА МИГРАЦИИ: {str(e)}")
        if connection:
            connection.rollback()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if connection:
            connection.close()
            print("\n🔌 Соединение с БД закрыто")

def rollback_migration():
    """Откат миграции (удаление добавленных полей)"""
    
    print("=" * 60)
    print("⏮️  ОТКАТ МИГРАЦИИ: Удаление полей позиций")
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
        
        # Удаляем индекс
        print("\n➖ Удаление индекса 'idx_last_serp_check'...")
        try:
            cursor.execute("DROP INDEX idx_last_serp_check ON keywords")
            print("   ✅ Индекс удалён")
        except pymysql.err.OperationalError as e:
            if "check that column/key exists" in str(e):
                print("   ℹ️  Индекс не существует, пропускаем")
            else:
                raise
        
        # Удаляем поля
        fields_to_remove = ['our_organic_position', 'our_actual_position', 'last_serp_check']
        
        for field in fields_to_remove:
            print(f"\n➖ Удаление поля '{field}'...")
            try:
                cursor.execute(f"ALTER TABLE keywords DROP COLUMN {field}")
                print(f"   ✅ Поле '{field}' удалено")
            except pymysql.err.OperationalError as e:
                if "check that column/key exists" in str(e):
                    print(f"   ℹ️  Поле '{field}' не существует, пропускаем")
                else:
                    raise
        
        connection.commit()
        cursor.close()
        
        print("\n" + "=" * 60)
        print("✅ ОТКАТ МИГРАЦИИ ЗАВЕРШЁН")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА ОТКАТА: {str(e)}")
        if connection:
            connection.rollback()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if connection:
            connection.close()
            print("\n🔌 Соединение с БД закрыто")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Миграция для добавления полей позиций в SERP')
    parser.add_argument('--rollback', action='store_true', help='Откатить миграцию')
    
    args = parser.parse_args()
    
    try:
        if args.rollback:
            success = rollback_migration()
        else:
            success = run_migration()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Миграция прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {str(e)}")
        sys.exit(1)