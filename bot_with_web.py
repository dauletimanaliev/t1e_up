"""
T1EUP Tie Shop Bot with Web Integration
Telegram бот с интеграцией веб-приложения
"""

import os
import io
import logging
import re
import zipfile
import requests
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes
from telegram.constants import ParseMode

from translations import get_text, TRANSLATIONS
from catalog import TIES_CATALOG, get_tie_by_id, format_tie_info
from database import get_or_create_user, update_user_language, get_user_language, create_order, get_user_orders, get_all_active_ties

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
PAYMENT_LINK = os.getenv('PAYMENT_LINK')
WEB_APP_URL = os.getenv('WEB_APP_URL', 'http://localhost:5000')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
LANGUAGE_SELECTION = 0
MAIN_MENU = 1
CATALOG_VIEW = 2
NAME = 3
SURNAME = 4
PHONE = 5
ADDRESS = 6
CONFIRMATION = 7
PAYMENT_CONFIRMATION = 8

class TieShopBotWithWeb:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        # Conversation handler for the entire flow
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                LANGUAGE_SELECTION: [CallbackQueryHandler(self.language_selected, pattern='^lang_')],
                MAIN_MENU: [
                    CallbackQueryHandler(self.show_catalog, pattern='^catalog$'),
                    CallbackQueryHandler(self.show_orders, pattern='^my_orders$'),
                    CallbackQueryHandler(self.contact_support, pattern='^support$'),
                    CallbackQueryHandler(self.about_us, pattern='^about$'),
                    CallbackQueryHandler(self.show_web_app, pattern='^web_app$'),
                ],
                CATALOG_VIEW: [
                    CallbackQueryHandler(self.tie_selected, pattern='^select_'),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.tie_selected)
                ],
                NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_name)],
                SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_surname)],
                PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_phone)],
                ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_address)],
                CONFIRMATION: [
                    CallbackQueryHandler(self.confirm_order, pattern='^confirm_order$'),
                    CallbackQueryHandler(self.cancel_order, pattern='^cancel_order$'),
                ],
                PAYMENT_CONFIRMATION: [
                    CallbackQueryHandler(self.payment_confirmed, pattern='^payment_done$'),
                    CallbackQueryHandler(self.payment_cancelled, pattern='^payment_cancel$'),
                ],
            },
            fallbacks=[
                CommandHandler('start', self.start),
                CallbackQueryHandler(self.back_to_menu, pattern='^back_menu$'),
            ],
        )
        
        self.application.add_handler(conv_handler)
        self.application.add_handler(CommandHandler('help', self.help_command))
        self.application.add_handler(CommandHandler('web', self.web_command))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start command - show language selection"""
        user = update.effective_user
        get_or_create_user(user.id, user.username)
        
        keyboard = [
            [InlineKeyboardButton("🇰🇿 Қазақша", callback_data='lang_kz')],
            [InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru')],
            [InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            get_text('ru', 'choose_language'),
            reply_markup=reply_markup
        )
        return LANGUAGE_SELECTION
    
    async def language_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle language selection"""
        query = update.callback_query
        await query.answer()
        
        lang = query.data.replace('lang_', '')
        user_id = update.effective_user.id
        
        # Save language preference
        update_user_language(user_id, lang)
        context.user_data['language'] = lang
        
        # Send welcome message
        await query.edit_message_text(
            get_text(lang, 'welcome'),
            parse_mode='Markdown'
        )
        
        # Show main menu
        return await self.show_main_menu(update, context)
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Display main menu with web app option"""
        lang = context.user_data.get('language', 'ru')
        
        keyboard = [
            [InlineKeyboardButton(get_text(lang, 'catalog'), callback_data='catalog')],
            [InlineKeyboardButton("🌐 Веб-каталог", callback_data='web_app')],
            [InlineKeyboardButton(get_text(lang, 'my_orders'), callback_data='my_orders')],
            [InlineKeyboardButton(get_text(lang, 'contact_support'), callback_data='support')],
            [InlineKeyboardButton(get_text(lang, 'about_us'), callback_data='about')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = f"{get_text(lang, 'choose_action')}\n\n🌐 *Новое!* Теперь вы можете заказывать через удобный веб-каталог!"
        
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
    
    async def show_web_app(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show web app information and link"""
        query = update.callback_query
        await query.answer()
        
        lang = context.user_data.get('language', 'ru')
        
        web_text = {
            'kz': (
                "🌐 *Веб-каталог T1EUP*\n\n"
                "Енді сіз галстуктарды веб-каталог арқылы таңдай аласыз:\n\n"
                "✨ *Артықшылықтары:*\n"
                "• Толық каталог\n"
                "• Жылдам тапсырыс\n"
                "• Қолайлы интерфейс\n"
                "• Мобильді нұсқа\n\n"
                "Веб-каталогты ашу үшін төмендегі батырманы басыңыз:"
            ),
            'ru': (
                "🌐 *Веб-каталог T1EUP*\n\n"
                "Теперь вы можете выбирать галстуки через удобный веб-каталог:\n\n"
                "✨ *Преимущества:*\n"
                "• Полный каталог\n"
                "• Быстрое оформление заказа\n"
                "• Удобный интерфейс\n"
                "• Мобильная версия\n\n"
                "Нажмите кнопку ниже, чтобы открыть веб-каталог:"
            ),
            'en': (
                "🌐 *T1EUP Web Catalog*\n\n"
                "Now you can choose ties through our convenient web catalog:\n\n"
                "✨ *Advantages:*\n"
                "• Full catalog\n"
                "• Quick order placement\n"
                "• User-friendly interface\n"
                "• Mobile version\n\n"
                "Click the button below to open the web catalog:"
            )
        }
        
        keyboard = [
            [InlineKeyboardButton("🌐 Открыть веб-каталог", url=WEB_APP_URL)],
            [InlineKeyboardButton("📱 Каталог в боте", callback_data='catalog')],
            [InlineKeyboardButton(get_text(lang, 'back'), callback_data='back_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            web_text[lang],
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return MAIN_MENU
    
    async def show_catalog(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show tie catalog - all photos at once"""
        query = update.callback_query
        await query.answer()
        
        lang = context.user_data.get('language', 'ru')
        
        # Delete the previous message
        await query.delete_message()
        
        # Send all ties as photos with numbers
        media_group = []
        
        for i, tie in enumerate(TIES_CATALOG[:10], 1):  # First 10 ties for media group
            caption = f"**{i}. {tie['name'][lang]}**\n"
            caption += f"💰 {get_text(lang, 'price')}: {tie['price']:,} {get_text(lang, 'currency')}"
            
            # Get image path
            image_path = tie.get('image', '')
            if image_path and os.path.exists(image_path):
                try:
                    with open(image_path, 'rb') as photo:
                        media_group.append(
                            InputMediaPhoto(
                                media=photo.read(),
                                caption=caption if i == 1 else f"{i}. {tie['name'][lang]} - {tie['price']:,} {get_text(lang, 'currency')}",
                                parse_mode='Markdown'
                            )
                        )
                except Exception as e:
                    logger.error(f"Error loading photo for {tie['id']}: {e}")
        
        # Send as media group (album)
        if media_group:
            await query.message.reply_media_group(media=media_group)
        
        # Send remaining ties if more than 10
        if len(TIES_CATALOG) > 10:
            for i, tie in enumerate(TIES_CATALOG[10:], 11):
                caption = f"**{i}. {tie['name'][lang]}**\n"
                caption += f"💰 {get_text(lang, 'price')}: {tie['price']:,} {get_text(lang, 'currency')}"
                
                image_path = tie.get('image', '')
                if image_path and os.path.exists(image_path):
                    try:
                        with open(image_path, 'rb') as photo:
                            await query.message.reply_photo(
                                photo=photo,
                                caption=caption,
                                parse_mode='Markdown'
                            )
                    except Exception as e:
                        logger.error(f"Error sending photo for {tie['id']}: {e}")
                        await query.message.reply_text(
                            caption,
                            parse_mode='Markdown'
                        )
                else:
                    await query.message.reply_text(
                        caption,
                        parse_mode='Markdown'
                    )
        
        # Ask user to choose by number
        await query.message.reply_text(
            get_text(lang, 'choose_tie_number'),
            parse_mode='Markdown'
        )
        
        return CATALOG_VIEW
    
    async def tie_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle tie selection by number"""
        lang = context.user_data.get('language', 'ru')
        
        if update.message:
            # User sent a number
            try:
                tie_number = int(update.message.text.strip())
                if 1 <= tie_number <= len(TIES_CATALOG):
                    tie = TIES_CATALOG[tie_number - 1]
                else:
                    await update.message.reply_text(
                        get_text(lang, 'invalid_number'),
                        parse_mode='Markdown'
                    )
                    return CATALOG_VIEW
            except ValueError:
                await update.message.reply_text(
                    get_text(lang, 'invalid_number'),
                    parse_mode='Markdown'
                )
                return CATALOG_VIEW
        else:
            # Old callback query handler (for backward compatibility)
            query = update.callback_query
            await query.answer()
            tie_id = query.data.replace('select_', '')
            tie = get_tie_by_id(tie_id)
            
        if not tie:
            await update.message.reply_text(get_text(lang, 'error'))
            return ConversationHandler.END
        
        context.user_data['selected_tie'] = tie
        
        # Send tie details with image if available
        message = f"✨ {get_text(lang, 'tie_selected')}\n\n"
        message += f"🎩 **{tie['name'][lang]}**\n"
        message += f"📝 {tie['description'][lang]}\n"
        message += f"🧵 {get_text(lang, 'material')}: {tie['material'][lang]}\n"
        message += f"💰 {get_text(lang, 'price')}: {tie['price']:,} {get_text(lang, 'currency')}\n\n"
        message += f"{get_text(lang, 'order_form_start')}\n\n"
        message += get_text(lang, 'ask_name')
        
        # Try to send with photo
        image_path = tie.get('image', '')
        if image_path and os.path.exists(image_path):
            try:
                with Image.open(image_path) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    max_size = (1280, 1280)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    bio = io.BytesIO()
                    img.save(bio, 'JPEG', quality=85, optimize=True)
                    bio.seek(0)
                    
                    await update.message.reply_photo(
                        photo=bio,
                        caption=message,
                        parse_mode='Markdown'
                    )
            except Exception as e:
                logger.error(f"Error sending photo: {e}")
                await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text(message, parse_mode='Markdown')
        
        return NAME
    
    async def receive_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive recipient's name"""
        lang = context.user_data.get('language', 'ru')
        context.user_data['recipient_name'] = update.message.text
        
        await update.message.reply_text(
            get_text(lang, 'ask_surname'),
            parse_mode='Markdown'
        )
        
        return SURNAME
    
    async def receive_surname(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive recipient's surname"""
        lang = context.user_data.get('language', 'ru')
        context.user_data['recipient_surname'] = update.message.text
        
        await update.message.reply_text(
            get_text(lang, 'ask_phone'),
            parse_mode='Markdown'
        )
        
        return PHONE
    
    async def receive_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive recipient's phone"""
        lang = context.user_data.get('language', 'ru')
        context.user_data['recipient_phone'] = update.message.text
        
        await update.message.reply_text(
            get_text(lang, 'ask_address'),
            parse_mode='Markdown'
        )
        
        return ADDRESS
    
    async def receive_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive delivery address and show order summary"""
        lang = context.user_data.get('language', 'ru')
        context.user_data['delivery_address'] = update.message.text
        
        # Prepare order summary
        tie = context.user_data['selected_tie']
        summary = (
            f"{get_text(lang, 'order_summary')}"
            f"👔 {tie['name'][lang]}\n"
            f"💰 {tie['price']:,} {get_text(lang, 'currency')}\n\n"
            f"👤 {context.user_data['recipient_name']} {context.user_data['recipient_surname']}\n"
            f"📱 {context.user_data['recipient_phone']}\n"
            f"📍 {context.user_data['delivery_address']}\n\n"
            f"{get_text(lang, 'delivery_info')}"
        )
        
        keyboard = [
            [InlineKeyboardButton(get_text(lang, 'confirm_order'), callback_data='confirm_order')],
            [InlineKeyboardButton(get_text(lang, 'cancel_order'), callback_data='cancel_order')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            summary,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return CONFIRMATION
    
    async def confirm_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Confirm order and show payment link"""
        query = update.callback_query
        await query.answer()
        
        lang = context.user_data.get('language', 'ru')
        user_id = update.effective_user.id
        tie = context.user_data['selected_tie']
        
        # Create order in database
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
        
        # Generate payment message with order details
        payment_message = (
            f"🎯 *{get_text(lang, 'order_number')}:* #{order.id}\n\n"
            f"👔 *{get_text(lang, 'product')}:* {tie['name'][lang]}\n"
            f"💰 *{get_text(lang, 'amount_to_pay')}:* {tie['price']:,} {get_text(lang, 'currency')}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💳 *{get_text(lang, 'payment_method')}:* Kaspi.kz\n\n"
            f"📋 *{get_text(lang, 'payment_instructions')}:*\n"
            f"1️⃣ {get_text(lang, 'step_1_detailed')}\n"
            f"2️⃣ {get_text(lang, 'step_2_detailed')}\n"
            f"3️⃣ {get_text(lang, 'step_3_detailed')}\n"
            f"4️⃣ {get_text(lang, 'step_4_detailed')}\n\n"
            f"⚠️ *{get_text(lang, 'important')}:* {get_text(lang, 'save_receipt')}"
        )
        
        # Professional payment buttons
        keyboard = [
            [InlineKeyboardButton(
                f"💳 {get_text(lang, 'pay_kaspi')} ({tie['price']:,} {get_text(lang, 'currency')})", 
                url=PAYMENT_LINK
            )],
            [InlineKeyboardButton(
                f"✅ {get_text(lang, 'payment_completed')}", 
                callback_data='payment_done'
            )],
            [InlineKeyboardButton(
                f"❓ {get_text(lang, 'need_help')}", 
                callback_data='payment_cancel'
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            payment_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return PAYMENT_CONFIRMATION
    
    async def payment_confirmed(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle payment confirmation"""
        query = update.callback_query
        await query.answer()
        
        lang = context.user_data.get('language', 'ru')
        user_id = update.effective_user.id
        tie = context.user_data['selected_tie']
        order_id = context.user_data.get('order_id', 'N/A')
        
        # Send notification to admin about payment
        admin_message = (
            f"✅ *Заказ #{order_id} ОПЛАЧЕН*\n\n"
            f"👤 Клиент: @{update.effective_user.username or 'N/A'} (ID: {user_id})\n"
            f"👔 Товар: {tie['name']['ru']}\n"
            f"💰 Сумма: {tie['price']:,} тг\n\n"
            f"*Получатель:*\n"
            f"Имя: {context.user_data['recipient_name']} {context.user_data['recipient_surname']}\n"
            f"Телефон: {context.user_data['recipient_phone']}\n"
            f"Адрес: {context.user_data['delivery_address']}\n\n"
            f"📦 Статус: Готов к отправке\n"
            f"🚚 Доставка в течение 15 дней\n"
            f"🌐 Источник: Telegram Bot"
        )
        
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")
        
        # Send confirmation to user
        await query.edit_message_text(
            get_text(lang, 'order_confirmed'),
            parse_mode='Markdown'
        )
        
        # Return to main menu
        return await self.show_main_menu(update, context)
    
    async def payment_cancelled(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle payment cancellation or problem"""
        query = update.callback_query
        await query.answer()
        
        lang = context.user_data.get('language', 'ru')
        
        keyboard = [
            [InlineKeyboardButton(get_text(lang, 'try_again'), url=PAYMENT_LINK)],
            [InlineKeyboardButton(get_text(lang, 'contact_support'), callback_data='support')],
            [InlineKeyboardButton(get_text(lang, 'cancel_order'), callback_data='cancel_order')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            get_text(lang, 'payment_problem_text'),
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return PAYMENT_CONFIRMATION
    
    async def cancel_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel order"""
        query = update.callback_query
        await query.answer()
        
        lang = context.user_data.get('language', 'ru')
        
        await query.edit_message_text(
            get_text(lang, 'order_cancelled'),
            parse_mode='Markdown'
        )
        
        return await self.show_main_menu(update, context)
    
    async def show_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show user's orders"""
        query = update.callback_query
        await query.answer()
        
        lang = context.user_data.get('language', 'ru')
        user_id = update.effective_user.id
        
        orders = get_user_orders(user_id)
        
        if not orders:
            message = "📦 У вас пока нет заказов"
        else:
            message = f"📦 *{get_text(lang, 'my_orders')}:*\n\n"
            for order in orders:
                status_emoji = "✅" if order.status == "delivered" else "⏳"
                message += (
                    f"{status_emoji} Заказ #{order.id}\n"
                    f"📅 {order.created_at.strftime('%d.%m.%Y')}\n"
                    f"👔 {order.tie_name}\n"
                    f"💰 {order.price:,.0f} {get_text(lang, 'currency')}\n\n"
                )
        
        keyboard = [[InlineKeyboardButton(get_text(lang, 'back'), callback_data='back_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return MAIN_MENU
    
    async def contact_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show support contact information"""
        query = update.callback_query
        await query.answer()
        
        lang = context.user_data.get('language', 'ru')
        
        support_text = {
            'kz': "💬 *Қолдау қызметі*\n\n📞 Телефон: +7 777 123 45 67\n📧 Email: support@tieshop.kz\n⏰ Жұмыс уақыты: 9:00 - 21:00",
            'ru': "💬 *Служба поддержки*\n\n📞 Телефон: +7 777 123 45 67\n📧 Email: support@tieshop.kz\n⏰ Время работы: 9:00 - 21:00",
            'en': "💬 *Customer Support*\n\n📞 Phone: +7 777 123 45 67\n📧 Email: support@tieshop.kz\n⏰ Working hours: 9:00 - 21:00"
        }
        
        keyboard = [[InlineKeyboardButton(get_text(lang, 'back'), callback_data='back_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            support_text[lang],
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return MAIN_MENU
    
    async def about_us(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show about us information"""
        query = update.callback_query
        await query.answer()
        
        lang = context.user_data.get('language', 'ru')
        
        about_text = {
            'kz': (
                "ℹ️ *Біз туралы*\n\n"
                "🎩 *T1EUP - Премиум галстуктар дүкені*\n\n"
                "20 жылдан астам тәжірибемізбен біз сізге ең жақсы галстуктарды ұсынамыз.\n\n"
                "✨ Біздің артықшылықтарымыз:\n"
                "• 100% табиғи жібек\n"
                "• Эксклюзивті дизайн\n"
                "• Жеке стиль кеңесі\n"
                "• Жылдам жеткізу\n"
                "• Сапа кепілдігі\n\n"
                "🌐 *Жаңалық!* Енді веб-каталог арқылы да тапсырыс бере аласыз!"
            ),
            'ru': (
                "ℹ️ *О нас*\n\n"
                "🎩 *T1EUP - Магазин премиальных галстуков*\n\n"
                "С опытом более 20 лет мы предлагаем вам лучшие галстуки.\n\n"
                "✨ Наши преимущества:\n"
                "• 100% натуральный шелк\n"
                "• Эксклюзивный дизайн\n"
                "• Персональная консультация по стилю\n"
                "• Быстрая доставка\n"
                "• Гарантия качества\n\n"
                "🌐 *Новое!* Теперь вы можете заказывать и через веб-каталог!"
            ),
            'en': (
                "ℹ️ *About Us*\n\n"
                "🎩 *T1EUP - Premium Tie Store*\n\n"
                "With over 20 years of experience, we offer you the finest ties.\n\n"
                "✨ Our advantages:\n"
                "• 100% natural silk\n"
                "• Exclusive design\n"
                "• Personal style consultation\n"
                "• Fast delivery\n"
                "• Quality guarantee\n\n"
                "🌐 *New!* Now you can also order through our web catalog!"
            )
        }
        
        keyboard = [[InlineKeyboardButton(get_text(lang, 'back'), callback_data='back_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            about_text[lang],
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return MAIN_MENU
    
    async def back_to_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Return to main menu"""
        query = update.callback_query
        await query.answer()
        
        await query.delete_message()
        return await self.show_main_menu(update, context)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command"""
        lang = get_user_language(update.effective_user.id)
        help_text = {
            'kz': "ℹ️ Көмек үшін /start командасын қолданыңыз",
            'ru': "ℹ️ Для помощи используйте команду /start",
            'en': "ℹ️ For help, use the /start command"
        }
        await update.message.reply_text(help_text[lang])
    
    async def web_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Web command - direct link to web app"""
        lang = get_user_language(update.effective_user.id) or 'ru'
        
        web_text = {
            'kz': "🌐 *T1EUP Веб-каталог*\n\nВеб-каталогты ашу үшін төмендегі сілтемені басыңыз:",
            'ru': "🌐 *T1EUP Веб-каталог*\n\nНажмите на ссылку ниже, чтобы открыть веб-каталог:",
            'en': "🌐 *T1EUP Web Catalog*\n\nClick the link below to open the web catalog:"
        }
        
        keyboard = [[InlineKeyboardButton("🌐 Открыть веб-каталог", url=WEB_APP_URL)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            web_text[lang],
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    def run(self):
        """Run the bot"""
        logger.info("Starting T1EUP Tie Shop Bot with Web Integration...")
        self.application.run_polling()

if __name__ == '__main__':
    bot = TieShopBotWithWeb()
    bot.run()
