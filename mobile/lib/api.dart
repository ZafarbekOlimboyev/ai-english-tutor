import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'models.dart';

/// Bepul limit tugaganда (402) — paywall ko'rsatish uchun.
class PaywallException implements Exception {
  final String message;
  final String error;
  PaywallException(this.message, this.error);
}

/// Umumiy API xatosi.
class ApiException implements Exception {
  final int status;
  final String message;
  ApiException(this.status, this.message);
  @override
  String toString() => message;
}

class Api {
  Api._();
  static final Api instance = Api._();

  /// Backend manzili. Android emulyatorда host = 10.0.2.2.
  /// O'zgartirish: flutter run --dart-define=API_BASE=http://192.168.x.x:9003
  static const String baseUrl =
      String.fromEnvironment('API_BASE', defaultValue: 'http://10.0.2.2:9003');

  String? _token;
  String? get token => _token;
  bool get isAuthed => _token != null;

  Future<void> loadToken() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString('token');
  }

  Future<void> _saveToken(String token) async {
    _token = token;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('token', token);
  }

  Future<void> logout() async {
    _token = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('token');
  }

  Future<String> _deviceId() async {
    final prefs = await SharedPreferences.getInstance();
    var id = prefs.getString('device_id');
    if (id == null) {
      id = 'dev-${DateTime.now().microsecondsSinceEpoch}';
      await prefs.setString('device_id', id);
    }
    return id;
  }

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  Never _raise(http.Response r) {
    dynamic body;
    try {
      body = jsonDecode(r.body);
    } catch (_) {
      body = null;
    }
    if (r.statusCode == 402 && body is Map && body['detail'] is Map) {
      final d = body['detail'] as Map;
      throw PaywallException(
          d['message']?.toString() ?? 'Bepul limit tugadi', d['error']?.toString() ?? '');
    }
    final detail = (body is Map ? body['detail'] : null)?.toString() ?? 'Xatolik yuz berdi';
    throw ApiException(r.statusCode, detail);
  }

  // ---------------- Auth ----------------

  Future<void> register({String? name, String? goal}) async {
    final r = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'device_id': await _deviceId(), 'name': name, 'goal': goal}),
    );
    if (r.statusCode != 200) _raise(r);
    final j = jsonDecode(r.body) as Map<String, dynamic>;
    await _saveToken(j['token'] as String);
  }

  Future<UserMe> me() async {
    final r = await http.get(Uri.parse('$baseUrl/auth/me'), headers: _headers);
    if (r.statusCode != 200) _raise(r);
    return UserMe.fromJson(jsonDecode(r.body) as Map<String, dynamic>);
  }

  // ---------------- Ssenariylar ----------------

  Future<List<Scenario>> scenarios() async {
    final r = await http.get(Uri.parse('$baseUrl/scenarios'), headers: _headers);
    if (r.statusCode != 200) _raise(r);
    final list = jsonDecode(r.body) as List;
    return list.map((e) => Scenario.fromJson(e as Map<String, dynamic>)).toList();
  }

  // ---------------- Suhbat ----------------

  Future<StartSession> startSession(String scenarioId, {String? level}) async {
    final r = await http.post(
      Uri.parse('$baseUrl/session/start'),
      headers: _headers,
      body: jsonEncode({'scenario_id': scenarioId, 'level': level}),
    );
    if (r.statusCode != 200) _raise(r);
    return StartSession.fromJson(jsonDecode(r.body) as Map<String, dynamic>);
  }

  /// Ovozли navbat: audio (WAV baytlari) -> {user_text, reply, reply_audio_b64}.
  Future<VoiceTurn> voiceTurn(String sessionId, List<int> wavBytes) async {
    final req = http.MultipartRequest('POST', Uri.parse('$baseUrl/session/$sessionId/voice'));
    req.headers['Authorization'] = 'Bearer $_token';
    req.files.add(http.MultipartFile.fromBytes('file', wavBytes,
        filename: 'turn.wav'));
    final streamed = await req.send();
    final r = await http.Response.fromStream(streamed);
    if (r.statusCode != 200) _raise(r);
    return VoiceTurn.fromJson(jsonDecode(r.body) as Map<String, dynamic>);
  }

  /// Matnли navbat (ovoz o'rniga, zaxira).
  Future<String> sendMessage(String sessionId, String message) async {
    final r = await http.post(
      Uri.parse('$baseUrl/session/$sessionId/message'),
      headers: _headers,
      body: jsonEncode({'message': message}),
    );
    if (r.statusCode != 200) _raise(r);
    return (jsonDecode(r.body) as Map<String, dynamic>)['reply'] as String;
  }

  Future<Feedback> feedback(String sessionId) async {
    final r = await http.post(
      Uri.parse('$baseUrl/session/$sessionId/feedback'),
      headers: _headers,
    );
    if (r.statusCode != 200) _raise(r);
    return Feedback.fromJson(jsonDecode(r.body) as Map<String, dynamic>);
  }

  Future<LevelResult> assess(List<String> samples) async {
    final r = await http.post(
      Uri.parse('$baseUrl/assess'),
      headers: _headers,
      body: jsonEncode({'samples': samples}),
    );
    if (r.statusCode != 200) _raise(r);
    return LevelResult.fromJson(jsonDecode(r.body) as Map<String, dynamic>);
  }

  // ---------------- Ovoz (alohida) ----------------

  /// Matn -> WAV audio baytlari.
  Future<List<int>> tts(String text) async {
    final r = await http.post(
      Uri.parse('$baseUrl/tts'),
      headers: _headers,
      body: jsonEncode({'text': text}),
    );
    if (r.statusCode != 200) _raise(r);
    return r.bodyBytes;
  }

  /// Audio -> matn.
  Future<String> stt(List<int> wavBytes) async {
    final req = http.MultipartRequest('POST', Uri.parse('$baseUrl/stt'));
    req.headers['Authorization'] = 'Bearer $_token';
    req.files.add(http.MultipartFile.fromBytes('file', wavBytes, filename: 'a.wav'));
    final streamed = await req.send();
    final r = await http.Response.fromStream(streamed);
    if (r.statusCode != 200) _raise(r);
    return (jsonDecode(r.body) as Map<String, dynamic>)['text'] as String;
  }
}
