import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../providers/aps_provider.dart';

/// AI-generated 3-action plan for closing the user's APS gaps.
/// Calls /api/v1/ocr/improvement-plan/ which uses Gemini grounded in the
/// user's actual subject marks + saved courses + dream career.
class ImprovementPlanScreen extends ConsumerStatefulWidget {
  const ImprovementPlanScreen({super.key});

  @override
  ConsumerState<ImprovementPlanScreen> createState() =>
      _ImprovementPlanScreenState();
}

class _ImprovementPlanScreenState
    extends ConsumerState<ImprovementPlanScreen> {
  late Future<Map<String, dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = ref.read(ocrRepositoryProvider).getImprovementPlan();
  }

  void _refresh() {
    setState(() {
      _future = ref.read(ocrRepositoryProvider).getImprovementPlan();
    });
  }

  static const _palette = [
    AppColors.eligible,
    AppColors.primary,
    AppColors.accent,
  ];
  static const _icons = [
    Icons.bolt_outlined,
    Icons.trending_up,
    Icons.alt_route_outlined,
  ];

  /// Title flips based on the grade returned by the API:
  ///   grade_10/11 → "My Improvement Path"  (lift your marks before matric)
  ///   grade_12/gap_year/other → "My Next Steps"  (marks locked, apply now)
  ///   unknown → "My Plan"  (neutral)
  static String _titleFor(String grade) {
    if (grade == 'grade_10' || grade == 'grade_11') return 'My Improvement Path';
    if (grade == 'grade_12' || grade == 'gap_year' || grade == 'other') {
      return 'My Next Steps';
    }
    return 'My Plan';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: FutureBuilder<Map<String, dynamic>>(
          future: _future,
          builder: (_, snap) {
            final grade = ((snap.data?['grade']) as String?) ?? '';
            return Text(_titleFor(grade));
          },
        ),
        leading: BackButton(onPressed: () => context.pop()),
        actions: [
          IconButton(
            tooltip: 'Regenerate',
            icon: const Icon(Icons.refresh),
            onPressed: _refresh,
          ),
        ],
      ),
      body: SafeArea(
        child: FutureBuilder<Map<String, dynamic>>(
          future: _future,
          builder: (ctx, snap) {
            if (snap.connectionState != ConnectionState.done) {
              return const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.auto_awesome,
                        color: AppColors.primary, size: 36),
                    SizedBox(height: 12),
                    CircularProgressIndicator(strokeWidth: 3),
                    SizedBox(height: 16),
                    Text('Building your plan with AI…'),
                    SizedBox(height: 4),
                    Text('This takes about 5 seconds.',
                        style: TextStyle(
                            color: AppColors.textHint, fontSize: 12)),
                  ],
                ),
              );
            }
            if (snap.hasError) {
              return Center(
                child: Padding(
                  padding: const EdgeInsets.all(32),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.document_scanner_outlined,
                          size: 56, color: AppColors.textHint),
                      const SizedBox(height: 12),
                      Text('No APS yet',
                          style: Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: 8),
                      const Text(
                        'Scan or enter your marks first — then we can build a personalised plan.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: AppColors.textSecondary),
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () => context.push('/scanner'),
                        child: const Text('Scan Report Card'),
                      ),
                    ],
                  ),
                ),
              );
            }
            final data = snap.data!;
            final aps = (data['total_aps'] as num?)?.toInt() ?? 0;
            final plan = Map<String, dynamic>.from(
                data['plan'] as Map? ?? const {});
            final summary = (plan['summary'] as String?) ?? '';
            final actions =
                ((plan['actions'] as List?) ?? const []).cast<Map>();

            return ListView(
              padding: const EdgeInsets.all(20),
              children: [
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [AppColors.primary, AppColors.primaryDark],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.auto_awesome,
                              color: Colors.white, size: 22),
                          const SizedBox(width: 8),
                          const Text(
                            'Your AI Coach',
                            style: TextStyle(
                                color: Colors.white,
                                fontSize: 14,
                                fontWeight: FontWeight.w700),
                          ),
                          const Spacer(),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.18),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Text(
                              'APS $aps',
                              style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w700),
                            ),
                          ),
                        ],
                      ),
                      if (summary.isNotEmpty) ...[
                        const SizedBox(height: 12),
                        Text(summary,
                            style: const TextStyle(
                                color: Colors.white,
                                fontSize: 15,
                                height: 1.45)),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                if (actions.isEmpty)
                  Padding(
                    padding: const EdgeInsets.all(20),
                    child: Text(
                      'AI coach is offline right now — please try again later.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: AppColors.textSecondary),
                    ),
                  ),
                ...actions.asMap().entries.map((entry) {
                  final i = entry.key;
                  final a = Map<String, dynamic>.from(entry.value);
                  final color = _palette[i % _palette.length];
                  final icon = _icons[i % _icons.length];
                  return _ActionCard(
                    index: i + 1,
                    icon: icon,
                    color: color,
                    title: (a['title'] as String?) ?? '',
                    description: (a['description'] as String?) ?? '',
                    impact: (a['impact'] as String?) ?? '',
                  );
                }),
                const SizedBox(height: 24),
                const Text(
                  'AI suggestions are estimates. Always verify subject requirements with the university you\'re applying to.',
                  style: TextStyle(
                      fontSize: 11,
                      color: AppColors.textHint,
                      fontStyle: FontStyle.italic),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _ActionCard extends StatelessWidget {
  final int index;
  final IconData icon;
  final Color color;
  final String title;
  final String description;
  final String impact;

  const _ActionCard({
    required this.index,
    required this.icon,
    required this.color,
    required this.title,
    required this.description,
    required this.impact,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icon, color: color, size: 20),
              ),
              const SizedBox(width: 10),
              Text('Step $index',
                  style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: color,
                      letterSpacing: 0.5)),
              const Spacer(),
              if (impact.isNotEmpty)
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    impact,
                    style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: color),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            title,
            style: const TextStyle(
                fontSize: 15, fontWeight: FontWeight.w700, height: 1.3),
          ),
          const SizedBox(height: 4),
          Text(
            description,
            style: const TextStyle(
                fontSize: 13, color: AppColors.textSecondary, height: 1.5),
          ),
        ],
      ),
    );
  }
}
