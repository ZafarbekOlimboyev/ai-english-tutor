# AI English Tutor — Backend (FastAPI)

AI bilan ingliz tilida gaplashib o'rgatadigan ilova backendi.

## Ishga tushirish (birinchi marta)

```bash
cd C:\ai-english-tutor\backend

# 1. Virtual muhit yaratish
python -m venv .venv

# 2. Aktivlashtirish (Windows PowerShell)
.venv\Scripts\Activate.ps1

# 3. Kutubxonalarni o'rnatish
pip install -r requirements.txt

# 4. Kalitni sozlash: .env.example dan nusxa oling
copy .env.example .env
# .env faylni oching va GEMINI_API_KEY ga haqiqiy kalitni qo'ying

# 5. Serverni ishga tushirish
uvicorn app.main:app --reload
```

Server ishlaganda: http://127.0.0.1:8000

## Tekshirish

- Health: http://127.0.0.1:8000/health
- API docs (Swagger): http://127.0.0.1:8000/docs — bu yerda /chat ni sinab ko'ring

## Xavfsizlik/ekonomika mustahkamligi (v0.4.0)

Adversarial verify-workflow (14 tasdiqlangan topilma) + real konkurentlik testی asosida:

- Hisob o'g'irlash yopildi — `/auth/register` device_id bo'yicha token qaytarmaydi (token = yagona kalit)
- Pullik LLM chaqiruvlari cheklandi — kunlik LLM budjeti (`free_daily_llm_calls`) + suhbat navbati cheklovi (`free_session_turn_limit`), /message + /feedback + /assess hammasi hisobga olinadi
- Kunlik limit ATOMIK (`db.try_consume`) — TOCTOU race yo'q (8 parallel start → faqat 1 o'tadi)
- Gemini xatosi/None → toza 503 (500 emas) + budjet refund (yiqilган chaqiruv budjetni kuydirmaydi)
- Kirish hajmi cheklovi (message/samples) + tarix oynasi (narx himoyasi)
- Barcha SQLite kirishи RLock ostида (qulfsiz o'qish konkurent yozuvда `InterfaceError` berardi — real test bilan topildi)

## Hozirgi holat (v0.4.0)

Backend "miyasi" + poydevor to'liq ishlaydi:

- [x] FastAPI skeleti + Gemini (`gemini-flash-latest`)
- [x] `POST /auth/register` — parolsiz device auth (Bearer token)
- [x] `GET /auth/me` — foydalanuvchи + bugungi foydalanish
- [x] `GET /scenarios` — 10+ ssenariy ro'yxati
- [x] `POST /session/start` — suhbat boshlash + **kunlik limit (402 paywall)**
- [x] `POST /session/{id}/message` — xotirali suhbat (DB'да saqlanadi)
- [x] `POST /session/{id}/feedback` — xato + yangi so'z + ravonlik bali
- [x] `POST /assess` — CEFR daraja aniqlash (limitга kirmaydi)
- [x] SQLite saqlash (users/sessions/messages/daily_usage/events)
- [x] Analitika event'lari (register, session_start, paywall_hit, feedback, assess)
- [ ] Ovozli suhbat (STT -> LLM -> TTS)
- [ ] Flutter mobil ilova

## Auth

Barcha `/session/*`, `/assess`, `/auth/me` uchun token kerak:
`Authorization: Bearer <token>` (token `/auth/register` dan olinadi).

Bepul limit: kuniga `free_daily_limit` (config, hozir 1) suhbat. Oshsa — 402.

## Tez sinov

Server ishlаganда to'liq oqimni sinash:

```bash
.venv\Scripts\python.exe test_flow.py
```

## Endpointlar

Swagger'да ko'ring: http://127.0.0.1:8001/docs (server 8001-portда ishlaydi)
