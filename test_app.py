#!/usr/bin/env python3
"""
Test version of T1EUP Web Application
Simple version to debug issues
"""

from flask import Flask, jsonify, request
import os
import json
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Простая база данных
DB_FILE = 'test_db.json'

def load_db():
    """Загружает данные из JSON файла"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading DB: {e}")
    
    return {
        'users': {},
        'orders': {},
        'ties': [
            {
                'id': 1,
                'name_ru': 'Тестовый галстук',
                'price': 15000,
                'active': True
            }
        ]
    }

def save_db(data):
    """Сохраняет данные в JSON файл"""
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving DB: {e}")

# Простые маршруты для тестирования
@app.route('/')
def index():
    try:
        db = load_db()
        ties = [tie for tie in db['ties'] if tie.get('active', True)]
        return f"""
        <html>
        <head><title>T1EUP Test</title></head>
        <body>
            <h1>T1EUP - Тестовая версия</h1>
            <h2>Каталог галстуков</h2>
            <ul>
                {''.join([f'<li>{tie["name_ru"]} - {tie["price"]} ₸</li>' for tie in ties])}
            </ul>
            <p>Статус: Работает!</p>
            <p>Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Error in index: {e}")
        return f"Ошибка: {str(e)}", 500

@app.route('/test')
def test():
    return jsonify({
        'status': 'ok',
        'message': 'Тест прошел успешно',
        'time': datetime.now().isoformat(),
        'environment': {
            'python_version': os.sys.version,
            'working_directory': os.getcwd(),
            'files': os.listdir('.')
        }
    })

@app.route('/db')
def db_test():
    try:
        db = load_db()
        return jsonify({
            'status': 'ok',
            'db_loaded': True,
            'ties_count': len(db['ties']),
            'users_count': len(db['users']),
            'orders_count': len(db['orders'])
        })
    except Exception as e:
        logger.error(f"Error in db_test: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/env')
def env_test():
    return jsonify({
        'status': 'ok',
        'environment_variables': {
            'ADMIN_IDS': os.environ.get('ADMIN_IDS', 'not_set'),
            'ADMIN_PASSWORD': os.environ.get('ADMIN_PASSWORD', 'not_set'),
            'BOT_TOKEN': 'set' if os.environ.get('BOT_TOKEN') else 'not_set',
            'ADMIN_ID': 'set' if os.environ.get('ADMIN_ID') else 'not_set',
            'SECRET_KEY': 'set' if os.environ.get('SECRET_KEY') else 'not_set'
        }
    })

# Обработчик ошибок
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return f"Внутренняя ошибка сервера: {str(error)}", 500

@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"Not found error: {error}")
    return f"Страница не найдена: {str(error)}", 404

# Для совместимости с Render
application = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting test app on port {port}")
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
