from services.fiat import get_fiat_rates
from services.crypto import get_crypto_prices
from services.stars import get_stars_rate

# Какие монеты поддерживаем
CRYPTO_CCY = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "GRAM": "toncoin",
    "SOL": "solana",
    "BNB": "binancecoin",
}

# Все доступные валюты для конвертера
FIAT_CCY = ["USD", "EUR", "PLN", "UAH", "RUB", "BYN", "GBP", "CHF", "JPY", "CNY"]
ALL_CCY = FIAT_CCY + list(CRYPTO_CCY.keys()) + ["STARS"]


async def get_usd_rate(currency: str) -> float:
    """Сколько USD стоит 1 единица валюты."""
    currency = currency.upper()

    if currency == "USD":
        return 1.0

    if currency == "STARS":
        rate = await get_stars_rate()
        return rate["usd_per_star"]

    if currency in CRYPTO_CCY:
        cid = CRYPTO_CCY[currency]
        data = await get_crypto_prices([cid], "usd")
        return float(data.get(cid, {}).get("usd", 0))

    # Фиат: open.er-api даёт 1 USD = rate[X], нам нужно 1 X = ? USD
    rates = await get_fiat_rates("USD")
    rate = rates.get(currency)
    if not rate:
        return 0.0
    return 1.0 / float(rate)


async def convert(amount: float, frm: str, to: str) -> dict:
    frm = frm.upper()
    to = to.upper()

    if frm not in ALL_CCY:
        return {"error": f"Неизвестная валюта: {frm}"}
    if to not in ALL_CCY:
        return {"error": f"Неизвестная валюта: {to}"}

    usd_from = await get_usd_rate(frm)
    usd_to = await get_usd_rate(to)

    if usd_from <= 0:
        return {"error": f"Курс {frm} недоступен"}
    if usd_to <= 0:
        return {"error": f"Курс {to} недоступен"}

    usd_amount = amount * usd_from
    result = usd_amount / usd_to

    return {
        "from": frm,
        "to": to,
        "amount": amount,
        "result": result,
        "usd_amount": usd_amount,
    }