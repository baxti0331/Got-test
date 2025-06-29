import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import openai

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("TELEGRAM_TOKEN или OPENAI_API_KEY не найдены!")

openai.api_key = OPENAI_API_KEY

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Словарь для хранения истории переписки по chat_id
user_histories = {}

MAX_HISTORY_LENGTH = 10  # Максимум последних сообщений для контекста

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    user_histories[user_id] = []
    await update.message.reply_text("Привет! Я ИИ-бот на базе ChatGPT. Напиши мне что-нибудь!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    user_text = update.message.text

    if user_id not in user_histories:
        user_histories[user_id] = []

    # Добавляем сообщение пользователя в историю
    user_histories[user_id].append({"role": "user", "content": user_text})

    # Обрезаем историю, чтобы не превышать лимит
    if len(user_histories[user_id]) > MAX_HISTORY_LENGTH:
        user_histories[user_id] = user_histories[user_id][-MAX_HISTORY_LENGTH:]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=user_histories[user_id],
            max_tokens=500,
            temperature=0.7,
        )
        reply = response['choices'][0]['message']['content'].strip()

        # Добавляем ответ бота в историю
        user_histories[user_id].append({"role": "assistant", "content": reply})
    except Exception as e:
        logging.error(f"Ошибка OpenAI: {e}")
        reply = "Извини, произошла ошибка при обработке запроса."

    await update.message.reply_text(reply)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()