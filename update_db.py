"""
Миграция: добавление ad_group_id в serp_logs
"""
import pymysql
import pymysql.cursors
from backend.config import Config

def get_db_connection():
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        raise

def main():
    print("=" * 70)
    print("🔧 Миграция: добавление ad_group_id в serp_logs")
    print("=" * 70)
    
    connection = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        print("\n✅ Подключение к БД успешно")
        
        # Проверяем наличие колонки
        cursor.execute("""
            SELECT COUNT(*) as cnt 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = 'serp_logs'
            AND COLUMN_NAME = 'ad_group_id'
        """, (Config.DB_NAME,))
        
        result = cursor.fetchone()
        
        if result['cnt'] == 0:
            print("\n➕ Добавляем колонку ad_group_id...")
            cursor.execute("""
                ALTER TABLE serp_logs 
                ADD COLUMN ad_group_id INT DEFAULT NULL COMMENT 'ID группы объявлений' AFTER keyword_id,
                ADD INDEX idx_ad_group_id (ad_group_id)
            """)
            connection.commit()
            print("✅ Колонка добавлена")
            
            # Заполняем данные
            print("\n🔄 Заполняем ad_group_id для существующих записей...")
            cursor.execute("""
                UPDATE serp_logs sl
                INNER JOIN keywords k ON sl.keyword_id = k.id
                SET sl.ad_group_id = k.ad_group_id
                WHERE sl.ad_group_id IS NULL
            """)
            updated = cursor.rowcount
            connection.commit()
            print(f"✅ Обновлено записей: {updated}")
        else:
            print("\n✅ Колонка ad_group_id уже существует")
        
        # Статистика
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(ad_group_id) as with_ad_group,
                COUNT(*) - COUNT(ad_group_id) as without_ad_group
            FROM serp_logs
        """)
        stats = cursor.fetchone()
        
        print(f"\n📊 Статистика serp_logs:")
        print(f"   Всего записей: {stats['total']}")
        print(f"   С ad_group_id: {stats['with_ad_group']}")
        print(f"   Без ad_group_id: {stats['without_ad_group']}")
        
        print("\n" + "=" * 70)
        print("✅ Миграция завершена успешно!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        if connection:
            connection.rollback()
        import traceback
        traceback.print_exc()
    finally:
        if connection:
            cursor.close()
            connection.close()

if __name__ == "__main__":
    main()