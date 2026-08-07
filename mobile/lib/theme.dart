import 'package:flutter/material.dart';

/// ARGUS AI English Tutor ranglar tizimi.
/// Falsafa: qo'rquvni kamaytirish — binafsha (tinch/ishonch), yashil (o'sish),
/// marjon (yumshoq xato). Ovoz-markazli, iliq.
class AppColors {
  // Asosiy — binafsha
  static const primary = Color(0xFF534AB7);
  static const primaryDark = Color(0xFF26215C);
  static const primaryLight = Color(0xFFEEEDFE);
  static const primaryMid = Color(0xFFAFA9EC);

  // O'sish — yashil/teal
  static const growth = Color(0xFF0F6E56);
  static const growthLight = Color(0xFFE1F5EE);
  static const growthMic = Color(0xFF5DCAA5);

  // Yumshoq xato — marjon
  static const coral = Color(0xFFD85A30);
  static const coralLight = Color(0xFFFAECE7);
  static const coralDark = Color(0xFF4A1B0C);

  // Neytral
  static const ink = Color(0xFF2C2C2A);
  static const inkSoft = Color(0xFF888780);
  static const surface = Color(0xFFFFFFFF);
  static const surfaceSoft = Color(0xFFF1EFE8);
}

ThemeData buildTheme() {
  final base = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: AppColors.primary,
      primary: AppColors.primary,
      surface: AppColors.surface,
    ),
    scaffoldBackgroundColor: AppColors.surface,
    fontFamily: 'Roboto',
  );
  return base.copyWith(
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        elevation: 0,
        padding: const EdgeInsets.symmetric(vertical: 16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      ),
    ),
  );
}
