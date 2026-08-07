import 'package:flutter/material.dart';

import '../api.dart';
import '../models.dart' as m;
import '../theme.dart';

class FeedbackScreen extends StatefulWidget {
  final String sessionId;
  const FeedbackScreen({super.key, required this.sessionId});

  @override
  State<FeedbackScreen> createState() => _FeedbackScreenState();
}

class _FeedbackScreenState extends State<FeedbackScreen> {
  m.Feedback? _fb;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final fb = await Api.instance.feedback(widget.sessionId);
      if (!mounted) return;
      setState(() {
        _fb = fb;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = 'Tahlil yuklanmadi';
        _loading = false;
      });
    }
  }

  void _done() => Navigator.of(context).popUntil((r) => r.isFirst);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator(color: AppColors.primary))
            : _error != null
                ? _errorView()
                : _content(_fb!),
      ),
    );
  }

  Widget _errorView() => Center(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text(_error!, style: const TextStyle(color: AppColors.inkSoft)),
          const SizedBox(height: 12),
          ElevatedButton(onPressed: _done, child: const Text('Bosh sahifa')),
        ]),
      );

  Widget _content(m.Feedback fb) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const SizedBox(height: 8),
        // Ball
        Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(color: AppColors.growthLight, borderRadius: BorderRadius.circular(20)),
          child: Column(
            children: [
              const Text('Ajoyib ish!',
                  style: TextStyle(color: AppColors.growth, fontSize: 18, fontWeight: FontWeight.w600)),
              const SizedBox(height: 10),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.baseline,
                textBaseline: TextBaseline.alphabetic,
                children: [
                  Text('${fb.fluencyScore}',
                      style: const TextStyle(
                          color: AppColors.primaryDark, fontSize: 44, fontWeight: FontWeight.w700)),
                  const Text(' /10 ravonlik', style: TextStyle(color: AppColors.growth, fontSize: 15)),
                ],
              ),
              const SizedBox(height: 8),
              Text(fb.encouragement,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: AppColors.ink, fontSize: 14, height: 1.4)),
            ],
          ),
        ),
        const SizedBox(height: 24),
        // Tuzatishlar
        if (fb.corrections.isNotEmpty) ...[
          const Text('Tuzatishlar',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.ink)),
          const SizedBox(height: 12),
          ...fb.corrections.map(_correctionCard),
          const SizedBox(height: 12),
        ],
        // Yangi so'zlar
        if (fb.newWords.isNotEmpty) ...[
          const Text('Yangi so\'zlar',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.ink)),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: fb.newWords
                .map((w) => Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                          color: AppColors.growthLight, borderRadius: BorderRadius.circular(20)),
                      child: Text(w, style: const TextStyle(color: AppColors.growth, fontSize: 13)),
                    ))
                .toList(),
          ),
          const SizedBox(height: 24),
        ],
        ElevatedButton(onPressed: _done, child: const Text('Davom etish')),
      ],
    );
  }

  Widget _correctionCard(m.Correction c) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.coralLight,
        borderRadius: BorderRadius.circular(12),
        border: const Border(left: BorderSide(color: AppColors.coral, width: 3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(c.original,
              style: const TextStyle(
                  color: AppColors.coral,
                  fontSize: 13,
                  decoration: TextDecoration.lineThrough)),
          const SizedBox(height: 4),
          Text(c.better,
              style: const TextStyle(
                  color: AppColors.coralDark, fontSize: 15, fontWeight: FontWeight.w600)),
          const SizedBox(height: 6),
          Text(c.tip, style: const TextStyle(color: AppColors.inkSoft, fontSize: 13, height: 1.3)),
        ],
      ),
    );
  }
}
