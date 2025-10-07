#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ реального ответа от DataForSEO API
Посмотрим, что именно возвращает API и почему реклама/карты не определяются
"""

import sys
import os
import json
from collections import Counter

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.dataforseo_client import get_dataforseo_client
from config import Config

def analyze_serp_response():
    """Анализируем реальный SERP ответ"""
    
    print("=" * 80)
    print("🔍 АНАЛИЗ РЕАЛЬНОГО SERP ОТВЕТА ОТ DataForSEO")
    print("=" * 80)
    
    try:
        # Получаем клиент
        client = get_dataforseo_client()
        
        # Тестовые запросы
        test_cases = [
            {
                'keyword': 'уроки фортепиано киев',
                'description': 'Информационный запрос'
            },
            {
                'keyword': 'купить пианино киев',
                'description': 'Коммерческий запрос (должна быть реклама)'
            },
            {
                'keyword': 'ресторан киев центр',
                'description': 'Локальный запрос (должны быть карты)'
            }
        ]
        
        for test in test_cases:
            keyword = test['keyword']
            
            print(f"\n{'=' * 80}")
            print(f"🔎 Тестируем: {keyword}")
            print(f"   ({test['description']})")
            print(f"{'=' * 80}\n")
            
            # Делаем SERP запрос
            response = client.get_serp(
                keyword=keyword,
                location_code=2804,  # Киев
                language_code='ru',
                device='desktop',
                depth=30
            )
            
            # Проверяем структуру ответа
            if not response.get('tasks'):
                print("❌ Нет 'tasks' в ответе")
                continue
            
            task = response['tasks'][0]
            
            if task.get('status_code') != 20000:
                print(f"❌ Ошибка API: {task.get('status_message')}")
                continue
            
            if not task.get('result'):
                print("❌ Нет 'result' в task")
                continue
            
            result = task['result'][0]
            items = result.get('items', [])
            
            if not items:
                print("⚠️ Нет 'items' в result")
                continue
            
            print(f"✅ Получено элементов: {len(items)}")
            print(f"💰 Стоимость: ${task.get('cost', 0)}")
            
            # Анализируем метаданные
            print(f"\n📊 МЕТАДАННЫЕ:")
            print(f"   - items_count: {result.get('items_count', 0)}")
            print(f"   - se_results_count: {result.get('se_results_count', 0)}")
            print(f"   - item_types: {result.get('item_types', [])}")
            
            # Считаем типы элементов
            type_counter = Counter()
            
            print(f"\n{'=' * 80}")
            print("📋 ДЕТАЛЬНЫЙ РАЗБОР КАЖДОГО ЭЛЕМЕНТА:")
            print(f"{'=' * 80}\n")
            
            for idx, item in enumerate(items, 1):
                item_type = item.get('type', 'UNKNOWN')
                rank_absolute = item.get('rank_absolute', 0)
                rank_group = item.get('rank_group', 0)
                
                type_counter[item_type] += 1
                
                # Выводим каждый элемент
                print(f"#{idx:2d} | type='{item_type:20s}' | rank_absolute={rank_absolute:3d} | rank_group={rank_group:3d}")
                
                # Дополнительные поля
                if 'domain' in item:
                    print(f"     domain: {item.get('domain', 'N/A')}")
                if 'title' in item:
                    title = item.get('title', '')
                    print(f"     title: {title[:70] if title else 'N/A'}")
                if 'url' in item:
                    url = item.get('url', '')
                    print(f"     url: {url[:80] if url else 'N/A'}")
                
                # Специальная обработка для local_pack
                if item_type == 'local_pack':
                    local_items = item.get('items', [])
                    if local_items:
                        print(f"     📍 Мест в local_pack: {len(local_items)}")
                        for i, place in enumerate(local_items[:3], 1):
                            print(f"        {i}. {place.get('title', 'No title')}")
                
                # Показываем ВСЕ ключи в item для диагностики
                print(f"     🔑 Все ключи в item: {list(item.keys())}")
                print()
            
            # Статистика
            print(f"\n{'=' * 80}")
            print("📊 СТАТИСТИКА ТИПОВ:")
            print(f"{'=' * 80}\n")
            
            for item_type, count in type_counter.most_common():
                print(f"   {item_type:20s}: {count:2d} шт.")
            
            # Проверка специальных типов
            print(f"\n{'=' * 80}")
            print("🎯 АНАЛИЗ РЕКЛАМЫ И КАРТ:")
            print(f"{'=' * 80}\n")
            
            # Все возможные варианты названий для рекламы
            ad_variants = ['paid', 'google_ads', 'shopping', 'ads', 'google_flights', 'google_hotels']
            found_ads = [t for t in type_counter.keys() if t in ad_variants]
            
            # Все возможные варианты для карт
            map_variants = ['local_pack', 'maps', 'map', 'google_maps']
            found_maps = [t for t in type_counter.keys() if t in map_variants]
            
            print(f"💰 РЕКЛАМА:")
            if found_ads:
                print(f"   ✅ Найдена реклама типов: {found_ads}")
                for ad_type in found_ads:
                    print(f"      - {ad_type}: {type_counter[ad_type]} шт.")
            else:
                print(f"   ❌ Реклама НЕ найдена")
                print(f"   ℹ️ Возможные причины:")
                print(f"      1. Информационный запрос (реклама действительно отсутствует)")
                print(f"      2. Геолокация (нет рекламодателей в данном регионе)")
                print(f"      3. API использует другие названия типов")
            
            print(f"\n🗺️ КАРТЫ GOOGLE:")
            if found_maps:
                print(f"   ✅ Найдены карты типов: {found_maps}")
                for map_type in found_maps:
                    print(f"      - {map_type}: {type_counter[map_type]} шт.")
            else:
                print(f"   ❌ Карты НЕ найдены")
                print(f"   ℹ️ Обычно карты показываются только для локальных запросов")
            
            # Рекомендации для кода
            print(f"\n{'=' * 80}")
            print("💡 РЕКОМЕНДАЦИИ ДЛЯ КОДА:")
            print(f"{'=' * 80}\n")
            
            all_types = list(type_counter.keys())
            
            # Для рекламы
            actual_ad_types = [t for t in all_types if t in ad_variants]
            if actual_ad_types:
                print(f"✅ Для определения РЕКЛАМЫ используйте:")
                print(f"   if item_type in {actual_ad_types}:")
                print(f"       has_ads = True\n")
            else:
                print(f"⚠️ Реклама не найдена в данных запросах\n")
            
            # Для карт
            actual_map_types = [t for t in all_types if t in map_variants]
            if actual_map_types:
                print(f"✅ Для определения КАРТ используйте:")
                print(f"   elif item_type in {actual_map_types}:")
                print(f"       has_google_maps = True\n")
            else:
                print(f"⚠️ Карты не найдены в данных запросах\n")
            
            # Для органики
            if 'organic' in all_types:
                print(f"✅ Органические результаты есть (тип 'organic')")
                print(f"   Органических результатов: {type_counter['organic']} шт.\n")
            
            # Сохраняем полный ответ в файл для детального анализа
            filename = f"serp_response_{keyword.replace(' ', '_')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(response, f, ensure_ascii=False, indent=2)
            print(f"💾 Полный ответ API сохранён в: {filename}")
            print()
        
        print("\n" + "=" * 80)
        print("✅ АНАЛИЗ ЗАВЕРШЁН")
        print("=" * 80)
        print("\n📌 ИТОГОВЫЕ ВЫВОДЫ:")
        print("   1. Проверьте типы элементов, которые реально возвращает API")
        print("   2. Обновите условия в parse_serp_response согласно найденным типам")
        print("   3. Полные ответы API сохранены в JSON файлы для детального изучения")
        print()
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        analyze_serp_response()
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)