import aiohttp
import time

_cache = {}
CACHE_TTL = 300  # 5 минут

# Telegram продаёт примерно 150 Stars за 1 Gram
STARS_PER_GRAM = 150

# Справочный курс на случай, если API недоступны
DEFAULT_USD_PER_STAR = 0.013


async def get_gram_usd() -> float:
    """Цена Gram (ex-TON) в USD через CoinGecko."""
    key = "gram_usd"
    now = time.time()
    if key in _cache and now - _cache[key]["t"] < CACHE_TTL:
        return _cache[key]["v"]

    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "the-open-network", "vs_currencies": "usd"}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, params=params, timeout=10) as r:
                data = await r.json()
                price = data.get("the-open-network", {}).get("usd", 0)
                if price > 0:
                    _cache[key] = {"t": now, "v": price}
                    return price
    except Exception as e:
        print(f"CoinGecko error: {e}")
    return 0.0


async def get_stars_rate() -> dict:
    """Считает курс Stars через цену Gram."""
    gram_usd = await get_gram_usd()

    if gram_usd <= 0:
        return {
            "usd_per_star": DEFAULT_USD_PER_STAR,
            "usd_per_gram": None,
            "gram_per_star": None,
            "source": "fallback",
        }

    gram_per_star = 1 / STARS_PER_GRAM
    usd_per_star = gram_per_star * gram_usd

    return {
        "usd_per_star": round(usd_per_star, 5),
        "usd_per_gram": round(gram_usd, 4),
        "gram_per_star": round(gram_per_star, 6),
        "source": "Gram × 150 Stars",
    }