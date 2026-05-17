from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from database import save_user, get_user
from keyboards import main_menu_keyboard, admin_keyboard
from ton_utils import get_ton_price_usd, format_rate_message
from config import ADMIN_ID, BOT_USERNAME

router = Router()

# ─────────────────────────────────────────────────────────────────
WELCOME_TEXT = """
🌟 <b>أهلاً بك في بوت تحويل النجوم إلى TON!</b>

أنا بوت متخصص في تحويل <b>نجوم تيليجرام ⭐</b> إلى عملة <b>TON 💎</b> بشكل فوري وآمن.

<b>كيف يعمل البوت؟</b>
1️⃣ تختار عدد النجوم التي تريد تحويلها
2️⃣ تضغط على رابط الدفع وتدفع بالنجوم
3️⃣ البوت يبيع النجوم ويحول TON مباشرة لمحفظتك
4️⃣ نأخذ عمولة <b>5%</b> فقط مقابل الخدمة

<b>الأسعار تتحدث تلقائياً كل دقيقة! 🔄</b>

اضغط على أي زر من القائمة للبدء 👇
"""

# ─────────────────────────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    await save_user(user.id, user.username or "", user.full_name or "")

    # Check if started with pay_ deep link
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("pay_"):
        try:
            stars = int(args[1].replace("pay_", ""))
            from handlers.conversion import start_conversion_with_stars
            await start_conversion_with_stars(message, state, stars)
            return
        except ValueError:
            pass

    await message.answer(
        WELCOME_TEXT,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )


# ─────────────────────────────────────────────────────────────────
@router.message(F.text == "ℹ️ كيف يعمل البوت?")
async def how_it_works(message: Message):
    text = """
📖 <b>كيف يعمل بوت Stars → TON</b>

<b>🔄 آلية العمل:</b>
┌─────────────────────────────
│ 1. تختار عدد النجوم
│ 2. تدفع عبر رابط الدفع
│ 3. البوت يستلم النجوم
│ 4. البوت يبيع النجوم → USD
│ 5. يشتري TON بالـ USD
│ 6. يخصم 5% عمولة
│ 7. يرسل TON لمحفظتك فوراً
└─────────────────────────────

<b>💰 الأسعار:</b>
• سعر النجمة: <b>$0.013</b> (رسمي من تيليجرام)
• العمولة: <b>5%</b> من قيمة TON
• سعر TON: يتحدث <b>تلقائياً</b> كل دقيقة

<b>⚡ السرعة:</b>
• التحويل يتم خلال <b>1-3 دقائق</b> بعد الدفع

<b>🔒 الأمان:</b>
• معاملات موثقة وشفافة
• يمكن التحقق من كل معاملة على TON Explorer

<b>📞 الدعم:</b> تواصل مع الأدمن عند أي مشكلة
"""
    await message.answer(text, parse_mode="HTML")


# ─────────────────────────────────────────────────────────────────
@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ ليس لديك صلاحية الوصول")
        return
    await message.answer(
        "🔧 <b>لوحة الإدارة</b>\nاختر ما تريد:",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )


# ─────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "🏠 القائمة الرئيسية",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()
