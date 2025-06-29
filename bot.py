import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import openai
import os

# Вставь сюда свои токены
TELEGRAM_TOKEN = "7291198714:AAE2x4jpnj0bnfZ300MZww-Du1HH_ZkzeSY"
OPENAI_API_KEY = "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"

openai.api_key = OPENAI_API_KEY

# Включаем логирование (необязательно, но удобно)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я ИИ-бот на базе ChatGPT. Напиши мне что-нибудь!")

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.message.chat_id
    
    # Отправляем запрос в OpenAI
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_text}]
        )
        reply = response['choices'][0]['message']['content']
    except Exception as e:
        reply = "Извини, произошла ошибка при обработке запроса."

    await update.message.reply_text(reply)

# Главная функция запуска бота
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
