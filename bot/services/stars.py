import aiohttp
import time

# Простой кэш, чтобы не спамить CoinGecko
_cache = {}
CACHE_TTL = 300  # 5 минут

# Фиксированное соотношение на Fragment: ~150 Stars за 1 TON
# (обновляй вручную раз в 1-2 недели, оно медленно меняется)
STARS_PER_TON = 150

# Справочный курс Telegram, если CoinGecko недоступен
DEFAULT_USD_PER_STAR = 0.013


async def get_ton_usd() -> float:
    """Текущая цена TON в USD через CoinGecko."""
    key = "ton_usd"
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
    """
    Возвращает оценку курса Telegram Stars.
    Поля:
      usd_per_star  — рыночная оценка через Fragment + TON
      ton_per_star  — фикс с Fragment
      ton_usd       — цена TON
      source        — откуда данные
    """
    ton_usd = await get_ton_usd()
    if ton_usd <= 0:
        return {
            "usd_per_star": DEFAULT_USD_PER_STAR,
            "ton_per_star": None,
            "ton_usd": None,
            "source": "telegram_reference",
        }

    ton_per_star = 1.0 / STARS_PER_TON
    usd_per_star = ton_per_star * ton_usd

    return {
        "usd_per_star": round(usd_per_star, 5),
        "ton_per_star": round(ton_per_star, 6),
        "ton_usd": round(ton_usd, 4),
        "source": "fragment_arbitrage",
    }