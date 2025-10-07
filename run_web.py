#!/usr/bin/env python3
"""
Запуск веб-приложения T1EUP
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import app
from database import migrate_ties_from_json

def main():
    """Основная функция запуска"""
    print("🎩 Запуск T1EUP Web Application...")
    
    # Миграция данных из JSON в базу данных
    print("📦 Миграция данных...")
    migrate_ties_from_json()
    
    # Получение настроек из переменных окружения
    host = os.getenv('WEB_HOST', '0.0.0.0')
    port = int(os.getenv('WEB_PORT', 5000))
    debug = os.getenv('WEB_DEBUG', 'True').lower() == 'true'
    
    print(f"🌐 Веб-приложение доступно по адресу: http://{host}:{port}")
    print(f"🔧 Режим отладки: {'включен' if debug else 'выключен'}")
    print("📱 Telegram бот: @t1eup_bot")
    print("=" * 50)
    
    # Запуск приложения
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )

if __name__ == '__main__':
    main()
