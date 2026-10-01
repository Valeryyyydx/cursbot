import aiosqlite

DB_PATH = "bot.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                user_id INTEGER,
                currency TEXT,
                PRIMARY KEY (user_id, currency)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                currency TEXT,
                condition TEXT,
                threshold REAL,
                base TEXT DEFAULT 'USD',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS triggered (
                alert_id INTEGER PRIMARY KEY
            )
        """)
        await db.commit()


async def add_watch(user_id: int, currency: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO watchlist(user_id, currency) VALUES(?, ?)",
            (user_id, currency.upper())
        )
        await db.commit()


async def remove_watch(user_id: int, currency: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM watchlist WHERE user_id=? AND currency=?",
            (user_id, currency.upper())
        )
        await db.commit()


async def get_watchlist(user_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT currency FROM watchlist WHERE user_id=?", (user_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [r[0] for r in rows]


async def add_alert(user_id: int, currency: str, condition: str,
                    threshold: float, base: str = "USD") -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO alerts(user_id, currency, condition, threshold, base) "
            "VALUES(?, ?, ?, ?, ?)",
            (user_id, currency.upper(), condition, threshold, base.upper())
        )
        await db.commit()
        return cur.lastrowid


async def get_user_alerts(user_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM alerts WHERE user_id=? ORDER BY id", (user_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def delete_alert(user_id: int, alert_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "DELETE FROM alerts WHERE id=? AND user_id=?",
            (alert_id, user_id)
        )
        await db.commit()
        return cur.rowcount > 0


async def get_all_alerts() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM alerts") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def mark_triggered(alert_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO triggered(alert_id) VALUES(?)", (alert_id,)
        )
        await db.commit()


async def is_triggered(alert_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM triggered WHERE alert_id=?", (alert_id,)
        ) as cur:
            return await cur.fetchone() is not None