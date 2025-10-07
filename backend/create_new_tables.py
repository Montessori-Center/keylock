#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление структуры таблицы serp_logs
Добавление/проверка правильных типов для JSON-полей
"""

import sys
import os
import pymysql

# Добавляем путь к backend для импорта модулей
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from config import Config

def get_db_connection():
    """Подключение к БД"""
    return pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT,
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4'
    )

def fix_serp_logs_table():
    """Исправление таблицы serp_logs"""
    
    print("=" * 80)
    print("🔧 ИСПРАВЛЕНИЕ ТАБЛИЦЫ serp_logs")
    print("=" * 80)
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # 1. Проверяем текущую структуру
        print("\n1️⃣ Проверка текущей структуры таблицы...")
        cursor.execute("DESCRIBE serp_logs")
        columns = cursor.fetchall()
        
        print("\n📋 Текущие колонки:")
        for col in columns:
            print(f"   - {col['Field']}: {col['Type']} (Null: {col['Null']})")
        
        # 2. Изменяем типы JSON-полей на LONGTEXT
        print("\n2️⃣ Изменение типов JSON-полей на LONGTEXT...")
        
        changes = [
            ('analysis_result', 'LONGTEXT'),
            ('parsed_items', 'LONGTEXT'),
            ('raw_response', 'LONGTEXT')
        ]
        
        for column_name, column_type in changes:
            try:
                alter_query = f"""
                    ALTER TABLE serp_logs 
                    MODIFY COLUMN {column_name} {column_type} 
                    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL
                """
                cursor.execute(alter_query)
                print(f"   ✅ {column_name} -> {column_type}")
            except pymysql.err.OperationalError as e:
                if "Duplicate column name" in str(e) or "Unknown column" in str(e):
                    print(f"   ⚠️ {column_name}: колонка уже существует или не найдена")
                else:
                    raise
        
        connection.commit()
        
        # 3. Проверяем результат
        print("\n3️⃣ Проверка после изменений...")
        cursor.execute("DESCRIBE serp_logs")
        columns = cursor.fetchall()
        
        print("\n📋 Обновлённые колонки:")
        for col in columns:
            if col['Field'] in ['analysis_result', 'parsed_items', 'raw_response']:
                print(f"   ✅ {col['Field']}: {col['Type']} (Null: {col['Null']})")
        
        # 4. Проверяем состояние данных
        print("\n4️⃣ Проверка состояния данных...")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN analysis_result IS NULL OR analysis_result = '' THEN 1 ELSE 0 END) as empty_analysis,
                SUM(CASE WHEN parsed_items IS NULL OR parsed_items = '' THEN 1 ELSE 0 END) as empty_parsed
            FROM serp_logs
        """)
        stats = cursor.fetchone()
        
        print(f"\n📊 Статистика данных:")
        print(f"   Всего записей: {stats['total']}")
        print(f"   С пустым analysis_result: {stats['empty_analysis']}")
        print(f"   С пустым parsed_items: {stats['empty_parsed']}")
        
        # 5. Спрашиваем об удалении некорректных записей
        if stats['empty_analysis'] > 0 or stats['empty_parsed'] > 0:
            print("\n⚠️ Обнаружены записи с пустыми JSON-полями")
            response = input("❓ Удалить некорректные записи? (yes/no): ").strip().lower()
            
            if response == 'yes':
                cursor.execute("""
                    DELETE FROM serp_logs 
                    WHERE analysis_result IS NULL 
                       OR analysis_result = ''
                       OR parsed_items IS NULL
                       OR parsed_items = ''
                """)
                deleted = cursor.rowcount
                connection.commit()
                print(f"   ✅ Удалено некорректных записей: {deleted}")
            else:
                print("   ℹ️ Некорректные записи оставлены без изменений")
        
        # 6. Показываем последние записи
        print("\n5️⃣ Проверка последних записей...")
        cursor.execute("""
            SELECT 
                id,
                keyword_text,
                created_at,
                CHAR_LENGTH(parsed_items) as parsed_len,
                CHAR_LENGTH(analysis_result) as analysis_len,
                CASE 
                    WHEN analysis_result IS NULL THEN '❌ NULL'
                    WHEN analysis_result = '' THEN '⚠️ EMPTY'
                    ELSE '✅ OK'
                END as status
            FROM serp_logs 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        records = cursor.fetchall()
        
        print("\n📝 Последние 5 записей:")
        for rec in records:
            print(f"   ID {rec['id']}: {rec['keyword_text']}")
            print(f"      Дата: {rec['created_at']}")
            print(f"      parsed_items: {rec['parsed_len'] or 0} байт")
            print(f"      analysis_result: {rec['analysis_len'] or 0} байт")
            print(f"      Статус: {rec['status']}")
            print()
        
        print("=" * 80)
        print("✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО")
        print("=" * 80)
        print("\n📌 Следующие шаги:")
        print("   1. Обновите код функции parse_serp_response в backend/api/dataforseo.py")
        print("   2. Перезапустите backend-сервер")
        print("   3. Запустите SERP анализ заново для тестовых ключевых слов")
        print("   4. Проверьте результат через debug_serp_logs.py")
        print()
        
    except Exception as e:
        connection.rollback()
        print(f"\n❌ Ошибка при исправлении: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        cursor.close()
        connection.close()
    
    return True

if __name__ == "__main__":
    try:
        success = fix_serp_logs_table()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)