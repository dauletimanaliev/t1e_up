#!/usr/bin/env python3
"""
Запуск T1EUP Tie Shop - Веб-приложение + Telegram бот
"""

import os
import sys
import subprocess
import threading
import time
import signal
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class T1EUPRunner:
    def __init__(self):
        self.web_process = None
        self.bot_process = None
        self.running = True
        
    def check_requirements(self):
        """Проверка требований"""
        print("🔍 Проверка требований...")
        
        # Проверяем Python версию
        if sys.version_info < (3, 8):
            print("❌ Требуется Python 3.8 или выше")
            return False
        
        # Проверяем переменные окружения
        required_vars = ['BOT_TOKEN', 'ADMIN_ID']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
            print("💡 Создайте файл .env на основе env_web_example.txt")
            return False
        
        # Проверяем зависимости
        try:
            import flask
            import telegram
            import sqlalchemy
            print("✅ Все зависимости установлены")
        except ImportError as e:
            print(f"❌ Отсутствует зависимость: {e}")
            print("💡 Установите зависимости: pip install -r requirements.txt")
            return False
        
        return True
    
    def start_web_app(self):
        """Запуск веб-приложения"""
        print("🌐 Запуск веб-приложения...")
        try:
            self.web_process = subprocess.Popen([
                sys.executable, 'run_web.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("✅ Веб-приложение запущено на http://localhost:5000")
        except Exception as e:
            print(f"❌ Ошибка запуска веб-приложения: {e}")
    
    def start_bot(self):
        """Запуск Telegram бота"""
        print("🤖 Запуск Telegram бота...")
        try:
            self.bot_process = subprocess.Popen([
                sys.executable, 'bot_with_web.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("✅ Telegram бот запущен")
        except Exception as e:
            print(f"❌ Ошибка запуска бота: {e}")
    
    def stop_all(self):
        """Остановка всех процессов"""
        print("\n🛑 Остановка сервисов...")
        self.running = False
        
        if self.web_process:
            self.web_process.terminate()
            print("✅ Веб-приложение остановлено")
        
        if self.bot_process:
            self.bot_process.terminate()
            print("✅ Telegram бот остановлен")
    
    def monitor_processes(self):
        """Мониторинг процессов"""
        while self.running:
            time.sleep(5)
            
            # Проверяем веб-приложение
            if self.web_process and self.web_process.poll() is not None:
                print("❌ Веб-приложение остановлено неожиданно")
                self.running = False
                break
            
            # Проверяем бота
            if self.bot_process and self.bot_process.poll() is not None:
                print("❌ Telegram бот остановлен неожиданно")
                self.running = False
                break
    
    def run(self):
        """Основной запуск"""
        print("🎩 T1EUP Tie Shop - Запуск всех сервисов")
        print("=" * 50)
        
        # Проверяем требования
        if not self.check_requirements():
            return
        
        # Настройка обработчика сигналов
        def signal_handler(signum, frame):
            print("\n🛑 Получен сигнал остановки...")
            self.stop_all()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Запускаем веб-приложение
            self.start_web_app()
            time.sleep(3)  # Даем время на запуск
            
            # Запускаем бота
            self.start_bot()
            time.sleep(3)  # Даем время на запуск
            
            print("\n🚀 Все сервисы запущены!")
            print("=" * 50)
            print("🌐 Веб-приложение: http://localhost:5000")
            print("🤖 Telegram бот: @your_bot_username")
            print("📱 Для остановки нажмите Ctrl+C")
            print("=" * 50)
            
            # Мониторим процессы
            self.monitor_processes()
            
        except KeyboardInterrupt:
            print("\n🛑 Получен сигнал остановки...")
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")
        finally:
            self.stop_all()

def main():
    """Главная функция"""
    runner = T1EUPRunner()
    runner.run()

if __name__ == '__main__':
    main()
