#!/usr/bin/env python3
# backend/debug_serp_logs.py
"""
Скрипт для проверки данных SERP логов в БД
"""

import pymysql
import json
import sys
from config import Config

def debug_serp_logs():
    """Проверяет последний SERP лог"""
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
        
        # Получаем последний лог
        cursor.execute("""
            SELECT id, keyword_text, created_at, parsed_items, analysis_result
            FROM serp_logs 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        
        log = cursor.fetchone()
        
        if not log:
            print("❌ Нет логов в БД")
            return
        
        print("\n" + "="*80)
        print(f"📊 ПОСЛЕДНИЙ SERP ЛОГ")
        print("="*80)
        print(f"ID: {log['id']}")
        print(f"Ключевое слово: {log['keyword_text']}")
        print(f"Дата: {log['created_at']}")
        
        # Парсим parsed_items
        if log.get('parsed_items'):
            print("\n" + "-"*80)
            print("📋 PARSED_ITEMS:")
            print("-"*80)
            
            try:
                parsed_items = json.loads(log['parsed_items'])
                
                organic = parsed_items.get('organic', [])
                print(f"\n✅ Найдено органических результатов: {len(organic)}")
                
                if organic:
                    print("\n🔍 ПЕРВЫЕ 5 ОРГАНИЧЕСКИХ РЕЗУЛЬТАТОВ:")
                    for i, item in enumerate(organic[:5], 1):
                        print(f"\n  [{i}] {item.get('domain', 'N/A')}")
                        print(f"      organic_position: {item.get('organic_position', 'ОТСУТСТВУЕТ')}")
                        print(f"      actual_position: {item.get('actual_position', 'ОТСУТСТВУЕТ')}")
                        print(f"      rank_absolute: {item.get('rank_absolute', 'ОТСУТСТВУЕТ')}")
                        print(f"      position: {item.get('position', 'ОТСУТСТВУЕТ')}")
                        print(f"      title: {item.get('title', 'N/A')[:50]}...")
                        
                    # Ищем montessori.ua
                    montessori = [item for item in organic if 'montessori' in item.get('domain', '').lower()]
                    if montessori:
                        print("\n🎯 НАЙДЕН MONTESSORI.UA:")
                        for item in montessori:
                            print(f"      domain: {item.get('domain')}")
                            print(f"      organic_position: {item.get('organic_position', 'ОТСУТСТВУЕТ')}")
                            print(f"      actual_position: {item.get('actual_position', 'ОТСУТСТВУЕТ')}")
                    else:
                        print("\n⚠️  MONTESSORI.UA НЕ НАЙДЕН в organic_results")
                else:
                    print("❌ Массив organic пустой")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Ошибка парсинга parsed_items: {e}")
        else:
            print("\n❌ parsed_items пустой или NULL")
        
        # Парсим analysis_result
        if log.get('analysis_result'):
            print("\n" + "-"*80)
            print("📊 ANALYSIS_RESULT:")
            print("-"*80)
            
            try:
                analysis = json.loads(log['analysis_result'])
                
                print(f"  has_our_site: {analysis.get('has_our_site', 'ОТСУТСТВУЕТ')}")
                print(f"  our_organic_position: {analysis.get('our_organic_position', 'ОТСУТСТВУЕТ')}")
                print(f"  our_actual_position: {analysis.get('our_actual_position', 'ОТСУТСТВУЕТ')}")
                print(f"  has_ads: {analysis.get('has_ads', 'ОТСУТСТВУЕТ')}")
                print(f"  has_google_maps: {analysis.get('has_google_maps', 'ОТСУТСТВУЕТ')}")
                print(f"  intent_type: {analysis.get('intent_type', 'ОТСУТСТВУЕТ')}")
                
            except json.JSONDecodeError as e:
                print(f"❌ Ошибка парсинга analysis_result: {e}")
        else:
            print("\n❌ analysis_result пустой или NULL")
        
        # Проверяем campaign_sites
        print("\n" + "-"*80)
        print("🏢 CAMPAIGN_SITES:")
        print("-"*80)
        
        cursor.execute("SELECT id, campaign_id, domain FROM campaign_sites")
        sites = cursor.fetchall()
        
        if sites:
            for site in sites:
                print(f"  Campaign ID {site['campaign_id']}: {site['domain']}")
        else:
            print("  ❌ Нет записей в campaign_sites")
        
        cursor.close()
        connection.close()
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_serp_logs()