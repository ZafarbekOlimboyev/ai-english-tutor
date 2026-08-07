import 'package:flutter/material.dart';

import '../theme.dart';

/// Bepul limit tugaganда — Premium taklifi.
/// Eslatma: to'lov integratsiyasi (Google Play Billing / Click / Payme) keyin ulanadi.
class PaywallScreen extends StatelessWidget {
  final String message;
  const PaywallScreen({super.key, required this.message});

  static const _benefits = [
    'Cheksiz suhbatlar — kuniga chegara yo\'q',
    'Chuqurroq feedback va tahlil',
    'Barcha ssenariylar va IELTS rejimi',
    'Progress tarixи va statistika',
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.primaryDark,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Align(
                alignment: Alignment.centerRight,
                child: IconButton(
                  onPressed: () => Navigator.of(context).popUntil((r) => r.isFirst),
                  icon: const Icon(Icons.close, color: AppColors.primaryMid),
                ),
              ),
              const Spacer(),
              Container(
                width: 80,
                height: 80,
                decoration: const BoxDecoration(color: AppColors.growthMic, shape: BoxShape.circle),
                child: const Icon(Icons.workspace_premium, color: AppColors.primaryDark, size: 40),
              ),
              const SizedBox(height: 24),
              const Text('ARGUS Premium',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.w700)),
              const SizedBox(height: 10),
              Text(message,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: AppColors.primaryMid, fontSize: 15, height: 1.4)),
              const SizedBox(height: 28),
              ..._benefits.map((b) => Padding(
                    padding: const EdgeInsets.only(bottom: 14),
                    child: Row(children: [
                      const Icon(Icons.check_circle, color: AppColors.growthMic, size: 22),
                      const SizedBox(width: 12),
                      Expanded(
                          child: Text(b,
                              style: const TextStyle(color: AppColors.primaryLight, fontSize: 15))),
                    ]),
                  )),
              const Spacer(),
              ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: AppColors.growthMic, foregroundColor: AppColors.primaryDark),
                onPressed: () {
                  // To'lov integratsiyasi keyin ulanadi (Play Billing / Click / Payme).
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('To\'lov tez orada ulanadi')),
                  );
                },
                child: const Text('Premium olish'),
              ),
              const SizedBox(height: 8),
              TextButton(
                onPressed: () => Navigator.of(context).popUntil((r) => r.isFirst),
                child: const Text('Ertaga qaytaman', style: TextStyle(color: AppColors.primaryMid)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
