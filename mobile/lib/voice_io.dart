import 'dart:async';
import 'dart:io';
import 'dart:typed_data';

import 'package:audioplayers/audioplayers.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

/// Ovoz yozish (mikrofon) va ijro (dinamik) — bir joyда.
class VoiceIO {
  final AudioRecorder _rec = AudioRecorder();
  final AudioPlayer _player = AudioPlayer();

  Future<bool> hasPermission() => _rec.hasPermission();

  Future<void> startRecording() async {
    // Yozишдан oldin ijroни to'xtatamiz — AI ovozi yozuvга kirib qolmasin
    await stopPlaying();
    final dir = await getTemporaryDirectory();
    final path = '${dir.path}/rec_${DateTime.now().millisecondsSinceEpoch}.wav';
    await _rec.start(
      const RecordConfig(encoder: AudioEncoder.wav, sampleRate: 16000, numChannels: 1),
      path: path,
    );
  }

  Future<bool> get isRecording => _rec.isRecording();

  /// Yozishни to'xtatib WAV baytlarни qaytaradi (yoki null).
  Future<Uint8List?> stopRecording() async {
    final path = await _rec.stop();
    if (path == null) return null;
    final file = File(path);
    if (!await file.exists()) return null;
    final bytes = await file.readAsBytes();
    try {
      await file.delete();
    } catch (_) {}
    return bytes;
  }

  /// Yozishни bekor qilib, vaqtinchalik faylни o'chiradi (ekrandан chiqib ketganда).
  Future<void> cancelRecording() async {
    try {
      final path = await _rec.stop();
      if (path != null) {
        final f = File(path);
        if (await f.exists()) await f.delete();
      }
    } catch (_) {}
  }

  /// WAV baytlarни ijro etadi va TUGASHINI kutadi.
  /// audioplayers'да play() ijro BOSHLANGANда qaytadi — tugashни onPlayerComplete beradi.
  Future<void> playBytes(List<int> bytes) async {
    await _player.stop();
    // Completion event'ини o'tkazib yubormaslik uchun oldин obuna bo'lamiz
    final done = _player.onPlayerComplete.first;
    await _player.play(BytesSource(Uint8List.fromList(bytes)));
    // stop() chaqirilса onPlayerComplete kelmasligи mumkin — himoya timeout
    final estMs = (bytes.length / 48).ceil() + 2000; // 24kHz 16-bit mono ≈ 48 bayt/ms
    await done.timeout(Duration(milliseconds: estMs), onTimeout: () {});
  }

  Future<void> stopPlaying() => _player.stop();

  Future<void> dispose() async {
    await cancelRecording();
    await _rec.dispose();
    await _player.dispose();
  }
}
