# backend/utils/serp_competitors_helper.py
"""
Вспомогательные функции для работы с конкурентами в SERP-анализе
"""

def save_serp_competitors(connection, serp_analysis_id, organic_results, paid_results, maps_results, campaign_id):
    """
    Сохранение конкурентов из SERP-анализа в БД
    
    Args:
        connection: подключение к БД
        serp_analysis_id: ID записи SERP-анализа
        organic_results: список органических результатов
        paid_results: список рекламных результатов
        maps_results: список результатов с карт
        campaign_id: ID кампании (для исключения нашего сайта)
    """
    cursor = connection.cursor()
    
    try:
        # Получаем домен нашего сайта, чтобы исключить его
        cursor.execute("""
            SELECT domain FROM campaign_sites WHERE campaign_id = %s
        """, (campaign_id,))
        our_site = cursor.fetchone()
        our_domain = our_site['domain'].lower() if our_site and our_site.get('domain') else None
        
        # Собираем все домены из всех типов результатов
        all_domains = []
        
        # Органика
        for item in organic_results:
            domain = item.get('domain', '').lower().strip()
            if domain and domain != our_domain:
                all_domains.append({
                    'domain': domain,
                    'position': item.get('position'),
                    'url': item.get('url', ''),
                    'title': item.get('title', ''),
                    'result_type': 'organic'
                })
        
        # Реклама
        for item in paid_results:
            domain = item.get('domain', '').lower().strip()
            if domain and domain != our_domain:
                all_domains.append({
                    'domain': domain,
                    'position': item.get('position'),
                    'url': item.get('url', ''),
                    'title': item.get('title', ''),
                    'result_type': 'paid'
                })
        
        # Карты
        for item in maps_results:
            domain = item.get('domain', '').lower().strip()
            if domain and domain != our_domain:
                all_domains.append({
                    'domain': domain,
                    'position': item.get('position'),
                    'url': item.get('url', ''),
                    'title': item.get('title', ''),
                    'result_type': 'maps'
                })
        
        print(f"   📊 Найдено уникальных доменов: {len(set([d['domain'] for d in all_domains]))}")
        
        # Для каждого домена
        for item in all_domains:
            domain = item['domain']
            
            # Проверяем/добавляем домен в competitor_schools
            cursor.execute("""
                INSERT IGNORE INTO competitor_schools (domain, org_type, created_at)
                VALUES (%s, 'Школа', NOW())
            """, (domain,))
            
            # Получаем ID конкурента
            cursor.execute("""
                SELECT id FROM competitor_schools WHERE domain = %s
            """, (domain,))
            competitor = cursor.fetchone()
            
            if competitor:
                competitor_id = competitor['id']
                
                # Добавляем запись о появлении
                cursor.execute("""
                    INSERT INTO serp_competitor_appearances 
                    (serp_analysis_id, competitor_id, position, result_type, url, title, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """, (
                    serp_analysis_id,
                    competitor_id,
                    item['position'],
                    item['result_type'],
                    item['url'],
                    item['title']
                ))
        
        # Обновляем конкурентность после добавления
        update_competitors_competitiveness(connection)
        
        connection.commit()
        print(f"   ✅ Конкуренты из SERP сохранены")
        
    except Exception as e:
        print(f"   ❌ Ошибка сохранения конкурентов: {e}")
        connection.rollback()
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()


def update_competitors_competitiveness(connection):
    """
    Обновление конкурентности для всех конкурентов
    Конкурентность = количество уникальных ключевых слов, 
    в последнем SERP-анализе которых встречается домен
    """
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            UPDATE competitor_schools c
            SET 
                competitiveness = (
                    SELECT COUNT(DISTINCT sa.keyword_id)
                    FROM serp_competitor_appearances sca
                    JOIN serp_analysis_history sa ON sca.serp_analysis_id = sa.id
                    WHERE sca.competitor_id = c.id
                    AND sa.id IN (
                        SELECT MAX(id) 
                        FROM serp_analysis_history 
                        GROUP BY keyword_id
                    )
                ),
                last_seen_at = (
                    SELECT MAX(sa.analysis_date)
                    FROM serp_competitor_appearances sca
                    JOIN serp_analysis_history sa ON sca.serp_analysis_id = sa.id
                    WHERE sca.competitor_id = c.id
                ),
                updated_at = NOW()
        """)
        connection.commit()
        
    except Exception as e:
        print(f"❌ Ошибка обновления конкурентности: {e}")
        connection.rollback()
    finally:
        cursor.close()


def get_competitor_details(connection, competitor_id):
    """
    Получение детальной информации о конкуренте:
    - В каких ключевых словах встречается
    - Средняя позиция
    - Тип результатов (органика/реклама/карты)
    """
    cursor = connection.cursor()
    
    try:
        # Получаем основную информацию
        cursor.execute("""
            SELECT * FROM competitor_schools WHERE id = %s
        """, (competitor_id,))
        competitor = cursor.fetchone()
        
        if not competitor:
            return None
        
        # Получаем ключевые слова, в которых встречается
        cursor.execute("""
            SELECT DISTINCT
                k.id,
                k.keyword,
                sca.position,
                sca.result_type,
                sa.analysis_date
            FROM serp_competitor_appearances sca
            JOIN serp_analysis_history sa ON sca.serp_analysis_id = sa.id
            JOIN keywords k ON sa.keyword_id = k.id
            WHERE sca.competitor_id = %s
            AND sa.id IN (
                SELECT MAX(id) 
                FROM serp_analysis_history 
                GROUP BY keyword_id
            )
            ORDER BY sca.position ASC
        """, (competitor_id,))
        
        keywords = cursor.fetchall()
        
        # Статистика по типам результатов
        cursor.execute("""
            SELECT 
                result_type,
                COUNT(*) as count,
                AVG(position) as avg_position
            FROM serp_competitor_appearances
            WHERE competitor_id = %s
            GROUP BY result_type
        """, (competitor_id,))
        
        result_types_stats = cursor.fetchall()
        
        return {
            'competitor': competitor,
            'keywords': keywords,
            'result_types': result_types_stats
        }
        
    except Exception as e:
        print(f"❌ Ошибка получения данных конкурента: {e}")
        return None
    finally:
        cursor.close()