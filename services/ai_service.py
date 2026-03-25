"""
Biznes Miyasi Bot — AI Service
Gibrid model: Gemini Flash (85%) + GPT-4o (15%)
Murakkablik skorer + semantic cache
"""
import json
import hashlib
from config import AI_CONFIG, GEMINI_API_KEY, OPENAI_API_KEY

# Simple in-memory cache (production da Redis ishlatiladi)
_cache: dict[str, str] = {}
_cache_max = 500


def _cache_key(text: str) -> str:
    return hashlib.md5(text.lower().strip().encode()).hexdigest()


def get_cached(text: str) -> str | None:
    return _cache.get(_cache_key(text))


def set_cached(text: str, response: str):
    if len(_cache) > _cache_max:
        # Eng eski 100 tani o'chirish
        keys = list(_cache.keys())[:100]
        for k in keys:
            _cache.pop(k, None)
    _cache[_cache_key(text)] = response


def calculate_complexity(text: str) -> float:
    """
    So'rov murakkabligini baholash (0-1)
    < 0.6 = oddiy (Gemini Flash)
    >= 0.6 = murakkab (GPT-4o)
    """
    score = 0.0
    text_lower = text.lower()

    # Uzunlik
    words = text.split()
    if len(words) > 50:
        score += 0.15
    elif len(words) > 20:
        score += 0.08

    # Murakkab kalit so'zlar
    complex_keywords = [
        "prognoz", "forecast", "kelajak", "5 yil", "strategiya",
        "investitsiya", "kredit", "soliq", "audit", "diversifikatsiya",
        "regression", "anomaliya", "trend", "korrelatsiya", "risk model",
        "monte carlo", "cashflow", "dcf", "npv", "irr", "wacc",
        "break-even", "sensitivity", "scenario", "stress test",
    ]
    complex_count = sum(1 for kw in complex_keywords if kw in text_lower)
    score += min(0.4, complex_count * 0.1)

    # Raqamlar soni (ko'p raqam = murakkab)
    import re
    numbers = re.findall(r"\d+", text)
    if len(numbers) > 5:
        score += 0.15
    elif len(numbers) > 2:
        score += 0.05

    # Savol turi
    if any(kw in text_lower for kw in ["nima qilsam", "qanday", "tahlil qil", "strategiya"]):
        score += 0.1

    return min(1.0, score)


def route_model(complexity: float) -> str:
    """Model yo'naltirish"""
    threshold = AI_CONFIG.get("complexity_threshold", 0.6)
    if complexity >= threshold:
        return AI_CONFIG["complex_model"]
    return AI_CONFIG["simple_model"]


def build_system_prompt(user_data: dict = None, analysis_data: dict = None) -> str:
    """Tizim promptini yaratish (700 tokenga siqilgan)"""
    prompt = """Sen Biznes Miyasi AI — O'zbekiston KOBlar uchun moliyaviy maslahatchi.
Rol: O'zbek tilida aniq, amaliy biznes maslahat ber.
Qoidalar:
- Faqat o'zbek tilida javob ber
- Har bir javobda ANIQ raqamlar va foizlar ber
- Amaliy qadam ko'rsat (1-2-3 formatda)
- Soha bo'yicha maxsus tavsiya ber
- Musbat va motivatsion ohangda gapir
- Qisqa va aniq bo'l (300 so'zdan oshmasin)"""

    if user_data:
        prompt += f"\nFoydalanuvchi: {user_data.get('full_name', 'Tadbirkor')}"
        if user_data.get("business_name"):
            prompt += f", Biznes: {user_data['business_name']}"
        if user_data.get("sector"):
            prompt += f", Soha: {user_data['sector']}"

    if analysis_data:
        from services.analysis import fmt_money_full
        prompt += f"""
Oxirgi tahlil:
- Daromad: {fmt_money_full(analysis_data.get('income', 0))}
- Xarajat: {fmt_money_full(analysis_data.get('expense', 0))}
- Risk: {analysis_data.get('risk_score', 0)}/100
- Xodimlar: {analysis_data.get('employees', 1)}"""

    return prompt


async def ask_ai(question: str, user_data: dict = None,
                 analysis_data: dict = None) -> str:
    """
    AI ga savol berish — gibrid routing bilan
    """
    # Cache tekshirish
    cached = get_cached(question)
    if cached:
        return cached

    complexity = calculate_complexity(question)
    model = route_model(complexity)
    system_prompt = build_system_prompt(user_data, analysis_data)

    try:
        if "gemini" in model:
            response = await _ask_gemini(question, system_prompt)
        else:
            response = await _ask_openai(question, system_prompt)

        if response:
            set_cached(question, response)
            return response
    except Exception as e:
        # Fallback: agar birinchi model ishlamasa, ikkinchisini sinash
        try:
            if "gemini" in model:
                response = await _ask_openai(question, system_prompt)
            else:
                response = await _ask_gemini(question, system_prompt)
            if response:
                return response
        except Exception:
            pass

    # Offline fallback
    return _offline_response(question, user_data, analysis_data)


async def _ask_gemini(question: str, system_prompt: str) -> str:
    """Google Gemini API"""
    if not GEMINI_API_KEY:
        return ""

    import aiohttp
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [
            {"parts": [{"text": f"{system_prompt}\n\nSavol: {question}"}]}
        ],
        "generationConfig": {
            "temperature": AI_CONFIG["temperature"],
            "maxOutputTokens": AI_CONFIG["max_tokens"],
        },
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status == 200:
                data = await resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
    return ""


async def _ask_openai(question: str, system_prompt: str) -> str:
    """OpenAI GPT-4o API"""
    if not OPENAI_API_KEY:
        return ""

    import aiohttp
    url = "https://api.openai.com/v1/chat/completions"

    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "max_tokens": AI_CONFIG["max_tokens"],
        "temperature": AI_CONFIG["temperature"],
    }

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers,
                                timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status == 200:
                data = await resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
    return ""


def _offline_response(question: str, user_data: dict = None,
                      analysis_data: dict = None) -> str:
    """Offline javob — AI ishlamaganida"""
    from services.analysis import fmt_money_full, calculate_risk_score

    q = question.lower()

    if analysis_data:
        income = analysis_data.get("income", 0)
        expense = analysis_data.get("expense", 0)
        profit = income - expense
        risk = analysis_data.get("risk_score", calculate_risk_score(analysis_data))
        savings = round(expense * 0.27 * 0.62)

        if any(kw in q for kw in ["foyda", "profit", "daromad"]):
            return (
                f"📊 Sizning foydangiz: {fmt_money_full(profit)}/oy\n"
                f"Foyda marjasi: {round(profit/max(income,1)*100, 1)}%\n\n"
                f"💡 Tavsiya: Eng katta 3 xarajat moddani audit qiling — "
                f"{fmt_money_full(savings)} tejash imkoni bor!"
            )

        if any(kw in q for kw in ["xavf", "risk", "bankrot"]):
            return (
                f"🛡️ Risk skoringiz: {risk}/100\n\n"
                + ("✅ Xavfsiz zonada — o'sishga e'tibor bering!" if risk < 30
                   else "⚠️ O'rta xavf — haftalik P&L jadval yuritishni boshlang!"
                   if risk < 60
                   else "🚨 Yuqori xavf! Zudlik: xarajatlarni 20% kamaytiring!")
            )

        if any(kw in q for kw in ["xarajat", "tejash", "kamayt"]):
            return (
                f"✂️ Tejash imkoni: {fmt_money_full(savings)}/oy\n\n"
                f"3 qadam:\n"
                f"1. Eng katta xarajat moddani aniqlang\n"
                f"2. Xodim KPI tizimini o'rnating\n"
                f"3. Haftalik moliyaviy tekshiruv boshlang"
            )

    if any(kw in q for kw in ["salom", "assalom", "hello"]):
        name = user_data.get("full_name", "Tadbirkor") if user_data else "Tadbirkor"
        return f"👋 Salom, {name}! Men Biznes Miyasi AI — moliyaviy maslahatchi. Nima haqida savol berasiz?"

    if any(kw in q for kw in ["yordam", "help", "nima"]):
        return (
            "🆘 Men sizga yordam bera olaman:\n\n"
            "💰 Xarajat qisqartirish\n"
            "📈 Daromad oshirish strategiyasi\n"
            "⚡ Risk tahlili\n"
            "🔍 Raqobatchilar tahlili\n"
            "📊 Moliyaviy prognoz\n\n"
            "Qaysi yo'nalishda yordam kerak?"
        )

    return (
        "🤔 Savolingizni tushundim! Aniqroq savol bering — masalan:\n"
        "• 'Xarajatni qanday kamaytiraman?'\n"
        "• 'Daromadni oshirish yo'llari'\n"
        "• 'Biznesim risk darajasi qanday?'"
    )
