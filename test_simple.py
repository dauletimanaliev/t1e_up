from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import json
from dotenv import load_dotenv
import logging
from datetime import datetime

load_dotenv()

app = Flask(__name__, 
            static_folder='static', 
            static_url_path='/static',
            template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'test-secret-key')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Простая база данных в JSON файле
DB_FILE = 'test_db.json'

def load_db():
    """Загружает данные из JSON файла"""
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading database: {e}")
    
    return {
        'users': {},
        'orders': {},
        'ties': [
            {
                'id': 1,
                'name_ru': 'Классический синий галстук',
                'price': 15000,
                'active': True,
                'image_path': 'tie1.jpg'
            },
            {
                'id': 2,
                'name_ru': 'Элегантный красный галстук',
                'price': 18000,
                'active': True,
                'image_path': 'tie2.jpg'
            }
        ]
    }

def save_db(data):
    """Сохраняет данные в JSON файл"""
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving database: {e}")
        raise

@app.route('/')
def index():
    try:
        logger.info("Loading index page")
        db = load_db()
        ties = [tie for tie in db['ties'] if tie.get('active', True)]
        logger.info(f"Found {len(ties)} active ties")
        return render_template('index.html', ties=ties)
    except Exception as e:
        logger.error(f"Error in index: {e}")
        return f"Ошибка загрузки главной страницы: {str(e)}", 500

@app.route('/login')
def login():
    """Простая страница входа"""
    return """
    <html>
    <head>
        <title>Вход в T1EUP</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; max-width: 400px; margin: 50px auto; padding: 20px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; }
            input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <h2>Вход в T1EUP</h2>
        
        <form method="post" action="/login">
            <div class="form-group">
                <label>Ваше имя:</label>
                <input type="text" name="name" required>
            </div>
            <div class="form-group">
                <label>Телефон:</label>
                <input type="tel" name="phone" required>
            </div>
            <button type="submit">Войти</button>
        </form>
    </body>
    </html>
    """

@app.route('/login', methods=['POST'])
def login_post():
    """Обработка простого входа"""
    try:
        name = request.form.get('name')
        phone = request.form.get('phone')
        
        if not name or not phone:
            return "Заполните все поля", 400
        
        # Создаем простого пользователя
        user_id = abs(hash(phone)) % 1000000
        user = {
            'id': user_id,
            'name': name,
            'phone': phone,
            'created_at': datetime.now().isoformat()
        }
        
        # Сохраняем пользователя
        db = load_db()
        db['users'][str(user_id)] = user
        save_db(db)
        
        # Устанавливаем cookie
        response = redirect(url_for('profile'))
        response.set_cookie('user_id', str(user_id), max_age=30*24*60*60)
        
        return response
    except Exception as e:
        logger.error(f"Error in login_post: {e}")
        return f"Ошибка входа: {str(e)}", 500

@app.route('/profile')
def profile():
    try:
        user_id = request.cookies.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        
        # Получаем информацию о пользователе
        db = load_db()
        user = db['users'].get(str(user_id), {})
        
        return f"""
        <html>
        <head>
            <title>Профиль - T1EUP</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .profile {{ background: #f8f9fa; padding: 20px; border-radius: 10px; }}
                .btn {{ padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
                .btn:hover {{ background: #0056b3; }}
            </style>
        </head>
        <body>
            <h2>Профиль пользователя</h2>
            <div class="profile">
                <p><strong>Имя:</strong> {user.get('name', 'Не указано')}</p>
                <p><strong>Телефон:</strong> {user.get('phone', 'Не указан')}</p>
                <p><strong>ID:</strong> {user.get('id', 'Не указан')}</p>
                <p><strong>Дата регистрации:</strong> {user.get('created_at', 'Не указана')}</p>
            </div>
            <br>
            <a href="/" class="btn">На главную</a>
            <a href="/logout" class="btn">Выйти</a>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Error in profile: {e}")
        return f"Ошибка загрузки профиля: {str(e)}", 500

@app.route('/logout')
def logout():
    """Выход из системы"""
    response = redirect(url_for('index'))
    response.set_cookie('user_id', '', expires=0)
    return response

@app.route('/admin')
def admin_catalog():
    """Простая админ-панель"""
    return """
    <html>
    <head>
        <title>Админ-панель - T1EUP</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .admin-panel { background: #f8f9fa; padding: 20px; border-radius: 10px; }
            .btn { padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 5px; }
            .btn:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <h2>Админ-панель T1EUP</h2>
        <div class="admin-panel">
            <p>Это упрощенная версия админ-панели.</p>
            <p>В полной версии здесь будет управление товарами.</p>
        </div>
        <br>
        <a href="/" class="btn">На главную</a>
    </body>
    </html>
    """

@app.route('/tie/<int:tie_id>')
def tie_detail(tie_id):
    """Детали галстука"""
    try:
        db = load_db()
        tie = next((t for t in db['ties'] if t['id'] == tie_id), None)
        if not tie:
            return "Галстук не найден", 404
        
        return f"""
        <html>
        <head>
            <title>{tie['name_ru']} - T1EUP</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .tie-detail {{ background: #f8f9fa; padding: 20px; border-radius: 10px; }}
                .btn {{ padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
                .btn:hover {{ background: #0056b3; }}
                .price {{ font-size: 24px; font-weight: bold; color: #28a745; }}
            </style>
        </head>
        <body>
            <h2>{tie['name_ru']}</h2>
            <div class="tie-detail">
                <p><strong>Название:</strong> {tie['name_ru']}</p>
                <p class="price"><strong>Цена:</strong> {tie['price']:,} ₸</p>
                <p><strong>Статус:</strong> {'Активен' if tie.get('active', True) else 'Неактивен'}</p>
            </div>
            <br>
            <a href="/" class="btn">Назад к каталогу</a>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Error in tie_detail: {e}")
        return f"Ошибка загрузки деталей: {str(e)}", 500

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return "Внутренняя ошибка сервера. Пожалуйста, попробуйте позже.", 500

@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"Not found error: {error}")
    return "Страница не найдена.", 404

application = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
