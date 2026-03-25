"""
Biznes Miyasi Bot — CSV/Excel Import Service
1C, Excel, CSV fayllarni parse qilish
"""
import csv
import io
import re
from datetime import date


def parse_csv_data(content: str | bytes) -> list[dict]:
    """
    CSV faylni parse qilish
    Avtomatik ustun aniqlash
    """
    if isinstance(content, bytes):
        # Encoding detect
        for enc in ["utf-8", "cp1251", "latin-1", "utf-16"]:
            try:
                content = content.decode(enc)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

    transactions = []
    reader = csv.reader(io.StringIO(content), delimiter=detect_delimiter(content))
    rows = list(reader)

    if not rows:
        return []

    # Sarlavha qatorini aniqlash
    header_idx = find_header_row(rows)
    if header_idx is None:
        return []

    headers = [h.strip().lower() for h in rows[header_idx]]

    # Ustun mapping
    col_map = map_columns(headers)

    for row in rows[header_idx + 1:]:
        if len(row) <= max(col_map.values(), default=0):
            continue

        tx = parse_row(row, col_map)
        if tx and tx["amount"] > 0:
            transactions.append(tx)

    return transactions


def detect_delimiter(content: str) -> str:
    """Delimiter aniqlash"""
    first_lines = content[:2000]
    counts = {
        ",": first_lines.count(","),
        ";": first_lines.count(";"),
        "\t": first_lines.count("\t"),
        "|": first_lines.count("|"),
    }
    return max(counts, key=counts.get)


def find_header_row(rows: list) -> int | None:
    """Sarlavha qatorini topish"""
    header_keywords = [
        "summa", "amount", "сумма", "дата", "date", "sana",
        "daromad", "xarajat", "income", "expense", "доход", "расход",
        "kirim", "chiqim", "turi", "type", "тип", "категория",
        "debet", "kredit", "debit", "credit", "дебет", "кредит",
    ]
    for i, row in enumerate(rows[:10]):  # Birinchi 10 qator
        row_text = " ".join(str(cell).lower() for cell in row)
        matches = sum(1 for kw in header_keywords if kw in row_text)
        if matches >= 2:
            return i
    return 0  # Default: birinchi qator


def map_columns(headers: list) -> dict:
    """Ustunlarni mapping qilish"""
    col_map = {}

    # Summa / Amount
    amount_keywords = ["summa", "amount", "сумма", "miqdor", "sum", "qiymat", "kirim", "daromad"]
    for i, h in enumerate(headers):
        for kw in amount_keywords:
            if kw in h:
                col_map["amount"] = i
                break
        if "amount" in col_map:
            break

    # Tur / Type
    type_keywords = ["tur", "type", "тип", "vid", "вид", "kirim/chiqim"]
    for i, h in enumerate(headers):
        for kw in type_keywords:
            if kw in h:
                col_map["type"] = i
                break

    # Sana / Date
    date_keywords = ["sana", "date", "дата", "kun", "vaqt", "время"]
    for i, h in enumerate(headers):
        for kw in date_keywords:
            if kw in h:
                col_map["date"] = i
                break

    # Kategoriya
    cat_keywords = ["kategoriya", "category", "категория", "soha", "razryad"]
    for i, h in enumerate(headers):
        for kw in cat_keywords:
            if kw in h:
                col_map["category"] = i
                break

    # Izoh / Description
    desc_keywords = ["izoh", "description", "описание", "примечание", "comment", "sharh"]
    for i, h in enumerate(headers):
        for kw in desc_keywords:
            if kw in h:
                col_map["description"] = i
                break

    # Debet / Kredit (1C format)
    for i, h in enumerate(headers):
        if any(kw in h for kw in ["debet", "debit", "дебет"]):
            col_map["debit"] = i
        if any(kw in h for kw in ["kredit", "credit", "кредит"]):
            col_map["credit"] = i

    # Agar summa topilmasa — eng katta raqamli ustunni olish
    if "amount" not in col_map:
        for i, h in enumerate(headers):
            if i not in col_map.values():
                col_map.setdefault("amount", i)
                break

    return col_map


def parse_row(row: list, col_map: dict) -> dict | None:
    """Bir qatorni parse qilish"""
    try:
        # 1C Debet/Kredit formati
        if "debit" in col_map and "credit" in col_map:
            debit = parse_number(row[col_map["debit"]])
            credit = parse_number(row[col_map["credit"]])
            if debit > 0:
                return {
                    "type": "expense",
                    "amount": debit,
                    "category": get_cell(row, col_map, "category", "boshqa"),
                    "description": get_cell(row, col_map, "description", "1C import"),
                    "date": parse_date(get_cell(row, col_map, "date", "")),
                    "source": "1c_import",
                }
            elif credit > 0:
                return {
                    "type": "income",
                    "amount": credit,
                    "category": get_cell(row, col_map, "category", "boshqa"),
                    "description": get_cell(row, col_map, "description", "1C import"),
                    "date": parse_date(get_cell(row, col_map, "date", "")),
                    "source": "1c_import",
                }
            return None

        # Standart format
        amount = parse_number(get_cell(row, col_map, "amount", "0"))
        if amount <= 0:
            return None

        tx_type = detect_type_from_cell(get_cell(row, col_map, "type", "expense"))

        return {
            "type": tx_type,
            "amount": abs(amount),
            "category": get_cell(row, col_map, "category", "boshqa"),
            "description": get_cell(row, col_map, "description", "CSV import"),
            "date": parse_date(get_cell(row, col_map, "date", "")),
            "source": "csv_import",
        }
    except (IndexError, ValueError):
        return None


def get_cell(row: list, col_map: dict, key: str, default: str = "") -> str:
    idx = col_map.get(key)
    if idx is not None and idx < len(row):
        return str(row[idx]).strip()
    return default


def parse_number(text: str) -> float:
    """Raqamni parse qilish"""
    if not text:
        return 0
    cleaned = text.replace(" ", "").replace("\u00a0", "").replace(",", ".")
    cleaned = re.sub(r"[^\d.\-]", "", cleaned)
    try:
        return float(cleaned)
    except ValueError:
        return 0


def detect_type_from_cell(text: str) -> str:
    """Hujayra qiymatidan tur aniqlash"""
    t = text.lower()
    if any(kw in t for kw in ["kirim", "income", "daromad", "tushum", "доход", "приход", "credit"]):
        return "income"
    return "expense"


def parse_date(text: str) -> str:
    """Sana parse qilish"""
    if not text:
        return date.today().isoformat()

    # dd.mm.yyyy
    m = re.match(r"(\d{1,2})[./\-](\d{1,2})[./\-](\d{2,4})", text)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        try:
            return date(y, mo, d).isoformat()
        except ValueError:
            pass

    # yyyy-mm-dd
    m = re.match(r"(\d{4})[./\-](\d{1,2})[./\-](\d{1,2})", text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            pass

    return date.today().isoformat()


async def parse_excel_file(file_bytes: bytes) -> list[dict]:
    """Excel faylni parse qilish (openpyxl orqali)"""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        ws = wb.active

        # CSV formatga o'girish
        rows = []
        for row in ws.iter_rows(values_only=True):
            rows.append([str(cell) if cell is not None else "" for cell in row])

        if not rows:
            return []

        # CSV parser orqali
        csv_content = "\n".join(";".join(row) for row in rows)
        return parse_csv_data(csv_content)
    except ImportError:
        return []
    except Exception:
        return []
