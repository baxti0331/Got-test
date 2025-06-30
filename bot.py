import logging
import os
import wikipedia
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, CallbackQueryHandler, filters
)

logging.basicConfig(level=logging.INFO)

DEFAULT_LANG = "ru"
wikipedia.set_lang(DEFAULT_LANG)

user_languages = {}
MAX_QUERY_LENGTH = 100

MESSAGES = {
    "ru": {
        "start": "👋 Привет! Я Википедия-Бот.\n\nОтправь мне слово или фразу, и я найду информацию из Википедии.\nМожешь выбрать язык поиска кнопками ниже.",
        "language_set": "🌐 Язык успешно изменён на Русский 🇷🇺.\nТеперь отправь запрос!",
        "empty": "❗ Пожалуйста, отправь непустой запрос.",
        "long": f"⚠️ Слишком длинный запрос! Максимум {MAX_QUERY_LENGTH} символов.",
        "not_found": "😞 Я не нашёл статью по твоему запросу. Попробуй другой запрос.",
        "disambiguation": "🤔 Запрос слишком общий, уточни одну из тем:",
        "error": "⚠️ Произошла ошибка. Попробуй позже.",
        "result": "📚 Вот что я нашёл для тебя:",
        "more": "Подробнее на Википедии"
    },
    "en": {
        "start": "👋 Hi! I'm your Wikipedia Bot.\n\nSend me any word or phrase, and I'll find information from Wikipedia.\nYou can change the search language using the buttons below.",
        "language_set": "🌐 Language changed to English 🇬🇧.\nNow send your query!",
        "empty": "❗ Please send a non-empty query.",
        "long": f"⚠️ Your query is too long! Maximum {MAX_QUERY_LENGTH} characters.",
        "not_found": "😞 I couldn't find an article for your query. Try another one.",
        "disambiguation": "🤔 Your query is too general, please clarify one of these topics:",
        "error": "⚠️ An error occurred. Please try again later.",
        "result": "📚 Here's what I found for you:",
        "more": "Read more on Wikipedia"
    },
    "uz": {
        "start": "👋 Salom! Men Vikipediya botiman.\n\nMenga so'z yoki ibora yuboring, men Vikipediyadan ma'lumot topaman.\nTilni pastdagi tugmalar orqali o'zgartirishingiz mumkin.",
        "language_set": "🌐 Til o'zgartirildi: O'zbek 🇺🇿.\nEndi so'rov yuboring!",
        "empty": "❗ Iltimos, bo'sh so'rov yubormang.",
        "long": f"⚠️ So'rov juda uzun! Maksimal {MAX_QUERY_LENGTH} ta belgi.",
        "not_found": "😞 So'rov bo'yicha maqola topilmadi. Boshqa so'rov urinib ko'ring.",
        "disambiguation": "🤔 So'rovingiz juda umumiy, iltimos, quyidagi mavzulardan birini aniqlang:",
        "error": "⚠️ Xatolik yuz berdi. Keyinroq urinib ko'ring.",
        "result": "📚 Siz uchun topdim:",
        "more": "Vikipediyada batafsil"
    },
    "kk": {
        "start": "👋 Сәлем! Мен Уикипедия ботымын.\n\nМаған сөз немесе тіркес жіберіңіз, мен Уикипедиядан ақпарат табамын.\nТілді төмендегі түймелер арқылы өзгертуге болады.",
        "language_set": "🌐 Тіл өзгертілді: Қазақша 🇰🇿.\nЕнді сұранысты жіберіңіз!",
        "empty": "❗ Өтінемін, бос сұраныс жібермеңіз.",
        "long": f"⚠️ Сұраныс тым ұзақ! Ең көбі {MAX_QUERY_LENGTH} таңба.",
        "not_found": "😞 Сұраныс бойынша мақала табылмады. Басқа сұраныс жасап көріңіз.",
        "disambiguation": "🤔 Сұраныс тым жалпы, нақтылап таңдаңыз:",
        "error": "⚠️ Қате пайда болды. Кейінірек қайталап көріңіз.",
        "result": "📚 Міне, сізге тапқаным:",
        "more": "Уикипедияда толығырақ"
    },
    "ky": {
        "start": "👋 Салам! Мен Википедия боту.\n\nМага сөз же сүйлөм жибериңиз, мен Википедиядан маалымат табам.\nТилди төмөнкү баскычтар аркылуу алмаштыра аласыз.",
        "language_set": "🌐 Тил өзгөртүлдү: Кыргызча 🇰🇬.\nЭми суроо жибериңиз!",
        "empty": "❗ Сураныч, бош суроо жибербеңиз.",
        "long": f"⚠️ Суроо өтө узун! Максималдуу {MAX_QUERY_LENGTH} тамга.",
        "not_found": "😞 Суроо боюнча макала табылган жок. Башка суроо берип көрүңүз.",
        "disambiguation": "🤔 Сурооңуз өтө жалпы, тактап бериңиз:",
        "error": "⚠️ Ката кетти. Кийинчерээк кайрылыңыз.",
        "result": "📚 Сиз үчүн таптым:",
        "more": "Википедиядан кененирээк окуу"
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_languages[user_id] = DEFAULT_LANG

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru"),
            InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
        ],
        [
            InlineKeyboardButton("O'zbek 🇺🇿", callback_data="lang_uz"),
            InlineKeyboardButton("Қазақша 🇰🇿", callback_data="lang_kk"),
            InlineKeyboardButton("Кыргызча 🇰🇬", callback_data="lang_ky")
        ]
    ])

    await update.message.reply_text(MESSAGES[DEFAULT_LANG]["start"], reply_markup=keyboard)

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    code = query.data.replace("lang_", "")
    if code in MESSAGES:
        user_languages[user_id] = code
        await query.answer()
        await query.edit_message_text(MESSAGES[code]["language_set"])
    else:
        await query.answer("Unknown language.")

async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, DEFAULT_LANG)
    msg = MESSAGES[lang]

    if not query:
        await update.message.reply_text(msg["empty"])
        return

    if len(query) > MAX_QUERY_LENGTH:
        await update.message.reply_text(msg["long"])
        return

    try:
        wikipedia.set_lang(lang)
        try:
            summary = wikipedia.summary(query, sentences=3)
            page = wikipedia.page(query)
        except (wikipedia.exceptions.PageError, wikipedia.exceptions.DisambiguationError):
            search_results = wikipedia.search(query)
            if not search_results:
                await update.message.reply_text(msg["not_found"])
                return
            corrected_query = search_results[0]
            summary = wikipedia.summary(corrected_query, sentences=3)
            page = wikipedia.page(corrected_query)

        url = page.url
        text = f"{msg['result']}\n\n{summary}"

        image_url = next((img for img in page.images if img.lower().endswith(('.jpg', '.jpeg', '.png'))), None)

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(msg['more'], url=url)]]
        )

        if image_url:
            await update.message.reply_photo(photo=image_url, caption=text, reply_markup=keyboard)
        else:
            await update.message.reply_text(text, reply_markup=keyboard)

    except wikipedia.exceptions.DisambiguationError as e:
        options = e.options[:5]
        opts_text = "\n".join(f"- {opt}" for opt in options)
        await update.message.reply_text(f"{msg['disambiguation']}\n{opts_text}")
    except wikipedia.exceptions.PageError:
        await update.message.reply_text(msg["not_found"])
    except Exception:
        await update.message.reply_text(msg["error"])


if __name__ == "__main__":
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    PORT = int(os.getenv("PORT", "8443"))
    RENDER_HOST = os.getenv('RENDER_EXTERNAL_HOSTNAME')

    if not TOKEN or not RENDER_HOST:
        raise ValueError("Отсутствует TELEGRAM_TOKEN или RENDER_EXTERNAL_HOSTNAME в переменных окружениях!")

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