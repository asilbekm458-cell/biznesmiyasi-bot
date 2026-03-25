"""
╔══════════════════════════════════════════════════════╗
║  BIZNES MIYASI BOT — Telegram Bot + Mini App         ║
║  O'zbekiston KOBlar uchun AI moliyaviy tahlil         ║
║  Gibrid: Gemini Flash (85%) + GPT-4o (15%)           ║
║  Asoschisi: Asilbek Maxmudov | 2026                  ║
╚══════════════════════════════════════════════════════╝
"""
import asyncio
import logging
import os
import io
from datetime import datetime, date

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
    WebAppInfo, ReplyKeyboardMarkup, KeyboardButton,
    BufferedInputFile, ContentType,
)
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode

from config import (
    BOT_TOKEN, WEBAPP_URL, ADMIN_TELEGRAM, ADMIN_PHONE,
    DAILY_TASKS, WEEKLY_TASKS, PREMIUM_TIERS, LEVELS,
)
import database as db
from services.analysis import (
    full_analysis, generate_analysis_text, generate_quick_summary,
    fmt_money, fmt_money_full,
)
from services.sms_parser import parse_sms, parse_sms_bulk
from services.ai_service import ask_ai
from services.gamification import (
    get_level, get_level_progress, check_achievements,
    format_profile_card, format_leaderboard, format_tasks,
)
from services.pdf_report import generate_pdf_report, generate_transactions_report
from services.csv_import import parse_csv_data, parse_excel_file

# ═══════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BiznesMiyasi")

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
router = Router()
dp.include_router(router)


# ═══════════════════════════════════════════════
# FSM STATES
# ═══════════════════════════════════════════════
class AnalysisForm(StatesGroup):
    business_name = State()
    sector = State()
    income = State()
    expense = State()
    employees = State()
    period = State()
    problem = State()


class ManualEntry(StatesGroup):
    type = State()
    amount = State()
    category = State()
    description = State()


class SMSParse(StatesGroup):
    waiting_sms = State()


class AIChat(StatesGroup):
    chatting = State()


# ═══════════════════════════════════════════════
# KEYBOARDS
# ═══════════════════════════════════════════════
def main_keyboard() -> ReplyKeyboardMarkup:
    """Asosiy reply keyboard"""
    buttons = [
        [KeyboardButton(text="📊 Tahlil"), KeyboardButton(text="🧠 AI Chat")],
        [KeyboardButton(text="💰 Kirim/Chiqim"), KeyboardButton(text="📱 SMS Parse")],
        [KeyboardButton(text="🏆 Reyting"), KeyboardButton(text="✅ Vazifalar")],
        [KeyboardButton(text="👤 Profil"), KeyboardButton(text="📄 PDF Hisobot")],
    ]
    # Mini App tugmasi (agar URL mavjud bo'lsa)
    if WEBAPP_URL:
        buttons.append([KeyboardButton(text="🚀 Mini App", web_app=WebAppInfo(url=WEBAPP_URL))])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def main_inline_keyboard() -> InlineKeyboardMarkup:
    """Asosiy inline keyboard"""
    buttons = [
        [
            InlineKeyboardButton(text="📊 Yangi Tahlil", callback_data="new_analysis"),
            InlineKeyboardButton(text="🧠 AI Chat", callback_data="ai_chat"),
        ],
        [
            InlineKeyboardButton(text="💰 Kirim qo'shish", callback_data="add_income"),
            InlineKeyboardButton(text="✂️ Chiqim qo'shish", callback_data="add_expense"),
        ],
        [
            InlineKeyboardButton(text="📱 SMS Parse", callback_data="sms_parse"),
            InlineKeyboardButton(text="📁 CSV/Excel", callback_data="csv_import"),
        ],
        [
            InlineKeyboardButton(text="🏆 Reyting", callback_data="leaderboard"),
            InlineKeyboardButton(text="✅ Vazifalar", callback_data="tasks"),
        ],
        [
            InlineKeyboardButton(text="📄 PDF Hisobot", callback_data="pdf_report"),
            InlineKeyboardButton(text="👤 Profil", callback_data="profile"),
        ],
    ]
    if WEBAPP_URL:
        buttons.append([InlineKeyboardButton(text="🚀 Mini App ochish", web_app=WebAppInfo(url=WEBAPP_URL))])
    buttons.append([InlineKeyboardButton(text="👑 Premium", callback_data="premium")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def sector_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="☕ Kafe/Restoran", callback_data="sec_kafe")],
        [InlineKeyboardButton(text="🏪 Do'kon/Savdo", callback_data="sec_dokon")],
        [InlineKeyboardButton(text="💊 Dorixona", callback_data="sec_dorixona")],
        [InlineKeyboardButton(text="🔧 Avto xizmat", callback_data="sec_auto")],
        [InlineKeyboardButton(text="🛒 Onlayn do'kon", callback_data="sec_onlayn")],
        [InlineKeyboardButton(text="🌾 Fermerlik", callback_data="sec_fermer")],
        [InlineKeyboardButton(text="📦 Boshqa", callback_data="sec_boshqa")],
    ])


def period_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Yangi (1 yildan kam)", callback_data="per_yangi")],
        [InlineKeyboardButton(text="📈 O'rta (1-3 yil)", callback_data="per_orta")],
        [InlineKeyboardButton(text="🏢 Tajribali (3+ yil)", callback_data="per_tajr")],
    ])


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu")],
    ])


def analysis_actions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🧠 AI Savol", callback_data="ai_chat"),
            InlineKeyboardButton(text="📄 PDF Yuklash", callback_data="pdf_report"),
        ],
        [
            InlineKeyboardButton(text="🔄 Yangi Tahlil", callback_data="new_analysis"),
            InlineKeyboardButton(text="🏠 Menyu", callback_data="main_menu"),
        ],
    ])


def category_keyboard(tx_type: str) -> InlineKeyboardMarkup:
    if tx_type == "income":
        cats = [
            ("💰 Sotuv", "cat_sotuv"), ("📦 Xizmat", "cat_xizmat"),
            ("💳 O'tkazma", "cat_otkazma"), ("📊 Boshqa kirim", "cat_boshqa"),
        ]
    else:
        cats = [
            ("🍞 Oziq-ovqat", "cat_oziq-ovqat"), ("🚗 Transport", "cat_transport"),
            ("🏠 Ijara", "cat_ijara"), ("👥 Maosh", "cat_maosh"),
            ("📦 Tovar", "cat_tovar"), ("📢 Reklama", "cat_reklama"),
            ("🔧 Xizmat", "cat_xizmat"), ("📊 Boshqa", "cat_boshqa"),
        ]
    buttons = [[InlineKeyboardButton(text=name, callback_data=cb)] for name, cb in cats]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ═══════════════════════════════════════════════
# /start COMMAND
# ═══════════════════════════════════════════════
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    full_name = message.from_user.full_name or "Tadbirkor"
    username = message.from_user.username or ""

    user = await db.get_user(user_id)
    if not user:
        user = await db.create_user(user_id, full_name, username)
        # Welcome message
        await message.answer(
            f"""
🧠 <b>BIZNES MIYASI</b>ga xush kelibsiz!
{'━' * 28}

Salom, <b>{full_name}</b>! 👋

Men sizning shaxsiy <b>AI moliyaviy maslahatchi</b>ngizman.

🔹 <b>Nima qila olaman:</b>
├ 📊 Moliyaviy tahlil (risk skori, prognoz)
├ 🧠 AI chat — istalgan savol bering
├ 📱 Bank SMS avtomatik parse
├ 📁 1C/CSV/Excel import
├ 📄 PDF hisobot generatsiya
├ 🏆 Gamifikatsiya (ballar, seviyalar)
└ 👑 Premium tariflar

🚀 <b>Boshlash uchun /tahlil yoki tugmalardan foydalaning!</b>
""",
            reply_markup=main_keyboard(),
        )
        await message.answer("⬇️ Quyidagi menyu orqali boshlang:", reply_markup=main_inline_keyboard())
        return

    # Qaytgan foydalanuvchi
    lvl = get_level(user["points"])
    await message.answer(
        f"👋 Qaytganingizdan xursandman, <b>{user['full_name']}</b>!\n\n"
        f"{lvl['icon']} Seviya: <b>{lvl['name']}</b> · ⭐ {user['points']} ball\n"
        f"📊 Tahlillar: {user['analysis_count']}\n\n"
        f"Nima qilamiz bugun?",
        reply_markup=main_keyboard(),
    )
    await message.answer("⬇️ Tanlang:", reply_markup=main_inline_keyboard())


# ═══════════════════════════════════════════════
# ANALYSIS FLOW
# ═══════════════════════════════════════════════
@router.message(Command("tahlil"))
@router.message(F.text == "📊 Tahlil")
@router.callback_query(F.data == "new_analysis")
async def start_analysis(event, state: FSMContext):
    await state.clear()
    msg = event.message if isinstance(event, CallbackQuery) else event
    if isinstance(event, CallbackQuery):
        await event.answer()

    await state.set_state(AnalysisForm.business_name)
    await msg.answer(
        "📊 <b>MOLIYAVIY TAHLIL</b>\n"
        "━" * 28 + "\n\n"
        "1️⃣ Biznesingiz nomini kiriting:\n\n"
        "<i>Masalan: Kafe Bahor, AutoFix, PharmPlus</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")]
        ]),
    )


@router.message(AnalysisForm.business_name)
async def analysis_name(message: Message, state: FSMContext):
    await state.update_data(business_name=message.text.strip())
    await state.set_state(AnalysisForm.sector)
    await message.answer("2️⃣ Soha tanlang:", reply_markup=sector_keyboard())


@router.callback_query(F.data.startswith("sec_"), AnalysisForm.sector)
async def analysis_sector(callback: CallbackQuery, state: FSMContext):
    sector = callback.data.replace("sec_", "")
    await state.update_data(sector=sector)
    await state.set_state(AnalysisForm.income)
    await callback.answer()
    await callback.message.answer(
        "3️⃣ <b>Oylik daromadni</b> kiriting (so'mda):\n\n"
        "<i>Masalan: 45000000 yoki 45M</i>"
    )


@router.message(AnalysisForm.income)
async def analysis_income(message: Message, state: FSMContext):
    amount = parse_money_input(message.text)
    if amount <= 0:
        await message.answer("❌ Noto'g'ri format! Raqam kiriting:\n<i>Masalan: 45000000 yoki 45M</i>")
        return
    await state.update_data(income=amount)
    await state.set_state(AnalysisForm.expense)
    await message.answer(
        f"✅ Daromad: <code>{fmt_money_full(amount)}</code>\n\n"
        "4️⃣ <b>Oylik xarajatni</b> kiriting (so'mda):"
    )


@router.message(AnalysisForm.expense)
async def analysis_expense(message: Message, state: FSMContext):
    amount = parse_money_input(message.text)
    if amount <= 0:
        await message.answer("❌ Noto'g'ri format! Raqam kiriting:")
        return
    await state.update_data(expense=amount)
    await state.set_state(AnalysisForm.employees)
    await message.answer(
        f"✅ Xarajat: <code>{fmt_money_full(amount)}</code>\n\n"
        "5️⃣ <b>Xodimlar soni</b>ni kiriting:"
    )


@router.message(AnalysisForm.employees)
async def analysis_employees(message: Message, state: FSMContext):
    try:
        emp = max(1, int(message.text.strip()))
    except ValueError:
        await message.answer("❌ Raqam kiriting (masalan: 5)")
        return
    await state.update_data(employees=emp)
    await state.set_state(AnalysisForm.period)
    await message.answer("6️⃣ Biznes yoshi:", reply_markup=period_keyboard())


@router.callback_query(F.data.startswith("per_"), AnalysisForm.period)
async def analysis_period(callback: CallbackQuery, state: FSMContext):
    period = callback.data.replace("per_", "")
    await state.update_data(period=period)
    await state.set_state(AnalysisForm.problem)
    await callback.answer()
    await callback.message.answer(
        "7️⃣ Asosiy <b>muammo</b>ni yozing (ixtiyoriy):\n\n"
        "<i>'Foydam kamaydi', 'Naqd pul yetmayapti' va h.k.\n"
        "Yoki /skip — o'tkazib yuborish</i>"
    )


@router.message(AnalysisForm.problem)
async def analysis_problem(message: Message, state: FSMContext):
    problem = "" if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(problem=problem)
    data = await state.get_data()
    await state.clear()

    user_id = message.from_user.id
    user = await db.get_user(user_id)

    # Loading animation
    loading_msg = await message.answer(
        "🧠 <b>AI tahlil qilmoqda...</b>\n\n"
        "⏳ Ma'lumotlar tekshirilmoqda...\n"
        "⏳ Risk baholanmoqda...\n"
        "⏳ Tavsiyalar tayyorlanmoqda..."
    )

    # Tahlil
    result = full_analysis(data)

    # DB ga saqlash
    save_data = {
        "business_name": data["business_name"],
        "sector": data["sector"],
        "income": data["income"],
        "expense": data["expense"],
        "employees": data["employees"],
        "period": data["period"],
        "problem": data.get("problem", ""),
        "risk_score": result["risk_score"],
        "profit_margin": result["margin"],
        "waste_estimate": result["waste_estimate"],
        "savings_potential": result["savings_potential"],
    }
    await db.save_analysis(user_id, save_data)

    # Ballar
    await db.add_points(user_id, 50, "Moliyaviy tahlil bajarildi")
    await db.complete_task(user_id, "t3", 50)

    # Loading o'chirish
    await loading_msg.delete()

    # Progressni ko'rsatish
    await message.answer(
        "✅ <b>Tahlil tayyor!</b>\n\n"
        "📊 Ma'lumotlar tekshirildi ✓\n"
        "⚡ Risk baholandi ✓\n"
        "💡 Tavsiyalar tayyorlandi ✓\n"
        "🧠 AI tahlili yakunlandi ✓\n\n"
        f"⭐ <b>+50 ball</b> topildi!"
    )

    # Natija
    analysis_text = generate_analysis_text(result)
    await message.answer(analysis_text, reply_markup=analysis_actions_keyboard())

    # Yutuqlarni tekshirish
    new_achs = await check_achievements(user_id)
    for ach in new_achs:
        await message.answer(
            f"🎉 <b>YANGI YUTUQ!</b>\n\n"
            f"{ach['icon']} <b>{ach['name']}</b>\n"
            f"{ach['desc']}\n"
            f"⭐ +{ach['pts']} ball!"
        )


# ═══════════════════════════════════════════════
# AI CHAT
# ═══════════════════════════════════════════════
@router.message(Command("chat"))
@router.message(F.text == "🧠 AI Chat")
@router.callback_query(F.data == "ai_chat")
async def start_ai_chat(event, state: FSMContext):
    msg = event.message if isinstance(event, CallbackQuery) else event
    if isinstance(event, CallbackQuery):
        await event.answer()

    user_id = msg.chat.id if isinstance(event, CallbackQuery) else event.from_user.id
    user = await db.get_user(user_id)
    analysis = await db.get_latest_analysis(user_id)

    await state.set_state(AIChat.chatting)

    intro = "🧠 <b>AI Chat rejimi</b>\n━" + "━" * 27 + "\n\n"
    if analysis:
        intro += f"📊 Oxirgi tahlil: <b>{analysis.get('business_name', '')}</b>\n"
        intro += f"⚡ Risk: {analysis.get('risk_score', '?')}/100\n\n"
    intro += (
        "Istalgan savol bering — men javob beraman!\n\n"
        "💡 <b>Masalan:</b>\n"
        "• Xarajatni qanday kamaytiraman?\n"
        "• Daromadni oshirish yo'llari\n"
        "• Biznesim risk darajasi qanday?\n\n"
        "<i>Chiqish: /stop yoki /menu</i>"
    )
    quick_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Foyda oshirish", callback_data="q_foyda"),
            InlineKeyboardButton(text="✂️ Xarajat kesish", callback_data="q_xarajat"),
        ],
        [
            InlineKeyboardButton(text="⚡ Risk tahlili", callback_data="q_risk"),
            InlineKeyboardButton(text="📈 Prognoz", callback_data="q_prognoz"),
        ],
        [InlineKeyboardButton(text="🏠 Chiqish", callback_data="main_menu")],
    ])
    await msg.answer(intro, reply_markup=quick_buttons)


@router.callback_query(F.data.startswith("q_"))
async def quick_chat_question(callback: CallbackQuery, state: FSMContext):
    questions = {
        "q_foyda": "Foydani qanday oshirsam bo'ladi?",
        "q_xarajat": "Xarajatni qanday kamaytiraman?",
        "q_risk": "Biznesim risk darajasi qanday va nima qilishim kerak?",
        "q_prognoz": "Kelasi 3 oy uchun prognoz bering",
    }
    question = questions.get(callback.data, "Yordam bering")
    await callback.answer()
    await process_ai_question(callback.message, callback.from_user.id, question, state)


@router.message(AIChat.chatting)
async def handle_ai_chat(message: Message, state: FSMContext):
    if message.text in ("/stop", "/menu"):
        await state.clear()
        await message.answer("👋 Chat tugatildi!", reply_markup=main_inline_keyboard())
        return
    await process_ai_question(message, message.from_user.id, message.text, state)


async def process_ai_question(message: Message, user_id: int, question: str, state: FSMContext):
    user = await db.get_user(user_id)
    analysis = await db.get_latest_analysis(user_id)

    # Typing animation
    typing_msg = await message.answer("🧠 <i>AI o'ylayapti...</i>")

    analysis_data = None
    if analysis:
        analysis_data = {
            "income": analysis.get("income", 0),
            "expense": analysis.get("expense", 0),
            "risk_score": analysis.get("risk_score", 0),
            "employees": analysis.get("employees", 1),
            "sector": analysis.get("sector", "boshqa"),
        }

    response = await ask_ai(question, user, analysis_data)
    await typing_msg.delete()

    # Chat count va task
    if user:
        await db.update_user(user_id, chat_count=user.get("chat_count", 0) + 1)
        await db.complete_task(user_id, "t4", 15)

    await message.answer(
        f"🧠 <b>Biznes Miyasi AI:</b>\n\n{response}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Menyu", callback_data="main_menu")],
        ]),
    )
    await check_achievements(user_id)


# ═══════════════════════════════════════════════
# MANUAL INCOME / EXPENSE ENTRY
# ═══════════════════════════════════════════════
@router.message(F.text == "💰 Kirim/Chiqim")
async def income_expense_menu(message: Message):
    await message.answer(
        "💰 <b>Kirim/Chiqim</b> qo'shish\n\nTanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Kirim", callback_data="add_income"),
                InlineKeyboardButton(text="✂️ Chiqim", callback_data="add_expense"),
            ],
            [InlineKeyboardButton(text="📋 Oxirgi tranzaksiyalar", callback_data="tx_history")],
            [InlineKeyboardButton(text="🏠 Menyu", callback_data="main_menu")],
        ]),
    )


@router.callback_query(F.data.in_({"add_income", "add_expense"}))
async def start_manual_entry(callback: CallbackQuery, state: FSMContext):
    tx_type = "income" if callback.data == "add_income" else "expense"
    label = "💰 Kirim" if tx_type == "income" else "✂️ Chiqim"
    await state.set_state(ManualEntry.amount)
    await state.update_data(type=tx_type)
    await callback.answer()
    await callback.message.answer(
        f"{label} <b>summani</b> kiriting (so'mda):\n\n"
        "<i>Masalan: 5000000 yoki 5M</i>"
    )


@router.message(ManualEntry.amount)
async def entry_amount(message: Message, state: FSMContext):
    amount = parse_money_input(message.text)
    if amount <= 0:
        await message.answer("❌ Noto'g'ri summa! Raqam kiriting:")
        return
    data = await state.get_data()
    await state.update_data(amount=amount)
    await state.set_state(ManualEntry.category)
    await message.answer(
        f"✅ Summa: <code>{fmt_money_full(amount)}</code>\n\n"
        "Kategoriya tanlang:",
        reply_markup=category_keyboard(data["type"]),
    )


@router.callback_query(F.data.startswith("cat_"), ManualEntry.category)
async def entry_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.replace("cat_", "")
    await state.update_data(category=category)
    await state.set_state(ManualEntry.description)
    await callback.answer()
    await callback.message.answer(
        "📝 Izoh qo'shing (ixtiyoriy):\n\n<i>/skip — o'tkazish</i>"
    )


@router.message(ManualEntry.description)
async def entry_description(message: Message, state: FSMContext):
    desc = "" if message.text == "/skip" else message.text.strip()
    data = await state.get_data()
    await state.clear()

    user_id = message.from_user.id
    await db.add_transaction(
        user_id, data["type"], data["amount"],
        data.get("category", "boshqa"), desc, "manual",
    )

    label = "💰 Kirim" if data["type"] == "income" else "✂️ Chiqim"
    await db.add_points(user_id, 10, f"{label} kiritildi")

    # Task completion
    if data["type"] == "income":
        await db.complete_task(user_id, "t1", 30)
    else:
        await db.complete_task(user_id, "t2", 20)

    await message.answer(
        f"✅ <b>{label} saqlandi!</b>\n\n"
        f"Summa: <code>{fmt_money_full(data['amount'])}</code>\n"
        f"Kategoriya: {data.get('category', 'boshqa')}\n"
        f"⭐ +10 ball",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Yana qo'shish", callback_data=f"add_{data['type']}"),
                InlineKeyboardButton(text="🏠 Menyu", callback_data="main_menu"),
            ],
        ]),
    )


@router.callback_query(F.data == "tx_history")
async def show_tx_history(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    summary = await db.get_financial_summary(user_id, 30)
    txs = await db.get_transactions(user_id, 30)

    text = f"📋 <b>Oxirgi 30 kun</b>\n━" + "━" * 27 + "\n\n"
    text += (
        f"💰 Kirim: <code>{fmt_money_full(summary['income'])}</code> ({summary['income_count']} ta)\n"
        f"✂️ Chiqim: <code>{fmt_money_full(summary['expense'])}</code> ({summary['expense_count']} ta)\n"
        f"📊 Foyda: <code>{fmt_money_full(summary['profit'])}</code> ({summary['margin']}%)\n\n"
    )

    if txs:
        text += "<b>Oxirgi tranzaksiyalar:</b>\n"
        for tx in txs[:10]:
            icon = "💰" if tx["type"] == "income" else "✂️"
            text += f"  {icon} {fmt_money_full(tx['amount'])} — {tx.get('category', '')} ({tx['date'][:10]})\n"

    await callback.message.answer(text, reply_markup=back_keyboard())


# ═══════════════════════════════════════════════
# SMS PARSE
# ═══════════════════════════════════════════════
@router.message(F.text == "📱 SMS Parse")
@router.callback_query(F.data == "sms_parse")
async def start_sms_parse(event, state: FSMContext):
    msg = event.message if isinstance(event, CallbackQuery) else event
    if isinstance(event, CallbackQuery):
        await event.answer()

    await state.set_state(SMSParse.waiting_sms)
    await msg.answer(
        "📱 <b>Bank SMS Parser</b>\n━" + "━" * 27 + "\n\n"
        "Bank SMS xabarlarini yuboring — avtomatik parse qilaman.\n\n"
        "✅ <b>Qo'llab-quvvatlangan banklar:</b>\n"
        "Uzcard, Humo, Kapitalbank, Ipoteka-bank,\n"
        "Asaka, Aloqa, Hamkor, Xalq bank va boshqalar\n\n"
        "📝 Bir yoki bir nechta SMS yuboring:\n"
        "<i>Har bir SMS yangi qatordan bo'lsin</i>\n\n"
        "<i>Chiqish: /stop</i>",
    )


@router.message(SMSParse.waiting_sms)
async def handle_sms(message: Message, state: FSMContext):
    if message.text in ("/stop", "/menu"):
        await state.clear()
        await message.answer("👋 SMS parse tugatildi!", reply_markup=main_inline_keyboard())
        return

    results = parse_sms_bulk(message.text)

    if not results:
        await message.answer(
            "❌ SMS formatini taniy olmadim.\n\n"
            "Masalan shu formatda yuboring:\n"
            "<code>Chiqim 150,000 so'm UZCARD Korzinka 01.03.2026</code>"
        )
        return

    user_id = message.from_user.id
    saved = 0
    total_income = 0
    total_expense = 0

    for tx in results:
        await db.add_transaction(
            user_id, tx["type"], tx["amount"],
            tx.get("category", "boshqa"),
            tx.get("description", ""),
            "sms",
        )
        saved += 1
        if tx["type"] == "income":
            total_income += tx["amount"]
        else:
            total_expense += tx["amount"]

    await db.add_points(user_id, saved * 5, f"SMS parse: {saved} ta")

    text = f"✅ <b>{saved} ta tranzaksiya saqlandi!</b>\n\n"
    if total_income:
        text += f"💰 Kirim: <code>{fmt_money_full(total_income)}</code>\n"
    if total_expense:
        text += f"✂️ Chiqim: <code>{fmt_money_full(total_expense)}</code>\n"
    text += f"\n⭐ +{saved * 5} ball\n\nYana SMS yuboring yoki /stop — chiqish"

    await message.answer(text)


# ═══════════════════════════════════════════════
# CSV / EXCEL IMPORT
# ═══════════════════════════════════════════════
@router.callback_query(F.data == "csv_import")
async def csv_import_start(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "📁 <b>CSV / Excel / 1C Import</b>\n━" + "━" * 27 + "\n\n"
        "Faylingizni yuboring:\n"
        "• .csv — CSV fayl\n"
        "• .xlsx — Excel fayl\n"
        "• .xls — Eski Excel\n\n"
        "📌 Ustunlar avtomatik aniqlanadi:\n"
        "summa, turi, sana, kategoriya, izoh\n\n"
        "🏢 <b>1C:Buxgalteriya</b> eksportlari ham qo'llab-quvvatlanadi!",
    )


@router.message(F.document)
async def handle_document(message: Message, state: FSMContext):
    doc = message.document
    filename = doc.file_name.lower() if doc.file_name else ""

    if not any(filename.endswith(ext) for ext in [".csv", ".xlsx", ".xls", ".txt"]):
        await message.answer("❌ Faqat CSV, Excel (.xlsx) yoki TXT fayllar qabul qilinadi!")
        return

    loading = await message.answer("📥 Fayl yuklanmoqda...")

    file = await bot.get_file(doc.file_id)
    file_bytes = await bot.download_file(file.file_path)
    content = file_bytes.read()

    transactions = []
    if filename.endswith(".csv") or filename.endswith(".txt"):
        transactions = parse_csv_data(content)
    elif filename.endswith((".xlsx", ".xls")):
        transactions = await parse_excel_file(content)

    await loading.delete()

    if not transactions:
        await message.answer("❌ Fayldan ma'lumot ajratib bo'lmadi. Formatni tekshiring!")
        return

    user_id = message.from_user.id
    saved = 0
    total_income = 0
    total_expense = 0

    for tx in transactions:
        await db.add_transaction(
            user_id, tx["type"], tx["amount"],
            tx.get("category", "boshqa"),
            tx.get("description", ""),
            tx.get("source", "csv_import"),
            tx.get("date"),
        )
        saved += 1
        if tx["type"] == "income":
            total_income += tx["amount"]
        else:
            total_expense += tx["amount"]

    pts = min(saved * 3, 100)
    await db.add_points(user_id, pts, f"CSV import: {saved} ta")

    await message.answer(
        f"✅ <b>{saved} ta tranzaksiya import qilindi!</b>\n\n"
        f"💰 Kirim: <code>{fmt_money_full(total_income)}</code>\n"
        f"✂️ Chiqim: <code>{fmt_money_full(total_expense)}</code>\n"
        f"📊 Foyda: <code>{fmt_money_full(total_income - total_expense)}</code>\n\n"
        f"⭐ +{pts} ball",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Tahlil qilish", callback_data="new_analysis")],
            [InlineKeyboardButton(text="🏠 Menyu", callback_data="main_menu")],
        ]),
    )


# ═══════════════════════════════════════════════
# PDF REPORT
# ═══════════════════════════════════════════════
@router.message(F.text == "📄 PDF Hisobot")
@router.callback_query(F.data == "pdf_report")
async def send_pdf_report(event, state: FSMContext = None):
    msg = event.message if isinstance(event, CallbackQuery) else event
    if isinstance(event, CallbackQuery):
        await event.answer()

    user_id = msg.chat.id if isinstance(event, CallbackQuery) else event.from_user.id
    user = await db.get_user(user_id)
    analysis = await db.get_latest_analysis(user_id)

    if not analysis:
        await msg.answer(
            "❌ Hali tahlil qilinmagan! Avval /tahlil bajaring.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📊 Tahlil boshlash", callback_data="new_analysis")],
            ]),
        )
        return

    loading = await msg.answer("📄 PDF hisobot tayyorlanmoqda...")
    pdf_bytes = await generate_pdf_report(analysis, user)
    await loading.delete()

    filename = f"BiznesMiyasi_{analysis.get('business_name', 'report')}_{datetime.now().strftime('%Y%m%d')}.pdf"
    doc = BufferedInputFile(pdf_bytes, filename=filename)

    await bot.send_document(
        user_id, doc,
        caption=f"📄 <b>{analysis.get('business_name', '')} — Moliyaviy Hisobot</b>\n"
                f"Risk: {analysis.get('risk_score', '?')}/100 | "
                f"Sana: {datetime.now().strftime('%d.%m.%Y')}",
    )
    await db.add_points(user_id, 15, "PDF hisobot yuklandi")
    await db.complete_task(user_id, "t5", 10)


# ═══════════════════════════════════════════════
# LEADERBOARD / RATING
# ═══════════════════════════════════════════════
@router.message(F.text == "🏆 Reyting")
@router.callback_query(F.data == "leaderboard")
async def show_leaderboard(event, state: FSMContext = None):
    msg = event.message if isinstance(event, CallbackQuery) else event
    if isinstance(event, CallbackQuery):
        await event.answer()

    user_id = msg.chat.id if isinstance(event, CallbackQuery) else event.from_user.id
    leaders = await db.get_leaderboard(20)
    text = format_leaderboard(leaders, user_id)
    await msg.answer(text, reply_markup=back_keyboard())


# ═══════════════════════════════════════════════
# TASKS
# ═══════════════════════════════════════════════
@router.message(F.text == "✅ Vazifalar")
@router.callback_query(F.data == "tasks")
async def show_tasks(event, state: FSMContext = None):
    msg = event.message if isinstance(event, CallbackQuery) else event
    if isinstance(event, CallbackQuery):
        await event.answer()

    user_id = msg.chat.id if isinstance(event, CallbackQuery) else event.from_user.id
    user = await db.get_user(user_id)
    if not user:
        return

    text = format_tasks(user)
    await msg.answer(text, reply_markup=back_keyboard())


# ═══════════════════════════════════════════════
# PROFILE
# ═══════════════════════════════════════════════
@router.message(F.text == "👤 Profil")
@router.callback_query(F.data == "profile")
async def show_profile(event, state: FSMContext = None):
    msg = event.message if isinstance(event, CallbackQuery) else event
    if isinstance(event, CallbackQuery):
        await event.answer()

    user_id = msg.chat.id if isinstance(event, CallbackQuery) else event.from_user.id
    user = await db.get_user(user_id)
    if not user:
        return

    text = format_profile_card(user)

    # Premium status
    tier = user.get("premium_tier", "free")
    if tier != "free":
        tier_info = PREMIUM_TIERS.get(tier, {})
        text += f"\n\n👑 Premium: <b>{tier_info.get('name', tier)}</b> {tier_info.get('icon', '')}"
    else:
        text += "\n\n💎 Premium: <i>Bepul rejim</i>"

    await msg.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👑 Premium ko'rish", callback_data="premium")],
        [InlineKeyboardButton(text="🏠 Menyu", callback_data="main_menu")],
    ]))


# ═══════════════════════════════════════════════
# PREMIUM
# ═══════════════════════════════════════════════
@router.callback_query(F.data == "premium")
async def show_premium(callback: CallbackQuery):
    await callback.answer()
    text = (
        "👑 <b>BIZNES MIYASI PREMIUM</b>\n"
        "━" * 28 + "\n\n"
        "🥉 <b>BRONZE — 149,000 so'm/oy</b>\n"
        "├ 10 ta moliyaviy tahlil\n"
        "├ 30 kunlik daromad prognozi\n"
        "└ AI chat (50 savol/oy)\n\n"
        "🥈 <b>SILVER — 390,000 so'm/oy</b> ⭐ ENG MASHHUR\n"
        "├ Cheksiz moliyaviy tahlillar\n"
        "├ 90 kunlik daromad prognozi\n"
        "├ Raqobatchi narx tahlili\n"
        "└ AI chat cheksiz + priority\n\n"
        "🥇 <b>GOLD — 1,450,000 so'm/oy</b>\n"
        "├ 1C va ERP integratsiya\n"
        "├ Dedikatsiyalangan server + SLA 99.9%\n"
        "├ Shaxsiy moliyaviy konsultant\n"
        "└ Xodimlar uchun o'qitish\n\n"
        "🔒 Xavfsiz to'lov · 7 kun qaytarish kafolati"
    )
    await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🥉 Bronze", callback_data="buy_bronze")],
        [InlineKeyboardButton(text="🥈 Silver ⭐", callback_data="buy_silver")],
        [InlineKeyboardButton(text="🥇 Gold", callback_data="buy_gold")],
        [InlineKeyboardButton(text="🏠 Menyu", callback_data="main_menu")],
    ]))


@router.callback_query(F.data.startswith("buy_"))
async def handle_buy(callback: CallbackQuery):
    tier = callback.data.replace("buy_", "")
    tier_info = PREMIUM_TIERS.get(tier, {})
    await callback.answer()
    await callback.message.answer(
        f"{tier_info.get('icon', '👑')} <b>{tier_info.get('name', tier)} — {tier_info.get('price', '')}</b>\n\n"
        f"To'lov uchun admin bilan bog'laning:\n\n"
        f"📱 Telegram: {ADMIN_TELEGRAM}\n"
        f"📞 Telefon: {ADMIN_PHONE}\n\n"
        f"<i>Tez orada avtomatik to'lov tizimi qo'shiladi!</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"📱 {ADMIN_TELEGRAM}", url=f"https://t.me/{ADMIN_TELEGRAM.replace('@', '')}")],
            [InlineKeyboardButton(text="🏠 Menyu", callback_data="main_menu")],
        ]),
    )


# ═══════════════════════════════════════════════
# MAIN MENU CALLBACK
# ═══════════════════════════════════════════════
@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.answer("🏠 <b>Bosh menyu</b>", reply_markup=main_inline_keyboard())


# ═══════════════════════════════════════════════
# HELP
# ═══════════════════════════════════════════════
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🧠 <b>BIZNES MIYASI — Yordam</b>\n"
        "━" * 28 + "\n\n"
        "<b>Buyruqlar:</b>\n"
        "/start — Botni boshlash\n"
        "/tahlil — Yangi moliyaviy tahlil\n"
        "/chat — AI chat rejimi\n"
        "/profil — Profilingiz\n"
        "/reyting — Reyting jadvali\n"
        "/vazifalar — Kunlik vazifalar\n"
        "/hisobot — PDF hisobot\n"
        "/help — Yordam\n\n"
        "<b>Ma'lumot kiritish:</b>\n"
        "📱 SMS — bank SMS larni yuboring\n"
        "📁 Fayl — CSV/Excel yuklang\n"
        "✏️ Qo'lda — tugma orqali\n\n"
        f"📞 Yordam: {ADMIN_TELEGRAM}",
        reply_markup=main_keyboard(),
    )


@router.message(Command("profil"))
async def cmd_profile(message: Message, state: FSMContext):
    await show_profile(message, state)


@router.message(Command("reyting"))
async def cmd_rating(message: Message, state: FSMContext):
    await show_leaderboard(message, state)


@router.message(Command("vazifalar"))
async def cmd_tasks(message: Message, state: FSMContext):
    await show_tasks(message, state)


@router.message(Command("hisobot"))
async def cmd_report(message: Message, state: FSMContext):
    await send_pdf_report(message, state)


# ═══════════════════════════════════════════════
# UNKNOWN MESSAGES (catch-all)
# ═══════════════════════════════════════════════
@router.message(StateFilter(None))
async def handle_unknown(message: Message, state: FSMContext):
    """Noma'lum xabarlar — AI chatga yo'naltirish"""
    text = message.text or ""
    if len(text) > 3:
        # Avtomatik AI chat
        await state.set_state(AIChat.chatting)
        await process_ai_question(message, message.from_user.id, text, state)
    else:
        await message.answer(
            "🤔 Tushinmadim. Quyidagi tugmalardan foydalaning yoki savol yozing!",
            reply_markup=main_inline_keyboard(),
        )


# ═══════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════
def parse_money_input(text: str) -> float:
    """Pul kiritishni parse qilish: '45M', '45000000', '45 000 000'"""
    import re
    text = text.strip().lower().replace(" ", "").replace(",", ".")
    # 45M, 45m
    m = re.match(r"([\d.]+)\s*m", text)
    if m:
        return float(m.group(1)) * 1_000_000
    # 45K, 45k
    m = re.match(r"([\d.]+)\s*k", text)
    if m:
        return float(m.group(1)) * 1_000
    # mlrd
    m = re.match(r"([\d.]+)\s*mlrd", text)
    if m:
        return float(m.group(1)) * 1_000_000_000
    try:
        return float(text)
    except ValueError:
        return 0


# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════
async def main():
    logger.info("🧠 Biznes Miyasi Bot ishga tushmoqda...")
    await db.init_db()
    logger.info("✅ Database tayyor")
    logger.info("🚀 Bot ishlayapti!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
