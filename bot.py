import logging
import os
import wikipedia
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

logging.basicConfig(level=logging.INFO)

DEFAULT_LANG = "ru"
user_languages = {}  # Сохраняем язык для каждого пользователя
wikipedia.set_lang(DEFAULT_LANG)

MAX_QUERY_LENGTH = 100


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я твой Википедия-бот.\n"
        "Отправь мне любой запрос, и я постараюсь найти информацию.\n"
        "Команды:\n/help — помощь\n/lang ru или /lang en — смена языка"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ Я ищу информацию из Википедии.\n"
        "Просто отправь запрос.\n"
        "Можно менять язык поиска: /lang ru или /lang en"
    )


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи язык: /lang ru или /lang en")
        return

    lang = context.args[0].lower()
    if lang in ["ru", "en"]:
        user_languages[update.effective_user.id] = lang
        await update.message.reply_text(f"✅ Язык установлен: {lang}")
    else:
        await update.message.reply_text("⚠️ Поддерживаются только 'ru' и 'en'")


async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()

    if not query:
        await update.message.reply_text("❗ Пожалуйста, отправь непустой запрос.")
        return

    if len(query) > MAX_QUERY_LENGTH:
        await update.message.reply_text(
            f"⚠️ Слишком длинный запрос! Не более {MAX_QUERY_LENGTH} символов."
        )
        return

    user_id = update.effective_user.id
    lang = user_languages.get(user_id, DEFAULT_LANG)
    wikipedia.set_lang(lang)

    try:
        summary = wikipedia.summary(query, sentences=10)
        page = wikipedia.page(query)
        url = page.url

        text = f"📚 Вот что я нашёл для тебя:\n\n{summary}\n\n🔗 Подробнее: {url}"

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Перейти к статье на Википедии", url=url)]]
        )

        if page.images:
            await update.message.reply_photo(photo=page.images[0], caption=text, reply_markup=keyboard)
        else:
            await update.message.reply_text(text, reply_markup=keyboard)

    except wikipedia.exceptions.DisambiguationError as e:
        options = e.options[:5]
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(opt, callback_data=opt)] for opt in options]
        )
        await update.message.reply_text(
            "🤔 Твой запрос слишком общий. Пожалуйста, выбери уточнение:",
            reply_markup=keyboard
        )

    except wikipedia.exceptions.PageError:
        await update.message.reply_text(
            "😞 Я не нашёл статью по твоему запросу. Попробуй другой запрос."
        )
    except Exception:
        await update.message.reply_text(
            "⚠️ Произошла ошибка при обработке запроса. Попробуй позже."
        )


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    await update.callback_query.answer()

    user_id = update.effective_user.id
    lang = user_languages.get(user_id, DEFAULT_LANG)
    wikipedia.set_lang(lang)

    try:
        summary = wikipedia.summary(query, sentences=10)
        page = wikipedia.page(query)
        url = page.url

        text = f"📚 Вот что я нашёл:\n\n{summary}\n\n🔗 Подробнее: {url}"

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Перейти к статье на Википедии", url=url)]]
        )

        if page.images:
            await update.callback_query.message.reply_photo(photo=page.images[0], caption=text, reply_markup=keyboard)
        else:
            await update.callback_query.message.reply_text(text, reply_markup=keyboard)

    except Exception:
        await update.callback_query.message.reply_text(
            "⚠️ Ошибка при попытке получить информацию. Попробуй позже."
        )


if __name__ == "__main__":
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    PORT = int(os.getenv("PORT", "8443"))  # Render даёт порт в env

    if not TOKEN:
        raise ValueError("Отсутствует TELEGRAM_TOKEN в переменных окружения!")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("lang", set_language))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question))

    WEBHOOK_PATH = f"/{TOKEN}"
    WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"

    print(f"Устанавливаю Webhook: {WEBHOOK_URL}")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL
    )