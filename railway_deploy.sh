#!/bin/bash

echo "🚀 Быстрый деплой T1EUP Web App на Railway"

# Проверяем, установлен ли Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI не установлен. Устанавливаем..."
    
    # Установка Railway CLI
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install railway
    else
        # Установка для Linux
        curl -fsSL https://railway.app/install.sh | sh
    fi
fi

# Входим в Railway
echo "🔐 Входим в Railway..."
railway login

# Инициализируем проект
echo "📱 Инициализируем проект Railway..."
railway init

# Деплой
echo "🚀 Деплоим приложение..."
railway up

# Настраиваем переменные окружения
echo "⚙️ Настраиваем переменные окружения..."
railway variables set ADMIN_IDS=1350637421,7148662346
railway variables set ADMIN_PASSWORD=admin123
railway variables set SECRET_KEY=$(openssl rand -base64 32)

echo "📝 Добавьте ваши настройки:"
echo "railway variables set BOT_TOKEN=your_bot_token_here"
echo "railway variables set ADMIN_ID=your_admin_chat_id_here"

# Открываем приложение
echo "🌐 Открываем приложение..."
railway open

echo "✅ Деплой завершен!"
echo "🔧 Для управления: railway logs"
