import aiohttp


async def get_crypto_prices(ids: list, vs: str = "usd") -> dict:
    """Цены крипты через CryptoCompare. Работает из США."""
    mapping = {
        "bitcoin": "BTC",
        "ethereum": "ETH",
        "the-open-network": "TON",
        "solana": "SOL",
        "binancecoin": "BNB",
    }

    symbols = [mapping[i] for i in ids if i in mapping]
    if not symbols:
        return {}

    url = "https://min-api.cryptocompare.com/data/pricemultifull"
    params = {
        "fsyms": ",".join(symbols),
        "tsyms": "USD",
    }

    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, params=params, timeout=10) as r:
                if r.status != 200:
                    print(f"CryptoCompare status: {r.status}")
                    return {}
                data = await r.json()
    except Exception as e:
        print(f"CryptoCompare error: {e}")
        return {}

    raw = data.get("RAW", {})
    result = {}

    for cid in ids:
        sym = mapping.get(cid)
        if not sym:
            continue
        if sym in raw and "USD" in raw[sym]:
            usd_data = raw[sym]["USD"]
            result[cid] = {
                "usd": float(usd_data.get("PRICE", 0)),
                "usd_24h_change": float(usd_data.get("CHANGEPCT24HOUR", 0)),
            }

    return result
