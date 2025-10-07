#!/bin/bash

echo "🚀 Быстрый деплой T1EUP Web App на Heroku"

# Проверяем, установлен ли Heroku CLI
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI не установлен. Устанавливаем..."
    
    # Установка Heroku CLI для macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install heroku/brew/heroku
    else
        # Установка для Linux
        curl https://cli-assets.heroku.com/install.sh | sh
    fi
fi

# Входим в Heroku
echo "🔐 Входим в Heroku..."
heroku login

# Создаем приложение
echo "📱 Создаем приложение Heroku..."
APP_NAME="t1eup-web-$(date +%s)"
heroku create $APP_NAME

# Добавляем переменные окружения
echo "⚙️ Настраиваем переменные окружения..."
heroku config:set ADMIN_IDS=1350637421,7148662346
heroku config:set ADMIN_PASSWORD=admin123
heroku config:set SECRET_KEY=$(openssl rand -base64 32)

echo "📝 Добавьте ваши настройки:"
echo "heroku config:set BOT_TOKEN=your_bot_token_here"
echo "heroku config:set ADMIN_ID=your_admin_chat_id_here"

# Деплой
echo "🚀 Деплоим приложение..."
git push heroku main

# Открываем приложение
echo "🌐 Открываем приложение..."
heroku open

echo "✅ Деплой завершен!"
echo "🌐 Ваш сайт: https://$APP_NAME.herokuapp.com"
echo "🔧 Для управления: heroku logs --tail"
