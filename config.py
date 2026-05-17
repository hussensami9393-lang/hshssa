import os
from dotenv import load_dotenv

load_dotenv()

# ─── Bot Settings ────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "8728825707:AAHe4Kr-dkCHSYhkfCyOmq0sdm0ZsDQecFs")
ADMIN_ID: int = int(os.getenv("ADMIN_ID", "6721652980"))
BOT_USERNAME: str = os.getenv("BOT_USERNAME", "Star_Ton_sell_Bot")

# ─── TON Settings ────────────────────────────────────────────────
ADMIN_TON_WALLET: str = os.getenv("ADMIN_TON_WALLET", "UQAC6yaR6e4MLGWCBuRW2sLrvSgGPkdKYUnBtyPjrVQNzpdH")
TON_API_KEY: str = os.getenv("TON_API_KEY", "43e16bbb40b73f4ef9a7273a6cd6943e2a7e49413d6215521ca5f0e58fd4f5e4")
TON_API_URL: str = "https://toncenter.com/api/v2"

# ─── Business Settings ───────────────────────────────────────────
MIN_STARS: int = int(os.getenv("MIN_STARS", "50"))
COMMISSION_PERCENT: float = float(os.getenv("COMMISSION_PERCENT", "5"))

# ─── Price Update Interval (seconds) ─────────────────────────────
PRICE_UPDATE_INTERVAL: int = 60  # Update price every 60 seconds

# ─── Telegram Stars Official Rate ────────────────────────────────
# 1 Star = $0.013 USD (Telegram official)
STAR_USD_PRICE: float = 0.0050

# ─── Database ────────────────────────────────────────────────────
DB_PATH: str = "bot_database.db"
