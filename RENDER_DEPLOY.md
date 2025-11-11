# 🚀 Render.com uchun Deploy Yo'riqnomasi

## 1️⃣ Render.com'da PostgreSQL Database Yaratish

1. **Render.com'ga kirish**: https://render.com
2. **"New" → "PostgreSQL"** tugmasini bosing
3. **Database nomini** soting (masalan `movies_db`)
4. **Region** tanlang
5. **"Create Database"** bosing
6. Database **Connection String** nusxalang (Internal va External):
   - Internal string → `DATABASE_URL` uchun

```
postgresql://username:password@dpg-xxxxx.render.internal/movies_db
```

---

## 2️⃣ GitHub'ga Upload qilish

```bash
# 1. GitHub'da yangi repo yaratish
# https://github.com/new

# 2. Folder'ni initialize qilish
cd "c:\Users\PC\Desktop\Новая папка"
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/telegram-bot.git
git push -u origin main
```

---

## 3️⃣ Render.com'da Bot Deploy qilish

1. **Render.com'da** → **"New" → "Web Service"**
2. **GitHub repo** tanlang
3. **Settings**:
   - **Name**: `telegram-movie-bot` (yoki boshqa nom)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn bot:app`
   - **Region**: Sizga yaqin (masalan `Singapore`)

4. **Environment Variables** qo'shish:
   ```
   TELEGRAM_BOT_TOKEN = 8500094262:AAEolHclNFc4gSzdwsjM5QbTtd6fMQ9qjWE
   ADMIN_ID = 8071103470
   CHANNEL_ID = -1001776843862
   CHANNEL_USERNAME = Hentailar_uz
   DATABASE_URL = postgresql://username:password@dpg-xxxxx.render.internal/movies_db
   WEBHOOK_URL = https://your-bot-name.onrender.com
   FLASK_HOST = 0.0.0.0
   FLASK_PORT = 8000
   ```

5. **"Create Web Service"** bosing ⏳

---

## 4️⃣ Deploy Tugatilganini Tekshirish

- Render'dan **URL'ni** olish (masalan: `https://telegram-movie-bot.onrender.com`)
- URL + `/health` tekshirish:
  ```
  https://telegram-movie-bot.onrender.com/health
  ```
  Response: `{"status": "ok"}`

---

## 5️⃣ Bot Ishga Tushganini Tekshirish

Telegram'da botni test qilish:
- `/start` - Ko'rish kerak
- `Flesh 76` - Qidirish
- `/list` - Kinolar ro'yxati

---

## 📝 Muhim Eslatmalar

✅ **Polling → Webhook o'zgarishi**:
   - Bot hozir polling bilan ishlaydi (lokal)
   - Render'da webhook bilan ishlab ketadi
   - Webhook URL automatic ravishda `/webhook` endpoint'iga chaqiradi

✅ **SQLite → PostgreSQL o'zgarishi**:
   - Lokal database emas
   - Render'dagi PostgreSQL ishlatiladi
   - Auto-migration qilmaydi - qo'l bilan yaratish kerak:

```sql
CREATE TABLE IF NOT EXISTS movies (
    id SERIAL PRIMARY KEY,
    title TEXT UNIQUE,
    message_id INTEGER,
    channel_id INTEGER
);
```

✅ **Free Tier Cheklovlari**:
   - Web service: birdan-bir ohirgi 15 daqiqa faol bo'lsa, sleep'ga o'tadi
   - PostgreSQL: 90 kun ishlatilmasa database o'chiriladi
   - Cold start: Birinchi so'rovda 30 sekundga qadar kuta olish kerak

---

## 🔧 Environment Variables

| Nom | Qiymat |
|-----|--------|
| `TELEGRAM_BOT_TOKEN` | Sizning bot token'i |
| `ADMIN_ID` | Admin Telegram ID |
| `CHANNEL_ID` | Kanal ID (-1001776843862) |
| `CHANNEL_USERNAME` | Kanal nomi (@Hentailar_uz) |
| `DATABASE_URL` | PostgreSQL connection string |
| `WEBHOOK_URL` | Render'dagi app URL |
| `FLASK_HOST` | 0.0.0.0 (o'zgartirmang) |
| `FLASK_PORT` | 8000 (o'zgartirmang) |

---

## 📞 Muammo uchun

- Render logs: **"Logs"** tab'da tekshiring
- Database check: Render PostgreSQL dashboard
- Webhook check: Bot logs'da `"✅ Webhook o'rnatildi"` ko'rish kerak

---

**Qo'shimcha:** Agar `get_message()` xatosi chiqsa, `/index` komandani foydalanmang.
O'z o'rniga **admin sifatida media yuborish** bilan auto-indexlang.
