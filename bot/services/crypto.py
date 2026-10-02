import aiohttp
import json


async def get_crypto_prices(ids: list, vs: str = "usd") -> dict:
    mapping = {
        "bitcoin": "BTCUSDT",
        "ethereum": "ETHUSDT",
        "the-open-network": "TONUSDT",
        "solana": "SOLUSDT",
        "binancecoin": "BNBUSDT",
    }

    symbols = [mapping[i] for i in ids if i in mapping]
    if not symbols:
        return {}

    url = "https://api.binance.com/api/v3/ticker/24hr"
    params = {"symbols": json.dumps(symbols)}

    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, params=params, timeout=10) as r:
                if r.status != 200:
                    print(f"Binance status: {r.status}")
                    return {}
                data = await r.json()
    except Exception as e:
        print(f"Binance error: {e}")
        return {}

    result = {}
    for item in data:
        sym = item.get("symbol", "")
        for cid, s in mapping.items():
            if s == sym:
                result[cid] = {
                    "usd": float(item.get("lastPrice", 0)),
                    "usd_24h_change": float(item.get("priceChangePercent", 0)),
                }
                break
    return result
