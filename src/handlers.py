from __future__ import annotations

import tempfile
from pathlib import Path

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, FSInputFile

from src.config import Settings
from src.generator import HFSpaceGenerator
from src.prompts import build_prompt


router = Router()


def _channels_text(channels: list[str]) -> str:
    parts: list[str] = []
    for ch in channels:
        if ch.startswith("@"):
            parts.append(f"• {ch}")
        else:
            parts.append(f"• {ch} (id)")
    return "\n".join(parts)


@router.message(Command("start"))
async def cmd_start(message: Message, settings: Settings) -> None:
    text = (
        "Привет! Отправь фото — сделаю стилизацию в тематике «1 Мая».\n\n"
        "Можно добавить подпись к фото (что именно изменить/добавить)."
    )
    await message.answer(text)


@router.callback_query(F.data == "check_subs")
async def cb_check_subs(query: CallbackQuery) -> None:
    # legacy callback kept to avoid "button does nothing" if someone has old message cached
    await query.answer("Ограничения отключены", show_alert=False)


@router.message(F.photo)
async def on_photo(message: Message, settings: Settings, generator: HFSpaceGenerator) -> None:
    photo = message.photo[-1]
    caption_hint = (message.caption or "").strip()
    prompt = build_prompt(caption_hint)

    await message.answer("Генерирую в стиле «1 Мая»… Это может занять до пары минут.")

    with tempfile.TemporaryDirectory() as td:
        src_path = Path(td) / f"src_{photo.file_unique_id}.jpg"
        try:
            await message.bot.download(file=photo.file_id, destination=src_path)
        except TelegramBadRequest:
            # fallback: try downloading via file object
            file = await message.bot.get_file(photo.file_id)
            await message.bot.download_file(file.file_path, destination=src_path)

        try:
            out_path = await generator.generate_img2img(str(src_path), prompt)
        except Exception as e:
            await message.answer(f"Не получилось сгенерировать изображение: {type(e).__name__}")
            return

        await message.answer_photo(
            photo=FSInputFile(out_path),
            caption="Готово.",
        )
