#!/bin/bash

echo "🚀 Быстрый деплой T1EUP Web App на VPS"

# Получаем IP адрес VPS
read -p "🌐 Введите IP адрес вашего VPS: " VPS_IP
read -p "👤 Введите имя пользователя VPS: " VPS_USER

echo "📦 Копируем файлы на VPS..."
scp -r . $VPS_USER@$VPS_IP:/home/$VPS_USER/t1eup_web/

echo "🔧 Настраиваем VPS..."
ssh $VPS_USER@$VPS_IP << 'EOF'
cd /home/$VPS_USER/t1eup_web

# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем Python и зависимости
sudo apt install python3 python3-pip python3-venv nginx -y

# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt

# Инициализируем базу данных
python3 -c "from database import init_db, migrate_ties_from_json; init_db(); migrate_ties_from_json()"

# Создаем systemd сервис
sudo tee /etc/systemd/system/t1eup_web.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=Gunicorn instance for T1EUP Web App
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/t1eup_web
Environment="PATH=/home/ubuntu/t1eup_web/venv/bin"
ExecStart=/home/ubuntu/t1eup_web/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Настраиваем Nginx
sudo tee /etc/nginx/sites-available/t1eup_web > /dev/null << 'NGINX_EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/ubuntu/t1eup_web/static/;
    }

    location /TieUp/ {
        alias /home/ubuntu/t1eup_web/TieUp/;
    }
}
NGINX_EOF

# Активируем конфигурацию
sudo ln -sf /etc/nginx/sites-available/t1eup_web /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Перезапускаем сервисы
sudo systemctl daemon-reload
sudo systemctl enable t1eup_web
sudo systemctl start t1eup_web
sudo systemctl restart nginx

echo "✅ Деплой завершен!"
echo "🌐 Ваш сайт: http://$VPS_IP"
echo "📝 Не забудьте настроить .env файл с вашими токенами!"
EOF

echo "🎉 Деплой завершен!"
echo "🌐 Ваш сайт: http://$VPS_IP"
echo "📝 Настройте .env файл на сервере с вашими токенами"
