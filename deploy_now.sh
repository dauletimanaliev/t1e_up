#!/bin/bash

echo "🚀 Быстрый деплой T1EUP на Railway"

# Проверяем, установлен ли Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI не установлен. Устанавливаем..."
    npm install -g @railway/cli
fi

echo "🔐 Входим в Railway..."
echo "Откройте браузер и войдите в Railway"
railway login

echo "📱 Инициализируем проект Railway..."
railway init

echo "🚀 Деплоим приложение..."
railway up

echo "⚙️ Настраиваем переменные окружения..."
echo "Добавьте следующие переменные в Railway Dashboard:"
echo "ADMIN_IDS=1350637421,7148662346"
echo "ADMIN_PASSWORD=admin123"
echo "SECRET_KEY=$(openssl rand -base64 32)"

echo "📝 Добавьте ваши настройки:"
echo "BOT_TOKEN=your_bot_token_here"
echo "ADMIN_ID=your_admin_chat_id_here"

echo "🌐 Открываем приложение..."
railway open

echo "✅ Деплой завершен!"
echo "🔧 Для управления: railway logs"
