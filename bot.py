import os
from flask import Flask, request
from dotenv import load_dotenv
import telebot

# .env fayldan o‘qish
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# /start komandasi
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 Salom! Bot ishlayapti ✅")

# Webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    json_data = request.get_json()
    if json_data:
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
    return "OK", 200

# Webhookni o‘rnatish
def set_webhook():
    url = f"{WEBHOOK_URL}/webhook"
    bot.remove_webhook()
    bot.set_webhook(url=url)

# Flask serverni ishga tushirish
if __name__ == '__main__':
    set_webhook()
    app.run(host="0.0.0.0", port=8000)
