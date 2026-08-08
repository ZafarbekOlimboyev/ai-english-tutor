import base64
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse

from app import db, llm, scenarios, voice
from app.auth import get_current_user
from app.config import settings
from app.schemas import (
    AssessRequest,
    Feedback,
    LevelResult,
    MeResponse,
    MessageRequest,
    MessageResponse,
    RegisterRequest,
    RegisterResponse,
    StartSessionRequest,
    StartSessionResponse,
    SttResponse,
    TtsRequest,
    VoiceTurnResponse,
    WaitlistRequest,
)

app = FastAPI(title=settings.app_name, version=settings.app_version)

db.init_db()

# Landing sayt (repo ildizидаги landing/index.html)
_LANDING = Path(__file__).resolve().parent.parent.parent / "landing" / "index.html"

_UNAVAILABLE = "AI hozir javob bera olmadi. Iltimos, birozdan keyin qayta urining."
_GLOBAL = "__global__"  # aggregat LLM hisoblagichи uchun sentinel user_id


@app.get("/health")
def health():
    """Server tirikligini tekshirish."""
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


@app.get("/", include_in_schema=False)
def landing():
    """Marketing landing sayti."""
    if _LANDING.exists():
        return FileResponse(_LANDING)
    return {"app": settings.app_name, "version": settings.app_version}


@app.post("/waitlist")
def join_waitlist(req: WaitlistRequest, request: Request):
    """Waitlist'ga qo'shilish (landing formasi). IP bo'yicha cheklangan."""
    ip = _client_ip(request)
    if not db.try_consume(f"wl:{ip}", "llm_calls", 20):  # kuniga 20/IP (spam himoya)
        raise HTTPException(status_code=429, detail="Juda ko'p urinish. Keyinroq urining.")
    is_new = db.add_waitlist(req.email, "landing")
    db.log_event(None, "waitlist", {"new": is_new})
    return {"ok": True, "already": not is_new, "count": db.waitlist_count()}


# ---------------- Auth ----------------

def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.post("/auth/register", response_model=RegisterResponse)
def register(req: RegisterRequest, request: Request):
    """Ro'yxatdan o'tish — har doim YANGI foydalanuvchи + token.

    Xavfsizlik: device_id bo'yicha mavjud tokenни QAYTARMAYMIZ (aks holda hisob o'g'irlanadi).
    Sybil himoya: IP bo'yicha kunlik ro'yxatdan o'tish cheklangan.
    """
    ip = _client_ip(request)
    if not db.try_consume(f"regip:{ip}", "llm_calls", settings.register_daily_per_ip):
        raise HTTPException(
            status_code=429,
            detail="Juda ko'p ro'yxatdan o'tish urinishi. Keyinroq urinib ko'ring.",
        )

    user = db.create_user(req.device_id, req.name, req.goal)
    db.log_event(user["id"], "register", {"goal": req.goal})
    return RegisterResponse(
        user_id=user["id"],
        token=user["token"],
        is_premium=bool(user["is_premium"]),
        level=user["level"],
    )


@app.get("/auth/me", response_model=MeResponse)
def me(user=Depends(get_current_user)):
    """Joriy foydalanuvchи ma'lumoti + bugungi foydalanish."""
    usage = db.get_today_usage(user["id"])
    return MeResponse(
        user_id=user["id"],
        name=user["name"],
        goal=user["goal"],
        level=user["level"],
        is_premium=bool(user["is_premium"]),
        sessions_today=usage["sessions_started"] if usage else 0,
        daily_limit=settings.free_daily_limit,
        llm_calls_today=usage["llm_calls"] if usage else 0,
        daily_llm_limit=settings.free_daily_llm_calls,
    )


# ---------------- Ssenariylar ----------------

@app.get("/scenarios")
def list_scenarios():
    """10+ ssenariy ro'yxati (Flutter uchun)."""
    return [
        {"id": s["id"], "title": s["title"], "description": s["description"]}
        for s in scenarios.SCENARIOS
    ]


# ---------------- LLM budjet yordamchilari ----------------

def _consume_llm_or_402(user):
    """Pullik LLM chaqiruvi uchun budjet rezerv qiladi: global kill-switch + per-user."""
    # 1) Aggregat kill-switch (HAMMA uchun) — Sybil floodni to'xtatadi
    if not db.try_consume(_GLOBAL, "llm_calls", settings.global_daily_llm_calls):
        db.log_event(user["id"], "global_limit_hit", None)
        raise HTTPException(status_code=503, detail="Xizmat hozir band. Birozdan keyin urining.")
    # 2) Per-user (bepul foydalanuvchи)
    if not user["is_premium"]:
        if not db.try_consume(user["id"], "llm_calls", settings.free_daily_llm_calls):
            db.refund(_GLOBAL, "llm_calls")  # global rezervni qaytaramiz
            db.log_event(user["id"], "llm_limit_hit", {"limit": settings.free_daily_llm_calls})
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "daily_llm_limit_reached",
                    "limit": settings.free_daily_llm_calls,
                    "message": "Bugungi bepul limit tugadi. Cheksiz foydalanish uchun Premium.",
                },
            )


def _refund_llm(user):
    """Budjetни qaytaradi — FAQAT chaqiruv to'lanmagan bo'lса (LLMUnavailable)."""
    db.refund(_GLOBAL, "llm_calls")
    if not user["is_premium"]:
        db.refund(user["id"], "llm_calls")


def _run_paid(user, fn):
    """Pullik LLM chaqiruvини budjet bilan bajaradi.

    - LLMUnavailable (to'lanmadi) -> budjet refund + 503
    - LLMBilledEmpty (to'landi, bo'sh) -> refund YO'Q + 503
    """
    _consume_llm_or_402(user)
    try:
        return fn()
    except llm.LLMUnavailable:
        _refund_llm(user)
        raise HTTPException(status_code=503, detail=_UNAVAILABLE)
    except llm.LLMBilledEmpty:
        raise HTTPException(status_code=503, detail=_UNAVAILABLE)


def _reserve_turn_or_402(user, session_id: str):
    """Atomik navbat rezervi (TOCTOU'siz). Bepulга cheklov, premiumга amaliy cheksiz."""
    limit = settings.free_session_turn_limit if not user["is_premium"] else 10**9
    if not db.try_reserve_turn(session_id, limit):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "turn_limit_reached",
                "limit": settings.free_session_turn_limit,
                "message": "Bu suhbat uzun bo'ldi. Yangi suhbat boshlang yoki Premium oling.",
            },
        )


def _owned_session(session_id: str, user):
    """Sessiyani topadi va egaligini tekshiradi."""
    s = db.get_session(session_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Sessiya topilmadi")
    if s["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Bu sessiya sizniki emas")
    return s


# ---------------- Suhbat ----------------

@app.post("/session/start", response_model=StartSessionResponse)
def start_session(req: StartSessionRequest, user=Depends(get_current_user)):
    """Yangi suhbat boshlash — kunlik limit ATOMIK tekshiriladi (TOCTOU'siz)."""
    scenario = scenarios.get(req.scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Bunday ssenariy yo'q")

    if not user["is_premium"]:
        if not db.try_consume(user["id"], "sessions_started", settings.free_daily_limit):
            db.log_event(user["id"], "paywall_hit", {"limit": settings.free_daily_limit})
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "daily_limit_reached",
                    "limit": settings.free_daily_limit,
                    "message": "Bugungi bepul suhbat tugadi. Cheksiz suhbat uchun Premium.",
                },
            )

    sid = db.create_session(user["id"], req.scenario_id, req.level)
    opening = scenario["opening"]
    db.add_message(sid, "model", opening)  # AI ochilish gapи (LLM chaqiruvi emas — bepul)
    db.log_event(user["id"], "session_start", {"scenario": req.scenario_id, "session_id": sid})

    return StartSessionResponse(session_id=sid, scenario_id=req.scenario_id, ai_opening=opening)


@app.post("/session/{session_id}/message", response_model=MessageResponse)
def send_message(session_id: str, req: MessageRequest, user=Depends(get_current_user)):
    """Foydalanuvchи gapiradi -> AI javob beradi (oyna ichidagi tarixni eslab)."""
    s = _owned_session(session_id, user)
    _reserve_turn_or_402(user, session_id)  # atomik navbat cheklovi

    try:
        convo = db.get_history(session_id, limit=settings.history_window_turns)
        convo.append({"role": "user", "text": req.message})
        system_prompt = scenarios.system_prompt_for(s["scenario_id"], s["level"])
        reply = _run_paid(user, lambda: llm.chat_reply(convo, system_prompt))
    except HTTPException:
        db.refund_turn(session_id)  # navbat kuymaydi
        raise

    db.add_message(session_id, "user", req.message)
    db.add_message(session_id, "model", reply)
    return MessageResponse(reply=reply, turn_count=db.count_user_turns(session_id))


@app.post("/session/{session_id}/feedback", response_model=Feedback)
def get_feedback(session_id: str, user=Depends(get_current_user)):
    """Suhbat oxiriда — xatolar, yangi so'zlar, ravonlik bali."""
    _owned_session(session_id, user)

    history = db.get_history(session_id)
    user_lines = [t["text"] for t in history if t["role"] == "user"]
    if not user_lines:
        raise HTTPException(status_code=400, detail="Foydalanuvchи hali gapirmagan")

    transcript = "\n".join(f"- {line}" for line in user_lines)
    prompt = (
        "Analyze this English learner's spoken lines and give gentle, encouraging feedback.\n"
        f"Learner level: {user['level'] or 'unknown'}.\n"
        f"Their lines:\n{transcript}"
    )
    system = (
        "You are a kind English tutor giving post-conversation feedback. "
        "Be encouraging. Pick only the 2-3 most useful corrections."
    )
    fb = _run_paid(user, lambda: llm.structured(prompt, Feedback, system))
    db.log_event(user["id"], "feedback", {"session_id": session_id, "score": fb.fluency_score})
    return fb


@app.post("/assess", response_model=LevelResult)
def assess_level(req: AssessRequest, user=Depends(get_current_user)):
    """Onboarding — foydalanuvchи gaplariдan CEFR darajaсини aniqlash (LLM budjetiga kiradi)."""
    joined = "\n".join(f"- {line}" for line in req.samples)
    prompt = (
        "Estimate this English learner's CEFR level from their spoken samples.\n"
        f"Samples:\n{joined}"
    )
    system = "You are an English placement assessor. Be fair and encouraging."
    result = _run_paid(user, lambda: llm.structured(prompt, LevelResult, system))
    db.update_user_level(user["id"], result.level)
    db.log_event(user["id"], "assess", {"level": result.level})
    return result


# ---------------- Ovoz ----------------

async def _read_audio(file: UploadFile) -> tuple[bytes, str]:
    """Yuklanган audioни o'qiydi + hajmini tekshiradi."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=422, detail="Audio bo'sh")
    if len(data) > settings.max_audio_bytes:
        raise HTTPException(status_code=413, detail="Audio juda katta")
    mime = file.content_type or "audio/wav"
    return data, mime


@app.post("/stt", response_model=SttResponse)
async def stt(user=Depends(get_current_user), file: UploadFile = File(...)):
    """Audio -> matn (onboarding namunалari va boshqalar uchun)."""
    data, mime = await _read_audio(file)
    _consume_llm_or_402(user)
    try:
        text = voice.transcribe(data, mime)
    except llm.LLMUnavailable:
        _refund_llm(user)  # to'lanmadi -> qaytaramiz
        raise HTTPException(status_code=503, detail=_UNAVAILABLE)
    if not text:
        # Gemini ishladi (to'landi) lekin nutq yo'q -> budjet kuydi, 422
        raise HTTPException(status_code=422, detail="Nutq aniqlanmadi")
    return SttResponse(text=text)


@app.post("/tts")
def tts(req: TtsRequest, user=Depends(get_current_user)):
    """Matn -> audio (WAV). AI ochilish gapи yoki istalgan matnни ovozга aylantirish."""
    _consume_llm_or_402(user)
    try:
        wav = voice.synthesize(req.text)
    except llm.LLMUnavailable:
        _refund_llm(user)
        raise HTTPException(status_code=503, detail=_UNAVAILABLE)
    except llm.LLMBilledEmpty:
        raise HTTPException(status_code=503, detail=_UNAVAILABLE)
    return Response(content=wav, media_type="audio/wav")


@app.post("/session/{session_id}/voice", response_model=VoiceTurnResponse)
async def voice_turn(session_id: str, user=Depends(get_current_user), file: UploadFile = File(...)):
    """Ovozли suhbat navbati: audio -> STT -> AI javob -> TTS. Bitta chaqiruvда.

    Bitta LLM budjeti sarflanadi (ichida STT+chat+TTS). Budjet FAQAT hech narsa to'lanmaган
    bo'lса qaytariladi (STT provider yiqilса). STT ishlagach (to'lanгач) budjet qaytmaydi.
    """
    s = _owned_session(session_id, user)
    data, mime = await _read_audio(file)  # rezervдан oldin (413/422 navbatни kuydirmaydi)
    _reserve_turn_or_402(user, session_id)

    try:
        _consume_llm_or_402(user)
    except HTTPException:
        db.refund_turn(session_id)
        raise

    # 1) STT
    try:
        user_text = voice.transcribe(data, mime)
    except llm.LLMUnavailable:
        _refund_llm(user)          # STT umuman to'lanmadi -> budjet qaytadi
        db.refund_turn(session_id)
        raise HTTPException(status_code=503, detail=_UNAVAILABLE)
    if not user_text:
        db.refund_turn(session_id)  # STT to'landi (budjet kuydi), lekin nutq yo'q
        raise HTTPException(status_code=422, detail="Nutq aniqlanmadi")

    # 2) Chat + TTS (STT allaqachon to'langan -> yiqilса budjet QAYTMAYDI)
    try:
        convo = db.get_history(session_id, limit=settings.history_window_turns)
        convo.append({"role": "user", "text": user_text})
        system_prompt = scenarios.system_prompt_for(s["scenario_id"], s["level"])
        reply = llm.chat_reply(convo, system_prompt)
        wav = voice.synthesize(reply)
    except (llm.LLMUnavailable, llm.LLMBilledEmpty):
        db.refund_turn(session_id)
        raise HTTPException(status_code=503, detail=_UNAVAILABLE)

    db.add_message(session_id, "user", user_text)
    db.add_message(session_id, "model", reply)
    return VoiceTurnResponse(
        user_text=user_text,
        reply=reply,
        reply_audio_b64=base64.b64encode(wav).decode("ascii"),
        turn_count=db.count_user_turns(session_id),
    )
