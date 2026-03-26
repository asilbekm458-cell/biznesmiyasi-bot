# 🧠 BIZNES MIYASI BOT

**O'zbekiston KOBlar uchun AI moliyaviy tahlil platformasi**

Telegram Bot + Mini App | Gibrid AI: Gemini Flash (85%) + GPT-4o (15%)

---

## 📋 Loyiha tuzilishi

```
biznes_miyasi_bot/
├── bot.py                    # 🤖 Asosiy bot (barcha handlerlar)
├── config.py                 # ⚙️ Konfiguratsiya
├── database.py               # 💾 SQLite database
├── requirements.txt          # 📦 Dependencies
├── .env.example              # 🔑 Environment o'zgaruvchilari namunasi
├── services/
│   ├── __init__.py
│   ├── analysis.py           # 📊 Moliyaviy tahlil engine
│   ├── ai_service.py         # 🧠 AI (Gemini + GPT-4o)
│   ├── sms_parser.py         # 📱 Bank SMS parser (12+ bank)
│   ├── csv_import.py         # 📁 CSV/Excel/1C import
│   ├── pdf_report.py         # 📄 PDF hisobot generator
│   └── gamification.py       # 🏆 Ballar, seviyalar, yutuqlar
└── mini_app/
    └── index.html            # 🌐 Telegram Mini App
```

---

## 🚀 O'RNATISH (3 QADAM)

### 1-qadam: Bot yaratish

1. Telegram'da [@BotFather](https://t.me/BotFather) ga `/newbot` yuboring
2. Bot nomini kiriting: `Biznes Miyasi`
3. Username: `biznesmiyasi_bot` (yoki boshqa)
4. Olingan **TOKEN**ni saqlang

### 2-qadam: API kalitlarini olish

**Gemini (BEPUL — asosiy AI):**
1. https://aistudio.google.com ga kiring
2. "Get API Key" → kalit yarating
3. Bu kalit **BEPUL** va 85% so'rovlar uchun ishlatiladi

**OpenAI (ixtiyoriy — faqat murakkab so'rovlar):**
1. https://platform.openai.com ga kiring
2. API key yarating
3. Faqat murakkab so'rovlar uchun (15%)

### 3-qadam: Deploy qilish

```bash
# Kodni yuklang
git clone <your-repo-url>
cd biznes_miyasi_bot

# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies o'rnatish
pip install -r requirements.txt

# .env faylini yarating
cp .env.example .env
# .env ni tahrirlang va tokenlarni qo'ying

# Botni ishga tushiring
python bot.py
```

---

## 🌐 MINI APP DEPLOY (GitHub Pages)

1. `mini_app/index.html` ni GitHub repository ga qo'ying
2. Settings → Pages → Deploy from branch: `main`
3. URL hosil bo'ladi: `https://username.github.io/repo-name/`
4. Bu URL ni `.env` dagi `WEBAPP_URL` ga qo'ying
5. BotFather da `/setmenubutton` → Web App URL ni o'rnating

---

## ☁️ SERVER DEPLOY

### Railway.app (eng oson)
1. https://railway.app → New Project → GitHub repo
2. Environment Variables ga `.env` qiymatlarini kiriting
3. Deploy tugmasini bosing — tayyor!

### VPS (Ubuntu)
```bash
# Screen orqali background da ishlash
screen -S biznes_miyasi
python bot.py
# Ctrl+A, D — screen dan chiqish
```

### Docker
```bash
docker build -t biznes-miyasi .
docker run -d --env-file .env biznes-miyasi
```

---

## 📊 BOT FUNKSIYALARI

| Funksiya | Buyruq | Ball |
|----------|--------|------|
| Moliyaviy tahlil | `/tahlil` | +50 ⭐ |
| AI Chat | `/chat` | +15 ⭐ |
| Bank SMS parse | `📱 SMS Parse` | +5/SMS ⭐ |
| CSV/Excel import | Fayl yuborish | +3/tx ⭐ |
| PDF hisobot | `/hisobot` | +15 ⭐ |
| Kirim/Chiqim | `💰 Kirim/Chiqim` | +10 ⭐ |
| Reyting | `/reyting` | — |
| Profil | `/profil` | — |

---

## 🏆 GAMIFIKATSIYA TIZIMI

### Seviyalar
| Seviya | Ball | Icon |
|--------|------|------|
| Boshlang'ich | 0-500 | ⭐ |
| Tadbirkor | 500-1500 | 🌱 |
| Biznesmen | 1500-3000 | 💼 |
| Moliyachi | 3000-6000 | 📊 |
| Ekspert | 6000-12000 | 🔥 |
| Legend | 12000+ | 👑 |

### Yutuqlar
🚀 Birinchi Qadam · 📊 Izchil · 💪 Tajribali · 🛡️ Xavfsiz · 🔥 Muntazam · ✅ Mehnatkash · 💬 Qiziquvchan · 💰 Foydali · 👑 LEGEND

---

## 📱 QO'LLAB-QUVVATLANGAN BANKLAR (SMS Parse)

Uzcard, Humo, Kapitalbank, Ipoteka-bank, Asaka bank, Aloqa bank, Hamkor bank, Xalq banki, Davr bank, TrustBank, Orient Finance, InfinBank + universal format

---

## 🔒 XAVFSIZLIK

- Ma'lumotlar SQLite da lokal saqlanadi (production: PostgreSQL)
- Bot tokeni `.env` da — kodda EMAS
- Shaxsiy ma'lumotlar faqat tahlil uchun ishlatiladi
- Keyingi versiya: AES-256 shifrlash, JWT autentifikatsiya

---

## 📞 Aloqa

**Asilbek Maxmudov**
- Telegram: @Makhmudov_asilbek_19
- Telefon: +998 93 643 77 02

---

*Biznes Miyasi MCHJ | ATMU Qarshi filiali | 2026*
