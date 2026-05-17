from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


# ─────────────────────────────────────────────────────────────────
def main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="⭐ تحويل النجوم إلى TON"),
        KeyboardButton(text="💱 أسعار الصرف")
    )
    builder.row(
        KeyboardButton(text="👛 محفظتي"),
        KeyboardButton(text="📊 معاملاتي")
    )
    builder.row(
        KeyboardButton(text="ℹ️ كيف يعمل البوت?")
    )
    return builder.as_markup(resize_keyboard=True)


# ─────────────────────────────────────────────────────────────────
def stars_amount_keyboard() -> InlineKeyboardMarkup:
    """Pre-set star amounts for quick selection."""
    builder = InlineKeyboardBuilder()
    amounts = [50, 100, 250, 500, 1000, 2500, 5000]
    for amount in amounts:
        builder.button(text=f"⭐ {amount}", callback_data=f"stars_{amount}")
    builder.button(text="✏️ أدخل عدداً مخصصاً", callback_data="stars_custom")
    builder.adjust(3, 3, 1, 1)
    return builder.as_markup()


# ─────────────────────────────────────────────────────────────────
def confirm_payment_keyboard(stars: int, invoice_link: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"💳 ادفع {stars} ⭐ نجمة الآن",
        url=invoice_link
    )
    builder.button(text="❌ إلغاء", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


# ─────────────────────────────────────────────────────────────────
def wallet_keyboard(has_wallet: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_wallet:
        builder.button(text="✏️ تغيير المحفظة", callback_data="change_wallet")
        builder.button(text="🗑️ حذف المحفظة", callback_data="delete_wallet")
    else:
        builder.button(text="➕ إضافة محفظة TON", callback_data="add_wallet")
    builder.button(text="🔙 رجوع", callback_data="back_main")
    builder.adjust(1)
    return builder.as_markup()


# ─────────────────────────────────────────────────────────────────
def back_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 رجوع للقائمة الرئيسية", callback_data="back_main")
    return builder.as_markup()


# ─────────────────────────────────────────────────────────────────
def admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 الإحصائيات", callback_data="admin_stats")
    builder.button(text="💰 رصيد المحفظة", callback_data="admin_balance")
    builder.button(text="📋 آخر المعاملات", callback_data="admin_txs")
    builder.button(text="📢 رسالة جماعية", callback_data="admin_broadcast")
    builder.adjust(2)
    return builder.as_markup()


# ─────────────────────────────────────────────────────────────────
def generate_payment_link(bot_username: str, stars: int) -> str:
    """Generate a t.me payment link for the bot."""
    return f"https://t.me/{bot_username}?start=pay_{stars}"
