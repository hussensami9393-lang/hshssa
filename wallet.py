from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_user, update_ton_wallet
from keyboards import wallet_keyboard, main_menu_keyboard, back_keyboard
from ton_utils import validate_ton_wallet

router = Router()


class WalletStates(StatesGroup):
    waiting_wallet = State()


# ─────────────────────────────────────────────────────────────────
@router.message(F.text == "👛 محفظتي")
async def my_wallet(message: Message):
    user = await get_user(message.from_user.id)
    if user and user[3]:  # ton_wallet column
        wallet = user[3]
        text = (
            f"👛 <b>محفظتك الحالية:</b>\n\n"
            f"<code>{wallet}</code>\n\n"
            f"✅ ستُرسل جميع التحويلات إلى هذه المحفظة"
        )
    else:
        text = (
            "👛 <b>لم تُضف محفظة TON بعد</b>\n\n"
            "أضف محفظتك لاستقبال التحويلات 👇"
        )

    await message.answer(
        text,
        reply_markup=wallet_keyboard(bool(user and user[3])),
        parse_mode="HTML"
    )


# ─────────────────────────────────────────────────────────────────
@router.callback_query(F.data.in_({"add_wallet", "change_wallet"}))
async def ask_for_wallet(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WalletStates.waiting_wallet)
    await callback.message.answer(
        "📝 <b>أرسل عنوان محفظة TON الخاصة بك:</b>\n\n"
        "مثال: <code>EQxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx</code>\n\n"
        "⚠️ تأكد من صحة العنوان، لا يمكن التراجع عن التحويل!",
        parse_mode="HTML",
        reply_markup=back_keyboard()
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────────
@router.message(WalletStates.waiting_wallet)
async def save_wallet(message: Message, state: FSMContext):
    address = message.text.strip()

    if not validate_ton_wallet(address):
        await message.answer(
            "❌ <b>عنوان المحفظة غير صحيح!</b>\n\n"
            "يجب أن يبدأ بـ <code>EQ</code> أو <code>UQ</code> ويتكون من 48 حرفاً\n\n"
            "حاول مرة أخرى 👇",
            parse_mode="HTML"
        )
        return

    await update_ton_wallet(message.from_user.id, address)
    await state.clear()

    await message.answer(
        f"✅ <b>تم حفظ محفظتك بنجاح!</b>\n\n"
        f"<code>{address}</code>\n\n"
        f"🎉 يمكنك الآن تحويل النجوم إلى TON",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )


# ─────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "delete_wallet")
async def delete_wallet(callback: CallbackQuery):
    await update_ton_wallet(callback.from_user.id, None)
    await callback.message.answer(
        "🗑️ <b>تم حذف المحفظة</b>\n\nيمكنك إضافة محفظة جديدة في أي وقت.",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
