#!/usr/bin/env python3
"""
Тестирование веб-приложения T1EUP
"""

import os
import sys
import requests
import time
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_web_app():
    """Тестирование веб-приложения"""
    print("🧪 Тестирование T1EUP Web Application...")
    
    base_url = "http://localhost:5000"
    
    # Список страниц для тестирования
    pages = [
        "/",
        "/tie/1",
        "/order/1"
    ]
    
    print(f"🌐 Тестируем URL: {base_url}")
    print("=" * 50)
    
    for page in pages:
        url = base_url + page
        try:
            print(f"📄 Тестируем: {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Статус: {response.status_code} - OK")
                print(f"📏 Размер: {len(response.content)} байт")
            else:
                print(f"❌ Статус: {response.status_code} - Ошибка")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Ошибка подключения - веб-приложение не запущено")
            print("💡 Запустите веб-приложение: python run_web.py")
            break
        except requests.exceptions.Timeout:
            print(f"⏰ Таймаут - страница загружается слишком долго")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        print("-" * 30)
        time.sleep(1)
    
    print("🏁 Тестирование завершено")

def test_database():
    """Тестирование базы данных"""
    print("\n🗄️ Тестирование базы данных...")
    
    try:
        from database import get_all_active_ties, migrate_ties_from_json
        
        # Миграция данных
        print("📦 Миграция данных...")
        migrate_ties_from_json()
        
        # Получение галстуков
        ties = get_all_active_ties()
        print(f"✅ Найдено галстуков: {len(ties)}")
        
        if ties:
            tie = ties[0]
            print(f"🎩 Пример галстука: {tie.name_ru}")
            print(f"💰 Цена: {tie.price} ₸")
            print(f"🖼️ Изображение: {tie.image_path or 'Нет'}")
        
    except Exception as e:
        print(f"❌ Ошибка базы данных: {e}")

def test_bot_integration():
    """Тестирование интеграции с ботом"""
    print("\n🤖 Тестирование интеграции с ботом...")
    
    try:
        from web_app import TieShopWebApp
        
        # Проверяем переменные окружения
        bot_token = os.getenv('BOT_TOKEN')
        admin_id = os.getenv('ADMIN_ID')
        
        if bot_token:
            print("✅ BOT_TOKEN настроен")
        else:
            print("❌ BOT_TOKEN не настроен")
            
        if admin_id:
            print("✅ ADMIN_ID настроен")
        else:
            print("❌ ADMIN_ID не настроен")
            
        print("🌐 Веб-приложение готово к интеграции с ботом")
        
    except Exception as e:
        print(f"❌ Ошибка интеграции: {e}")

def main():
    """Основная функция тестирования"""
    print("🎩 T1EUP Web Application - Тестирование")
    print("=" * 50)
    
    # Тестирование базы данных
    test_database()
    
    # Тестирование интеграции
    test_bot_integration()
    
    # Тестирование веб-приложения
    print("\n" + "=" * 50)
    test_web_app()
    
    print("\n📋 Инструкции по запуску:")
    print("1. Настройте .env файл с вашими данными")
    print("2. Запустите веб-приложение: python run_web.py")
    print("3. Откройте браузер: http://localhost:5000")
    print("4. Запустите бота: python bot_with_web.py")

if __name__ == '__main__':
    main()
