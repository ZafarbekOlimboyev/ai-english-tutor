import 'dart:async';
import 'dart:io';
import 'dart:typed_data';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

/// Ovoz yozish (mikrofon) va ijro (dinamik) — bir joyда.
/// Mobil: WAV faylга yozadi. Web: brauzer formatида (webm/mp4) — backend ffmpeg bilan
/// wav'ga o'giradi. Web'да path_provider/dart:io ishlatilmaydi (kIsWeb bilan ajratilган).
class VoiceIO {
  final AudioRecorder _rec = AudioRecorder();
  final AudioPlayer _player = AudioPlayer();

  Future<bool> hasPermission() => _rec.hasPermission();

  Future<void> startRecording() async {
    // Yozишдан oldin ijroни to'xtatamiz — AI ovozi yozuvга kirib qolmasin
    await stopPlaying();
    if (kIsWeb) {
      // Web: brauzer qo'llab-quvvatlaydigan formatни o'zi tanlaydi; fayl yo'li kerak emas
      await _rec.start(const RecordConfig(), path: '');
    } else {
      final dir = await getTemporaryDirectory();
      final path = '${dir.path}/rec_${DateTime.now().millisecondsSinceEpoch}.wav';
      await _rec.start(
        const RecordConfig(encoder: AudioEncoder.wav, sampleRate: 16000, numChannels: 1),
        path: path,
      );
    }
  }

  Future<bool> get isRecording => _rec.isRecording();

  /// Yozishни to'xtatib audio baytlarни qaytaradi (yoki null).
  Future<Uint8List?> stopRecording() async {
    final path = await _rec.stop();
    if (path == null) return null;
    if (kIsWeb) {
      // Web: path = blob URL -> baytlarни olib kelamiz
      try {
        return await http.readBytes(Uri.parse(path));
      } catch (_) {
        return null;
      }
    }
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
      if (!kIsWeb && path != null) {
        final f = File(path);
        if (await f.exists()) await f.delete();
      }
    } catch (_) {}
  }

  /// Audio baytlarни ijro etadi va TUGASHINI kutadi.
  /// audioplayers'да play() ijro BOSHLANGANда qaytadi — tugashні onPlayerComplete beradi.
  Future<void> playBytes(List<int> bytes) async {
    await _player.stop();
    // Completion event'ини o'tkazib yubormaslik uchun oldин obuna bo'lamiz
    final done = _player.onPlayerComplete.first;
    await _player.play(BytesSource(Uint8List.fromList(bytes)));
    // stop() chaqirilса onPlayerComplete kelmasligі mumkin — himoya timeout
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
