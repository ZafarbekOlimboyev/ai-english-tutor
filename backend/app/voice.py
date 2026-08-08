"""Ovoz — STT (audio -> matn) va TTS (matn -> audio), Gemini bilan.

STT matn modeli (kvota fallback bilan) orqali; TTS alohida TTS modeli orqali.
Xato bo'lса toza 503 (500 emas).
"""
import io
import shutil
import subprocess
import wave

from google.genai import types

from app.config import settings
from app.llm import LLMBilledEmpty, LLMUnavailable, client  # bitta genai mijozini qayta ishlatamiz


def _is_quota(exc: Exception) -> bool:
    s = str(exc)
    return "429" in s or "RESOURCE_EXHAUSTED" in s


def _to_gemini_audio(audio_bytes: bytes, mime_type: str) -> tuple[bytes, str]:
    """Brauzer (webm/mp4/ogg) audiosini Gemini qo'llaydiган wav'ga o'giradi (ffmpeg orqали).

    Allaqачон wav bo'lса — tegmaydi. ffmpeg yo'q yoki xato bo'lса — asl baytlarни qaytaradi.
    ffmpeg formatни o'zi aniqlaydi (mime muhim emas).
    """
    if "wav" in (mime_type or "").lower():
        return audio_bytes, "audio/wav"
    if not shutil.which("ffmpeg"):
        return audio_bytes, mime_type  # ffmpeg yo'q — asl holида urinib ko'ramiz
    try:
        proc = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", "pipe:0",
             "-ac", "1", "-ar", "16000", "-f", "wav", "pipe:1"],
            input=audio_bytes, capture_output=True, timeout=30,
        )
        if proc.returncode == 0 and proc.stdout:
            return proc.stdout, "audio/wav"
    except Exception:
        pass
    return audio_bytes, mime_type


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
    if client is None:
        raise LLMUnavailable()  # GEMINI_API_KEY sozlanmagан
    audio_bytes, mime_type = _to_gemini_audio(audio_bytes, mime_type)  # web formatни wav'ga
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
    if client is None:
        raise LLMUnavailable()  # GEMINI_API_KEY sozlanmagан
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
