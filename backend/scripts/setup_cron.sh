#!/bin/bash
# backend/scripts/setup_cron.sh
# Скрипт для настройки cron задачи автоматической очистки корзины

PROJECT_DIR="/www/wwwroot/keylock.interschool.online/www/backend"
PYTHON_PATH="$PROJECT_DIR/venv/bin/python3"
SCRIPT_PATH="$PROJECT_DIR/scripts/cleanup_trash.py"
LOG_PATH="$PROJECT_DIR/logs/cleanup_trash.log"

echo "🔧 Setting up cron job for trash cleanup..."

# Создаём директорию для логов если не существует
mkdir -p "$PROJECT_DIR/logs"

# Создаём временный файл crontab
TEMP_CRON=$(mktemp)

# Получаем текущий crontab (если есть)
crontab -l > "$TEMP_CRON" 2>/dev/null || true

# Проверяем, не добавлена ли уже задача
if grep -q "cleanup_trash.py" "$TEMP_CRON"; then
    echo "⚠️  Cron job already exists, removing old entry..."
    grep -v "cleanup_trash.py" "$TEMP_CRON" > "${TEMP_CRON}.new"
    mv "${TEMP_CRON}.new" "$TEMP_CRON"
fi

# Добавляем новую задачу (каждый день в 3:00 ночи)
echo "" >> "$TEMP_CRON"
echo "# Keyword Lock: Auto cleanup trash (every day at 3:00 AM)" >> "$TEMP_CRON"
echo "0 3 * * * $PYTHON_PATH $SCRIPT_PATH >> $LOG_PATH 2>&1" >> "$TEMP_CRON"

# Устанавливаем новый crontab
crontab "$TEMP_CRON"

# Удаляем временный файл
rm "$TEMP_CRON"

echo "✅ Cron job successfully installed!"
echo ""
echo "📋 Current crontab:"
crontab -l | grep -A 1 "Keyword Lock"
echo ""
echo "📝 Logs will be saved to: $LOG_PATH"
echo "🕐 Task will run every day at 3:00 AM"
echo ""
echo "To test the script manually, run:"
echo "   $PYTHON_PATH $SCRIPT_PATH"