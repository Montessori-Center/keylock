# backend/utils/serp_competitors_helper.py
"""
Вспомогательные функции для работы с конкурентами в SERP-анализе
"""

def get_campaign_domain(campaign_id: int, connection) -> str:
    """
    Получает домен сайта для кампании из таблицы campaign_sites
    """
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT domain 
            FROM campaign_sites 
            WHERE campaign_id = %s
        """, (campaign_id,))
        
        result = cursor.fetchone()
        cursor.close()
        
        if result and result['domain']:
            domain = result['domain'].lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        
        return None
        
    except Exception as e:
        print(f"❌ Error getting campaign domain: {e}")
        return None


def save_serp_competitors(connection, serp_analysis_id: int, organic_results: list, paid_results: list, maps_results: list, campaign_id: int):
    """
    Сохранение конкурентов из SERP-анализа в БД с установкой флага is_new
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
        
        unique_domains = list(set([d['domain'] for d in all_domains]))
        print(f"   📊 Найдено уникальных доменов: {len(unique_domains)}")
        
        # Обрабатываем каждый уникальный домен
        for domain in unique_domains:
            # Проверяем, существует ли домен
            cursor.execute("SELECT id, is_new FROM competitor_schools WHERE domain = %s", (domain,))
            existing = cursor.fetchone()
            
            if not existing:
                # ✅ НОВЫЙ ДОМЕН - добавляем с is_new=TRUE
                try:
                    cursor.execute("""
                        INSERT INTO competitor_schools (domain, org_type, is_new, created_at, updated_at)
                        VALUES (%s, 'Школа', TRUE, NOW(), NOW())
                    """, (domain,))
                    competitor_id = cursor.lastrowid
                    print(f"      ✅ НОВЫЙ конкурент добавлен: {domain} (id={competitor_id}, is_new=TRUE)")
                except Exception as insert_error:
                    print(f"      ⚠️ Ошибка добавления {domain}: {insert_error}")
                    # Если ошибка уникальности - пытаемся получить существующий
                    cursor.execute("SELECT id FROM competitor_schools WHERE domain = %s", (domain,))
                    existing = cursor.fetchone()
                    if existing:
                        competitor_id = existing['id']
                    else:
                        continue
            else:
                competitor_id = existing['id']
                is_new_flag = existing.get('is_new', False)
                print(f"      ℹ️ Существующий конкурент: {domain} (id={competitor_id}, is_new={is_new_flag})")
            
            # Добавляем записи о всех появлениях этого домена
            domain_items = [d for d in all_domains if d['domain'] == domain]
            for item in domain_items:
                try:
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
                except Exception as appearance_error:
                    print(f"      ⚠️ Ошибка добавления appearance для {domain}: {appearance_error}")
        
        # Обновляем конкурентность после добавления
        update_competitors_competitiveness(connection)
        
        print(f"   ✅ Конкуренты из SERP сохранены, коммит...")
        
    except Exception as e:
        print(f"   ❌ Ошибка сохранения конкурентов: {e}")
        import traceback
        traceback.print_exc()
        raise  # Пробрасываем ошибку дальше
    finally:
        cursor.close()


def update_competitors_competitiveness(connection):
    """
    Обновление конкурентности для всех конкурентов
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
        updated = cursor.rowcount
        print(f"   📊 Обновлена конкурентность для {updated} записей")
        
    except Exception as e:
        print(f"❌ Ошибка обновления конкурентности: {e}")
        raise
    finally:
        cursor.close()