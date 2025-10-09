# backend/utils/serp_competitors_helper.py
"""
Вспомогательные функции для работы с конкурентами в SERP-анализе
"""

def save_serp_competitors(connection, serp_analysis_id: int, organic_results: list, paid_results: list, maps_results: list, campaign_id: int):
    """
    Сохранение конкурентов из SERP-анализа в БД
    """
    cursor = connection.cursor()
    
    try:
        # Получаем домен нашего сайта
        our_domain = get_campaign_domain(campaign_id, connection)
        if our_domain:
            our_domain = our_domain.lower()
            print(f"   📌 Наш домен: {our_domain}")
        
        # Собираем все домены из результатов
        all_domains = []
        
        # Органические результаты
        for item in organic_results:
            domain = item.get('domain', '').lower().strip()
            if domain and domain != our_domain:
                all_domains.append({
                    'domain': domain,
                    'position': item.get('organic_position'),
                    'url': item.get('url', ''),
                    'title': item.get('title', ''),
                    'result_type': 'organic'
                })
        
        # Рекламные результаты
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
            
            # ✅ ИЗМЕНЕНО: Проверяем существование домена и добавляем с флагом is_new
            cursor.execute("SELECT id, is_new FROM competitor_schools WHERE domain = %s", (domain,))
            existing = cursor.fetchone()
            
            if not existing:
                # Новый домен - добавляем с is_new=TRUE
                cursor.execute("""
                    INSERT INTO competitor_schools (domain, org_type, is_new, created_at)
                    VALUES (%s, 'Школа', TRUE, NOW())
                """, (domain,))
                competitor_id = cursor.lastrowid
                print(f"   ✅ Добавлен НОВЫЙ конкурент: {domain} (id={competitor_id})")
            else:
                competitor_id = existing['id']
            
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