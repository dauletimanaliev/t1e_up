# 🚀 Простой деплой T1EUP

## 🎯 Варианты деплоя (выберите один):

### 1. 🌐 Railway (Рекомендуется - самый простой)

#### Шаг 1: Создайте аккаунт
1. Зайдите на [railway.app](https://railway.app)
2. Нажмите "Login" → "GitHub"
3. Авторизуйтесь через GitHub

#### Шаг 2: Создайте проект
1. Нажмите "New Project"
2. Выберите "Deploy from GitHub repo"
3. Найдите ваш репозиторий `t1e_up`
4. Нажмите "Deploy Now"

#### Шаг 3: Настройте переменные
В разделе "Variables" добавьте:
```
ADMIN_IDS=1350637421,7148662346
ADMIN_PASSWORD=admin123
SECRET_KEY=your_secret_key_here
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_admin_chat_id
```

#### Шаг 4: Готово!
Railway автоматически задеплоит ваш сайт. URL будет показан в Dashboard.

---

### 2. 🌐 Render.com (Простой веб-интерфейс)

#### Шаг 1: Создайте аккаунт
1. Зайдите на [render.com](https://render.com)
2. Нажмите "Get Started" → "GitHub"
3. Авторизуйтесь через GitHub

#### Шаг 2: Создайте Web Service
1. Нажмите "New +" → "Web Service"
2. Подключите ваш репозиторий `t1e_up`
3. Настройте:
   - **Name**: `t1eup-web`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:application`

#### Шаг 3: Настройте переменные
В разделе "Environment" добавьте:
```
ADMIN_IDS=1350637421,7148662346
ADMIN_PASSWORD=admin123
SECRET_KEY=your_secret_key_here
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_admin_chat_id
```

#### Шаг 4: Деплой
1. Нажмите "Create Web Service"
2. Дождитесь завершения деплоя
3. Ваш сайт будет доступен по адресу: `https://t1eup-web.onrender.com`

---

### 3. 🆓 Heroku (Бесплатно, но медленно)

#### Шаг 1: Создайте аккаунт
1. Зайдите на [heroku.com](https://heroku.com)
2. Создайте аккаунт

#### Шаг 2: Создайте приложение
1. Нажмите "New" → "Create new app"
2. Название: `t1eup-ties-shop`
3. Выберите регион
4. Нажмите "Create app"

#### Шаг 3: Подключите GitHub
1. В разделе "Deploy" выберите "GitHub"
2. Подключите ваш репозиторий `t1e_up`
3. Нажмите "Deploy Branch"

#### Шаг 4: Настройте переменные
В разделе "Settings" → "Config Vars" добавьте:
```
ADMIN_IDS=1350637421,7148662346
ADMIN_PASSWORD=admin123
SECRET_KEY=your_secret_key_here
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_admin_chat_id
```

#### Шаг 5: Готово!
Ваш сайт будет доступен по адресу: `https://t1eup-ties-shop.herokuapp.com`

---

## 🔧 Настройка переменных окружения

### Обязательные переменные:
```bash
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_admin_chat_id
```

### Уже настроенные:
```bash
ADMIN_IDS=1350637421,7148662346
ADMIN_PASSWORD=admin123
SECRET_KEY=auto_generated
```

## 🎉 Готово!

После деплоя ваш сайт T1EUP будет доступен 24/7 с:
- ✅ Каталогом галстуков
- ✅ Системой заказов
- ✅ Админ-панелью
- ✅ Уведомлениями в Telegram
- ✅ Профилем пользователя

## 📱 Тестирование

1. Откройте ваш сайт
2. Нажмите "Войти" через Telegram
3. Если ваш ID в списке админов - увидите кнопку "Админ"
4. Сделайте тестовый заказ

---

**Рекомендация: Используйте Railway - самый простой и быстрый деплой!** 🚀
