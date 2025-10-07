# 🚀 Деплой T1EUP Web App

## 📋 Подготовка к деплою

### 1. Настройте переменные окружения

Создайте файл `.env` с вашими настройками:

```bash
# Telegram Bot настройки
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_admin_chat_id_here

# Админские Telegram ID (ваши реальные ID)
ADMIN_IDS=1350637421,7148662346

# Веб-приложение настройки
ADMIN_PASSWORD=admin123
SECRET_KEY=your_secret_key_here
WEBHOOK_URL=https://your-domain.com
```

### 2. Узнайте ваши Telegram ID

Напишите боту [@userinfobot](https://t.me/userinfobot) - он пришлет ваш ID.

## 🌐 Деплой на VPS (Ubuntu/Debian)

### Автоматический деплой

```bash
# Сделайте скрипт исполняемым
chmod +x deploy.sh

# Запустите деплой
./deploy.sh
```

### Ручной деплой

```bash
# 1. Обновите систему
sudo apt update && sudo apt upgrade -y

# 2. Установите зависимости
sudo apt install python3 python3-pip python3-venv nginx -y

# 3. Создайте директорию
sudo mkdir -p /var/www/t1eup
sudo chown $USER:$USER /var/www/t1eup

# 4. Скопируйте файлы
cp -r . /var/www/t1eup/
cd /var/www/t1eup

# 5. Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# 6. Установите зависимости
pip install -r requirements.txt

# 7. Запустите приложение
gunicorn --workers 3 --bind 0.0.0.0:8000 wsgi:app
```

## ☁️ Деплой на Heroku

### 1. Установите Heroku CLI

```bash
# Ubuntu/Debian
curl https://cli-assets.heroku.com/install.sh | sh

# macOS
brew install heroku/brew/heroku
```

### 2. Создайте приложение

```bash
# Войдите в Heroku
heroku login

# Создайте приложение
heroku create your-app-name

# Добавьте переменные окружения
heroku config:set BOT_TOKEN=your_bot_token
heroku config:set ADMIN_IDS=1350637421,7148662346
heroku config:set ADMIN_PASSWORD=admin123
heroku config:set SECRET_KEY=your_secret_key
```

### 3. Деплой

```bash
# Деплой на Heroku
git add .
git commit -m "Deploy T1EUP Web App"
git push heroku main
```

## 🔧 Управление сервисом

### VPS команды

```bash
# Статус сервиса
sudo systemctl status t1eup

# Перезапуск
sudo systemctl restart t1eup

# Остановка
sudo systemctl stop t1eup

# Логи
sudo journalctl -u t1eup -f
```

### Heroku команды

```bash
# Логи
heroku logs --tail

# Перезапуск
heroku restart

# Масштабирование
heroku ps:scale web=1
```

## 🔐 Настройка домена

### 1. Настройте DNS

Добавьте A-запись, указывающую на IP вашего VPS.

### 2. Обновите Nginx конфигурацию

```bash
sudo nano /etc/nginx/sites-available/t1eup
```

Замените `your-domain.com` на ваш реальный домен.

### 3. Перезапустите Nginx

```bash
sudo systemctl restart nginx
```

## 🔒 SSL сертификат (Let's Encrypt)

```bash
# Установите Certbot
sudo apt install certbot python3-certbot-nginx -y

# Получите сертификат
sudo certbot --nginx -d your-domain.com

# Автообновление
sudo crontab -e
# Добавьте: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📱 Настройка Telegram бота

### 1. Создайте бота

Напишите [@BotFather](https://t.me/botfather) и создайте нового бота.

### 2. Настройте Webhook

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-domain.com/webhook"}'
```

## 🎯 Проверка работы

1. Откройте ваш сайт в браузере
2. Нажмите "Войти" и авторизуйтесь через Telegram
3. Если ваш ID в `ADMIN_IDS` - попадете в админ-панель
4. Если нет - останетесь на главной странице

## 🆘 Решение проблем

### Приложение не запускается

```bash
# Проверьте логи
sudo journalctl -u t1eup -f

# Проверьте порт
sudo netstat -tlnp | grep :8000
```

### Nginx ошибки

```bash
# Проверьте конфигурацию
sudo nginx -t

# Перезапустите Nginx
sudo systemctl restart nginx
```

### Проблемы с Telegram

1. Проверьте правильность `BOT_TOKEN`
2. Убедитесь, что webhook настроен правильно
3. Проверьте логи бота

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи сервиса
2. Убедитесь, что все переменные окружения настроены
3. Проверьте, что порты открыты в файрволе
