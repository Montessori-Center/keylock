#!/bin/bash

# setup_frontend.sh - Скрипт для создания структуры frontend

echo "📁 Создание структуры Frontend..."

# Создание директорий
mkdir -p public
mkdir -p src/components/Modals
mkdir -p src/services
mkdir -p src/styles

# Создание public/index.html
cat > public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Ключик, замочек - система управления ключевыми словами" />
    <title>Ключик, замочек</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
EOF

# Создание public/manifest.json
cat > public/manifest.json << 'EOF'
{
  "short_name": "KeyLock",
  "name": "Ключик, замочек",
  "icons": [
    {
      "src": "favicon.ico",
      "sizes": "64x64 32x32 24x24 16x16",
      "type": "image/x-icon"
    }
  ],
  "start_url": ".",
  "display": "standalone",
  "theme_color": "#000000",
  "background_color": "#ffffff"
}
EOF

# Создание public/robots.txt
cat > public/robots.txt << 'EOF'
User-agent: *
Disallow: /api/
Disallow: /admin/
EOF

# Создание пустого favicon.ico
touch public/favicon.ico

# Проверка наличия основных компонентов
if [ ! -f "src/index.js" ]; then
    echo "⚠️  Отсутствует src/index.js"
fi

if [ ! -f "src/App.jsx" ]; then
    echo "⚠️  Отсутствует src/App.jsx"
fi

echo "✅ Структура Frontend создана!"
echo ""
echo "Проверьте наличие файлов:"
echo "  - src/index.js"
echo "  - src/App.jsx"
echo "  - src/components/Header.jsx"
echo "  - src/components/Sidebar.jsx"
echo "  - src/components/KeywordsTable.jsx"
echo "  - src/services/api.js"
echo "  - src/styles/main.css"
echo ""
echo "После создания всех файлов запустите: npm start"