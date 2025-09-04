# init_db.py - Полностью автоматическая инициализация БД
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
import pymysql

def check_database_exists():
    """Проверка существования БД"""
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        cursor = connection.cursor()
        cursor.execute(f"SHOW DATABASES LIKE '{Config.DB_NAME}'")
        result = cursor.fetchone()
        
        if not result:
            print(f"❌ БД {Config.DB_NAME} не существует. Создаю...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ БД {Config.DB_NAME} создана")
        else:
            print(f"✅ БД {Config.DB_NAME} существует")
        
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к MySQL: {e}")
        return False

def check_tables_exist():
    """Проверка существования таблиц"""
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = connection.cursor()
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        cursor.close()
        connection.close()
        
        required_tables = ['campaigns', 'ad_groups', 'keywords', 'app_settings']
        missing_tables = [t for t in required_tables if t not in table_names]
        
        if missing_tables:
            print(f"⚠️  Отсутствуют таблицы: {', '.join(missing_tables)}")
            return False
        else:
            print(f"✅ Все таблицы существуют: {', '.join(table_names)}")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка проверки таблиц: {e}")
        return False

def create_all_tables():
    """Создание всех таблиц через прямой SQL"""
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = connection.cursor()
        
        print("📋 Создаю таблицы...")
        
        # Удаляем старые таблицы если нужно пересоздать (опционально)
        # cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        # cursor.execute("DROP TABLE IF EXISTS keywords")
        # cursor.execute("DROP TABLE IF EXISTS ad_groups")
        # cursor.execute("DROP TABLE IF EXISTS campaigns")
        # cursor.execute("DROP TABLE IF EXISTS app_settings")
        # cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # Создаём таблицы
        sql_commands = [
            # Таблица campaigns
            """
            CREATE TABLE IF NOT EXISTS campaigns (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                status ENUM('Enabled', 'Paused', 'Removed') DEFAULT 'Enabled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            # Таблица ad_groups
            """
            CREATE TABLE IF NOT EXISTS ad_groups (
                id INT AUTO_INCREMENT PRIMARY KEY,
                campaign_id INT NOT NULL,
                name VARCHAR(255) NOT NULL,
                status ENUM('Enabled', 'Paused', 'Removed') DEFAULT 'Enabled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            # Таблица keywords - со всеми полями
            """
            CREATE TABLE IF NOT EXISTS keywords (
                id INT AUTO_INCREMENT PRIMARY KEY,
                campaign_id INT NOT NULL,
                ad_group_id INT NOT NULL,
                keyword VARCHAR(500) NOT NULL,
                criterion_type ENUM('Phrase', 'Broad', 'Exact') DEFAULT 'Phrase',
                max_cpc DECIMAL(10, 2),
                max_cpm DECIMAL(10, 2),
                max_cpv DECIMAL(10, 2),
                first_page_bid DECIMAL(10, 2),
                top_of_page_bid DECIMAL(10, 2),
                first_position_bid DECIMAL(10, 2),
                quality_score INT,
                landing_page_experience VARCHAR(50),
                expected_ctr VARCHAR(50),
                ad_relevance VARCHAR(50),
                final_url TEXT,
                final_mobile_url TEXT,
                tracking_template TEXT,
                final_url_suffix VARCHAR(255),
                custom_parameters TEXT,
                status ENUM('Enabled', 'Paused', 'Removed') DEFAULT 'Enabled',
                approval_status VARCHAR(50),
                comment TEXT,
                has_ads BOOLEAN DEFAULT FALSE,
                has_school_sites BOOLEAN DEFAULT FALSE,
                has_google_maps BOOLEAN DEFAULT FALSE,
                has_our_site BOOLEAN DEFAULT FALSE,
                intent_type VARCHAR(50),
                recommendation TEXT,
                avg_monthly_searches INT,
                three_month_change DECIMAL(10, 2),
                yearly_change DECIMAL(10, 2),
                competition VARCHAR(50),
                competition_percent DECIMAL(5, 2),
                min_top_of_page_bid DECIMAL(10, 2),
                max_top_of_page_bid DECIMAL(10, 2),
                ad_impression_share DECIMAL(5, 2),
                organic_average_position DECIMAL(5, 2),
                organic_impression_share DECIMAL(5, 2),
                labels TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
                FOREIGN KEY (ad_group_id) REFERENCES ad_groups(id) ON DELETE CASCADE,
                INDEX idx_keyword (keyword),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            # Таблица app_settings
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                setting_key VARCHAR(100) UNIQUE NOT NULL,
                setting_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        ]
        
        # Выполняем каждую команду
        for i, sql in enumerate(sql_commands, 1):
            try:
                cursor.execute(sql)
                connection.commit()
                print(f"  ✅ Таблица {i}/4 создана")
            except Exception as e:
                print(f"  ❌ Ошибка создания таблицы {i}: {e}")
        
        # Проверяем что создалось
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        print(f"✅ Созданы таблицы: {', '.join(table_names)}")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False

def insert_test_data():
    """Вставка тестовых данных"""
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = connection.cursor()
        
        # Проверяем есть ли уже данные
        cursor.execute("SELECT COUNT(*) FROM campaigns")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("📝 Добавляю тестовые данные...")
            
            # Вставляем тестовую кампанию
            cursor.execute("INSERT INTO campaigns (name) VALUES ('montessori.ua')")
            campaign_id = cursor.lastrowid
            connection.commit()
            
            # Вставляем группы объявлений
            ad_groups = [
                '001 Уроки фортепиано (RU)',
                '002 Уроки вокала (RU)',
                '003 Уроки классической гитары (RU)',
                '004 Уроки электрогитары (RU)',
                '005 Уроки бас-гитары (RU)',
                '006 Уроки барабанов (RU)',
                '007 Уроки скрипки (RU)',
                '008 Уроки виолончели (RU)',
                '009 Уроки саксофона (RU)',
                '010 Уроки флейты (RU)'
            ]
            
            for ad_group_name in ad_groups:
                cursor.execute("INSERT INTO ad_groups (campaign_id, name) VALUES (%s, %s)", 
                              (campaign_id, ad_group_name))
            
            connection.commit()
            print(f"✅ Добавлено: 1 кампания, {len(ad_groups)} групп объявлений")
            
            # Добавим несколько тестовых ключевых слов
            test_keywords = [
                ('уроки саксофона киев', 9, 'Phrase', 4.01, 'Коммерческий', 320),
                ('обучение саксофону', 9, 'Phrase', 3.61, 'Информационный', 1200),
                ('школа саксофона', 9, 'Phrase', 3.61, 'Коммерческий', 480)
            ]
            
            for keyword, ad_group_id, criterion_type, max_cpc, intent_type, searches in test_keywords:
                cursor.execute("""
                    INSERT INTO keywords (campaign_id, ad_group_id, keyword, criterion_type, max_cpc, intent_type, avg_monthly_searches)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (campaign_id, ad_group_id, keyword, criterion_type, max_cpc, intent_type, searches))
            
            connection.commit()
            print(f"✅ Добавлено {len(test_keywords)} тестовых ключевых слов")
            
        else:
            print(f"ℹ️ Данные уже существуют: {count} кампаний")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка вставки тестовых данных: {e}")
        print(f"   Детали: {str(e)}")
        return False

def show_statistics():
    """Показ статистики БД"""
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = connection.cursor()
        
        stats = {}
        tables = ['campaigns', 'ad_groups', 'keywords', 'app_settings']
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[table] = count
            except:
                stats[table] = 'не создана'
        
        print("\n📊 Статистика БД:")
        print(f"   Кампаний: {stats['campaigns']}")
        print(f"   Групп объявлений: {stats['ad_groups']}")
        print(f"   Ключевых слов: {stats['keywords']}")
        print(f"   Настроек: {stats['app_settings']}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"\n❌ Не удалось получить статистику: {e}")

def main():
    print("=" * 50)
    print("🚀 Инициализация БД для Keyword Lock")
    print("=" * 50)
    
    # 1. Проверяем/создаём БД
    if not check_database_exists():
        print("\n❌ Не удалось подключиться к MySQL")
        print("Проверьте настройки в .env файле")
        return False
    
    # 2. Проверяем таблицы
    if not check_tables_exist():
        # Если таблиц нет или не все - создаём
        print("\n📋 Создаю недостающие таблицы...")
        if not create_all_tables():
            print("\n❌ Не удалось создать таблицы")
            return False
    
    # 3. Добавляем тестовые данные
    insert_test_data()
    
    # 4. Показываем статистику
    show_statistics()
    
    print("\n" + "=" * 50)
    print("✅ Инициализация завершена!")
    print("Теперь можно запускать: python3 app.py")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)