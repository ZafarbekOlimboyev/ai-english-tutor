/// Backend javoblariга mos data klasslar.

class Scenario {
  final String id;
  final String title;
  final String description;
  Scenario({required this.id, required this.title, required this.description});
  factory Scenario.fromJson(Map<String, dynamic> j) => Scenario(
        id: j['id'] as String,
        title: j['title'] as String,
        description: j['description'] as String,
      );
}

class UserMe {
  final String userId;
  final String? name;
  final String? goal;
  final String? level;
  final bool isPremium;
  final int sessionsToday;
  final int dailyLimit;
  final int llmCallsToday;
  final int dailyLlmLimit;
  UserMe({
    required this.userId,
    this.name,
    this.goal,
    this.level,
    required this.isPremium,
    required this.sessionsToday,
    required this.dailyLimit,
    required this.llmCallsToday,
    required this.dailyLlmLimit,
  });
  factory UserMe.fromJson(Map<String, dynamic> j) => UserMe(
        userId: j['user_id'] as String,
        name: j['name'] as String?,
        goal: j['goal'] as String?,
        level: j['level'] as String?,
        isPremium: j['is_premium'] as bool? ?? false,
        sessionsToday: j['sessions_today'] as int? ?? 0,
        dailyLimit: j['daily_limit'] as int? ?? 1,
        llmCallsToday: j['llm_calls_today'] as int? ?? 0,
        dailyLlmLimit: j['daily_llm_limit'] as int? ?? 40,
      );
}

class StartSession {
  final String sessionId;
  final String scenarioId;
  final String aiOpening;
  StartSession({required this.sessionId, required this.scenarioId, required this.aiOpening});
  factory StartSession.fromJson(Map<String, dynamic> j) => StartSession(
        sessionId: j['session_id'] as String,
        scenarioId: j['scenario_id'] as String,
        aiOpening: j['ai_opening'] as String,
      );
}

class VoiceTurn {
  final String userText;
  final String reply;
  final String replyAudioB64;
  final int turnCount;
  VoiceTurn({
    required this.userText,
    required this.reply,
    required this.replyAudioB64,
    required this.turnCount,
  });
  factory VoiceTurn.fromJson(Map<String, dynamic> j) => VoiceTurn(
        userText: j['user_text'] as String,
        reply: j['reply'] as String,
        replyAudioB64: j['reply_audio_b64'] as String,
        turnCount: j['turn_count'] as int,
      );
}

class Correction {
  final String original;
  final String better;
  final String tip;
  Correction({required this.original, required this.better, required this.tip});
  factory Correction.fromJson(Map<String, dynamic> j) => Correction(
        original: j['original'] as String,
        better: j['better'] as String,
        tip: j['tip'] as String,
      );
}

class Feedback {
  final int fluencyScore;
  final String encouragement;
  final List<Correction> corrections;
  final List<String> newWords;
  Feedback({
    required this.fluencyScore,
    required this.encouragement,
    required this.corrections,
    required this.newWords,
  });
  factory Feedback.fromJson(Map<String, dynamic> j) => Feedback(
        fluencyScore: j['fluency_score'] as int,
        encouragement: j['encouragement'] as String,
        corrections: (j['corrections'] as List)
            .map((e) => Correction.fromJson(e as Map<String, dynamic>))
            .toList(),
        newWords: (j['new_words'] as List).map((e) => e as String).toList(),
      );
}

class LevelResult {
  final String level;
  final String summary;
  final String focus;
  LevelResult({required this.level, required this.summary, required this.focus});
  factory LevelResult.fromJson(Map<String, dynamic> j) => LevelResult(
        level: j['level'] as String,
        summary: j['summary'] as String,
        focus: j['focus'] as String,
      );
}
