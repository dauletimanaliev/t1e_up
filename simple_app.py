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

# Загружаем переменные окружения
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Простая база данных в JSON файле
DB_FILE = 'simple_db.json'

def load_db():
    """Загружает данные из JSON файла"""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
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
            }
        ]
    }

def save_db(data):
    """Сохраняет данные в JSON файл"""
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_all_active_ties():
    """Возвращает все активные галстуки"""
    db = load_db()
    return [tie for tie in db['ties'] if tie.get('active', True)]

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
    db = load_db()
    return [order for order in db['orders'].values() if order['user_id'] == user_id]

def send_admin_notification(order):
    """Отправляет уведомление админу в Telegram"""
    bot_token = os.environ.get('BOT_TOKEN')
    admin_id = os.environ.get('ADMIN_ID')
    
    if not bot_token or not admin_id:
        print("BOT_TOKEN или ADMIN_ID не настроены")
        return False
    
    message = f"""
🛍️ *НОВЫЙ ЗАКАЗ #{order['id']}*

👤 *ИНФОРМАЦИЯ О ПОКУПАТЕЛЕ:*
• Имя: {order['recipient_name']} {order.get('recipient_surname', '')}
• Телефон: {order['recipient_phone']}
• Адрес доставки: {order['delivery_address']}

🎩 *ИНФОРМАЦИЯ О ТОВАРЕ:*
• Название: {order['tie_name']}
• Цена: {order['price']:,.0f} ₸
• Количество: 1 шт

📦 *ИНФОРМАЦИЯ О ЗАКАЗЕ:*
• Номер заказа: #{order['id']}
• Дата заказа: {datetime.fromisoformat(order['created_at']).strftime('%d.%m.%Y в %H:%M')}
• Статус: {order['status']}
• Источник: Веб-сайт T1EUP

💰 *ОПЛАТА:*
• Сумма к оплате: {order['price']:,.0f} ₸
• Способ оплаты: Kaspi
• Ссылка для оплаты: https://pay.kaspi.kz/pay/sl65g7ez

🏢 *РЕКВИЗИТЫ:*
• Получатель: ИП АУЕЛЬТАЙ
• Адрес: Алматы, Мустай Карима 13а, 72

📞 *КОНТАКТЫ:*
• Телефон покупателя: {order['recipient_phone']}
• Для связи с покупателем используйте указанный номер

⏰ *ВРЕМЯ ОБРАБОТКИ:*
• Обработать заказ в течение 24 часов
• Связаться с покупателем для подтверждения
    """
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        'chat_id': admin_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, data=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка отправки уведомления: {e}")
        return False

# Маршруты
@app.route('/')
def index():
    ties = get_all_active_ties()
    return render_template('index.html', ties=ties)

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
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    
    orders = get_user_orders(int(user_id))
    return render_template('profile.html', orders=orders)

@app.route('/auth/telegram', methods=['POST'])
def auth_telegram():
    data = request.get_json()
    user_id = data.get('id')
    username = data.get('username')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    
    if not user_id:
        return jsonify({'success': False, 'error': 'ID пользователя не предоставлен'})
    
    user = get_or_create_user(user_id, username, first_name, last_name)
    
    # Проверяем, является ли пользователь админом
    admin_ids = os.environ.get('ADMIN_IDS', '').split(',')
    is_admin = str(user_id) in admin_ids
    
    if is_admin:
        session['admin_authenticated'] = True
        session['admin_telegram_id'] = user_id
    
    response = jsonify({
        'success': True,
        'user': user,
        'is_admin': is_admin
    })
    
    response.set_cookie('user_id', str(user_id), max_age=30*24*60*60)  # 30 дней
    return response

@app.route('/TieUp/<path:filename>')
def tie_images(filename):
    return send_from_directory('TieUp', filename)

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
