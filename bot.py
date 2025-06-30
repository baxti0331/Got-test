import os
import json
import threading
import time
import schedule
from datetime import datetime, timedelta
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)

tasks = []
data_file = "tasks.json"

def load_tasks():
    global tasks
    if os.path.exists(data_file):
        with open(data_file, "r") as f:
            tasks = json.load(f)
    else:
        tasks = []

def save_tasks():
    with open(data_file, "w") as f:
        json.dump(tasks, f, indent=4)

def control_panel(update: Update, context: CallbackContext):
    buttons = [
        [InlineKeyboardButton("➕ Добавить по интервалу", callback_data="add_interval")],
        [InlineKeyboardButton("📅 Добавить ежедневное", callback_data="add_daily")],
        [InlineKeyboardButton("📆 Добавить еженедельное", callback_data="add_weekly")],
        [InlineKeyboardButton("🗓 Добавить ежемесячное", callback_data="add_monthly")],
        [InlineKeyboardButton("📋 Список задач", callback_data="show_tasks")]
    ]
    markup = InlineKeyboardMarkup(buttons)
    update.message.reply_text("Панель управления:", reply_markup=markup)

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == "add_interval":
        query.edit_message_text("Отправь текст сообщения и интервал в минутах через `|`. Пример:\nПривет! | 15", parse_mode='Markdown')
        context.user_data["mode"] = "interval"
        context.user_data["last_task"] = None

    elif query.data == "add_daily":
        query.edit_message_text("Отправь текст сообщения и время (HH:MM) через `|`. Пример:\nДоброе утро! | 09:00", parse_mode='Markdown')
        context.user_data["mode"] = "daily"
        context.user_data["last_task"] = None

    elif query.data == "add_weekly":
        query.edit_message_text("Отправь текст сообщения и день недели/время через `|`. Пример:\nОтчёт | Monday 10:00", parse_mode='Markdown')
        context.user_data["mode"] = "weekly"
        context.user_data["last_task"] = None

    elif query.data == "add_monthly":
        query.edit_message_text("Отправь текст сообщения и день месяца/время через `|`. Пример:\nСобрание | 1 10:00", parse_mode='Markdown')
        context.user_data["mode"] = "monthly"
        context.user_data["last_task"] = None

    elif query.data == "show_tasks":
        text = "Текущие задачи:\n"
        for idx, task in enumerate(tasks, 1):
            desc = f"{idx}. [{task['type']}] {task['text'][:30]}"
            if task['type'] == "interval":
                desc += f" — каждые {task['interval']} минут"
            elif task['type'] == "daily":
                desc += f" — каждый день в {task['time']}"
            elif task['type'] == "weekly":
                desc += f" — каждую {task['weekday']} в {task['time']}"
            elif task['type'] == "monthly":
                desc += f" — каждый месяц {task['day']} числа в {task['time']}"
            text += desc + "\n"
        if not tasks:
            text = "Нет активных задач."
        query.edit_message_text(text)

def message_handler(update: Update, context: CallbackContext):
    mode = context.user_data.get("mode")

    # Добавляем проверку на фото/видео в отдельную ветку ниже
    if update.message.text and mode:
        try:
            if mode == "interval":
                text, interval = update.message.text.split("|")
                task = {
                    "text": text.strip(),
                    "interval": int(interval.strip()),
                    "type": "interval",
                    "photo_file_id": None,
                    "video_file_id": None,
                    "last_sent": None
                }
                tasks.append(task)
                save_tasks()
                update.message.reply_text(f"Задача добавлена: каждые {task['interval']} минут.\nТеперь можешь прислать фото или видео для этого сообщения.")
                context.user_data["last_task"] = task

            elif mode == "daily":
                text, time_str = update.message.text.split("|")
                task = {
                    "text": text.strip(),
                    "time": time_str.strip(),
                    "type": "daily",
                    "photo_file_id": None,
                    "video_file_id": None
                }
                tasks.append(task)
                save_tasks()
                schedule.every().day.at(task["time"]).do(send_task, task=task)
                update.message.reply_text(f"Ежедневная задача добавлена на {task['time']}. Теперь можешь прислать фото или видео.")
                context.user_data["last_task"] = task

            elif mode == "weekly":
                text, when = update.message.text.split("|")
                weekday, time_str = when.strip().split()
                task = {
                    "text": text.strip(),
                    "weekday": weekday.capitalize(),
                    "time": time_str,
                    "type": "weekly",
                    "photo_file_id": None,
                    "video_file_id": None
                }
                tasks.append(task)
                save_tasks()
                getattr(schedule.every(), weekday.lower()).at(task["time"]).do(send_task, task=task)
                update.message.reply_text(f"Еженедельная задача добавлена: {task['weekday']} в {task['time']}. Теперь можешь прислать фото или видео.")
                context.user_data["last_task"] = task

            elif mode == "monthly":
                text, when = update.message.text.split("|")
                day, time_str = when.strip().split()
                task = {
                    "text": text.strip(),
                    "day": int(day),
                    "time": time_str,
                    "type": "monthly",
                    "photo_file_id": None,
                    "video_file_id": None,
                    "last_sent_date": None
                }
                tasks.append(task)
                save_tasks()
                update.message.reply_text(f"Ежемесячная задача добавлена: {task['day']} числа в {task['time']}. Теперь можешь прислать фото или видео.")
                context.user_data["last_task"] = task

            context.user_data["mode"] = None
        except Exception as e:
            update.message.reply_text(f"Ошибка формата или данных: {e}\nПроверь формат и попробуй ещё раз.")
            return

    # Если прислали фото или видео — добавляем к последней задаче
    last_task = context.user_data.get("last_task")
    if last_task:
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            last_task["photo_file_id"] = file_id
            last_task["video_file_id"] = None
            save_tasks()
            update.message.reply_text("Фото добавлено к последнему сообщению.")
            context.user_data["last_task"] = None

        elif update.message.video:
            file_id = update.message.video.file_id
            last_task["video_file_id"] = file_id
            last_task["photo_file_id"] = None
            save_tasks()
            update.message.reply_text("Видео добавлено к последнему сообщению.")
            context.user_data["last_task"] = None

def send_task(task):
    try:
        if task.get("photo_file_id"):
            bot.send_photo(chat_id=CHAT_ID, photo=task["photo_file_id"], caption=task["text"])
        elif task.get("video_file_id"):
            bot.send_video(chat_id=CHAT_ID, video=task["video_file_id"], caption=task["text"])
        else:
            bot.send_message(chat_id=CHAT_ID, text=task["text"])

        task["last_sent"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_tasks()
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")

def task_loop():
    while True:
        now = datetime.now()
        for task in tasks:
            if task["type"] == "interval":
                last = datetime.strptime(task["last_sent"], "%Y-%m-%d %H:%M:%S") if task.get("last_sent") else None
                if not last or (now - last) >= timedelta(minutes=task["interval"]):
                    send_task(task)

            elif task["type"] == "monthly":
                last_date = task.get("last_sent_date")
                if now.day == task["day"] and now.strftime("%H:%M") == task["time"]:
                    if last_date != now.strftime("%Y-%m-%d"):
                        send_task(task)
                        task["last_sent_date"] = now.strftime("%Y-%m-%d")
                        save_tasks()

        schedule.run_pending()
        time.sleep(10)

def main():
    load_tasks()

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", control_panel))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))
    dp.add_handler(MessageHandler(Filters.photo | Filters.video, message_handler))

    for task in tasks:
        if task["type"] == "daily":
            schedule.every().day.at(task["time"]).do(send_task, task=task)
        elif task["type"] == "weekly":
            getattr(schedule.every(), task["weekday"].lower()).at(task["time"]).do(send_task, task=task)

    threading.Thread(target=task_loop, daemon=True).start()

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()