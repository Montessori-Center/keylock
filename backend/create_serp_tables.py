#!/usr/bin/env python3
"""
Скрипт для создания всех необходимых таблиц для SERP анализа
Запускать из директории backend: python3 create_all_serp_tables.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
import pymysql
from datetime import datetime

def create_connection():
    """Создаёт подключение к БД"""
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset='utf8mb4'
    )

def create_serp_tables():
    """Создание всех таблиц для SERP функционала"""
    
    connection = None
    try:
        print("=" * 60)
        print("🚀 СОЗДАНИЕ ТАБЛИЦ ДЛЯ SERP АНАЛИЗА")
        print("=" * 60)
        print(f"📊 База данных: {Config.DB_NAME}")
        print(f"🔧 Хост: {Config.DB_HOST}:{Config.DB_PORT}")
        print("-" * 60)
        
        connection = create_connection()
        cursor = connection.cursor()
        
        # 1. ТАБЛИЦА campaign_sites (сайты кампаний)
        print("\n1️⃣ Создание таблицы campaign_sites...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaign_sites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                campaign_id INT NOT NULL UNIQUE,
                site_url VARCHAR(255),
                domain VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
                INDEX idx_campaign_domain (campaign_id, domain)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("   ✅ Таблица campaign_sites создана/обновлена")
        
        # 2. ТАБЛИЦА school_sites (сайты школ-конкурентов)
        print("\n2️⃣ Создание таблицы school_sites...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS school_sites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL COMMENT 'Название школы/конкурента',
                domain VARCHAR(255) NOT NULL UNIQUE COMMENT 'Домен без www',
                full_url VARCHAR(500) COMMENT 'Полный URL сайта',
                is_active BOOLEAN DEFAULT TRUE COMMENT 'Активен ли для проверки',
                category VARCHAR(100) COMMENT 'Категория конкурента',
                notes TEXT COMMENT 'Заметки',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_domain (domain),
                INDEX idx_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("   ✅ Таблица school_sites создана/обновлена")
        
        # 3. ТАБЛИЦА serp_logs (логи SERP анализов)
        print("\n3️⃣ Создание таблицы serp_logs...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS serp_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                keyword_id INT NOT NULL,
                keyword_text VARCHAR(500),
                location_code INT,
                language_code VARCHAR(10),
                device VARCHAR(20),
                depth INT,
                
                -- Результаты анализа
                total_items INT,
                organic_count INT,
                paid_count INT,
                maps_count INT,
                shopping_count INT,
                
                -- Флаги
                has_ads BOOLEAN DEFAULT FALSE,
                has_maps BOOLEAN DEFAULT FALSE,
                has_our_site BOOLEAN DEFAULT FALSE,
                has_school_sites BOOLEAN DEFAULT FALSE,
                
                -- Детали
                intent_type VARCHAR(50),
                school_percentage DECIMAL(5,2),
                cost DECIMAL(10,6),
                
                -- Raw данные для отладки
                raw_response JSON,
                parsed_items JSON,
                
                -- Метаданные
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE,
                INDEX idx_keyword_date (keyword_id, created_at),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("   ✅ Таблица serp_logs создана/обновлена")
        
        # 4. Проверка/добавление колонок в keywords
        print("\n4️⃣ Проверка таблицы keywords...")
        
        # Проверяем и добавляем колонки если их нет
        columns_to_check = [
            ('is_new', 'BOOLEAN DEFAULT FALSE', 'Флаг новой записи'),
            ('batch_color', 'VARCHAR(20)', 'Цвет партии для выделения')
        ]
        
        for column_name, column_type, comment in columns_to_check:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'keywords' 
                AND COLUMN_NAME = %s
            """, (Config.DB_NAME, column_name))
            
            if cursor.fetchone()[0] == 0:
                print(f"   ➕ Добавляем колонку {column_name}...")
                try:
                    cursor.execute(f"""
                        ALTER TABLE keywords 
                        ADD COLUMN {column_name} {column_type} 
                        COMMENT '{comment}'
                    """)
                    print(f"   ✅ Колонка {column_name} добавлена")
                except pymysql.err.OperationalError as e:
                    if "Duplicate column name" in str(e):
                        print(f"   ℹ️ Колонка {column_name} уже существует")
                    else:
                        raise e
            else:
                print(f"   ✅ Колонка {column_name} уже существует")
        
        connection.commit()
        
        print("\n" + "=" * 60)
        print("📝 ДОБАВЛЕНИЕ ПРИМЕРОВ ДАННЫХ")
        print("=" * 60)
        
        # 5. Добавляем примеры данных
        # Проверяем есть ли уже данные в campaign_sites
        cursor.execute("SELECT COUNT(*) FROM campaign_sites")
        campaign_sites_count = cursor.fetchone()[0]
        
        if campaign_sites_count == 0:
            print("\n5️⃣ Добавление сайта для кампании...")
            cursor.execute("SELECT id, name FROM campaigns LIMIT 1")
            campaign = cursor.fetchone()
            
            if campaign:
                campaign_id = campaign[0]
                campaign_name = campaign[1]
                
                # Определяем домен по имени кампании
                if 'montessori' in campaign_name.lower():
                    site_url = 'https://montessori.ua'
                    domain = 'montessori.ua'
                else:
                    # Для других кампаний используем примерный домен
                    site_url = 'https://example.com'
                    domain = 'example.com'
                
                cursor.execute("""
                    INSERT INTO campaign_sites (campaign_id, site_url, domain) 
                    VALUES (%s, %s, %s)
                """, (campaign_id, site_url, domain))
                print(f"   ✅ Добавлен сайт {domain} для кампании '{campaign_name}'")
                connection.commit()
        else:
            print("\n5️⃣ Сайты кампаний уже настроены")
        
        # 6. Добавляем школы-конкуренты
        cursor.execute("SELECT COUNT(*) FROM school_sites")
        school_sites_count = cursor.fetchone()[0]
        
        if school_sites_count == 0:
            print("\n6️⃣ Добавление сайтов школ-конкурентов...")
            
            schools = [
                # Музыкальные школы Киева (реальные)
                ('Jam Music School', 'jam.ua', 'https://jam.ua', True, 'Музыкальная школа', 'Популярная школа в Киеве'),
                ('ArtVocal', 'artvocal.com.ua', 'https://artvocal.com.ua', True, 'Вокальная школа', ''),
                ('Music School', 'music-school.com.ua', 'https://music-school.com.ua', True, 'Музыкальная школа', ''),
                ('Maestro', 'maestro.kiev.ua', 'https://maestro.kiev.ua', True, 'Музыкальная школа', ''),
                ('Rock School', 'rockschool.com.ua', 'https://rockschool.com.ua', True, 'Рок-школа', ''),
                ('Virtuosos', 'virtuosos.com.ua', 'https://virtuosos.com.ua', True, 'Музыкальная школа', ''),
                ('Montessori School', 'montessori-school.com.ua', 'https://montessori-school.com.ua', True, 'Монтессори школа', 'Конкурент по Монтессори'),
                ('Guitar College', 'guitarcollege.com.ua', 'https://guitarcollege.com.ua', True, 'Гитарная школа', ''),
                ('Vocal Freedom', 'vocalfreedom.com.ua', 'https://vocalfreedom.com.ua', True, 'Вокальная школа', ''),
                ('Music House', 'musichouse.ua', 'https://musichouse.ua', True, 'Музыкальная школа', ''),
            ]
            
            added_schools = 0
            for school_data in schools:
                try:
                    cursor.execute("""
                        INSERT INTO school_sites (name, domain, full_url, is_active, category, notes)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, school_data)
                    added_schools += 1
                    print(f"   ✅ Добавлена школа: {school_data[0]} ({school_data[1]})")
                except pymysql.err.IntegrityError:
                    print(f"   ⚠️ Школа {school_data[1]} уже существует")
            
            if added_schools > 0:
                connection.commit()
                print(f"   📚 Всего добавлено школ: {added_schools}")
        else:
            print(f"\n6️⃣ Школы-конкуренты уже добавлены ({school_sites_count} шт)")
        
        print("\n" + "=" * 60)
        print("📊 ИТОГОВАЯ СТАТИСТИКА")
        print("=" * 60)
        
        # 7. Показываем статистику
        cursor.execute("SELECT COUNT(*) FROM campaign_sites")
        print(f"✅ Сайтов кампаний: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM school_sites WHERE is_active = TRUE")
        print(f"✅ Активных школ-конкурентов: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM serp_logs")
        print(f"✅ SERP логов: {cursor.fetchone()[0]}")
        
        # Показываем настроенные домены
        print("\n📌 Настроенные домены кампаний:")
        cursor.execute("""
            SELECT c.name, cs.domain 
            FROM campaigns c
            LEFT JOIN campaign_sites cs ON c.id = cs.campaign_id
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"   • {row[0]}: {row[1] or 'НЕ УКАЗАН'}")
        
        print("\n🏫 Примеры школ-конкурентов:")
        cursor.execute("SELECT name, domain FROM school_sites WHERE is_active = TRUE LIMIT 5")
        for row in cursor.fetchall():
            print(f"   • {row[0]}: {row[1]}")
        
        cursor.close()
        
        print("\n" + "=" * 60)
        print("✨ ВСЕ ТАБЛИЦЫ УСПЕШНО СОЗДАНЫ!")
        print("=" * 60)
        print("\n📝 Следующие шаги:")
        print("1. Проверьте домен вашего сайта в настройках")
        print("2. Добавьте больше школ-конкурентов если нужно")
        print("3. Запустите SERP анализ для тестирования")
        print("4. Проверьте логи в таблице serp_logs")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {str(e)}")
        if connection:
            connection.rollback()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if connection:
            connection.close()

def show_quick_sql_commands():
    """Показывает полезные SQL команды для работы с таблицами"""
    print("\n" + "=" * 60)
    print("📋 ПОЛЕЗНЫЕ SQL КОМАНДЫ")
    print("=" * 60)
    
    commands = """
# Просмотр последних SERP логов:
SELECT * FROM serp_logs ORDER BY created_at DESC LIMIT 5;

# Проверка доменов кампаний:
SELECT c.name, cs.domain FROM campaigns c 
LEFT JOIN campaign_sites cs ON c.id = cs.campaign_id;

# Список школ-конкурентов:
SELECT name, domain, is_active FROM school_sites;

# Анализы где не нашли наш сайт:
SELECT keyword_text, has_our_site, has_school_sites, intent_type 
FROM serp_logs WHERE has_our_site = FALSE;

# Обновить домен кампании:
UPDATE campaign_sites SET domain = 'yourdomain.com' WHERE campaign_id = 1;

# Добавить новую школу:
INSERT INTO school_sites (name, domain, full_url, is_active) 
VALUES ('Школа', 'school.com', 'https://school.com', TRUE);
"""
    
    print(commands)

if __name__ == "__main__":
    print("\n🔧 Запуск скрипта создания таблиц SERP...")
    print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = create_serp_tables()
    
    if success:
        show_quick_sql_commands()
        print("\n✅ Скрипт выполнен успешно!")
        sys.exit(0)
    else:
        print("\n❌ Скрипт завершен с ошибками")
        print("Проверьте настройки подключения к БД в файле .env")
        sys.exit(1)