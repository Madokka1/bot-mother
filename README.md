# Telegram bot: “1 Мая” стилизация фото (Vercel webhook)

## Что умеет
- `/start` — краткая инструкция.
- Пользователь отправляет фото (можно с подписью) — бот делает стилизацию в тематике “1 Мая”.

Сейчас ограничения/проверки подписок отключены (подготовка к деплою).

## Быстрый старт
1) Создайте окружение и поставьте зависимости:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`
2) Создайте `.env` на основе `.env.example` и заполните `BOT_TOKEN`.
3) Локальный запуск (polling, для отладки):
   - `python main.py`

## Генерация изображений
По умолчанию используется бесплатный Hugging Face Space `diffusers/unofficial-SDXL-Turbo-i2i-t2i` через `gradio_client`.
Если захотите заменить Space — поменяйте `HF_SPACE_ID` и (если нужно) `HF_TOKEN`.

Примечание: Space `multimodalart/nano-banana` использует Nano Banana (Gemini), но в текущей реализации он **PRO-only** на стороне Hugging Face, поэтому по умолчанию выбран публичный SDXL img2img Space.

## Деплой на Vercel
1) Задеплойте репозиторий на Vercel (Python).
2) В настройках проекта Vercel добавьте env vars:
   - `BOT_TOKEN`
   - `TELEGRAM_SECRET_TOKEN` (рекомендуется)
   - `HF_SPACE_ID` (опционально)
   - `HF_TOKEN` (опционально)
3) Установите webhook в Telegram на URL вашей функции:
   - URL: `https://<your-vercel-domain>/api/telegram`
   - Secret token: значение `TELEGRAM_SECRET_TOKEN`

Установка webhook (пример через curl):
`curl -X POST "https://api.telegram.org/bot<БОТ_ТОКЕН>/setWebhook" -d "url=https://<your-vercel-domain>/api/telegram" -d "secret_token=<TELEGRAM_SECRET_TOKEN>"`

Важно: генерация может занимать >10 секунд, поэтому на бесплатных лимитах Vercel возможны таймауты. В `vercel.json` выставлен `maxDuration: 300`, но фактический лимит зависит от вашего тарифа.
