from __future__ import annotations

from dataclasses import dataclass

from dotenv import load_dotenv
import os


@dataclass(frozen=True)
class Settings:
    bot_token: str
    telegram_secret_token: str | None
    hf_space_id: str
    hf_token: str | None
    gen_strength: float
    gen_steps: int
    gen_timeout_sec: int

    @staticmethod
    def load() -> "Settings":
        load_dotenv()

        bot_token = os.getenv("BOT_TOKEN", "").strip()
        if not bot_token:
            raise RuntimeError("BOT_TOKEN is required")

        telegram_secret_token = os.getenv("TELEGRAM_SECRET_TOKEN", "").strip() or None

        hf_space_id = os.getenv("HF_SPACE_ID", "diffusers/unofficial-SDXL-Turbo-i2i-t2i").strip()
        hf_token = os.getenv("HF_TOKEN", "").strip() or None

        gen_strength = float(os.getenv("GEN_STRENGTH", "0.65"))
        gen_steps = int(os.getenv("GEN_STEPS", "2"))
        gen_timeout_sec = int(os.getenv("GEN_TIMEOUT_SEC", "180"))

        return Settings(
            bot_token=bot_token,
            telegram_secret_token=telegram_secret_token,
            hf_space_id=hf_space_id,
            hf_token=hf_token,
            gen_strength=gen_strength,
            gen_steps=gen_steps,
            gen_timeout_sec=gen_timeout_sec,
        )
