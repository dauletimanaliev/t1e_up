#!/usr/bin/env python3
"""
Simple version of T1EUP Web Application without SQLAlchemy
For deployment compatibility
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
import os
import json
from datetime import datetime
import requests
from dotenv import load_dotenv
import logging

# Загружаем переменные окружения
load_dotenv()

app = Flask(__name__, 
            static_folder='static', 
            static_url_path='/static',
            template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Простая база данных в JSON файле
DB_FILE = 'simple_db.json'

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
                'name_kz': 'Классикалық көк галстук',
                'name_en': 'Classic Blue Tie',
                'color_ru': 'Синий',
                'color_kz': 'Көк',
                'color_en': 'Blue',
                'description_ru': 'Элегантный классический галстук из натурального материала',
                'description_kz': 'Табиғи материалдан жасалған сәнді классикалық галстук',
                'description_en': 'Elegant classic tie made from natural material',
                'price': 15000,
                'image_path': 'TieUp/088eb3ce-53ee-4b2e-9de8-9f0a832537e0.jpg',
                'active': True,
                'material_ru': '100% натуральный материал',
                'material_kz': '100% табиғи материал',
                'material_en': '100% natural material'
            },
            {
                'id': 2,
                'name_ru': 'Элегантный красный галстук',
                'name_kz': 'Сәнді қызыл галстук',
                'name_en': 'Elegant Red Tie',
                'color_ru': 'Красный',
                'color_kz': 'Қызыл',
                'color_en': 'Red',
                'description_ru': 'Стильный красный галстук для особых случаев',
                'description_kz': 'Арнайы оқиғаларға арналған стильді қызыл галстук',
                'description_en': 'Stylish red tie for special occasions',
                'price': 18000,
                'image_path': 'TieUp/49b0c5337f0a4cab049faca97a0938ae.webp',
                'active': True,
                'material_ru': '100% натуральный материал',
                'material_kz': '100% табиғи материал',
                'material_en': '100% natural material'
            },
            {
                'id': 3,
                'name_ru': 'Деловой серый галстук',
                'name_kz': 'Бизнес сұр галстук',
                'name_en': 'Business Gray Tie',
                'color_ru': 'Серый',
                'color_kz': 'Сұр',
                'color_en': 'Gray',
                'description_ru': 'Идеальный выбор для деловых встреч',
                'description_kz': 'Бизнес кездесулерге арналған тамаша таңдау',
                'description_en': 'Perfect choice for business meetings',
                'price': 16000,
                'image_path': 'TieUp/5474e6af70d8ed1516dc9896acc5451e.webp',
                'active': True,
                'material_ru': '100% натуральный материал',
                'material_kz': '100% табиғи материал',
                'material_en': '100% natural material'
            },
            {
                'id': 4,
                'name_ru': 'Стильный черный галстук',
                'name_kz': 'Стильді қара галстук',
                'name_en': 'Stylish Black Tie',
                'color_ru': 'Черный',
                'color_kz': 'Қара',
                'color_en': 'Black',
                'description_ru': 'Универсальный черный галстук для любого случая',
                'description_kz': 'Кез келген жағдайға арналған универсалды қара галстук',
                'description_en': 'Universal black tie for any occasion',
                'price': 17000,
                'image_path': 'TieUp/54f2053123a61212aed740fe11e6193d.webp',
                'active': True,
                'material_ru': '100% натуральный материал',
                'material_kz': '100% табиғи материал',
                'material_en': '100% natural material'
            },
            {
                'id': 5,
                'name_ru': 'Модный зеленый галстук',
                'name_kz': 'Сәнді жасыл галстук',
                'name_en': 'Fashionable Green Tie',
                'color_ru': 'Зеленый',
                'color_kz': 'Жасыл',
                'color_en': 'Green',
                'description_ru': 'Современный зеленый галстук с уникальным дизайном',
                'description_kz': 'Бірегей дизайны бар заманауи жасыл галстук',
                'description_en': 'Modern green tie with unique design',
                'price': 19000,
                'image_path': 'TieUp/a0a1a0a307f4c5c41cf5987d166141eb.webp',
                'active': True,
                'material_ru': '100% натуральный материал',
                'material_kz': '100% табиғи материал',
                'material_en': '100% natural material'
            },
            {
                'id': 6,
                'name_ru': 'Премиум коричневый галстук',
                'name_kz': 'Премиум қоңыр галстук',
                'name_en': 'Premium Brown Tie',
                'color_ru': 'Коричневый',
                'color_kz': 'Қоңыр',
                'color_en': 'Brown',
                'description_ru': 'Премиум качество коричневого галстука',
                'description_kz': 'Қоңыр галстуктің премиум сапасы',
                'description_en': 'Premium quality brown tie',
                'price': 22000,
                'image_path': 'TieUp/dff9ee5594129bda03a963b9c2d65612.webp',
                'active': True,
                'material_ru': '100% натуральный материал',
                'material_kz': '100% табиғи материал',
                'material_en': '100% natural material'
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

def get_all_active_ties():
    """Возвращает все активные галстуки"""
    try:
        db = load_db()
        ties = [tie for tie in db['ties'] if tie.get('active', True)]
        logger.info(f"Loaded {len(ties)} active ties from database")
        return ties
    except Exception as e:
        logger.error(f"Error loading active ties: {e}")
        return []

def create_order(tie_id, recipient_name, recipient_surname, recipient_phone, delivery_address, user_id):
    """Создает новый заказ"""
    db = load_db()
    ties = {tie['id']: tie for tie in db['ties']}
    
    if tie_id not in ties:
        return None
    
    tie = ties[tie_id]
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
        'user_id': user_id,
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    
    db['orders'][str(order_id)] = order
    save_db(db)
    return order

def get_or_create_user(user_id, username, first_name, last_name):
    """Получает или создает пользователя"""
    db = load_db()
    
    if str(user_id) not in db['users']:
        db['users'][str(user_id)] = {
            'id': user_id,
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'created_at': datetime.now().isoformat()
        }
        save_db(db)
    
    return db['users'][str(user_id)]

def get_user_orders(user_id):
    """Возвращает заказы пользователя"""
    try:
        db = load_db()
        return [order for order in db['orders'].values() if order.get('user_id') == user_id]
    except Exception as e:
        logger.error(f"Error loading user orders: {e}")
        return []

def send_admin_notification(order):
    """Отправляет уведомление админу (заглушка)"""
    print(f"🛍️ НОВЫЙ ЗАКАЗ #{order['id']}")
    print(f"👤 Покупатель: {order['recipient_name']} {order.get('recipient_surname', '')}")
    print(f"📞 Телефон: {order['recipient_phone']}")
    print(f"🎩 Товар: {order['tie_name']} - {order['price']:,.0f} ₸")
    print(f"📍 Адрес: {order['delivery_address']}")
    print(f"📅 Дата: {datetime.fromisoformat(order['created_at']).strftime('%d.%m.%Y в %H:%M')}")
    print("=" * 50)
    # Здесь можно добавить отправку email или другие уведомления
    return True

# Маршруты
@app.route('/')
def index():
    try:
        logger.info("Loading index page")
        ties = get_all_active_ties()
        logger.info(f"Found {len(ties)} active ties")
        return render_template('index.html', ties=ties)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return f"Ошибка загрузки главной страницы: {str(e)}", 500

@app.route('/tie/<int:tie_id>')
def tie_detail(tie_id):
    db = load_db()
    tie = next((t for t in db['ties'] if t['id'] == tie_id), None)
    if not tie:
        return "Галстук не найден", 404
    return render_template('tie_detail.html', tie=tie)

@app.route('/order/<int:tie_id>')
def order_form(tie_id):
    db = load_db()
    tie = next((t for t in db['ties'] if t['id'] == tie_id), None)
    if not tie:
        return "Галстук не найден", 404
    return render_template('order_form.html', tie=tie)

@app.route('/create-order/<int:tie_id>')
def create_order_page(tie_id):
    """Алиас для order_form для совместимости с шаблонами"""
    return order_form(tie_id)

@app.route('/order/<int:tie_id>', methods=['POST'])
def create_order_route(tie_id):
    user_id = request.cookies.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Пользователь не авторизован'})
    
    recipient_name = request.form.get('recipient_name')
    recipient_surname = request.form.get('recipient_surname')
    recipient_phone = request.form.get('recipient_phone')
    delivery_address = request.form.get('delivery_address')
    
    if not all([recipient_name, recipient_phone, delivery_address]):
        return jsonify({'success': False, 'error': 'Заполните все обязательные поля'})
    
    order = create_order(tie_id, recipient_name, recipient_surname, recipient_phone, delivery_address, int(user_id))
    
    if order:
        send_admin_notification(order)
        return redirect(url_for('order_success', order_id=order['id']))
    else:
        return jsonify({'success': False, 'error': 'Ошибка создания заказа'})

@app.route('/order/success/<int:order_id>')
def order_success(order_id):
    db = load_db()
    order = db['orders'].get(str(order_id))
    if not order:
        return "Заказ не найден", 404
    return render_template('order_success.html', order=order)

@app.route('/profile')
def profile():
    try:
        user_id = request.cookies.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        
        # Получаем информацию о пользователе
        db = load_db()
        user = db['users'].get(str(user_id), {})
        orders = get_user_orders(int(user_id))
        
        # Вычисляем общую сумму потраченных денег
        total_spent = sum(order.get('price', 0) for order in orders)
        
        return render_template('profile.html', orders=orders, user=user, total_spent=total_spent)
    except Exception as e:
        logger.error(f"Error in profile: {e}")
        return f"Ошибка загрузки профиля: {str(e)}", 500

@app.route('/login')
def login():
    """Красивая страница входа с валидацией"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Вход - T1EUP</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .login-container {{
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                padding: 40px;
                width: 100%;
                max-width: 400px;
                position: relative;
                overflow: hidden;
            }}
            .login-container::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #667eea, #764ba2);
            }}
            .logo {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo h1 {{
                color: #333;
                font-size: 2.5em;
                font-weight: 700;
                margin-bottom: 10px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            .logo p {{
                color: #666;
                font-size: 1.1em;
            }}
            .form-group {{ 
                margin-bottom: 25px; 
                position: relative;
            }}
            label {{ 
                display: block; 
                margin-bottom: 8px; 
                color: #333;
                font-weight: 600;
                font-size: 0.95em;
            }}
            input {{ 
                width: 100%; 
                padding: 15px 20px; 
                border: 2px solid #e1e5e9; 
                border-radius: 12px; 
                font-size: 16px;
                transition: all 0.3s ease;
                background: #f8f9fa;
            }}
            input:focus {{
                outline: none;
                border-color: #667eea;
                background: white;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }}
            .error {{
                color: #e74c3c;
                font-size: 0.85em;
                margin-top: 5px;
                display: none;
            }}
            .btn {{ 
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white; 
                padding: 15px 20px; 
                border: none; 
                border-radius: 12px; 
                cursor: pointer; 
                width: 100%; 
                font-size: 16px;
                font-weight: 600;
                transition: all 0.3s ease;
                margin-top: 10px;
            }}
            .btn:hover {{ 
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }}
            .btn:active {{
                transform: translateY(0);
            }}
            .features {{
                margin-top: 30px;
                text-align: center;
            }}
            .features h3 {{
                color: #333;
                margin-bottom: 15px;
                font-size: 1.1em;
            }}
            .feature-list {{
                list-style: none;
                color: #666;
                font-size: 0.9em;
                line-height: 1.6;
            }}
            .feature-list li {{
                margin-bottom: 5px;
            }}
            .feature-list li::before {{
                content: '✓';
                color: #27ae60;
                font-weight: bold;
                margin-right: 8px;
            }}
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="logo">
                <h1>T1EUP</h1>
                <p>Магазин элегантных галстуков</p>
            </div>
            
            <form method="post" action="/login" id="loginForm">
                <div class="form-group">
                    <label for="name">Ваше имя</label>
                    <input type="text" name="name" id="name" required minlength="2" maxlength="50">
                    <div class="error" id="nameError">Имя должно содержать от 2 до 50 символов</div>
                </div>
                <div class="form-group">
                    <label for="phone">Номер телефона</label>
                    <input type="tel" name="phone" id="phone" required pattern="[0-9]{{10,15}}" placeholder="87771234567">
                    <div class="error" id="phoneError">Введите корректный номер телефона (10-15 цифр)</div>
                </div>
                
                <button type="submit" class="btn">Войти в магазин</button>
            </form>
            
            <div class="features">
                <h3>Почему выбирают нас?</h3>
                <ul class="feature-list">
                    <li>Эксклюзивные дизайны</li>
                    <li>Качественные материалы</li>
                    <li>Быстрая доставка</li>
                    <li>Гарантия качества</li>
                </ul>
            </div>
        </div>
        
        <script>
        document.getElementById('loginForm').addEventListener('submit', function(e) {{
            let isValid = true;
            
            // Валидация имени
            const name = document.getElementById('name').value.trim();
            const nameError = document.getElementById('nameError');
            if (name.length < 2 || name.length > 50) {{
                nameError.style.display = 'block';
                isValid = false;
            }} else {{
                nameError.style.display = 'none';
            }}
            
            // Валидация телефона
            const phone = document.getElementById('phone').value.replace(/\D/g, '');
            const phoneError = document.getElementById('phoneError');
            if (phone.length < 10 || phone.length > 15) {{
                phoneError.style.display = 'block';
                isValid = false;
            }} else {{
                phoneError.style.display = 'none';
            }}
            
            if (!isValid) {{
                e.preventDefault();
            }}
        }});
        
        // Автоформатирование телефона
        document.getElementById('phone').addEventListener('input', function(e) {{
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 0) {{
                if (value.startsWith('7')) {{
                    value = value.substring(1);
                }}
                if (value.length > 10) {{
                    value = value.substring(0, 10);
                }}
            }}
            e.target.value = value;
        }});
        </script>
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
        user_id = abs(hash(phone)) % 1000000  # Простой ID на основе телефона
        
        # Проверяем, является ли пользователь админом по номеру телефона
        is_admin = phone == '87718626629'
        
        logger.info(f"Login attempt - name: '{name}', phone: '{phone}', is_admin: {is_admin}")
        logger.info(f"Phone comparison: '{phone}' == '87718626629' = {phone == '87718626629'}")
        
        user = {
            'id': user_id,
            'name': name,
            'phone': phone,
            'is_admin': is_admin,
            'created_at': datetime.now().isoformat()
        }
        
        # Сохраняем пользователя
        db = load_db()
        
        # Если пользователь уже существует, обновляем его данные
        if str(user_id) in db['users']:
            existing_user = db['users'][str(user_id)]
            logger.info(f"Updating existing user: {existing_user}")
            # Обновляем номер телефона и админские права
            existing_user['phone'] = phone
            existing_user['is_admin'] = is_admin
            existing_user['name'] = name
            db['users'][str(user_id)] = existing_user
        else:
            db['users'][str(user_id)] = user
            
        save_db(db)
        logger.info(f"Saved user: {db['users'][str(user_id)]}")
        
        # Устанавливаем cookie
        response = redirect(url_for('profile'))
        response.set_cookie('user_id', str(user_id), max_age=30*24*60*60)  # 30 дней
        
        return response
    except Exception as e:
        logger.error(f"Error in login_post: {e}")
        return f"Ошибка входа: {str(e)}", 500

@app.route('/logout')
def logout():
    """Выход из системы"""
    response = redirect(url_for('index'))
    response.set_cookie('user_id', '', expires=0)
    return response

@app.route('/admin/force-login')
def admin_force_login():
    """Принудительный вход как админ для отладки"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    db = load_db()
    user = db['users'].get(str(user_id), {})
    
    # Принудительно делаем пользователя админом
    user['phone'] = '87718626629'
    user['is_admin'] = True
    db['users'][str(user_id)] = user
    save_db(db)
    
    logger.info(f"Force admin login for user {user_id}: {user}")
    
    return f"""
    <html>
    <head>
        <title>Принудительный вход как админ - T1EUP</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
            .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 10px; border: 1px solid #c3e6cb; }}
            .btn {{ padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h2>Принудительный вход как админ</h2>
        <div class="success">
            <p>Вы принудительно вошли как администратор!</p>
            <p>Ваш номер: {user['phone']}</p>
            <p>Статус: Администратор ✅</p>
        </div>
        <br>
        <a href="/admin" class="btn">Перейти в админ-панель</a>
    </body>
    </html>
    """


@app.route('/check-user-status', methods=['POST'])
def check_user_status():
    """Проверка статуса пользователя"""
    data = request.get_json()
    user_id = data.get('id')
    
    if not user_id:
        return jsonify({'success': False, 'error': 'ID пользователя не предоставлен'})
    
    # Проверяем, является ли пользователь админом по номеру телефона
    db = load_db()
    user = db['users'].get(str(user_id), {})
    is_admin = user.get('is_admin', False)
    
    return jsonify({
        'success': True,
        'is_admin': is_admin
    })

@app.route('/TieUp/<path:filename>')
def tie_images(filename):
    return send_from_directory('TieUp', filename)

# Админские маршруты
@app.route('/admin')
def admin_catalog():
    """Админ-панель - каталог товаров"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    db = load_db()
    
    # Проверяем, является ли пользователь админом
    user = db['users'].get(str(user_id), {})
    user_phone = user.get('phone', '')
    
    # Простая проверка админа по номеру телефона
    logger.info(f"Checking admin access for user_id: {user_id}, phone: '{user_phone}', expected: '87718626629'")
    logger.info(f"Phone comparison: '{user_phone}' == '87718626629' = {user_phone == '87718626629'}")
    
    if user_phone != '87718626629':
        return f"""
        <html>
        <head>
            <title>Доступ запрещен - T1EUP</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
                .error {{ background: #f8d7da; color: #721c24; padding: 20px; border-radius: 10px; border: 1px solid #f5c6cb; }}
                .debug {{ background: #e2e3e5; color: #383d41; padding: 15px; border-radius: 5px; margin: 10px 0; font-family: monospace; }}
                .btn {{ padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h2>Доступ запрещен</h2>
            <div class="error">
                <p>Только для администраторов!</p>
                <p>Ваш номер: '{user_phone}'</p>
                <p>Админский номер: '87718626629'</p>
                <p>Длина вашего номера: {len(user_phone)}</p>
                <p>Длина админского номера: {len('87718626629')}</p>
            </div>
            <div class="debug">
                <p><strong>Отладочная информация:</strong></p>
                <p>User ID: {user_id}</p>
                <p>User object: {user}</p>
                <p>Phone type: {type(user_phone)}</p>
                <p>Phone repr: {repr(user_phone)}</p>
            </div>
            <br>
            <a href="/" class="btn">На главную</a>
            <a href="/admin/force-login" class="btn" style="background: #28a745;">Принудительный вход как админ</a>
        </body>
        </html>
        """, 403
    ties = db['ties']
    orders = list(db['orders'].values())
    
    # Вычисляем статистику
    total_ties = len(ties)
    active_ties = len([t for t in ties if t.get('active', True)])
    avg_price = sum(t.get('price', 0) for t in ties) / total_ties if total_ties > 0 else 0
    
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
            .success {{ background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <h2>Админ-панель T1EUP</h2>
        <div class="success">
            <p><strong>Добро пожаловать, {user.get('name', 'Администратор')}!</strong></p>
            <p>Ваш номер: {user_phone}</p>
            <p>Статус: Администратор ✅</p>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <h3>Товары</h3>
                <p>Всего: {total_ties}</p>
                <p>Активных: {active_ties}</p>
                <p>Средняя цена: {avg_price:,.0f} ₸</p>
            </div>
            <div class="stat-box">
                <h3>Заказы</h3>
                <p>Всего: {len(orders)}</p>
                <p>Ожидают: {len([o for o in orders if o.get('status') == 'pending'])}</p>
            </div>
        </div>
        
        <h3>Управление товарами:</h3>
        <div style="margin-bottom: 20px;">
            <a href="/admin/tie/add" class="btn" style="background: #28a745;">+ Добавить новый галстук</a>
        </div>
        
        <div class="ties-list">
            {''.join([f'''
            <div class="order" style="border-left-color: {'#28a745' if tie.get('active', True) else '#dc3545'};">
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div style="flex-shrink: 0;">
                        <img src="/TieUp/{tie['image_path']}" 
                             style="width: 80px; height: 80px; object-fit: cover; border-radius: 8px; border: 2px solid #ddd;"
                             alt="{tie['name_ru']}"
                             onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAiIGhlaWdodD0iODAiIHZpZXdCb3g9IjAgMCA4MCA4MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjgwIiBoZWlnaHQ9IjgwIiBmaWxsPSIjRjVGNUY1Ii8+CjxwYXRoIGQ9Ik0yMCAyMEg2MFY2MEgyMFYyMFoiIHN0cm9rZT0iI0NDQyIgc3Ryb2tlLXdpZHRoPSIyIi8+CjxwYXRoIGQ9Ik0zMCAzMEg1MFY1MEgzMFYzMFoiIGZpbGw9IiNEREQiLz4KPC9zdmc+'; this.alt='Изображение не найдено';">
                    </div>
                    <div style="flex-grow: 1;">
                        <h5>{tie['name_ru']}</h5>
                        <p><strong>Цена:</strong> {tie['price']:,} ₸</p>
                        <p><strong>Статус:</strong> {'Активен' if tie.get('active', True) else 'Неактивен'}</p>
                        <p><strong>ID:</strong> {tie['id']}</p>
                        <p><strong>Изображение:</strong> {tie['image_path']}</p>
                    </div>
                    <div style="flex-shrink: 0; display: flex; flex-direction: column; gap: 5px;">
                        <a href="/admin/tie/{tie['id']}/edit" class="btn" style="background: #ffc107; color: black; margin: 2px; padding: 8px 12px; font-size: 12px;">Редактировать</a>
                        <a href="/admin/tie/{tie['id']}/toggle" class="btn" style="background: {'#dc3545' if tie.get('active', True) else '#28a745'}; margin: 2px; padding: 8px 12px; font-size: 12px;">
                            {'Деактивировать' if tie.get('active', True) else 'Активировать'}
                        </a>
                        <a href="/admin/tie/{tie['id']}/delete" class="btn" style="background: #dc3545; margin: 2px; padding: 8px 12px; font-size: 12px;" onclick="return confirm('Удалить галстук?')">Удалить</a>
                    </div>
                </div>
            </div>
            ''' for tie in ties]) if ties else '<p>Товаров пока нет</p>'}
        </div>
        
        <h3>Последние заказы:</h3>
        {''.join([f'''
        <div class="order">
            <p><strong>Заказ #{order['id']}</strong> - {order['tie_name']}</p>
            <p>Получатель: {order['recipient_name']} {order['recipient_surname']}</p>
            <p>Телефон: {order['recipient_phone']}</p>
            <p>Цена: {order['price']:,} ₸</p>
            <p>Статус: {order['status']}</p>
            <p>Дата: {order.get('created_at', 'Неизвестно')[:16]}</p>
        </div>
        ''' for order in orders[-5:]]) if orders else '<p>Заказов пока нет</p>'}
        
        <br>
        <a href="/" class="btn">На главную</a>
        <a href="/logout" class="btn" style="background: #dc3545;">Выйти</a>
    </body>
    </html>
    """

@app.route('/admin/tie/add')
def admin_add_tie():
    """Страница добавления нового галстука"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    db = load_db()
    user = db['users'].get(str(user_id), {})
    if user.get('phone', '') != '87718626629':
        return "Доступ запрещен", 403
    
    return """
    <html>
    <head>
        <title>Добавить галстук - T1EUP</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            .btn { padding: 12px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; border: none; cursor: pointer; margin: 5px; }
            .btn:hover { background: #0056b3; }
            .btn-success { background: #28a745; }
            .btn-success:hover { background: #218838; }
            .btn-secondary { background: #6c757d; }
            .btn-secondary:hover { background: #545b62; }
        </style>
    </head>
    <body>
        <h2>Добавить новый галстук</h2>
        
        <form method="post" action="/admin/tie/add" enctype="multipart/form-data">
            <div class="form-group">
                <label>Название:</label>
                <input type="text" name="name_ru" required>
            </div>
            <div class="form-group">
                <label>Цвет:</label>
                <input type="text" name="color_ru" required>
            </div>
            <div class="form-group">
                <label>Описание:</label>
                <textarea name="description_ru" rows="3" required></textarea>
            </div>
            <div class="form-group">
                <label>Материал:</label>
                <input type="text" name="material_ru" value="100% натуральный материал" required>
            </div>
            <div class="form-group">
                <label>Цена (₸):</label>
                <input type="number" name="price" min="0" required>
            </div>
            <div class="form-group">
                <label>Изображение:</label>
                <input type="file" name="image_file" accept="image/*" onchange="previewImage(this)" style="margin-bottom: 10px;">
                <div id="imagePreview" style="margin-top: 10px; display: none;">
                    <img id="previewImg" style="max-width: 200px; max-height: 200px; border-radius: 8px; border: 2px solid #ddd;">
                </div>
                <p style="font-size: 12px; color: #666; margin-top: 5px;">
                    Или выберите из существующих:
                </p>
                <select name="image_path" style="margin-top: 5px;">
                    <option value="">Выберите существующее изображение</option>
                    <option value="tie1.jpg">tie1.jpg</option>
                    <option value="tie2.jpg">tie2.jpg</option>
                    <option value="tie3.jpg">tie3.jpg</option>
                    <option value="tie4.jpg">tie4.jpg</option>
                    <option value="tie5.jpg">tie5.jpg</option>
                    <option value="tie6.jpg">tie6.jpg</option>
                </select>
            </div>
            <div class="form-group">
                <label>Статус:</label>
                <select name="active">
                    <option value="true">Активен</option>
                    <option value="false">Неактивен</option>
                </select>
            </div>
            
            <button type="submit" class="btn btn-success">Добавить галстук</button>
            <a href="/admin" class="btn btn-secondary">Отмена</a>
        </form>
        
        <script>
        function previewImage(input) {{
            if (input.files && input.files[0]) {{
                const reader = new FileReader();
                reader.onload = function(e) {{
                    const preview = document.getElementById('imagePreview');
                    const img = document.getElementById('previewImg');
                    img.src = e.target.result;
                    preview.style.display = 'block';
                }}
                reader.readAsDataURL(input.files[0]);
            }}
        }}
        </script>
    </body>
    </html>
    """

@app.route('/admin/tie/add', methods=['POST'])
def admin_add_tie_post():
    """Обработка добавления нового галстука"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    db = load_db()
    user = db['users'].get(str(user_id), {})
    if user.get('phone', '') != '87718626629':
        return "Доступ запрещен", 403
    
    try:
        # Получаем данные формы
        name_ru = request.form.get('name_ru')
        color_ru = request.form.get('color_ru')
        description_ru = request.form.get('description_ru')
        material_ru = request.form.get('material_ru')
        price = int(request.form.get('price', 0))
        active = request.form.get('active') == 'true'
        
        # Обрабатываем изображение
        image_path = request.form.get('image_path', '')
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename:
                # Генерируем уникальное имя файла
                import uuid
                filename = str(uuid.uuid4()) + '.jpg'
                file.save(f'TieUp/{filename}')
                image_path = filename
        
        # Создаем новый ID
        new_id = max([tie['id'] for tie in db['ties']], default=0) + 1
        
        # Создаем новый галстук
        new_tie = {
            'id': new_id,
            'name_ru': name_ru,
            'name_kz': name_ru,  # Дублируем русское название
            'name_en': name_ru,  # Дублируем русское название
            'color_ru': color_ru,
            'color_kz': color_ru,  # Дублируем русский цвет
            'color_en': color_ru,  # Дублируем русский цвет
            'description_ru': description_ru,
            'description_kz': description_ru,  # Дублируем русское описание
            'description_en': description_ru,  # Дублируем русское описание
            'material_ru': material_ru,
            'material_kz': material_ru,  # Дублируем русский материал
            'material_en': material_ru,  # Дублируем русский материал
            'price': price,
            'image_path': image_path,
            'active': active
        }
        
        # Добавляем в базу данных
        db['ties'].append(new_tie)
        save_db(db)
        
        return f"""
        <html>
        <head>
            <title>Галстук добавлен - T1EUP</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
                .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 10px; border: 1px solid #c3e6cb; }}
                .btn {{ padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h2>Галстук успешно добавлен!</h2>
            <div class="success">
                <p><strong>ID:</strong> {new_id}</p>
                <p><strong>Название:</strong> {name_ru}</p>
                <p><strong>Цена:</strong> {price:,} ₸</p>
                <p><strong>Статус:</strong> {'Активен' if active else 'Неактивен'}</p>
            </div>
            <br>
            <a href="/admin" class="btn">Вернуться в админ-панель</a>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Error adding tie: {e}")
        return f"Ошибка добавления галстука: {str(e)}", 500

@app.route('/admin/tie/<int:tie_id>/edit')
def admin_edit_tie(tie_id):
    """Страница редактирования галстука"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    db = load_db()
    user = db['users'].get(str(user_id), {})
    if user.get('phone', '') != '87718626629':
        return "Доступ запрещен", 403
    
    tie = next((t for t in db['ties'] if t['id'] == tie_id), None)
    if not tie:
        return "Галстук не найден", 404
    
    return f"""
    <html>
    <head>
        <title>Редактировать галстук - T1EUP</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            input, textarea, select {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
            .btn {{ padding: 12px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; border: none; cursor: pointer; margin: 5px; }}
            .btn:hover {{ background: #0056b3; }}
            .btn-success {{ background: #28a745; }}
            .btn-success:hover {{ background: #218838; }}
            .btn-secondary {{ background: #6c757d; }}
            .btn-secondary:hover {{ background: #545b62; }}
        </style>
    </head>
    <body>
        <h2>Редактировать галстук #{tie_id}</h2>
        
        <div style="margin-bottom: 20px; text-align: center;">
            <img src="/TieUp/{tie['image_path']}" 
                 style="width: 120px; height: 120px; object-fit: cover; border-radius: 8px; border: 2px solid #ddd;"
                 alt="{tie['name_ru']}"
                 onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIwIiBoZWlnaHQ9IjEyMCIgdmlld0JveD0iMCAwIDEyMCAxMjAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxMjAiIGhlaWdodD0iMTIwIiBmaWxsPSIjRjVGNUY1Ii8+CjxwYXRoIGQ9Ik0zMCAzMEg5MFY5MEgzMFYzMFoiIHN0cm9rZT0iI0NDQyIgc3Ryb2tlLXdpZHRoPSIyIi8+CjxwYXRoIGQ9Ik00NSA0NUg3NVY3NUg0NVY0NVoiIGZpbGw9IiNEREQiLz4KPC9zdmc+'; this.alt='Изображение не найдено';">
            <p style="margin-top: 10px; color: #666;">Текущее изображение</p>
        </div>
        
        <form method="post" action="/admin/tie/{tie_id}/edit" enctype="multipart/form-data">
            <div class="form-group">
                <label>Название:</label>
                <input type="text" name="name_ru" value="{tie['name_ru']}" required>
            </div>
            <div class="form-group">
                <label>Цвет:</label>
                <input type="text" name="color_ru" value="{tie['color_ru']}" required>
            </div>
            <div class="form-group">
                <label>Описание:</label>
                <textarea name="description_ru" rows="3" required>{tie['description_ru']}</textarea>
            </div>
            <div class="form-group">
                <label>Материал:</label>
                <input type="text" name="material_ru" value="{tie['material_ru']}" required>
            </div>
            <div class="form-group">
                <label>Цена (₸):</label>
                <input type="number" name="price" value="{tie['price']}" min="0" required>
            </div>
            <div class="form-group">
                <label>Изображение:</label>
                <input type="file" name="image_file" accept="image/*" onchange="previewImage(this)" style="margin-bottom: 10px;">
                <div id="imagePreview" style="margin-top: 10px; display: none;">
                    <img id="previewImg" style="max-width: 200px; max-height: 200px; border-radius: 8px; border: 2px solid #ddd;">
                </div>
                <p style="font-size: 12px; color: #666; margin-top: 5px;">
                    Или выберите из существующих:
                </p>
                <select name="image_path" style="margin-top: 5px;">
                    <option value="">Выберите существующее изображение</option>
                    <option value="tie1.jpg" {'selected' if tie.get('image_path') == 'tie1.jpg' else ''}>tie1.jpg</option>
                    <option value="tie2.jpg" {'selected' if tie.get('image_path') == 'tie2.jpg' else ''}>tie2.jpg</option>
                    <option value="tie3.jpg" {'selected' if tie.get('image_path') == 'tie3.jpg' else ''}>tie3.jpg</option>
                    <option value="tie4.jpg" {'selected' if tie.get('image_path') == 'tie4.jpg' else ''}>tie4.jpg</option>
                    <option value="tie5.jpg" {'selected' if tie.get('image_path') == 'tie5.jpg' else ''}>tie5.jpg</option>
                    <option value="tie6.jpg" {'selected' if tie.get('image_path') == 'tie6.jpg' else ''}>tie6.jpg</option>
                </select>
            </div>
            <div class="form-group">
                <label>Статус:</label>
                <select name="active">
                    <option value="true" {'selected' if tie.get('active', True) else ''}>Активен</option>
                    <option value="false" {'selected' if not tie.get('active', True) else ''}>Неактивен</option>
                </select>
            </div>
            
            <button type="submit" class="btn btn-success">Сохранить изменения</button>
            <a href="/admin" class="btn btn-secondary">Отмена</a>
        </form>
        
        <script>
        function previewImage(input) {{
            if (input.files && input.files[0]) {{
                const reader = new FileReader();
                reader.onload = function(e) {{
                    const preview = document.getElementById('imagePreview');
                    const img = document.getElementById('previewImg');
                    img.src = e.target.result;
                    preview.style.display = 'block';
                }}
                reader.readAsDataURL(input.files[0]);
            }}
        }}
        </script>
    </body>
    </html>
    """

@app.route('/admin/tie/<int:tie_id>/edit', methods=['POST'])
def admin_edit_tie_post(tie_id):
    """Обработка редактирования галстука"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    db = load_db()
    user = db['users'].get(str(user_id), {})
    if user.get('phone', '') != '87718626629':
        return "Доступ запрещен", 403
    
    try:
        tie = next((t for t in db['ties'] if t['id'] == tie_id), None)
        if not tie:
            return "Галстук не найден", 404
        
        # Обновляем данные
        name_ru = request.form.get('name_ru')
        color_ru = request.form.get('color_ru')
        description_ru = request.form.get('description_ru')
        material_ru = request.form.get('material_ru')
        
        tie['name_ru'] = name_ru
        tie['name_kz'] = name_ru  # Дублируем русское название
        tie['name_en'] = name_ru  # Дублируем русское название
        tie['color_ru'] = color_ru
        tie['color_kz'] = color_ru  # Дублируем русский цвет
        tie['color_en'] = color_ru  # Дублируем русский цвет
        tie['description_ru'] = description_ru
        tie['description_kz'] = description_ru  # Дублируем русское описание
        tie['description_en'] = description_ru  # Дублируем русское описание
        tie['material_ru'] = material_ru
        tie['material_kz'] = material_ru  # Дублируем русский материал
        tie['material_en'] = material_ru  # Дублируем русский материал
        tie['price'] = int(request.form.get('price', 0))
        tie['active'] = request.form.get('active') == 'true'
        
        # Обрабатываем изображение
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename:
                # Генерируем уникальное имя файла
                import uuid
                filename = str(uuid.uuid4()) + '.jpg'
                file.save(f'TieUp/{filename}')
                tie['image_path'] = filename
        else:
            # Используем выбранное из списка
            tie['image_path'] = request.form.get('image_path', tie.get('image_path', ''))
        
        save_db(db)
        
        return f"""
        <html>
        <head>
            <title>Галстук обновлен - T1EUP</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
                .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 10px; border: 1px solid #c3e6cb; }}
                .btn {{ padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h2>Галстук успешно обновлен!</h2>
            <div class="success">
                <p><strong>ID:</strong> {tie_id}</p>
                <p><strong>Название:</strong> {tie['name_ru']}</p>
                <p><strong>Цена:</strong> {tie['price']:,} ₸</p>
                <p><strong>Статус:</strong> {'Активен' if tie['active'] else 'Неактивен'}</p>
            </div>
            <br>
            <a href="/admin" class="btn">Вернуться в админ-панель</a>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Error editing tie: {e}")
        return f"Ошибка редактирования галстука: {str(e)}", 500

@app.route('/admin/tie/<int:tie_id>/toggle')
def admin_toggle_tie(tie_id):
    """Активация/деактивация галстука"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    db = load_db()
    user = db['users'].get(str(user_id), {})
    if user.get('phone', '') != '87718626629':
        return "Доступ запрещен", 403
    
    try:
        tie = next((t for t in db['ties'] if t['id'] == tie_id), None)
        if not tie:
            return "Галстук не найден", 404
        
        # Переключаем статус
        tie['active'] = not tie.get('active', True)
        save_db(db)
        
        status = "активирован" if tie['active'] else "деактивирован"
        return f"""
        <html>
        <head>
            <title>Галстук {status} - T1EUP</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
                .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 10px; border: 1px solid #c3e6cb; }}
                .btn {{ padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h2>Галстук {status}!</h2>
            <div class="success">
                <p><strong>ID:</strong> {tie_id}</p>
                <p><strong>Название:</strong> {tie['name_ru']}</p>
                <p><strong>Новый статус:</strong> {'Активен' if tie['active'] else 'Неактивен'}</p>
            </div>
            <br>
            <a href="/admin" class="btn">Вернуться в админ-панель</a>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Error toggling tie: {e}")
        return f"Ошибка изменения статуса: {str(e)}", 500

@app.route('/admin/tie/<int:tie_id>/delete')
def admin_delete_tie(tie_id):
    """Удаление галстука"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    db = load_db()
    user = db['users'].get(str(user_id), {})
    if user.get('phone', '') != '87718626629':
        return "Доступ запрещен", 403
    
    try:
        tie = next((t for t in db['ties'] if t['id'] == tie_id), None)
        if not tie:
            return "Галстук не найден", 404
        
        tie_name = tie['name_ru']
        
        # Удаляем галстук
        db['ties'] = [t for t in db['ties'] if t['id'] != tie_id]
        save_db(db)
        
        return f"""
        <html>
        <head>
            <title>Галстук удален - T1EUP</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
                .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 10px; border: 1px solid #c3e6cb; }}
                .btn {{ padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h2>Галстук удален!</h2>
            <div class="success">
                <p><strong>ID:</strong> {tie_id}</p>
                <p><strong>Название:</strong> {tie_name}</p>
                <p>Галстук был полностью удален из системы.</p>
            </div>
            <br>
            <a href="/admin" class="btn">Вернуться в админ-панель</a>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Error deleting tie: {e}")
        return f"Ошибка удаления галстука: {str(e)}", 500

@app.route('/admin/login')
def admin_login():
    """Страница входа в админ-панель"""
    return render_template('admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    """Обработка входа в админ-панель"""
    password = request.form.get('password')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    if password == admin_password:
        session['admin_authenticated'] = True
        return redirect(url_for('admin_catalog'))
    else:
        return render_template('admin/login.html', error='Неверный пароль')

@app.route('/admin/logout')
def admin_logout():
    """Выход из админ-панели"""
    session.pop('admin_authenticated', None)
    return redirect(url_for('index'))


# Обработчик ошибок
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return "Внутренняя ошибка сервера. Пожалуйста, попробуйте позже.", 500

@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"Not found error: {error}")
    return "Страница не найдена.", 404

# Для совместимости с Render
application = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
