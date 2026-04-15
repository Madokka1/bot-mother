from __future__ import annotations

from dataclasses import dataclass
from typing import List

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError


@dataclass(frozen=True)
class SubscriptionCheckResult:
    ok: bool
    missing: List[str]
    errors: List[str]


async def check_user_subscriptions(bot: Bot, user_id: int, channels: list[str]) -> SubscriptionCheckResult:
    missing: list[str] = []
    errors: list[str] = []

    for channel in channels:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            status = getattr(member, "status", None)
            if status in ("left", "kicked"):
                missing.append(channel)
        except (TelegramForbiddenError, TelegramBadRequest) as e:
            # Typically means the bot is not an admin/member in that channel, or the channel is invalid.
            errors.append(f"{channel}: {e.__class__.__name__}")
        except Exception as e:  # pragma: no cover
            errors.append(f"{channel}: {type(e).__name__}")

    ok = (not missing) and (not errors)
    return SubscriptionCheckResult(ok=ok, missing=missing, errors=errors)
