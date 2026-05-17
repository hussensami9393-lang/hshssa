import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    get_user, create_transaction, update_transaction_status,
    get_user_transactions, update_stats, cache_ton_price, get_cached_ton_price
)
from keyboards import (
    stars_amount_keyboard, confirm_payment_keyboard,
    main_menu_keyboard, back_keyboard, generate_payment_link
)
from ton_utils import (
    get_ton_price_usd, calculate_conversion,
    format_rate_message, send_ton
)
from config import MIN_STARS, COMMISSION_PERCENT, ADMIN_TON_WALLET, BOT_USERNAME

logger = logging.getLogger(__name__)
router = Router()


class ConversionStates(StatesGroup):
    waiting_stars_amount = State()
    confirming_payment = State()


# ─────────────────────────────────────────────────────────────────
async def start_conversion_with_stars(message: Message, state: FSMContext, stars: int):
    """Called when user uses deep link pay_XXX"""
    user = await get_user(message.from_user.id)
    if not user or not user[3]:
        await state.set_state(ConversionStates.waiting_stars_amount)
        await message.answer(
            "⚠️ <b>يجب إضافة محفظة TON أولاً!</b>\n\n"
            "اضغط على 👛 <b>محفظتي</b> من القائمة لإضافة محفظتك",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )
        return
    await process_stars_amount(message, state, stars)


# ─────────────────────────────────────────────────────────────────
@router.message(F.text == "⭐ تحويل النجوم إلى TON")
async def convert_stars(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)

    if not user or not user[3]:
        await message.answer(
            "⚠️ <b>يجب إضافة محفظة TON أولاً!</b>\n\n"
            "اذهب إلى 👛 <b>محفظتي</b> وأضف عنوان محفظتك، ثم ارجع وحوّل نجومك.",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )
        return

    # Get live TON price
    ton_price = await get_ton_price_usd()
    await cache_ton_price(ton_price)

    calc_50   = calculate_conversion(50,   ton_price)
    calc_100  = calculate_conversion(100,  ton_price)
    calc_500  = calculate_conversion(500,  ton_price)
    calc_1000 = calculate_conversion(1000, ton_price)

    wallet = user[3]
    short_wallet = f"{wallet[:6]}...{wallet[-4:]}"

    text = (
        f"⭐ <b>تحويل النجوم إلى TON</b>\n\n"
        f"💎 سعر TON الحالي: <b>${ton_price:.2f}</b>\n"
        f"⭐ سعر النجمة: <b>$0.013</b>\n"
        f"💸 العمولة: <b>5%</b>\n"
        f"👛 محفظتك: <code>{short_wallet}</code>\n\n"
        f"📊 <b>أمثلة:</b>\n"
        f"• 50 ⭐ = <b>{calc_50['net_ton']} TON</b>\n"
        f"• 100 ⭐ = <b>{calc_100['net_ton']} TON</b>\n"
        f"• 500 ⭐ = <b>{calc_500['net_ton']} TON</b>\n"
        f"• 1000 ⭐ = <b>{calc_1000['net_ton']} TON</b>\n\n"
        f"👇 <b>اختر عدد النجوم:</b>"
    )

    await message.answer(text, reply_markup=stars_amount_keyboard(), parse_mode="HTML")
    await state.set_state(ConversionStates.waiting_stars_amount)


# ─────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("stars_"), ConversionStates.waiting_stars_amount)
async def handle_stars_selection(callback: CallbackQuery, state: FSMContext):
    data = callback.data

    if data == "stars_custom":
        await callback.message.answer(
            f"✏️ <b>أدخل عدد النجوم يدوياً:</b>\n\n"
            f"الحد الأدنى: <b>{MIN_STARS} نجمة</b>",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return

    stars = int(data.replace("stars_", ""))
    await process_stars_amount(callback.message, state, stars, callback.from_user.id)
    await callback.answer()


# ─────────────────────────────────────────────────────────────────
@router.message(ConversionStates.waiting_stars_amount, F.text.regexp(r'^\d+$'))
async def handle_custom_stars(message: Message, state: FSMContext):
    stars = int(message.text)
    if stars < MIN_STARS:
        await message.answer(
            f"❌ الحد الأدنى هو <b>{MIN_STARS} نجمة</b>، أدخل عدداً أكبر.",
            parse_mode="HTML"
        )
        return
    await process_stars_amount(message, state, stars)


# ─────────────────────────────────────────────────────────────────
async def process_stars_amount(message: Message, state: FSMContext,
                                stars: int, user_id: int = None):
    uid = user_id or message.from_user.id
    user = await get_user(uid)

    if not user or not user[3]:
        await message.answer(
            "⚠️ أضف محفظة TON أولاً من قائمة 👛 <b>محفظتي</b>",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )
        await state.clear()
        return

    ton_price = await get_ton_price_usd()
    await cache_ton_price(ton_price)
    calc = calculate_conversion(stars, ton_price)
    wallet = user[3]
    short_wallet = f"{wallet[:6]}...{wallet[-4:]}"

    # Save to FSM
    await state.update_data(
        stars=stars,
        ton_price=ton_price,
        calc=calc,
        wallet=wallet,
        user_id=uid
    )
    await state.set_state(ConversionStates.confirming_payment)

    # Generate invoice link
    invoice_link = generate_payment_link(BOT_USERNAME, stars)

    text = (
        f"📋 <b>تفاصيل التحويل</b>\n"
        f"{'─' * 30}\n"
        f"⭐ النجوم: <b>{stars}</b>\n"
        f"💰 القيمة: <b>${calc['total_usd']:.3f}</b>\n"
        f"💎 إجمالي TON: <b>{calc['total_ton']} TON</b>\n"
        f"💸 العمولة (5%): <b>{calc['commission_ton']} TON</b>\n"
        f"✅ ستستلم: <b>{calc['net_ton']} TON</b>\n"
        f"👛 إلى: <code>{short_wallet}</code>\n"
        f"{'─' * 30}\n\n"
        f"💳 <b>اضغط الزر أدناه لإتمام الدفع بالنجوم:</b>"
    )

    await message.answer(
        text,
        reply_markup=confirm_payment_keyboard(stars, invoice_link),
        parse_mode="HTML"
    )


# ─────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "cancel")
async def cancel_conversion(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "❌ تم الإلغاء.",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────────
#  TELEGRAM STARS PAYMENT HANDLERS
# ─────────────────────────────────────────────────────────────────

@router.message(F.text == "💱 أسعار الصرف")
async def show_rates(message: Message):
    ton_price = await get_ton_price_usd()
    await cache_ton_price(ton_price)
    text = format_rate_message(ton_price)
    await message.answer(text, parse_mode="HTML")


# ─────────────────────────────────────────────────────────────────
@router.message(F.text == "📊 معاملاتي")
async def my_transactions(message: Message):
    txs = await get_user_transactions(message.from_user.id)
    if not txs:
        await message.answer(
            "📭 <b>لا توجد معاملات بعد</b>\n\nابدأ بتحويل نجومك الآن! ⭐",
            parse_mode="HTML"
        )
        return

    text = "📊 <b>آخر معاملاتك:</b>\n\n"
    status_emoji = {"pending": "⏳", "completed": "✅", "failed": "❌"}

    for tx in txs:
        # tx columns: id,user_id,stars,ton,commission,net_ton,wallet,ton_price,star_price,status,tx_hash,created_at
        emoji = status_emoji.get(tx[9], "❓")
        short_wallet = f"{tx[6][:6]}...{tx[6][-4:]}"
        text += (
            f"{emoji} <b>#{tx[0]}</b> | {tx[11][:10]}\n"
            f"   ⭐ {tx[2]} نجمة → 💎 {tx[5]} TON\n"
            f"   👛 {short_wallet}\n\n"
        )

    await message.answer(text, parse_mode="HTML")


# ─────────────────────────────────────────────────────────────────
#  ACTUAL STARS INVOICE (sent by bot to user)
# ─────────────────────────────────────────────────────────────────
async def send_stars_invoice(bot, chat_id: int, stars: int, ton_price: float, calc: dict):
    """Send a Telegram Stars invoice to collect payment."""
    description = (
        f"تحويل {stars} نجمة إلى TON\n"
        f"ستستلم: {calc['net_ton']} TON\n"
        f"بعد عمولة 5% ({calc['commission_ton']} TON)"
    )
    prices = [LabeledPrice(label=f"⭐ {stars} نجمة → 💎 TON", amount=stars)]

    await bot.send_invoice(
        chat_id=chat_id,
        title=f"تحويل {stars} ⭐ إلى TON 💎",
        description=description,
        payload=f"stars_to_ton_{stars}_{chat_id}",
        currency="XTR",  # Telegram Stars currency code
        prices=prices,
    )


# ─────────────────────────────────────────────────────────────────
#  PRE-CHECKOUT (must answer within 10 seconds)
# ─────────────────────────────────────────────────────────────────
@router.pre_checkout_query()
async def pre_checkout(pre_checkout_q: PreCheckoutQuery):
    """Approve all pre-checkout queries."""
    await pre_checkout_q.answer(ok=True)


# ─────────────────────────────────────────────────────────────────
#  SUCCESSFUL PAYMENT → SELL STARS → SEND TON
# ─────────────────────────────────────────────────────────────────
@router.message(F.successful_payment)
async def successful_payment_handler(message: Message, state: FSMContext):
    """
    Triggered when user pays with Stars.
    Flow:
      1. Receive Stars from user
      2. Bot sells Stars → gets TON equivalent
      3. Deduct 5% commission → send to ADMIN_TON_WALLET
      4. Send remaining 95% TON → user's wallet
      5. Log transaction
    """
    payment = message.successful_payment
    stars_received = payment.total_amount  # in Stars (XTR)
    payload = payment.invoice_payload      # "stars_to_ton_{stars}_{chat_id}"

    user = await get_user(message.from_user.id)
    user_wallet = user[3] if user else None

    if not user_wallet:
        await message.answer(
            "⚠️ <b>لم نجد محفظتك!</b>\nيرجى إضافة محفظة TON من قسم 👛 محفظتي",
            parse_mode="HTML"
        )
        return

    # Get latest TON price
    ton_price = await get_ton_price_usd()
    calc = calculate_conversion(stars_received, ton_price)

    # Create pending transaction record
    tx_id = await create_transaction(
        user_id=message.from_user.id,
        stars=stars_received,
        ton=calc["total_ton"],
        commission=calc["commission_ton"],
        net_ton=calc["net_ton"],
        wallet=user_wallet,
        ton_price=ton_price,
        star_price=calc["star_price_usd"]
    )

    await message.answer(
        f"✅ <b>تم استلام {stars_received} ⭐ نجمة!</b>\n\n"
        f"⏳ جارٍ بيع النجوم وإرسال TON لمحفظتك...\n"
        f"💎 ستستلم: <b>{calc['net_ton']} TON</b>",
        parse_mode="HTML"
    )

    # ── Step 1: Send commission (5%) to admin wallet ──────────────
    commission_result = await send_ton(
        to_wallet=ADMIN_TON_WALLET,
        amount_ton=calc["commission_ton"],
        comment=f"Commission tx#{tx_id} | {stars_received} stars"
    )

    # ── Step 2: Send net TON (95%) to user wallet ─────────────────
    user_result = await send_ton(
        to_wallet=user_wallet,
        amount_ton=calc["net_ton"],
        comment=f"Stars→TON tx#{tx_id} | {stars_received}⭐ → {calc['net_ton']}TON"
    )

    if user_result["success"]:
        await update_transaction_status(tx_id, "completed", user_result["tx_hash"])
        await update_stats(stars_received, calc["net_ton"], calc["commission_ton"])

        short_wallet = f"{user_wallet[:6]}...{user_wallet[-4:]}"
        await message.answer(
            f"🎉 <b>تم التحويل بنجاح!</b>\n\n"
            f"{'─' * 30}\n"
            f"⭐ النجوم المُباعة: <b>{stars_received}</b>\n"
            f"💎 TON المُرسل: <b>{calc['net_ton']} TON</b>\n"
            f"💸 العمولة: <b>{calc['commission_ton']} TON</b>\n"
            f"👛 إلى: <code>{short_wallet}</code>\n"
            f"{'─' * 30}\n"
            f"🔍 رقم المعاملة: <code>#{tx_id}</code>\n\n"
            f"شكراً لاستخدامك البوت! ⭐",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )
        logger.info(f"✅ TX#{tx_id}: {stars_received}⭐ → {calc['net_ton']} TON → {user_wallet}")
    else:
        await update_transaction_status(tx_id, "failed")
        await message.answer(
            f"❌ <b>حدث خطأ أثناء الإرسال!</b>\n\n"
            f"رقم المعاملة: <code>#{tx_id}</code>\n"
            f"يرجى التواصل مع الدعم وذكر رقم المعاملة.",
            parse_mode="HTML"
        )
        logger.error(f"❌ TX#{tx_id} failed: {user_result['error']}")
