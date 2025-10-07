"""
T1EUP Tie Shop Web Application
Веб-приложение для магазина галстуков с интеграцией Telegram бота
"""

import os
import json
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory, session
from dotenv import load_dotenv
from database import get_all_active_ties, create_order, get_order_by_id, update_order_status, get_or_create_user, get_user_orders, get_tie_by_id, create_tie, update_tie, delete_tie, toggle_tie_status

# Загружаем переменные окружения
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'http://localhost:5000')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')  # Пароль по умолчанию

# Список админских Telegram ID (можно добавить несколько админов)
ADMIN_TELEGRAM_IDS = [
    int(admin_id.strip()) for admin_id in os.getenv('ADMIN_IDS', '123456789').split(',')
    if admin_id.strip().isdigit()
]

class TieShopWebApp:
    def __init__(self):
        self.app = app
        self.setup_routes()
    
    def is_admin_authenticated(self):
        """Проверка авторизации админа"""
        return session.get('admin_authenticated', False)
    
    def is_telegram_admin(self, telegram_id):
        """Проверка, является ли пользователь админом по Telegram ID"""
        return telegram_id in ADMIN_TELEGRAM_IDS
    
    def require_admin_auth(self, f):
        """Декоратор для защиты админ-маршрутов"""
        def decorated_function(*args, **kwargs):
            # Проверяем авторизацию через сессию
            if self.is_admin_authenticated():
                return f(*args, **kwargs)
            
            # Проверяем авторизацию через Telegram ID
            user_id = request.cookies.get('user_id')
            if user_id and self.is_telegram_admin(int(user_id)):
                session['admin_authenticated'] = True
                session['admin_telegram_id'] = int(user_id)
                return f(*args, **kwargs)
            
            # Если не авторизован, перенаправляем на страницу входа
            return redirect(url_for('admin_login'))
        decorated_function.__name__ = f.__name__
        return decorated_function
    
    def setup_routes(self):
        """Настройка маршрутов"""
        
        @self.app.route('/')
        def index():
            """Главная страница с каталогом"""
            ties = get_all_active_ties()
            return render_template('index.html', ties=ties)
        
        @self.app.route('/TieUp/<path:filename>')
        def tie_images(filename):
            """Обслуживание изображений галстуков"""
            return send_from_directory('TieUp', filename)
        
        @self.app.route('/tie/<int:tie_id>')
        def tie_detail(tie_id):
            """Страница детального просмотра галстука"""
            ties = get_all_active_ties()
            tie = next((t for t in ties if t.id == tie_id), None)
            
            if not tie:
                flash('Галстук не найден', 'error')
                return redirect(url_for('index'))
            
            return render_template('tie_detail.html', tie=tie)
        
        @self.app.route('/order/<int:tie_id>', methods=['GET', 'POST'])
        def create_order_page(tie_id):
            """Страница оформления заказа"""
            ties = get_all_active_ties()
            tie = next((t for t in ties if t.id == tie_id), None)
            
            if not tie:
                flash('Галстук не найден', 'error')
                return redirect(url_for('index'))
            
            if request.method == 'POST':
                return self.process_order(tie)
            
            return render_template('order_form.html', tie=tie)
        
        @self.app.route('/order/success/<int:order_id>')
        def order_success(order_id):
            """Страница успешного заказа"""
            order = get_order_by_id(order_id)
            if not order:
                flash('Заказ не найден', 'error')
                return redirect(url_for('index'))
            
            return render_template('order_success.html', order=order)
        
        @self.app.route('/api/order', methods=['POST'])
        def api_create_order():
            """API для создания заказа"""
            try:
                data = request.get_json()
                
                # Валидация данных
                required_fields = ['tie_id', 'customer_name', 'customer_phone', 'delivery_address']
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({'error': f'Поле {field} обязательно'}), 400
                
                # Создание заказа
                order_data = {
                    'user_telegram_id': None,  # Для веб-заказов
                    'tie_id': data['tie_id'],
                    'tie_name': data.get('tie_name', ''),
                    'price': data.get('price', 0),
                    'recipient_name': data['customer_name'],
                    'recipient_surname': data.get('customer_surname', ''),
                    'recipient_phone': data['customer_phone'],
                    'delivery_address': data['delivery_address'],
                    'status': 'pending'
                }
                
                order = create_order(order_data)
                
                # Отправка уведомления админу
                self.send_admin_notification(order)
                
                return jsonify({
                    'success': True,
                    'order_id': order.id,
                    'message': 'Заказ успешно создан'
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/admin/orders')
        def admin_orders():
            """Админ панель для просмотра заказов"""
            # Здесь можно добавить аутентификацию
            from database import Session, Order
            session = Session()
            try:
                orders = session.query(Order).order_by(Order.created_at.desc()).all()
                return render_template('admin_orders.html', orders=orders)
            finally:
                session.close()
        
        @self.app.route('/admin/order/<int:order_id>/status', methods=['POST'])
        def update_order_status_api(order_id):
            """API для обновления статуса заказа"""
            try:
                data = request.get_json()
                new_status = data.get('status')
                
                if not new_status:
                    return jsonify({'error': 'Статус не указан'}), 400
                
                update_order_status(order_id, new_status)
                
                return jsonify({'success': True, 'message': 'Статус обновлен'})
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/profile')
        def profile():
            """Страница профиля пользователя"""
            # Получаем пользователя из сессии или создаем демо-пользователя
            user_id = request.cookies.get('user_id')
            
            if not user_id:
                # Создаем демо-пользователя
                user = get_or_create_user(999999999, 'demo_user')
                user_id = user.telegram_id
            else:
                user = get_or_create_user(int(user_id), 'web_user')
            
            # Получаем заказы пользователя
            orders = get_user_orders(user.telegram_id)
            
            # Вычисляем общую сумму потраченных денег
            total_spent = sum(order.price for order in orders if order.status in ['paid', 'delivered'])
            
            # Создаем словарь с данными пользователя для передачи в шаблон
            user_data = {
                'name': user.username or 'Пользователь',
                'phone': 'Не указан',
                'created_at': user.created_at
            }
            
            return render_template('profile.html', 
                                 user=user_data, 
                                 orders=orders, 
                                 total_spent=total_spent)
        
        @self.app.route('/auth/telegram', methods=['POST'])
        def auth_telegram():
            """Авторизация через Telegram"""
            try:
                data = request.get_json()
                telegram_id = data.get('id')
                username = data.get('username')
                first_name = data.get('first_name')
                last_name = data.get('last_name')
                
                if not telegram_id:
                    return jsonify({'error': 'ID пользователя не указан'}), 400
                
                # Создаем или получаем пользователя
                user = get_or_create_user(telegram_id, username)
                
                # Обновляем информацию о пользователе
                if first_name:
                    user.name = first_name
                if last_name:
                    user.surname = last_name
                
                # Проверяем, является ли пользователь админом
                is_admin = self.is_telegram_admin(telegram_id)
                if is_admin:
                    session['admin_authenticated'] = True
                    session['admin_telegram_id'] = telegram_id
                
                response = jsonify({
                    'success': True, 
                    'user_id': user.telegram_id,
                    'is_admin': is_admin
                })
                response.set_cookie('user_id', str(user.telegram_id), max_age=30*24*60*60)  # 30 дней
                
                return response
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/check-user-status', methods=['POST'])
        def check_user_status():
            """Проверка статуса пользователя без создания сессии"""
            try:
                data = request.get_json()
                telegram_id = data.get('id')
                
                if not telegram_id:
                    return jsonify({'error': 'ID пользователя не указан'}), 400
                
                # Проверяем, является ли пользователь админом
                is_admin = self.is_telegram_admin(telegram_id)
                
                return jsonify({
                    'success': True,
                    'is_admin': is_admin
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # Admin authentication routes
        @self.app.route('/admin/login', methods=['GET', 'POST'])
        def admin_login():
            """Вход в админ-панель"""
            if request.method == 'POST':
                password = request.form.get('password')
                if password == ADMIN_PASSWORD:
                    session['admin_authenticated'] = True
                    flash('Добро пожаловать в админ-панель!', 'success')
                    return redirect(url_for('admin_catalog'))
                else:
                    flash('Неверный пароль!', 'error')
            
            return render_template('admin/login.html')
        
        @self.app.route('/admin/logout')
        def admin_logout():
            """Выход из админ-панели"""
            session.pop('admin_authenticated', None)
            flash('Вы вышли из админ-панели', 'info')
            return redirect(url_for('admin_login'))
        
        # Admin routes
        @self.app.route('/admin')
        @self.require_admin_auth
        def admin_catalog():
            """Админ-панель - управление каталогом"""
            from database import Session, Tie
            session = Session()
            try:
                ties = session.query(Tie).all()
                active_ties = [tie for tie in ties if tie.is_active]
                inactive_ties = [tie for tie in ties if not tie.is_active]
                avg_price = sum(tie.price for tie in ties) / len(ties) if ties else 0
            finally:
                session.close()
            
            return render_template('admin/catalog.html', 
                                 ties=ties, 
                                 active_ties=active_ties, 
                                 inactive_ties=inactive_ties, 
                                 avg_price=avg_price)
        
        @self.app.route('/admin/tie/add', methods=['GET', 'POST'])
        @self.require_admin_auth
        def admin_add_tie():
            """Добавить новый товар"""
            if request.method == 'POST':
                try:
                    # Получаем данные из формы
                    tie_data = {
                        'name_ru': request.form.get('name_ru'),
                        'name_kz': request.form.get('name_kz'),
                        'name_en': request.form.get('name_en'),
                        'color_ru': request.form.get('color_ru'),
                        'color_kz': request.form.get('color_kz'),
                        'color_en': request.form.get('color_en'),
                        'description_ru': request.form.get('description_ru'),
                        'description_kz': request.form.get('description_kz'),
                        'description_en': request.form.get('description_en'),
                        'price': float(request.form.get('price')),
                        'is_active': request.form.get('is_active') == 'true'
                    }
                    
                    # Обработка изображения
                    if 'image' in request.files and request.files['image'].filename:
                        file = request.files['image']
                        if file and file.filename:
                            # Сохраняем файл
                            filename = f"tie_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                            filepath = f"TieUp/{filename}"
                            file.save(filepath)
                            tie_data['image_path'] = filepath
                    elif request.form.get('image_url'):
                        tie_data['image_path'] = request.form.get('image_url')
                    
                    # Создаем товар
                    tie = create_tie(tie_data)
                    flash(f'Товар "{tie.name_ru}" успешно добавлен!', 'success')
                    return redirect(url_for('admin_catalog'))
                    
                except Exception as e:
                    flash(f'Ошибка при добавлении товара: {str(e)}', 'error')
            
            return render_template('admin/add_tie.html')
        
        @self.app.route('/admin/tie/<int:tie_id>/edit', methods=['GET', 'POST'])
        @self.require_admin_auth
        def admin_edit_tie(tie_id):
            """Редактировать товар"""
            tie = get_tie_by_id(tie_id)
            if not tie:
                flash('Товар не найден', 'error')
                return redirect(url_for('admin_catalog'))
            
            if request.method == 'POST':
                try:
                    # Получаем данные из формы
                    tie_data = {
                        'name_ru': request.form.get('name_ru'),
                        'name_kz': request.form.get('name_kz'),
                        'name_en': request.form.get('name_en'),
                        'color_ru': request.form.get('color_ru'),
                        'color_kz': request.form.get('color_kz'),
                        'color_en': request.form.get('color_en'),
                        'material_ru': request.form.get('material_ru'),
                        'material_kz': request.form.get('material_kz'),
                        'material_en': request.form.get('material_en'),
                        'description_ru': request.form.get('description_ru'),
                        'description_kz': request.form.get('description_kz'),
                        'description_en': request.form.get('description_en'),
                        'price': float(request.form.get('price')),
                        'is_active': request.form.get('is_active') == 'true'
                    }
                    
                    # Обработка изображения
                    if 'image' in request.files and request.files['image'].filename:
                        file = request.files['image']
                        if file and file.filename:
                            # Сохраняем файл
                            filename = f"tie_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                            filepath = f"TieUp/{filename}"
                            file.save(filepath)
                            tie_data['image_path'] = filepath
                    elif request.form.get('image_url'):
                        tie_data['image_path'] = request.form.get('image_url')
                    
                    # Обновляем товар
                    update_tie(tie_id, tie_data)
                    flash(f'Товар "{tie_data["name_ru"]}" успешно обновлен!', 'success')
                    return redirect(url_for('admin_catalog'))
                    
                except Exception as e:
                    flash(f'Ошибка при обновлении товара: {str(e)}', 'error')
            
            return render_template('admin/edit_tie.html', tie=tie)
        
        @self.app.route('/admin/tie/<int:tie_id>/toggle-status', methods=['POST'])
        @self.require_admin_auth
        def admin_toggle_tie_status(tie_id):
            """Переключить статус товара"""
            try:
                tie = toggle_tie_status(tie_id)
                if tie:
                    status = "активирован" if tie.is_active else "деактивирован"
                    return jsonify({'success': True, 'message': f'Товар {status}'})
                else:
                    return jsonify({'error': 'Товар не найден'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/admin/tie/<int:tie_id>/delete', methods=['POST'])
        @self.require_admin_auth
        def admin_delete_tie(tie_id):
            """Удалить товар"""
            try:
                tie = get_tie_by_id(tie_id)
                if not tie:
                    return jsonify({'error': 'Товар не найден'}), 404
                
                tie_name = tie.name_ru
                success = delete_tie(tie_id)
                if success:
                    return jsonify({'success': True, 'message': f'Товар "{tie_name}" удален'})
                else:
                    return jsonify({'error': 'Ошибка при удалении товара'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def process_order(self, tie):
        """Обработка заказа"""
        try:
            # Получение данных из формы
            customer_name = request.form.get('customer_name')
            customer_surname = request.form.get('customer_surname', '')
            customer_phone = request.form.get('customer_phone')
            delivery_address = request.form.get('delivery_address')
            
            # Валидация
            if not all([customer_name, customer_phone, delivery_address]):
                flash('Пожалуйста, заполните все обязательные поля', 'error')
                return render_template('order_form.html', tie=tie)
            
            # Получаем пользователя из сессии
            user_id = request.cookies.get('user_id')
            if not user_id:
                # Создаем демо-пользователя
                user = get_or_create_user(999999999, 'demo_user')
                user_id = user.telegram_id
            
            # Создание заказа
            order_data = {
                'user_telegram_id': int(user_id),
                'tie_id': tie.id,
                'tie_name': tie.name_ru,
                'price': tie.price,
                'recipient_name': customer_name,
                'recipient_surname': customer_surname,
                'recipient_phone': customer_phone,
                'delivery_address': delivery_address,
                'status': 'pending'
            }
            
            order = create_order(order_data)
            
            # Отправка уведомления админу
            self.send_admin_notification(order)
            
            return redirect(url_for('order_success', order_id=order.id))
            
        except Exception as e:
            flash(f'Ошибка при создании заказа: {str(e)}', 'error')
            return render_template('order_form.html', tie=tie)
    
    def send_admin_notification(self, order):
        """Отправка уведомления админу в Telegram"""
        try:
            if not BOT_TOKEN or not ADMIN_CHAT_ID:
                print("BOT_TOKEN или ADMIN_CHAT_ID не настроены")
                return
            
            # Формирование сообщения
            message = f"""
🛍️ *НОВЫЙ ЗАКАЗ #{order.id}*

👤 *ИНФОРМАЦИЯ О ПОКУПАТЕЛЕ:*
• Имя: {order.recipient_name} {order.recipient_surname or ''}
• Телефон: {order.recipient_phone}
• Адрес доставки: {order.delivery_address}

🎩 *ИНФОРМАЦИЯ О ТОВАРЕ:*
• Название: {order.tie_name}
• Цена: {order.price:,.0f} ₸
• Количество: 1 шт

📦 *ИНФОРМАЦИЯ О ЗАКАЗЕ:*
• Номер заказа: #{order.id}
• Дата заказа: {order.created_at.strftime('%d.%m.%Y в %H:%M')}
• Статус: {order.status}
• Источник: Веб-сайт T1EUP

💰 *ОПЛАТА:*
• Сумма к оплате: {order.price:,.0f} ₸
• Способ оплаты: Kaspi
• Ссылка для оплаты: https://pay.kaspi.kz/pay/sl65g7ez

🏢 *РЕКВИЗИТЫ:*
• Получатель: ИП АУЕЛЬТАЙ
• Адрес: Алматы, Мустай Карима 13а, 72

📞 *КОНТАКТЫ:*
• Телефон покупателя: {order.recipient_phone}
• Для связи с покупателем используйте указанный номер

⏰ *ВРЕМЯ ОБРАБОТКИ:*
• Обработать заказ в течение 24 часов
• Связаться с покупателем для подтверждения
            """
            
            # Отправка через Telegram Bot API
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                'chat_id': ADMIN_CHAT_ID,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                print(f"✅ Уведомление о заказе #{order.id} отправлено админу")
            else:
                print(f"❌ Ошибка отправки уведомления: {response.text}")
                
        except Exception as e:
            print(f"❌ Ошибка при отправке уведомления: {e}")

# Создание экземпляра приложения
web_app = TieShopWebApp()

if __name__ == '__main__':
    # Миграция данных из JSON в базу данных
    from database import migrate_ties_from_json
    migrate_ties_from_json()
    
    # Запуск приложения
    app.run(debug=True, host='0.0.0.0', port=5000)
