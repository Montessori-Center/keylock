#!/bin/bash

echo "🚀 Настройка проекта Keyword Lock"
echo "================================="

# Переход в директорию backend
cd backend

# 1. Генерация ключа шифрования
echo "📝 Генерация ключа шифрования..."
python3 -c "from cryptography.fernet import Fernet; key = Fernet.generate_key(); print(f'ENCRYPTION_KEY={key.decode()}')" > encryption_key.txt
echo "Ключ сохранен в encryption_key.txt"

# 2. Проверка Docker MySQL
echo ""
echo "🐳 Проверка MySQL в Docker..."
docker ps | grep mysql
echo ""
echo "Если вы видите контейнер MySQL выше, используйте эту информацию для .env"

# 3. Создание .env если не существует
if [ ! -f .env ]; then
    echo ""
    echo "📋 Создание .env файла..."
    cat > .env << EOL
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=True

# Database
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=keyword_lock
DB_USER=root
DB_PASSWORD=

# Encryption - вставьте ключ из encryption_key.txt
ENCRYPTION_KEY=

# CORS
CORS_ORIGINS=http://localhost:3000
EOL
    echo ".env файл создан. Отредактируйте его и добавьте:"
    echo "1. Пароль от MySQL (DB_PASSWORD)"
    echo "2. Ключ шифрования из encryption_key.txt (ENCRYPTION_KEY)"
else
    echo ".env файл уже существует"
fi

# 4. Проверка структуры файлов
echo ""
echo "📂 Создание структуры директорий..."
mkdir -p api models services utils

# 5. Создание __init__.py файлов
touch api/__init__.py
touch models/__init__.py  
touch services/__init__.py
touch utils/__init__.py

echo ""
echo "✅ Базовая настройка завершена!"
echo ""
echo "Следующие шаги:"
echo "1. Отредактируйте .env файл"
echo "2. Создайте БД в MySQL:"
echo "   docker exec -it ИМЯ_КОНТЕЙНЕРА mysql -u root -p"
echo "   Затем выполните: CREATE DATABASE keyword_lock CHARACTER SET utf8mb4;"
echo "3. Запустите: python3 app.py"