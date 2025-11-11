import telebot
import requests
import logging
import sqlite3
import os
import re
from dotenv import load_dotenv
from flask import Flask, request

# .env fayLdan load qilish
load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sozlamalar (environment variables dan)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", 8000))
DB_FILE = "movies.db"

# Bot yaratish
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Flask app (webhook uchun)
app = Flask(__name__)

# Database yaratish
def init_db():
    """Ma'lumotlar bazasini yaratish"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS movies
                     (id INTEGER PRIMARY KEY,
                      title TEXT UNIQUE,
                      message_id INTEGER,
                      channel_id INTEGER)''')
        conn.commit()
        conn.close()
        logger.info("✅ Database tayyoq")
    except Exception as e:
        logger.error(f"Database init xato: {e}")

init_db()

def add_movie_to_db(title, message_id, channel_id):
    """Kinoni ma'lumotlar bazasiga qo'shish"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO movies (title, message_id, channel_id) VALUES (?, ?, ?)",
                  (title.lower(), message_id, channel_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False  # Kino allaqachon bor
    except Exception as e:
        logger.error(f"DB xato: {e}")
        return False

def search_movie_in_db(movie_name):
    """Qisman va seriyali qidiruv"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        query_raw = movie_name.strip()
        low = query_raw.lower()

        # Seriya raqamini aniqlash
        m = re.search(r"^(.+?)\s+(\d{1,4})$", query_raw.strip())
        if m:
            base = m.group(1).strip().lower()
            try:
                target_num = int(m.group(2))
            except:
                target_num = None

            # Base bilan mos keluvchi kinolarni olish
            c.execute("SELECT id, message_id, channel_id, title FROM movies WHERE LOWER(title) LIKE ?", (f"%{base}%",))
            rows = c.fetchall()

            exact = []
            close = []
            for row in rows:
                title = row[3]
                nums = [int(x) for x in re.findall(r"\d+", title)]
                if nums:
                    if target_num in nums:
                        exact.append(row)
                    else:
                        dif = min(abs(n - target_num) for n in nums)
                        close.append((dif, row))

            if exact:
                conn.close()
                return exact

            if close:
                close_sorted = [r for d, r in sorted(close, key=lambda x: x[0])]
                conn.close()
                return close_sorted

        # Umumiy qisman qidiruv
        search_terms = [t for t in low.split() if len(t) > 1]
        if not search_terms:
            conn.close()
            return []

        conditions = []
        params = []
        for term in search_terms:
            conditions.append("LOWER(title) LIKE ?")
            params.append(f"%{term}%")

        sql = "SELECT id, message_id, channel_id, title FROM movies WHERE " + " OR ".join(conditions) + " LIMIT 100"
        c.execute(sql, params)
        results = c.fetchall()
        conn.close()

        def score(row):
            title = row[3].lower()
            return sum(1 for t in search_terms if t in title)

        sorted_results = sorted(results, key=lambda r: score(r), reverse=True)
        return sorted_results

    except Exception as e:
        logger.error(f"Qidirish xato: {e}")
        return []


@bot.message_handler(commands=['start'])
def start(message):
    """Start komandasi"""
    bot.reply_to(message, 
        "🎬 <b>KINO BOT - Kinolar Qidiruvi</b> 🎬\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👋 <b>Xush Kelibsiz!</b>\n\n"
        "� <b>Qidiruv Usullari:</b>\n"
        "  1️⃣ Kino nomini yozing (masalan:Flesh)\n"
        "  2️⃣ <code>/search Flesh 76</code> - To'g'ridan to'g'ri qidirish\n"
        "  3️⃣ <code>/list</code> - Barcha kinolar ro'yxati\n\n"
        "� <b>Maslahat:</b>\n"
        "  • <code>Flesh 76</code> yozsa → Flesh 76 topiladi\n"
        "  • <code>Flesh</code> yozsa → Barcha Flesh qismlari\n"
        "  • Qisman nom ham qidiradi\n\n"
        "�🔧 <b>Admin Komandalar:</b>\n"
        "  • <code>/index</code> - Kanaldan indexlash\n"
        "  • <code>/add ID NOM</code> - Kino qo'shish\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode='HTML'
    )


@bot.message_handler(commands=['search'])
def search_command(message):
    """Search komandasi: /search kino_nomi"""
    try:
        # Komandadan keyin keladigan matnni olish
        text = message.text.split(maxsplit=1)
        if len(text) < 2:
            bot.reply_to(message, 
                "❌ <b>Noto'g'ri foydalanish!</b>\n\n"
                "✅ <b>To'g'ri foydalanish:</b>\n"
                "<code>/search Flesh 76</code>\n\n"
                "💡 <b>Masallar:</b>\n"
                "  • <code>/search Flesh</code> - Barcha Flesh\n"
                "  • <code>/search Flesh 76</code> - Flesh 76\n"
                "  • <code>/search Inter</code> - Interstellar kabi",
                parse_mode='HTML')
            return
        
        movie_name = text[1].strip()
        status_msg = bot.reply_to(message, 
            f"🔍 <b>Qidirilmoqda:</b>\n<code>{movie_name}</code>\n\n⏳ Biroz kuting...",
            parse_mode='HTML')
        
        # Ma'lumotlar bazasida qidirish
        results = search_movie_in_db(movie_name)
        
        if results:
            bot.delete_message(message.chat.id, status_msg.message_id)
            
            sent_count = 0
            for movie_id, msg_id, ch_id, title in results[:5]:  # Birinchi 5 ta
                try:
                    # Kinoni to'g'ridan-to'g'ri yuborish
                    bot.forward_message(
                        chat_id=message.chat.id,
                        from_chat_id=ch_id,
                        message_id=msg_id
                    )
                    sent_count += 1
                    logger.info(f"Kino yuborildi (search): {title}")
                except Exception as e:
                    logger.error(f"Forward xato: {e}")
            
            summary = (
                f"✅ <b>Qidiruv Natijalari</b>\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"🔎 Qidirilgan: <code>{movie_name}</code>\n"
                f"📹 Yuborildi: <b>{sent_count}</b> ta\n"
            )
            if len(results) > 5:
                summary += f"📌 Yana: <b>{len(results) - 5}</b> ta mavjud\n"
            summary += "━━━━━━━━━━━━━━━━"
            
            bot.send_message(message.chat.id, summary, parse_mode='HTML')
        else:
            bot.delete_message(message.chat.id, status_msg.message_id)
            bot.reply_to(message, 
                f"❌ <b>Topilmadi!</b>\n\n"
                f"🔎 Qidirilgan: <code>{movie_name}</code>\n\n"
                f"💡 <b>Maslahat:</b>\n"
                f"  • Nomi boshqacha bo'lishi mumkin\n"
                f"  • Qismi bilan yozib ko'ring\n"
                f"  • <code>/list</code> bilan barcha kinolarni ko'ring",
                parse_mode='HTML')
    
    except Exception as e:
        logger.error(f"Search xato: {e}")
        bot.reply_to(message, f"❌ Xato: {str(e)[:100]}")


@bot.message_handler(commands=['list'])
def list_movies(message):
    """Barcha kinolarni ro'yxati tugmachalar bilan"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id, title FROM movies ORDER BY title LIMIT 100")
        movies = c.fetchall()
        conn.close()
        
        if not movies:
            bot.reply_to(message, "❌ <b>Ma'lumotlar bazasida kino yo'q</b>\n\n"
                        "💡 Siz admin bo'lsangiz, <code>/index</code> bilan kino qo'shing",
                        parse_mode='HTML')
            return
        
        # Inline tugmachalari yaratish
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        
        for movie_id, title in movies:
            # Chiroyli tugma
            btn = telebot.types.InlineKeyboardButton(
                text=f"▶️ {title[:40]}{'...' if len(title) > 40 else ''}",
                callback_data=f"movie_{movie_id}"
            )
            markup.add(btn)
        
        # Chiroyli header
        header = (
            "📚 <b>BARCHA KINOLAR</b> 📚\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📹 Jami: <b>{len(movies)}</b> ta kino\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👇 Quyidagi tugmalardan birini bosing:\n\n"
        )
        
        bot.send_message(
            message.chat.id,
            header,
            reply_markup=markup,
            parse_mode='HTML'
        )
    
    except Exception as e:
        logger.error(f"List xato: {e}")
        bot.reply_to(message, f"❌ Xato: {str(e)[:100]}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('movie_'))
def movie_callback(call):
    """Tugmaga bosilganda kino yuborish"""
    try:
        # Callback_data dan kino ID'sini olish
        movie_id = int(call.data.split('_')[1])
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT message_id, channel_id, title FROM movies WHERE id = ?", (movie_id,))
        result = c.fetchone()
        conn.close()
        
        if not result:
            bot.answer_callback_query(call.id, "❌ Kino topilmadi!", show_alert=True)
            return
        
        msg_id, ch_id, title = result
        
        # Kino yuborish
        try:
            bot.forward_message(
                chat_id=call.from_user.id,
                from_chat_id=ch_id,
                message_id=msg_id
            )
            bot.answer_callback_query(call.id, f"✅ '{title}' yuborildi!", show_alert=False)
            logger.info(f"Kino yuborildi (tugmadan): {title}")
        except Exception as e:
            logger.error(f"Yuborish xato: {e}")
            bot.answer_callback_query(call.id, f"❌ Yuborishda xato: {str(e)[:50]}", show_alert=True)
    
    except Exception as e:
        logger.error(f"Callback xato: {e}")
        bot.answer_callback_query(call.id, f"❌ Xato: {str(e)[:50]}", show_alert=True)


@bot.message_handler(commands=['add'])
def add_movie_command(message):
    """Admin: kino qo'shish: /add message_id kino_nomi"""
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Ruxsat yo'q!")
        return
    
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, "❌ Foydalanish: /add &lt;message_id&gt; &lt;kino_nomi&gt;", parse_mode='HTML')
            return
        
        msg_id = int(parts[1])
        movie_name = parts[2].strip()
        
        if add_movie_to_db(movie_name, msg_id, CHANNEL_ID):
            bot.reply_to(message, f"✅ Kino qo'shildi: <b>{movie_name}</b>", parse_mode='HTML')
        else:
            bot.reply_to(message, f"⚠️ Kino allaqachon mavjud: <b>{movie_name}</b>", parse_mode='HTML')
    
    except ValueError:
        bot.reply_to(message, "❌ Message ID raqam bo'lishi kerak!")
    except Exception as e:
        logger.error(f"Add xato: {e}")
        bot.reply_to(message, f"❌ Xato: {str(e)[:100]}")


@bot.message_handler(commands=['index'])
def index_movies(message):
    """Kanaldan kinolarni indexlash"""
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Ruxsat yo'q!")
        return
    
    try:
        status = bot.reply_to(message, "📚 Kanaldan kinolar o'qilmoqda...")
        
        count = 0
        try:
            # Kanaldan so'ngi 100 ta xabarni o'qish
            for message_id in range(1, 101):
                try:
                    msg = bot.get_message(CHANNEL_ID, message_id)
                    
                    if msg.text:
                        # Xabarda "🎬" yoki "Kino" bo'lsa, saqlash
                        text = msg.text.lower()
                        if "🎬" in text or "kino" in text or "film" in text:
                            # Kino nomini chiqarish
                            lines = msg.text.split('\n')
                            if lines:
                                movie_title = lines[0].replace('🎬', '').strip()
                                if add_movie_to_db(movie_title, message_id, CHANNEL_ID):
                                    count += 1
                except:
                    pass
        except Exception as e:
            logger.error(f"Indexlash xato: {e}")
        
        bot.delete_message(message.chat.id, status.message_id)
        bot.reply_to(message, f"✅ {count} ta kino indexed qilindi!")
        
    except Exception as e:
        logger.error(f"Admin xato: {e}")
        bot.reply_to(message, f"❌ Xato: {str(e)[:100]}")


@bot.message_handler(content_types=['document', 'video', 'photo'])
def handle_media(message):
    """Kino (video, rasm, dokument) yuborilsa avtomatik indexlab olish"""
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        # Matnni qabul qil (agar bo'lsa)
        if message.caption:
            movie_title = message.caption.strip()
        elif message.text:
            movie_title = message.text.strip()
        else:
            # Media nomi yoki ID dan olib qo'yish
            if message.document:
                movie_title = message.document.file_name or f"Kino_{message.message_id}"
            elif message.video:
                movie_title = message.video.file_name or f"Video_{message.message_id}"
            else:
                movie_title = f"Media_{message.message_id}"
        
        # Ma'lumotlar bazasiga qo'shish
        if add_movie_to_db(movie_title, message.message_id, message.chat.id):
            bot.reply_to(message, f"✅ Kino indexed: <b>{movie_title}</b>", parse_mode='HTML')
            logger.info(f"Kino indexed: {movie_title}")
        else:
            bot.reply_to(message, f"⚠️ Kino allaqachon indexed: <b>{movie_title}</b>", parse_mode='HTML')
    
    except Exception as e:
        logger.error(f"Media indexlash xato: {e}")
        bot.reply_to(message, f"❌ Xato: {str(e)[:100]}")


@bot.message_handler(func=lambda message: True)
def handle_movie_search(message):
    """Kino nomini yozsa to'g'ridan-to'g'ri yuboradi"""
    movie_name = message.text.strip()
    
    if message.text.startswith('/'):
        return
    
    try:
        status_msg = bot.reply_to(message, f"🔍 <b>Qidirilmoqda:</b> <i>{movie_name}</i>\n⏳ Biroz kuting...", 
                                  parse_mode='HTML')
        
        # Ma'lumotlar bazasida qidirish
        results = search_movie_in_db(movie_name)
        
        if results:
            bot.delete_message(message.chat.id, status_msg.message_id)
            
            # To'g'ridan-to'g'ri kinolarni yuborish
            sent_count = 0
            for movie_id, msg_id, ch_id, title in results[:5]:  # Birinchi 5 ta
                try:
                    bot.forward_message(
                        chat_id=message.chat.id,
                        from_chat_id=ch_id,
                        message_id=msg_id
                    )
                    sent_count += 1
                    logger.info(f"Kino yuborildi: {title}")
                except Exception as e:
                    logger.error(f"Forward xato: {e}")
            
            summary = (
                f"✅ <b>Topildi!</b>\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"📹 Yuborildi: <b>{sent_count}</b> ta\n"
            )
            if len(results) > 5:
                summary += f"📌 Yana: <b>{len(results) - 5}</b> ta mavjud\n"
            summary += "━━━━━━━━━━━━━━━━"
            
            bot.send_message(message.chat.id, summary, parse_mode='HTML')
        else:
            bot.delete_message(message.chat.id, status_msg.message_id)
            bot.reply_to(message,
                f"❌ <b>Topilmadi!</b>\n\n"
                f"🔎 Qidirilgan: <code>{movie_name}</code>\n\n"
                f"💡 <b>Maslahat:</b>\n"
                f"  • Boshqa nomi bilan yozib ko'ring\n"
                f"  • Qismi bilan yozib ko'ring\n"
                f"  • <code>/list</code> bilan ro'yxat ko'ring",
                parse_mode='HTML'
            )
        
    except Exception as e:
        logger.error(f"Xato: {e}")
        try:
            bot.reply_to(message,
                "❌ <b>Xato yuz berdi!</b>\n"
                "⏳ Iltimos biroz kuting va qayta urinib ko'ring.",
                parse_mode='HTML'
            )
        except:
            pass


@bot.callback_query_handler(func=lambda call: call.data.startswith('search_movie_'))
def search_movie_callback(call):
    """Search tugmasiga bosilganda kino yuborish"""
    try:
        # Callback_data dan kino ID'sini olish
        movie_id = int(call.data.split('_')[2])
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT message_id, channel_id, title FROM movies WHERE id = ?", (movie_id,))
        result = c.fetchone()
        conn.close()
        
        if not result:
            bot.answer_callback_query(call.id, "❌ Kino topilmadi!", show_alert=True)
            return
        
        msg_id, ch_id, title = result
        
        # Kino yuborish
        try:
            bot.forward_message(
                chat_id=call.from_user.id,
                from_chat_id=ch_id,
                message_id=msg_id
            )
            bot.answer_callback_query(call.id, f"✅ '{title}' yuborildi!", show_alert=False)
            logger.info(f"Kino yuborildi (qidiruvdan): {title}")
        except Exception as e:
            logger.error(f"Yuborish xato: {e}")
            bot.answer_callback_query(call.id, f"❌ Yuborishda xato!", show_alert=True)
    
    except Exception as e:
        logger.error(f"Search callback xato: {e}")
        bot.answer_callback_query(call.id, f"❌ Xato!", show_alert=True)


# ============ WEBHOOK (Render.com uchun) ============

@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram webhook endpoint"""
    try:
        json_data = request.get_json()
        if json_data:
            update = telebot.types.Update.de_json(json_data)
            if update:
                bot.process_new_updates([update])
    except Exception as e:
        logger.error(f"Webhook xato: {e}")
    return "ok", 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return {"status": "ok"}, 200


def set_webhook():
    """Webhook'ni Telegram'da ro'yxatdan o'tkazish"""
    try:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook o'rnatildi: {webhook_url}")
    except Exception as e:
        logger.error(f"Webhook o'rnatish xato: {e}")


if __name__ == '__main__':
    logger.info("🤖 Bot ishga tushdi...")
    
    # Webhook'ni o'rnatish (Render uchun)
    if WEBHOOK_URL and "onrender.com" in WEBHOOK_URL:
        set_webhook()
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
    else:
        # Lokal ishlatish uchun polling
        logger.info("⏳ Polling rejimida...")
        bot.infinity_polling()
