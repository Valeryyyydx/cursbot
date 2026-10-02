import aiohttp


async def get_crypto_prices(ids: list, vs: str = "usd") -> dict:
    """Цены крипты через CoinCap. Работает из США."""
    mapping = {
        "bitcoin": "bitcoin",
        "ethereum": "ethereum",
        "the-open-network": "toncoin",
        "solana": "solana",
        "binancecoin": "binance-coin",
    }

    coin_ids = [mapping[i] for i in ids if i in mapping]
    if not coin_ids:
        return {}

    url = "https://api.coincap.io/v2/assets"
    params = {"ids": ",".join(coin_ids)}

    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, params=params, timeout=10) as r:
                if r.status != 200:
                    print(f"CoinCap status: {r.status}")
                    return {}
                data = await r.json()
    except Exception as e:
        print(f"CoinCap error: {e}")
        return {}

    result = {}
    for item in data.get("data", []):
        coin_id = item.get("id", "")
        for cid, mapping_id in mapping.items():
            if mapping_id == coin_id:
                price = float(item.get("priceUsd", 0) or 0)
                change = float(item.get("changePercent24Hr", 0) or 0)
                result[cid] = {
                    "usd": price,
                    "usd_24h_change": change,
                }
                break
    return result
