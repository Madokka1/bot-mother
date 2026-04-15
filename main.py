import asyncio
import logging

from src.config import Settings
from src.app_factory import create_bot_app


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    settings = Settings.load()
    bot, dp, generator = create_bot_app(settings)
    await dp.start_polling(bot, settings=settings, generator=generator)


if __name__ == "__main__":
    asyncio.run(main())
