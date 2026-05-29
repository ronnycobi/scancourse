import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/repositories/application_repository.dart';
import '../../../providers/application_provider.dart';

class ApplicationsScreen extends ConsumerWidget {
  const ApplicationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final apps = ref.watch(applicationListProvider);
    final stats = ref.watch(applicationStatsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Applications'),
        leading: BackButton(onPressed: () => context.pop()),
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(applicationListProvider);
          ref.invalidate(applicationStatsProvider);
        },
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            stats.when(
              loading: () => const SizedBox(height: 84),
              error: (_, __) => const SizedBox.shrink(),
              data: (s) => _StatsRow(stats: s),
            ),
            const SizedBox(height: 16),
            apps.when(
              loading: () => const Padding(
                padding: EdgeInsets.all(40),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (e, _) => Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    const Icon(Icons.wifi_off_outlined,
                        size: 48, color: AppColors.textHint),
                    const SizedBox(height: 12),
                    const Text('Could not load applications'),
                    const SizedBox(height: 12),
                    OutlinedButton(
                      onPressed: () =>
                          ref.invalidate(applicationListProvider),
                      child: const Text('Retry'),
                    ),
                  ],
                ),
              ),
              data: (items) {
                if (items.isEmpty) {
                  return Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      children: [
                        const Icon(Icons.assignment_outlined,
                            size: 56, color: AppColors.textHint),
                        const SizedBox(height: 16),
                        Text('No applications yet',
                            style:
                                Theme.of(context).textTheme.titleMedium),
                        const SizedBox(height: 8),
                        const Padding(
                          padding: EdgeInsets.symmetric(horizontal: 24),
                          child: Text(
                            'When you start applying to courses or bursaries, mark them here to track deadlines and status.',
                            textAlign: TextAlign.center,
                            style:
                                TextStyle(color: AppColors.textSecondary),
                          ),
                        ),
                        const SizedBox(height: 16),
                        ElevatedButton(
                          // /courses is a ShellRoute branch — go(), not push().
                          onPressed: () => context.go('/courses'),
                          child: const Text('Browse Courses'),
                        ),
                      ],
                    ),
                  );
                }
                return Column(
                  children: items
                      .map((a) => _ApplicationCard(app: a))
                      .toList(),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _StatsRow extends StatelessWidget {
  final ApplicationStats stats;
  const _StatsRow({required this.stats});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          _StatChip(label: 'Total', value: stats.total, color: AppColors.primary),
          const SizedBox(width: 8),
          _StatChip(
              label: 'In progress',
              value: stats.inProgress,
              color: AppColors.accent),
          const SizedBox(width: 8),
          _StatChip(
              label: 'Submitted',
              value: stats.submitted,
              color: AppColors.secondary),
          const SizedBox(width: 8),
          _StatChip(
              label: 'Offers',
              value: stats.offers,
              color: AppColors.eligible),
          const SizedBox(width: 8),
          _StatChip(
              label: 'Closing ≤14d',
              value: stats.closingSoon,
              color: AppColors.error),
        ],
      ),
    );
  }
}

class _StatChip extends StatelessWidget {
  final String label;
  final int value;
  final Color color;
  const _StatChip(
      {required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withOpacity(0.25)),
      ),
      child: Row(
        children: [
          Text('$value',
              style: TextStyle(
                  fontSize: 18, fontWeight: FontWeight.w800, color: color)),
          const SizedBox(width: 6),
          Text(label,
              style: TextStyle(
                  fontSize: 12, fontWeight: FontWeight.w600, color: color)),
        ],
      ),
    );
  }
}

class _ApplicationCard extends ConsumerWidget {
  final ApplicationModel app;
  const _ApplicationCard({required this.app});

  Color get _statusColor {
    switch (app.status) {
      case 'accepted':
      case 'firm_offer':
        return AppColors.eligible;
      case 'conditional_offer':
      case 'submitted':
      case 'under_review':
        return AppColors.secondary;
      case 'rejected':
      case 'withdrawn':
        return AppColors.error;
      case 'in_progress':
      case 'draft':
      default:
        return AppColors.accent;
    }
  }

  String get _statusLabel {
    return app.status
        .split('_')
        .map((p) => p.isEmpty ? p : '${p[0].toUpperCase()}${p.substring(1)}')
        .join(' ');
  }

  int? get _daysUntilDeadline {
    if (app.deadline == null) return null;
    final d = DateTime.tryParse(app.deadline!);
    if (d == null) return null;
    return d.difference(DateTime.now()).inDays;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final days = _daysUntilDeadline;
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  app.courseName ?? 'General application',
                  style: const TextStyle(
                      fontSize: 15, fontWeight: FontWeight.w700),
                ),
              ),
              if (app.isPriority)
                const Icon(Icons.star_rounded,
                    color: AppColors.accent, size: 18),
            ],
          ),
          const SizedBox(height: 4),
          Text(app.institutionName,
              style: const TextStyle(
                  fontSize: 13, color: AppColors.textSecondary)),
          const SizedBox(height: 10),
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: _statusColor.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(_statusLabel,
                    style: TextStyle(
                        color: _statusColor,
                        fontSize: 11,
                        fontWeight: FontWeight.w600)),
              ),
              const SizedBox(width: 8),
              if (days != null)
                Text(
                  days < 0
                      ? 'Closed'
                      : days == 0
                          ? 'Closes today'
                          : days <= 14
                              ? '$days days left'
                              : 'Closes ${app.deadline}',
                  style: TextStyle(
                    fontSize: 12,
                    color: days <= 7 && days >= 0
                        ? AppColors.error
                        : AppColors.textSecondary,
                    fontWeight: days <= 7 && days >= 0
                        ? FontWeight.w600
                        : FontWeight.normal,
                  ),
                ),
              const Spacer(),
              IconButton(
                visualDensity: VisualDensity.compact,
                icon: const Icon(Icons.more_horiz, size: 20),
                onPressed: () => _showActions(context, ref),
              ),
            ],
          ),
          LinearProgressIndicator(
            value: app.progress / 100,
            backgroundColor: AppColors.surface,
            valueColor: AlwaysStoppedAnimation<Color>(_statusColor),
            minHeight: 4,
          ),
        ],
      ),
    );
  }

  void _showActions(BuildContext context, WidgetRef ref) {
    showModalBottomSheet<void>(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const SizedBox(height: 8),
              Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: AppColors.border,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 12),
              for (final s in const [
                ('in_progress', 'Mark as In Progress'),
                ('submitted', 'Mark as Submitted'),
                ('accepted', 'Mark as Accepted'),
                ('rejected', 'Mark as Rejected'),
                ('withdrawn', 'Withdraw'),
              ])
                ListTile(
                  title: Text(s.$2),
                  onTap: () async {
                    Navigator.of(ctx).pop();
                    try {
                      await ref
                          .read(applicationRepositoryProvider)
                          .updateStatus(app.id, s.$1);
                      ref.invalidate(applicationListProvider);
                      ref.invalidate(applicationStatsProvider);
                    } catch (_) {}
                  },
                ),
              const Divider(height: 1),
              ListTile(
                leading:
                    const Icon(Icons.delete_outline, color: AppColors.error),
                title: const Text('Delete',
                    style: TextStyle(color: AppColors.error)),
                onTap: () async {
                  Navigator.of(ctx).pop();
                  try {
                    await ref
                        .read(applicationRepositoryProvider)
                        .delete(app.id);
                    ref.invalidate(applicationListProvider);
                    ref.invalidate(applicationStatsProvider);
                  } catch (_) {}
                },
              ),
            ],
          ),
        );
      },
    );
  }
}
