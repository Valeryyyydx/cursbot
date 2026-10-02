from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Доступные валюты для избранного
FIAT_LIST = ["USD", "EUR", "PLN", "UAH", "RUB", "BYN", "GBP", "CHF", "JPY", "CNY"]
CRYPTO_LIST = ["BTC", "ETH", "GRAM", "SOL", "BNB", "STARS"]


def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💱 Фиат", callback_data="fiat"),
         InlineKeyboardButton(text="🪙 Крипта", callback_data="crypto")],
        [InlineKeyboardButton(text="⭐ Stars", callback_data="stars"),
         InlineKeyboardButton(text="🔄 Конвертер", callback_data="convert")],
        [InlineKeyboardButton(text="⭐ Избранное", callback_data="wl:show")],
        [InlineKeyboardButton(text="🔔 Алерты", callback_data="al:show")],
    ])


def back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu")],
    ])


# --- Watchlist ---

def wl_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить", callback_data="wl:add")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data="wl:del")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu")],
    ])


def wl_currency_kb(action: str, items: list[str] = None):
    """action: 'add' или 'del'. items: для 'del' — что уже в списке."""
    rows = []
    if action == "add":
        all_ccy = FIAT_LIST + CRYPTO_LIST
        row = []
        for c in all_ccy:
            row.append(InlineKeyboardButton(text=c, callback_data=f"wl:do_add:{c}"))
            if len(row) == 3:
                rows.append(row); row = []
        if row: rows.append(row)
    else:  # del
        if items:
            row = []
            for c in items:
                row.append(InlineKeyboardButton(text=f"❌ {c}", callback_data=f"wl:do_del:{c}"))
                if len(row) == 3:
                    rows.append(row); row = []
            if row: rows.append(row)
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="wl:show")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# --- Alerts ---

def al_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать", callback_data="al:new")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data="al:del")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu")],
    ])


def al_currency_kb():
    all_ccy = FIAT_LIST + CRYPTO_LIST
    rows = []
    row = []
    for c in all_ccy:
        row.append(InlineKeyboardButton(text=c, callback_data=f"al:ccy:{c}"))
        if len(row) == 3:
            rows.append(row); row = []
    if row: rows.append(row)
    rows.append([InlineKeyboardButton(text="⬅️ Отмена", callback_data="al:show")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def al_sign_kb(ccy: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⬆️ {ccy} выше", callback_data="al:sign:above"),
         InlineKeyboardButton(text=f"⬇️ {ccy} ниже", callback_data="al:sign:below")],
        [InlineKeyboardButton(text="⬅️ Отмена", callback_data="al:show")],
    ])


def al_del_kb(alerts: list[dict]):
    rows = []
    for a in alerts:
        sign = ">" if a["condition"] == "above" else "<"
        text = f"❌ №{a['id']} {a['currency']} {sign} {a['threshold']} {a['base']}"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"al:do_del:{a['id']}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="al:show")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
