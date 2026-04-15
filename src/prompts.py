BASE_STYLE_PROMPT = (
    "Soviet May Day (1st of May) propaganda poster style, 1950s USSR, "
    "bright red flags, optimistic workers, heroic realism, vintage print texture, "
    "bold graphic composition, high contrast, clean face, high quality, no text, no watermark"
)

NEGATIVE_HINTS = "blurry, lowres, deformed, extra fingers, bad anatomy, watermark, text"


def build_prompt(user_hint: str | None) -> str:
    hint = (user_hint or "").strip()
    if not hint:
        return BASE_STYLE_PROMPT
    return f"{BASE_STYLE_PROMPT}. User request: {hint}"
