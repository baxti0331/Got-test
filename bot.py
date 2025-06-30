import logging
import os
import wikipedia
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, CallbackQueryHandler
)

logging.basicConfig(level=logging.INFO)

DEFAULT_LANG = "ru"
user_languages = {}  # Словарь для хранения языка каждого пользователя

MAX_QUERY_LENGTH = 100

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Русский 🌐", callback_data="setlang_ru"),
         InlineKeyboardButton("English 🌐", callback_data="setlang_en")]
    ])
    await update.message.reply_text(
        "👋 Привет! Я Википедия-бот.\n"
        "Просто напиши мне любой запрос — я найду информацию из Википедии.\n"
        "👇 Выбери язык:",
        reply_markup=keyboard
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Русский 🌐", callback_data="setlang_ru"),
         InlineKeyboardButton("English 🌐", callback_data="setlang_en")]
    ])
    await update.message.reply_text(
        "ℹ️ <b>Возможности бота:</b>\n"
        "🔍 Поиск информации из Википедии на русском или английском языке.\n"
        "💡 Если запрос общий — бот предложит уточнения.\n"
        "🌐 Для смены языка нажмите кнопку ниже.\n\n"
        "Просто отправьте любое слово или вопрос.\n\n"
        "<b>Примеры:</b>\n"
        "- Солнце\n"
        "- Python programming\n"
        "- Россия\n",
        parse_mode="HTML",
        reply_markup=keyboard
    )

async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == "setlang_ru":
        user_languages[user_id] = "ru"
        await query.answer("Язык установлен: Русский 🌐")
    elif query.data == "setlang_en":
        user_languages[user_id] = "en"
        await query.answer("Language set to: English 🌐")

    await query.edit_message_text("✅ Язык успешно изменён.")

async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = update.message.text.strip()

    if not query_text:
        await update.message.reply_text("❗ Пожалуйста, отправьте непустой запрос.")
        return

    if len(query_text) > MAX_QUERY_LENGTH:
        await update.message.reply_text(f"⚠️ Слишком длинный запрос. Не более {MAX_QUERY_LENGTH} символов.")
        return

    user_id = update.effective_user.id
    lang = user_languages.get(user_id, DEFAULT_LANG)
    wikipedia.set_lang(lang)

    try:
        summary = wikipedia.summary(query_text, sentences=5)
        page = wikipedia.page(query_text)
        url = page.url

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Читать на Википедии", url=url)]
        ])

        text = f"📚 <b>Вот что я нашёл:</b>\n\n{summary}"
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)

    except wikipedia.exceptions.DisambiguationError as e:
        options = e.options[:5]
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(opt, callback_data=f"search_{opt}")]
            for opt in options
        ])
        await update.message.reply_text(
            "🤔 Ваш запрос слишком общий. Выберите один из вариантов:",
            reply_markup=keyboard
        )

    except wikipedia.exceptions.PageError:
        await update.message.reply_text(
            "😞 Статья не найдена. Попробуйте другой запрос."
        )
    except Exception as ex:
        logging.error(f"Ошибка при запросе: {ex}")
        await update.message.reply_text(
            "⚠️ Произошла непредвиденная ошибка. Попробуйте позже."
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.data.startswith("setlang_"):
        await set_language_callback(update, context)
    elif query.data.startswith("search_"):
        topic = query.data.replace("search_", "")
        user_id = query.from_user.id
        lang = user_languages.get(user_id, DEFAULT_LANG)
        wikipedia.set_lang(lang)

        try:
            summary = wikipedia.summary(topic, sentences=5)
            page = wikipedia.page(topic)
            url = page.url

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Читать на Википедии", url=url)]
            ])

            text = f"📚 <b>Вот уточнённая информация:</b>\n\n{summary}"
            await query.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)
            await query.answer()
        except Exception as ex:
            logging.error(f"Ошибка при уточнении запроса: {ex}")
            await query.message.reply_text(
                "⚠️ Не удалось получить данные по уточнённому запросу."
            )
            await query.answer()

if __name__ == "__main__":
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    PORT = int(os.getenv("PORT", "8443"))

    if not TOKEN:
        raise ValueError("Отсутствует TELEGRAM_TOKEN в переменных окружения!")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question))

    WEBHOOK_PATH = f"/{TOKEN}"
    WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"

    logging.info(f"Устанавливаю Webhook: {WEBHOOK_URL}")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL
    )