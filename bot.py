import logging
import os
import wikipedia
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(level=logging.INFO)

wikipedia.set_lang("ru")

MAX_QUERY_LENGTH = 100

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я твой Википедия-бот.\n"
        "Напиши мне любой вопрос или слово, и я постараюсь найти информацию в Википедии."
    )

async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()

    if not query:
        await update.message.reply_text("❗ Пожалуйста, отправь непустой запрос.")
        return

    if len(query) > MAX_QUERY_LENGTH:
        await update.message.reply_text(
            f"⚠️ Слишком длинный запрос! Пожалуйста, не более {MAX_QUERY_LENGTH} символов."
        )
        return

    try:
        summary = wikipedia.summary(query, sentences=3)
        page = wikipedia.page(query)
        url = page.url

        text = f"📚 Вот что я нашёл для тебя:\n\n{summary}\n\nНадеюсь, эта информация поможет! 😊"

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Подробнее на Википедии", url=url)]]
        )

        await update.message.reply_text(text, reply_markup=keyboard)

    except wikipedia.exceptions.DisambiguationError as e:
        options = e.options[:5]
        opts_text = "\n".join(f"- {opt}" for opt in options)
        await update.message.reply_text(
            f"🤔 Твой запрос слишком общий, уточни, пожалуйста, одну из тем:\n{opts_text}"
        )
    except wikipedia.exceptions.PageError:
        await update.message.reply_text(
            "😞 Извините, я не нашёл статью по твоему запросу. Попробуй другой запрос."
        )
    except Exception:
        await update.message.reply_text(
            "⚠️ Произошла ошибка при обработке запроса. Попробуй позже."
        )


if __name__ == "__main__":
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    PORT = int(os.getenv("PORT", "8443"))  # Render даёт порт в env

    if not TOKEN:
        raise ValueError("Отсутствует TELEGRAM_TOKEN в переменных окружения!")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question))

    # Вебхук URL Telegram будет ждать по пути /<TOKEN>
    WEBHOOK_PATH = f"/{TOKEN}"
    WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"

    print(f"Setting webhook to {WEBHOOK_URL}")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL
    )