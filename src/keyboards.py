from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def subscription_keyboard(channels: list[str]) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []

    for ch in channels:
        username = ch
        if ch.startswith("@"):
            username = ch[1:]
        if username.isdigit() or username.startswith("-100"):
            # numeric ids can't be opened as URL reliably
            continue
        buttons.append([InlineKeyboardButton(text=f"Подписаться: @{username}", url=f"https://t.me/{username}")])

    buttons.append([InlineKeyboardButton(text="Проверить подписку ✅", callback_data="check_subs")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
