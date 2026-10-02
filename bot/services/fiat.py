import aiohttp


async def get_fiat_rates(base: str = "USD") -> dict:
    """Курсы всех валют к базовой через open.er-api.com."""
    url = f"https://open.er-api.com/v6/latest/{base.upper()}"
    async with aiohttp.ClientSession() as s:
        async with s.get(url, timeout=10) as r:
            data = await r.json()
            return data.get("rates", {})
