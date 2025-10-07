# 🚀 Быстрый запуск T1EUP

## 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

## 2. Настройка
```bash
cp env_web_example.txt .env
```
Отредактируйте `.env` файл и укажите:
- `BOT_TOKEN` - токен вашего Telegram бота
- `ADMIN_ID` - ваш Telegram ID

## 3. Запуск

### Вариант 1: Все сразу
```bash
python start_all.py
```

### Вариант 2: По отдельности
```bash
# Терминал 1 - Веб-приложение
python run_web.py

# Терминал 2 - Telegram бот
python bot_with_web.py
```

## 4. Использование

- **Веб-каталог**: http://localhost:5000
- **Telegram бот**: @your_bot_username
- **Команда в боте**: `/web` - открыть веб-каталог

## 5. Тестирование
```bash
python test_web.py
```

---

**Готово!** 🎉 Теперь у вас есть веб-приложение с каталогом галстуков и интеграция с Telegram ботом для уведомлений о заказах.
