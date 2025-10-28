# backend/models/references.py
import pymysql.cursors
from config import Config


class ReferencesModel:
    """Модель для работы с языками и локациями"""
    
    @staticmethod
    def get_connection():
        """Создание подключения к БД"""
        return pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
    
    @staticmethod
    def get_languages(display_only=True):
        """Получение списка языков"""
        connection = ReferencesModel.get_connection()
        cursor = connection.cursor()
        
        query = "SELECT id, language_name, language_code FROM languages"
        if display_only:
            query += " WHERE display_flag = 'L'"
        query += " ORDER BY language_name"
        
        cursor.execute(query)
        languages = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return languages
    
    @staticmethod
    def get_locations(display_only=True, country_iso_code=None):
        """Получение списка локаций"""
        connection = ReferencesModel.get_connection()
        cursor = connection.cursor()
        
        query = """
            SELECT id, location_code, location_name, 
                   location_code_parent, country_iso_code, location_type 
            FROM locations
        """
        conditions = []
        params = []
        
        if display_only:
            conditions.append("display_flag = 'L'")
        
        if country_iso_code:
            conditions.append("country_iso_code = %s")
            params.append(country_iso_code)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY location_name"
        
        cursor.execute(query, params)
        locations = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return locations
    
    @staticmethod
    def get_language_by_code(language_code):
        """Получение языка по коду"""
        connection = ReferencesModel.get_connection()
        cursor = connection.cursor()
        
        cursor.execute(
            "SELECT * FROM languages WHERE language_code = %s",
            (language_code,)
        )
        language = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return language
    
    @staticmethod
    def get_location_by_code(location_code):
        """Получение локации по коду"""
        connection = ReferencesModel.get_connection()
        cursor = connection.cursor()
        
        cursor.execute(
            "SELECT * FROM locations WHERE location_code = %s",
            (location_code,)
        )
        location = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return location