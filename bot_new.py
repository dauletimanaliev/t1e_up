"""
Professional Telegram Bot for Tie Shop with Enhanced Features
"""

import os
import io
import re
import logging
import zipfile
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes
from telegram.constants import ParseMode

from translations import get_text, TRANSLATIONS
from catalog import TIES_CATALOG, get_tie_by_id
from database import get_or_create_user, update_user_language, get_user_language, create_order, get_user_orders, update_order_status

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
PAYMENT_LINK = os.getenv('PAYMENT_LINK')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
LANGUAGE_SELECTION = 0
MAIN_MENU = 1
CATALOG_SENT = 2
TIE_DETAILS = 3
CONFIRM_PURCHASE = 4
NAME = 5
SURNAME = 6
PHONE = 7
ADDRESS = 8
CHECKOUT = 9
PAYMENT = 10
ADMIN_REVIEW = 11

# Tie colors mapping
TIE_COLORS = {
    'tie_001': '🔵 Синий классический',
    'tie_002': '🔴 Красный элегантный', 
    'tie_003': '⚫ Черный деловой',
    'tie_004': '🟢 Зеленый премиум',
    'tie_005': '🟣 Фиолетовый стильный',
    'tie_006': '🟡 Золотой праздничный',
    'tie_007': '🔵 Темно-синий',
    'tie_008': '🟤 Коричневый эксклюзив',
    'tie_009': '⚪ Серебристый люкс',
    'tie_010': '🔴 Бордовый VIP',
    'tie_011': '⚫ Черный эксклюзив'
}

class TieShopBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                LANGUAGE_SELECTION: [CallbackQueryHandler(self.language_selected, pattern='^lang_')],
                MAIN_MENU: [
                    CallbackQueryHandler(self.show_catalog, pattern='^catalog$'),
                    CallbackQueryHandler(self.show_orders, pattern='^my_orders$'),
                    CallbackQueryHandler(self.contact_support, pattern='^support$'),
                ],
                CATALOG_SENT: [
                    CallbackQueryHandler(self.show_tie_details, pattern='^tie_'),
                    CallbackQueryHandler(self.back_to_menu, pattern='^back_menu$'),
                ],
                TIE_DETAILS: [
                    CallbackQueryHandler(self.confirm_purchase, pattern='^buy_'),
                    CallbackQueryHandler(self.back_to_catalog, pattern='^back_catalog$'),
                ],
                CONFIRM_PURCHASE: [
                    CallbackQueryHandler(self.start_order, pattern='^yes_buy$'),
                    CallbackQueryHandler(self.back_to_catalog, pattern='^no_buy$'),
                ],
                NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_name)],
                SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_surname)],
                PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_phone)],
                ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_address)],
                CHECKOUT: [
                    CallbackQueryHandler(self.process_payment, pattern='^pay_order$'),
                    CallbackQueryHandler(self.cancel_order, pattern='^cancel_order$'),
                ],
                PAYMENT: [
                    CallbackQueryHandler(self.payment_done, pattern='^payment_done$'),
                ],
                ADMIN_REVIEW: [
                    CallbackQueryHandler(self.admin_approve, pattern='^approve_'),
                    CallbackQueryHandler(self.admin_reject, pattern='^reject_'),
                ],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
        
        self.application.add_handler(conv_handler)
        
        # Admin commands
        self.application.add_handler(CommandHandler('admin', self.admin_panel))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start command handler"""
        user = update.effective_user
        get_or_create_user(user.id, user.username)
        
        keyboard = [
            [InlineKeyboardButton("🇰🇿 Қазақша", callback_data='lang_kz')],
            [InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru')],
            [InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🌐 Тілді таңдаңыз / Выберите язык / Choose language",
            reply_markup=reply_markup
        )
        return LANGUAGE_SELECTION
    
    async def language_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle language selection"""
        query = update.callback_query
        await query.answer()
        
        lang = query.data.replace('lang_', '')
        user_id = update.effective_user.id
        
        update_user_language(user_id, lang)
        context.user_data['language'] = lang
        
        await query.edit_message_text(
            get_text(lang, 'welcome'),
            parse_mode='Markdown'
        )
        
        return await self.show_main_menu(update, context)
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Display main menu"""
        lang = context.user_data.get('language', 'ru')
        
        keyboard = [
            [InlineKeyboardButton("🛍️ Каталог галстуков", callback_data='catalog')],
            [InlineKeyboardButton("📦 Мои заказы", callback_data='my_orders')],
            [InlineKeyboardButton("💬 Поддержка", callback_data='support')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = "📌 Выберите действие:"
        
        if update.callback_query:
            await update.callback_query.message.reply_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        return MAIN_MENU
    
    async def show_catalog(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Send catalog as ZIP archive and show tie selection buttons"""
        query = update.callback_query
        await query.answer()
        
        lang = context.user_data.get('language', 'ru')
        
        # Create ZIP archive with all tie images
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            tie_folder = 'TieUp'
            for filename in os.listdir(tie_folder):
                if filename.endswith('.webp'):
                    file_path = os.path.join(tie_folder, filename)
                    zip_file.write(file_path, filename)
        
        zip_buffer.seek(0)
        
        # Send ZIP file
        await query.message.reply_document(
            document=InputFile(zip_buffer, filename='Tie_Catalog.zip'),
            caption="📦 *Полный каталог галстуков*\n\nВыберите галстук по цвету:",
            parse_mode='Markdown'
        )
        
        # Create color selection buttons
        keyboard = []
        for tie_id, color_name in TIE_COLORS.items():
            keyboard.append([InlineKeyboardButton(color_name, callback_data=f'tie_{tie_id}')])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад в меню", callback_data='back_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            "🎨 Выберите цвет галстука:",
            reply_markup=reply_markup
        )
        
        return CATALOG_SENT
    
    async def show_tie_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show detailed information about selected tie"""
        query = update.callback_query
        await query.answer()
        
        lang = context.user_data.get('language', 'ru')
        tie_id = query.data.replace('tie_', '')
        
        tie = get_tie_by_id(tie_id)
        if not tie:
            await query.message.reply_text("❌ Галстук не найден")
            return CATALOG_SENT
        
        context.user_data['selected_tie'] = tie
        
        # Send tie photo with details
        image_path = tie.get('image', '')
        caption = f"""
🎯 *{tie['name'][lang]}*

📝 *Описание:* {tie['description'][lang]}
💰 *Цена:* {tie['price']:,} тг
🚚 *Доставка:* 15 дней
📦 *Материал:* {tie['material']}

✅ Премиум качество
✅ Ручная работа
✅ Гарантия возврата
"""
        
        keyboard = [
            [InlineKeyboardButton("💳 Купить", callback_data=f"buy_{tie_id}")],
            [InlineKeyboardButton("◀️ Назад к каталогу", callback_data='back_catalog')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption=caption,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        else:
            await query.message.reply_text(
                caption,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
        return TIE_DETAILS
    
    async def confirm_purchase(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Confirm purchase intention"""
        query = update.callback_query
        await query.answer()
        
        lang = context.user_data.get('language', 'ru')
        tie = context.user_data.get('selected_tie')
        
        message = f"""
❓ *Вы действительно хотите купить этот галстук?*

🎯 {tie['name'][lang]}
💰 {tie['price']:,} тг
"""
        
        keyboard = [
            [InlineKeyboardButton("✅ Да, хочу купить", callback_data='yes_buy')],
            [InlineKeyboardButton("❌ Нет, посмотреть другие", callback_data='no_buy')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return CONFIRM_PURCHASE
    
    async def start_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start order form"""
        query = update.callback_query
        await query.answer()
        
        lang = context.user_data.get('language', 'ru')
        
        await query.message.reply_text(
            "📝 *Заполните анкету для оформления заказа*\n\n👤 Введите ваше имя:",
            parse_mode='Markdown'
        )
        
        return NAME
    
    async def receive_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive and validate name"""
        name = update.message.text.strip()
        
        # Validation
        if len(name) < 2:
            await update.message.reply_text(
                "❌ Имя слишком короткое. Минимум 2 символа.\n\nВведите имя заново:"
            )
            return NAME
        
        if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s-]+$', name):
            await update.message.reply_text(
                "❌ Имя может содержать только буквы и дефис.\n\nВведите имя заново:"
            )
            return NAME
        
        context.user_data['recipient_name'] = name
        
        await update.message.reply_text(
            "👤 Введите вашу фамилию:"
        )
        
        return SURNAME
    
    async def receive_surname(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive and validate surname"""
        surname = update.message.text.strip()
        
        # Validation
        if len(surname) < 2:
            await update.message.reply_text(
                "❌ Фамилия слишком короткая. Минимум 2 символа.\n\nВведите фамилию заново:"
            )
            return SURNAME
        
        if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s-]+$', surname):
            await update.message.reply_text(
                "❌ Фамилия может содержать только буквы и дефис.\n\nВведите фамилию заново:"
            )
            return SURNAME
        
        context.user_data['recipient_surname'] = surname
        
        await update.message.reply_text(
            "📱 Введите номер телефона:\n(Формат: +7 777 123 45 67)"
        )
        
        return PHONE
    
    async def receive_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive and validate phone"""
        phone = update.message.text.strip()
        
        # Remove all non-digit characters for validation
        phone_digits = re.sub(r'\D', '', phone)
        
        # Check Kazakhstan phone format
        if not re.match(r'^(7|8)?7\d{9}$', phone_digits):
            await update.message.reply_text(
                "❌ Неверный формат номера.\n\nВведите казахстанский номер:\n+7 777 123 45 67"
            )
            return PHONE
        
        # Format phone number
        if phone_digits.startswith('8'):
            phone_digits = '7' + phone_digits[1:]
        elif not phone_digits.startswith('7'):
            phone_digits = '7' + phone_digits
        
        formatted_phone = f"+{phone_digits[0]} {phone_digits[1:4]} {phone_digits[4:7]} {phone_digits[7:9]} {phone_digits[9:11]}"
        context.user_data['recipient_phone'] = formatted_phone
        
        await update.message.reply_text(
            "📍 Введите полный адрес доставки:\n(Город, улица, дом, квартира)"
        )
        
        return ADDRESS
    
    async def receive_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive and validate address"""
        address = update.message.text.strip()
        
        # Validation
        if len(address) < 10:
            await update.message.reply_text(
                "❌ Адрес слишком короткий.\n\nВведите полный адрес с городом, улицей и номером дома:"
            )
            return ADDRESS
        
        context.user_data['delivery_address'] = address
        
        # Show order summary
        tie = context.user_data['selected_tie']
        lang = context.user_data.get('language', 'ru')
        
        summary = f"""
📋 *Проверьте ваш заказ:*

🎯 *Товар:* {tie['name'][lang]}
💰 *Цена:* {tie['price']:,} тг

👤 *Получатель:* {context.user_data['recipient_name']} {context.user_data['recipient_surname']}
📱 *Телефон:* {context.user_data['recipient_phone']}
📍 *Адрес:* {context.user_data['delivery_address']}

💳 *К оплате:* {tie['price']:,} тг
"""
        
        keyboard = [
            [InlineKeyboardButton("💳 Оплатить", callback_data='pay_order')],
            [InlineKeyboardButton("❌ Отменить заказ", callback_data='cancel_order')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            summary,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return CHECKOUT
    
    async def process_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Process payment"""
        query = update.callback_query
        await query.answer()
        
        # Create order in database
        user_id = update.effective_user.id
        tie = context.user_data['selected_tie']
        lang = context.user_data.get('language', 'ru')
        
        order_data = {
            'user_telegram_id': user_id,
            'tie_id': tie['id'],
            'tie_name': tie['name'][lang],
            'price': tie['price'],
            'recipient_name': context.user_data['recipient_name'],
            'recipient_surname': context.user_data['recipient_surname'],
            'recipient_phone': context.user_data['recipient_phone'],
            'delivery_address': context.user_data['delivery_address'],
            'status': 'pending_payment'
        }
        
        order = create_order(order_data)
        context.user_data['order_id'] = order.id
        
        # Send payment instructions
        payment_message = f"""
💳 *Оплата заказа #{order.id}*

Сумма к оплате: *{tie['price']:,} тг*

1️⃣ Нажмите кнопку "Оплатить через Kaspi"
2️⃣ Оплатите заказ
3️⃣ Сохраните чек
4️⃣ Нажмите "Я оплатил"

⚠️ *Важно:* Сохраните чек для подтверждения оплаты
"""
        
        keyboard = [
            [InlineKeyboardButton("💳 Оплатить через Kaspi", url=PAYMENT_LINK)],
            [InlineKeyboardButton("✅ Я оплатил", callback_data='payment_done')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            payment_message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return PAYMENT
    
    async def payment_done(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle payment confirmation"""
        query = update.callback_query
        await query.answer()
        
        order_id = context.user_data['order_id']
        tie = context.user_data['selected_tie']
        lang = context.user_data.get('language', 'ru')
        
        # Update order status
        update_order_status(order_id, 'pending_admin_review')
        
        # Send notification to admin
        admin_message = f"""
🆕 *Новый заказ #{order_id}*

👤 *Клиент:* {context.user_data['recipient_name']} {context.user_data['recipient_surname']}
📱 *Телефон:* {context.user_data['recipient_phone']}
📍 *Адрес:* {context.user_data['delivery_address']}

🎯 *Товар:* {tie['name'][lang]}
💰 *Сумма:* {tie['price']:,} тг

⏳ *Статус:* Ожидает проверки чека

Проверьте оплату в Kaspi и подтвердите заказ:
"""
        
        keyboard = [
            [InlineKeyboardButton("✅ Подтвердить заказ", callback_data=f'approve_{order_id}')],
            [InlineKeyboardButton("❌ Отклонить заказ", callback_data=f'reject_{order_id}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        # Send confirmation to user
        await query.message.reply_text(
            "✅ Спасибо! Ваш заказ отправлен на проверку.\n\nМы проверим оплату и отправим вам подтверждение.",
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
    
    async def admin_approve(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Admin approves order"""
        query = update.callback_query
        await query.answer()
        
        order_id = int(query.data.replace('approve_', ''))
        
        # Update order status
        update_order_status(order_id, 'confirmed')
        
        # Get order details from database
        # This would need implementation in database.py
        
        await query.edit_message_text(
            f"✅ Заказ #{order_id} подтвержден и отправлен в обработку.",
            parse_mode='Markdown'
        )
        
        # Notify customer
        # You would need to store user_id with the order to send this
        # await context.bot.send_message(
        #     chat_id=user_id,
        #     text=f"✅ Ваш заказ #{order_id} подтвержден!\n\n🚚 Доставка в течение 15 дней.",
        #     parse_mode='Markdown'
        # )
        
        return ConversationHandler.END
    
    async def admin_reject(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Admin rejects order"""
        query = update.callback_query
        await query.answer()
        
        order_id = int(query.data.replace('reject_', ''))
        
        # Update order status
        update_order_status(order_id, 'rejected')
        
        await query.edit_message_text(
            f"❌ Заказ #{order_id} отклонен.",
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
    
    async def back_to_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Go back to main menu"""
        return await self.show_main_menu(update, context)
    
    async def back_to_catalog(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Go back to catalog"""
        return await self.show_catalog(update, context)
    
    async def cancel_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel order"""
        query = update.callback_query
        await query.answer()
        
        await query.message.reply_text(
            "❌ Заказ отменен.\n\nВозвращаемся в главное меню...",
            parse_mode='Markdown'
        )
        
        return await self.show_main_menu(update, context)
    
    async def show_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show user orders"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        orders = get_user_orders(user_id)
        
        if not orders:
            await query.message.reply_text("У вас пока нет заказов.")
        else:
            orders_text = "📦 *Ваши заказы:*\n\n"
            for order in orders:
                orders_text += f"Заказ #{order.id} - {order.status}\n"
            
            await query.message.reply_text(orders_text, parse_mode='Markdown')
        
        return await self.show_main_menu(update, context)
    
    async def contact_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Contact support"""
        query = update.callback_query
        await query.answer()
        
        await query.message.reply_text(
            "💬 Свяжитесь с поддержкой:\n\n📱 WhatsApp: +7 777 123 45 67\n📧 Email: support@tieshop.kz",
            parse_mode='Markdown'
        )
        
        return await self.show_main_menu(update, context)
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel conversation"""
        await update.message.reply_text("Операция отменена.")
        return ConversationHandler.END
    
    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Admin panel"""
        user_id = update.effective_user.id
        
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ У вас нет доступа к админ-панели.")
            return
        
        await update.message.reply_text(
            "🔧 *Админ-панель*\n\nЗдесь будут отображаться новые заказы для проверки.",
            parse_mode='Markdown'
        )
    
    def run(self):
        """Run the bot"""
        logger.info("Starting bot...")
        self.application.run_polling()

if __name__ == '__main__':
    bot = TieShopBot()
    bot.run()
