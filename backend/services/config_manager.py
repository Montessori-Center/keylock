# backend/services/config_manager.py
import json
import os
from cryptography.fernet import Fernet
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.config_file = Path(__file__).parent.parent / 'config' / 'app_config.enc'
        self.key_file = Path(__file__).parent.parent / 'config' / 'app.key'
        self._ensure_key_exists()
    
    def _ensure_key_exists(self):
        """Создает ключ шифрования если его нет"""
        os.makedirs(self.key_file.parent, exist_ok=True)
        
        if not self.key_file.exists():
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            print(f"⚠️ Создан новый ключ шифрования: {self.key_file}")
    
    def _get_cipher(self):
        """Получает объект шифрования"""
        with open(self.key_file, 'rb') as f:
            key = f.read()
        return Fernet(key)
    
    def save_settings(self, settings):
        """Сохраняет настройки в зашифрованный файл"""
        try:
            cipher = self._get_cipher()
            encrypted_data = cipher.encrypt(json.dumps(settings).encode())
            
            os.makedirs(self.config_file.parent, exist_ok=True)
            with open(self.config_file, 'wb') as f:
                f.write(encrypted_data)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def load_settings(self):
        """Загружает настройки из зашифрованного файла"""
        try:
            if not self.config_file.exists():
                return {}
            
            cipher = self._get_cipher()
            with open(self.config_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            print(f"Error loading settings: {e}")
            return {}

# Глобальный экземпляр
config_manager = ConfigManager()