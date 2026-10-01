import aiohttp


async def get_crypto_prices(ids: list[str], vs: str = "usd") -> dict:
    """Цены крипты через CoinGecko."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(ids),
        "vs_currencies": vs,
        "include_24hr_change": "true",
    }
    async with aiohttp.ClientSession() as s:
        async with s.get(url, params=params, timeout=10) as r:
            return await r.json()