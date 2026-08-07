import 'package:flutter/material.dart';

import '../api.dart';
import '../theme.dart';
import 'onboarding_assess_screen.dart';

/// Onboarding 1 — maqsad tanlash. Tanlagach ro'yxatdan o'tadi.
class OnboardingGoalScreen extends StatefulWidget {
  const OnboardingGoalScreen({super.key});

  @override
  State<OnboardingGoalScreen> createState() => _OnboardingGoalScreenState();
}

class _OnboardingGoalScreenState extends State<OnboardingGoalScreen> {
  static const _goals = [
    ('work', 'Ish va karyera', Icons.work_outline),
    ('ielts', 'IELTS / imtihon', Icons.school_outlined),
    ('travel', 'Sayohat', Icons.flight_takeoff),
    ('general', 'Umumiy rivojlanish', Icons.auto_awesome_outlined),
  ];

  String? _selected;
  bool _busy = false;
  String? _error;

  Future<void> _continue() async {
    if (_selected == null) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await Api.instance.register(goal: _selected);
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const OnboardingAssessScreen()),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = 'Ulanib bo\'lmadi. Internetни tekshiring.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 20),
              const Text('Nima uchun o\'rganyapsiz?',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700, color: AppColors.ink)),
              const SizedBox(height: 8),
              const Text('Suhbatlarни siz uchun moslashtiramiz',
                  style: TextStyle(fontSize: 15, color: AppColors.inkSoft)),
              const SizedBox(height: 28),
              Expanded(
                child: ListView.separated(
                  itemCount: _goals.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 12),
                  itemBuilder: (_, i) {
                    final g = _goals[i];
                    final sel = _selected == g.$1;
                    return InkWell(
                      borderRadius: BorderRadius.circular(16),
                      onTap: () => setState(() => _selected = g.$1),
                      child: Container(
                        padding: const EdgeInsets.all(18),
                        decoration: BoxDecoration(
                          color: sel ? AppColors.primaryLight : AppColors.surfaceSoft,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(
                            color: sel ? AppColors.primary : Colors.transparent,
                            width: 2,
                          ),
                        ),
                        child: Row(
                          children: [
                            Icon(g.$3, color: sel ? AppColors.primary : AppColors.inkSoft),
                            const SizedBox(width: 14),
                            Text(g.$2,
                                style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w500,
                                    color: sel ? AppColors.primaryDark : AppColors.ink)),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
              if (_error != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Text(_error!, style: const TextStyle(color: AppColors.coral)),
                ),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: (_selected == null || _busy) ? null : _continue,
                  child: _busy
                      ? const SizedBox(
                          height: 22, width: 22,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : const Text('Davom etish'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
