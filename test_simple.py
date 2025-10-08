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
        
        # Проверяем, является ли пользователь админом по номеру телефона
        is_admin = phone == '87718626629'
        
        user = {
            'id': user_id,
            'name': name,
            'phone': phone,
            'is_admin': is_admin,
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
    try:
        user_id = request.cookies.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        
        # Проверяем админские права
        db = load_db()
        user = db['users'].get(str(user_id), {})
        if not user.get('is_admin', False):
            return "Доступ запрещен. Только для администраторов.", 403
        
        # Получаем статистику
        orders = list(db['orders'].values())
        ties = db['ties']
        
        return f"""
        <html>
        <head>
            <title>Админ-панель - T1EUP</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 1000px; margin: 50px auto; padding: 20px; }}
                .admin-panel {{ background: #f8f9fa; padding: 20px; border-radius: 10px; }}
                .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
                .stat-box {{ background: white; padding: 15px; border-radius: 5px; flex: 1; }}
                .btn {{ padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 5px; }}
                .btn:hover {{ background: #0056b3; }}
                .order {{ background: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }}
            </style>
        </head>
        <body>
            <h2>Админ-панель T1EUP</h2>
            <p>Добро пожаловать, {user.get('name', 'Администратор')}!</p>
            
            <div class="stats">
                <div class="stat-box">
                    <h3>Товары</h3>
                    <p>Всего: {len(ties)}</p>
                    <p>Активных: {len([t for t in ties if t.get('active', True)])}</p>
                </div>
                <div class="stat-box">
                    <h3>Заказы</h3>
                    <p>Всего: {len(orders)}</p>
                    <p>Ожидают: {len([o for o in orders if o.get('status') == 'pending'])}</p>
                </div>
            </div>
            
            <h3>Последние заказы:</h3>
            {''.join([f'''
            <div class="order">
                <p><strong>Заказ #{order['id']}</strong> - {order['tie_name']}</p>
                <p>Получатель: {order['recipient_name']} {order['recipient_surname']}</p>
                <p>Телефон: {order['recipient_phone']}</p>
                <p>Цена: {order['price']:,} ₸</p>
                <p>Статус: {order['status']}</p>
            </div>
            ''' for order in orders[-5:]]) if orders else '<p>Заказов пока нет</p>'}
            
            <br>
            <a href="/" class="btn">На главную</a>
            <a href="/logout" class="btn" style="background: #dc3545;">Выйти</a>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Error in admin_catalog: {e}")
        return f"Ошибка загрузки админ-панели: {str(e)}", 500

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

@app.route('/TieUp/<path:filename>')
def tie_images(filename):
    """Служит изображения галстуков"""
    try:
        from flask import send_from_directory
        return send_from_directory('TieUp', filename)
    except Exception as e:
        logger.error(f"Error serving image {filename}: {e}")
        return "Изображение не найдено", 404

@app.route('/order/<int:tie_id>')
def create_order_page(tie_id):
    """Страница оформления заказа"""
    try:
        db = load_db()
        tie = next((t for t in db['ties'] if t['id'] == tie_id), None)
        if not tie:
            return "Галстук не найден", 404
        
        return f"""
        <html>
        <head>
            <title>Заказ {tie['name_ru']} - T1EUP</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .order-form {{ background: #f8f9fa; padding: 20px; border-radius: 10px; }}
                .form-group {{ margin-bottom: 15px; }}
                label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
                input, textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
                .btn {{ padding: 12px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; border: none; cursor: pointer; }}
                .btn:hover {{ background: #218838; }}
                .price {{ font-size: 24px; font-weight: bold; color: #28a745; }}
            </style>
        </head>
        <body>
            <h2>Оформление заказа</h2>
            <div class="order-form">
                <h3>{tie['name_ru']}</h3>
                <p class="price">Цена: {tie['price']:,} ₸</p>
                
                <form method="post" action="/order/{tie_id}">
                    <div class="form-group">
                        <label>Имя получателя:</label>
                        <input type="text" name="recipient_name" required>
                    </div>
                    <div class="form-group">
                        <label>Фамилия получателя:</label>
                        <input type="text" name="recipient_surname" required>
                    </div>
                    <div class="form-group">
                        <label>Телефон получателя:</label>
                        <input type="tel" name="recipient_phone" required>
                    </div>
                    <div class="form-group">
                        <label>Адрес доставки:</label>
                        <textarea name="delivery_address" rows="3" required></textarea>
                    </div>
                    <button type="submit" class="btn">Оформить заказ</button>
                </form>
            </div>
            <br>
            <a href="/" class="btn" style="background: #6c757d;">Назад к каталогу</a>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Error in create_order_page: {e}")
        return f"Ошибка загрузки формы заказа: {str(e)}", 500

@app.route('/order/<int:tie_id>', methods=['POST'])
def process_order(tie_id):
    """Обработка заказа"""
    try:
        db = load_db()
        tie = next((t for t in db['ties'] if t['id'] == tie_id), None)
        if not tie:
            return "Галстук не найден", 404
        
        # Получаем данные формы
        recipient_name = request.form.get('recipient_name')
        recipient_surname = request.form.get('recipient_surname')
        recipient_phone = request.form.get('recipient_phone')
        delivery_address = request.form.get('delivery_address')
        
        if not all([recipient_name, recipient_surname, recipient_phone, delivery_address]):
            return "Заполните все поля", 400
        
        # Создаем заказ
        order_id = len(db['orders']) + 1
        order = {
            'id': order_id,
            'tie_id': tie_id,
            'tie_name': tie['name_ru'],
            'price': tie['price'],
            'recipient_name': recipient_name,
            'recipient_surname': recipient_surname,
            'recipient_phone': recipient_phone,
            'delivery_address': delivery_address,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        db['orders'][str(order_id)] = order
        save_db(db)
        
        return f"""
        <html>
        <head>
            <title>Заказ оформлен - T1EUP</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .success {{ background: #d4edda; padding: 20px; border-radius: 10px; border: 1px solid #c3e6cb; }}
                .btn {{ padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
                .btn:hover {{ background: #0056b3; }}
            </style>
        </head>
        <body>
            <h2>Заказ успешно оформлен!</h2>
            <div class="success">
                <p><strong>Номер заказа:</strong> #{order_id}</p>
                <p><strong>Товар:</strong> {tie['name_ru']}</p>
                <p><strong>Цена:</strong> {tie['price']:,} ₸</p>
                <p><strong>Получатель:</strong> {recipient_name} {recipient_surname}</p>
                <p><strong>Телефон:</strong> {recipient_phone}</p>
                <p><strong>Адрес:</strong> {delivery_address}</p>
                <p><strong>Статус:</strong> Ожидает обработки</p>
            </div>
            <br>
            <a href="/" class="btn">На главную</a>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Error processing order: {e}")
        return f"Ошибка оформления заказа: {str(e)}", 500

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
