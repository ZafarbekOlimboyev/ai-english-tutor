# Railway'ga deploy qilish

Backend (FastAPI + landing sayt) Railway'да ishlaydi. Railway US/EU'да — Gemini geo-blok yo'q.

## Qadamlar (Railway dashboard)

1. **railway.app** ga kiring (GitHub bilan ro'yxatdan o'ting — bepul).
2. **New Project** → **Deploy from GitHub repo** → `ZafarbekOlimboyev/ai-english-tutor` ni tanlang.
3. Railway `railway.json` ni topadi va avtomatik quradi (NIXPACKS, Python 3.12).
   - Build: `pip install -r requirements.txt` (u `backend/requirements.txt` ni chaqiradi)
   - Start: `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Variables** (Settings → Variables) ga qo'shing:
   - `GEMINI_API_KEY` = sizning kalitingiz (MAJBURIY)
   - `DB_PATH` = `/data/argus_tutor.db` (doimiy saqlash uchun — pastдаги volume bilan)
   - (ixtiyoriy) `GEMINI_MODEL`, `FREE_DAILY_LLM_CALLS`, `GLOBAL_DAILY_LLM_CALLS` va h.k.
5. **Doimiy DB uchun volume** (aks holда har deploy'да ma'lumot o'chadi):
   - Service → **Settings → Volumes** → **New Volume** → Mount path: `/data`
6. **Generate Domain** (Settings → Networking → Public Networking) → `https://xxx.up.railway.app` olasiz.

## Deploy'дан keyin

1. Tekshiring: `https://xxx.up.railway.app/health` va `/` (landing).
2. **APK'ни yangi URL bilan qayta build qiling** (telefon istalgan joydan ulanсин):
   ```
   cd mobile
   flutter build apk --release --dart-define=API_BASE=https://xxx.up.railway.app
   ```
3. Landing waitlist formasi endi Railway domenида ishlaydi.

## Muhim

- `.env` va DB Git'ga chiqmaydi — kalitni faqat Railway Variables'да bering.
- Bepul reja cheklovlari bor (soatlik/oylik) — trafik oshса Pro rejага o'ting.
- Alternativa: Render, Fly.io — bir xil `railway.json`/start buyrug'и mantiqи bilan.
