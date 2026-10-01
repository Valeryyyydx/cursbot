import asyncio
from database import get_all_alerts, is_triggered, mark_triggered
from services.converter import get_usd_rate

CHECK_INTERVAL = 300


async def check_alerts(bot):
    while True:
        try:
            alerts = await get_all_alerts()
            for a in alerts:
                if await is_triggered(a["id"]):
                    continue

                usd_rate = await get_usd_rate(a["currency"])
                if usd_rate <= 0:
                    continue

                if a["base"] != "USD":
                    base_usd = await get_usd_rate(a["base"])
                    if base_usd <= 0:
                        continue
                    price_in_base = usd_rate / base_usd
                else:
                    price_in_base = usd_rate

                hit = (
                    (a["condition"] == "above" and price_in_base > a["threshold"]) or
                    (a["condition"] == "below" and price_in_base < a["threshold"])
                )

                if hit:
                    arrow = "📈" if a["condition"] == "above" else "📉"
                    word = "выше" if a["condition"] == "above" else "ниже"
                    text = (
                        f"🔔 <b>Алерт сработал!</b>\n\n"
                        f"{arrow} <b>{a['currency']}</b> сейчас <b>{price_in_base:.4f} {a['base']}</b>\n"
                        f"Условие: {word} <b>{a['threshold']} {a['base']}</b>"
                    )
                    try:
                        await bot.send_message(a["user_id"], text)
                        await mark_triggered(a["id"])
                    except Exception as e:
                        print(f"Alert send error: {e}")
        except Exception as e:
            print(f"Alert checker error: {e}")

        await asyncio.sleep(CHECK_INTERVAL)