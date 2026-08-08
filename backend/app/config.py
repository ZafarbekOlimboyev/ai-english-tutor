from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ilova sozlamalari — .env fayldan avtomatik o'qiladi."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gemini_api_key: str
    gemini_model: str = "gemini-flash-latest"
    # Asosiy model kvotasi (429) tugasa avtomatik shu modelга o'tiladi (kvota model-boshiga)
    gemini_fallback_model: str = "gemini-flash-lite-latest"
    # Geo-blok (UZ/RU Gemini'ni to'g'ridan bloklaydi) bo'lса — proksi bazaviy URL.
    # Bo'sh bo'lsa to'g'ridan Gemini'ga ulanadi. Masalan: https://argus-ai.uz/gai
    gemini_base_url: str = ""

    # Ovoz modellari (STT matn modeli bilan, TTS alohida)
    tts_model: str = "gemini-2.5-flash-preview-tts"
    tts_fallback_model: str = "gemini-3.1-flash-tts-preview"
    tts_voice: str = "Kore"

    app_name: str = "AI English Tutor"
    app_version: str = "0.4.0"

    # Ma'lumotlar bazasi yo'li. Bo'sh bo'lsa backend/argus_tutor.db.
    # Railway'да doimiy saqlash uchun volume yo'lини bering: masalan /data/argus_tutor.db
    db_path: str = ""

    # --- Ekonomika himoyasi (bepul foydalanuvchi uchun) ---
    free_daily_limit: int = 1          # kuniga nechta suhbat BOSHLASH mumkin
    free_daily_llm_calls: int = 40     # kuniga jami pullik LLM chaqiruvi (message+feedback+assess)
    free_session_turn_limit: int = 30  # bitta suhbatda maks foydalanuvchi navbati
    history_window_turns: int = 40     # LLM'ga yuboriladigan oxirgi xabarlar soni (narx cheklovi)

    # --- Aggregat himoya (Sybil/hisob-fermasига qarshi) ---
    # Kunlik JAMI pullik LLM chaqiruvi (barcha foydalanuvchилар) — kill-switch.
    # Cheksiz anonim register'дан kelib chiqadigan xarajatни chegaralaydi.
    global_daily_llm_calls: int = 5000
    # Bitta IP kuniga nechta ro'yxatdan o'tishi mumkin (Sybil sekinlashtirish)
    register_daily_per_ip: int = 50

    # --- Kirish hajmi cheklovlari ---
    max_message_chars: int = 4000
    max_assess_samples: int = 20
    max_sample_chars: int = 1000
    max_audio_bytes: int = 10 * 1024 * 1024  # yuklanadigan audio maks hajmi (10 MB)


settings = Settings()
