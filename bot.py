import os
import random
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не найден!")

logging.basicConfig(level=logging.INFO)

# База вопросов, шуток и загадок
quiz_questions = [
    {"question": "Сколько будет 3 + 5?", "answers": ["7", "8", "9"], "correct": "8"},
    {"question": "Столица Италии?", "answers": ["Рим", "Мадрид", "Париж"], "correct": "Рим"},
    {"question": "Какой океан самый большой?", "answers": ["Атлантический", "Индийский", "Тихий"], "correct": "Тихий"},
]

jokes = [
    "Почему программисты путают Хэллоуин и Рождество? Потому что 31 Oct = 25 Dec.",
    "Всё ломается. Даже код, который ещё не написал.",
    "Как зовут программиста-волшебника? Алгоритмович!"
]

truth_or_lie_statements = [
    {"statement": "Солнце — звезда.", "truth": True},
    {"statement": "Человек может дышать под водой без устройств.", "truth": False},
    {"statement": "Python — это язык программирования.", "truth": True},
]

riddles = [
    {"question": "Что можно увидеть с закрытыми глазами?", "answers": ["Сон", "Свет", "Ничего"], "correct": "Сон"},
    {"question": "Что всегда идёт, но никогда не приходит?", "answers": ["Время", "Поезд", "Эхо"], "correct": "Время"},
]

# Главное меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎯 Викторина", callback_data="quiz")],
        [InlineKeyboardButton("😂 Анекдот", callback_data="joke")],
        [InlineKeyboardButton("⏰ Время", callback_data="time")],
        [InlineKeyboardButton("🎲 Угадай число", callback_data="guess")],
        [InlineKeyboardButton("✊ Камень/Ножницы/Бумага", callback_data="rps")],
        [InlineKeyboardButton("🎲 Бросок кубика", callback_data="dice")],
        [InlineKeyboardButton("🧠 Правда или ложь", callback_data="truthlie")],
        [InlineKeyboardButton("🕵 Загадка", callback_data="riddle")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Выбери действие:", reply_markup=reply_markup)

# Обработка кнопок
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "quiz":
        question = random.choice(quiz_questions)
        context.user_data['quiz'] = question
        buttons = [[InlineKeyboardButton(ans, callback_data=f"answer:{ans}")] for ans in question['answers']]
        await query.edit_message_text(question['question'], reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data.startswith("answer:"):
        selected = query.data.split(":", 1)[1]
        question = context.user_data.get('quiz')
        result = "✅ Верно!" if question and selected == question['correct'] else f"❌ Неправильно. Ответ: {question['correct']}"
        await query.edit_message_text(result)

    elif query.data == "joke":
        await query.edit_message_text(random.choice(jokes))

    elif query.data == "time":
        now = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        await query.edit_message_text(f"Текущее время: {now}")

    elif query.data == "guess":
        number = random.randint(1, 5)
        context.user_data['secret'] = number
        buttons = [[InlineKeyboardButton(str(n), callback_data=f"guess_number:{n}")] for n in range(1, 6)]
        await query.edit_message_text("Я загадал число от 1 до 5. Попробуй угадать:", reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data.startswith("guess_number:"):
        guess = int(query.data.split(":")[1])
        secret = context.user_data.get('secret')
        result = "🎉 Ты угадал!" if guess == secret else f"Нет, я загадал {secret}."
        await query.edit_message_text(result)

    elif query.data == "rps":
        buttons = [
            [InlineKeyboardButton("Камень", callback_data="rps_choice:Камень"),
             InlineKeyboardButton("Ножницы", callback_data="rps_choice:Ножницы"),
             InlineKeyboardButton("Бумага", callback_data="rps_choice:Бумага")]
        ]
        await query.edit_message_text("Выбери свой ход:", reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data.startswith("rps_choice:"):
        user_choice = query.data.split(":")[1]
        bot_choice = random.choice(["Камень", "Ножницы", "Бумага"])
        outcome = "Ничья!"
        if (user_choice == "Камень" and bot_choice == "Ножницы") or \
           (user_choice == "Ножницы" and bot_choice == "Бумага") or \
           (user_choice == "Бумага" and bot_choice == "Камень"):
            outcome = "Ты победил!"
        elif user_choice != bot_choice:
            outcome = "Бот победил!"
        await query.edit_message_text(f"Ты выбрал: {user_choice}\nБот выбрал: {bot_choice}\n{outcome}")

    elif query.data == "dice":
        roll = random.randint(1, 6)
        await query.edit_message_text(f"Ты бросил кубик и выпало: {roll}")

    elif query.data == "truthlie":
        statement = random.choice(truth_or_lie_statements)
        context.user_data['truth'] = statement
        buttons = [
            [InlineKeyboardButton("Правда", callback_data="truth_answer:True"),
             InlineKeyboardButton("Ложь", callback_data="truth_answer:False")]
        ]
        await query.edit_message_text(statement['statement'], reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data.startswith("truth_answer:"):
        user_answer = query.data.split(":")[1] == "True"
        correct = context.user_data.get('truth', {}).get('truth')
        result = "✅ Верно!" if user_answer == correct else "❌ Неправильно."
        await query.edit_message_text(result)

    elif query.data == "riddle":
        riddle = random.choice(riddles)
        context.user_data['riddle'] = riddle
        buttons = [[InlineKeyboardButton(ans, callback_data=f"riddle_answer:{ans}")] for ans in riddle['answers']]
        await query.edit_message_text(riddle['question'], reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data.startswith("riddle_answer:"):
        selected = query.data.split(":")[1]
        riddle = context.user_data.get('riddle')
        result = "✅ Правильно!" if riddle and selected == riddle['correct'] else f"❌ Нет, ответ: {riddle['correct']}"
        await query.edit_message_text(result)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я тебя не понял. Используй /start для вызова меню.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()