"""
╔══════════════════════════════════════════╗
║   Stars → TON Bot  |  Main Entry Point   ║
║   By: Stars TON Bot Team                 ║
╚══════════════════════════════════════════╝

Flow:
  User pays Stars
    → Bot receives Stars (sold automatically by Telegram)
    → Bot gets equivalent XTR value
    → Calculates TON equivalent at live price
    → Deducts 5% commission → sends to admin wallet
    → Sends 95% TON → user's wallet
    → Logs transaction in SQLite
"""

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, PRICE_UPDATE_INTERVAL
from database import init_db, cache_ton_price
from ton_utils import get_ton_price_usd

# Import handlers
from handlers.start import router as start_router
from handlers.wallet import router as wallet_router
from handlers.conversion import router as conversion_router
from handlers.admin import router as admin_router

# ─── Logging ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
async def price_updater():
    """Background task: update TON price every 60 seconds."""
    while True:
        try:
            price = await get_ton_price_usd()
            await cache_ton_price(price)
            logger.info(f"💰 TON price updated: ${price:.2f}")
        except Exception as e:
            logger.error(f"Price update error: {e}")
        await asyncio.sleep(PRICE_UPDATE_INTERVAL)


# ─────────────────────────────────────────────────────────────────
async def on_startup(bot: Bot):
    """Called when bot starts."""
    logger.info("🚀 Bot starting...")
    await init_db()

    # Initial price fetch
    price = await get_ton_price_usd()
    await cache_ton_price(price)
    logger.info(f"💰 Initial TON price: ${price:.2f}")

    me = await bot.get_me()
    logger.info(f"✅ Bot started: @{me.username} ({me.full_name})")
    logger.info(f"🔗 Payment link format: https://t.me/{me.username}?start=pay_{{stars}}")

    # Notify admin
    from config import ADMIN_ID
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🟢 <b>البوت يعمل الآن!</b>\n\n"
            f"🤖 @{me.username}\n"
            f"💰 سعر TON: <b>${price:.2f}</b>\n\n"
            f"اضغط /admin للوحة الإدارة",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Could not notify admin: {e}")


# ─────────────────────────────────────────────────────────────────
async def on_shutdown(bot: Bot):
    """Called when bot stops."""
    logger.info("🔴 Bot shutting down...")
    from config import ADMIN_ID
    try:
        await bot.send_message(ADMIN_ID, "🔴 <b>البوت توقف!</b>", parse_mode="HTML")
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────
async def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ BOT_TOKEN not set! Copy .env.example to .env and fill values.")
        sys.exit(1)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()

    # Register routers (order matters)
    dp.include_router(start_router)
    dp.include_router(wallet_router)
    dp.include_router(conversion_router)
    dp.include_router(admin_router)

    # Startup/shutdown hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Start background price updater
    asyncio.create_task(price_updater())

    logger.info("📡 Starting polling...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(main())
