"""
Biznes Miyasi Bot — Konfiguratsiya
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "")  # Mini App URL (GitHub Pages / Vercel)

# AI API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "biznes_miyasi.db")

# AI Model routing (texnik arxitekturaga mos)
AI_CONFIG = {
    "simple_model": "gemini-1.5-flash",     # 85% so'rovlar
    "complex_model": "gpt-4o",              # 15% so'rovlar
    "complexity_threshold": 0.6,             # Murakkablik chegarasi
    "max_tokens": 1500,
    "temperature": 0.7,
}

# Gamifikatsiya
LEVELS = [
    {"id": 0, "name": "Boshlang'ich", "icon": "⭐", "min": 0, "max": 500, "color": "#FFB300"},
    {"id": 1, "name": "Tadbirkor", "icon": "🌱", "min": 500, "max": 1500, "color": "#00E676"},
    {"id": 2, "name": "Biznesmen", "icon": "💼", "min": 1500, "max": 3000, "color": "#2563FF"},
    {"id": 3, "name": "Moliyachi", "icon": "📊", "min": 3000, "max": 6000, "color": "#A855F7"},
    {"id": 4, "name": "Ekspert", "icon": "🔥", "min": 6000, "max": 12000, "color": "#FF6B35"},
    {"id": 5, "name": "Legend", "icon": "👑", "min": 12000, "max": 99999, "color": "#00E5CC"},
]

ACHIEVEMENTS = [
    {"id": "a1", "name": "Birinchi Qadam", "icon": "🚀", "desc": "Birinchi tahlil", "pts": 100, "check": "analysis_count >= 1"},
    {"id": "a2", "name": "Izchil", "icon": "📊", "desc": "5 ta tahlil", "pts": 200, "check": "analysis_count >= 5"},
    {"id": "a3", "name": "Tajribali", "icon": "💪", "desc": "10 ta tahlil", "pts": 300, "check": "analysis_count >= 10"},
    {"id": "a4", "name": "Xavfsiz", "icon": "🛡️", "desc": "Risk < 20", "pts": 150, "check": "last_risk < 20"},
    {"id": "a5", "name": "Muntazam", "icon": "🔥", "desc": "3 kun ketma-ket", "pts": 200, "check": "streak >= 3"},
    {"id": "a6", "name": "Mehnatkash", "icon": "✅", "desc": "5 vazifa bajarildi", "pts": 150, "check": "tasks_done >= 5"},
    {"id": "a7", "name": "Qiziquvchan", "icon": "💬", "desc": "10 ta chat", "pts": 100, "check": "chat_count >= 10"},
    {"id": "a8", "name": "Foydali", "icon": "💰", "desc": "Foyda > 0", "pts": 250, "check": "has_profit"},
    {"id": "a9", "name": "LEGEND", "icon": "👑", "desc": "12000+ ball", "pts": 500, "check": "points >= 12000"},
]

DAILY_TASKS = [
    {"id": "t1", "text": "Bugungi daromadni kiriting", "pts": 30, "icon": "💰", "cat": "Moliya"},
    {"id": "t2", "text": "Xarajatlarni tekshiring", "pts": 20, "icon": "✂️", "cat": "Moliya"},
    {"id": "t3", "text": "AI Tahlil bajaring", "pts": 50, "icon": "🧠", "cat": "Tahlil"},
    {"id": "t4", "text": "Chat orqali savol bering", "pts": 15, "icon": "💬", "cat": "Chat"},
    {"id": "t5", "text": "Prognozni ko'ring", "pts": 10, "icon": "📈", "cat": "Prognoz"},
]

WEEKLY_TASKS = [
    {"id": "w1", "text": "Haftalik moliyaviy hisobot tayyorlang", "pts": 100, "icon": "📊", "cat": "Haftalik"},
    {"id": "w2", "text": "Raqobatchilar narxini solishtiring", "pts": 80, "icon": "🔍", "cat": "Haftalik"},
    {"id": "w3", "text": "3 ta yangi mijoz qo'shing", "pts": 120, "icon": "👥", "cat": "Haftalik"},
]

# Bank SMS formatlar (12+ bank)
SMS_PATTERNS = {
    "uzcard": {
        "income": [
            r"(?:Popolnenie|Kirim|O'tkazma)\s*(?:na|ga)?\s*.*?(\d[\d\s,.]+)\s*(?:so'm|UZS|сум)",
            r"Balans.*?(\d[\d\s,.]+)\s*(?:so'm|UZS)",
        ],
        "expense": [
            r"(?:Spisanie|Chiqim|To'lov|Xarid)\s*.*?(\d[\d\s,.]+)\s*(?:so'm|UZS|сум)",
            r"(?:Покупка|Оплата)\s*.*?(\d[\d\s,.]+)\s*(?:so'm|UZS|сум)",
        ],
    },
    "humo": {
        "income": [r"(?:Kirim|Popolnenie)\s*.*?(\d[\d\s,.]+)\s*(?:so'm|UZS)"],
        "expense": [r"(?:Chiqim|Xarid|Spisanie)\s*.*?(\d[\d\s,.]+)\s*(?:so'm|UZS)"],
    },
    "kapitalbank": {
        "income": [r"(?:Kirim|Tushum)\s*.*?(\d[\d\s,.]+)\s*(?:so'm|UZS)"],
        "expense": [r"(?:Chiqim|To'lov)\s*.*?(\d[\d\s,.]+)\s*(?:so'm|UZS)"],
    },
    "ipoteka_bank": {
        "income": [r"(?:Hisobga|Kirim)\s*.*?(\d[\d\s,.]+)"],
        "expense": [r"(?:Hisobdan|Chiqim)\s*.*?(\d[\d\s,.]+)"],
    },
    "asakabank": {
        "income": [r"(?:Kirim|Credit)\s*.*?(\d[\d\s,.]+)"],
        "expense": [r"(?:Chiqim|Debet|Debit)\s*.*?(\d[\d\s,.]+)"],
    },
    "universal": {
        "income": [
            r"[+]?\s*(\d[\d\s,.]{2,})\s*(?:so'm|UZS|сум|sum)",
            r"(?:[Kk]irim|[Pp]opolnenie|[Tt]ushum|[Зз]ачисление)\s*.*?(\d[\d\s,.]+)",
        ],
        "expense": [
            r"[-]?\s*(\d[\d\s,.]{2,})\s*(?:so'm|UZS|сум|sum)",
            r"(?:[Cc]hiqim|[Ss]pisanie|[Xx]arid|[Tt]o'lov|[Сс]писание|[Пп]окупка)\s*.*?(\d[\d\s,.]+)",
        ],
    },
}

# Soha bo'yicha tavsiyalar
SECTOR_ADVICE = {
    "kafe": {
        "name": "Kafe/Restoran",
        "icon": "☕",
        "tips": [
            "Ovqat isrofini kuzating — qolgan mahsulotlar hisobi yuring",
            "Menyu narxlarini optimallang — eng ko'p sotilgan 5 ta taomga e'tibor bering",
            "Hafta oxiri maxsus menyu yarating — daromadni 20-30% oshiradi",
        ],
    },
    "dokon": {
        "name": "Do'kon/Savdo",
        "icon": "🏪",
        "tips": [
            "O'lik tovarni aniqlang — 60+ kun sotilmaganlarni chegirmaga chiqaring",
            "Stok aylanishini oshiring — haftalik inventarizatsiya olib boring",
            "Chegirma vaqtlari: oyning 1-5 va 15-20 kunlari eng samarali",
        ],
    },
    "dorixona": {
        "name": "Dorixona",
        "icon": "💊",
        "tips": [
            "Muddati yaqin dorilarni kuzating — alert tizimi o'rnating",
            "Hamkor klinikalar bilan shartnoma tuzing",
            "Vitamins va BFQ (biologik faol qo'shimchalar) assortimentini kengaytiring",
        ],
    },
    "auto": {
        "name": "Avto xizmat",
        "icon": "🔧",
        "tips": [
            "Top-5 ehtiyot qismlarni stokda tuting",
            "Kafolat xizmati orqali mijozlarni saqlab qoling",
            "Online bron tizimi yarating — Telegram bot orqali",
        ],
    },
    "onlayn": {
        "name": "Onlayn do'kon",
        "icon": "🛒",
        "tips": [
            "Reklama konversiyasini kuzating — ROAS 3x dan past bo'lsa kanal o'zgartiring",
            "Qaytish (return) foizini 5% dan past tuting",
            "Instagram + Telegram komboda ishlang — cross-selling",
        ],
    },
    "fermer": {
        "name": "Fermerlik",
        "icon": "🌾",
        "tips": [
            "Suv va mineral o'g'it xarajatlarini optimallashtiring",
            "Hosil saqlash muddatini uzaytiring — sovutish tizimi",
            "To'g'ridan-to'g'ri restoran va do'konlarga soting — 15-25% yuqori narx",
        ],
    },
    "boshqa": {
        "name": "Boshqa",
        "icon": "📦",
        "tips": [
            "Asosiy xarajatlarni haftalik kuzating",
            "Top-3 xarajat moddani kamaytiring",
            "Daromad diversifikatsiyasi — kamida 2 manba yarating",
        ],
    },
}

# Premium tariflar
PREMIUM_TIERS = {
    "bronze": {"name": "Bronze", "icon": "🥉", "price": "149,000 so'm/oy", "price_num": 149000},
    "silver": {"name": "Silver", "icon": "🥈", "price": "390,000 so'm/oy", "price_num": 390000},
    "gold": {"name": "Gold", "icon": "🥇", "price": "1,450,000 so'm/oy", "price_num": 1450000},
}

# Admin
ADMIN_TELEGRAM = "@Makhmudov_asilbek_19"
ADMIN_PHONE = "+998936437702"
