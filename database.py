"""
Biznes Miyasi Bot — Database (SQLite + aiosqlite)
PostgreSQL ga o'tish oson — SQL standart
"""
import aiosqlite
import json
from datetime import datetime, date
from config import DATABASE_PATH


async def init_db():
    """Database yaratish va migratsiya"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT NOT NULL,
                business_name TEXT DEFAULT '',
                sector TEXT DEFAULT 'boshqa',
                bio TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                points INTEGER DEFAULT 0,
                level_id INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 1,
                analysis_count INTEGER DEFAULT 0,
                chat_count INTEGER DEFAULT 0,
                tasks_done TEXT DEFAULT '[]',
                achievements TEXT DEFAULT '[]',
                premium_tier TEXT DEFAULT 'free',
                last_active DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                photo_id TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                amount REAL NOT NULL,
                category TEXT DEFAULT 'umumiy',
                description TEXT DEFAULT '',
                source TEXT DEFAULT 'manual',
                date DATE DEFAULT (date('now')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                business_name TEXT,
                sector TEXT,
                income REAL,
                expense REAL,
                employees INTEGER DEFAULT 1,
                period TEXT DEFAULT 'orta',
                problem TEXT DEFAULT '',
                risk_score INTEGER DEFAULT 0,
                profit_margin REAL DEFAULT 0,
                waste_estimate REAL DEFAULT 0,
                savings_potential REAL DEFAULT 0,
                ai_response TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                details TEXT DEFAULT '',
                points_earned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
            CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(user_id, date);
            CREATE INDEX IF NOT EXISTS idx_analyses_user ON analyses(user_id);
            CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_log(user_id);
        """)
        await db.commit()


# ═══════════════════════════════════════════════
# USER OPERATIONS
# ═══════════════════════════════════════════════

async def get_user(user_id: int) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            d = dict(row)
            d["tasks_done"] = json.loads(d["tasks_done"])
            d["achievements"] = json.loads(d["achievements"])
            return d
        return None


async def create_user(user_id: int, full_name: str, username: str = "") -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT OR IGNORE INTO users (user_id, full_name, username, last_active)
               VALUES (?, ?, ?, ?)""",
            (user_id, full_name, username, date.today().isoformat()),
        )
        await db.commit()
    return await get_user(user_id)


async def update_user(user_id: int, **kwargs):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for key, value in kwargs.items():
            if key in ("tasks_done", "achievements"):
                value = json.dumps(value, ensure_ascii=False)
            await db.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))
        await db.execute(
            "UPDATE users SET last_active = ? WHERE user_id = ?",
            (date.today().isoformat(), user_id),
        )
        await db.commit()


async def add_points(user_id: int, pts: int, reason: str = ""):
    user = await get_user(user_id)
    if not user:
        return
    new_pts = user["points"] + pts
    # Level hisoblash
    from config import LEVELS
    new_level = 0
    for lvl in LEVELS:
        if new_pts >= lvl["min"]:
            new_level = lvl["id"]
    await update_user(user_id, points=new_pts, level_id=new_level)
    if reason:
        await log_activity(user_id, reason, points_earned=pts)


async def complete_task(user_id: int, task_id: str, pts: int) -> bool:
    user = await get_user(user_id)
    if not user:
        return False
    tasks = user["tasks_done"]
    if task_id in tasks:
        return False
    tasks.append(task_id)
    await update_user(user_id, tasks_done=tasks)
    await add_points(user_id, pts, f"Vazifa: {task_id}")
    return True


async def earn_achievement(user_id: int, ach_id: str, pts: int) -> bool:
    user = await get_user(user_id)
    if not user:
        return False
    achs = user["achievements"]
    if ach_id in achs:
        return False
    achs.append(ach_id)
    await update_user(user_id, achievements=achs)
    await add_points(user_id, pts, f"Yutuq: {ach_id}")
    return True


# ═══════════════════════════════════════════════
# TRANSACTION OPERATIONS
# ═══════════════════════════════════════════════

async def add_transaction(user_id: int, tx_type: str, amount: float,
                          category: str = "umumiy", description: str = "",
                          source: str = "manual", tx_date: str = None) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO transactions (user_id, type, amount, category, description, source, date)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, tx_type, amount, category, description, source,
             tx_date or date.today().isoformat()),
        )
        await db.commit()
        return cursor.lastrowid


async def get_transactions(user_id: int, days: int = 30) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT * FROM transactions WHERE user_id = ?
               AND date >= date('now', ? || ' days')
               ORDER BY date DESC""",
            (user_id, f"-{days}"),
        )
        return [dict(row) for row in await cursor.fetchall()]


async def get_financial_summary(user_id: int, days: int = 30) -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """SELECT type, SUM(amount) as total, COUNT(*) as count
               FROM transactions WHERE user_id = ?
               AND date >= date('now', ? || ' days')
               GROUP BY type""",
            (user_id, f"-{days}"),
        )
        rows = await cursor.fetchall()
        summary = {"income": 0, "expense": 0, "income_count": 0, "expense_count": 0}
        for row in rows:
            summary[row[0]] = row[1] or 0
            summary[f"{row[0]}_count"] = row[2] or 0
        summary["profit"] = summary["income"] - summary["expense"]
        summary["margin"] = (
            round(summary["profit"] / summary["income"] * 100, 1)
            if summary["income"] > 0
            else 0
        )
        return summary

    
async def get_category_breakdown(user_id: int, tx_type: str = "expense", days: int = 30) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT category, SUM(amount) as total, COUNT(*) as count
               FROM transactions WHERE user_id = ? AND type = ?
               AND date >= date('now', ? || ' days')
               GROUP BY category ORDER BY total DESC""",
            (user_id, tx_type, f"-{days}"),
        )
        return [dict(row) for row in await cursor.fetchall()]


# ═══════════════════════════════════════════════
# ANALYSIS OPERATIONS
# ═══════════════════════════════════════════════

async def save_analysis(user_id: int, data: dict) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO analyses
               (user_id, business_name, sector, income, expense, employees,
                period, problem, risk_score, profit_margin, waste_estimate,
                savings_potential, ai_response)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                data.get("business_name", ""),
                data.get("sector", "boshqa"),
                data.get("income", 0),
                data.get("expense", 0),
                data.get("employees", 1),
                data.get("period", "orta"),
                data.get("problem", ""),
                data.get("risk_score", 0),
                data.get("profit_margin", 0),
                data.get("waste_estimate", 0),
                data.get("savings_potential", 0),
                data.get("ai_response", ""),
            ),
        )
        await db.commit()
        # Update user analysis count
        user = await get_user(user_id)
        if user:
            await update_user(user_id, analysis_count=user["analysis_count"] + 1)
        return cursor.lastrowid


async def get_latest_analysis(user_id: int) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_analysis_history(user_id: int, limit: int = 10) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )
        return [dict(row) for row in await cursor.fetchall()]


# ═══════════════════════════════════════════════
# ACTIVITY LOG
# ═══════════════════════════════════════════════

async def log_activity(user_id: int, action: str, details: str = "", points_earned: int = 0):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO activity_log (user_id, action, details, points_earned) VALUES (?, ?, ?, ?)",
            (user_id, action, details, points_earned),
        )
        await db.commit()


async def get_leaderboard(limit: int = 20) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT user_id, full_name, business_name, points, level_id, analysis_count
               FROM users ORDER BY points DESC LIMIT ?""",
            (limit,),
        )
        return [dict(row) for row in await cursor.fetchall()]


async def get_stats() -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        total_users = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM analyses")
        total_analyses = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM transactions")
        total_tx = (await cursor.fetchone())[0]
        return {
            "total_users": total_users,
            "total_analyses": total_analyses,
            "total_transactions": total_tx,
        }
