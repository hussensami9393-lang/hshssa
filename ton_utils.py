import aiohttp
import logging
from config import TON_API_URL, TON_API_KEY, STAR_USD_PRICE

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
async def get_ton_price_usd() -> float:
    """Fetch live TON price in USD from CoinGecko (free, no API key needed)."""
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {"ids": "the-open-network", "vs_currencies": "usd"}
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    price = data["the-open-network"]["usd"]
                    logger.info(f"💰 TON price fetched: ${price}")
                    return float(price)
    except Exception as e:
        logger.error(f"CoinGecko error: {e}")

    # Fallback: try OKX
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://www.okx.com/api/v5/market/ticker?instId=TON-USDT"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    price = float(data["data"][0]["last"])
                    logger.info(f"💰 TON price (OKX fallback): ${price}")
                    return price
    except Exception as e:
        logger.error(f"OKX fallback error: {e}")

    # Final fallback static price
    logger.warning("⚠️ Using static TON price fallback: $5.00")
    return 5.00


# ─────────────────────────────────────────────────────────────────
def calculate_conversion(stars: int, ton_price_usd: float) -> dict:
    """
    Calculate Stars → TON conversion with 5% commission.

    1 Star = $0.013 USD (Telegram official)
    TON amount = (stars * star_price_usd) / ton_price_usd
    Commission = 5% of TON amount
    Net TON to user = TON amount - commission
    """
    star_price_usd = STAR_USD_PRICE
    total_usd = stars * star_price_usd
    total_ton = total_usd / ton_price_usd
    commission_ton = total_ton * 0.05         # 5% commission
    net_ton = total_ton - commission_ton       # User gets 95%

    return {
        "stars": stars,
        "star_price_usd": star_price_usd,
        "total_usd": round(total_usd, 4),
        "ton_price_usd": ton_price_usd,
        "total_ton": round(total_ton, 6),
        "commission_ton": round(commission_ton, 6),
        "commission_percent": 5,
        "net_ton": round(net_ton, 6),
    }


# ─────────────────────────────────────────────────────────────────
async def send_ton(to_wallet: str, amount_ton: float, comment: str = "") -> dict:
    """
    Send TON to a wallet via TonCenter API.
    Returns: {"success": bool, "tx_hash": str, "error": str}

    NOTE: This requires a funded custodial wallet on your server.
    For production, integrate with @wallet bot or TON Connect.
    """
    try:
        headers = {"X-API-Key": TON_API_KEY} if TON_API_KEY else {}
        payload = {
            "to": to_wallet,
            "value": str(int(amount_ton * 1e9)),  # Convert to nanoTON
            "comment": comment or f"Stars→TON conversion | {amount_ton} TON"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{TON_API_URL}/sendBoc",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                data = await resp.json()
                if resp.status == 200 and data.get("ok"):
                    return {"success": True, "tx_hash": data.get("result", ""), "error": None}
                return {"success": False, "tx_hash": None, "error": data.get("error", "Unknown")}
    except Exception as e:
        return {"success": False, "tx_hash": None, "error": str(e)}


# ─────────────────────────────────────────────────────────────────
def validate_ton_wallet(address: str) -> bool:
    """Basic TON wallet address validation."""
    address = address.strip()
    # TON addresses: EQ/UQ format (48 chars) or raw hex
    if address.startswith(("EQ", "UQ")) and len(address) == 48:
        return True
    # Raw format: 0: prefix
    if address.startswith("0:") and len(address) == 66:
        return True
    return False


# ─────────────────────────────────────────────────────────────────
def format_rate_message(ton_price: float, stars_examples: list = None) -> str:
    """Format exchange rate message for display."""
    if stars_examples is None:
        stars_examples = [50, 100, 250, 500, 1000, 2500, 5000]

    lines = [
        "💱 <b>أسعار الصرف الحالية</b>",
        f"",
        f"🔸 سعر TON: <b>${ton_price:.2f}</b>",
        f"⭐ سعر النجمة: <b>${STAR_USD_PRICE}</b>",
        f"💸 العمولة: <b>5%</b>",
        f"",
        "📊 <b>جدول التحويل:</b>",
        "<code>نجوم    →    TON (صافي)</code>",
        "─" * 28,
    ]

    for stars in stars_examples:
        calc = calculate_conversion(stars, ton_price)
        lines.append(f"⭐ <code>{stars:>5}</code>  →  <b>{calc['net_ton']:.4f} TON</b>")

    lines.append("")
    lines.append(f"<i>🔄 يتحدث تلقائياً كل دقيقة</i>")
    return "\n".join(lines)
