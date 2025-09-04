-- database/schema.sql
-- Схема БД для Keyword Lock

-- Используем БД
USE sql8_keylock;

-- Удаляем таблицы если существуют (в правильном порядке из-за foreign keys)
DROP TABLE IF EXISTS keywords;
DROP TABLE IF EXISTS ad_groups;
DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS app_settings;

-- Таблица кампаний
CREATE TABLE campaigns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status ENUM('Enabled', 'Paused', 'Removed') DEFAULT 'Enabled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица групп объявлений
CREATE TABLE ad_groups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    campaign_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    status ENUM('Enabled', 'Paused', 'Removed') DEFAULT 'Enabled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Основная таблица ключевых слов
CREATE TABLE keywords (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица настроек приложения
CREATE TABLE app_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Вставляем тестовые данные
INSERT INTO campaigns (name) VALUES ('montessori.ua');

-- Получаем ID кампании
SET @campaign_id = LAST_INSERT_ID();

-- Вставляем группы объявлений
INSERT INTO ad_groups (campaign_id, name) VALUES 
    (@campaign_id, '001 Уроки фортепиано (RU)'),
    (@campaign_id, '002 Уроки вокала (RU)'),
    (@campaign_id, '003 Уроки классической гитары (RU)'),
    (@campaign_id, '004 Уроки электрогитары (RU)'),
    (@campaign_id, '005 Уроки бас-гитары (RU)'),
    (@campaign_id, '006 Уроки барабанов (RU)'),
    (@campaign_id, '007 Уроки скрипки (RU)'),
    (@campaign_id, '008 Уроки виолончели (RU)'),
    (@campaign_id, '009 Уроки саксофона (RU)'),
    (@campaign_id, '010 Уроки флейты (RU)');

-- Проверяем что создалось
SELECT 'Tables created:' as Message;
SHOW TABLES;

SELECT 'Data inserted:' as Message;
SELECT COUNT(*) as campaigns_count FROM campaigns;
SELECT COUNT(*) as ad_groups_count FROM ad_groups;