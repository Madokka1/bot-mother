from __future__ import annotations

from functools import lru_cache
import logging
import hashlib

from fastapi import FastAPI, Header, HTTPException, Request, Response
from aiogram.types import Update

from src.app_factory import create_bot_app
from src.config import Settings


app = FastAPI()
logger = logging.getLogger("telegram_webhook")

if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)


@lru_cache(maxsize=1)
def _get_runtime() -> tuple[Settings, object, object, object]:
    settings = Settings.load()
    bot, dp, generator = create_bot_app(settings)
    return settings, bot, dp, generator


def _token_fingerprint(value: str | None) -> str | None:
    if not value:
        return None
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return digest[:10]


def _get_secret_from_headers(request: Request) -> str | None:
    return (
        request.headers.get("x-telegram-bot-api-secret-token")
        or request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        or None
    )

def _get_secret_from_query(request: Request) -> str | None:
    qp = request.query_params
    return qp.get("token") or qp.get("secret") or None


async def _handle_webhook(
    request: Request,
    header_secret: str | None,
    path_secret: str | None,
) -> dict:
    logger.info("incoming update")
    try:
        settings, bot, dp, generator = _get_runtime()
    except Exception as e:
        logger.exception("runtime init failed")
        raise HTTPException(status_code=500, detail=f"Init failed: {type(e).__name__}: {e}") from e

    expected = settings.telegram_secret_token
    if expected:
        received_header = header_secret or _get_secret_from_headers(request)
        received_query = _get_secret_from_query(request)
        if (
            received_header != expected
            and received_query != expected
            and path_secret != expected
        ):
            logger.warning(
                "invalid secret token expected_fp=%s header_fp=%s query_fp=%s path_fp=%s",
                _token_fingerprint(expected),
                _token_fingerprint(received_header),
                _token_fingerprint(received_query),
                _token_fingerprint(path_secret),
            )
            raise HTTPException(status_code=401, detail="Invalid secret token")

    payload = await request.json()
    update = Update.model_validate(payload)
    await dp.feed_update(bot, update, settings=settings, generator=generator)
    return {"ok": True}


@app.get("/")
@app.get("/api/telegram")
async def health(response: Response) -> dict:
    try:
        settings, _, _, _ = _get_runtime()
        return {
            "ok": True,
            "bot_token_set": bool(settings.bot_token),
            "telegram_secret_token_set": bool(settings.telegram_secret_token),
            "telegram_secret_token_fp": _token_fingerprint(settings.telegram_secret_token),
        }
    except Exception as e:
        logger.exception("health check failed")
        response.status_code = 500
        return {"ok": False, "error": type(e).__name__, "detail": str(e)}


@app.post("/api/telegram/{path_secret}")
async def telegram_webhook_with_path(
    path_secret: str,
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(
        default=None,
        alias="X-Telegram-Bot-Api-Secret-Token",
    ),
) -> dict:
    return await _handle_webhook(
        request=request,
        header_secret=x_telegram_bot_api_secret_token,
        path_secret=path_secret,
    )


@app.post("/api/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(
        default=None,
        alias="X-Telegram-Bot-Api-Secret-Token",
    ),
) -> dict:
    return await _handle_webhook(
        request=request,
        header_secret=x_telegram_bot_api_secret_token,
        path_secret=None,
    )
