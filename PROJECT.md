# 🎩 T1EUP - Проект интернет-магазина галстуков

## 📋 Обзор проекта

T1EUP - это современный интернет-магазин галстуков, который сочетает в себе красивый веб-сайт и интеллектуального Telegram бота для максимального удобства покупателей.

## 🎯 Цели проекта

### Основные цели
- Создать удобный интернет-магазин для продажи галстуков
- Интегрировать Telegram бота для расширения функциональности
- Обеспечить простоту управления каталогом для администраторов
- Предоставить многоязычную поддержку

### Долгосрочные цели
- Масштабирование на другие товары
- Создание мобильного приложения
- Интеграция с CRM системами
- Расширение на международные рынки

## 🏗️ Архитектура проекта

### Компоненты
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web App       │    │  Telegram Bot   │    │   Database      │
│   (Flask)       │◄──►│   (Python)      │◄──►│   (SQLite)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Admin Panel   │    │   File Storage  │
│   (HTML/CSS/JS) │    │   (Flask)       │    │   (Local)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Технологический стек
- **Backend**: Python, Flask, SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Bot**: Telegram Bot API
- **Deployment**: Heroku, Railway, Render, VPS

## 📁 Структура проекта

```
t1eup-web/
├── web_app.py              # Основное Flask приложение
├── database.py             # Модели базы данных
├── run_web.py              # Запуск веб-приложения
├── wsgi.py                 # WSGI для продакшена
├── requirements.txt        # Python зависимости
├── Procfile               # Heroku конфигурация
├── templates/             # HTML шаблоны
│   ├── base.html
│   ├── index.html
│   ├── tie_detail.html
│   ├── order_form.html
│   ├── order_success.html
│   ├── profile.html
│   └── admin/
│       ├── catalog.html
│       ├── add_tie.html
│       ├── edit_tie.html
│       └── login.html
├── static/                # Статические файлы
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── images/
│       └── kaspi-qr.png
├── TieUp/                 # Изображения товаров
├── fonts/                 # Шрифты
├── deploy_scripts/        # Скрипты деплоя
│   ├── quick_deploy.sh
│   ├── railway_deploy.sh
│   ├── vps_deploy.sh
│   ├── render_deploy.md
│   ├── DEPLOY_QUICK.md
│   └── GITHUB_SETUP.md
└── docs/                  # Документация
    ├── README.md
    ├── SETUP.md
    ├── FAQ.md
    ├── ABOUT.md
    ├── CONTRIBUTING.md
    ├── CODE_OF_CONDUCT.md
    ├── SECURITY.md
    ├── CHANGELOG.md
    ├── RELEASES.md
    └── PROJECT.md
```

## 🔧 Установка и настройка

### Требования
- Python 3.8+
- pip
- Git

### Быстрая установка
```bash
# Клонирование репозитория
git clone https://github.com/YOUR_USERNAME/t1eup-web.git
cd t1eup-web

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp env.example .env
# Отредактируйте .env файл

# Инициализация базы данных
python3 -c "from database import init_db, migrate_ties_from_json; init_db(); migrate_ties_from_json()"

# Запуск приложения
python3 run_web.py
```

## 🚀 Деплой

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

## 🧪 Тестирование

### Запуск тестов
```bash
python3 test_web.py
```

### Тестирование функций
- [ ] Каталог товаров
- [ ] Система заказов
- [ ] Админ-панель
- [ ] Telegram бот
- [ ] Многоязычность

## 📊 Мониторинг

### Логи
- **Heroku**: `heroku logs --tail`
- **Railway**: `railway logs`
- **VPS**: `journalctl -u t1eup_web -f`

### Метрики
- Количество заказов
- Популярные товары
- Активность пользователей
- Производительность

## 🔒 Безопасность

### Меры безопасности
- Аутентификация через Telegram ID
- Защищенные админ-маршруты
- Валидация пользовательского ввода
- Безопасное хранение переменных окружения

### Рекомендации
- Регулярно обновляйте зависимости
- Используйте HTTPS в продакшене
- Создавайте бэкапы базы данных
- Мониторьте логи на подозрительную активность

## 🤝 Участие в проекте

### Для разработчиков
1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

### Для пользователей
1. Сообщайте об ошибках
2. Предлагайте новые функции
3. Делитесь обратной связью

### Для администраторов
1. Тестируйте новые версии
2. Предоставляйте обратную связь
3. Помогайте с документацией

## 📈 Планы развития

### Краткосрочные (3 месяца)
- [ ] Docker контейнеризация
- [ ] Система отзывов
- [ ] Программа лояльности
- [ ] Мобильное приложение

### Долгосрочные (1 год)
- [ ] ИИ рекомендации
- [ ] Виртуальная примерка
- [ ] Интеграция с CRM
- [ ] Международная экспансия

## 📞 Поддержка

### Контакты
- **Email**: [info@t1eup.com]
- **Telegram**: [@t1eup_bot]
- **GitHub**: [github.com/YOUR_USERNAME/t1eup-web]

### Ресурсы
- **Документация**: [docs/](docs/)
- **FAQ**: [FAQ.md](FAQ.md)
- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/t1eup-web/issues)

---

**T1EUP - современный интернет-магазин галстуков!** 🎩✨
