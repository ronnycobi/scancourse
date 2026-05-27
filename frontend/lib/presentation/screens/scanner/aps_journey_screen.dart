import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../providers/aps_provider.dart';

/// Visualises the user's APS growth over time. Hero number, gradient
/// growth banner, line chart, top-3 subject movers, "courses unlocked"
/// celebration.
class ApsJourneyScreen extends ConsumerStatefulWidget {
  const ApsJourneyScreen({super.key});

  @override
  ConsumerState<ApsJourneyScreen> createState() => _ApsJourneyScreenState();
}

class _ApsJourneyScreenState extends ConsumerState<ApsJourneyScreen> {
  late Future<Map<String, dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = ref.read(ocrRepositoryProvider).getApsJourney();
  }

  void _refresh() {
    setState(() {
      _future = ref.read(ocrRepositoryProvider).getApsJourney();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF2F4F7),
      appBar: AppBar(
        title: const Text('My APS Journey'),
        leading: BackButton(onPressed: () => context.pop()),
        actions: [
          IconButton(
            tooltip: 'Refresh',
            icon: const Icon(Icons.refresh),
            onPressed: _refresh,
          ),
        ],
      ),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (ctx, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError || !snap.hasData) {
            return _ErrorView(onRetry: _refresh);
          }
          final data = snap.data!;
          final currentAps = (data['current_aps'] as num?)?.toInt() ?? 0;
          if (currentAps == 0) return _EmptyView();
          final growth = (data['growth'] as Map?)?.cast<String, dynamic>();
          final timeline = ((data['timeline'] as List?) ?? const [])
              .cast<Map>()
              .map((m) => m.cast<String, dynamic>())
              .toList();
          final movers = ((data['subject_movers'] as List?) ?? const [])
              .cast<Map>()
              .map((m) => m.cast<String, dynamic>())
              .toList();
          final unlocked =
              (data['courses_unlocked'] as Map?)?.cast<String, dynamic>();

          return RefreshIndicator(
            onRefresh: () async => _refresh(),
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
              children: [
                _HeroCard(currentAps: currentAps, growth: growth),
                const SizedBox(height: 16),
                if (timeline.length >= 2)
                  _ChartCard(timeline: timeline),
                if (timeline.length >= 2) const SizedBox(height: 16),
                if (movers.isNotEmpty) _MoversCard(movers: movers),
                if (movers.isNotEmpty) const SizedBox(height: 16),
                if (unlocked != null && (unlocked['delta'] as int? ?? 0) > 0)
                  _UnlockedCard(unlocked: unlocked),
                if (unlocked != null) const SizedBox(height: 16),
                _CtaCard(),
                const SizedBox(height: 12),
                const Center(
                  child: Text(
                    'Scans build your APS history — the more you upload, the better.',
                    style: TextStyle(
                        fontSize: 11,
                        color: AppColors.textHint,
                        fontStyle: FontStyle.italic),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

// ── Hero ────────────────────────────────────────────────────────────

class _HeroCard extends StatelessWidget {
  final int currentAps;
  final Map<String, dynamic>? growth;
  const _HeroCard({required this.currentAps, required this.growth});

  @override
  Widget build(BuildContext context) {
    final delta = (growth?['delta'] as int?) ?? 0;
    final positive = delta > 0;
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 22),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.primary, AppColors.primaryDark],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withOpacity(0.25),
            blurRadius: 14,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Your current APS',
              style: TextStyle(
                  color: Colors.white70,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 0.5)),
          const SizedBox(height: 6),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '$currentAps',
                style: const TextStyle(
                    color: Colors.white,
                    fontSize: 56,
                    fontWeight: FontWeight.w900,
                    height: 1),
              ),
              const SizedBox(width: 6),
              const Padding(
                padding: EdgeInsets.only(bottom: 12),
                child: Text('/42',
                    style: TextStyle(
                        color: Colors.white70,
                        fontSize: 18,
                        fontWeight: FontWeight.w700)),
              ),
              const Spacer(),
              if (growth != null && delta != 0)
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: positive
                        ? Colors.white.withOpacity(0.2)
                        : AppColors.error.withOpacity(0.7),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                        color: Colors.white.withOpacity(0.35)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                          positive
                              ? Icons.trending_up_rounded
                              : Icons.trending_down_rounded,
                          color: Colors.white,
                          size: 14),
                      const SizedBox(width: 4),
                      Text(
                        growth!['delta_label'] as String,
                        style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.w800),
                      ),
                    ],
                  ),
                ),
            ],
          ),
          if (growth != null && delta > 0) ...[
            const SizedBox(height: 10),
            Text(
              'Up $delta APS since your first scan. 🎉',
              style: const TextStyle(color: Colors.white70, fontSize: 13),
            ),
          ] else if (growth == null) ...[
            const SizedBox(height: 10),
            const Text(
              'Scan another report to start tracking your improvement.',
              style: TextStyle(color: Colors.white70, fontSize: 13),
            ),
          ],
        ],
      ),
    );
  }
}

// ── Line chart ───────────────────────────────────────────────────────

class _ChartCard extends StatelessWidget {
  final List<Map<String, dynamic>> timeline;
  const _ChartCard({required this.timeline});

  @override
  Widget build(BuildContext context) {
    final spots = <FlSpot>[];
    for (int i = 0; i < timeline.length; i++) {
      final aps = (timeline[i]['total_aps'] as num?)?.toDouble() ?? 0;
      spots.add(FlSpot(i.toDouble(), aps));
    }
    final maxAps = spots.map((s) => s.y).reduce((a, b) => a > b ? a : b);
    final minAps = spots.map((s) => s.y).reduce((a, b) => a < b ? a : b);

    return Container(
      padding: const EdgeInsets.fromLTRB(20, 18, 16, 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.show_chart_rounded,
                  color: AppColors.primary, size: 20),
              const SizedBox(width: 8),
              const Text('Your APS over time',
                  style: TextStyle(
                      fontSize: 15, fontWeight: FontWeight.w800)),
              const Spacer(),
              Text('${timeline.length} scans',
                  style: const TextStyle(
                      fontSize: 11,
                      color: AppColors.textHint,
                      fontWeight: FontWeight.w600)),
            ],
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 180,
            child: LineChart(
              LineChartData(
                minY: (minAps - 2).clamp(0, 42).toDouble(),
                maxY: (maxAps + 2).clamp(0, 42).toDouble(),
                gridData: FlGridData(
                  drawVerticalLine: false,
                  horizontalInterval: 4,
                  getDrawingHorizontalLine: (_) => FlLine(
                      color: AppColors.border, strokeWidth: 1, dashArray: [4, 4]),
                ),
                borderData: FlBorderData(show: false),
                titlesData: FlTitlesData(
                  show: true,
                  topTitles: const AxisTitles(),
                  rightTitles: const AxisTitles(),
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 28,
                      interval: 4,
                      getTitlesWidget: (v, _) => Text(
                        v.toInt().toString(),
                        style: const TextStyle(
                            fontSize: 10, color: AppColors.textSecondary),
                      ),
                    ),
                  ),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 22,
                      interval: 1,
                      getTitlesWidget: (v, _) {
                        final i = v.toInt();
                        if (i < 0 || i >= timeline.length) {
                          return const SizedBox.shrink();
                        }
                        // Show short date "5 Mar"
                        final raw = timeline[i]['date'] as String?;
                        final d = raw != null ? DateTime.tryParse(raw) : null;
                        if (d == null) return const SizedBox.shrink();
                        const months = [
                          '',
                          'Jan',
                          'Feb',
                          'Mar',
                          'Apr',
                          'May',
                          'Jun',
                          'Jul',
                          'Aug',
                          'Sep',
                          'Oct',
                          'Nov',
                          'Dec'
                        ];
                        return Padding(
                          padding: const EdgeInsets.only(top: 6),
                          child: Text('${d.day} ${months[d.month]}',
                              style: const TextStyle(
                                  fontSize: 10,
                                  color: AppColors.textSecondary)),
                        );
                      },
                    ),
                  ),
                ),
                lineBarsData: [
                  LineChartBarData(
                    spots: spots,
                    isCurved: true,
                    curveSmoothness: 0.35,
                    color: AppColors.primary,
                    barWidth: 3,
                    dotData: FlDotData(
                      show: true,
                      getDotPainter: (spot, _, __, ___) =>
                          FlDotCirclePainter(
                        radius: 4,
                        color: AppColors.primary,
                        strokeWidth: 2,
                        strokeColor: Colors.white,
                      ),
                    ),
                    belowBarData: BarAreaData(
                      show: true,
                      color: AppColors.primary.withOpacity(0.12),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Subject movers ─────────────────────────────────────────────────

class _MoversCard extends StatelessWidget {
  final List<Map<String, dynamic>> movers;
  const _MoversCard({required this.movers});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.trending_up_rounded,
                  color: AppColors.eligible, size: 20),
              SizedBox(width: 8),
              Text('Biggest improvements',
                  style: TextStyle(
                      fontSize: 15, fontWeight: FontWeight.w800)),
            ],
          ),
          const SizedBox(height: 12),
          ...movers.map((m) {
            final subject = (m['subject'] as String?) ?? '';
            final oldMark = (m['old_mark'] as num?)?.toInt() ?? 0;
            final newMark = (m['new_mark'] as num?)?.toInt() ?? 0;
            final delta = (m['delta'] as num?)?.toInt() ?? 0;
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 6),
              child: Row(
                children: [
                  Expanded(
                    flex: 3,
                    child: Text(
                      subject,
                      style: const TextStyle(
                          fontWeight: FontWeight.w700, fontSize: 14),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  Expanded(
                    flex: 4,
                    child: Row(
                      children: [
                        Text('$oldMark%',
                            style: const TextStyle(
                                color: AppColors.textHint,
                                decoration: TextDecoration.lineThrough,
                                fontSize: 13)),
                        const SizedBox(width: 8),
                        const Icon(Icons.arrow_forward_rounded,
                            size: 13, color: AppColors.textHint),
                        const SizedBox(width: 8),
                        Text('$newMark%',
                            style: const TextStyle(
                                fontWeight: FontWeight.w800,
                                fontSize: 14,
                                color: AppColors.textPrimary)),
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppColors.eligible.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text('+$delta%',
                        style: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w800,
                            color: AppColors.eligible)),
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}

// ── Courses unlocked ───────────────────────────────────────────────

class _UnlockedCard extends StatelessWidget {
  final Map<String, dynamic> unlocked;
  const _UnlockedCard({required this.unlocked});

  @override
  Widget build(BuildContext context) {
    final delta = (unlocked['delta'] as num?)?.toInt() ?? 0;
    final latestCount = (unlocked['latest_count'] as num?)?.toInt() ?? 0;
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.eligible, AppColors.secondary],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        children: [
          const Icon(Icons.celebration_rounded,
              color: Colors.white, size: 40),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('+$delta courses unlocked',
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 17,
                        fontWeight: FontWeight.w900)),
                const SizedBox(height: 2),
                Text(
                  'Your higher APS now qualifies you for $latestCount programmes.',
                  style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      height: 1.4),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── CTA ────────────────────────────────────────────────────────────

class _CtaCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          Row(
            children: const [
              Icon(Icons.bolt, color: AppColors.accent, size: 22),
              SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Want to push your APS higher?',
                  style: TextStyle(
                      fontSize: 14, fontWeight: FontWeight.w700),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => context.push('/improvement-plan'),
                  icon: const Icon(Icons.psychology_alt_outlined, size: 16),
                  label: const Text('AI plan'),
                  style: OutlinedButton.styleFrom(
                    minimumSize: const Size(0, 44),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => context.push('/scanner'),
                  icon: const Icon(Icons.add_a_photo_outlined, size: 16),
                  label: const Text('Scan again'),
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(0, 44),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Empty / error views ────────────────────────────────────────────

class _EmptyView extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.show_chart_rounded,
                size: 64, color: AppColors.textHint),
            const SizedBox(height: 12),
            Text('No APS journey yet',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            const Text(
              'Scan your first report card to start tracking your improvement.',
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
}

class _ErrorView extends StatelessWidget {
  final VoidCallback onRetry;
  const _ErrorView({required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.wifi_off_outlined,
                size: 48, color: AppColors.textHint),
            const SizedBox(height: 12),
            const Text('Could not load your APS journey'),
            const SizedBox(height: 12),
            OutlinedButton(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }
}
