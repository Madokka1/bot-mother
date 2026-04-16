from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.config import Settings
from src.generator import HFSpaceGenerator
from src.handlers import router


def create_bot_app(settings: Settings) -> tuple[Bot, Dispatcher, HFSpaceGenerator]:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    generator = HFSpaceGenerator(
        space_id=settings.hf_space_id,
        hf_token=settings.hf_token,
        timeout_sec=settings.gen_timeout_sec,
        default_strength=settings.gen_strength,
        default_steps=settings.gen_steps,
    )

    dp = Dispatcher()
    dp.include_router(router)
    return bot, dp, generator
