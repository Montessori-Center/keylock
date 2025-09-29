#!/usr/bin/env python3
"""
Скрипт для создания новых таблиц для SERP анализа
Запускать из директории backend: python3 create_serp_tables.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
import pymysql

def create_serp_tables():
    """Создание новых таблиц для SERP функционала"""
    
    connection = None
    try:
        print("🔧 Подключение к БД...")
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = connection.cursor()
        
        print("📋 Создание таблицы campaign_sites...")
        
        # Таблица сайтов кампаний (наши сайты)
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
        print("✅ Таблица campaign_sites создана/обновлена")
        
        print("📋 Создание таблицы school_sites...")
        
        # Таблица сайтов школ-конкурентов
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
        print("✅ Таблица school_sites создана/обновлена")
        
        # Проверяем, нужно ли добавить новые колонки в keywords если их нет
        print("📋 Проверка структуры таблицы keywords...")
        
        # Проверяем наличие колонки is_new
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'keywords' 
            AND COLUMN_NAME = 'is_new'
        """, (Config.DB_NAME,))
        
        if cursor.fetchone()[0] == 0:
            print("   Добавляем колонку is_new...")
            cursor.execute("""
                ALTER TABLE keywords 
                ADD COLUMN is_new BOOLEAN DEFAULT FALSE 
                COMMENT 'Флаг новой записи' 
                AFTER labels
            """)
            print("   ✅ Колонка is_new добавлена")
        
        # Проверяем наличие колонки batch_color
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'keywords' 
            AND COLUMN_NAME = 'batch_color'
        """, (Config.DB_NAME,))
        
        if cursor.fetchone()[0] == 0:
            print("   Добавляем колонку batch_color...")
            cursor.execute("""
                ALTER TABLE keywords 
                ADD COLUMN batch_color VARCHAR(20) 
                COMMENT 'Цвет партии для выделения' 
                AFTER is_new
            """)
            print("   ✅ Колонка batch_color добавлена")
        
        # Добавляем тестовые данные для примера
        print("\n📝 Добавление примеров данных...")
        
        # Проверяем, есть ли уже данные в campaign_sites
        cursor.execute("SELECT COUNT(*) FROM campaign_sites")
        if cursor.fetchone()[0] == 0:
            # Получаем первую кампанию
            cursor.execute("SELECT id, name FROM campaigns LIMIT 1")
            campaign = cursor.fetchone()
            
            if campaign:
                campaign_id = campaign[0]
                campaign_name = campaign[1]
                
                # Добавляем сайт для кампании (пример)
                if 'montessori' in campaign_name.lower():
                    cursor.execute("""
                        INSERT INTO campaign_sites (campaign_id, site_url, domain) 
                        VALUES (%s, 'https://montessori.ua', 'montessori.ua')
                    """, (campaign_id,))
                    print(f"   ✅ Добавлен пример сайта для кампании {campaign_name}")
        
        # Добавляем примеры сайтов школ-конкурентов
        cursor.execute("SELECT COUNT(*) FROM school_sites")
        if cursor.fetchone()[0] == 0:
            example_schools = [
                ('Музыкальная школа Jam', 'jam.ua', 'https://jam.ua', True, 'Музыкальная школа', 'Основной конкурент'),
                ('Арт-школа Монтессори', 'artschool.com.ua', 'https://artschool.com.ua', True, 'Арт-школа', ''),
                ('Музыкальная академия', 'music-academy.kiev.ua', 'https://music-academy.kiev.ua', True, 'Музыкальная школа', ''),
                ('Школа вокала Voice', 'voiceschool.com.ua', 'https://voiceschool.com.ua', True, 'Вокальная школа', ''),
                ('Гитарная школа', 'guitar-school.kiev.ua', 'https://guitar-school.kiev.ua', True, 'Музыкальная школа', ''),
            ]
            
            for school_data in example_schools:
                try:
                    cursor.execute("""
                        INSERT INTO school_sites (name, domain, full_url, is_active, category, notes)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, school_data)
                    print(f"   ✅ Добавлен сайт школы: {school_data[0]}")
                except pymysql.err.IntegrityError:
                    print(f"   ⚠️ Сайт {school_data[1]} уже существует")
        
        # Применяем изменения
        connection.commit()
        
        print("\n📊 Итоговая статистика:")
        
        # Показываем статистику
        cursor.execute("SELECT COUNT(*) FROM campaign_sites")
        print(f"   Сайтов кампаний: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM school_sites")
        print(f"   Сайтов школ-конкурентов: {cursor.fetchone()[0]}")
        
        # Показываем список школ
        cursor.execute("SELECT name, domain, is_active FROM school_sites ORDER BY name")
        schools = cursor.fetchall()
        if schools:
            print("\n📚 Список сайтов школ-конкурентов:")
            for school in schools:
                status = "✅" if school[2] else "⏸️"
                print(f"   {status} {school[0]}: {school[1]}")
        
        cursor.close()
        print("\n✨ Все таблицы успешно созданы и настроены!")
        print("   Теперь можно использовать SERP анализ с определением сайтов школ")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка: {str(e)}")
        if connection:
            connection.rollback()
        return False
        
    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Создание таблиц для SERP анализа")
    print("=" * 50)
    
    success = create_serp_tables()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ Скрипт выполнен успешно!")
        print("=" * 50)
        sys.exit(0)
    else:
        print("\n" + "=" * 50)
        print("❌ Скрипт завершен с ошибками")
        print("=" * 50)
        sys.exit(1)