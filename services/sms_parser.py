"""
Biznes Miyasi Bot — Bank SMS Parser
12+ bank formati: Uzcard, Humo, Kapitalbank, Ipoteka-bank, Asaka va h.k.
"""
import re
from datetime import date
from config import SMS_PATTERNS


def parse_amount(raw: str) -> float:
    """Summani parse qilish: '45 000,50' -> 45000.5, '2.500.000' -> 2500000"""
    cleaned = raw.replace(" ", "").replace("\u00a0", "")
    # Agar nuqta minglik ajratuvchi sifatida ishlatilsa: 2.500.000
    dot_count = cleaned.count(".")
    comma_count = cleaned.count(",")
    if dot_count > 1 and comma_count == 0:
        # Nuqtalar minglik ajratuvchi: 2.500.000 -> 2500000
        cleaned = cleaned.replace(".", "")
    elif comma_count > 1 and dot_count == 0:
        # Vergullar minglik ajratuvchi: 2,500,000 -> 2500000
        cleaned = cleaned.replace(",", "")
    elif comma_count == 1 and dot_count == 0:
        # 150,000 -> minglik (3 raqam keyin) vs 45000,50 -> kasr (2 raqam keyin)
        parts = cleaned.split(",")
        if len(parts[1]) == 3:
            cleaned = cleaned.replace(",", "")  # 150,000 -> 150000
        else:
            cleaned = cleaned.replace(",", ".")  # 45000,50 -> 45000.50
    elif dot_count == 1 and comma_count == 0:
        # Nuqta kasr yoki minglik — kontekstga qarab
        parts = cleaned.split(".")
        if len(parts[1]) == 3 and len(parts[0]) <= 3:
            cleaned = cleaned.replace(".", "")  # 2.500 -> 2500
        # Aks holda kasr sifatida qoladi: 45.5
    else:
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        nums = re.findall(r"\d+", cleaned)
        if nums:
            return float("".join(nums))
        return 0


def detect_bank(text: str) -> str:
    """Bank nomini aniqlash"""
    text_lower = text.lower()
    bank_keywords = {
        "uzcard": ["uzcard", "uz card"],
        "humo": ["humo", "хумо"],
        "kapitalbank": ["kapitalbank", "капиталбанк", "kapital"],
        "ipoteka_bank": ["ipoteka", "ипотека", "ipotekabank"],
        "asakabank": ["asaka", "асака", "asakabank"],
        "aloqabank": ["aloqa", "алоқа"],
        "hamkorbank": ["hamkor", "hamkorbank"],
        "xalq_bank": ["xalq bank", "халқ банк"],
        "davr_bank": ["davr bank", "давр"],
        "trustbank": ["trustbank", "trust bank"],
        "orient_finance": ["orient", "ориент"],
        "infinbank": ["infin", "infinbank"],
    }
    for bank, keywords in bank_keywords.items():
        for kw in keywords:
            if kw in text_lower:
                return bank
    return "universal"


def classify_transaction(text: str) -> str:
    """Tranzaksiya turini aniqlash (income/expense)"""
    text_lower = text.lower()

    income_keywords = [
        "kirim", "popolnenie", "tushum", "zachislenie",
        "зачисление", "пополнение", "credit", "o'tkazma olindi",
        "perevod poluchil", "перевод получил", "cashback"
    ]
    expense_keywords = [
        "chiqim", "spisanie", "xarid", "to'lov", "oplata",
        "списание", "покупка", "оплата", "debit", "debet",
        "transfer sent", "perevod otprav", "перевод отправ"
    ]

    for kw in income_keywords:
        if kw in text_lower:
            return "income"
    for kw in expense_keywords:
        if kw in text_lower:
            return "expense"

    # +/- belgilari bo'yicha
    if re.search(r"[+]\s*\d", text):
        return "income"
    if re.search(r"[-]\s*\d", text):
        return "expense"

    return "expense"  # Default


def extract_category(text: str) -> str:
    """Xarajat kategoriyasini aniqlash"""
    text_lower = text.lower()
    categories = {
        "oziq-ovqat": ["market", "dokon", "magazin", "supermarket", "korzinka", "makro", "havas", "meva"],
        "transport": ["taxi", "taksi", "yandex", "uber", "benzin", "gaz", "avto"],
        "kommunal": ["kommunal", "elektr", "gaz", "suv", "internet", "telefon"],
        "ijara": ["ijara", "arenda", "kvartira", "uy"],
        "maosh": ["maosh", "oylik", "ish haqi", "zarplata"],
        "reklama": ["reklama", "marketing", "google", "facebook", "instagram", "ads"],
        "tovar": ["tovar", "mahsulot", "zakaz", "optom", "zakupka"],
        "xizmat": ["xizmat", "servis", "remont", "ta'mir"],
        "soliq": ["soliq", "nalog", "budjet", "davlat"],
    }
    for cat, keywords in categories.items():
        for kw in keywords:
            if kw in text_lower:
                return cat
    return "boshqa"


def parse_sms(text: str) -> dict | None:
    """
    SMS ni parse qilish
    Returns: {"type": "income/expense", "amount": float, "bank": str, "category": str}
    """
    if not text or len(text) < 10:
        return None

    bank = detect_bank(text)
    tx_type = classify_transaction(text)

    # Bank-specific patterns
    patterns = SMS_PATTERNS.get(bank, SMS_PATTERNS["universal"])
    type_patterns = patterns.get(tx_type, patterns.get("expense", []))

    amount = 0
    for pattern in type_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = parse_amount(match.group(1))
            break

    # Agar hech qanday pattern ishlamasa — universal
    if amount == 0:
        universal_patterns = SMS_PATTERNS["universal"][tx_type]
        for pattern in universal_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = parse_amount(match.group(1))
                break

    # Hali ham 0 bo'lsa — har qanday raqamni olish
    if amount == 0:
        nums = re.findall(r"(\d[\d\s,.]{3,})", text)
        for n in nums:
            val = parse_amount(n)
            if val >= 100:  # Kamida 100 so'm
                amount = val
                break

    if amount <= 0:
        return None

    return {
        "type": tx_type,
        "amount": amount,
        "bank": bank,
        "category": extract_category(text),
        "description": text[:100],
        "source": "sms",
    }


def parse_multiple_sms(texts: list[str]) -> list[dict]:
    """Bir nechta SMS ni parse qilish"""
    results = []
    for text in texts:
        parsed = parse_sms(text.strip())
        if parsed:
            results.append(parsed)
    return results


def parse_sms_bulk(raw_text: str) -> list[dict]:
    """
    Yirik SMS matn — har bir SMS ni ajratib parse qilish
    SMS lar yangi qator bilan ajralgan deb hisoblanadi
    """
    # SMS larni ajratish
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    return parse_multiple_sms(lines)
