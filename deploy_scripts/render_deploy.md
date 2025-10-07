# 🚀 Быстрый деплой на Render.com

## 1. Подготовка
1. Зайдите на [render.com](https://render.com)
2. Зарегистрируйтесь через GitHub
3. Подключите ваш GitHub репозиторий

## 2. Создание Web Service
1. Нажмите "New +" → "Web Service"
2. Подключите ваш репозиторий
3. Настройте:
   - **Name**: `t1eup-web`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:application`

## 3. Переменные окружения
Добавьте в Environment Variables:
```
ADMIN_IDS=1350637421,7148662346
ADMIN_PASSWORD=admin123
SECRET_KEY=your_secret_key_here
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_admin_chat_id_here
```

## 4. Деплой
1. Нажмите "Create Web Service"
2. Дождитесь завершения деплоя
3. Ваш сайт будет доступен по адресу: `https://t1eup-web.onrender.com`

## 5. Обновления
- Просто пушите изменения в GitHub
- Render автоматически передеплоит приложение

## ✅ Готово!
Ваш сайт T1EUP будет доступен 24/7 на Render.com
