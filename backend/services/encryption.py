# services/encryption.py - исправленная версия
from cryptography.fernet import Fernet
from config import Config
import json
import base64

class EncryptionService:
    def __init__(self):
        key = Config.ENCRYPTION_KEY
        
        # Если ключ не установлен или это дефолтный ключ
        if not key or key == 'generate-strong-key-for-production':
            # Генерируем новый ключ для разработки
            key = Fernet.generate_key()
            print(f"⚠️  ВНИМАНИЕ: Используется временный ключ шифрования!")
            print(f"Для production добавьте в .env файл:")
            print(f"ENCRYPTION_KEY={key.decode()}")
            print("-" * 50)
        else:
            # Если ключ строка, кодируем в байты
            if isinstance(key, str):
                key = key.encode()
        
        self.cipher = Fernet(key)
    
    def encrypt(self, data):
        """Шифрование данных"""
        if isinstance(data, dict):
            data = json.dumps(data)
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data).decode()
    
    def decrypt(self, encrypted_data):
        """Расшифровка данных"""
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode()
        decrypted = self.cipher.decrypt(encrypted_data)
        try:
            # Пытаемся распарсить как JSON
            return json.loads(decrypted.decode())
        except:
            # Если не JSON, возвращаем как строку
            return decrypted.decode()
    
    @staticmethod
    def generate_key():
        """Генерация нового ключа шифрования"""
        return Fernet.generate_key().decode()

# Глобальный экземпляр
encryption_service = EncryptionService()
