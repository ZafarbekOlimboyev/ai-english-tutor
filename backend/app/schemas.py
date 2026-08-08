"""Pydantic modellar — API so'rov/javoblari va AI strukturali tahlillari."""
from pydantic import BaseModel, Field, field_validator

from app.config import settings


# --- Auth ---
class RegisterRequest(BaseModel):
    device_id: str | None = None
    name: str | None = None
    goal: str | None = None  # "work" | "ielts" | "travel" | "general"


class RegisterResponse(BaseModel):
    user_id: str
    token: str
    is_premium: bool
    level: str | None = None


class WaitlistRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)

    @field_validator("email")
    @classmethod
    def _valid_email(cls, v: str) -> str:
        v = v.strip().lower()
        import re
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("email noto'g'ri")
        return v


class MeResponse(BaseModel):
    user_id: str
    name: str | None = None
    goal: str | None = None
    level: str | None = None
    is_premium: bool
    sessions_today: int
    daily_limit: int
    llm_calls_today: int
    daily_llm_limit: int


# --- Suhbat ---
class StartSessionRequest(BaseModel):
    scenario_id: str = "free_talk"
    level: str | None = None  # masalan "A2", "B1"


class StartSessionResponse(BaseModel):
    session_id: str
    scenario_id: str
    ai_opening: str


class MessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=settings.max_message_chars)


class MessageResponse(BaseModel):
    reply: str
    turn_count: int


# --- Ovoz ---
class TtsRequest(BaseModel):
    text: str = Field(min_length=1, max_length=settings.max_message_chars)


class SttResponse(BaseModel):
    text: str


class VoiceTurnResponse(BaseModel):
    user_text: str          # STT natijasi (foydalanuvchи nima dedi)
    reply: str              # AI matn javobi
    reply_audio_b64: str    # AI javobi WAV (base64) — Flutter ijro etadi
    turn_count: int


# --- Feedback (AI strukturali javobi) ---
class Correction(BaseModel):
    original: str = Field(description="What the learner said (with the mistake)")
    better: str = Field(description="A more natural/correct version")
    tip: str = Field(description="A short, simple explanation of the fix")


class Feedback(BaseModel):
    fluency_score: int = Field(description="Overall fluency from 1 to 10")
    encouragement: str = Field(description="One warm, encouraging sentence")
    corrections: list[Correction] = Field(description="2-3 gentle corrections, most useful first")
    new_words: list[str] = Field(description="Useful words/phrases the learner could start using")


# --- Daraja aniqlash ---
class AssessRequest(BaseModel):
    # Onboarding suhbatidagi foydalanuvchi gaplari (bir nechta jumla)
    samples: list[str] = Field(min_length=1, max_length=settings.max_assess_samples)

    @field_validator("samples")
    @classmethod
    def _cap_and_clean(cls, v: list[str]) -> list[str]:
        # Har bir namunani cheklaymiz + bo'shlarini olib tashlaymiz (narx va bema'ni chaqiruv himoyasi)
        cleaned = [s.strip()[: settings.max_sample_chars] for s in v if s and s.strip()]
        if not cleaned:
            raise ValueError("kamida bitta bo'sh bo'lmagan namuna kerak")
        return cleaned


class LevelResult(BaseModel):
    level: str = Field(description="CEFR level: A1, A2, B1, B2, or C1")
    summary: str = Field(description="One friendly sentence about their current level")
    focus: str = Field(description="One thing to focus on next")
