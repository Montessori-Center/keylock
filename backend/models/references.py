# models/references.py
import mysql.connector

class ReferencesModel:
    def __init__(self, db_config):
        self.db_config = db_config
    
    def get_connection(self):
        return mysql.connector.connect(**self.db_config)
    
    def get_languages(self, display_only=True):
        """Получение списка языков"""
        connection = self.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT id, language_name, language_code FROM languages"
        if display_only:
            query += " WHERE display_flag = 'L'"
        query += " ORDER BY language_name"
        
        cursor.execute(query)
        languages = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return languages
    
    def get_locations(self, display_only=True, country_iso_code=None):
        """Получение списка локаций"""
        connection = self.get_connection()
        cursor = connection.cursor(dictionary=True)
        
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
    
    def get_language_by_code(self, language_code):
        """Получение языка по коду"""
        connection = self.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute(
            "SELECT * FROM languages WHERE language_code = %s",
            (language_code,)
        )
        language = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return language
    
    def get_location_by_code(self, location_code):
        """Получение локации по коду"""
        connection = self.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute(
            "SELECT * FROM locations WHERE location_code = %s",
            (location_code,)
        )
        location = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return location