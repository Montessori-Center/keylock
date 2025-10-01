#!/usr/bin/env python3
# create_serp_tables.py - выполните этот скрипт в папке backend

import pymysql
from config import Config

def create_serp_tables():
    """Создание недостающих таблиц для SERP функционала"""
    connection = None
    try:
        # Подключаемся к БД
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = connection.cursor()
        
        print("🔨 Создаю таблицы для SERP функционала...")
        
        # Таблица для логирования SERP анализов
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS serp_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            keyword_id INT,
            keyword_text VARCHAR(500),
            location_code INT,
            language_code VARCHAR(10),
            device VARCHAR(50),
            depth INT,
            total_items INT DEFAULT 0,
            organic_count INT DEFAULT 0,
            paid_count INT DEFAULT 0,
            maps_count INT DEFAULT 0,
            shopping_count INT DEFAULT 0,
            has_ads BOOLEAN DEFAULT FALSE,
            has_maps BOOLEAN DEFAULT FALSE,
            has_our_site BOOLEAN DEFAULT FALSE,
            has_school_sites BOOLEAN DEFAULT FALSE,
            intent_type VARCHAR(50),
            school_percentage DECIMAL(5,2),
            cost DECIMAL(10,4),
            raw_response JSON,
            parsed_items JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE SET NULL,
            INDEX idx_keyword_id (keyword_id),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Таблица serp_logs создана")
        
        # Таблица для хранения сайтов кампаний
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaign_sites (
            id INT AUTO_INCREMENT PRIMARY KEY,
            campaign_id INT NOT NULL,
            site_url VARCHAR(500),
            domain VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_campaign (campaign_id),
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
            INDEX idx_domain (domain)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Таблица campaign_sites создана")
        
        # Таблица для хранения сайтов школ-конкурентов
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS school_sites (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            domain VARCHAR(255) NOT NULL,
            full_url VARCHAR(500),
            is_active BOOLEAN DEFAULT TRUE,
            category VARCHAR(100),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_domain (domain),
            INDEX idx_active (is_active)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Таблица school_sites создана")
        
        # Добавляем поля для новых ключевых слов (если еще не добавлены)
        try:
            cursor.execute("""
            ALTER TABLE keywords 
            ADD COLUMN IF NOT EXISTS is_new BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS batch_color VARCHAR(20)
            """)
            print("✅ Поля is_new и batch_color добавлены")
        except:
            print("ℹ️ Поля is_new и batch_color уже существуют")
        
        # Вставляем тестовые данные для сайтов школ
        cursor.execute("""
        INSERT IGNORE INTO school_sites (name, domain, full_url, category) VALUES 
        ('JAM Music School', 'jam.ua', 'https://jam.ua', 'Музыкальная школа'),
        ('Art School', 'artschool.com.ua', 'https://artschool.com.ua', 'Школа искусств'),
        ('Music Academy Kiev', 'music-academy.kiev.ua', 'https://music-academy.kiev.ua', 'Музыкальная академия'),
        ('Voice School', 'voiceschool.com.ua', 'https://voiceschool.com.ua', 'Вокальная школа'),
        ('Guitar School Kiev', 'guitar-school.kiev.ua', 'https://guitar-school.kiev.ua', 'Гитарная школа')
        """)
        print(f"✅ Добавлено школ-конкурентов: {cursor.rowcount}")
        
        # Вставляем сайт для первой кампании
        cursor.execute("""
        INSERT INTO campaign_sites (campaign_id, site_url, domain) 
        SELECT 1, 'https://montessori.ua', 'montessori.ua' 
        FROM dual 
        WHERE EXISTS (SELECT 1 FROM campaigns WHERE id = 1)
        ON DUPLICATE KEY UPDATE domain = VALUES(domain)
        """)
        print(f"✅ Сайт montessori.ua привязан к кампании")
        
        connection.commit()
        cursor.close()
        
        print("\n🎉 Все таблицы успешно созданы!")
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    create_serp_tables()