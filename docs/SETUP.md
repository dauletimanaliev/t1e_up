# ⚙️ Настройка T1EUP Web App

## 🔧 Требования

- Python 3.8+
- pip
- Git

## 📋 Пошаговая настройка

### 1. Клонирование репозитория
```bash
git clone https://github.com/YOUR_USERNAME/t1eup-web.git
cd t1eup-web
```

### 2. Создание виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения
```bash
cp env.example .env
```

Отредактируйте `.env` файл:
```bash
# Telegram Bot Configuration
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_ID=123456789

# Admin Configuration
ADMIN_IDS=1350637421,7148662346
ADMIN_PASSWORD=admin123

# Flask Configuration
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
```

### 5. Инициализация базы данных
```bash
python3 -c "from database import init_db, migrate_ties_from_json; init_db(); migrate_ties_from_json()"
```

### 6. Запуск приложения
```bash
python3 run_web.py
```

## 🌐 Деплой

### Heroku
```bash
./deploy_scripts/quick_deploy.sh
```

### Railway
```bash
./deploy_scripts/railway_deploy.sh
```

### Render.com
Следуйте инструкциям в `deploy_scripts/render_deploy.md`

### VPS
```bash
./deploy_scripts/vps_deploy.sh
```

## 🔍 Проверка работы

1. Откройте `http://localhost:5000`
2. Проверьте каталог товаров
3. Попробуйте оформить заказ
4. Проверьте админ-панель

## 🐛 Решение проблем

### Ошибка "Module not found"
```bash
pip install -r requirements.txt
```

### Ошибка базы данных
```bash
rm tie_shop.db
python3 -c "from database import init_db, migrate_ties_from_json; init_db(); migrate_ties_from_json()"
```

### Порт занят
```bash
WEB_PORT=8000 python3 run_web.py
```

## 📞 Поддержка

При возникновении проблем проверьте:
1. Правильность переменных окружения
2. Подключение к интернету
3. Логи приложения
