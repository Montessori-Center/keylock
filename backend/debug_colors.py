#!/usr/bin/env python3
# backend/debug_colors.py - скрипт для проверки цветов новых записей

import pymysql
from config import Config
import json

def check_colors():
    """Проверяет и выводит информацию о цветах новых записей"""
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
        
        print("=" * 60)
        print("🎨 ПРОВЕРКА ЦВЕТОВ НОВЫХ ЗАПИСЕЙ")
        print("=" * 60)
        
        # 1. Проверяем структуру таблицы
        cursor.execute("DESCRIBE keywords")
        columns = cursor.fetchall()
        has_is_new = any(col['Field'] == 'is_new' for col in columns)
        has_batch_color = any(col['Field'] == 'batch_color' for col in columns)
        
        print(f"\n✅ Поле is_new: {'существует' if has_is_new else 'НЕ НАЙДЕНО!'}")
        print(f"✅ Поле batch_color: {'существует' if has_batch_color else 'НЕ НАЙДЕНО!'}")
        
        if not has_is_new or not has_batch_color:
            print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Необходимые поля отсутствуют!")
            print("Выполните:")
            print("  python3 add_is_new_field.py")
            print("  python3 add_batch_color_field.py")
            return
        
        # 2. Проверяем новые записи
        cursor.execute("""
            SELECT ad_group_id, COUNT(*) as count, 
                   GROUP_CONCAT(DISTINCT batch_color) as colors
            FROM keywords 
            WHERE is_new = TRUE
            GROUP BY ad_group_id
        """)
        new_records = cursor.fetchall()
        
        print(f"\n📊 СТАТИСТИКА НОВЫХ ЗАПИСЕЙ:")
        print("-" * 40)
        
        if not new_records:
            print("Нет новых записей (is_new = TRUE)")
        else:
            for record in new_records:
                print(f"Группа {record['ad_group_id']}: {record['count']} новых записей")
                print(f"  Цвета: {record['colors']}")
        
        # 3. Детальный вывод новых записей
        cursor.execute("""
            SELECT id, ad_group_id, keyword, is_new, batch_color
            FROM keywords 
            WHERE is_new = TRUE
            LIMIT 10
        """)
        details = cursor.fetchall()
        
        if details:
            print(f"\n📝 ПРИМЕРЫ НОВЫХ ЗАПИСЕЙ (первые 10):")
            print("-" * 40)
            for row in details:
                print(f"ID {row['id']}: {row['keyword'][:30]}")
                print(f"  Группа: {row['ad_group_id']}, Цвет: {row['batch_color']}")
        
        # 4. Проверяем уникальность цветов
        cursor.execute("""
            SELECT batch_color, COUNT(*) as count, 
                   GROUP_CONCAT(DISTINCT ad_group_id) as groups
            FROM keywords 
            WHERE is_new = TRUE AND batch_color IS NOT NULL
            GROUP BY batch_color
        """)
        color_usage = cursor.fetchall()
        
        if color_usage:
            print(f"\n🎨 ИСПОЛЬЗОВАНИЕ ЦВЕТОВ:")
            print("-" * 40)
            for color in color_usage:
                print(f"Цвет {color['batch_color']}: {color['count']} записей в группах {color['groups']}")
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 60)
        print("✅ ПРОВЕРКА ЗАВЕРШЕНА")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

def reset_test_colors():
    """Добавляет тестовые новые записи с цветами для проверки"""
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = connection.cursor()
        
        print("\n🔧 ДОБАВЛЕНИЕ ТЕСТОВЫХ НОВЫХ ЗАПИСЕЙ...")
        
        # Палитра цветов
        colors = ['#fff2cc', '#e1d5e7', '#dae8fc', '#d5e8d4', '#ffe6cc']
        
        # Сбрасываем все is_new флаги
        cursor.execute("UPDATE keywords SET is_new = FALSE, batch_color = NULL")
        
        # Добавляем по 2 новые записи в первые 3 группы с разными цветами
        for ad_group_id in range(1, 4):
            color = colors[ad_group_id - 1]
            cursor.execute("""
                UPDATE keywords 
                SET is_new = TRUE, batch_color = %s
                WHERE ad_group_id = %s
                LIMIT 2
            """, (color, ad_group_id))
            
            affected = cursor.rowcount
            print(f"  Группа {ad_group_id}: установлен цвет {color} для {affected} записей")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("✅ Тестовые данные добавлены!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        reset_test_colors()
    
    check_colors()
    
    if len(sys.argv) == 1:
        print("\nСовет: запустите с флагом --test для добавления тестовых данных:")
        print("  python3 debug_colors.py --test")