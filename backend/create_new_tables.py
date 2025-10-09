#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Миграция: Добавление таблиц для школ-конкурентов и SERP-анализа
Файл: backend/migrations/add_competitors_tables.py
"""

import pymysql
import sys
import os

# Добавляем путь к корню проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def run_migration():
    """Выполнение миграции"""
    print("=" * 70)
    print("МИГРАЦИЯ: Добавление таблиц конкурентов")
    print("=" * 70)
    
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
        print("✅ Подключение к БД установлено")
        
        # 1. Таблица campaign_sites (домены наших сайтов)
        print("\n📝 Создание таблицы campaign_sites...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaign_sites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                campaign_id INT NOT NULL,
                site_url VARCHAR(500),
                domain VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_campaign (campaign_id),
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Таблица campaign_sites создана")
        
        # 2. Таблица school_sites (старая версия, для совместимости)
        print("\n📝 Создание таблицы school_sites...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS school_sites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                domain VARCHAR(255) NOT NULL UNIQUE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_domain (domain),
                INDEX idx_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Таблица school_sites создана")
        
        # 3. Основная таблица competitor_schools
        print("\n📝 Создание таблицы competitor_schools...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitor_schools (
                id INT AUTO_INCREMENT PRIMARY KEY,
                domain VARCHAR(255) NOT NULL UNIQUE,
                org_type ENUM('Школа', 'База репетиторов', 'Не школа', 'Партнёр') DEFAULT 'Школа',
                competitiveness INT DEFAULT 0 COMMENT 'Частота появлений в SERP',
                last_seen_at TIMESTAMP NULL COMMENT 'Последнее появление в SERP',
                notes TEXT COMMENT 'Заметки пользователя',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_domain (domain),
                INDEX idx_org_type (org_type),
                INDEX idx_competitiveness (competitiveness)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Таблица competitor_schools создана")
        
        # 4. Таблица для истории SERP-анализов
        print("\n📝 Создание таблицы serp_analysis_history...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS serp_analysis_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                keyword_id INT NOT NULL,
                keyword_text VARCHAR(500) NOT NULL,
                campaign_id INT NOT NULL,
                analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                has_ads BOOLEAN DEFAULT FALSE,
                has_maps BOOLEAN DEFAULT FALSE,
                has_our_site BOOLEAN DEFAULT FALSE,
                has_school_sites BOOLEAN DEFAULT FALSE,
                intent_type VARCHAR(50),
                organic_count INT DEFAULT 0,
                paid_count INT DEFAULT 0,
                maps_count INT DEFAULT 0,
                school_percentage DECIMAL(5,2) DEFAULT 0,
                cost DECIMAL(10, 4) DEFAULT 0,
                parsed_items JSON COMMENT 'JSON с детальными данными',
                analysis_result JSON COMMENT 'JSON с результатами анализа',
                FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
                INDEX idx_keyword_id (keyword_id),
                INDEX idx_analysis_date (analysis_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Таблица serp_analysis_history создана")
        
        # 5. Таблица связей: какие домены найдены в каких SERP-анализах
        print("\n📝 Создание таблицы serp_competitor_appearances...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS serp_competitor_appearances (
                id INT AUTO_INCREMENT PRIMARY KEY,
                serp_analysis_id INT NOT NULL,
                competitor_id INT NOT NULL,
                position INT COMMENT 'Позиция в выдаче',
                result_type ENUM('organic', 'paid', 'maps') DEFAULT 'organic',
                url TEXT COMMENT 'Конкретный URL',
                title TEXT COMMENT 'Заголовок результата',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (serp_analysis_id) REFERENCES serp_analysis_history(id) ON DELETE CASCADE,
                FOREIGN KEY (competitor_id) REFERENCES competitor_schools(id) ON DELETE CASCADE,
                INDEX idx_serp_analysis (serp_analysis_id),
                INDEX idx_competitor (competitor_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Таблица serp_competitor_appearances создана")
        
        # 6. Мигрируем данные из school_sites в competitor_schools (если есть)
        print("\n📝 Миграция данных из school_sites в competitor_schools...")
        cursor.execute("""
            INSERT IGNORE INTO competitor_schools (domain, org_type, created_at)
            SELECT domain, 'Школа', created_at
            FROM school_sites
            WHERE is_active = TRUE
        """)
        migrated = cursor.rowcount
        print(f"✅ Мигрировано записей: {migrated}")
        
        # Сохраняем изменения
        connection.commit()
        print("\n" + "=" * 70)
        print("✅ МИГРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
        print("=" * 70)
        
        # Проверяем созданные таблицы
        print("\n📊 Созданные таблицы:")
        cursor.execute("SHOW TABLES")
        all_tables = cursor.fetchall()
        
        relevant_tables = []
        for table in all_tables:
            table_name = list(table.values())[0]
            if any(keyword in table_name for keyword in ['competitor', 'serp', 'campaign_sites', 'school_sites']):
                relevant_tables.append(table_name)
                print(f"   • {table_name}")
        
        if not relevant_tables:
            print("   ⚠️ Таблицы конкурентов не найдены")
        else:
            print(f"\n✅ Всего создано таблиц для конкурентов: {len(relevant_tables)}")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА МИГРАЦИИ: {e}")
        if connection:
            connection.rollback()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if connection:
            connection.close()
            print("\n🔌 Соединение с БД закрыто")

if __name__ == '__main__':
    print("\n🚀 Запуск миграции...")
    success = run_migration()
    
    if success:
        print("\n✅ Миграция выполнена успешно!")
        sys.exit(0)
    else:
        print("\n❌ Миграция завершилась с ошибками!")
        sys.exit(1)