import asyncio
import os
import aiohttp
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from services.fiat import get_fiat_rates
from services.crypto import get_crypto_prices
from services.converter import convert
from services.stars import get_stars_rate, STARS_PER_TON

# --- Загружаем токен из .env ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN не найден в .env")
    exit(1)

# --- Создаём бота ---
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


# --- Кнопки ---
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💱 Фиат", callback_data="fiat")],
        [InlineKeyboardButton(text="🪙 Криптавалюта", callback_data="crypto")],
        [InlineKeyboardButton(text="⭐ Stars", callback_data="stars")],
        [InlineKeyboardButton(text="🔄 Конвертер", callback_data="convert")],
    ])


# --- Хендлеры ---
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! 🚀\n\n"
        "Я <b>ROCKET</b> — показываю курсы валют, крипты и Stars.\n"
        "Выбирай, что показать:",
        reply_markup=main_menu(),
    )


@dp.callback_query(F.data == "fiat")
async def show_fiat(cb: CallbackQuery):
    await cb.answer("Загружаю курсы...")
    rates = await get_fiat_rates("USD")
    if not rates:
        try:
            await cb.message.edit_text(
                "⚠️ Не удалось получить курсы. Попробуй позже.",
                reply_markup=main_menu(),
            )
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
    ids = ["bitcoin", "ethereum", "toncoin", "solana", "binancecoin"]
    names = {
        "bitcoin": "BTC",
        "ethereum": "ETH",
        "gram": "TON",
        "solana": "SOL",
        "binancecoin": "BNB",
    }
    data = await get_crypto_prices(ids)
    if not data:
        try:
            await cb.message.edit_text(
                "⚠️ Не удалось получить данные.", reply_markup=main_menu()
            )
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
    await cb.answer("Считаю курс...")
    rate = await get_stars_rate()

    text = (
        "⭐ <b>Telegram Stars</b>\n\n"
        f"<b>1 Star ≈ ${rate['usd_per_star']}</b>\n"
    )
    if rate["ton_usd"]:
        text += (
            f"\n📊 Расчёт:\n"
            f"• 1 TON = <b>${rate['ton_usd']}</b>\n"
            f"• 1 TON ≈ <b>{STARS_PER_TON} Stars</b>\n"
            f"• 1 Star ≈ <b>{rate['ton_per_star']} TON</b>\n"
        )
    text += f"\n<i>источник: {rate['source']}</i>"

    try:
        await cb.message.edit_text(text, reply_markup=main_menu())
    except Exception:
        pass


@dp.callback_query(F.data == "convert")
async def show_convert(cb: CallbackQuery):
    await cb.answer()
    try:
        await cb.message.edit_text(
            "🔄 <b>Конвертер валют</b>\n\n"
            "Напиши команду в чат:\n\n"
            "<code>/rate 100 USD BYN</code>\n"
            "<code>/rate 1000 RUB PLN</code>\n"
            "<code>/rate 0.5 BTC USD</code>\n"
            "<code>/rate 100 USD STARS</code>\n\n"
            "<b>Фиат:</b> USD, EUR, PLN, UAH, RUB, BYN, GBP, CHF, JPY, CNY\n"
            "<b>Криптавалюта:</b> BTC, ETH, TON, SOL, BNB\n"
            "<b>Telegram:</b> STARS",
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
            "Пример:\n"
            "<code>/rate 100 USD BYN</code>\n"
            "<code>/rate 1000 RUB PLN</code>\n"
            "<code>/rate 0.5 BTC USD</code>\n"
            "<code>/rate 100 USD STARS</code>"
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
        f"<b>{amount:,.4g} {frm}</b> = <b>{res['result']:,.4g} {to}</b>\n\n"
        f"<i>через USD: ${res['usd_amount']:,.4g}</i>"
    )


# --- Запуск ---
async def main():
    print("🚀 Бот запущен. Открой Telegram и напиши /start")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())