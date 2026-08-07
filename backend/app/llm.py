"""Gemini bilan ishlash — bir joyда, qayta ishlatiladi.

IKKI xil xatoні ajratamiz (ekonomika uchun muhim):
- LLMUnavailable: chaqiruv Gemini'ga YETIB BORMADI (yoki xato bilan qaytdi) -> TO'LANMADI -> budjet qaytariladi
- LLMBilledEmpty: Gemini ISHLADI (to'landi) lekin bo'sh/parse bo'lmaydigan javob -> budjet QAYTMAYDI
Ikkalasi ham klientга 503 beriladi, lekin refund faqat birinchisiда.
"""
from google import genai
from google.genai import types

from app.config import settings

# Geo-blok bo'lса proksi bazaviy URL orqali (aks holda to'g'ridan Gemini'ga)
_http_opts = (
    types.HttpOptions(base_url=settings.gemini_base_url) if settings.gemini_base_url else None
)
client = genai.Client(api_key=settings.gemini_api_key, http_options=_http_opts)


class LLMUnavailable(Exception):
    """Provider yiqildi/ishlamadi — chaqiruv to'lanmadi (refund mumkin)."""


class LLMBilledEmpty(Exception):
    """Gemini ishladi (to'landi) lekin javob yaroqsiz (bo'sh/None) — refund YO'Q."""


def _to_contents(history: list[dict]) -> list[types.Content]:
    """[{'role': 'user'|'model', 'text': ...}] -> Gemini Content ro'yxati."""
    return [
        types.Content(role=t["role"], parts=[types.Part.from_text(text=t["text"])])
        for t in history
    ]


def _is_quota_error(exc: Exception) -> bool:
    s = str(exc)
    return "429" in s or "RESOURCE_EXHAUSTED" in s


def _generate(contents, config) -> types.GenerateContentResponse:
    """Asosiy model bilan urinadi; kvota (429) tugagan bo'lsa zaxira modelга o'tadi.

    Provider xatoси -> LLMUnavailable (to'lanmadi, refund mumkin).
    """
    try:
        return client.models.generate_content(
            model=settings.gemini_model, contents=contents, config=config
        )
    except Exception as e:
        if _is_quota_error(e) and settings.gemini_fallback_model:
            try:
                return client.models.generate_content(
                    model=settings.gemini_fallback_model, contents=contents, config=config
                )
            except Exception:
                raise LLMUnavailable()
        raise LLMUnavailable()


def chat_reply(history: list[dict], system_prompt: str) -> str:
    """Suhbat javobини qaytaradi (butun tarixни hisobga olib)."""
    response = _generate(
        _to_contents(history),
        types.GenerateContentConfig(system_instruction=system_prompt),
    )
    text = (response.text or "").strip()
    if not text:
        # Gemini ishladi (to'landi) lekin bo'sh/bloklangan javob -> refund YO'Q
        raise LLMBilledEmpty()
    return text


def structured(prompt: str, schema, system_prompt: str | None = None):
    """Strukturali (JSON) javob — feedback va daraja tahlili uchun."""
    response = _generate(
        prompt,
        types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )
    result = response.parsed
    if result is None:
        # parse xatosi yoki xavfsizlik bloki -> to'landi, refund YO'Q
        raise LLMBilledEmpty()
    return result
