import aiosqlite
import logging
from config import DB_PATH

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
async def init_db():
    """Initialize the SQLite database with required tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                full_name   TEXT,
                ton_wallet  TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Transactions table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL,
                stars_amount    INTEGER NOT NULL,
                ton_amount      REAL NOT NULL,
                commission_ton  REAL NOT NULL,
                net_ton         REAL NOT NULL,
                ton_wallet      TEXT NOT NULL,
                ton_price_usd   REAL NOT NULL,
                star_price_usd  REAL NOT NULL,
                status          TEXT DEFAULT 'pending',
                tx_hash         TEXT,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Price cache table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS price_cache (
                id          INTEGER PRIMARY KEY CHECK (id = 1),
                ton_usd     REAL NOT NULL,
                updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Stats table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                id                  INTEGER PRIMARY KEY CHECK (id = 1),
                total_stars         INTEGER DEFAULT 0,
                total_ton_sent      REAL DEFAULT 0,
                total_commission    REAL DEFAULT 0,
                total_transactions  INTEGER DEFAULT 0
            )
        """)
        # Insert default stats row
        await db.execute("""
            INSERT OR IGNORE INTO stats (id) VALUES (1)
        """)

        await db.commit()
    logger.info("✅ Database initialized successfully")


# ─────────────────────────────────────────────────────────────────
async def save_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO users (user_id, username, full_name)
            VALUES (?, ?, ?)
        """, (user_id, username, full_name))
        await db.commit()


async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            return await cursor.fetchone()


async def update_ton_wallet(user_id: int, wallet: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET ton_wallet = ? WHERE user_id = ?",
            (wallet, user_id)
        )
        await db.commit()


# ─────────────────────────────────────────────────────────────────
async def create_transaction(
    user_id: int, stars: int, ton: float, commission: float,
    net_ton: float, wallet: str, ton_price: float, star_price: float
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO transactions
            (user_id, stars_amount, ton_amount, commission_ton, net_ton,
             ton_wallet, ton_price_usd, star_price_usd, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (user_id, stars, ton, commission, net_ton, wallet, ton_price, star_price))
        await db.commit()
        return cursor.lastrowid


async def update_transaction_status(tx_id: int, status: str, tx_hash: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE transactions
            SET status = ?, tx_hash = ?
            WHERE id = ?
        """, (status, tx_hash, tx_id))
        await db.commit()


async def get_user_transactions(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT * FROM transactions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        """, (user_id,)) as cursor:
            return await cursor.fetchall()


# ─────────────────────────────────────────────────────────────────
async def cache_ton_price(price: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO price_cache (id, ton_usd, updated_at)
            VALUES (1, ?, CURRENT_TIMESTAMP)
        """, (price,))
        await db.commit()


async def get_cached_ton_price() -> float | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT ton_usd FROM price_cache WHERE id = 1"
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


# ─────────────────────────────────────────────────────────────────
async def update_stats(stars: int, ton_sent: float, commission: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE stats SET
                total_stars = total_stars + ?,
                total_ton_sent = total_ton_sent + ?,
                total_commission = total_commission + ?,
                total_transactions = total_transactions + 1
            WHERE id = 1
        """, (stars, ton_sent, commission))
        await db.commit()


async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM stats WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "total_stars": row[1],
                    "total_ton_sent": row[2],
                    "total_commission": row[3],
                    "total_transactions": row[4]
                }
    return {}
