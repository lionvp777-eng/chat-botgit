# 🎬 Telegram Kino Qidirish Boti

Bu bot Telegram da foydalanuvchilarga kino qidirish xizmatini taqdim etadi. Foydalanuvchi kino nomini yozsa, bot uni qidirib topib, kanalga yuboradi.

## ⚙️ Sozlamalar

### 1️⃣ Bot tokenini oling
- [@BotFather](https://t.me/botfather) ga murojaat qiling
- `/newbot` komandasi bilan yangi bot yarating
- Olingan tokenni `bot.py` faylidagi `TELEGRAM_BOT_TOKEN` o'rniga qo'ying

### 2️⃣ TMDB API kalitini oling
- [TheMovieDB](https://www.themoviedb.org/settings/api) saytiga o'ting
- Akkaunt yarating (agar bo'lmasa)
- API kalitni olish uchun "Create" tugmasini bosing
- Kalitni `bot.py` faylidagi `TMDB_API_KEY` o'rniga qo'ying

### 3️⃣ Kanalning ID'sini topish
```
- Kanalga @username bilan bot admin sifatida qo'shing
- Bot ga /start yozing va bir kino nomini yozing
- Botning log'ida channel ID ni ko'rasiz
- Uni CHANNEL_ID o'rniga qo'ying
```

## 🚀 Ishga tushirish

### Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### Botni ishga tushirish
```bash
python bot.py
```

## 📋 Foydalanish

1. Botga xabar yuboring: `/start`
2. Kino nomi yozing, masalan: "Interstellar"
3. Bot kinoni TMDB dan qidirib topadi
4. Kino ma'lumotlari kanalga yuboriladi

## 🔧 Bot Features

✅ Kino nomini qidirish (TMDB API)
✅ Kino ma'lumotlarini (yil, reyting, tasnif)
✅ Kinoni kanalga avtomatik yuborish
✅ Xato boshqarish

## ⚠️ Eslatmalar

- Bot shunchaki qidirish xizmati taqdim etadi
- Haqiqiy kino video fayl jo'natmaydi
- Kino ma'lumotlari TMDB dan olinadi

---
📧 Agar savol bo'lsa, yordam beraman!
