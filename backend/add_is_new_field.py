import pymysql
from config import Config

def check_and_add_is_new_field():
    """Проверяет и добавляет поле is_new в таблицу keywords если его нет"""
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = connection.cursor()
        
        # Проверяем есть ли поле is_new
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'keywords' 
            AND COLUMN_NAME = 'is_new'
        """, (Config.DB_NAME,))
        
        result = cursor.fetchone()
        
        if not result:
            print("🔧 Поле is_new не найдено, добавляю...")
            
            # Добавляем поле is_new
            cursor.execute("""
                ALTER TABLE keywords 
                ADD COLUMN is_new BOOLEAN DEFAULT FALSE 
                COMMENT 'Флаг для подсветки новых записей'
            """)
            connection.commit()
            print("✅ Поле is_new успешно добавлено")
            
            # Проверяем что поле добавилось
            cursor.execute("DESCRIBE keywords")
            columns = cursor.fetchall()
            is_new_found = any('is_new' in str(col) for col in columns)
            
            if is_new_found:
                print("✅ Поле is_new подтверждено в структуре таблицы")
            else:
                print("❌ Поле is_new не найдено после добавления")
        else:
            print("✅ Поле is_new уже существует")
        
        # Показываем структуру таблицы
        cursor.execute("DESCRIBE keywords")
        columns = cursor.fetchall()
        print("\n📋 Текущая структура таблицы keywords:")
        for col in columns:
            print(f"  - {col}")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка работы с БД: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Проверка поля is_new в таблице keywords...")
    success = check_and_add_is_new_field()
    
    if success:
        print("\n✅ Проверка завершена успешно!")
    else:
        print("\n❌ Проверка завершена с ошибками!")