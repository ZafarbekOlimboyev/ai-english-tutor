import 'dart:async';

import 'package:flutter/material.dart';

import '../api.dart';
import '../models.dart';
import '../theme.dart';
import '../voice_io.dart';
import 'home_screen.dart';

/// Onboarding 2 — daraja aniqlash. Foydalanuvchи o'zini tanishtiradi, AI darajани baholaydi.
class OnboardingAssessScreen extends StatefulWidget {
  const OnboardingAssessScreen({super.key});

  @override
  State<OnboardingAssessScreen> createState() => _OnboardingAssessScreenState();
}

enum _Phase { intro, recording, thinking, result, error }

class _OnboardingAssessScreenState extends State<OnboardingAssessScreen> {
  final _voice = VoiceIO();
  _Phase _phase = _Phase.intro;
  LevelResult? _result;
  String _error = '';

  @override
  void dispose() {
    unawaited(_voice.dispose());
    super.dispose();
  }

  Future<void> _toggleRecord() async {
    if (_phase == _Phase.recording) {
      // to'xtatib -> STT -> assess
      setState(() => _phase = _Phase.thinking);
      try {
        final bytes = await _voice.stopRecording();
        if (!mounted) return;
        if (bytes == null) {
          setState(() => _phase = _Phase.intro);
          return;
        }
        final text = await Api.instance.stt(bytes);
        final res = await Api.instance.assess([text]);
        if (!mounted) return;
        setState(() {
          _result = res;
          _phase = _Phase.result;
        });
      } catch (e) {
        if (!mounted) return;
        setState(() {
          _error = 'Aniqlab bo\'lmadi. Qayta urinib ko\'ring.';
          _phase = _Phase.error;
        });
      }
    } else {
      if (!await _voice.hasPermission()) {
        if (!mounted) return;
        setState(() {
          _error = 'Mikrofonга ruxsat kerak.';
          _phase = _Phase.error;
        });
        return;
      }
      try {
        await _voice.startRecording();
        if (!mounted) return;
        setState(() => _phase = _Phase.recording);
      } catch (e) {
        if (!mounted) return;
        setState(() {
          _error = 'Mikrofonни ishga tushirib bo\'lmadi.';
          _phase = _Phase.error;
        });
      }
    }
  }

  void _goHome() {
    Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => const HomeScreen()));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        actions: [
          TextButton(
            onPressed: _goHome,
            child: const Text('O\'tkazib yuborish', style: TextStyle(color: AppColors.inkSoft)),
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: _phase == _Phase.result ? _buildResult() : _buildRecord(),
        ),
      ),
    );
  }

  Widget _buildRecord() {
    final recording = _phase == _Phase.recording;
    final thinking = _phase == _Phase.thinking;
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const Text('Keling, tanishamiz',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700, color: AppColors.ink)),
        const SizedBox(height: 12),
        const Text(
          'Ingliz tilida o\'zingiz haqingizda 20-30 soniya gapiring.\nQo\'rqmang — bu test emas, shunchaki suhbat.',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 15, color: AppColors.inkSoft, height: 1.5),
        ),
        const SizedBox(height: 48),
        GestureDetector(
          onTap: thinking ? null : _toggleRecord,
          child: Container(
            width: 120,
            height: 120,
            decoration: BoxDecoration(
              color: recording ? AppColors.growthMic : AppColors.primary,
              shape: BoxShape.circle,
              boxShadow: recording
                  ? [BoxShadow(color: AppColors.growthMic.withValues(alpha: 0.3), blurRadius: 0, spreadRadius: 12)]
                  : null,
            ),
            child: Icon(
              thinking ? Icons.hourglass_empty : (recording ? Icons.stop_rounded : Icons.mic_rounded),
              color: Colors.white,
              size: 52,
            ),
          ),
        ),
        const SizedBox(height: 24),
        Text(
          thinking
              ? 'Baholayapman...'
              : (recording ? 'Tinglayapman — tugagach bosing' : 'Gapirishни boshlash uchun bosing'),
          style: const TextStyle(fontSize: 14, color: AppColors.inkSoft),
        ),
        if (_phase == _Phase.error) ...[
          const SizedBox(height: 16),
          Text(_error, style: const TextStyle(color: AppColors.coral)),
        ],
      ],
    );
  }

  Widget _buildResult() {
    final r = _result!;
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: AppColors.growthLight,
            borderRadius: BorderRadius.circular(20),
          ),
          child: Column(
            children: [
              const Text('Sizning darajangiz', style: TextStyle(color: AppColors.growth, fontSize: 14)),
              const SizedBox(height: 8),
              Text(r.level,
                  style: const TextStyle(
                      color: AppColors.primaryDark, fontSize: 44, fontWeight: FontWeight.w700)),
              const SizedBox(height: 8),
              Text(r.summary,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: AppColors.ink, fontSize: 15, height: 1.4)),
            ],
          ),
        ),
        const SizedBox(height: 20),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.surfaceSoft,
            borderRadius: BorderRadius.circular(14),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(Icons.lightbulb_outline, color: AppColors.primary, size: 20),
              const SizedBox(width: 10),
              Expanded(
                  child: Text(r.focus,
                      style: const TextStyle(color: AppColors.ink, fontSize: 14, height: 1.4))),
            ],
          ),
        ),
        const SizedBox(height: 32),
        ElevatedButton(onPressed: _goHome, child: const Text('Boshlaymiz!')),
      ],
    );
  }
}
