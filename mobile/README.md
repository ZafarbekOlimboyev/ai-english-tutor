# AI English Tutor — Mobil ilova (Flutter)

Ovoz-markazли ingliz tili suhbat ilovasi. Backend: `../backend` (FastAPI).

## Ishga tushirish (birinchi marta)

Bu papkada `lib/`, `pubspec.yaml` va Android manifest tayyor. Platforma
skeletини (android/ios/…) yaratish uchun:

```bash
cd C:\ai-english-tutor\mobile
flutter create .
```

> `flutter create .` mavjud fayllarни (lib/, pubspec.yaml, AndroidManifest.xml)
> O'ZGARTIRMAYDI — faqat yetishmayotган platforma fayllarини qo'shadi.

Keyin:

```bash
flutter pub get
flutter run --dart-define=API_BASE=http://10.0.2.2:9003
```

- **Android emulyator**: backend host = `http://10.0.2.2:9003` (yuqoridagi kabi).
- **Haqiqiy telefon**: kompyuteringiz LAN IP'sини bering, masalan
  `--dart-define=API_BASE=http://192.168.1.50:9003` (telefon va kompyuter bir Wi-Fi'да).

## Backend'ni ishga tushirish (avval)

```bash
cd C:\ai-english-tutor\backend
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 9003
```

> `--host 0.0.0.0` — telefondан ulanish uchun shart.

## iOS uchun qo'shimcha

`ios/Runner/Info.plist` ga mikrofon ruxsatи izohини qo'shing:

```xml
<key>NSMicrophoneUsageDescription</key>
<string>Ingliz tilida gaplashib mashq qilish uchun mikrofon kerak</string>
```

## Ekranlar

- Splash → (token bormi?) → Onboarding yoki Home
- Onboarding: maqsad tanlash → daraja aniqlash (ovozли)
- Home: daraja, kunlik holat, ssenariylar
- Suhbat: ovozли (mikrofon → STT → AI → TTS)
- Feedback: ball + tuzatishlar + yangi so'zlar
- Paywall: bepul limit tugaganда (to'lov integratsiyasi keyin)

## Arxitektura

- `lib/api.dart` — backend client (token SharedPreferences'да)
- `lib/voice_io.dart` — mikrofon yozish (`record`) + ijro (`audioplayers`)
- `lib/models.dart` — data klasslar
- `lib/theme.dart` — ranglar (binafsha/yashil/marjon)
- `lib/screens/` — ekranlar
