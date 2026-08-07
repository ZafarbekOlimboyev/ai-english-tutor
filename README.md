# AI English Tutor

AI bilan ingliz tilida **gaplashib** o'rgatadigan mobil ilova. MDH bozori uchun,
ovoz-markazли, IELTS/karyera fokusi.

- **backend/** — FastAPI + SQLite + Gemini (STT/LLM/TTS bitta kalit bilan)
- **mobile/** — Flutter ilova (ovozли suhbat)

## Tezkor boshlash

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # .env ga GEMINI_API_KEY qo'ying
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 9003
```

Tekshirish: http://127.0.0.1:9003/health va /docs

### 2. Mobil (Flutter)

```bash
cd mobile
flutter create .            # platforma skeletини yaratadi (mavjud fayllarга tegmaydi)
flutter pub get
flutter run --dart-define=API_BASE=http://10.0.2.2:9003
```

## Nima ishlaydi (MVP)

- Ro'yxatdan o'tish (parolsiz, token asosida)
- Daraja aniqlash (ovozли onboarding suhbati)
- 11 ta ssenariy (intervyu, restoran, IELTS...)
- Ovozли suhbat: mikrofon → STT → AI → TTS (xotirali)
- Feedback: ravonlik bali + yumshoq tuzatishlar + yangi so'zlar
- Kunlik bepul limit + paywall (ekonomika himoyasi)

## Ekonomika himoyasi (muhim)

Ovozли AI har chaqiruvга pul yeydi, shuning uchun:
- Kunlik suhbat limiti (`free_daily_limit`) + kunlik LLM budjeti (`free_daily_llm_calls`)
- Suhbat uzunligи cheklovi (`free_session_turn_limit`) + tarix oynasi
- **Global kunlik kill-switch** (`global_daily_llm_calls`) — Sybil hujumга qarshi
- IP bo'yicha ro'yxatdan o'tish cheklovi
- To'langan chaqiruv refund qilinmaydi (faqat provider yiqilса)

Barcha limitlar `backend/app/config.py` да sozlanadi.

## Sifat

Kod ikki bosqichли adversarial verify-workflow (18 tasdiqlangan topilma) va real
konkurentlik/ovoz testlaridан o'tган. Batafsil: `backend/README.md`.
