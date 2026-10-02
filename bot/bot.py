import asyncio
import os
from aiohttp import web
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from services.fiat import get_fiat_rates
from services.crypto import get_crypto_prices
from services.converter import convert
from services.stars import get_stars_rate
from services.alert_checker import check_alerts
from database import (
    init_db, add_watch, remove_watch, get_watchlist,
    add_alert, get_user_alerts, delete_alert,
)
from keyboards import (
    main_menu, wl_menu, wl_currency_kb,
    al_menu, al_currency_kb, al_sign_kb, al_del_kb,
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN not found")
    exit(1)

print(f"Token length: {len(BOT_TOKEN)}")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


class AlertFSM(StatesGroup):
    currency = State()
    sign = State()
    threshold = State()


# ================= ГЛАВНОЕ МЕНЮ =================

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! 🍀\n\n"
        "Я <b>Lucky Курсы</b> — показываю курсы валют, крипты и Stars.\n\n"
        "⭐ <b>Избранное</b> — твои любимые валюты\n"
        "🔔 <b>Алерты</b> — уведомления при изменении курса\n\n"
        "Всё через кнопки 👇",
        reply_markup=main_menu(),
    )


@dp.callback_query(F.data == "menu")
async def back_to_menu(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.answer()
    try:
        await cb.message.edit_text(
            "🏠 <b>Главное меню</b>\n\nВыбирай:",
            reply_markup=main_menu(),
        )
    except Exception:
        pass


# ================= КУРСЫ =================

@dp.callback_query(F.data == "fiat")
async def show_fiat(cb: CallbackQuery):
    await cb.answer("Загружаю...")
    rates = await get_fiat_rates("USD")
    if not rates:
        try:
            await cb.message.edit_text("⚠️ Не удалось получить курсы.", reply_markup=main_menu())
        except Exception:
            pass
        return
    targets = ["EUR", "PLN", "UAH", "RUB", "BYN", "GBP", "CHF", "JPY", "CNY"]
    lines = ["💱 <b>Курсы валют к USD</b>\n"]
    for t in targets:
        if t in rates:
            lines.append(f"• 1 USD = <b>{rates[t]:.4f}</b> {t}")
    try:
        await cb.message.edit_text("\n".join(lines), reply_markup=main_menu())
    except Exception:
        pass


@dp.callback_query(F.data == "crypto")
async def show_crypto(cb: CallbackQuery):
    await cb.answer("Загружаю...")
    ids = ["bitcoin", "ethereum", "the-open-network", "solana", "binancecoin"]
    names = {
        "bitcoin": "BTC", "ethereum": "ETH",
    "the-open-network": "GRAM", "solana": "SOL", "binancecoin": "BNB",
    }
    data = await get_crypto_prices(ids)
    if not data:
        try:
            await cb.message.edit_text("⚠️ Не удалось получить данные.", reply_markup=main_menu())
        except Exception:
            pass
        return
    lines = ["🪙 <b>Криптовалюты (USD)</b>\n"]
    for cid in ids:
        if cid in data:
            p = data[cid].get("usd", 0)
            c = data[cid].get("usd_24h_change", 0)
            arrow = "📈" if c >= 0 else "📉"
            lines.append(f"{arrow} <b>{names[cid]}</b>: ${p:,.2f} ({c:+.2f}%)")
    try:
        await cb.message.edit_text("\n".join(lines), reply_markup=main_menu())
    except Exception:
        pass


@dp.callback_query(F.data == "stars")
async def show_stars(cb: CallbackQuery):
    await cb.answer("Считаю...")
    rate = await get_stars_rate()
    text = (
        "⭐ <b>Telegram Stars</b>\n\n"
        f"<b>1 Star ≈ ${rate['usd_per_star']}</b>\n\n"
        f"<i>Курс: {rate['source']}</i>"
    )
    try:
        await cb.message.edit_text(text, reply_markup=main_menu())
    except Exception:
        pass


@dp.callback_query(F.data == "convert")
async def show_convert(cb: CallbackQuery):
    await cb.answer()
    try:
        await cb.message.edit_text(
            "🔄 <b>Конвертер</b>\n\n"
            "Формат: <code>/rate сумма ИЗ В КУДА</code>\n\n"
            "Примеры:\n"
            "<code>/rate 100 USD BYN</code>\n"
            "<code>/rate 1000 RUB PLN</code>\n"
            "<code>/rate 0.5 BTC USD</code>\n"
            "<code>/rate 100 USD STARS</code>",
            reply_markup=main_menu(),
        )
    except Exception:
        pass


@dp.message(Command("rate"))
async def cmd_rate(message: Message):
    parts = message.text.split()
    if len(parts) != 4:
        await message.answer(
            "💱 <b>Конвертер</b>\n\n"
            "Формат: <code>/rate сумма ИЗ В КУДА</code>\n\n"
            "Пример: <code>/rate 100 USD BYN</code>"
        )
        return
    try:
        amount = float(parts[1].replace(",", "."))
    except ValueError:
        await message.answer("⚠️ Сумма должна быть числом.")
        return
    frm = parts[2].upper()
    to = parts[3].upper()
    res = await convert(amount, frm, to)
    if "error" in res:
        await message.answer(f"⚠️ {res['error']}")
        return
    await message.answer(
        f"💱 <b>Конвертация</b>\n\n"
        f"<b>{amount:,.4g} {frm}</b> = <b>{res['result']:,.4g} {to}</b>"
    )


# ================= WATCHLIST =================

@dp.callback_query(F.data == "wl:show")
async def wl_show(cb: CallbackQuery):
    await cb.answer()
    items = await get_watchlist(cb.from_user.id)
    if items:
        text = "⭐ <b>Твоё избранное:</b>\n\n" + "\n".join(f"• <code>{c}</code>" for c in items)
    else:
        text = "⭐ <b>Избранное пусто.</b>\n\nДобавь валюты кнопкой ниже."
    try:
        await cb.message.edit_text(text, reply_markup=wl_menu())
    except Exception:
        pass


@dp.callback_query(F.data == "wl:add")
async def wl_add(cb: CallbackQuery):
    await cb.answer()
    try:
        await cb.message.edit_text(
            "➕ <b>Выбери валюту:</b>",
            reply_markup=wl_currency_kb("add"),
        )
    except Exception:
        pass


@dp.callback_query(F.data.startswith("wl:do_add:"))
async def wl_do_add(cb: CallbackQuery):
    ccy = cb.data.split(":")[2]
    await add_watch(cb.from_user.id, ccy)
    await cb.answer(f"✅ {ccy} добавлено")
    await wl_show(cb)


@dp.callback_query(F.data == "wl:del")
async def wl_del(cb: CallbackQuery):
    await cb.answer()
    items = await get_watchlist(cb.from_user.id)
    if not items:
        try:
            await cb.message.edit_text("⭐ Избранное пусто.", reply_markup=wl_menu())
        except Exception:
            pass
        return
    try:
        await cb.message.edit_text(
            "🗑 <b>Что удалить?</b>",
            reply_markup=wl_currency_kb("del", items),
        )
    except Exception:
        pass


@dp.callback_query(F.data.startswith("wl:do_del:"))
async def wl_do_del(cb: CallbackQuery):
    ccy = cb.data.split(":")[2]
    await remove_watch(cb.from_user.id, ccy)
    await cb.answer(f"🗑 {ccy} удалено")
    await wl_del(cb)


# ================= ALERTS =================

@dp.callback_query(F.data == "al:show")
async def al_show(cb: CallbackQuery):
    await cb.answer()
    alerts = await get_user_alerts(cb.from_user.id)
    if alerts:
        lines = ["🔔 <b>Твои алерты:</b>\n"]
        for a in alerts:
            sign = ">" if a["condition"] == "above" else "<"
            lines.append(f"<b>№{a['id']}</b> {a['currency']} {sign} {a['threshold']} {a['base']}")
        text = "\n".join(lines)
    else:
        text = "🔔 <b>Алертов нет.</b>\n\nСоздай кнопкой ниже."
    try:
        await cb.message.edit_text(text, reply_markup=al_menu())
    except Exception:
        pass


@dp.callback_query(F.data == "al:new")
async def al_new(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await state.set_state(AlertFSM.currency)
    try:
        await cb.message.edit_text(
            "🔔 <b>Шаг 1/3. Выбери валюту:</b>",
            reply_markup=al_currency_kb(),
        )
    except Exception:
        pass


@dp.callback_query(F.data.startswith("al:ccy:"), AlertFSM.currency)
async def al_pick_ccy(cb: CallbackQuery, state: FSMContext):
    ccy = cb.data.split(":")[2]
    await state.update_data(currency=ccy)
    await state.set_state(AlertFSM.sign)
    await cb.answer()
    try:
        await cb.message.edit_text(
            f"🔔 <b>Шаг 2/3.</b> Что должно произойти с <b>{ccy}</b>?",
            reply_markup=al_sign_kb(ccy),
        )
    except Exception:
        pass


@dp.callback_query(F.data.startswith("al:sign:"), AlertFSM.sign)
async def al_pick_sign(cb: CallbackQuery, state: FSMContext):
    sign = cb.data.split(":")[2]
    await state.update_data(condition=sign)
    await state.set_state(AlertFSM.threshold)
    await cb.answer()
    data = await state.get_data()
    ccy = data["currency"]
    word = "выше" if sign == "above" else "ниже"
    try:
        await cb.message.edit_text(
            f"🔔 <b>Шаг 3/3.</b>\n\n"
            f"Введи число, при котором <b>{ccy}</b> станет <b>{word}</b>:\n\n"
            f"Например: <code>100000</code>\n\n"
            f"<i>Можно с базой: <code>3.5 BYN</code></i>"
        )
    except Exception:
        pass


@dp.message(AlertFSM.threshold)
async def al_enter_threshold(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")
    parts = text.split()
    base = "USD"
    try:
        if len(parts) == 1:
            threshold = float(parts[0])
        elif len(parts) == 2:
            threshold = float(parts[0])
            base = parts[1].upper()
        else:
            await message.answer("⚠️ Напиши число. Пример: <code>3.5 BYN</code>")
            return
    except ValueError:
        await message.answer("⚠️ Не похоже на число.")
        return

    data = await state.get_data()
    ccy = data["currency"]
    condition = data["condition"]
    await state.clear()

    alert_id = await add_alert(message.from_user.id, ccy, condition, threshold, base)
    word = "выше" if condition == "above" else "ниже"

    await message.answer(
        f"✅ <b>Алерт создан (№{alert_id})</b>\n\n"
        f"Пингну, когда <b>{ccy}</b> будет <b>{word} {threshold} {base}</b>.",
        reply_markup=main_menu(),
    )


@dp.callback_query(F.data == "al:del")
async def al_del(cb: CallbackQuery):
    await cb.answer()
    alerts = await get_user_alerts(cb.from_user.id)
    if not alerts:
        try:
            await cb.message.edit_text("🔔 Алертов нет.", reply_markup=al_menu())
        except Exception:
            pass
        return
    try:
        await cb.message.edit_text(
            "🗑 <b>Что удалить?</b>",
            reply_markup=al_del_kb(alerts),
        )
    except Exception:
        pass


@dp.callback_query(F.data.startswith("al:do_del:"))
async def al_do_del(cb: CallbackQuery):
    alert_id = int(cb.data.split(":")[2])
    ok = await delete_alert(cb.from_user.id, alert_id)
    if ok:
        await cb.answer(f"🗑 Удалён №{alert_id}")
    else:
        await cb.answer("⚠️ Не найден")
    await al_show(cb)


# ================= HEALTHCHECK + ЗАПУСК =================

async def healthcheck(request):
    return web.Response(text="OK — bot is alive")


async def start_webserver():
    app = web.Application()
    app.router.add_get("/", healthcheck)
    app.router.add_get("/health", healthcheck)
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Webserver started on port {port}")


async def main():
    await init_db()
    print("Bot started. Open Telegram and send /start")
    await asyncio.gather(
        start_webserver(),
        dp.start_polling(bot),
        check_alerts(bot),
    )


if __name__ == "__main__":
    asyncio.run(main())
