import logging
import os
import wikipedia
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters

logging.basicConfig(level=logging.INFO)

# Язык по умолчанию
DEFAULT_LANG = "ru"
wikipedia.set_lang(DEFAULT_LANG)

# Словарь для хранения языка по пользователю
user_languages = {}

MAX_QUERY_LENGTH = 100

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_languages[user_id] = DEFAULT_LANG

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru"),
            InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
            InlineKeyboardButton("O'zbek 🇺🇿", callback_data="lang_uz")
        ]
    ])

    await update.message.reply_text(
        "👋 Привет! Я Википедия-Бот.\n\n"
        "Отправь мне слово или фразу, и я найду информацию из Википедии.\n"
        "Можешь выбрать язык поиска кнопками ниже.",
        reply_markup=keyboard
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == "lang_ru":
        user_languages[user_id] = "ru"
        lang_text = "Русский 🇷🇺"
    elif query.data == "lang_en":
        user_languages[user_id] = "en"
        lang_text = "English 🇬🇧"
    elif query.data == "lang_uz":
        user_languages[user_id] = "uz"
        lang_text = "O'zbek 🇺🇿"
    else:
        await query.answer("Неизвестный язык.")
        return

    await query.answer()
    await query.edit_message_text(f"🌐 Язык успешно изменён на {lang_text}.\nТеперь отправь запрос!")

async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, DEFAULT_LANG)

    if not query:
        await update.message.reply_text("❗ Пожалуйста, отправь непустой запрос.")
        return

    if len(query) > MAX_QUERY_LENGTH:
        await update.message.reply_text(
            f"⚠️ Слишком длинный запрос! Максимум {MAX_QUERY_LENGTH} символов."
        )
        return

    try:
        wikipedia.set_lang(lang)
        summary = wikipedia.summary(query, sentences=3)
        page = wikipedia.page(query)
        url = page.url

        text = f"📚 Вот что я нашёл для тебя:\n\n{summary}\n\n🔗 [Подробнее на Википедии]({url})"

        # Ищем подходящее изображение
        image_url = None
        for img in page.images:
            if img.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_url = img
                break

        if image_url:
            await update.message.reply_photo(photo=image_url, caption=text, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, parse_mode="Markdown")

    except wikipedia.exceptions.DisambiguationError as e:
        options = e.options[:5]
        opts_text = "\n".join(f"- {opt}" for opt in options)
        await update.message.reply_text(
            f"🤔 Запрос слишком общий, уточни одну из тем:\n{opts_text}"
        )
    except wikipedia.exceptions.PageError:
        await update.message.reply_text(
            "😞 Я не нашёл статью по твоему запросу. Попробуй другой запрос."
        )
    except Exception as e:
        await update.message.reply_text(
            f"⚠️ Произошла ошибка: {str(e)}. Попробуй позже."
        )


if __name__ == "__main__":
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    PORT = int(os.getenv("PORT", "8443"))
    RENDER_HOST = os.getenv('RENDER_EXTERNAL_HOSTNAME')

    if not TOKEN or not RENDER_HOST:
        raise ValueError("Отсутствует TELEGRAM_TOKEN или RENDER_EXTERNAL_HOSTNAME в переменных окружения!")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_language))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question))

    WEBHOOK_PATH = f"/{TOKEN}"
    WEBHOOK_URL = f"https://{RENDER_HOST}{WEBHOOK_PATH}"

    print(f"Устанавливаю вебхук: {WEBHOOK_URL}")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL
    )