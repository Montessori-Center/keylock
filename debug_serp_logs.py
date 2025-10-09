#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Миграция БД: Добавление поля is_new в таблицу competitor_schools
Запускать из корневой директории проекта: python migrate_competitors_is_new.py
"""

import sys
import os
from pathlib import Path

# Добавляем backend в путь для импорта
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

try:
    from config import Config
    import pymysql
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("   Убедитесь, что файл backend/config.py существует")
    sys.exit(1)


def get_db_connection():
    """Создаёт подключение к БД используя Config"""
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )


def check_column_exists(cursor, table_name, column_name):
    """Проверяет существование колонки в таблице"""
    cursor.execute(f"""
        SELECT COUNT(*) as count
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = '{table_name}'
        AND COLUMN_NAME = '{column_name}'
    """)
    result = cursor.fetchone()
    return result['count'] > 0


def check_index_exists(cursor, table_name, index_name):
    """Проверяет существование индекса"""
    cursor.execute(f"""
        SELECT COUNT(*) as count
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = '{table_name}'
        AND INDEX_NAME = '{index_name}'
    """)
    result = cursor.fetchone()
    return result['count'] > 0


def main():
    """Основная функция миграции"""
    
    print("=" * 70)
    print("🔧 МИГРАЦИЯ БД: Добавление поля is_new в таблицу competitor_schools")
    print("=" * 70)
    
    connection = None
    
    try:
        # Выводим информацию о подключении
        print(f"\n📋 Параметры подключения:")
        print(f"   Host: {Config.DB_HOST}")
        print(f"   Port: {Config.DB_PORT}")
        print(f"   Database: {Config.DB_NAME}")
        print(f"   User: {Config.DB_USER}")
        
        # Подключение к БД
        print("\n📡 Подключение к базе данных...")
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Получаем имя текущей БД
        cursor.execute("SELECT DATABASE() as db_name")
        db_info = cursor.fetchone()
        print(f"   ✅ Подключено к БД: {db_info['db_name']}")
        
        # Проверяем версию MySQL
        cursor.execute("SELECT VERSION() as version")
        version_info = cursor.fetchone()
        print(f"   ✅ MySQL версия: {version_info['version']}")
        
        # Проверяем существование таблицы competitor_schools
        print("\n🔍 Проверка таблицы competitor_schools...")
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'competitor_schools'
        """)
        table_exists = cursor.fetchone()['count'] > 0
        
        if not table_exists:
            print("   ❌ ОШИБКА: Таблица competitor_schools не существует!")
            print("   Создайте таблицу сначала через create_new_tables.py")
            return False
        
        print("   ✅ Таблица competitor_schools найдена")
        
        # Проверяем текущие колонки
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'competitor_schools'
            ORDER BY ORDINAL_POSITION
        """)
        current_columns = cursor.fetchall()
        
        print(f"\n📋 Текущие колонки в таблице competitor_schools ({len(current_columns)}):")
        for col in current_columns:
            print(f"   - {col['COLUMN_NAME']} ({col['COLUMN_TYPE']})")
        
        # Проверяем существование поля is_new
        print("\n🔍 Проверка поля is_new...")
        is_new_exists = check_column_exists(cursor, 'competitor_schools', 'is_new')
        
        if is_new_exists:
            print("   ⚠️  Поле is_new уже существует!")
            print("   Миграция уже была выполнена ранее")
            
            # Показываем статистику
            cursor.execute("SELECT COUNT(*) as count FROM competitor_schools WHERE is_new = 1")
            pending_count = cursor.fetchone()['count']
            print(f"\n📊 Статистика:")
            print(f"   Необработанных школ (is_new = 1): {pending_count}")
            
            return True
        
        print("   ✅ Поле is_new отсутствует, начинаем миграцию...")
        
        # ===== МИГРАЦИЯ 1: Добавление поля is_new =====
        print("\n🔨 Шаг 1/4: Добавление поля is_new...")
        cursor.execute("""
            ALTER TABLE competitor_schools 
            ADD COLUMN is_new TINYINT(1) NOT NULL DEFAULT 0 
            COMMENT 'Флаг новой необработанной школы (1 = новая, 0 = обработана)'
            AFTER notes
        """)
        print("   ✅ Поле is_new успешно добавлено")
        
        # ===== МИГРАЦИЯ 2: Установка значений по умолчанию =====
        print("\n🔨 Шаг 2/4: Установка значений по умолчанию...")
        cursor.execute("UPDATE competitor_schools SET is_new = 0 WHERE is_new IS NULL")
        affected = cursor.rowcount
        print(f"   ✅ Обновлено записей: {affected}")
        
        # ===== МИГРАЦИЯ 3: Добавление индекса =====
        print("\n🔨 Шаг 3/4: Добавление индекса для быстрого поиска...")
        
        index_exists = check_index_exists(cursor, 'competitor_schools', 'idx_is_new')
        
        if not index_exists:
            cursor.execute("CREATE INDEX idx_is_new ON competitor_schools(is_new)")
            print("   ✅ Индекс idx_is_new создан")
        else:
            print("   ℹ️  Индекс idx_is_new уже существует")
        
        # ===== МИГРАЦИЯ 4: Добавление составного индекса =====
        print("\n🔨 Шаг 4/4: Добавление составного индекса для фильтрации...")
        
        composite_index_exists = check_index_exists(cursor, 'competitor_schools', 'idx_is_new_org_type')
        
        if not composite_index_exists:
            cursor.execute("CREATE INDEX idx_is_new_org_type ON competitor_schools(is_new, org_type)")
            print("   ✅ Индекс idx_is_new_org_type создан")
        else:
            print("   ℹ️  Индекс idx_is_new_org_type уже существует")
        
        # Коммитим изменения
        connection.commit()
        print("\n💾 Изменения успешно сохранены в БД")
        
        # Проверка результата
        print("\n🔍 Проверка результата миграции...")
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'competitor_schools'
            AND COLUMN_NAME = 'is_new'
        """)
        new_column = cursor.fetchone()
        
        if new_column:
            print("   ✅ Поле is_new успешно создано:")
            print(f"      Тип: {new_column['COLUMN_TYPE']}")
            print(f"      NULL: {new_column['IS_NULLABLE']}")
            print(f"      По умолчанию: {new_column['COLUMN_DEFAULT']}")
            print(f"      Комментарий: {new_column['COLUMN_COMMENT']}")
        
        # Показываем индексы
        print("\n📑 Индексы таблицы competitor_schools:")
        cursor.execute("""
            SELECT DISTINCT INDEX_NAME, NON_UNIQUE, GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) as COLUMNS
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'competitor_schools'
            GROUP BY INDEX_NAME, NON_UNIQUE
            ORDER BY INDEX_NAME
        """)
        indexes = cursor.fetchall()
        for idx in indexes:
            index_type = "UNIQUE" if idx['NON_UNIQUE'] == 0 else "INDEX"
            print(f"   - {idx['INDEX_NAME']} ({index_type}): {idx['COLUMNS']}")
        
        # Финальная статистика
        cursor.execute("SELECT COUNT(*) as count FROM competitor_schools")
        total = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM competitor_schools WHERE is_new = 1")
        pending = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM competitor_schools WHERE is_new = 0")
        processed = cursor.fetchone()['count']
        
        print("\n📊 Статистика после миграции:")
        print(f"   Всего записей: {total}")
        print(f"   Обработанных (is_new = 0): {processed}")
        print(f"   Необработанных (is_new = 1): {pending}")
        
        print("\n" + "=" * 70)
        print("✅ МИГРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
        print("=" * 70)
        
        print("\n📝 Следующие шаги:")
        print("   1. Обновите backend API для работы с новым полем")
        print("   2. Обновите frontend компоненты")
        print("   3. При создании школ из SERP устанавливайте is_new = 1")
        print("   4. Перезапустите Flask сервер")
        
        return True
        
    except pymysql.err.OperationalError as e:
        print(f"\n❌ ОШИБКА подключения к БД:")
        print(f"   {e}")
        print("\n💡 Проверьте:")
        print("   1. MySQL сервер запущен")
        print("   2. Параметры подключения в backend/config.py или .env")
        print("   3. База данных существует")
        print("   4. Пользователь имеет права доступа")
        return False
        
    except Exception as e:
        print(f"\n❌ ОШИБКА при выполнении миграции:")
        print(f"   {type(e).__name__}: {e}")
        
        if connection:
            print("\n🔄 Откат изменений...")
            connection.rollback()
            print("   ✅ Откат выполнен")
        
        import traceback
        print("\n📋 Детали ошибки:")
        traceback.print_exc()
        
        return False
        
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("\n🔌 Соединение с БД закрыто")


if __name__ == '__main__':
    try:
        success = main()
        
        if success:
            print("\n🎉 Миграция завершена успешно!")
            sys.exit(0)
        else:
            print("\n⚠️  Миграция завершена с ошибками")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Миграция прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)