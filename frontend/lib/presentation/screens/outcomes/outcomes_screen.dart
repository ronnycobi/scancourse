import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:intl/intl.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/models/outcome_model.dart';
import '../../../providers/outcome_provider.dart';

final _zar = NumberFormat.currency(locale: 'en_ZA', symbol: 'R', decimalDigits: 0);

class OutcomesScreen extends ConsumerWidget {
  final int courseId;

  const OutcomesScreen({super.key, required this.courseId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final outcomeAsync = ref.watch(courseOutcomeProvider(courseId));

    return Scaffold(
      appBar: AppBar(title: const Text('Career Outcomes')),
      body: outcomeAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (outcome) {
          if (outcome == null) return const _NoDataView();
          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _HeaderCard(outcome: outcome),
                const SizedBox(height: 16),
                _EmploymentStatsCard(outcome: outcome),
                const SizedBox(height: 16),
                _SalaryTrajectoryCard(outcome: outcome),
                const SizedBox(height: 16),
                if (outcome.sectorBreakdown.isNotEmpty)
                  _SectorBreakdownCard(sectors: outcome.sectorBreakdown),
                const SizedBox(height: 16),
                if (outcome.jobRoles.isNotEmpty) _JobRolesCard(roles: outcome.jobRoles),
                const SizedBox(height: 16),
                if (outcome.topEmployers.isNotEmpty) _TopEmployersCard(employers: outcome.topEmployers),
                const SizedBox(height: 16),
                _DataSourcesCard(sources: outcome.sources, year: outcome.dataYear, cohortSize: outcome.cohortSize),
                const SizedBox(height: 24),
              ],
            ),
          );
        },
      ),
    );
  }
}

// ════════════════════════════════════════════════════════════════
// Header
// ════════════════════════════════════════════════════════════════

class _HeaderCard extends StatelessWidget {
  final OutcomeData outcome;
  const _HeaderCard({required this.outcome});

  Color get _employmentColor {
    switch (outcome.employmentLevel) {
      case 'excellent': return AppColors.secondary;
      case 'high': return AppColors.primary;
      case 'medium': return AppColors.accent;
      case 'low': return AppColors.error;
      default: return AppColors.textHint;
    }
  }

  @override
  Widget build(BuildContext context) {
    final rate = outcome.employmentRate12m ?? 0;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [_employmentColor.withOpacity(0.85), _employmentColor],
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
              const Icon(Icons.trending_up, color: Colors.white, size: 28),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  outcome.courseName,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: Colors.white, fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '${rate.toStringAsFixed(1)}%',
                style: Theme.of(context).textTheme.displayMedium?.copyWith(
                  color: Colors.white, fontWeight: FontWeight.w800, height: 1,
                ),
              ),
              const SizedBox(width: 8),
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Text(
                  'employed within 12 months',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.white70),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            outcome.institutionName ?? 'Based on national data',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.white60),
          ),
        ],
      ),
    );
  }
}

// ════════════════════════════════════════════════════════════════
// Employment stats
// ════════════════════════════════════════════════════════════════

class _EmploymentStatsCard extends StatelessWidget {
  final OutcomeData outcome;
  const _EmploymentStatsCard({required this.outcome});

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
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Employment breakdown', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 14),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            childAspectRatio: 2.4,
            mainAxisSpacing: 8,
            crossAxisSpacing: 8,
            children: [
              if (outcome.employmentRate6m != null)
                _StatTile(
                  icon: Icons.bolt,
                  color: AppColors.secondary,
                  label: '6 months',
                  value: '${outcome.employmentRate6m!.toStringAsFixed(0)}%',
                ),
              if (outcome.employmentRate12m != null)
                _StatTile(
                  icon: Icons.event,
                  color: AppColors.primary,
                  label: '12 months',
                  value: '${outcome.employmentRate12m!.toStringAsFixed(0)}%',
                ),
              if (outcome.avgTimeToFirstJobMonths != null)
                _StatTile(
                  icon: Icons.timer_outlined,
                  color: AppColors.accent,
                  label: 'Time to job',
                  value: '${outcome.avgTimeToFirstJobMonths}mo',
                ),
              if (outcome.fieldMatchRate != null)
                _StatTile(
                  icon: Icons.check_circle_outline,
                  color: AppColors.alternative,
                  label: 'In field',
                  value: '${outcome.fieldMatchRate!.toStringAsFixed(0)}%',
                ),
              if (outcome.furtherStudyRate != null)
                _StatTile(
                  icon: Icons.school_outlined,
                  color: AppColors.primary,
                  label: 'Postgrad',
                  value: '${outcome.furtherStudyRate!.toStringAsFixed(0)}%',
                ),
              if (outcome.jobSatisfactionScore != null)
                _StatTile(
                  icon: Icons.sentiment_satisfied_outlined,
                  color: AppColors.secondary,
                  label: 'Satisfaction',
                  value: '${outcome.jobSatisfactionScore!.toStringAsFixed(1)}/10',
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _StatTile extends StatelessWidget {
  final IconData icon;
  final Color color;
  final String label;
  final String value;

  const _StatTile({required this.icon, required this.color, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: TextStyle(fontSize: 11, color: color.withOpacity(0.85))),
                Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: color)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ════════════════════════════════════════════════════════════════
// Salary trajectory chart
// ════════════════════════════════════════════════════════════════

class _SalaryTrajectoryCard extends StatelessWidget {
  final OutcomeData outcome;
  const _SalaryTrajectoryCard({required this.outcome});

  @override
  Widget build(BuildContext context) {
    final entry = outcome.salaryEntryMedian?.toDouble() ?? 0;
    final five = outcome.salary5yrMedian?.toDouble() ?? 0;
    final ten = outcome.salary10yrMedian?.toDouble() ?? 0;

    if (entry == 0) return const SizedBox.shrink();

    final spots = <FlSpot>[
      FlSpot(0, entry),
      if (five > 0) FlSpot(5, five),
      if (ten > 0) FlSpot(10, ten),
    ];
    final maxY = (spots.map((s) => s.y).reduce((a, b) => a > b ? a : b) * 1.2);

    return Container(
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
              Text('Salary trajectory', style: Theme.of(context).textTheme.titleMedium),
              const Spacer(),
              Text(
                '${_zar.format(entry)} → ${_zar.format(ten == 0 ? five : ten)}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text('Monthly median, ZAR', style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 16),
          SizedBox(
            height: 180,
            child: LineChart(
              LineChartData(
                gridData: FlGridData(show: true, drawVerticalLine: false, horizontalInterval: maxY / 4),
                titlesData: FlTitlesData(
                  topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 30,
                      interval: 5,
                      getTitlesWidget: (v, _) => Padding(
                        padding: const EdgeInsets.only(top: 6),
                        child: Text(
                          v == 0 ? 'Entry' : '${v.toInt()}yr',
                          style: const TextStyle(color: AppColors.textSecondary, fontSize: 11),
                        ),
                      ),
                    ),
                  ),
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 50,
                      interval: maxY / 4,
                      getTitlesWidget: (v, _) => Text(
                        'R${(v / 1000).toStringAsFixed(0)}k',
                        style: const TextStyle(color: AppColors.textSecondary, fontSize: 10),
                      ),
                    ),
                  ),
                ),
                borderData: FlBorderData(show: false),
                minX: 0,
                maxX: 10,
                minY: 0,
                maxY: maxY,
                lineBarsData: [
                  LineChartBarData(
                    spots: spots,
                    isCurved: true,
                    color: AppColors.primary,
                    barWidth: 3,
                    isStrokeCapRound: true,
                    dotData: FlDotData(
                      show: true,
                      getDotPainter: (s, _, __, ___) => FlDotCirclePainter(
                        radius: 5, color: AppColors.primary, strokeWidth: 2, strokeColor: Colors.white,
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
          const SizedBox(height: 12),
          // Salary range table
          if (outcome.salaryEntryP25 != null && outcome.salaryEntryP75 != null) ...[
            const Divider(),
            const SizedBox(height: 8),
            Text('Entry-level range (25th–75th percentile)',
                style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 4),
            Text(
              '${_zar.format(outcome.salaryEntryP25)} – ${_zar.format(outcome.salaryEntryP75)} per month',
              style: Theme.of(context).textTheme.titleMedium,
            ),
          ],
        ],
      ),
    );
  }
}

// ════════════════════════════════════════════════════════════════
// Sector breakdown — horizontal bars
// ════════════════════════════════════════════════════════════════

class _SectorBreakdownCard extends StatelessWidget {
  final List<SectorBreakdown> sectors;
  const _SectorBreakdownCard({required this.sectors});

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
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Where graduates work', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 14),
          ...sectors.map((s) => Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(s.sectorEmoji, style: const TextStyle(fontSize: 18)),
                    const SizedBox(width: 8),
                    Expanded(child: Text(s.sectorName, style: Theme.of(context).textTheme.bodyMedium)),
                    Text('${s.percentage.toStringAsFixed(1)}%',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(color: AppColors.primary)),
                  ],
                ),
                const SizedBox(height: 4),
                LinearProgressIndicator(
                  value: s.percentage / 100,
                  minHeight: 6,
                  backgroundColor: AppColors.surface,
                  valueColor: const AlwaysStoppedAnimation(AppColors.primary),
                ),
              ],
            ),
          )),
        ],
      ),
    );
  }
}

// ════════════════════════════════════════════════════════════════
// Job roles
// ════════════════════════════════════════════════════════════════

class _JobRolesCard extends StatelessWidget {
  final List<JobRole> roles;
  const _JobRolesCard({required this.roles});

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
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Common job roles', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          ...roles.map((r) => Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 24, height: 24,
                        decoration: BoxDecoration(
                          color: AppColors.primaryLight,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        alignment: Alignment.center,
                        child: Text('${r.rank}',
                            style: const TextStyle(color: AppColors.primary, fontSize: 12, fontWeight: FontWeight.w700)),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(r.title, style: Theme.of(context).textTheme.titleMedium),
                      ),
                      if (r.medianMonthlySalaryZar != null)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: AppColors.secondaryLight,
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            '${_zar.format(r.medianMonthlySalaryZar)}/mo',
                            style: const TextStyle(color: AppColors.secondary, fontSize: 12, fontWeight: FontWeight.w600),
                          ),
                        ),
                    ],
                  ),
                  if (r.description.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Padding(
                      padding: const EdgeInsets.only(left: 34),
                      child: Text(r.description, style: Theme.of(context).textTheme.bodySmall),
                    ),
                  ],
                ],
              ),
            ),
          )),
        ],
      ),
    );
  }
}

// ════════════════════════════════════════════════════════════════
// Top employers
// ════════════════════════════════════════════════════════════════

class _TopEmployersCard extends StatelessWidget {
  final List<TopEmployer> employers;
  const _TopEmployersCard({required this.employers});

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
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Top hiring employers', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          Wrap(
            spacing: 10, runSpacing: 10,
            children: employers.map((e) => Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.border),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(e.name, style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600)),
                  if (e.isJseListed) ...[
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                      decoration: BoxDecoration(
                        color: AppColors.accentLight,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: const Text('JSE', style: TextStyle(color: AppColors.accent, fontSize: 9, fontWeight: FontWeight.w700)),
                    ),
                  ],
                ],
              ),
            )).toList(),
          ),
        ],
      ),
    );
  }
}

// ════════════════════════════════════════════════════════════════
// Data sources (trust signal)
// ════════════════════════════════════════════════════════════════

class _DataSourcesCard extends StatelessWidget {
  final List<DataSource> sources;
  final int year;
  final int? cohortSize;
  const _DataSourcesCard({required this.sources, required this.year, this.cohortSize});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.primaryLight,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.fact_check_outlined, size: 18, color: AppColors.primary),
              const SizedBox(width: 8),
              Text('Where this data comes from',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(color: AppColors.primary)),
            ],
          ),
          const SizedBox(height: 8),
          Text('Data year: $year${cohortSize != null ? "  ·  Sample: $cohortSize graduates" : ""}',
              style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 10),
          ...sources.map((s) => Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: GestureDetector(
              onTap: s.url != null ? () => launchUrl(Uri.parse(s.url!)) : null,
              child: Row(
                children: [
                  const Icon(Icons.link, size: 14, color: AppColors.primary),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      '${s.publisher} — ${s.name}',
                      style: TextStyle(
                        color: AppColors.primary,
                        fontSize: 12,
                        decoration: s.url != null ? TextDecoration.underline : null,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          )),
        ],
      ),
    );
  }
}

// ════════════════════════════════════════════════════════════════
// No data fallback
// ════════════════════════════════════════════════════════════════

class _NoDataView extends StatelessWidget {
  const _NoDataView();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.bar_chart_outlined, size: 72, color: AppColors.textHint),
            const SizedBox(height: 16),
            Text('Outcome data coming soon',
                style: Theme.of(context).textTheme.titleLarge, textAlign: TextAlign.center),
            const SizedBox(height: 8),
            Text(
              'We\'re collecting graduate destination and salary data for this course. Check back soon!',
              style: Theme.of(context).textTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
