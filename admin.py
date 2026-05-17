import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command

from database import get_stats, get_user_transactions
from keyboards import admin_keyboard
from ton_utils import get_ton_price_usd
from config import ADMIN_ID

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ─────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ ممنوع", show_alert=True)
        return

    stats = await get_stats()
    ton_price = await get_ton_price_usd()
    commission_usd = stats.get("total_commission", 0) * ton_price

    text = (
        f"📊 <b>إحصائيات البوت</b>\n"
        f"{'─' * 30}\n"
        f"📦 إجمالي المعاملات: <b>{stats.get('total_transactions', 0)}</b>\n"
        f"⭐ إجمالي النجوم: <b>{stats.get('total_stars', 0)}</b>\n"
        f"💎 TON المُرسل للمستخدمين: <b>{stats.get('total_ton_sent', 0):.4f}</b>\n"
        f"💰 إجمالي العمولات: <b>{stats.get('total_commission', 0):.4f} TON</b>\n"
        f"💵 العمولة بالدولار: <b>${commission_usd:.2f}</b>\n"
        f"{'─' * 30}\n"
        f"💹 سعر TON الحالي: <b>${ton_price:.2f}</b>"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_keyboard())
    await callback.answer()


# ─────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin_txs")
async def admin_transactions(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ ممنوع", show_alert=True)
        return

    import aiosqlite
    from config import DB_PATH

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT t.id, u.full_name, t.stars_amount, t.net_ton, t.status, t.created_at
            FROM transactions t
            JOIN users u ON t.user_id = u.user_id
            ORDER BY t.created_at DESC LIMIT 10
        """) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        await callback.message.edit_text(
            "📭 لا توجد معاملات بعد",
            reply_markup=admin_keyboard()
        )
        await callback.answer()
        return

    status_emoji = {"pending": "⏳", "completed": "✅", "failed": "❌"}
    text = "📋 <b>آخر 10 معاملات:</b>\n\n"
    for row in rows:
        emoji = status_emoji.get(row[4], "❓")
        text += (
            f"{emoji} <b>#{row[0]}</b> | {row[5][:10]}\n"
            f"   👤 {row[1]} | ⭐{row[2]} → 💎{row[3]} TON\n\n"
        )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_keyboard())
    await callback.answer()


# ─────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_prompt(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ ممنوع", show_alert=True)
        return
    await callback.message.answer(
        "📢 أرسل الرسالة التي تريد بثها لجميع المستخدمين:\n"
        "(أرسل /cancel للإلغاء)"
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────────
@router.message(Command("broadcast"))
async def broadcast_command(message: Message):
    if not is_admin(message.from_user.id):
        return

    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("⚠️ أرسل: /broadcast <الرسالة>")
        return

    import aiosqlite
    from config import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            users = await cursor.fetchall()

    sent = 0
    failed = 0
    for (uid,) in users:
        try:
            await message.bot.send_message(uid, text)
            sent += 1
        except Exception:
            failed += 1

    await message.answer(f"📢 تم الإرسال: ✅{sent} | ❌{failed}")
