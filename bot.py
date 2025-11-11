import os
import logging
import sqlite3
from flask import Flask, request
from dotenv import load_dotenv
import telebot

# .env fayldan o‘qish
load_dotenv()

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Muhit o‘zgaruvchilari
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", 8000))
DB_FILE = "movies.db"

# Telegram bot
bot = telebot.TeleBot(TOKEN)

# Flask app
app = Flask(__name__)

# SQLite bazasini yaratish
def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE,
                message_id INTEGER,
                channel_id INTEGER
            )
        """)
        conn.commit()
        conn.close()
        logger.info("🎬 SQLite bazasi tayyor")
    except Exception as e:
        logger.error(f"Database yaratishda xato: {e}")

init_db()

# Kino qo‘shish
def add_movie_to_db(title, message_id, channel_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO movies (title, message_id, channel_id) VALUES (?, ?, ?)",
                  (title.lower(), message_id, channel_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        logger.error(f"DB xato: {e}")
        return False

# Kino qidirish
def search_movie_in_db(name):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id, title, message_id, channel_id FROM movies WHERE LOWER(title) LIKE ? LIMIT 10",
                  ('%' + name.lower() + '%',))
        results = c.fetchall()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Qidiruv xato: {e}")
        return []

# /start komandasi
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 Xush kelibsiz! 🎬 Kino bot ishga tushdi.\n\n/search <kino nomi> orqali qidiruv qiling.", parse_mode="HTML")

# /search komandasi
@bot.message_handler(commands=['search'])
def search(message):
    query = message.text.split(maxsplit=1)
    if len(query) < 2:
        bot.reply_to(message, "❗ Kino nomini yozing: /search Inter", parse_mode="HTML")
        return

    movie_name = query[1]
    results = search_movie_in_db(movie_name)

    if results:
        for _, title, msg_id, ch_id in results:
            try:
                bot.forward_message(chat_id=message.chat.id, from_chat_id=ch_id, message_id=msg_id)
            except Exception as e:
                logger.error(f"Yuborishda xato: {e}")
        bot.send_message(message.chat.id, f"✅ Topildi: {len(results)} ta kino", parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "❌ Kino topilmadi!", parse_mode="HTML")

# /add komandasi (admin uchun)
@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "🚫 Ruxsat yo‘q!")
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "❗ Format: /add <message_id> <kino_nomi>")
        return

    try:
        msg_id = int(parts[1])
        title = parts[2]
        if add_movie_to_db(title, msg_id, CHANNEL_ID):
            bot.reply_to(message, f"✅ Kino qo‘shildi: {title}")
        else:
            bot.reply_to(message, f"⚠ Kino allaqachon mavjud: {title}")
    except Exception as e:
        logger.error(f"Qo‘shishda xato: {e}")
        bot.reply_to(message, "❌ Xatolik yuz berdi")

# /list komandasi — tugmalar bilan kino ro‘yxati
@bot.message_handler(commands=['list'])
def list_movies(message):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id, title FROM movies ORDER BY title LIMIT 50")
        movies = c.fetchall()
        conn.close()

        if not movies:
            bot.reply_to(message, "❌ Kino bazasi bo‘sh!", parse_mode="HTML")
            return

        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        for movie_id, title in movies:
            btn = telebot.types.InlineKeyboardButton(
                text=title[:40] + ("..." if len(title) > 40 else ""),
                callback_data=f"movie_{movie_id}"
            )
            markup.add(btn)

        bot.send_message(
            message.chat.id,
            "📁 Kino ro‘yxati:\n\nQuyidagilardan birini tanlang:",
            reply_markup=markup,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Ro‘yxat xato: {e}")
        bot.reply_to(message, "❌ Ro‘yxatni olishda xatolik", parse_mode="HTML")

# Tugmaga bosilganda kino yuborish
@bot.callback_query_handler(func=lambda call: call.data.startswith("movie_"))
def movie_callback(call):
    try:
        movie_id = int(call.data.split("_")[1])
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT message_id, channel_id, title FROM movies WHERE id = ?", (movie_id,))
        result = c.fetchone()
        conn.close()

        if not result:
            bot.answer_callback_query(call.id, "❌ Kino topilmadi!", show_alert=True)
            return

        msg_id, ch_id, title = result
        bot.forward_message(chat_id=call.from_user.id, from_chat_id=ch_id, message_id=msg_id)
        bot.answer_callback_query(call.id, f"🎬 {title} yuborildi!", show_alert=False)
        logger.info(f"Kino yuborildi: {title}")

    except Exception as e:
        logger.error(f"Callback xato: {e}")
        bot.answer_callback_query(call.id, "❌ Yuborishda xatolik", show_alert=True)

# Webhook endpoint
@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    try:
        json_data = request.get_json()
        if json_data:
            update = telebot.types.Update.de_json(json_data)
            bot.process_new_updates([update])
    except Exception as e:
        logger.error(f"Webhook xato: {e}")
    return "OK", 200

# Healthcheck
@app.route('/health', methods=['GET'])
def health():
    return {"status": "ok"}, 200

# Webhookni o‘rnatish
def set_webhook():
    try:
        url = f"{WEBHOOK_URL}/webhook"
        bot.remove_webhook()
        bot.set_webhook(url=url)
        logger.info(f"Webhook o‘rnatildi: {url}")
    except Exception as e:
        logger.error(f"Webhook o‘rnatishda xato: {e}")

# Ishga tushirish
if __name__ == '__main__':
    logger.info("🚀 Bot ishga tushdi...")
    if WEBHOOK_URL and "render.com" in WEBHOOK_URL:
        set_webhook()
        app.run(host=FLASK_HOST, port=FLASK_PORT)
    else:
        bot.infinity_polling()
