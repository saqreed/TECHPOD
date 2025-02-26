from dotenv import load_dotenv
import logging
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)

# Инициализация окружения
load_dotenv()

# Логирование
logging.basicConfig(
    format='%(asctime)s | %(levelname)s | %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния диалога
WHO, LOCATION, ANYDESK, PROBLEM, URGENCY, ADDITIONAL = range(6)

# ID администратора
ADMIN_CHAT = os.getenv('ADMIN_CHAT_ID') or '956940111'

# Клавиатуры
MAIN_KEYBOARD = [['Создать запрос', 'FAQ']]
LOCATION_KEYBOARD = [['🏢 2 этаж', '🏢 3 этаж', '🌐 Удалёнка']]
URGENCY_KEYBOARD = [['🟢 Низкая', '🟡 Средняя', '🔴 Высокая']]
FAQ_KEYBOARD = [
    [InlineKeyboardButton("Как сбросить пароль?", callback_data='faq_password')],
    [InlineKeyboardButton("Где найти логи?", callback_data='faq_logs')],
    [InlineKeyboardButton("Как обновить ПО?", callback_data='faq_update')],
    [InlineKeyboardButton("Время работы поддержки", callback_data='faq_hours')],
    [InlineKeyboardButton("Главное меню", callback_data='faq_main')]
]

# База знаний FAQ
FAQ_DATABASE = {
    'faq_password': "Чтобы сбросить пароль:\n1. Перейдите на страницу входа\n2. Нажмите 'Забыли пароль?'\n3. Следуйте инструкциям в письме",
    'faq_logs': "Логи находятся в:\n- Windows: C:/ProgramData/Logs\n- Linux: /var/log/app\n- MacOS: ~/Library/Logs",
    'faq_update': "Обновление ПО:\n1. Запустите приложение\n2. Перейдите в 'Настройки'\n3. Выберите 'Проверить обновления'",
    'faq_hours': "Часы работы поддержки:\nПн-Пт: 9:00-18:00 (МСК)\nСб-Вс: выходные"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Главное меню"""
    user = update.message.from_user
    context.user_data['username'] = user.username or 'не указан'
    
    await update.message.reply_text(
        "✨ *Добро пожаловать!* ✨\n\n"
        "Выберите действие:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(
            MAIN_KEYBOARD,
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return ConversationHandler.END  # Выходим из основного диалога

async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /faq"""
    keyboard = InlineKeyboardMarkup(FAQ_KEYBOARD)
    await update.message.reply_text(
        "📚 *Часто задаваемые вопросы*\n\nВыберите вопрос:",
        parse_mode='Markdown',
        reply_markup=keyboard
    )

async def handle_faq_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатий кнопок FAQ"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'faq_main':
        await query.edit_message_text(
            "📚 *Часто задаваемые вопросы*\n\nВыберите вопрос:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(FAQ_KEYBOARD)
        )
        return
    
    answer = FAQ_DATABASE.get(query.data, "Извините, ответ пока не доступен. Мы скоро добавим информацию!")
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='faq_main')]])
    
    await query.edit_message_text(
        answer,
        parse_mode='Markdown',
        reply_markup=keyboard
    )
    
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    await update.message.reply_text(
        "🛠 *Справка*\n\n"
        "1. Начните диалог с командой /start\n"
        "2. Следуйте инструкциям бота\n"
        "3. Для отмены используйте /cancel\n\n"
        "Часы работы поддержки: 9:00-18:00 (МСК)",
        parse_mode='Markdown'
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало диалога"""
    user = update.message.from_user
    context.user_data['username'] = user.username or 'не указан'
    
    await update.message.reply_text(
        "✨ *Добро пожаловать в техподдержку!* ✨\n\n"
        "Представьтесь пожалуйста:\n"
        "_Пример: Иван Петров или @ivan_petrov_2024_",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return WHO

async def who(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохранение имени пользователя"""
    user_input = update.message.text.strip()
    if not user_input:
        await update.message.reply_text("⚠️ Введите ваше имя или ID:")
        return WHO
        
    context.user_data['who'] = user_input
    await update.message.reply_text(
        f"Привет, {user_input}! 🎉\n"
        "Выберите ваше местоположение:",
        reply_markup=ReplyKeyboardMarkup(
            LOCATION_KEYBOARD,
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return LOCATION

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка локации"""
    loc = update.message.text.strip()
    
    # Исправленная проверка допустимых локаций
    valid_locations = LOCATION_KEYBOARD[0]  # Прямое получение списка кнопок
    
    if loc not in valid_locations:
        await update.message.reply_text("❌ Используйте кнопки для выбора локации:")
        return LOCATION
        
    context.user_data['location'] = loc
    
    if 'Удалёнка' in loc:
        await update.message.reply_text(
            "🌐 *Удалённый доступ*\n"
            "Введите ваш AnyDesk ID:\n"
            "_Пример: 123-456-789_",
            parse_mode='Markdown'
        )
        return ANYDESK
    else:
        await update.message.reply_text(
            "🖥️ *Описание проблемы*\n"
            "Опишите что произошло:\n"
            "_Максимум 500 символов_",
            parse_mode='Markdown'
        )
        return PROBLEM

async def anydesk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Проверка AnyDesk ID"""
    anydesk_id = update.message.text.strip()
    if not anydesk_id:
        await update.message.reply_text("⚠️ Введите ваш AnyDesk ID:")
        return ANYDESK
        
    context.user_data['anydesk'] = anydesk_id
    await update.message.reply_text(
        "✅ AnyDesk получен\n\n"
        "🖥️ *Описание проблемы*\n"
        "Опишите что произошло:",
        parse_mode='Markdown'
    )
    return PROBLEM

async def problem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Проверка описания проблемы"""
    problem_text = update.message.text.strip()
    if len(problem_text) > 500:
        await update.message.reply_text("⚠️ Слишком длинное описание! Максимум 500 символов.")
        return PROBLEM
        
    context.user_data['problem'] = problem_text
    await update.message.reply_text(
        "⏳ *Срочность*\n"
        "Выберите приоритет:",
        reply_markup=ReplyKeyboardMarkup(
            URGENCY_KEYBOARD,
            one_time_keyboard=True,
            resize_keyboard=True
        ),
        parse_mode='Markdown'
    )
    return URGENCY

async def urgency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохранение срочности"""
    urgency_text = update.message.text.strip()
    context.user_data['urgency'] = urgency_text
    
    await update.message.reply_text(
        "📝 *Дополнительные файлы*\n"
        "Приложите скриншоты/логи или напишите 'нет':",
        parse_mode='Markdown'
    )
    return ADDITIONAL

async def additional(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Формирование итогового отчёта"""
    additional_info = update.message.text.strip() or "Не предоставлено"
    context.user_data['additional'] = additional_info
    
    # Формируем отчёт
    summary = (
        "🚨 *НОВЫЙ ЗАПРОС* 🚨\n\n"
        f"👤 *Пользователь:* {context.user_data['who']} (@{context.user_data['username']})\n"
        f"📍 *Локация:* {context.user_data['location']}\n"
    )
    
    if 'Удалёнка' in context.user_data['location']:
        summary += f"🔗 *AnyDesk:* `{context.user_data['anydesk']}`\n"
        
    summary += (
        f"🖥️ *Проблема:* {context.user_data['problem']}\n"
        f"⏳ *Срочность:* {context.user_data['urgency']}\n"
        f"📦 *Дополнительно:* {additional_info}\n\n"
        "✅ Запрос отправлен в поддержку!"
    )
    
    # Отправляем пользователю
    await update.message.reply_text(
        summary,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Отправляем админу
    admin_summary = f"{summary}\n\n_Отправил: @{context.user_data['username']} ({context.user_data['who']})_"
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT,
            text=admin_summary,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Ошибка отправки админу: {e}")
        
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена диалога"""
    await update.message.reply_text(
        "❌ Операция отменена\n"
        "Для нового запроса используйте /start",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main() -> None:
    """Запуск бота"""
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        logger.error("Не найден TELEGRAM_BOT_TOKEN в переменных окружения!")
        return
        
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('faq', faq_command))
    application.add_handler(CallbackQueryHandler(handle_faq_buttons))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WHO: [MessageHandler(filters.TEXT & ~filters.COMMAND, who)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, location)],
            ANYDESK: [MessageHandler(filters.TEXT & ~filters.COMMAND, anydesk)],
            PROBLEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, problem)],
            URGENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, urgency)],
            ADDITIONAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, additional)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))
    
    logger.info("Бот запущен ✨")
    application.run_polling()

if __name__ == '__main__':
    main()