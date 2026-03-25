"""
Biznes Miyasi Bot — Moliyaviy Tahlil Engine
v10 JS logikasidan portlangan + kengaytirilgan
"""
from config import SECTOR_ADVICE


def fmt_money(amount: float) -> str:
    """Pulni formatlash: 45000000 -> 45.0M"""
    if amount >= 1_000_000_000:
        return f"{amount / 1_000_000_000:.1f} mlrd"
    elif amount >= 1_000_000:
        return f"{amount / 1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"{amount / 1_000:.0f}K"
    return f"{amount:.0f}"


def fmt_money_full(amount: float) -> str:
    """To'liq formatlash: 45,000,000 so'm"""
    return f"{amount:,.0f} so'm".replace(",", " ")


def calculate_risk_score(data: dict) -> int:
    """
    Risk skorini hisoblash (0-100)
    v10 algoritmidan kengaytirilgan versiya
    """
    income = data.get("income", 0)
    expense = data.get("expense", 0)
    employees = data.get("employees", 1)
    period = data.get("period", "orta")
    problem = data.get("problem", "")

    if income <= 0:
        return 95

    score = 0
    margin = (income - expense) / income

    # Foyda marjasi
    if margin < 0:
        score += 55
    elif margin < 0.05:
        score += 40
    elif margin < 0.12:
        score += 26
    elif margin < 0.20:
        score += 12
    elif margin < 0.30:
        score += 5

    # Xodim samaradorligi
    per_employee = income / max(employees, 1)
    if per_employee < 2_000_000:
        score += 15
    elif per_employee < 4_000_000:
        score += 8

    # Xarajat nisbati
    expense_ratio = expense / income if income > 0 else 1
    if expense_ratio > 0.95:
        score += 15
    elif expense_ratio > 0.85:
        score += 8
    elif expense_ratio > 0.75:
        score += 4

    # Biznes yoshi
    if period == "yangi":
        score += 20
    elif period == "orta":
        score += 6

    # Muammo bor-yo'qligi
    if problem and len(problem) > 4:
        score += 7

    return min(96, max(6, score))


def full_analysis(data: dict) -> dict:
    """
    To'liq moliyaviy tahlil
    Returns: risk, tavsiyalar, prognoz, ko'rsatkichlar
    """
    income = data.get("income", 0)
    expense = data.get("expense", 0)
    employees = data.get("employees", 1)
    sector = data.get("sector", "boshqa")
    period = data.get("period", "orta")
    problem = data.get("problem", "")
    biz_name = data.get("business_name", "Biznesingiz")

    profit = income - expense
    margin = round((profit / income * 100), 1) if income > 0 else 0
    waste = round(expense * 0.27)  # Isrof taxmini
    savings = round(waste * 0.62)  # Tejash imkoniyati
    risk = calculate_risk_score(data)
    per_employee = round(income / max(employees, 1))

    # Soha tavsiyalari
    sector_info = SECTOR_ADVICE.get(sector, SECTOR_ADVICE["boshqa"])

    # Margin holati
    if margin < 5:
        margin_status = "🚨 KRITIK: foyda juda past"
        margin_advice = "Zudlik bilan choralar ko'ring"
    elif margin < 15:
        margin_status = "⚠️ O'rta: optimallashtirish zarur"
        margin_advice = "Xarajatlarni kamaytiring"
    elif margin < 25:
        margin_status = "✅ Yaxshi, lekin yaxshilash mumkin"
        margin_advice = "Yaxshi holat — o'sishga e'tibor bering"
    else:
        margin_status = "🌟 Ajoyib!"
        margin_advice = "Kengayishni rejalashtiring"

    # Risk darajasi
    if risk < 30:
        risk_label = "✅ Xavfsiz"
        risk_advice = "Asosiy maqsad — o'sish va kengayish"
    elif risk < 60:
        risk_label = "⚠️ O'rta xavf"
        risk_advice = "Optimallashtirish va xarajat nazorati kerak"
    else:
        risk_label = "🚨 Yuqori xavf"
        risk_advice = "Darhol choralar ko'ring!"

    # Xarajat tarkibi (taxminiy)
    cost_breakdown = [
        {"name": "Maosh va mehnat", "percent": 35},
        {"name": "Ijara va kommunal", "percent": 22},
        {"name": "Xom ashyo / tovar", "percent": 28},
        {"name": "O'lik tovar / isrof", "percent": 15},
    ]

    # 3 oylik prognoz
    profit_increase = round(savings / max(profit, 1) * 100) if profit > 0 else 0

    result = {
        # Asosiy ko'rsatkichlar
        "business_name": biz_name,
        "sector": sector,
        "sector_info": sector_info,
        "income": income,
        "expense": expense,
        "profit": profit,
        "margin": margin,
        "margin_status": margin_status,
        "margin_advice": margin_advice,
        "employees": employees,
        "per_employee": per_employee,
        "period": period,
        "problem": problem,
        # Risk
        "risk_score": risk,
        "risk_label": risk_label,
        "risk_advice": risk_advice,
        # Isrof va tejash
        "waste_estimate": waste,
        "savings_potential": savings,
        "cost_breakdown": cost_breakdown,
        # Prognoz
        "profit_increase_pct": profit_increase,
        "annual_savings": savings * 12,
        # Tavsiyalar
        "recommendations": generate_recommendations(data, risk, margin, savings, sector_info),
    }

    return result


def generate_recommendations(data: dict, risk: int, margin: float,
                              savings: float, sector_info: dict) -> list:
    """Shaxsiy tavsiyalar generatsiya qilish"""
    recs = []
    income = data.get("income", 0)
    expense = data.get("expense", 0)
    employees = data.get("employees", 1)

    # Soha tavsiyasi
    if sector_info.get("tips"):
        recs.append(f"📌 {sector_info['tips'][0]}")

    # Margin bo'yicha
    if margin < 5:
        recs.append(f"🚨 Zudlik: xarajatlarni kamida 15% kamaytiring — {fmt_money_full(round(expense * 0.15))} tejash")
    elif margin < 15:
        recs.append(f"✂️ Eng katta 3 xarajat moddani audit qiling — {fmt_money_full(savings)} tejash realistik")
    else:
        recs.append(f"📈 Daromadni oshirishga e'tibor bering — yangi mijoz kanallari")

    # Xodim samaradorligi
    per_emp = income / max(employees, 1)
    if per_emp < 3_000_000:
        recs.append(f"👥 Xodim samaradorligi past ({fmt_money(per_emp)}/kishi) — KPI tizimi o'rnating")

    # Risk bo'yicha
    if risk >= 60:
        recs.append("🛡️ Zaxira fond yarating — kamida 1 oylik xarajat miqdorida")
        recs.append("📊 Har kunlik naqd pul oqimi kuzatuvini boshlang")
    elif risk >= 30:
        recs.append("📋 Haftalik P&L (foyda-zarar) jadvalini yuritishni boshlang")

    # Umumiy
    recs.append(f"💡 Haftalik tahlil qiling — {fmt_money(savings)} so'm/oy tejash imkoni")

    return recs[:6]  # Max 6 ta tavsiya


def generate_analysis_text(result: dict) -> str:
    """Telegram uchun formatlangan tahlil natijasi"""
    r = result
    icon = r["sector_info"].get("icon", "📊")

    text = f"""
{icon} <b>{r['business_name']}</b> — Moliyaviy Tahlil
{'━' * 28}

💰 <b>ASOSIY KO'RSATKICHLAR</b>
├ Daromad: <code>{fmt_money_full(r['income'])}</code>
├ Xarajat: <code>{fmt_money_full(r['expense'])}</code>
├ Foyda: <code>{fmt_money_full(r['profit'])}</code>
├ Foyda marjasi: <b>{r['margin']}%</b> {r['margin_status']}
└ Xodim samaradorligi: <code>{fmt_money_full(r['per_employee'])}</code>/kishi

{'━' * 28}

⚡ <b>RISK SKORI: {r['risk_score']}/100</b> {r['risk_label']}
{r['risk_advice']}

{'━' * 28}

🔍 <b>ANIQLANGAN MUAMMOLAR</b>
├ Keraksiz xarajat (taxmin): ~<code>{fmt_money_full(r['waste_estimate'])}</code>/oy
├ Bu daromadning <b>{round(r['waste_estimate']/max(r['income'],1)*100)}%</b> isrof
└ Tejash imkoni: <code>+{fmt_money_full(r['savings_potential'])}</code>/oy

{'━' * 28}

📊 <b>XARAJAT TARKIBI</b> (taxminiy)"""

    for item in r["cost_breakdown"]:
        bar = "█" * (item["percent"] // 5) + "░" * (20 - item["percent"] // 5)
        text += f"\n  {item['name']}: {bar} {item['percent']}%"

    text += f"""

{'━' * 28}

💡 <b>AMALIY TAVSIYALAR</b>"""

    for i, rec in enumerate(r["recommendations"], 1):
        text += f"\n{i}. {rec}"

    text += f"""

{'━' * 28}

📈 <b>3 OYLIK PROGNOZ</b> (tavsiyalar bajarilsa)
├ Oylik tejash: <code>+{fmt_money_full(r['savings_potential'])}</code>
├ Foyda o'sishi: <b>+{r['profit_increase_pct']}%</b>
└ Yillik tejash: <code>{fmt_money_full(r['annual_savings'])}</code>

🧠 <i>Biznes Miyasi AI tahlili</i>
"""
    return text.strip()


def generate_quick_summary(data: dict) -> str:
    """Qisqa xulosa (chat uchun)"""
    risk = calculate_risk_score(data)
    income = data.get("income", 0)
    expense = data.get("expense", 0)
    profit = income - expense
    margin = round((profit / income * 100), 1) if income > 0 else 0

    if risk < 30:
        emoji = "✅"
    elif risk < 60:
        emoji = "⚠️"
    else:
        emoji = "🚨"

    return (
        f"{emoji} Risk: {risk}/100 | "
        f"Foyda: {fmt_money_full(profit)} ({margin}%) | "
        f"Tejash: +{fmt_money_full(round(expense * 0.27 * 0.62))}/oy"
    )
