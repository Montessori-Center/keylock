#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для диагностики проблем с позициями в SERP логах
"""

import sys
import os
import json
import pymysql
from datetime import datetime

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

def diagnose_serp_logs():
    """Диагностика SERP логов"""
    
    print("=" * 80)
    print("🔍 ДИАГНОСТИКА SERP ЛОГОВ")
    print("=" * 80)
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Получаем последние 5 логов
    cursor.execute("""
        SELECT id, keyword_text, created_at, parsed_items, analysis_result
        FROM serp_logs 
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    
    logs = cursor.fetchall()
    
    if not logs:
        print("❌ Нет SERP логов в БД")
        return
    
    print(f"\n📊 Найдено логов: {len(logs)}\n")
    
    for i, log in enumerate(logs, 1):
        print(f"\n{'=' * 80}")
        print(f"Лог #{i}: {log['keyword_text']} (ID: {log['id']})")
        print(f"Дата: {log['created_at']}")
        print(f"{'-' * 80}")
        
        # Проверяем analysis_result
        if log.get('analysis_result'):
            try:
                analysis_result = json.loads(log['analysis_result'])
                print("\n✅ analysis_result распарсен:")
                print(f"   - has_our_site: {analysis_result.get('has_our_site')}")
                print(f"   - our_organic_position: {analysis_result.get('our_organic_position')}")
                print(f"   - our_actual_position: {analysis_result.get('our_actual_position')}")
            except Exception as e:
                print(f"❌ Ошибка парсинга analysis_result: {e}")
        else:
            print("⚠️ analysis_result пустой")
        
        # Проверяем parsed_items
        if log.get('parsed_items'):
            try:
                parsed_items = json.loads(log['parsed_items'])
                organic_results = parsed_items.get('organic', [])
                
                print(f"\n✅ parsed_items распарсен:")
                print(f"   - Органических результатов: {len(organic_results)}")
                
                if organic_results:
                    print(f"\n   📝 Первые 3 результата:")
                    for j, item in enumerate(organic_results[:3], 1):
                        print(f"      {j}. {item.get('domain', 'NO DOMAIN')}")
                        print(f"         organic_position: {item.get('organic_position', 'MISSING!')}")
                        print(f"         actual_position: {item.get('actual_position', 'MISSING!')}")
                        print(f"         title: {item.get('title', '')[:50]}...")
                        
                        # КРИТИЧНО: Проверяем наличие ключей
                        if 'organic_position' not in item:
                            print(f"         ⚠️ WARNING: organic_position ОТСУТСТВУЕТ!")
                        if 'actual_position' not in item:
                            print(f"         ⚠️ WARNING: actual_position ОТСУТСТВУЕТ!")
                        
                        print()
                else:
                    print("   ⚠️ Нет органических результатов")
                    
            except Exception as e:
                print(f"❌ Ошибка парсинга parsed_items: {e}")
        else:
            print("⚠️ parsed_items пустой")
    
    cursor.close()
    connection.close()
    
    print("\n" + "=" * 80)
    print("✅ Диагностика завершена")
    print("=" * 80)

if __name__ == "__main__":
    try:
        diagnose_serp_logs()
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()