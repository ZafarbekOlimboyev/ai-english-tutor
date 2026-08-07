"""Ovoz — STT (audio -> matn) va TTS (matn -> audio), Gemini bilan.

STT matn modeli (kvota fallback bilan) orqali; TTS alohida TTS modeli orqali.
Xato bo'lса toza 503 (500 emas).
"""
import io
import wave

from google.genai import types

from app.config import settings
from app.llm import LLMBilledEmpty, LLMUnavailable, client  # bitta genai mijozini qayta ishlatamiz


def _is_quota(exc: Exception) -> bool:
    s = str(exc)
    return "429" in s or "RESOURCE_EXHAUSTED" in s


def _pcm_to_wav(pcm: bytes, rate: int = 24000) -> bytes:
    """Gemini TTS xom PCM (L16 mono) qaytaradi -> ijro etiladigan WAV."""
    buf = io.BytesIO()
    w = wave.open(buf, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)  # 16-bit
    w.setframerate(rate)
    w.writeframes(pcm)
    w.close()
    return buf.getvalue()


def transcribe(audio_bytes: bytes, mime_type: str) -> str:
    """STT: audio -> ingliz matni. Kvota tugasa fallback modelга o'tadi.

    Provider yiqilса LLMUnavailable (to'lanmadi). Bo'sh natija -> "" (chaqiruvchи 422 qiladi,
    lekin Gemini ishlagani uchun budjet qaytmaydi).
    """
    contents = [
        types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
        "Transcribe this English audio to text. Output ONLY the transcription, nothing else.",
    ]
    try:
        resp = client.models.generate_content(model=settings.gemini_model, contents=contents)
    except Exception as e:
        if _is_quota(e) and settings.gemini_fallback_model:
            try:
                resp = client.models.generate_content(
                    model=settings.gemini_fallback_model, contents=contents
                )
            except Exception:
                raise LLMUnavailable()
        else:
            raise LLMUnavailable()
    return (resp.text or "").strip()


def synthesize(text: str) -> bytes:
    """TTS: matn -> WAV baytlari. Kvota tugasa zaxira TTS modelга o'tadi."""
    config = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=settings.tts_voice)
            )
        ),
    )
    resp = None
    for model in (settings.tts_model, settings.tts_fallback_model):
        try:
            resp = client.models.generate_content(model=model, contents=text, config=config)
            break
        except Exception:
            resp = None
            continue
    if resp is None:
        raise LLMUnavailable()

    try:
        part = resp.candidates[0].content.parts[0]
        pcm = part.inline_data.data
    except Exception:
        pcm = None
    if not pcm:
        # Gemini ishladi lekin audio bermadi -> to'landi, refund yo'q
        raise LLMBilledEmpty()
    return _pcm_to_wav(pcm)
