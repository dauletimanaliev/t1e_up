#!/bin/bash

# Скрипт для деплоя T1EUP Web App на VPS

echo "🚀 Начинаем деплой T1EUP Web App..."

# Обновляем систему
echo "📦 Обновляем систему..."
sudo apt update && sudo apt upgrade -y

# Устанавливаем Python и pip
echo "🐍 Устанавливаем Python..."
sudo apt install python3 python3-pip python3-venv nginx -y

# Создаем директорию для приложения
echo "📁 Создаем директорию приложения..."
sudo mkdir -p /var/www/t1eup
sudo chown $USER:$USER /var/www/t1eup

# Копируем файлы приложения
echo "📋 Копируем файлы приложения..."
cp -r . /var/www/t1eup/
cd /var/www/t1eup

# Создаем виртуальное окружение
echo "🔧 Создаем виртуальное окружение..."
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
echo "📦 Устанавливаем зависимости..."
pip install -r requirements.txt

# Создаем systemd сервис
echo "⚙️ Создаем systemd сервис..."
sudo tee /etc/systemd/system/t1eup.service > /dev/null <<EOF
[Unit]
Description=T1EUP Web Application
After=network.target

[Service]
User=$USER
WorkingDirectory=/var/www/t1eup
Environment=PATH=/var/www/t1eup/venv/bin
ExecStart=/var/www/t1eup/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Настраиваем Nginx
echo "🌐 Настраиваем Nginx..."
sudo tee /etc/nginx/sites-available/t1eup > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /var/www/t1eup/static;
    }
}
EOF

# Активируем сайт
sudo ln -sf /etc/nginx/sites-available/t1eup /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Перезапускаем сервисы
echo "🔄 Перезапускаем сервисы..."
sudo systemctl daemon-reload
sudo systemctl enable t1eup
sudo systemctl start t1eup
sudo systemctl restart nginx

echo "✅ Деплой завершен!"
echo "🌐 Ваш сайт доступен по адресу: http://your-domain.com"
echo "🔧 Для управления сервисом используйте:"
echo "   sudo systemctl status t1eup"
echo "   sudo systemctl restart t1eup"
echo "   sudo systemctl stop t1eup"
