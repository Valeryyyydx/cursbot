import aiohttp


async def _try_coincap(ids: list, mapping: dict) -> dict:
    """Попытка через CoinCap."""
    coin_ids = [mapping[i] for i in ids if i in mapping]
    if not coin_ids:
        return {}
    url = "https://api.coincap.io/v2/assets"
    params = {"ids": ",".join(coin_ids)}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, params=params, timeout=10) as r:
                print(f"[CoinCap] status={r.status}")
                if r.status != 200:
                    return {}
                data = await r.json()
    except Exception as e:
        print(f"[CoinCap] error: {e}")
        return {}

    result = {}
    for item in data.get("data", []):
        coin_id = item.get("id", "")
        for cid, mapping_id in mapping.items():
            if mapping_id == coin_id:
                result[cid] = {
                    "usd": float(item.get("priceUsd", 0) or 0),
                    "usd_24h_change": float(item.get("changePercent24Hr", 0) or 0),
                }
                break
    return result


async def _try_paprika(ids: list, mapping: dict) -> dict:
    """Попытка через CoinPaprika."""
    symbol_map = {
        "bitcoin": "BTC",
        "ethereum": "ETH",
        "the-open-network": "TON",
        "solana": "SOL",
        "binancecoin": "BNB",
    }
    result = {}
    async with aiohttp.ClientSession() as s:
        for cid in ids:
            sym = symbol_map.get(cid)
            if not sym:
                continue
            try:
                url = f"https://api.coinpaprika.com/v1/tickers/{sym.lower()}"
                async with s.get(url, timeout=10) as r:
                    print(f"[Paprika] {sym} status={r.status}")
                    if r.status != 200:
                        continue
                    data = await r.json()
                    quotes = data.get("quotes", {}).get("USD", {})
                    result[cid] = {
                        "usd": float(quotes.get("price", 0) or 0),
                        "usd_24h_change": float(quotes.get("percent_change_24h", 0) or 0),
                    }
            except Exception as e:
                print(f"[Paprika] {sym} error: {e}")
                continue
    return result


async def _try_binance(ids: list, mapping: dict) -> dict:
    """Попытка через Binance."""
    binance_map = {
        "bitcoin": "BTCUSDT",
        "ethereum": "ETHUSDT",
        "the-open-network": "TONUSDT",
        "solana": "SOLUSDT",
        "binancecoin": "BNBUSDT",
    }
    result = {}
    async with aiohttp.ClientSession() as s:
        for cid in ids:
            sym = binance_map.get(cid)
            if not sym:
                continue
            try:
                url = "https://api.binance.com/api/v3/ticker/24hr"
                async with s.get(url, params={"symbol": sym}, timeout=10) as r:
                    print(f"[Binance] {sym} status={r.status}")
                    if r.status != 200:
                        continue
                    data = await r.json()
                    if not isinstance(data, dict) or "lastPrice" not in data:
                        continue
                    result[cid] = {
                        "usd": float(data.get("lastPrice", 0)),
                        "usd_24h_change": float(data.get("priceChangePercent", 0)),
                    }
            except Exception as e:
                print(f"[Binance] {sym} error: {e}")
                continue
    return result


async def get_crypto_prices(ids: list, vs: str = "usd") -> dict:
    """Цены крипты с fallback: CoinCap → CoinPaprika → Binance."""
    mapping = {
        "bitcoin": "bitcoin",
        "ethereum": "ethereum",
        "the-open-network": "toncoin",
        "solana": "solana",
        "binancecoin": "binance-coin",
    }

    print(f"[crypto] Start. ids={ids}")

    # 1. CoinCap
    result = await _try_coincap(ids, mapping)
    print(f"[crypto] CoinCap got {len(result)} coins")
    if len(result) >= 3:
        return result

    # 2. CoinPaprika
    result2 = await _try_paprika(ids, mapping)
    print(f"[crypto] Paprika got {len(result2)} coins")
    if len(result2) > len(result):
        result = result2

    # 3. Binance
    if len(result) < 3:
        result3 = await _try_binance(ids, mapping)
        print(f"[crypto] Binance got {len(result3)} coins")
        if len(result3) > len(result):
            result = result3

    print(f"[crypto] Final: {len(result)} coins")
    return result
