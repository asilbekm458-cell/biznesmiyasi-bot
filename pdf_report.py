"""
Biznes Miyasi Bot — PDF Hisobot Generator
Avtomatik moliyaviy hisobot yaratish
"""
import os
import io
from datetime import datetime


async def generate_pdf_report(analysis: dict, user: dict, transactions: list = None) -> bytes:
    """
    PDF moliyaviy hisobot yaratish
    fpdf2 kutubxonasi orqali
    """
    from fpdf import FPDF

    class BiznesPDF(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 12)
            self.set_text_color(0, 229, 204)
            self.cell(0, 10, "BIZNES MIYASI", 0, 0, "L")
            self.set_font("Helvetica", "", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, datetime.now().strftime("%d.%m.%Y %H:%M"), 0, 1, "R")
            self.set_draw_color(0, 229, 204)
            self.line(10, 18, 200, 18)
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 7)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f"Biznes Miyasi AI | Sahifa {self.page_no()}/{{nb}}", 0, 0, "C")

    pdf = BiznesPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    biz_name = analysis.get("business_name", "Biznes")
    income = analysis.get("income", 0)
    expense = analysis.get("expense", 0)
    profit = income - expense
    risk = analysis.get("risk_score", 0)
    margin = analysis.get("profit_margin", 0)
    employees = analysis.get("employees", 1)

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 12, f"Moliyaviy Tahlil: {biz_name}", 0, 1, "C")
    pdf.ln(3)

    # User info
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Tayyorlangan: {user.get('full_name', '')} | "
             f"Soha: {analysis.get('sector', '')} | "
             f"Sana: {datetime.now().strftime('%d.%m.%Y')}", 0, 1, "C")
    pdf.ln(8)

    # === ASOSIY KO'RSATKICHLAR ===
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(0, 100, 200)
    pdf.cell(0, 8, "ASOSIY KO'RSATKICHLAR", 0, 1)
    pdf.set_draw_color(0, 100, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # KPI table
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)
    kpis = [
        ("Daromad", f"{income:,.0f} so'm"),
        ("Xarajat", f"{expense:,.0f} so'm"),
        ("Foyda", f"{profit:,.0f} so'm"),
        ("Foyda marjasi", f"{round(profit/max(income,1)*100, 1)}%"),
        ("Risk skori", f"{risk}/100"),
        ("Xodimlar", str(employees)),
        ("Xodim samaradorligi", f"{income/max(employees,1):,.0f} so'm/kishi"),
    ]

    col_w = 95
    for i, (label, value) in enumerate(kpis):
        if i % 2 == 0:
            pdf.set_x(10)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(40, 6, label, 0, 0)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(55, 6, value, 0, 1 if i % 2 == 1 else 0)

    pdf.ln(8)

    # === RISK TAHLILI ===
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(200, 50, 50) if risk >= 60 else pdf.set_text_color(0, 150, 100)
    risk_label = "XAVFSIZ" if risk < 30 else ("O'RTA XAVF" if risk < 60 else "YUQORI XAVF")
    pdf.cell(0, 8, f"RISK TAHLILI: {risk}/100 — {risk_label}", 0, 1)
    pdf.set_draw_color(200, 50, 50) if risk >= 60 else pdf.set_draw_color(0, 150, 100)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # Risk bar
    bar_width = 180
    pdf.set_fill_color(230, 230, 230)
    pdf.rect(10, pdf.get_y(), bar_width, 6, "F")
    if risk < 30:
        pdf.set_fill_color(0, 200, 80)
    elif risk < 60:
        pdf.set_fill_color(255, 179, 0)
    else:
        pdf.set_fill_color(255, 59, 92)
    pdf.rect(10, pdf.get_y(), bar_width * risk / 100, 6, "F")
    pdf.ln(12)

    # === XARAJAT TARKIBI ===
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(0, 100, 200)
    pdf.cell(0, 8, "XARAJAT TARKIBI (taxminiy)", 0, 1)
    pdf.set_draw_color(0, 100, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    cost_items = [
        ("Maosh va mehnat", 35, (37, 99, 255)),
        ("Ijara va kommunal", 22, (0, 229, 204)),
        ("Xom ashyo / tovar", 28, (168, 85, 247)),
        ("O'lik tovar / isrof", 15, (255, 59, 92)),
    ]

    for name, pct, color in cost_items:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(50, 5, name, 0, 0)
        pdf.set_fill_color(240, 240, 240)
        pdf.rect(60, pdf.get_y(), 100, 5, "F")
        pdf.set_fill_color(*color)
        pdf.rect(60, pdf.get_y(), pct, 5, "F")
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(100, 5, "", 0, 0)
        pdf.cell(30, 5, f"{pct}% ({expense * pct / 100:,.0f})", 0, 1)

    pdf.ln(6)

    # === TAVSIYALAR ===
    waste = round(expense * 0.27)
    savings = round(waste * 0.62)

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(0, 100, 200)
    pdf.cell(0, 8, "AMALIY TAVSIYALAR", 0, 1)
    pdf.set_draw_color(0, 100, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    from config import SECTOR_ADVICE
    sector_info = SECTOR_ADVICE.get(analysis.get("sector", "boshqa"), SECTOR_ADVICE["boshqa"])

    recommendations = [
        f"Keraksiz xarajat (taxmin): ~{waste:,.0f} so'm/oy — audit qiling",
        f"Tejash imkoni: +{savings:,.0f} so'm/oy (yillik: {savings*12:,.0f} so'm)",
        f"Soha tavsiyasi: {sector_info['tips'][0]}",
        "Haftalik P&L (foyda-zarar) jadvalini yuritishni boshlang",
        "Xodimlar uchun KPI o'rnating — rag'batlantirish tizimi kiriting",
    ]

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)
    for i, rec in enumerate(recommendations, 1):
        pdf.multi_cell(0, 5, f"  {i}. {rec}")
        pdf.ln(2)

    pdf.ln(4)

    # === 3 OYLIK PROGNOZ ===
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(0, 150, 100)
    pdf.cell(0, 8, "3 OYLIK PROGNOZ (tavsiyalar bajarilsa)", 0, 1)
    pdf.set_draw_color(0, 150, 100)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    profit_increase = round(savings / max(profit, 1) * 100) if profit > 0 else 0
    forecast = [
        f"Oylik tejash: +{savings:,.0f} so'm",
        f"Foyda o'sishi: +{profit_increase}%",
        f"Yillik tejash: {savings * 12:,.0f} so'm",
        f"3 oyda foyda: ~{profit + savings:,.0f} → {profit + savings * 3:,.0f} so'm",
    ]

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 120, 80)
    for item in forecast:
        pdf.cell(0, 6, f"  → {item}", 0, 1)

    # Footer text
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(0, 4,
        "Bu hisobot Biznes Miyasi AI tomonidan avtomatik yaratilgan. "
        "Barcha raqamlar taxminiy bo'lib, aniq buxgalteriya hisobiga asoslangan emas. "
        "Professional moliyaviy maslahat uchun buxgalteringizga murojaat qiling.",
        align="C"
    )

    return pdf.output()


async def generate_transactions_report(user: dict, transactions: list) -> bytes:
    """Tranzaksiyalar ro'yxati PDF"""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"Tranzaksiyalar hisoboti — {user.get('full_name', '')}", 0, 1, "C")
    pdf.ln(5)

    # Jadval sarlavha
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(0, 100, 200)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(25, 7, "Sana", 1, 0, "C", True)
    pdf.cell(25, 7, "Tur", 1, 0, "C", True)
    pdf.cell(40, 7, "Summa", 1, 0, "C", True)
    pdf.cell(30, 7, "Kategoriya", 1, 0, "C", True)
    pdf.cell(70, 7, "Izoh", 1, 1, "C", True)

    # Ma'lumotlar
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(50, 50, 50)
    total_income = 0
    total_expense = 0

    for tx in transactions[:100]:  # Max 100 ta
        tx_type = tx.get("type", "expense")
        amount = tx.get("amount", 0)
        if tx_type == "income":
            total_income += amount
            pdf.set_text_color(0, 150, 80)
        else:
            total_expense += amount
            pdf.set_text_color(200, 50, 50)

        pdf.cell(25, 6, str(tx.get("date", ""))[:10], 1, 0, "C")
        pdf.cell(25, 6, "Kirim" if tx_type == "income" else "Chiqim", 1, 0, "C")
        pdf.cell(40, 6, f"{amount:,.0f}", 1, 0, "R")
        pdf.set_text_color(50, 50, 50)
        pdf.cell(30, 6, tx.get("category", "")[:15], 1, 0, "C")
        pdf.cell(70, 6, tx.get("description", "")[:35], 1, 1)

    # Jami
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 7, f"Jami kirim: {total_income:,.0f} so'm | "
             f"Jami chiqim: {total_expense:,.0f} so'm | "
             f"Foyda: {total_income - total_expense:,.0f} so'm", 0, 1)

    return pdf.output()
