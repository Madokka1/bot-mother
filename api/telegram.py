from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException, Request
from aiogram.types import Update

from src.config import Settings
from src.app_factory import create_bot_app


settings = Settings.load()
bot, dp, generator = create_bot_app(settings)

app = FastAPI()


@app.get("/api/telegram")
async def health() -> dict:
    return {"ok": True}


@app.post("/api/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict:
    expected = settings.telegram_secret_token
    if expected and x_telegram_bot_api_secret_token != expected:
        raise HTTPException(status_code=401, detail="Invalid secret token")

    payload = await request.json()
    update = Update.model_validate(payload)
    await dp.feed_update(bot, update, settings=settings, generator=generator)
    return {"ok": True}

