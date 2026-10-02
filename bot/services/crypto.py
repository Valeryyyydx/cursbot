import aiohttp


async def get_crypto_prices(ids: list, vs: str = "usd") -> dict:
    """Цены крипты через CoinGecko. Устойчиво к ошибкам."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(ids),
        "vs_currencies": vs,
        "include_24hr_change": "true",
    }
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, params=params, timeout=10) as r:
                if r.status != 200:
                    print(f"CoinGecko status: {r.status}")
                    return {}
                data = await r.json()
                if not isinstance(data, dict):
                    print(f"CoinGecko bad response: {data}")
                    return {}
                return data
    except Exception as e:
        print(f"CoinGecko error: {e}")
        return {}
