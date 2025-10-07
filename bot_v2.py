"""
Professional Telegram Bot for Tie Shop - Version 2
With card-based catalog navigation and full localization
"""

import os
import re
import logging
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv
from bot_translations import get_text
from database import (
    get_or_create_user, update_user_language, get_user_language, 
    Session, Order, User, Tie,
    migrate_ties_from_json, get_all_active_ties, get_tie_by_id,
    create_tie, update_tie, delete_tie, update_order_status, get_order_by_id,
    create_order, get_user_orders
)

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
# Get admin IDs from environment variable (comma-separated)
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
# Fallback to single ADMIN_ID for compatibility
if not ADMIN_IDS:
    admin_id = os.getenv('ADMIN_ID')
    if admin_id:
        ADMIN_IDS = [int(admin_id)]
PAYMENT_LINK = os.getenv('PAYMENT_LINK', 'https://kaspi.kz/pay')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
LANGUAGE_SELECTION = 0
MAIN_MENU = 1
CATALOG_BROWSING = 2
TIE_SELECTED = 3
CONFIRM_PURCHASE = 4
NAME = 5
SURNAME = 6
PHONE = 7
ADDRESS = 8
CHECKOUT = 9
PAYMENT = 10

# Import translations from separate file (already imported above)

class TieShopBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        # Migrate data from JSON to database on startup
        migrate_ties_from_json()
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
                    CallbackQueryHandler(self.show_support, pattern='^support$'),
                    CallbackQueryHandler(self.show_contacts, pattern='^contact$'),
                ],
                CATALOG_BROWSING: [
                    CallbackQueryHandler(self.select_tie_by_number, pattern='^tie_\d+$'),
                    CallbackQueryHandler(self.back_to_menu, pattern='^back_menu$'),
                ],
                TIE_SELECTED: [
                    CallbackQueryHandler(self.confirm_purchase, pattern='^confirm_yes$'),
                    CallbackQueryHandler(self.confirm_purchase, pattern='^confirm_no$'),
                ],
                NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message_input),
                    MessageHandler(filters.PHOTO, self.handle_catalog_photo)
                ],
                SURNAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message_input),
                    MessageHandler(filters.PHOTO, self.handle_catalog_photo)
                ],
                PHONE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message_input),
                    MessageHandler(filters.PHOTO, self.handle_catalog_photo)
                ],
                ADDRESS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message_input),
                    MessageHandler(filters.PHOTO, self.handle_catalog_photo)
                ],
                CHECKOUT: [
                    CallbackQueryHandler(self.process_payment, pattern='^pay_order$'),
                    CallbackQueryHandler(self.cancel_order, pattern='^cancel_order$'),
                ],
                PAYMENT: [
                    CallbackQueryHandler(self.payment_done, pattern='^payment_done$'),
                ],
            },
            fallbacks=[],
        )
        
        # Cancel command handler (highest priority - must be first)
        self.application.add_handler(CommandHandler('cancel', self.handle_cancel_command))
        
        self.application.add_handler(conv_handler)
        
        # Admin handlers
        self.application.add_handler(CallbackQueryHandler(self.admin_approve, pattern='^approve_'))
        self.application.add_handler(CallbackQueryHandler(self.admin_reject, pattern='^reject_'))
        self.application.add_handler(CallbackQueryHandler(self.admin_set_delivery, pattern='^setdelivery_'))
        self.application.add_handler(CallbackQueryHandler(self.admin_mark_delivered, pattern='^delivered_'))
        self.application.add_handler(CallbackQueryHandler(self.user_confirm_receipt, pattern='^received_'))
        # admin_input_days is handled in specific conversation states
        self.application.add_handler(CommandHandler('boss', self.boss_panel))
        self.application.add_handler(CommandHandler('debug', self.debug_logs))
        self.application.add_handler(CommandHandler('logs', self.show_logs))
        self.application.add_handler(CommandHandler('db', self.check_database))
        self.application.add_handler(CommandHandler('test_update', self.test_update))
        self.application.add_handler(CommandHandler('migrate', self.force_migrate))
        self.application.add_handler(CommandHandler('catalog', self.show_catalog_command))
        self.application.add_handler(CommandHandler('sync', self.sync_json_db))
        self.application.add_handler(CommandHandler('admin_test', self.admin_test))
        self.application.add_handler(CommandHandler('edit_test', self.edit_test))
        self.application.add_handler(CommandHandler('test_edit', self.test_edit))
        self.application.add_handler(CommandHandler('test_conflict', self.test_conflict))
        self.application.add_handler(CommandHandler('force_edit', self.force_edit))
        self.application.add_handler(CommandHandler('clear_all', self.clear_all_data))
        self.application.add_handler(CommandHandler('reset_ties', self.reset_ties))
        self.application.add_handler(CallbackQueryHandler(self.boss_show_orders, pattern='^boss_orders$'))
        self.application.add_handler(CallbackQueryHandler(self.boss_monitor, pattern='^boss_monitor$'))
        self.application.add_handler(CallbackQueryHandler(self.boss_report, pattern='^boss_report$'))
        self.application.add_handler(CallbackQueryHandler(self.boss_catalog_menu, pattern='^boss_catalog$'))
        self.application.add_handler(CallbackQueryHandler(self.boss_add_tie, pattern='^add_tie$'))
        self.application.add_handler(CallbackQueryHandler(self.boss_edit_tie, pattern='^edit_tie_\d+$'))
        self.application.add_handler(CallbackQueryHandler(self.boss_delete_tie, pattern='^delete_tie_\d+$'))
        self.application.add_handler(CallbackQueryHandler(self.boss_list_ties, pattern='^list_ties$'))
        self.application.add_handler(CallbackQueryHandler(self.handle_edit_field, pattern='^edit_field_'))
        self.application.add_handler(CallbackQueryHandler(self.cancel_edit, pattern='^cancel_edit$'))
        self.application.add_handler(CallbackQueryHandler(self.boss_broadcast_menu, pattern='^boss_broadcast$'))
        self.application.add_handler(CallbackQueryHandler(self.broadcast_all, pattern='^broadcast_all$'))
        self.application.add_handler(CallbackQueryHandler(self.broadcast_one, pattern='^broadcast_one$'))
        self.application.add_handler(CallbackQueryHandler(self.select_user, pattern='^select_user_'))
        self.application.add_handler(CallbackQueryHandler(self.cancel_broadcast, pattern='^cancel_broadcast$'))
        self.application.add_handler(CallbackQueryHandler(self.boss_back, pattern='^boss_back$'))
        
        # IMPORTANT: Add message handlers for catalog input (must be last)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_catalog_input))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_catalog_photo))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start command handler"""
        logger.info(f"START command from user {update.effective_user.id} (@{update.effective_user.username})")
        user = update.effective_user
        get_or_create_user(user.id, user.username)
        
        # Set Russian as default language
        context.user_data['language'] = 'ru'
        update_user_language(user.id, 'ru')
        
        # Go directly to main menu
        return await self.show_main_menu(update, context)
    
    async def language_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle language selection"""
        query = update.callback_query
        logger.info(f"LANGUAGE_SELECTED callback from user {update.effective_user.id}: {query.data}")
        await query.answer()
        
        lang = query.data.replace('lang_', '')
        user_id = update.effective_user.id
        
        update_user_language(user_id, lang)
        context.user_data['language'] = lang
        
        await query.edit_message_text(get_text(lang, 'welcome'))
        
        return await self.show_main_menu(update, context)
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show main menu"""
        logger.info(f"SHOW_MAIN_MENU for user {update.effective_user.id}")
        lang = 'ru'  # Force Russian
        context.user_data['language'] = 'ru'
        
        keyboard = [
            [InlineKeyboardButton("🛍️ Каталог", callback_data='catalog')],
            [InlineKeyboardButton("📦 Мои заказы", callback_data='my_orders')],
            [InlineKeyboardButton("📞 Контакты", callback_data='contact')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = "Выберите действие:"
        
        if update.callback_query:
            await update.callback_query.message.reply_text(
                message_text,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                message_text,
                reply_markup=reply_markup
            )
        
        return MAIN_MENU
    
    async def show_catalog(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show all ties with full info and select buttons"""
        query = update.callback_query
        logger.info(f"SHOW_CATALOG callback from user {update.effective_user.id}")
        await query.answer()
        
        lang = 'ru'  # Force Russian
        
        # Get ties from database
        ties = get_all_active_ties()
        logger.info(f"Retrieved {len(ties)} ties from database")
        
        if not ties:
            logger.warning("No ties found in database")
            await query.message.reply_text("Каталог пуст. Товары скоро появятся!")
            return MAIN_MENU
        
        # Store message IDs for later deletion
        context.user_data['catalog_messages'] = []
        
        # Send each tie as a separate message with photo and full info
        for i, tie in enumerate(ties):
            # Create full info text
            info_text = f"""
🎯 *{tie.name_ru}*

🎨 *Цвет:* {tie.color_ru}
🧵 *Материал:* {tie.material_ru}
💰 *Цена:* {tie.price:,.0f} тг

📝 {tie.description_ru}

🚚 Доставка: 15 дней

✅ *Подтвердить покупку {tie.name_ru}?*
"""
            
            # Create button for this tie
            keyboard = [[
                InlineKeyboardButton("✅ Выбрать", callback_data=f'tie_{tie.id}')
            ]]
            
            # Add back button only on the last tie
            if i == len(ties) - 1:
                keyboard.append([
                    InlineKeyboardButton("🔙 Главное меню", callback_data='back_menu')
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send photo with caption and button
            if tie.image_path and os.path.exists(tie.image_path):
                with open(tie.image_path, 'rb') as photo:
                    message = await query.message.reply_photo(
                        photo=photo,
                        caption=info_text,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                    context.user_data['catalog_messages'].append(message.message_id)
            else:
                message = await query.message.reply_text(
                    info_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                context.user_data['catalog_messages'].append(message.message_id)
        
        return CATALOG_BROWSING
    
    async def back_to_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Return to main menu from catalog"""
        query = update.callback_query
        await query.answer()
        
        # Delete catalog messages if they exist
        if 'catalog_messages' in context.user_data:
            for msg_id in context.user_data['catalog_messages']:
                try:
                    await context.bot.delete_message(
                        chat_id=query.message.chat_id,
                        message_id=msg_id
                    )
                except:
                    pass
            context.user_data['catalog_messages'] = []
        
        return await self.show_main_menu(update, context)
    
    async def show_tie_card(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show single tie card"""
        query = update.callback_query
        
        position = context.user_data.get('catalog_position', 0)
        ties = get_all_active_ties()
        
        if position >= len(ties):
            position = 0
        
        tie = ties[position]
        
        # Create navigation keyboard
        keyboard = []
        
        # Add navigation buttons if there are multiple ties
        if len(ties) > 1:
            nav_buttons = []
            if position > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data='prev_tie'))
            nav_buttons.append(InlineKeyboardButton(f"{position+1}/{len(ties)}", callback_data='current'))
            if position < len(ties) - 1:
                nav_buttons.append(InlineKeyboardButton("➡️ Вперед", callback_data='next_tie'))
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("✅ Выбрать", callback_data=f'tie_{tie.id}')])
        keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data='back_menu')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CATALOG_BROWSING
    
    async def navigate_catalog(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Navigate through catalog"""
        query = update.callback_query
        await query.answer()
        
        position = context.user_data.get('catalog_position', 0)
        ties = get_all_active_ties()
        if position >= len(ties):
            return CATALOG_BROWSING
        tie = ties[position]
        
        # Create card text
        card_text = f"""
🎯 *{tie.name_ru}*

🎨 *{get_text(lang, 'color')}:* {tie.color_ru}
🧵 *{get_text(lang, 'material')}:* {tie.material_ru}
💰 *{get_text(lang, 'price')}:* {tie.price:,.0f} {get_text(lang, 'currency')}

📝 {tie.description_ru}

{get_text(lang, 'delivery')}

{get_text(lang, 'catalog_page')} {position + 1}/{len(ties)}
"""
        
        # Create navigation buttons
        keyboard = []
        
        # Navigation row
        nav_row = []
        if position > 0:
            nav_row.append(InlineKeyboardButton(get_text(lang, 'previous'), callback_data='prev_tie'))
        nav_row.append(InlineKeyboardButton(get_text(lang, 'select'), callback_data='select_tie'))
        if position < len(ties) - 1:
            nav_row.append(InlineKeyboardButton(get_text(lang, 'next'), callback_data='next_tie'))
        keyboard.append(nav_row)
        
        # Back button
        keyboard.append([InlineKeyboardButton(get_text(lang, 'main_menu'), callback_data='back_menu')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send or update message with photo
        image_path = tie.image_path
        
        if update.callback_query:
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as photo:
                    # Delete old message and send new one with photo
                    await update.callback_query.message.delete()
                    await update.callback_query.message.chat.send_photo(
                        photo=photo,
                        caption=card_text,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
            else:
                await update.callback_query.edit_message_text(
                    card_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        
        return CATALOG_BROWSING
    
    async def next_tie(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show next tie"""
        query = update.callback_query
        await query.answer()
        
        position = context.user_data.get('catalog_position', 0)
        ties = get_all_active_ties()
        if position < len(ties) - 1:
            context.user_data['catalog_position'] = position + 1
        
        return await self.show_tie_card(update, context)
    
    async def prev_tie(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show previous tie"""
        query = update.callback_query
        await query.answer()
        
        position = context.user_data.get('catalog_position', 0)
        if position > 0:
            context.user_data['catalog_position'] = position - 1
        
        return await self.show_tie_card(update, context)
    
    async def select_tie_by_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Select tie by number"""
        query = update.callback_query
        logger.info(f"SELECT_TIE_BY_NUMBER callback from user {update.effective_user.id}: {query.data}")
        await query.answer()
        
        lang = 'ru'  # Force Russian
        tie_id = int(query.data.replace('tie_', ''))
        tie = get_tie_by_id(tie_id)
        
        if not tie:
            await query.message.reply_text("Товар не найден")
            return CATALOG_BROWSING
        
        context.user_data['selected_tie'] = tie
        context.user_data['selected_tie_id'] = tie_id
        
        # Delete all other catalog messages except the selected one
        if 'catalog_messages' in context.user_data:
            for msg_id in context.user_data['catalog_messages']:
                if msg_id != query.message.message_id:
                    try:
                        await context.bot.delete_message(
                            chat_id=query.message.chat_id,
                            message_id=msg_id
                        )
                    except:
                        pass  # Message might already be deleted
        
        # Update the selected tie message with confirmation buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ Да", callback_data='confirm_yes'),
                InlineKeyboardButton("❌ Нет", callback_data='confirm_no')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Create beautiful tie card
        info_text = f"""
🛍️ *ВЫБРАННЫЙ ТОВАР*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 *{tie.name_ru}*

🎨 *Цвет:* {tie.color_ru}
🧵 *Материал:* {tie.material_ru}
💰 *Цена:* *{tie.price:,.0f} тг*

📝 *Описание:*
{tie.description_ru}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚚 *Доставка:* 15 дней по всему Казахстану
💳 *Оплата:* Наличными при получении

✅ *Подтвердить покупку {tie.name_ru}?*
"""
        
        # Check if the message has a photo (caption) or just text
        try:
            # Try to edit caption first (for messages with photos)
            await query.edit_message_caption(
                caption=info_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except:
            # If that fails, try to edit text (for messages without photos)
            try:
                await query.edit_message_text(
                    text=info_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Error editing message: {e}")
                # As a fallback, send a new message
                await query.message.reply_text(
                    info_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        
        return TIE_SELECTED
    
    async def confirm_purchase(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start order process"""
        query = update.callback_query
        await query.answer()
        
        logger.info(f"=== CONFIRM_PURCHASE START ===")
        logger.info(f"Query data: {query.data}")
        logger.info(f"User data: {context.user_data}")
        
        lang = 'ru'  # Force Russian
        
        if query.data == 'confirm_yes':
            logger.info(f"User confirmed purchase, requesting name")
            context.user_data['current_state'] = NAME
            await query.message.reply_text(
                "💳 *Введите имя плательщика:*\n\n"
                "_Укажите имя человека, который будет производить оплату "
                "(это может быть родитель, если оплачивает за студента)_",
                parse_mode='Markdown'
            )
            logger.info(f"Returning NAME state")
            return NAME
        else:
            logger.info(f"User cancelled purchase")
            await query.message.reply_text("Заказ отменен")
            return await self.show_main_menu(update, context)
    
    async def handle_message_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Универсальный обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        
        # Проверяем, есть ли фото в сообщении
        if update.message.photo:
            logger.info(f"Photo received in handle_message_input for user {user_id}")
            await self.handle_catalog_photo(update, context)
            return context.user_data.get('current_state', NAME)
        
        # Проверяем, есть ли текст в сообщении
        if not update.message.text:
            logger.warning(f"No text in message for user {user_id}")
            return context.user_data.get('current_state', NAME)
        
        text = update.message.text
        
        logger.info(f"=== HANDLE_MESSAGE_INPUT START ===")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Message text: '{text}'")
        logger.info(f"User data: {context.user_data}")
        
        # Проверяем режим подтверждения очистки данных (САМЫЙ ВЫСШИЙ ПРИОРИТЕТ)
        if user_id in ADMIN_IDS and context.user_data.get('waiting_for_clear_confirmation'):
            if text == 'CONFIRM_CLEAR_ALL':
                await update.message.reply_text("🗑️ Очищаю все данные...")
                
                from database import clear_all_data
                if clear_all_data():
                    await update.message.reply_text(
                        "✅ **ДАННЫЕ ОЧИЩЕНЫ!**\n\n"
                        "База данных готова для запуска на рынок:\n"
                        "• Все заказы удалены\n"
                        "• Все пользователи удалены\n"
                        "• Каталог товаров сохранен\n\n"
                        "🚀 **Система готова к работе!**"
                    )
                else:
                    await update.message.reply_text("❌ Ошибка при очистке данных")
                
                context.user_data['waiting_for_clear_confirmation'] = False
                return
            elif text == 'CANCEL':
                await update.message.reply_text("❌ Очистка данных отменена")
                context.user_data['waiting_for_clear_confirmation'] = False
                return
            else:
                await update.message.reply_text(
                    "⚠️ Неверная команда. Введите:\n"
                    "• **CONFIRM_CLEAR_ALL** - для подтверждения\n"
                    "• **CANCEL** - для отмены"
                )
                return
        
        # Проверяем режим ввода дней доставки для админа (ВЫСШИЙ ПРИОРИТЕТ)
        if user_id in ADMIN_IDS and context.user_data.get('pending_delivery_order'):
            logger.info(f"Admin input days mode, delegating to admin_input_days")
            await self.admin_input_days(update, context)
            return context.user_data.get('current_state', NAME)
        
        # Проверяем режим редактирования (ВЫСШИЙ ПРИОРИТЕТ)
        if context.user_data.get('editing_active'):
            logger.info(f"User in editing mode, delegating to handle_edit_input")
            logger.info(f"Editing tie: {context.user_data.get('editing_tie')}")
            logger.info(f"Editing field: {context.user_data.get('editing_field')}")
            
            # Отправляем отладочное сообщение админу
            if user_id in ADMIN_IDS:
                await update.message.reply_text(
                    f"🔍 ОТЛАДКА: Режим редактирования активен\n"
                    f"Товар ID: {context.user_data.get('editing_tie')}\n"
                    f"Поле: {context.user_data.get('editing_field')}\n"
                    f"Введенный текст: '{text}'"
                )
            
            result = await self.handle_edit_input(update, context)
            logger.info(f"handle_edit_input returned: {result}")
            return context.user_data.get('current_state', NAME)
        
        # Проверяем режим добавления товара (НИЗШИЙ ПРИОРИТЕТ)
        if context.user_data.get('adding_tie'):
            logger.info(f"User in adding tie mode, delegating to handle_catalog_input")
            await self.handle_catalog_input(update, context)
            return context.user_data.get('current_state', NAME)
        
        # Проверяем режим рассылки
        if context.user_data.get('broadcast_active'):
            logger.info(f"User in broadcast mode, delegating to handle_broadcast_message")
            await self.handle_broadcast_message(update, context)
            return context.user_data.get('current_state', NAME)
        
        # Обычная обработка заказа
        current_state = context.user_data.get('current_state', NAME)
        
        if current_state == NAME:
            return await self.receive_name(update, context)
        elif current_state == SURNAME:
            return await self.receive_surname(update, context)
        elif current_state == PHONE:
            return await self.receive_phone(update, context)
        elif current_state == ADDRESS:
            return await self.receive_address(update, context)
        elif current_state is None:
            # Если состояние None, но нет активных режимов, игнорируем сообщение
            logger.info(f"Current state is None and no active modes, ignoring message")
            return NAME
        else:
            logger.warning(f"Unknown current state: {current_state}")
            return NAME

    async def receive_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive and validate name"""
        user_id = update.effective_user.id
        text = update.message.text
        
        logger.info(f"=== RECEIVE_NAME START ===")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Message text: '{text}'")
        logger.info(f"User data: {context.user_data}")
        
        lang = 'ru'  # Force Russian
        name = update.message.text.strip()
        
        # Check if user is in adding tie mode
        if context.user_data.get('adding_tie'):
            logger.info(f"User in adding tie mode, delegating to handle_catalog_input")
            await self.handle_catalog_input(update, context)
            return NAME
        
        # Check if user is in editing mode
        if context.user_data.get('editing_active'):
            logger.info(f"User in editing mode, delegating to handle_edit_input")
            await self.handle_edit_input(update, context)
            return NAME
        
        # Check if user is in broadcast mode
        if context.user_data.get('broadcast_active'):
            logger.info(f"User in broadcast mode, delegating to handle_broadcast_message")
            await self.handle_broadcast_message(update, context)
            return NAME
        
        # Note: Removed isdigit() check as names should be processed normally
        
        if len(name) < 2:
            await update.message.reply_text("Имя слишком короткое. Введите полное имя:")
            return NAME
        
        if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s-]+$', name):
            await update.message.reply_text("Используйте только буквы. Введите имя:")
            return NAME
        
        context.user_data['recipient_name'] = name
        context.user_data['current_state'] = SURNAME
        await update.message.reply_text(
            "👤 *Введите фамилию плательщика:*\n\n"
            "_Укажите фамилию человека, который будет производить оплату_",
            parse_mode='Markdown'
        )
        
        return SURNAME
    
    async def receive_surname(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive and validate surname"""
        lang = 'ru'  # Force Russian
        surname = update.message.text.strip()
        
        # Check if user is in adding tie mode
        if context.user_data.get('adding_tie'):
            logger.info(f"User in adding tie mode, delegating to handle_catalog_input")
            await self.handle_catalog_input(update, context)
            return SURNAME
        
        # Check if user is in editing mode
        if context.user_data.get('editing_active'):
            logger.info(f"User in editing mode, delegating to handle_edit_input")
            await self.handle_edit_input(update, context)
            return SURNAME
        
        # Check if user is in broadcast mode
        if context.user_data.get('broadcast_active'):
            logger.info(f"User in broadcast mode, delegating to handle_broadcast_message")
            await self.handle_broadcast_message(update, context)
            return SURNAME
        
        # Note: Removed isdigit() check as surnames should be processed normally
        
        if len(surname) < 2:
            await update.message.reply_text("Фамилия слишком короткая. Введите полную фамилию:")
            return SURNAME
        
        if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s-]+$', surname):
            await update.message.reply_text("Используйте только буквы. Введите фамилию:")
            return SURNAME
        
        context.user_data['recipient_surname'] = surname
        context.user_data['current_state'] = PHONE
        await update.message.reply_text(
            "📱 *Введите номер телефона плательщика:*\n\n"
            "_Формат: +7XXXXXXXXXX_\n"
            "_Этот номер будет использован для связи по вопросам оплаты_",
            parse_mode='Markdown'
        )
        
        return PHONE
    
    async def receive_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive and validate phone"""
        user_id = update.effective_user.id
        text = update.message.text
        
        logger.info(f"=== RECEIVE_PHONE START ===")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Message text: '{text}'")
        logger.info(f"User data: {context.user_data}")
        
        lang = 'ru'  # Force Russian
        phone = update.message.text.strip()
        
        # Check if user is in adding tie mode
        if context.user_data.get('adding_tie'):
            logger.info(f"User in adding tie mode, delegating to handle_catalog_input")
            await self.handle_catalog_input(update, context)
            return PHONE
        
        # Check if user is in editing mode
        if context.user_data.get('editing_active'):
            logger.info(f"User in editing mode, delegating to handle_edit_input")
            await self.handle_edit_input(update, context)
            return PHONE
        
        # Check if user is in broadcast mode
        if context.user_data.get('broadcast_active'):
            logger.info(f"User in broadcast mode, delegating to handle_broadcast_message")
            await self.handle_broadcast_message(update, context)
            return PHONE
        
        # Note: Removed isdigit() check as phone numbers should be processed normally
        
        phone_digits = re.sub(r'\D', '', phone)
        
        if not re.match(r'^(7|8)?7\d{9}$', phone_digits):
            await update.message.reply_text("Неверный формат телефона. Введите корректный номер:")
            return PHONE
        
        if phone_digits.startswith('8'):
            phone_digits = '7' + phone_digits[1:]
        elif not phone_digits.startswith('7'):
            phone_digits = '7' + phone_digits
        
        formatted_phone = f"+{phone_digits[0]} {phone_digits[1:4]} {phone_digits[4:7]} {phone_digits[7:9]} {phone_digits[9:11]}"
        context.user_data['recipient_phone'] = f'+{phone_digits}'
        context.user_data['current_state'] = ADDRESS
        await update.message.reply_text("Введите ваш адрес доставки:")
        
        return ADDRESS
    
    async def receive_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive address and show payment options"""
        user_id = update.effective_user.id
        text = update.message.text
        
        logger.info(f"=== RECEIVE_ADDRESS START ===")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Message text: '{text}'")
        logger.info(f"User data: {context.user_data}")
        
        lang = 'ru'  # Force Russian
        address = update.message.text.strip()
        
        if len(address) < 5:
            await update.message.reply_text("Адрес слишком короткий. Введите полный адрес:")
            return ADDRESS
        
        context.user_data['delivery_address'] = address
        
        # Show order summary
        tie = context.user_data['selected_tie']
        
        summary = f"""
{get_text(lang, 'order_summary')}

🎯 *{get_text(lang, 'product')}:* {tie.name_ru}
💰 *{get_text(lang, 'price')}:* {tie.price:,.0f} {get_text(lang, 'currency')}

👤 *{get_text(lang, 'recipient')}:* {context.user_data['recipient_name']} {context.user_data['recipient_surname']}
📱 *{get_text(lang, 'phone')}:* {context.user_data['recipient_phone']}
📍 *{get_text(lang, 'address')}:* {context.user_data['delivery_address']}

💳 *{get_text(lang, 'total')}:* {tie.price:,.0f} {get_text(lang, 'currency')}
"""
        
        keyboard = [
            [InlineKeyboardButton(get_text(lang, 'pay'), callback_data='pay_order')],
            [InlineKeyboardButton(get_text(lang, 'cancel'), callback_data='cancel_order')]
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
        
        lang = context.user_data.get('language', 'ru')
        tie = context.user_data['selected_tie']
        
        # Create order
        order_data = {
            'user_telegram_id': update.effective_user.id,
            'tie_id': tie.id,
            'tie_name': tie.name_ru,
            'price': tie.price,
            'recipient_name': context.user_data['recipient_name'],
            'recipient_surname': context.user_data['recipient_surname'],
            'recipient_phone': context.user_data['recipient_phone'],
            'delivery_address': context.user_data['delivery_address'],
            'status': 'pending_payment'
        }
        
        order = create_order(order_data)
        context.user_data['order_id'] = order.id
        
        # Payment instructions
        payment_text = f"""
{get_text(lang, 'payment_instruction')}

*{get_text(lang, 'order')} #{order.id}*
*{get_text(lang, 'total')}:* {tie.price:,.0f} {get_text(lang, 'currency')}
"""
        
        keyboard = [
            [InlineKeyboardButton(get_text(lang, 'pay_button'), url=PAYMENT_LINK)],
            [InlineKeyboardButton(get_text(lang, 'paid_button'), callback_data='payment_done')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            payment_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return PAYMENT
    
    async def payment_done(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle payment confirmation"""
        query = update.callback_query
        await query.answer()
        
        lang = context.user_data.get('language', 'ru')
        order_id = context.user_data['order_id']
        tie = context.user_data['selected_tie']
        
        # Update order status
        update_order_status(order_id, 'pending_admin_review')
        
        # Send notification to all admins
        admin_message = f"""
🆕 *Новый заказ #{order_id}*

👤 *Клиент:* {context.user_data['recipient_name']} {context.user_data['recipient_surname']}
📱 *Телефон:* {context.user_data['recipient_phone']}
📍 *Адрес:* {context.user_data['delivery_address']}

🎯 *Товар:* {tie.name_ru}
💰 *Сумма:* {tie.price:,.0f} тг

⏳ *Статус:* Ожидает проверки чека
"""
        
        # Create admin buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ Подтвердить заказ", callback_data=f'approve_{order_id}'),
                InlineKeyboardButton("❌ Отклонить заказ", callback_data=f'reject_{order_id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send to all admins
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Failed to send notification to admin {admin_id}: {e}")
        
        await query.message.reply_text(
            get_text(lang, 'order_sent'),
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
    
    async def show_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show user orders"""
        query = update.callback_query
        await query.answer()
        
        lang = context.user_data.get('language', 'ru')
        user_id = update.effective_user.id
        orders = get_user_orders(user_id)
        
        if not orders:
            await query.message.reply_text(get_text(lang, 'no_orders'))
        else:
            orders_text = f"{get_text(lang, 'your_orders')}\n\n"
            
            status_map = {
                'pending_payment': '⏳ Ожидает оплаты',
                'pending_admin_review': '🔍 На проверке',
                'confirmed': '✅ Подтвержден',
                'in_delivery': '🚚 В доставке',
                'delivered': '📦 Доставлен',
                'completed': '✔️ Завершен',
                'rejected': '❌ Отклонен'
            }
            
            for order in orders:
                status_text = status_map.get(order.status, order.status)
                orders_text += f"📦 *{get_text(lang, 'order')} #{order.id}*\n"
                orders_text += f"🎯 {order.tie_name}\n"
                orders_text += f"💰 {order.price:,} {get_text(lang, 'currency')}\n"
                orders_text += f"📊 {status_text}\n"
                orders_text += f"📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            
            await query.message.reply_text(orders_text, parse_mode='Markdown')
        
        return await self.show_main_menu(update, context)
    
    async def show_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show support info"""
        query = update.callback_query
        await query.answer()
        
        lang = context.user_data.get('language', 'ru')
        
        await query.message.reply_text(
            get_text(lang, 'support_text'),
            parse_mode='Markdown'
        )
        
        return await self.show_main_menu(update, context)
    
    async def show_contacts(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show contact info"""
        query = update.callback_query
        await query.answer()
        
        lang = context.user_data.get('language', 'ru')
        
        await query.message.reply_text(
            get_text(lang, 'support_text'),
            parse_mode='Markdown'
        )
        
        return await self.show_main_menu(update, context)
    
    async def back_to_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Go back to main menu"""
        return await self.show_main_menu(update, context)
    
    async def cancel_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel order"""
        query = update.callback_query
        await query.answer()
        
        lang = context.user_data.get('language', 'ru')
        
        await query.message.reply_text(
            get_text(lang, 'order_cancelled'),
            parse_mode='Markdown'
        )
        
        return await self.show_main_menu(update, context)
    
    async def debug_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Debug command to show current user data and logs"""
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        user_data = context.user_data
        debug_info = f"""
🔍 **Отладочная информация для пользователя {user_id}**

**Текущие данные пользователя:**
```json
{json.dumps(user_data, indent=2, ensure_ascii=False)}
```

**Активные режимы:**
• Редактирование: {user_data.get('editing_active', False)}
• Добавление товара: {user_data.get('adding_tie', False)}
• Рассылка: {user_data.get('broadcast_active', False)}
• Ожидание доставки: {user_data.get('pending_delivery_order', None)}

**Текущее состояние:**
• Состояние: {user_data.get('current_state', 'None')}
• Редактируемый товар: {user_data.get('editing_tie', 'None')}
• Редактируемое поле: {user_data.get('editing_field', 'None')}
• Шаг добавления: {user_data.get('add_step', 'None')}
"""
        
        await update.message.reply_text(debug_info, parse_mode='Markdown')
    
    async def show_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show recent logs for debugging"""
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        # Создаем простой лог-файл для отладки
        log_info = f"""
📋 **Последние действия бота**

**Текущее время:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Статус бота:** ✅ Активен

**Доступные команды для отладки:**
• `/debug` - показать данные пользователя
• `/logs` - показать эту информацию
• `/boss` - панель администратора

**Для просмотра подробных логов:**
Логи выводятся в консоль (терминал) где запущен бот.
Ищите сообщения с префиксом "=== HANDLE_MESSAGE_INPUT START ===" и "=== HANDLE_EDIT_INPUT START ==="

**Если проблема с изменением цены:**
1. Выберите товар для редактирования
2. Нажмите "💰 Изменить цену"
3. Введите новую цену
4. Проверьте логи в консоли
"""
        
        await update.message.reply_text(log_info, parse_mode='Markdown')
    
    async def check_database(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Check database status and show ties"""
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        try:
            # Получаем все товары из базы данных
            ties = get_all_active_ties()
            
            db_info = f"""
🗄️ **Состояние базы данных**

**Всего товаров:** {len(ties)}

**Список товаров:**
"""
            
            for tie in ties:
                db_info += f"""
• **ID {tie.id}:** {tie.name_ru}
  Цена: {tie.price} тг
  Цвет: {tie.color_ru}
  Активен: {'✅' if tie.is_active else '❌'}
"""
            
            if len(db_info) > 4000:  # Telegram limit
                db_info = db_info[:4000] + "\n... (обрезано)"
            
            await update.message.reply_text(db_info, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при проверке базы данных: {str(e)}")
    
    async def test_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Test database update functionality"""
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        try:
            # Получаем первый товар для тестирования
            ties = get_all_active_ties()
            if not ties:
                await update.message.reply_text("❌ Нет товаров в базе данных")
                return
            
            test_tie = ties[0]
            original_price = test_tie.price
            new_price = original_price + 100
            
            await update.message.reply_text(
                f"🧪 **Тестирование обновления базы данных**\n\n"
                f"Товар: {test_tie.name_ru}\n"
                f"Текущая цена: {original_price}\n"
                f"Новая цена: {new_price}",
                parse_mode='Markdown'
            )
            
            # Тестируем обновление
            update_result = update_tie(test_tie.id, price=new_price)
            
            if update_result:
                # Проверяем результат
                updated_tie = get_tie_by_id(test_tie.id)
                if updated_tie and updated_tie.price == new_price:
                    await update.message.reply_text(
                        f"✅ **Тест успешен!**\n\n"
                        f"Цена обновлена с {original_price} на {updated_tie.price}",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(
                        f"❌ **Тест не прошел!**\n\n"
                        f"Ожидалось: {new_price}\n"
                        f"Получено: {updated_tie.price if updated_tie else 'None'}",
                        parse_mode='Markdown'
                    )
            else:
                await update.message.reply_text("❌ **Ошибка при обновлении базы данных**")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при тестировании: {str(e)}")
    
    async def force_migrate(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Force migration of ties from JSON to database"""
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        try:
            # Очищаем существующие товары
            from database import Session, Tie
            session = Session()
            session.query(Tie).delete()
            session.commit()
            session.close()
            
            # Принудительно мигрируем данные
            migrate_ties_from_json()
            
            # Проверяем результат
            ties = get_all_active_ties()
            
            await update.message.reply_text(
                f"✅ **Миграция завершена!**\n\n"
                f"Загружено товаров: {len(ties)}\n\n"
                f"Используйте `/db` для проверки",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при миграции: {str(e)}")
    
    async def sync_json_db(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Sync JSON changes with database"""
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        try:
            # Загружаем данные из JSON
            import json
            with open('ties_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            from database import Session, Tie
            session = Session()
            
            # Получаем существующие товары
            existing_ties = {tie.id: tie for tie in session.query(Tie).all()}
            
            updated_count = 0
            created_count = 0
            
            # Обрабатываем каждый товар из JSON
            for i, tie_data in enumerate(data['ties']):
                # Преобразуем строковый ID в числовой
                tie_id = i + 1  # 1, 2, 3, 4, 5
                
                # Подготавливаем данные для обновления
                tie_update_data = {
                    'name_ru': tie_data['name'].get('ru', ''),
                    'name_kz': tie_data['name'].get('kz', ''),
                    'name_en': tie_data['name'].get('en', ''),
                    'color_ru': tie_data['color'].get('ru', ''),
                    'color_kz': tie_data['color'].get('kz', ''),
                    'color_en': tie_data['color'].get('en', ''),
                    'material_ru': tie_data['material'].get('ru', '100% шелк'),
                    'material_kz': tie_data['material'].get('kz', '100% жібек'),
                    'material_en': tie_data['material'].get('en', '100% silk'),
                    'description_ru': tie_data['description'].get('ru', ''),
                    'description_kz': tie_data['description'].get('kz', ''),
                    'description_en': tie_data['description'].get('en', ''),
                    'price': tie_data.get('price', 1500),
                    'image_path': tie_data.get('image', ''),
                    'is_active': True
                }
                
                if tie_id in existing_ties:
                    # Обновляем существующий товар
                    existing_tie = existing_ties[tie_id]
                    for key, value in tie_update_data.items():
                        setattr(existing_tie, key, value)
                    updated_count += 1
                else:
                    # Создаем новый товар
                    new_tie = Tie(
                        id=tie_id,
                        **tie_update_data
                    )
                    session.add(new_tie)
                    created_count += 1
            
            session.commit()
            session.close()
            
            # Проверяем результат
            ties = get_all_active_ties()
            
            await update.message.reply_text(
                f"✅ **Синхронизация завершена!**\n\n"
                f"📊 Статистика:\n"
                f"• Обновлено товаров: {updated_count}\n"
                f"• Создано товаров: {created_count}\n"
                f"• Всего товаров в БД: {len(ties)}\n\n"
                f"Используйте `/db` для проверки",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при синхронизации: {str(e)}")
    
    async def admin_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Test admin functions"""
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        # Получаем заказы для тестирования
        from database import Session, Order
        session = Session()
        orders = session.query(Order).filter_by(status='pending_admin_review').all()
        session.close()
        
        if not orders:
            await update.message.reply_text(
                "📋 **Тест админских функций**\n\n"
                "❌ Нет заказов для тестирования\n"
                "Статус: pending_admin_review\n\n"
                "Создайте заказ для тестирования админских функций",
                parse_mode='Markdown'
            )
            return
        
        test_info = f"""
🧪 **Тест админских функций**

📊 **Статистика заказов:**
• Всего заказов: {len(orders)}
• Ожидающих подтверждения: {len([o for o in orders if o.status == 'pending_admin_review'])}

🔧 **Доступные функции:**
• ✅ Подтвердить заказ
• ❌ Отклонить заказ  
• 📅 Установить доставку
• ✅ Отметить как доставленный

📋 **Заказы для тестирования:**
"""
        
        for i, order in enumerate(orders[:5]):  # Показываем первые 5 заказов
            test_info += f"\n• Заказ #{order.id}: {order.tie_name} - {order.status}"
        
        if len(orders) > 5:
            test_info += f"\n• ... и еще {len(orders) - 5} заказов"
        
        test_info += f"""

💡 **Для тестирования:**
1. Используйте кнопку "Мониторинг заказов" в админ панели
2. Или создайте новый заказ и протестируйте его обработку
"""
        
        await update.message.reply_text(test_info, parse_mode='Markdown')
    
    async def edit_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Test editing functions"""
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        # Получаем товары для тестирования
        ties = get_all_active_ties()
        
        if not ties:
            await update.message.reply_text(
                "📋 **Тест редактирования товаров**\n\n"
                "❌ Нет товаров для тестирования\n\n"
                "Сначала добавьте товары в каталог",
                parse_mode='Markdown'
            )
            return
        
        test_info = f"""
🧪 **Тест редактирования товаров**

📊 **Статистика товаров:**
• Всего товаров: {len(ties)}

🔧 **Доступные функции редактирования:**
• 📝 Изменить название
• 🎨 Изменить цвет  
• 💰 Изменить цену
• 📄 Изменить описание
• 🖼️ Изменить фото

📋 **Товары для тестирования:**
"""
        
        for i, tie in enumerate(ties[:5]):  # Показываем первые 5 товаров
            test_info += f"\n• {i+1}. {tie.name_ru} (ID: {tie.id}) - {tie.price} тг"
        
        if len(ties) > 5:
            test_info += f"\n• ... и еще {len(ties) - 5} товаров"
        
        test_info += f"""

💡 **Для тестирования редактирования:**
1. Используйте команду `/boss` → "Управление каталогом" → "Список товаров"
2. Выберите товар для редактирования
3. Выберите поле для изменения
4. Введите новое значение

🔍 **Отладочные команды:**
• `/debug` - показать данные пользователя
• `/db` - проверить базу данных
• `/catalog` - показать каталог
"""
        
        await update.message.reply_text(test_info, parse_mode='Markdown')
    
    async def test_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Test editing a specific tie"""
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        # Получаем первый товар для тестирования
        ties = get_all_active_ties()
        if not ties:
            await update.message.reply_text("❌ Нет товаров для тестирования")
            return
        
        test_tie = ties[0]
        
        # Тестируем обновление цены
        test_price = 9999
        await update.message.reply_text(
            f"🧪 ТЕСТ редактирования товара\n\n"
            f"Товар: {test_tie.name_ru} (ID: {test_tie.id})\n"
            f"Текущая цена: {test_tie.price}\n"
            f"Тестовая цена: {test_price}\n\n"
            f"Вызываем update_tie..."
        )
        
        # Вызываем update_tie напрямую
        result = update_tie(test_tie.id, price=test_price)
        
        # Проверяем результат
        updated_tie = get_tie_by_id(test_tie.id)
        
        await update.message.reply_text(
            f"🔍 РЕЗУЛЬТАТ теста:\n\n"
            f"update_tie вернул: {result}\n"
            f"Тип результата: {type(result)}\n\n"
            f"Товар после обновления:\n"
            f"• Название: {updated_tie.name_ru if updated_tie else 'НЕ НАЙДЕН'}\n"
            f"• Цена: {updated_tie.price if updated_tie else 'НЕ НАЙДЕН'}\n\n"
            f"Статус: {'✅ УСПЕШНО' if result and updated_tie and updated_tie.price == test_price else '❌ ОШИБКА'}"
        )
    
    async def test_conflict(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Test conflict between number input fields"""
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        # Проверяем текущее состояние
        editing_active = context.user_data.get('editing_active', False)
        pending_delivery = context.user_data.get('pending_delivery_order')
        adding_tie = context.user_data.get('adding_tie', False)
        broadcast_active = context.user_data.get('broadcast_active', False)
        
        conflict_info = f"""
🧪 ТЕСТ конфликта полей ввода

📊 ТЕКУЩЕЕ СОСТОЯНИЕ:
• Режим редактирования: {editing_active}
• Ожидающий заказ: {pending_delivery}
• Режим добавления товара: {adding_tie}
• Режим рассылки: {broadcast_active}

🔧 ПРИОРИТЕТЫ ОБРАБОТКИ:
1. Ввод дней доставки (САМЫЙ ВЫСШИЙ)
2. Редактирование товара (ВЫСШИЙ)
3. Добавление товара (НИЗШИЙ)
4. Рассылка (НИЗШИЙ)
5. Обычная обработка заказа

💡 ДЛЯ ТЕСТИРОВАНИЯ:
1. Активируйте режим редактирования товара
2. Попробуйте ввести число
3. Проверьте, что обрабатывается правильное поле

🔍 ОТЛАДОЧНЫЕ КОМАНДЫ:
• /debug - показать данные пользователя
• /edit_test - тест редактирования
• /admin_test - тест админских функций
"""
        
        await update.message.reply_text(conflict_info)
    
    async def force_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Force activate editing mode for testing"""
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        # Получаем первый товар для тестирования
        ties = get_all_active_ties()
        if not ties:
            await update.message.reply_text("❌ Нет товаров для тестирования")
            return
        
        test_tie = ties[0]
        
        # Принудительно активируем режим редактирования
        context.user_data['editing_tie'] = test_tie.id
        context.user_data['editing_field'] = 'price'
        context.user_data['editing_active'] = True
        context.user_data['current_state'] = None
        
        await update.message.reply_text(
            f"🔧 ПРИНУДИТЕЛЬНАЯ АКТИВАЦИЯ РЕЖИМА РЕДАКТИРОВАНИЯ\n\n"
            f"Товар: {test_tie.name_ru} (ID: {test_tie.id})\n"
            f"Поле: price\n"
            f"Режим редактирования: АКТИВЕН\n\n"
            f"Теперь введите новую цену (например: 3000)"
        )
    
    async def clear_all_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear all data from database - PRODUCTION LAUNCH"""
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        # Confirmation message
        await update.message.reply_text(
            "⚠️ **ВНИМАНИЕ! ОЧИСТКА ДАННЫХ**\n\n"
            "Эта команда удалит:\n"
            "• Все заказы\n"
            "• Всех пользователей\n\n"
            "Каталог товаров останется нетронутым!\n\n"
            "Для подтверждения введите: **CONFIRM_CLEAR_ALL**\n"
            "Для отмены введите: **CANCEL**"
        )
        
        # Set confirmation state
        context.user_data['waiting_for_clear_confirmation'] = True
    
    async def reset_ties(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Reset ties to default state from JSON"""
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        await update.message.reply_text("🔄 Сбрасываю товары к исходному состоянию...")
        
        from database import reset_ties_to_default
        
        if reset_ties_to_default():
            await update.message.reply_text(
                "✅ Товары успешно сброшены к исходному состоянию!\n\n"
                "Все товары восстановлены из JSON файла."
            )
        else:
            await update.message.reply_text("❌ Ошибка при сбросе товаров")
    
    async def show_catalog_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show catalog via command"""
        user_id = update.effective_user.id
        
        # Get ties from database
        ties = get_all_active_ties()
        logger.info(f"Retrieved {len(ties)} ties from database for user {user_id}")
        
        if not ties:
            await update.message.reply_text("Каталог пуст. Товары скоро появятся!")
            return
        
        # Create beautiful catalog header
        catalog_text = f"""
🛍️ *КАТАЛОГ ГАЛСТУКОВ*

📊 Всего товаров: {len(ties)}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        # Add each tie to the catalog
        for i, tie in enumerate(ties):
            # Create tie entry with beautiful formatting
            tie_entry = f"""
🔹 *{i+1}. {tie.name_ru}*
   🎨 Цвет: {tie.color_ru}
   🧵 Материал: {tie.material_ru}
   💰 Цена: *{tie.price:,.0f} тг*
   📝 {tie.description_ru}
   
   ─────────────────────────────────────
"""
            catalog_text += tie_entry
        
        # Add footer
        catalog_text += f"""
💳 *Оплата:* Наличными при получении
🚚 *Доставка:* 15 дней по всему Казахстану
📞 *Поддержка:* @your_support_username

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 *Для заказа используйте кнопку "Каталог" в главном меню*
"""
        
        # Send the catalog
        try:
            await update.message.reply_text(
                catalog_text,
                parse_mode='Markdown'
            )
            logger.info(f"Successfully sent catalog to user {user_id}")
        except Exception as e:
            logger.error(f"Error sending catalog to user {user_id}: {e}")
            await update.message.reply_text("❌ Ошибка при загрузке каталога")
    
    async def handle_cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Универсальный обработчик команды /cancel"""
        user_id = update.effective_user.id
        logger.info(f"=== CANCEL COMMAND from user {user_id} ===")
        logger.info(f"User data: {context.user_data}")
        
        # Проверяем режим редактирования (высший приоритет)
        if context.user_data.get('editing_active'):
            logger.info(f"Cancelling editing mode for user {user_id}")
            logger.info(f"Editing tie: {context.user_data.get('editing_tie')}")
            logger.info(f"Editing field: {context.user_data.get('editing_field')}")
            context.user_data['editing_tie'] = None
            context.user_data['editing_field'] = None
            context.user_data['editing_active'] = False
            context.user_data['current_state'] = None
            await update.message.reply_text("❌ Редактирование отменено")
            logger.info(f"Editing mode cancelled for user {user_id}")
            return
        
        # Проверяем режим добавления товара
        if context.user_data.get('adding_tie'):
            logger.info(f"Cancelling adding tie mode for user {user_id}")
            context.user_data['adding_tie'] = False
            context.user_data['new_tie'] = {}
            context.user_data['add_step'] = None
            context.user_data['current_state'] = None
            await update.message.reply_text("❌ Добавление товара отменено")
            return
        
        # Проверяем режим рассылки
        if context.user_data.get('broadcast_active'):
            logger.info(f"Cancelling broadcast mode for user {user_id}")
            context.user_data['broadcast_active'] = False
            context.user_data['broadcast_mode'] = None
            context.user_data['target_user_id'] = None
            context.user_data['current_state'] = None
            await update.message.reply_text("❌ Рассылка отменена")
            return
        
        # Проверяем режим ввода дней доставки для админа
        if user_id in ADMIN_IDS and context.user_data.get('pending_delivery_order'):
            logger.info(f"Cancelling delivery input mode for admin {user_id}")
            del context.user_data['pending_delivery_order']
            context.user_data['current_state'] = None
            await update.message.reply_text("❌ Ввод дней доставки отменен")
            return
        
        # Обычная отмена разговора
        lang = context.user_data.get('language', 'ru')
        await update.message.reply_text(get_text(lang, 'cancelled'))
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel conversation (fallback)"""
        lang = context.user_data.get('language', 'ru')
        await update.message.reply_text(get_text(lang, 'cancelled'))
        return ConversationHandler.END
    
    async def admin_approve(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Admin approves order"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await query.answer("❌ У вас нет прав админа", show_alert=True)
            return
        
        order_id = int(query.data.replace('approve_', ''))
        update_order_status(order_id, 'confirmed')
        
        # Get order details
        order = get_order_by_id(order_id)
        if order:
            # Get user's language
            user_lang = get_user_language(order.user_telegram_id)
            
            # Send final receipt to customer
            final_receipt = f"""
✅ *{get_text(user_lang, 'order_confirmed_title')}*

📦 *{get_text(user_lang, 'order')} #{order_id}*
🎯 *{get_text(user_lang, 'product')}:* {order.tie_name}
💰 *{get_text(user_lang, 'price')}:* {order.price:,} {get_text(user_lang, 'currency')}

👤 *{get_text(user_lang, 'recipient')}:* {order.recipient_name} {order.recipient_surname}
📱 *{get_text(user_lang, 'phone')}:* {order.recipient_phone}
📍 *{get_text(user_lang, 'address')}:* {order.delivery_address}

🚚 *{get_text(user_lang, 'delivery_time')}:* 15 {get_text(user_lang, 'days')}
📅 *{get_text(user_lang, 'estimated_delivery')}:* {get_text(user_lang, 'within_15_days')}

{get_text(user_lang, 'thank_you_message')}
"""
            
            try:
                await context.bot.send_message(
                    chat_id=order.user_telegram_id,
                    text=final_receipt,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to send confirmation to user {order.user_telegram_id}: {e}")
        
        await query.edit_message_text(
            f"✅ Заказ #{order_id} подтвержден!\n\nСтатус изменен на: ПОДТВЕРЖДЕН\nЧек отправлен клиенту.",
            parse_mode='Markdown'
        )
    
    async def admin_reject(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Admin rejects order"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await query.answer("❌ У вас нет прав админа", show_alert=True)
            return
        
        order_id = int(query.data.replace('reject_', ''))
        update_order_status(order_id, 'rejected')
        
        await query.edit_message_text(
            f"❌ Заказ #{order_id} отклонен!\n\nСтатус изменен на: ОТКЛОНЕН",
            parse_mode='Markdown'
        )
    
    async def admin_set_delivery(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Set delivery time for order"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await query.answer("❌ У вас нет прав админа", show_alert=True)
            return
        
        order_id = int(query.data.replace('setdelivery_', ''))
        context.user_data['pending_delivery_order'] = order_id
        context.user_data['current_state'] = NAME
        
        await query.message.reply_text(
            f"📅 Введите количество дней до доставки заказа #{order_id}:\n(Например: 5)",
            parse_mode='Markdown'
        )
    
    async def admin_input_days(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle admin input for delivery days"""
        user_id = update.effective_user.id
        
        # Проверяем, есть ли текст в сообщении
        if not update.message.text:
            logger.warning(f"No text in admin input days message for user {user_id}")
            return
        
        text = update.message.text
        
        logger.info(f"=== ADMIN_INPUT_DAYS START ===")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Message text: '{text}'")
        logger.info(f"Admin IDs: {ADMIN_IDS}")
        logger.info(f"User data: {context.user_data}")
        
        # Проверяем, что режим редактирования не активен
        if context.user_data.get('editing_active'):
            logger.info(f"Editing mode is active, ignoring admin_input_days")
            return
        
        # Отправляем отладочное сообщение админу
        if user_id in ADMIN_IDS:
            await update.message.reply_text(
                f"🔍 ОТЛАДКА admin_input_days:\n"
                f"Функция вызвана!\n"
                f"Пользователь: {user_id}\n"
                f"Текст: '{text}'\n"
                f"Ожидающий заказ: {context.user_data.get('pending_delivery_order')}\n"
                f"Режим редактирования: {context.user_data.get('editing_active', False)}"
            )
        
        if user_id not in ADMIN_IDS:
            logger.info(f"User {user_id} not in admin list, ignoring admin_input_days")
            return
        
        if 'pending_delivery_order' not in context.user_data:
            logger.info(f"No pending delivery order for user {user_id}")
            await update.message.reply_text("❌ Нет ожидающего заказа для установки доставки")
            return
        
        try:
            days = int(update.message.text)
            order_id = context.user_data['pending_delivery_order']
            order = get_order_by_id(order_id)
            
            if order:
                update_order_status(order_id, 'in_delivery')
                user_lang = get_user_language(order.user_telegram_id)
                
                delivery_message = f"""
📦 *{get_text(user_lang, 'delivery_update')}*

{get_text(user_lang, 'order')} #{order_id}
🚚 {get_text(user_lang, 'will_be_delivered')}: {days} {get_text(user_lang, 'days')}

{get_text(user_lang, 'prepare_to_receive')}
"""
                
                await context.bot.send_message(
                    chat_id=order.user_telegram_id,
                    text=delivery_message,
                    parse_mode='Markdown'
                )
                
                await update.message.reply_text(
                    f"✅ Клиенту отправлено уведомление о доставке через {days} дней",
                    parse_mode='Markdown'
                )
            
            del context.user_data['pending_delivery_order']
            context.user_data['current_state'] = None
        except ValueError:
            await update.message.reply_text("❌ Введите число")
    
    async def admin_mark_delivered(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Mark order as delivered"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await query.answer("❌ У вас нет прав админа", show_alert=True)
            return
        
        order_id = int(query.data.replace('delivered_', ''))
        order = get_order_by_id(order_id)
        
        logger.info(f"Admin {user_id} marking order {order_id} as delivered")
        
        if order:
            update_order_status(order_id, 'delivered')
            user_lang = get_user_language(order.user_telegram_id)
            
            logger.info(f"Order {order_id} status updated to delivered, user language: {user_lang}")
            
            keyboard = [[
                InlineKeyboardButton(
                    get_text(user_lang, 'confirm_receipt'),
                    callback_data=f'received_{order_id}'
                )
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            delivered_message = f"""
🎉 *{get_text(user_lang, 'order_delivered')}*

{get_text(user_lang, 'order')} #{order_id}
{get_text(user_lang, 'please_confirm')}
"""
            
            logger.info(f"Sending delivery confirmation to user {order.user_telegram_id}")
            
            try:
                await context.bot.send_message(
                    chat_id=order.user_telegram_id,
                    text=delivered_message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                logger.info(f"Delivery confirmation sent successfully to user {order.user_telegram_id}")
            except Exception as e:
                logger.error(f"Failed to send delivery confirmation to user {order.user_telegram_id}: {e}")
            
            await query.edit_message_text(
                f"✅ Заказ #{order_id} отмечен как доставленный",
                parse_mode='Markdown'
            )
        else:
            logger.error(f"Order {order_id} not found")
            await query.edit_message_text(
                f"❌ Заказ #{order_id} не найден",
                parse_mode='Markdown'
            )
    
    async def user_confirm_receipt(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """User confirms receipt of order"""
        query = update.callback_query
        await query.answer()
        
        order_id = int(query.data.replace('received_', ''))
        order = get_order_by_id(order_id)
        
        if order and order.user_telegram_id == update.effective_user.id:
            update_order_status(order_id, 'completed')
            lang = get_user_language(order.user_telegram_id)
            
            await query.edit_message_text(
                f"✅ {get_text(lang, 'thank_you_confirm')}\n\n{get_text(lang, 'order_completed')}",
                parse_mode='Markdown'
            )
            
            # Notify admins
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"✅ Клиент подтвердил получение заказа #{order_id}",
                        parse_mode='Markdown'
                    )
                except:
                    pass
    
    async def boss_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Boss panel with all admin functions"""
        user_id = update.effective_user.id
        logger.info(f"BOSS_PANEL command from user {user_id}")
        
        if user_id not in ADMIN_IDS:
            logger.warning(f"Non-admin user {user_id} tried to access boss panel")
            await update.message.reply_text("❌ У вас нет доступа")
            return
        
        # Show admin menu with inline buttons
        keyboard = [
            [InlineKeyboardButton("📦 Все заказы", callback_data='boss_orders')],
            [InlineKeyboardButton("👥 Мониторинг пользователей", callback_data='boss_monitor')],
            [InlineKeyboardButton("📊 Генерация PDF отчета", callback_data='boss_report')],
            [InlineKeyboardButton("🛍️ Управление каталогом", callback_data='boss_catalog')],
            [InlineKeyboardButton("📨 Рассылка сообщений", callback_data='boss_broadcast')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        admin_menu = """
🔧 *АДМИН-ПАНЕЛЬ /boss*

Выберите действие:
"""
        
        await update.message.reply_text(admin_menu, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def boss_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Return to boss panel"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await query.message.reply_text("❌ У вас нет доступа")
            return
        
        # Show admin menu with inline buttons
        keyboard = [
            [InlineKeyboardButton("📦 Все заказы", callback_data='boss_orders')],
            [InlineKeyboardButton("👥 Мониторинг пользователей", callback_data='boss_monitor')],
            [InlineKeyboardButton("📊 Генерация PDF отчета", callback_data='boss_report')],
            [InlineKeyboardButton("🛍️ Управление каталогом", callback_data='boss_catalog')],
            [InlineKeyboardButton("📨 Рассылка сообщений", callback_data='boss_broadcast')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        admin_menu = """
🔧 *АДМИН-ПАНЕЛЬ /boss*

Выберите действие:
"""
        
        await query.edit_message_text(admin_menu, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def boss_show_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show all orders from boss panel"""
        query = update.callback_query
        await query.answer()
        
        from database import Session, Order
        session = Session()
        try:
            all_orders = session.query(Order).order_by(Order.created_at.desc()).all()
            
            if not all_orders:
                await query.message.reply_text("📦 Заказов пока нет")
                return
            
            await query.message.reply_text("📊 *УПРАВЛЕНИЕ ЗАКАЗАМИ*", parse_mode='Markdown')
            
            # Show each order with appropriate action buttons
            for order in all_orders[:30]:  # Show last 30 orders
                status_emoji = {
                    'pending_payment': '⏳',
                    'pending_admin_review': '🔍',
                    'confirmed': '✅',
                    'in_delivery': '🚚',
                    'delivered': '📦',
                    'completed': '✔️',
                    'rejected': '❌'
                }.get(order.status, '❓')
                
                # Use the name from the order (payer's name)
                user_name = f"{order.recipient_name} {order.recipient_surname}"
                
                order_text = f"{status_emoji} *Заказ #{order.id}*\n"
                order_text += f"👤 {user_name}\n"
                order_text += f"📱 {order.recipient_phone}\n"
                order_text += f"🎯 {order.tie_name}\n"
                order_text += f"💰 {order.price:,.0f} тг\n"
                order_text += f"📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                order_text += f"📊 Статус: *{order.status}*"
                
                # Create action buttons based on order status
                keyboard = []
                
                if order.status == 'pending_admin_review':
                    keyboard.append([
                        InlineKeyboardButton("✅ Подтвердить", callback_data=f'approve_{order.id}'),
                        InlineKeyboardButton("❌ Отклонить", callback_data=f'reject_{order.id}')
                    ])
                elif order.status == 'confirmed':
                    keyboard.append([
                        InlineKeyboardButton("📅 Установить срок доставки", callback_data=f'setdelivery_{order.id}')
                    ])
                elif order.status == 'in_delivery':
                    keyboard.append([
                        InlineKeyboardButton("✅ Отметить как доставлено", callback_data=f'delivered_{order.id}')
                    ])
                
                if keyboard:
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.message.reply_text(
                        order_text,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                else:
                    await query.message.reply_text(
                        order_text,
                        parse_mode='Markdown'
                    )
            
        finally:
            session.close()
    
    async def boss_monitor(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Monitor active users from boss panel"""
        query = update.callback_query
        await query.answer()
        
        from database import Session, User, Order
        from datetime import datetime, timedelta
        
        session = Session()
        try:
            # Get all users
            all_users = session.query(User).all()
            
            # Time thresholds
            now = datetime.now()
            last_hour = now - timedelta(hours=1)
            last_24h = now - timedelta(hours=24)
            last_week = now - timedelta(days=7)
            
            monitoring_text = "👥 *МОНИТОРИНГ ПОЛЬЗОВАТЕЛЕЙ*\n\n"
            monitoring_text += f"📊 Всего пользователей: {len(all_users)}\n"
            monitoring_text += f"🕐 Текущее время: {now.strftime('%H:%M')}\n"
            monitoring_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
            
            # Active RIGHT NOW (last hour)
            monitoring_text += "🔴 *СЕЙЧАС АКТИВНЫ (последний час):*\n"
            active_now = []
            
            for user in all_users:
                recent_order = session.query(Order).filter(
                    Order.user_telegram_id == user.telegram_id,
                    Order.created_at >= last_hour
                ).order_by(Order.created_at.desc()).first()
                
                if recent_order:
                    minutes_ago = int((now - recent_order.created_at).total_seconds() / 60)
                    active_now.append({
                        'user': user,
                        'order': recent_order,
                        'minutes_ago': minutes_ago
                    })
            
            if active_now:
                for item in sorted(active_now, key=lambda x: x['minutes_ago']):
                    user = item['user']
                    order = item['order']
                    
                    # Get user name from Telegram
                    try:
                        tg_user = await context.bot.get_chat(user.telegram_id)
                        user_name = tg_user.first_name or "Пользователь"
                        if tg_user.last_name:
                            user_name += f" {tg_user.last_name}"
                    except:
                        user_name = f"ID: {user.telegram_id}"
                    
                    monitoring_text += f"👤 *{user_name}*\n"
                    monitoring_text += f"   ID: `{user.telegram_id}`\n"
                    monitoring_text += f"   📱 Действие: {order.status}\n"
                    monitoring_text += f"   ⏰ {item['minutes_ago']} мин назад\n\n"
            else:
                monitoring_text += "   Нет активных\n\n"
            
            # Active today (last 24 hours)
            monitoring_text += "🟡 *АКТИВНЫ СЕГОДНЯ (24ч):*\n"
            active_today_count = 0
            
            for user in all_users:
                recent_order = session.query(Order).filter(
                    Order.user_telegram_id == user.telegram_id,
                    Order.created_at >= last_24h
                ).first()
                
                if recent_order:
                    active_today_count += 1
            
            monitoring_text += f"   Всего: {active_today_count} пользователей\n\n"
            
            # All users with order statistics
            monitoring_text += "📋 *ВСЕ ПОЛЬЗОВАТЕЛИ:*\n"
            
            for user in all_users[:20]:  # Show first 20 users
                user_orders = session.query(Order).filter(
                    Order.user_telegram_id == user.telegram_id
                ).all()
                
                last_order = session.query(Order).filter(
                    Order.user_telegram_id == user.telegram_id
                ).order_by(Order.created_at.desc()).first()
                
                # Get user name from Telegram
                try:
                    tg_user = await context.bot.get_chat(user.telegram_id)
                    user_name = tg_user.first_name or "Пользователь"
                    if tg_user.last_name:
                        user_name += f" {tg_user.last_name}"
                except:
                    user_name = f"ID: {user.telegram_id}"
                
                monitoring_text += f"• {user_name} (`{user.telegram_id}`)\n"
                monitoring_text += f"  📦 Заказов: {len(user_orders)}"
                
                if last_order:
                    days_ago = (now - last_order.created_at).days
                    if days_ago == 0:
                        monitoring_text += f" | Последний: сегодня\n"
                    elif days_ago == 1:
                        monitoring_text += f" | Последний: вчера\n"
                    else:
                        monitoring_text += f" | Последний: {days_ago} дн. назад\n"
                else:
                    monitoring_text += " | Нет заказов\n"
            
            monitoring_text += f"\n📈 *СТАТИСТИКА:*\n"
            monitoring_text += f"🔴 Сейчас активны: {len(active_now)}\n"
            monitoring_text += f"🟡 За 24 часа: {active_today_count}\n"
            monitoring_text += f"📊 Всего: {len(all_users)}"
            
            await query.message.reply_text(monitoring_text, parse_mode='Markdown')
            
        finally:
            session.close()
    
    async def boss_catalog_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Catalog management menu"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("➕ Добавить товар", callback_data='add_tie')],
            [InlineKeyboardButton("📋 Список товаров", callback_data='list_ties')],
            [InlineKeyboardButton("◀️ Назад", callback_data='boss_back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🛍️ *УПРАВЛЕНИЕ КАТАЛОГОМ*\n\nВыберите действие:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def boss_list_ties(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """List all ties for editing"""
        query = update.callback_query
        await query.answer()
        
        logger.info(f"BOSS_LIST_TIES callback from user {update.effective_user.id}")
        
        try:
            ties = get_all_active_ties()
            logger.info(f"Retrieved {len(ties)} ties from database")
        
            if not ties:
                logger.info("No ties found in database")
                await query.message.reply_text("📋 Каталог пуст")
                return
        
            await query.message.reply_text("📋 *ТЕКУЩИЕ ТОВАРЫ В КАТАЛОГЕ:*\n", parse_mode='Markdown')
            
            for i, tie in enumerate(ties):
                logger.info(f"Processing tie {i+1}: {tie.name_ru} (ID: {tie.id})")
                
                keyboard = [
                    [
                        InlineKeyboardButton("✏️ Редактировать", callback_data=f'edit_tie_{tie.id}'),
                        InlineKeyboardButton("🗑️ Удалить", callback_data=f'delete_tie_{tie.id}')
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                tie_info = f"""
*{i+1}. {tie.name_ru}*
🎨 Цвет: {tie.color_ru}
💰 Цена: {tie.price:.0f} тг
📝 {tie.description_ru}
"""
                
                if tie.image_path and os.path.exists(tie.image_path):
                    logger.info(f"Sending photo for tie {tie.id}: {tie.image_path}")
                    try:
                        with open(tie.image_path, 'rb') as photo:
                            await query.message.reply_photo(
                                photo=photo,
                                caption=tie_info,
                                parse_mode='Markdown',
                                reply_markup=reply_markup
                            )
                    except Exception as e:
                        logger.error(f"Error sending photo for tie {tie.id}: {e}")
                        await query.message.reply_text(
                            f"{tie_info}\n❌ Ошибка загрузки изображения",
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                else:
                    logger.info(f"No image for tie {tie.id} or file not found: {tie.image_path}")
                    await query.message.reply_text(
                        f"{tie_info}\n📷 Изображение недоступно",
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                    
        except Exception as e:
            logger.error(f"Error in boss_list_ties: {e}")
            await query.message.reply_text(f"❌ Ошибка загрузки каталога: {str(e)}")
    
    async def boss_add_tie(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Start adding new tie"""
        query = update.callback_query
        await query.answer()
        
        # Clear any broadcast state
        context.user_data['broadcast_active'] = False
        context.user_data['broadcast_mode'] = None
        context.user_data['target_user_id'] = None
        
        context.user_data['adding_tie'] = True
        context.user_data['new_tie'] = {}
        context.user_data['add_step'] = 'name_ru'
        context.user_data['current_state'] = NAME
        
        await query.message.reply_text(
            "➕ *ДОБАВЛЕНИЕ НОВОГО ТОВАРА*\n\n"
            "Шаг 1/5: Введите название товара\n"
            "Например: Красный элегантный галстук\n\n"
            "Для отмены введите /cancel",
            parse_mode='Markdown'
        )
    
    async def boss_edit_tie(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Edit existing tie"""
        query = update.callback_query
        await query.answer()
        
        tie_id = int(query.data.replace('edit_tie_', ''))
        tie = get_tie_by_id(tie_id)
        
        if not tie:
            await query.message.reply_text("❌ Товар не найден")
            return
        
        context.user_data['editing_tie'] = tie_id
        context.user_data['editing_field'] = None
        
        keyboard = [
            [InlineKeyboardButton("📝 Изменить название", callback_data=f'edit_field_name_{tie_id}')],
            [InlineKeyboardButton("🎨 Изменить цвет", callback_data=f'edit_field_color_{tie_id}')],
            [InlineKeyboardButton("💰 Изменить цену", callback_data=f'edit_field_price_{tie_id}')],
            [InlineKeyboardButton("📄 Изменить описание", callback_data=f'edit_field_desc_{tie_id}')],
            [InlineKeyboardButton("🖼️ Изменить фото", callback_data=f'edit_field_photo_{tie_id}')],
            [InlineKeyboardButton("❌ Отмена", callback_data='cancel_edit')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            f"✏️ *РЕДАКТИРОВАНИЕ ТОВАРА*\n\n"
            f"📦 *{tie.name_ru}*\n"
            f"🎨 Цвет: {tie.color_ru}\n"
            f"💰 Цена: {tie.price:.0f} тг\n"
            f"📝 {tie.description_ru}\n\n"
            f"Выберите, что хотите изменить:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def handle_edit_field(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle field editing selection"""
        query = update.callback_query
        await query.answer()
        
        # Parse the callback data: edit_field_<field>_<id>
        parts = query.data.split('_')
        field = parts[2]
        tie_id = int(parts[3])
        
        context.user_data['editing_tie'] = tie_id
        context.user_data['editing_field'] = field
        context.user_data['editing_active'] = True
        context.user_data['current_state'] = None  # Сбрасываем состояние для режима редактирования
        
        field_names = {
            'name': 'название',
            'color': 'цвет',
            'price': 'цену',
            'desc': 'описание',
            'photo': 'фото'
        }
        
        if field == 'photo':
            await query.message.reply_text(
                f"🖼️ Отправьте новое фото товара\n\n"
                f"Для отмены введите /cancel",
                parse_mode='Markdown'
            )
        else:
            await query.message.reply_text(
                f"✏️ Введите новое значение для поля *{field_names[field]}*\n\n"
                f"Для отмены введите /cancel",
                parse_mode='Markdown'
            )
    
    async def cancel_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Cancel editing"""
        query = update.callback_query
        await query.answer()
        
        context.user_data['editing_tie'] = None
        context.user_data['editing_field'] = None
        context.user_data['editing_active'] = False
        context.user_data['current_state'] = None
        
        await query.message.reply_text("❌ Редактирование отменено")
    
    async def handle_edit_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle input for editing fields"""
        logger.info(f"=== HANDLE_EDIT_INPUT CALLED ===")
        logger.info(f"Editing active: {context.user_data.get('editing_active')}")
        logger.info(f"Editing tie: {context.user_data.get('editing_tie')}")
        logger.info(f"Editing field: {context.user_data.get('editing_field')}")
        
        if not context.user_data.get('editing_active'):
            logger.info("Editing not active, returning")
            return
        
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            logger.info(f"User {user_id} not admin, returning")
            return
        
        text = update.message.text
        logger.info(f"Input text: {text}")
        
        if text == '/cancel':
            context.user_data['editing_tie'] = None
            context.user_data['editing_field'] = None
            context.user_data['editing_active'] = False
            await update.message.reply_text("❌ Редактирование отменено")
            return
        
        tie_id = context.user_data.get('editing_tie')
        field = context.user_data.get('editing_field')
        
        if tie_id is None or field is None:
            logger.warning(f"Missing tie_id or field: tie_id={tie_id}, field={field}")
            return
        
        # Update tie in database
        update_data = {}
        
        if field == 'name':
            update_data = {
                'name_ru': text,
                'name_kz': text,
                'name_en': text
            }
        elif field == 'color':
            update_data = {
                'color_ru': text,
                'color_kz': text,
                'color_en': text
            }
        elif field == 'price':
            try:
                price = float(text)
                update_data = {'price': price}
            except ValueError:
                await update.message.reply_text("❌ Цена должна быть числом")
                return
        elif field == 'desc':
            update_data = {
                'description_ru': text,
                'description_kz': text,
                'description_en': text
            }
        
        logger.info(f"Updating tie {tie_id} with data: {update_data}")
        
        # Update in database
        if update_tie(tie_id, **update_data):
            # Clear editing state
            context.user_data['editing_tie'] = None
            context.user_data['editing_field'] = None
            context.user_data['editing_active'] = False
            
            await update.message.reply_text(
                f"✅ Товар успешно обновлен в базе данных!",
                parse_mode='Markdown'
            )
            logger.info(f"Tie {tie_id} updated successfully")
        else:
            await update.message.reply_text("❌ Ошибка обновления товара")
            logger.error(f"Failed to update tie {tie_id}")
        
        # Дополнительная проверка: убеждаемся, что режим добавления не активен
        if context.user_data.get('adding_tie'):
            logger.warning(f"Adding tie mode is active, but trying to edit. This should not happen!")
            return
        
        if user_id not in ADMIN_IDS:
            logger.info(f"User {user_id} not in admin list, ignoring edit input")
            return
        
        tie_id = context.user_data.get('editing_tie')
        field = context.user_data.get('editing_field')
        
        if tie_id is None or field is None:
            logger.warning(f"Missing editing data: tie_id={tie_id}, field={field}")
            return
        
        # Update the tie in database
        logger.info(f"Updating tie {tie_id}, field: {field}, value: {text}")
        
        # Отправляем отладочное сообщение админу перед обновлением
        if user_id in ADMIN_IDS:
            await update.message.reply_text(
                f"🔍 ОТЛАДКА перед обновлением:\n"
                f"Товар ID: {tie_id}\n"
                f"Поле: {field}\n"
                f"Значение: '{text}'\n"
                f"Вызываем update_tie..."
            )
        
        if field == 'name':
            logger.info(f"Updating name field for tie {tie_id}")
            update_result = update_tie(tie_id, name_ru=text, name_kz=text, name_en=text)
            logger.info(f"Update result for name: {update_result}")
            if not update_result:
                logger.error(f"Failed to update name for tie {tie_id}")
                await update.message.reply_text("❌ Ошибка при обновлении названия")
                return
        elif field == 'color':
            logger.info(f"Updating color field for tie {tie_id}")
            update_result = update_tie(tie_id, color_ru=text, color_kz=text, color_en=text)
            if not update_result:
                logger.error(f"Failed to update color for tie {tie_id}")
                await update.message.reply_text("❌ Ошибка при обновлении цвета")
                return
        elif field == 'price':
            logger.info(f"Updating price field for tie {tie_id}")
            try:
                price = int(text)
                logger.info(f"Parsed price: {price}")
                
                # Отправляем отладочное сообщение админу
                if user_id in ADMIN_IDS:
                    await update.message.reply_text(
                        f"🔍 ОТЛАДКА цены:\n"
                        f"Парсинг цены: {price}\n"
                        f"Товар ID: {tie_id}\n"
                        f"Вызываем update_tie..."
                    )
                
                # Проверяем, что товар существует перед обновлением
                tie_before = get_tie_by_id(tie_id)
                if not tie_before:
                    logger.error(f"Tie {tie_id} not found before update")
                    await update.message.reply_text("❌ Товар не найден")
                    return
                
                logger.info(f"Tie before update: {tie_before.name_ru}, price: {tie_before.price}")
                
                # Обновляем товар и проверяем результат
                update_result = update_tie(tie_id, price=price)
                logger.info(f"Update result for price: {update_result}")
                
                if user_id in ADMIN_IDS:
                    await update.message.reply_text(
                        f"🔍 РЕЗУЛЬТАТ обновления:\n"
                        f"update_tie вернул: {update_result}\n"
                        f"Тип: {type(update_result)}"
                    )
                
                if update_result:
                    logger.info(f"Successfully updated price to {price}")
                else:
                    logger.error(f"Failed to update price for tie {tie_id}")
                    await update.message.reply_text("❌ Ошибка при обновлении цены в базе данных")
                    return
                
                # Проверяем, что обновление прошло успешно
                tie_after = get_tie_by_id(tie_id)
                if tie_after:
                    logger.info(f"Tie after update: {tie_after.name_ru}, price: {tie_after.price}")
                    if user_id in ADMIN_IDS:
                        await update.message.reply_text(
                            f"🔍 ПРОВЕРКА после обновления:\n"
                            f"Товар: {tie_after.name_ru}\n"
                            f"Цена: {tie_after.price}"
                        )
                else:
                    logger.error(f"Tie {tie_id} not found after update")
                    await update.message.reply_text("❌ Ошибка при получении обновленного товара")
                    return
                    
            except ValueError:
                logger.error(f"Invalid price format: {text}")
                await update.message.reply_text("❌ Цена должна быть числом")
                return
            except Exception as e:
                logger.error(f"Error updating price: {e}")
                await update.message.reply_text(f"❌ Ошибка при обновлении цены: {str(e)}")
                return
        elif field == 'desc':
            logger.info(f"Updating description field for tie {tie_id}")
            update_result = update_tie(tie_id, description_ru=text, description_kz=text, description_en=text)
            if not update_result:
                logger.error(f"Failed to update description for tie {tie_id}")
                await update.message.reply_text("❌ Ошибка при обновлении описания")
                return
        
        # Get updated tie for confirmation
        tie = get_tie_by_id(tie_id)
        if not tie:
            logger.error(f"Tie {tie_id} not found after update for confirmation")
            await update.message.reply_text("❌ Ошибка при получении обновленного товара")
            return
        
        logger.info(f"Confirmation: Updated tie {tie.name_ru} with price {tie.price}")
        
        # Clear editing state
        context.user_data['editing_tie'] = None
        context.user_data['editing_field'] = None
        context.user_data['editing_active'] = False
        context.user_data['current_state'] = None
        
        # Отправляем подтверждение с новой ценой
        if field == 'price':
            await update.message.reply_text(
                f"✅ Цена товара *{tie.name_ru}* успешно изменена на *{tie.price}* тенге!",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"✅ Товар *{tie.name_ru}* успешно обновлен!",
                parse_mode='Markdown'
            )
    
    async def boss_delete_tie(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Delete tie from catalog"""
        query = update.callback_query
        await query.answer()
        
        tie_id = int(query.data.replace('delete_tie_', ''))
        tie = get_tie_by_id(tie_id)
        
        if not tie:
            await query.message.reply_text("❌ Товар не найден")
            return
        
        # Soft delete in database
        if delete_tie(tie_id):
            await query.message.reply_text(
                f"✅ Товар *{tie.name_ru}* удален из каталога",
                parse_mode='Markdown'
            )
        else:
            await query.message.reply_text("❌ Ошибка удаления товара")
    
    async def handle_catalog_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle step-by-step catalog input"""
        user_id = update.effective_user.id
        
        # Проверяем, есть ли текст в сообщении
        if not update.message.text:
            logger.warning(f"No text in catalog input message for user {user_id}")
            return
        
        text = update.message.text
        logger.info(f"=== HANDLE_CATALOG_INPUT START ===")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Message text: '{text}'")
        logger.info(f"Admin IDs: {ADMIN_IDS}")
        logger.info(f"User data: {context.user_data}")
        
        # ПРОВЕРЯЕМ РЕЖИМ ПОДТВЕРЖДЕНИЯ ОЧИСТКИ (САМЫЙ ВЫСШИЙ ПРИОРИТЕТ)
        if user_id in ADMIN_IDS and context.user_data.get('waiting_for_clear_confirmation'):
            if text == 'CONFIRM_CLEAR_ALL':
                await update.message.reply_text("🗑️ Очищаю все данные...")
                
                from database import clear_all_data
                if clear_all_data():
                    await update.message.reply_text(
                        "✅ **ДАННЫЕ ОЧИЩЕНЫ!**\n\n"
                        "База данных готова для запуска на рынок:\n"
                        "• Все заказы удалены\n"
                        "• Все пользователи удалены\n"
                        "• Каталог товаров сохранен\n\n"
                        "🚀 **Система готова к работе!**"
                    )
                else:
                    await update.message.reply_text("❌ Ошибка при очистке данных")
                
                context.user_data['waiting_for_clear_confirmation'] = False
                return
            elif text == 'CANCEL':
                await update.message.reply_text("❌ Очистка данных отменена")
                context.user_data['waiting_for_clear_confirmation'] = False
                return
            else:
                await update.message.reply_text(
                    "⚠️ Неверная команда. Введите:\n"
                    "• **CONFIRM_CLEAR_ALL** - для подтверждения\n"
                    "• **CANCEL** - для отмены"
                )
                return
        
        # ПРОВЕРЯЕМ РЕЖИМ РЕДАКТИРОВАНИЯ (ВЫСШИЙ ПРИОРИТЕТ)
        if context.user_data.get('editing_active'):
            logger.info(f"Editing mode active, delegating to handle_edit_input from handle_catalog_input")
            return await self.handle_edit_input(update, context)
        
        # Check for admin-specific modes first (only for admins)
        if user_id in ADMIN_IDS:
            # Check for pending delivery order first (highest priority)
            if context.user_data.get('pending_delivery_order'):
                logger.info(f"Pending delivery order for admin {user_id}, delegating to admin_input_days")
                return await self.admin_input_days(update, context)
            # Check for broadcast mode
            elif context.user_data.get('broadcast_active'):
                logger.info(f"Broadcast mode active for admin {user_id}")
                return await self.handle_broadcast_message(update, context)
            # Check for adding tie mode
            elif context.user_data.get('adding_tie'):
                logger.info(f"Adding tie mode active for admin {user_id}")
                # Process tie addition
                pass  # Continue with tie processing below
            else:
                logger.info(f"No active admin mode for admin {user_id}, ignoring message in handle_catalog_input")
                return  # No active mode for admin
        else:
            # For non-admin users, check if they have any active modes
            if not any([
                context.user_data.get('adding_tie'),
                context.user_data.get('editing_active'),
                context.user_data.get('broadcast_active'),
                context.user_data.get('pending_delivery_order')
            ]):
                logger.info(f"No active mode for regular user {user_id}, ignoring message")
                return  # No active mode for regular user
        
        step = context.user_data.get('add_step')
        
        logger.info(f"Text: '{text}', Step: {step}")
        logger.info(f"Adding tie: {context.user_data.get('adding_tie')}")
        
        # Check if we should process this message
        if not context.user_data.get('adding_tie'):
            logger.info(f"No adding_tie mode active, ignoring message in handle_catalog_input")
            return
        
        logger.info(f"Processing message in handle_catalog_input")
        
        
        # Process each step
        if step == 'name_ru':
            context.user_data['new_tie']['name_ru'] = text
            context.user_data['new_tie']['name_kz'] = text  # Use same name for Kazakh
            context.user_data['add_step'] = 'color_ru'
            await update.message.reply_text(
                "✅ Название сохранено\n\n"
                "Шаг 2/5: Введите цвет товара\n"
                "Например: Красный",
                parse_mode='Markdown'
            )
            return  # Important: stop processing after sending message
        
        elif step == 'color_ru':
            context.user_data['new_tie']['color_ru'] = text
            context.user_data['new_tie']['color_kz'] = text  # Use same color for Kazakh
            context.user_data['add_step'] = 'price'
            await update.message.reply_text(
                "✅ Цвет сохранен\n\n"
                "Шаг 3/5: Введите цену (только число)\n"
                "Например: 1500",
                parse_mode='Markdown'
            )
            return  # Important: stop processing after sending message
        
        elif step == 'price':
            try:
                price = int(text)
                context.user_data['new_tie']['price'] = price
                context.user_data['add_step'] = 'desc_ru'
                await update.message.reply_text(
                    "✅ Цена сохранена\n\n"
                    "Шаг 4/5: Введите описание товара\n"
                    "Например: Элегантный галстук для особых случаев",
                    parse_mode='Markdown'
                )
                return  # Important: stop processing after sending message
            except ValueError:
                await update.message.reply_text("❌ Введите корректную цену (только число)")
                return  # Important: stop processing after error
        
        elif step == 'desc_ru':
            context.user_data['new_tie']['desc_ru'] = text
            context.user_data['new_tie']['desc_kz'] = text  # Use same description for Kazakh
            context.user_data['add_step'] = 'photo'
            await update.message.reply_text(
                "✅ Описание сохранено\n\n"
                "Шаг 5/5: Отправьте фото товара",
                parse_mode='Markdown'
            )
            return  # Important: stop processing text messages when waiting for photo
    
    async def handle_catalog_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle photo upload for new tie or editing existing tie"""
        user_id = update.effective_user.id
        logger.info(f"=== HANDLE_CATALOG_PHOTO START ===")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Admin IDs: {ADMIN_IDS}")
        logger.info(f"User data: {context.user_data}")
        
        if user_id not in ADMIN_IDS:
            logger.info(f"User {user_id} not in admin list, ignoring photo")
            return
        
        # Check if we're adding a new tie
        if context.user_data.get('adding_tie') and context.user_data.get('add_step') == 'photo':
            logger.info(f"Handling new tie photo for user {user_id}")
            await self._handle_new_tie_photo(update, context)
        # Check if we're editing an existing tie
        elif context.user_data.get('editing_active') and context.user_data.get('editing_field') == 'photo':
            logger.info(f"Handling edit tie photo for user {user_id}")
            await self._handle_edit_tie_photo(update, context)
        else:
            logger.info(f"No active photo mode for user {user_id}, ignoring photo")
            return
    
    async def _handle_new_tie_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle photo upload for new tie"""
        
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            return
        
        import uuid
        
        # Download photo
        photo_file = await update.message.photo[-1].get_file()
        file_extension = photo_file.file_path.split('.')[-1]
        filename = f"TieUp/{uuid.uuid4()}.{file_extension}"
        
        # Create directory if not exists
        os.makedirs("TieUp", exist_ok=True)
        await photo_file.download_to_drive(filename)
        
        # Create new tie in database
        new_tie_data = context.user_data['new_tie']
        
        tie_id = create_tie(
            name_ru=new_tie_data['name_ru'],
            color_ru=new_tie_data['color_ru'],
            price=new_tie_data['price'],
            description_ru=new_tie_data['desc_ru'],
            image_path=filename
        )
        
        # Clear context
        context.user_data['adding_tie'] = False
        context.user_data['new_tie'] = {}
        context.user_data['add_step'] = None
        context.user_data['current_state'] = None
        
        await update.message.reply_text(
            f"✅ *Товар успешно добавлен в базу данных!*\n\n"
            f"ID: {tie_id}\n"
            f"Название: {new_tie_data['name_ru']}\n"
            f"Цвет: {new_tie_data['color_ru']}\n"
            f"Цена: {new_tie_data['price']} тг\n\n"
            f"Товар теперь доступен в каталоге!",
            parse_mode='Markdown'
        )
    
    async def _handle_edit_tie_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle photo upload for editing existing tie"""
        import uuid
        
        # Download photo
        photo_file = await update.message.photo[-1].get_file()
        file_extension = photo_file.file_path.split('.')[-1]
        filename = f"TieUp/{uuid.uuid4()}.{file_extension}"
        
        # Create directory if not exists
        os.makedirs("TieUp", exist_ok=True)
        await photo_file.download_to_drive(filename)
        
        # Update tie in database
        tie_id = context.user_data.get('editing_tie')
        update_tie(tie_id, image_path=filename)
        
        # Get updated tie for confirmation
        tie = get_tie_by_id(tie_id)
        
        # Clear editing state
        context.user_data['editing_tie'] = None
        context.user_data['editing_field'] = None
        context.user_data['editing_active'] = False
        context.user_data['current_state'] = None
        
        await update.message.reply_text(
            f"✅ *Фото товара обновлено!*\n\n"
            f"📦 *{tie.name_ru}*\n"
            f"🎨 Цвет: {tie.color_ru}\n"
            f"💰 Цена: {tie.price:,.0f} тг\n"
            f"📝 {tie.description_ru}",
            parse_mode='Markdown'
        )
    
    async def boss_broadcast_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Broadcast menu for admin"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("📢 Отправить всем", callback_data='broadcast_all')],
            [InlineKeyboardButton("👤 Отправить одному", callback_data='broadcast_one')],
            [InlineKeyboardButton("◀️ Назад", callback_data='boss_back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📨 *РАССЫЛКА СООБЩЕНИЙ*\n\nВыберите тип рассылки:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def broadcast_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Start broadcast to all users"""
        query = update.callback_query
        await query.answer()
        
        # Clear any tie adding state
        context.user_data['adding_tie'] = False
        context.user_data['new_tie'] = {}
        context.user_data['add_step'] = None
        
        context.user_data['broadcast_mode'] = 'all'
        context.user_data['broadcast_active'] = True
        context.user_data['current_state'] = NAME
        
        await query.message.reply_text(
            "📢 *РАССЫЛКА ВСЕМ ПОЛЬЗОВАТЕЛЯМ*\n\n"
            "Отправьте сообщение, которое хотите разослать всем.\n"
            "Можно отправить текст или фото с подписью.\n\n"
            "Для отмены введите /cancel",
            parse_mode='Markdown'
        )
    
    async def broadcast_one(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Start broadcast to one user - show user selection"""
        query = update.callback_query
        logger.info(f"BROADCAST_ONE callback from user {update.effective_user.id}")
        await query.answer()
        
        # Clear any tie adding state
        context.user_data['adding_tie'] = False
        context.user_data['new_tie'] = {}
        context.user_data['add_step'] = None
        
        context.user_data['broadcast_mode'] = 'one'
        context.user_data['broadcast_active'] = True
        context.user_data['current_state'] = NAME
        
        logger.info(f"Broadcast mode set to 'one' for user {update.effective_user.id}")
        
        # Get users from database
        from database import Session, User
        session = Session()
        try:
            users = session.query(User).all()
            
            if not users:
                await query.message.reply_text("❌ Пользователи не найдены в базе данных")
                return
            
            # Create inline keyboard with users
            keyboard = []
            for user in users:
                # Create user display name - prioritize first_name + last_name, then username, then ID
                if user.first_name and user.last_name:
                    display_name = f"{user.first_name} {user.last_name}"
                elif user.first_name:
                    display_name = user.first_name
                elif user.username:
                    display_name = f"@{user.username}"
                else:
                    display_name = f"ID: {user.telegram_id}"
                
                callback_data = f"select_user_{user.telegram_id}"
                keyboard.append([InlineKeyboardButton(display_name, callback_data=callback_data)])
            
            # Add cancel button
            keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_broadcast")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
        
            await query.message.reply_text(
                "👤 *ВЫБЕРИТЕ ПОЛЬЗОВАТЕЛЯ*\n\n"
                "Выберите пользователя для отправки личного сообщения:",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Error getting users for broadcast: {e}")
            await query.message.reply_text(f"❌ Ошибка загрузки пользователей: {str(e)}")
        finally:
            session.close()
    
    async def select_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle user selection for broadcast"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            logger.info(f"User {user_id} not in admin list, ignoring select_user")
            return
        
        # Extract target user ID from callback data
        callback_data = query.data
        target_user_id = int(callback_data.replace('select_user_', ''))
        
        logger.info(f"User {user_id} selected target user {target_user_id}")
        
        # Store target user ID
        context.user_data['target_user_id'] = target_user_id
        
        # Get target user info for display
        from database import Session, User
        session = Session()
        try:
            target_user = session.query(User).filter(User.telegram_id == target_user_id).first()
            if target_user:
                display_name = f"@{target_user.username}" if target_user.username else f"ID: {target_user.telegram_id}"
                await query.message.reply_text(
                    f"✅ Выбран пользователь: {display_name}\n\n"
                    "Теперь отправьте сообщение для этого пользователя:",
            parse_mode='Markdown'
        )
            else:
                await query.message.reply_text(
                    f"✅ Выбран пользователь ID: {target_user_id}\n\n"
                    "Теперь отправьте сообщение для этого пользователя:",
                    parse_mode='Markdown'
                )
        finally:
            session.close()
    
    async def cancel_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Cancel broadcast operation"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            logger.info(f"User {user_id} not in admin list, ignoring cancel_broadcast")
            return
        
        logger.info(f"Broadcast cancelled by user {user_id}")
        
        # Reset broadcast state
        context.user_data['broadcast_active'] = False
        context.user_data['broadcast_mode'] = None
        context.user_data['target_user_id'] = None
        context.user_data['current_state'] = None
        
        await query.message.reply_text("❌ Рассылка отменена")
    
    async def handle_broadcast_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle broadcast messages"""
        if not context.user_data.get('broadcast_active'):
            logger.info("Broadcast not active, ignoring message")
            return
        
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            logger.info(f"User {user_id} not in admin list, ignoring broadcast message")
            return
        
        # Проверяем, есть ли текст в сообщении
        if not update.message.text:
            logger.warning(f"No text in broadcast message for user {user_id}")
            return
        
        text = update.message.text
        mode = context.user_data.get('broadcast_mode')
        target_user_id = context.user_data.get('target_user_id')
        
        logger.info(f"Broadcast message received from user {user_id}: mode='{mode}', target_user_id={target_user_id}, text='{text[:50]}...'")
        
        
        # For mode 'one', we expect target_user_id to be already set from user selection
        if mode == 'one' and not context.user_data.get('target_user_id'):
            logger.warning(f"Mode 'one' but no target_user_id set for user {user_id}")
            await update.message.reply_text("❌ Пользователь не выбран. Начните заново.")
            return
        
        # If we have target_user_id and mode is 'one', send message to that user
        if mode == 'one' and context.user_data.get('target_user_id'):
            target_id = context.user_data.get('target_user_id')
            logger.info(f"Sending message to user {target_id} from admin {user_id}")
            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=f"💬 *Личное сообщение от администрации:*\n\n{text}",
                    parse_mode='Markdown'
                )
                logger.info(f"Message successfully sent to user {target_id}")
                await update.message.reply_text(f"✅ Сообщение отправлено пользователю {target_id}")
                
                # Reset broadcast state
                context.user_data['broadcast_active'] = False
                context.user_data['broadcast_mode'] = None
                context.user_data['target_user_id'] = None
                context.user_data['current_state'] = None
                logger.info(f"Broadcast state reset for user {user_id}")
                return
            except Exception as e:
                logger.error(f"Error sending message to user {target_id}: {str(e)}")
                await update.message.reply_text(f"❌ Ошибка отправки: {str(e)}")
                return
        
        # Send broadcast to all users
        from database import Session, User
        session = Session()
        
        try:
            if mode == 'all':
                logger.info(f"Starting broadcast to all users from admin {user_id}")
                users = session.query(User).all()
                success_count = 0
                fail_count = 0
                
                await update.message.reply_text("📤 Начинаю рассылку...")
                
                for user in users:
                    try:
                        await context.bot.send_message(
                            chat_id=user.telegram_id,
                            text=f"📢 *Сообщение от администрации:*\n\n{text}",
                            parse_mode='Markdown'
                        )
                        success_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to send message to user {user.telegram_id}: {e}")
                        fail_count += 1
                
                logger.info(f"Broadcast completed: {success_count} success, {fail_count} failed")
                await update.message.reply_text(
                    f"✅ Рассылка завершена!\n\n"
                    f"Успешно: {success_count}\n"
                    f"Ошибок: {fail_count}"
                )
            else:
                logger.warning(f"Unknown broadcast mode: {mode}")
                await update.message.reply_text("❌ Неизвестный режим рассылки")
            
            # Reset broadcast state
            context.user_data['broadcast_active'] = False
            context.user_data['broadcast_mode'] = None
            context.user_data['target_user_id'] = None
            context.user_data['current_state'] = None
            logger.info(f"Broadcast state reset for user {user_id}")
            
        finally:
            session.close()
    
    async def boss_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Generate PDF report from boss panel"""
        query = update.callback_query
        await query.answer()
        
        await query.message.reply_text("📊 Генерирую отчет...")
        
        from database import Session, User, Order
        from pdf_generator import generate_admin_report
        
        session = Session()
        try:
            # Get all data
            all_orders = session.query(Order).all()
            all_users = session.query(User).all()
            
            # Generate PDF
            report_path = generate_admin_report(all_orders, all_users)
            
            # Send PDF file
            with open(report_path, 'rb') as pdf_file:
                await query.message.reply_document(
                    document=pdf_file,
                    filename=f"TieShop_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    caption="📊 *Отчет готов!*\n\nВ отчете:\n• Статистика заказов\n• Активные пользователи\n• Финансовые показатели\n• Последние заказы",
                    parse_mode='Markdown'
                )
            
            # Clean up
            os.remove(report_path)
            
        except Exception as e:
            await query.message.reply_text(f"❌ Ошибка генерации отчета: {str(e)}")
        finally:
            session.close()
    
    def run(self):
        """Run the bot"""
        logger.info("Starting bot...")
        # Add error handler
        self.application.add_error_handler(self.error_handler)
        self.application.run_polling()
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        try:
            # Notify user about error
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "❌ Произошла ошибка. Попробуйте еще раз или обратитесь в поддержку.\n"
                    "Используйте /start для перезапуска."
                )
        except:
            pass
        
        # Notify admins
        for admin_id in ADMIN_IDS:
            try:
                error_text = f"⚠️ ОШИБКА В БОТЕ:\n\n{str(context.error)[:500]}"
                await context.bot.send_message(chat_id=admin_id, text=error_text)
            except:
                pass

if __name__ == '__main__':
    bot = TieShopBot()
    bot.run()
