# iOS (iPhone) uchun qurish

⚠️ **iOS ilovani faqat macOS (Mac) da Xcode bilan qurish mumkin.** Windows'da bo'lmaydi (Apple qoidasi).
iOS papka (`ios/`) va mikrofon ruxsati allaqachon tayyorlangan.

## Mac'da qurish (eng oson yo'l)

1. Repo'ni Mac'ga oling:
   ```bash
   git clone https://github.com/ZafarbekOlimboyev/ai-english-tutor.git
   cd ai-english-tutor/mobile
   ```
2. Flutter + Xcode + CocoaPods o'rnatilган bo'lсин (`flutter doctor` tekshiradi).
3. Paketlar:
   ```bash
   flutter pub get
   cd ios && pod install && cd ..
   ```
4. **O'z iPhone'ingizда sinash** (bepul Apple ID bilan — ilova 7 kun ishlaydi):
   ```bash
   flutter run --release --dart-define=API_BASE=https://ai-english-tutor-production-999c.up.railway.app
   ```
   (iPhone'ни USB bilan ulang; birinchи marta Xcode'да "Signing & Capabilities" да o'z Apple ID (Team) ni tanlang.)

## App Store / TestFlight (ko'p kishiga tarqatish)

- **Apple Developer Program** kerak: $99/yil (developer.apple.com).
- Xcode'да Team + Bundle ID (`uz.argus.aiEnglishTutor`) sozlang.
- `flutter build ipa --dart-define=API_BASE=https://ai-english-tutor-production-999c.up.railway.app`
- `build/ios/ipa/*.ipa` ni **Transporter** (yoki Xcode Organizer) orqali **App Store Connect** ga yuklang.
- TestFlight orqali beta-testerlarга tarqating, so'ng App Store'ga chiqaring.

## Mac yo'q bo'lsa — bulutda qurish

- **Codemagic** (codemagic.io) yoki **GitHub Actions (macos runner)** — GitHub rep'ni ulaб, iOS build bulutда bo'ladi.
- Baribir **Apple Developer akkаunt** (signing sertifikati) kerak.

## Eslatма

- `API_BASE` ni doim Railway URL bilan bering (yuqoridаги), aks holда ilova backendни topmaydi.
- Mikrofon ruxsati (`NSMicrophoneUsageDescription`) Info.plist'да tayyor.
- Bundle ID: `uz.argus.aiEnglishTutor` (org: uz.argus).
