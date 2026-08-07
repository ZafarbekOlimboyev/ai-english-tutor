import 'package:flutter/material.dart';

import '../api.dart';
import '../models.dart';
import '../theme.dart';
import 'conversation_screen.dart';
import 'paywall_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  UserMe? _me;
  List<Scenario> _scenarios = [];
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
      final me = await Api.instance.me();
      final scenarios = await Api.instance.scenarios();
      if (!mounted) return;
      setState(() {
        _me = me;
        _scenarios = scenarios;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = 'Ma\'lumot yuklanmadi';
        _loading = false;
      });
    }
  }

  Future<void> _start(Scenario s) async {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => const Center(child: CircularProgressIndicator(color: AppColors.primary)),
    );
    try {
      final session = await Api.instance.startSession(s.id, level: _me?.level);
      if (!mounted) return;
      Navigator.of(context).pop(); // dialog
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ConversationScreen(sessionId: session.sessionId, scenario: s, opening: session.aiOpening),
        ),
      );
      _load(); // qaytгач yangilaymiz
    } on PaywallException catch (e) {
      if (!mounted) return;
      Navigator.of(context).pop();
      Navigator.of(context).push(MaterialPageRoute(builder: (_) => PaywallScreen(message: e.message)));
    } catch (e) {
      if (!mounted) return;
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Suhbatni boshlab bo\'lmadi')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator(color: AppColors.primary)));
    }
    if (_error != null) {
      return Scaffold(
        body: Center(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Text(_error!, style: const TextStyle(color: AppColors.inkSoft)),
            const SizedBox(height: 12),
            ElevatedButton(onPressed: _load, child: const Text('Qayta urinish')),
          ]),
        ),
      );
    }

    final me = _me!;
    final featured = _scenarios.isNotEmpty ? _scenarios.first : null;
    final rest = _scenarios.length > 1 ? _scenarios.sublist(1) : <Scenario>[];

    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _load,
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              _header(me),
              const SizedBox(height: 20),
              if (featured != null) _featuredCard(featured),
              const SizedBox(height: 24),
              const Text('Boshqa mavzular',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.ink)),
              const SizedBox(height: 12),
              ...rest.map(_scenarioTile),
            ],
          ),
        ),
      ),
    );
  }

  Widget _header(UserMe me) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(color: AppColors.primaryLight, borderRadius: BorderRadius.circular(20)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Salom${me.name != null ? ", ${me.name}" : ""}!',
                  style: const TextStyle(
                      fontSize: 20, fontWeight: FontWeight.w700, color: AppColors.primaryDark)),
              if (me.level != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(color: AppColors.primary, borderRadius: BorderRadius.circular(20)),
                  child: Text(me.level!, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                ),
            ],
          ),
          const SizedBox(height: 6),
          Text('Bugun: ${me.sessionsToday}/${me.dailyLimit} suhbat',
              style: const TextStyle(color: AppColors.primary, fontSize: 13)),
        ],
      ),
    );
  }

  Widget _featuredCard(Scenario s) {
    return InkWell(
      borderRadius: BorderRadius.circular(20),
      onTap: () => _start(s),
      child: Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(color: AppColors.primary, borderRadius: BorderRadius.circular(20)),
        child: Column(
          children: [
            const Text('Bugungi suhbat', style: TextStyle(color: AppColors.primaryMid, fontSize: 13)),
            const SizedBox(height: 6),
            Text(s.title,
                style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w600)),
            const SizedBox(height: 20),
            Container(
              width: 64,
              height: 64,
              decoration: const BoxDecoration(color: Colors.white, shape: BoxShape.circle),
              child: const Icon(Icons.mic_rounded, color: AppColors.primary, size: 32),
            ),
            const SizedBox(height: 12),
            const Text('Boshlash', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
          ],
        ),
      ),
    );
  }

  Widget _scenarioTile(Scenario s) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: () => _start(s),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: AppColors.surfaceSoft, borderRadius: BorderRadius.circular(14)),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(s.title,
                        style: const TextStyle(
                            fontSize: 15, fontWeight: FontWeight.w500, color: AppColors.ink)),
                    const SizedBox(height: 2),
                    Text(s.description,
                        style: const TextStyle(fontSize: 13, color: AppColors.inkSoft)),
                  ],
                ),
              ),
              const Icon(Icons.arrow_forward_ios, size: 14, color: AppColors.inkSoft),
            ],
          ),
        ),
      ),
    );
  }
}
