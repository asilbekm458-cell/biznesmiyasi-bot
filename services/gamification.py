"""
Biznes Miyasi Bot — Gamification Service
Ballar, seviyalar, yutuqlar, streak tizimi
"""
from config import LEVELS, ACHIEVEMENTS
import database as db


def get_level(points: int) -> dict:
    """Joriy seviyani aniqlash"""
    for lvl in reversed(LEVELS):
        if points >= lvl["min"]:
            return lvl
    return LEVELS[0]


def get_level_progress(points: int) -> dict:
    """Seviya progressi"""
    lvl = get_level(points)
    next_lvl = LEVELS[min(lvl["id"] + 1, len(LEVELS) - 1)]
    progress = (points - lvl["min"]) / max(lvl["max"] - lvl["min"], 1) * 100
    return {
        "current": lvl,
        "next": next_lvl,
        "progress": min(100, round(progress, 1)),
        "points_to_next": max(0, next_lvl["min"] - points),
    }


async def check_achievements(user_id: int) -> list[dict]:
    """Yangi yutuqlarni tekshirish"""
    user = await db.get_user(user_id)
    if not user:
        return []

    earned = user.get("achievements", [])
    new_achievements = []
    latest_analysis = await db.get_latest_analysis(user_id)

    for ach in ACHIEVEMENTS:
        if ach["id"] in earned:
            continue

        check = ach["check"]
        unlocked = False

        if "analysis_count" in check:
            threshold = int(check.split(">=")[1].strip())
            if user["analysis_count"] >= threshold:
                unlocked = True

        elif "last_risk" in check and latest_analysis:
            threshold = int(check.split("<")[1].strip())
            if latest_analysis.get("risk_score", 100) < threshold:
                unlocked = True

        elif "streak" in check:
            threshold = int(check.split(">=")[1].strip())
            if user.get("streak", 0) >= threshold:
                unlocked = True

        elif "tasks_done" in check:
            threshold = int(check.split(">=")[1].strip())
            if len(user.get("tasks_done", [])) >= threshold:
                unlocked = True

        elif "chat_count" in check:
            threshold = int(check.split(">=")[1].strip())
            if user.get("chat_count", 0) >= threshold:
                unlocked = True

        elif "has_profit" in check and latest_analysis:
            income = latest_analysis.get("income", 0)
            expense = latest_analysis.get("expense", 0)
            if income > expense:
                unlocked = True

        elif "points" in check:
            threshold = int(check.split(">=")[1].strip())
            if user["points"] >= threshold:
                unlocked = True

        if unlocked:
            success = await db.earn_achievement(user_id, ach["id"], ach["pts"])
            if success:
                new_achievements.append(ach)

    return new_achievements


def format_profile_card(user: dict) -> str:
    """Profil kartasini formatlash"""
    lvl = get_level(user["points"])
    progress = get_level_progress(user["points"])
    bar_len = 20
    filled = int(progress["progress"] / 100 * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)

    earned_achs = [
        ach for ach in ACHIEVEMENTS if ach["id"] in user.get("achievements", [])
    ]
    ach_text = " ".join(ach["icon"] for ach in earned_achs) if earned_achs else "Hali yo'q"

    tasks_done = len(user.get("tasks_done", []))

    return f"""
👤 <b>{user['full_name']}</b>
{user.get('bio', '') or ''}

{lvl['icon']} <b>Seviya:</b> {lvl['name']}
⭐ <b>Ballar:</b> {user['points']}
{bar} {progress['progress']}%
{'→ ' + progress['next']['name'] + 'ga ' + str(progress['points_to_next']) + ' ball qoldi' if progress['points_to_next'] > 0 else '🏆 Maksimal seviya!'}

📊 Tahlillar: {user.get('analysis_count', 0)}
✅ Vazifalar: {tasks_done}
🔥 Streak: {user.get('streak', 1)} kun

🏅 <b>Yutuqlar:</b> {ach_text}
""".strip()


def format_leaderboard(leaders: list, current_user_id: int = None) -> str:
    """Reyting jadvalini formatlash"""
    if not leaders:
        return "📊 Hali reyting mavjud emas. Birinchi bo'ling!"

    medals = ["🥇", "🥈", "🥉"]
    text = "🏆 <b>BIZNES MIYASI REYTING</b>\n" + "━" * 28 + "\n\n"

    for i, leader in enumerate(leaders[:20]):
        medal = medals[i] if i < 3 else f"  {i+1}."
        lvl = get_level(leader["points"])
        is_me = " ← Siz" if leader["user_id"] == current_user_id else ""
        name = leader.get("full_name", "Tadbirkor")[:15]
        biz = leader.get("business_name", "")
        if biz:
            name += f" ({biz[:10]})"

        text += (
            f"{medal} <b>{name}</b>{is_me}\n"
            f"    {lvl['icon']} {lvl['name']} · ⭐ {leader['points']} · "
            f"📊 {leader.get('analysis_count', 0)} tahlil\n\n"
        )

    return text.strip()


def format_tasks(user: dict) -> str:
    """Vazifalar ro'yxatini formatlash"""
    from config import DAILY_TASKS, WEEKLY_TASKS

    done = user.get("tasks_done", [])
    total = len(DAILY_TASKS) + len(WEEKLY_TASKS)
    completed = len([t for t in DAILY_TASKS + WEEKLY_TASKS if t["id"] in done])
    progress = round(completed / max(total, 1) * 100)

    text = f"✅ <b>VAZIFALAR</b> — {completed}/{total} ({progress}%)\n"
    text += "━" * 28 + "\n\n"

    text += "📋 <b>Kunlik vazifalar:</b>\n"
    for t in DAILY_TASKS:
        status = "✅" if t["id"] in done else "⬜"
        pts = f"✓{t['pts']}" if t["id"] in done else f"+{t['pts']}"
        text += f"  {status} {t['icon']} {t['text']} ({pts}⭐)\n"

    text += f"\n📅 <b>Haftalik vazifalar:</b>\n"
    for t in WEEKLY_TASKS:
        status = "✅" if t["id"] in done else "⬜"
        pts = f"✓{t['pts']}" if t["id"] in done else f"+{t['pts']}"
        text += f"  {status} {t['icon']} {t['text']} ({pts}⭐)\n"

    return text.strip()
