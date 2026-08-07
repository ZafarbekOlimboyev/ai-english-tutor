import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';

import '../api.dart';
import '../models.dart';
import '../theme.dart';
import '../voice_io.dart';
import 'feedback_screen.dart';
import 'paywall_screen.dart';

enum _Phase { speaking, idle, listening, thinking }

class ConversationScreen extends StatefulWidget {
  final String sessionId;
  final Scenario scenario;
  final String opening;
  const ConversationScreen({
    super.key,
    required this.sessionId,
    required this.scenario,
    required this.opening,
  });

  @override
  State<ConversationScreen> createState() => _ConversationScreenState();
}

class _ConversationScreenState extends State<ConversationScreen> {
  final _voice = VoiceIO();
  _Phase _phase = _Phase.speaking;
  late String _aiText;
  String _userText = '';
  int _turnCount = 0;

  @override
  void initState() {
    super.initState();
    _aiText = widget.opening;
    _playOpening();
  }

  @override
  void dispose() {
    unawaited(_voice.dispose());
    super.dispose();
  }

  Future<void> _playOpening() async {
    try {
      final audio = await Api.instance.tts(widget.opening);
      await _voice.playBytes(audio);
    } on PaywallException catch (e) {
      // Limit tugagan — yashirmaymiz, paywall ko'rsatamiz
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => PaywallScreen(message: e.message)));
      return;
    } catch (_) {
      // Ochilishни ovoz bilan o'qib bo'lmasa — matn baribir ko'rinadi
    } finally {
      if (mounted) setState(() => _phase = _Phase.idle);
    }
  }

  Future<void> _tapMic() async {
    if (_phase == _Phase.thinking || _phase == _Phase.speaking) return;

    if (_phase == _Phase.listening) {
      // to'xtatib -> yuborish
      setState(() => _phase = _Phase.thinking);
      try {
        final bytes = await _voice.stopRecording();
        if (!mounted) return;
        if (bytes == null) {
          setState(() => _phase = _Phase.idle);
          return;
        }
        final turn = await Api.instance.voiceTurn(widget.sessionId, bytes);
        if (!mounted) return;
        setState(() {
          _userText = turn.userText;
          _aiText = turn.reply;
          _turnCount = turn.turnCount;
          _phase = _Phase.speaking;
        });
        await _voice.playBytes(_decodeB64(turn.replyAudioB64));
        if (mounted) setState(() => _phase = _Phase.idle);
      } on PaywallException catch (e) {
        if (!mounted) return;
        Navigator.of(context).pushReplacement(
            MaterialPageRoute(builder: (_) => PaywallScreen(message: e.message)));
      } catch (e) {
        if (!mounted) return;
        setState(() => _phase = _Phase.idle);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Ushlab bo\'lmadi. Qayta urining.')),
        );
      }
    } else {
      if (!await _voice.hasPermission()) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Mikrofonга ruxsat kerak')),
        );
        return;
      }
      try {
        await _voice.startRecording();
        if (!mounted) return;
        setState(() => _phase = _Phase.listening);
      } catch (e) {
        if (!mounted) return;
        setState(() => _phase = _Phase.idle);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Mikrofonni ishga tushirib bo\'lmadi. Qayta urining.')),
        );
      }
    }
  }

  List<int> _decodeB64(String b64) {
    // base64 -> baytlar (dart:convert kerak emas — kichik yordamchи)
    return base64Decode(b64);
  }

  Future<void> _finish() async {
    if (_turnCount == 0) {
      Navigator.of(context).pop();
      return;
    }
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => FeedbackScreen(sessionId: widget.sessionId)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.primaryDark,
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(widget.scenario.title,
                      style: const TextStyle(color: AppColors.primaryMid, fontSize: 14)),
                  Row(children: [
                    if (_turnCount > 0)
                      TextButton(
                        onPressed: _phase == _Phase.thinking ? null : _finish,
                        child: const Text('Tugatish', style: TextStyle(color: AppColors.growthMic)),
                      ),
                    IconButton(
                      onPressed: _phase == _Phase.thinking
                          ? null
                          : () => Navigator.of(context).pop(),
                      icon: const Icon(Icons.close, color: AppColors.primaryMid),
                    ),
                  ]),
                ],
              ),
            ),
            // AI orb + text
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      width: 72,
                      height: 72,
                      decoration: BoxDecoration(
                        color: _phase == _Phase.speaking ? AppColors.growthMic : AppColors.primary,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.record_voice_over, color: Colors.white, size: 34),
                    ),
                    const SizedBox(height: 20),
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.primary.withValues(alpha: 0.35),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Text(_aiText,
                          textAlign: TextAlign.center,
                          style: const TextStyle(color: AppColors.primaryLight, fontSize: 16, height: 1.5)),
                    ),
                    if (_userText.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      Text('Siz: $_userText',
                          textAlign: TextAlign.center,
                          style: const TextStyle(color: AppColors.primaryMid, fontSize: 13, fontStyle: FontStyle.italic)),
                    ],
                  ],
                ),
              ),
            ),
            // Mic
            Padding(
              padding: const EdgeInsets.only(bottom: 40, top: 10),
              child: Column(
                children: [
                  Text(_statusText(),
                      style: const TextStyle(color: AppColors.primaryMid, fontSize: 13)),
                  const SizedBox(height: 16),
                  GestureDetector(
                    onTap: _tapMic,
                    child: Container(
                      width: 84,
                      height: 84,
                      decoration: BoxDecoration(
                        color: _micColor(),
                        shape: BoxShape.circle,
                        boxShadow: _phase == _Phase.listening
                            ? [BoxShadow(color: AppColors.growthMic.withValues(alpha: 0.3), blurRadius: 0, spreadRadius: 10)]
                            : null,
                      ),
                      child: Icon(_micIcon(), color: Colors.white, size: 36),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _statusText() {
    switch (_phase) {
      case _Phase.speaking:
        return 'AI gapiryapti...';
      case _Phase.listening:
        return 'Tinglayapman — tugagach bosing';
      case _Phase.thinking:
        return 'O\'ylayapman...';
      case _Phase.idle:
        return 'Gapirish uchun bosing';
    }
  }

  Color _micColor() {
    if (_phase == _Phase.listening) return AppColors.growthMic;
    if (_phase == _Phase.thinking || _phase == _Phase.speaking) return AppColors.primaryMid;
    return AppColors.primary;
  }

  IconData _micIcon() {
    switch (_phase) {
      case _Phase.listening:
        return Icons.stop_rounded;
      case _Phase.thinking:
        return Icons.hourglass_empty;
      case _Phase.speaking:
        return Icons.volume_up_rounded;
      case _Phase.idle:
        return Icons.mic_rounded;
    }
  }
}
