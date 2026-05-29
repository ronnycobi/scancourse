import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/repositories/application_repository.dart';
import '../../../providers/application_provider.dart';
import '../../../providers/saved_provider.dart';

/// Kanban view of the user's applications.
///
/// 5 columns, swipe horizontally to flip between them:
///   Draft        — draft, in_progress
///   Submitted    — submitted, under_review, waitlisted
///   Offered      — conditional_offer, firm_offer
///   Accepted     — accepted
///   Closed       — rejected, withdrawn
///
/// Each card → tap-and-hold (or "..." menu) to move to a sibling column.
class ApplicationsKanbanScreen extends ConsumerStatefulWidget {
  const ApplicationsKanbanScreen({super.key});

  @override
  ConsumerState<ApplicationsKanbanScreen> createState() =>
      _ApplicationsKanbanScreenState();
}

class _ApplicationsKanbanScreenState
    extends ConsumerState<ApplicationsKanbanScreen> {
  late final PageController _pages;
  int _activeColumn = 0;

  static const _columns = <_KanbanColumn>[
    _KanbanColumn(
      key: 'draft',
      label: 'Draft',
      icon: Icons.edit_note_rounded,
      color: AppColors.textHint,
      statuses: ['draft', 'in_progress'],
    ),
    _KanbanColumn(
      key: 'submitted',
      label: 'Submitted',
      icon: Icons.send_outlined,
      color: AppColors.accent,
      statuses: ['submitted', 'under_review', 'waitlisted'],
    ),
    _KanbanColumn(
      key: 'offered',
      label: 'Offered',
      icon: Icons.workspace_premium_outlined,
      color: AppColors.secondary,
      statuses: ['conditional_offer', 'firm_offer'],
    ),
    _KanbanColumn(
      key: 'accepted',
      label: 'Accepted',
      icon: Icons.check_circle_outline,
      color: AppColors.eligible,
      statuses: ['accepted'],
    ),
    _KanbanColumn(
      key: 'closed',
      label: 'Closed',
      icon: Icons.archive_outlined,
      color: AppColors.error,
      statuses: ['rejected', 'withdrawn'],
    ),
  ];

  @override
  void initState() {
    super.initState();
    _pages = PageController();
  }

  @override
  void dispose() {
    _pages.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final appsAsync = ref.watch(applicationListProvider);
    final statsAsync = ref.watch(applicationStatsProvider);

    return Scaffold(
      backgroundColor: const Color(0xFFF2F4F7),
      appBar: AppBar(
        title: const Text('My Applications'),
        leading: BackButton(onPressed: () => context.pop()),
        backgroundColor: Colors.white,
        elevation: 0,
        scrolledUnderElevation: 0.5,
        actions: [
          IconButton(
            tooltip: 'Refresh',
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.invalidate(applicationListProvider);
              ref.invalidate(applicationStatsProvider);
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // ── Top stats row + column scroller ─────────────────────────
          Container(
            color: Colors.white,
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: statsAsync.when(
              loading: () => const SizedBox(height: 30),
              error: (_, __) => const SizedBox.shrink(),
              data: (s) => _StatStrip(stats: s),
            ),
          ),
          // ── Tab strip ───────────────────────────────────────────────
          Container(
            color: Colors.white,
            padding: const EdgeInsets.fromLTRB(8, 0, 8, 8),
            child: appsAsync.when(
              loading: () => const SizedBox(height: 56),
              error: (_, __) => const SizedBox(height: 56),
              data: (apps) => _ColumnTabBar(
                columns: _columns,
                activeIndex: _activeColumn,
                counts: {
                  for (final c in _columns)
                    c.key: apps
                        .where((a) => c.statuses.contains(a.status))
                        .length,
                },
                onTap: (i) {
                  setState(() => _activeColumn = i);
                  _pages.animateToPage(
                    i,
                    duration: const Duration(milliseconds: 240),
                    curve: Curves.easeOutCubic,
                  );
                },
              ),
            ),
          ),
          // Saved courses not yet tracked → prompt the student to start
          // tracking their progress.
          const _SavedCoursesPrompt(),
          const Divider(height: 1),
          Expanded(
            child: appsAsync.when(
              loading: () =>
                  const Center(child: CircularProgressIndicator()),
              error: (e, _) => _ErrorView(
                onRetry: () => ref.invalidate(applicationListProvider),
              ),
              data: (apps) {
                if (apps.isEmpty) return _EmptyView();
                return PageView.builder(
                  controller: _pages,
                  onPageChanged: (i) =>
                      setState(() => _activeColumn = i),
                  itemCount: _columns.length,
                  itemBuilder: (_, i) {
                    final col = _columns[i];
                    final items = apps
                        .where((a) => col.statuses.contains(a.status))
                        .toList();
                    return RefreshIndicator(
                      onRefresh: () async {
                        ref.invalidate(applicationListProvider);
                        ref.invalidate(applicationStatsProvider);
                      },
                      child: items.isEmpty
                          ? _ColumnEmptyView(column: col)
                          : ListView.builder(
                              padding: const EdgeInsets.fromLTRB(
                                  16, 14, 16, 24),
                              physics:
                                  const AlwaysScrollableScrollPhysics(),
                              itemCount: items.length,
                              itemBuilder: (_, idx) => Padding(
                                padding:
                                    const EdgeInsets.only(bottom: 12),
                                child: _ApplicationCard(
                                  app: items[idx],
                                  column: col,
                                  onChangeStatus: _showChangeStatusSheet,
                                ),
                              ),
                            ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _showChangeStatusSheet(ApplicationModel app) async {
    final picked = await showModalBottomSheet<String>(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 12),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: AppColors.border,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 20),
                  child: Text('Move to…',
                      style: TextStyle(
                          fontSize: 16, fontWeight: FontWeight.w800)),
                ),
                const SizedBox(height: 8),
                for (final s in const [
                  ('in_progress', 'In progress', Icons.edit_outlined),
                  ('submitted', 'Submitted', Icons.send_outlined),
                  ('under_review', 'Under review', Icons.hourglass_top),
                  ('conditional_offer', 'Conditional offer',
                      Icons.workspace_premium_outlined),
                  ('firm_offer', 'Firm offer', Icons.verified_outlined),
                  ('accepted', 'Accepted', Icons.check_circle_outline),
                  ('waitlisted', 'Waitlisted', Icons.access_time),
                  ('rejected', 'Rejected', Icons.cancel_outlined),
                  ('withdrawn', 'Withdrawn',
                      Icons.exit_to_app_outlined),
                ])
                  ListTile(
                    leading: Icon(s.$3,
                        color: app.status == s.$1
                            ? AppColors.primary
                            : AppColors.textSecondary),
                    title: Text(s.$2,
                        style: TextStyle(
                            color: app.status == s.$1
                                ? AppColors.primary
                                : AppColors.textPrimary,
                            fontWeight: app.status == s.$1
                                ? FontWeight.w700
                                : FontWeight.w500)),
                    trailing: app.status == s.$1
                        ? const Icon(Icons.check, color: AppColors.primary)
                        : null,
                    onTap: () => Navigator.pop(ctx, s.$1),
                  ),
                const SizedBox(height: 8),
              ],
            ),
          ),
        );
      },
    );
    if (picked == null || picked == app.status) return;
    try {
      await ref
          .read(applicationRepositoryProvider)
          .updateStatus(app.id, picked);
      ref.invalidate(applicationListProvider);
      ref.invalidate(applicationStatsProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
                'Moved "${app.courseName ?? app.institutionName}" to ${picked.replaceAll('_', ' ')}'),
            backgroundColor: AppColors.eligible,
          ),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Could not update status. Try again.'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }
}

// ── Models ────────────────────────────────────────────────────────────

class _KanbanColumn {
  final String key;
  final String label;
  final IconData icon;
  final Color color;
  final List<String> statuses;
  const _KanbanColumn({
    required this.key,
    required this.label,
    required this.icon,
    required this.color,
    required this.statuses,
  });
}

// ── Saved-courses → "track your progress" prompt ──────────────────────

/// Surfaces courses the student has saved but isn't tracking yet, nudging
/// them to start an application and report progress. Hides itself when
/// there's nothing to suggest.
class _SavedCoursesPrompt extends ConsumerWidget {
  const _SavedCoursesPrompt();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final saved = ref.watch(savedItemsProvider).valueOrNull ?? const [];
    final apps = ref.watch(applicationListProvider).valueOrNull ?? const [];
    final trackedCourseIds =
        apps.map((a) => a.courseId).whereType<int>().toSet();
    final suggestions = saved
        .where((s) =>
            s.itemType == 'course' && !trackedCourseIds.contains(s.itemId))
        .toList();
    if (suggestions.isEmpty) return const SizedBox.shrink();

    return Container(
      color: Colors.white,
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.bookmark_added_outlined,
                  size: 16, color: AppColors.primary),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  'Track your saved courses',
                  style: TextStyle(
                      fontSize: 12.5,
                      fontWeight: FontWeight.w800,
                      color: AppColors.textPrimary),
                ),
              ),
            ],
          ),
          const SizedBox(height: 2),
          const Text(
            'How are these going? Add one to track your progress.',
            style: TextStyle(fontSize: 11.5, color: AppColors.textSecondary),
          ),
          const SizedBox(height: 8),
          SizedBox(
            height: 64,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: suggestions.length,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (_, i) {
                final s = suggestions[i];
                return InkWell(
                  onTap: () => context.push('/courses/${s.itemId}'),
                  borderRadius: BorderRadius.circular(12),
                  child: Container(
                    width: 200,
                    padding: const EdgeInsets.symmetric(
                        horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: AppColors.primaryLight,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                          color: AppColors.primary.withOpacity(0.25)),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                s.itemName ?? 'Saved course',
                                style: const TextStyle(
                                    fontSize: 12.5,
                                    fontWeight: FontWeight.w700,
                                    color: AppColors.textPrimary),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                              if (s.itemSubtitle != null)
                                Text(
                                  s.itemSubtitle!,
                                  style: const TextStyle(
                                      fontSize: 11,
                                      color: AppColors.textSecondary),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                            ],
                          ),
                        ),
                        const Icon(Icons.add_circle_outline,
                            size: 20, color: AppColors.primary),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

// ── Top stats strip ──────────────────────────────────────────────────

class _StatStrip extends StatelessWidget {
  final ApplicationStats stats;
  const _StatStrip({required this.stats});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _StatPill(
            label: 'Total',
            value: stats.total,
            color: AppColors.primary,
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _StatPill(
            label: 'Offers',
            value: stats.offers,
            color: AppColors.eligible,
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _StatPill(
            label: 'Closing ≤14d',
            value: stats.closingSoon,
            color: AppColors.error,
          ),
        ),
      ],
    );
  }
}

class _StatPill extends StatelessWidget {
  final String label;
  final int value;
  final Color color;
  const _StatPill(
      {required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.10),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text('$value',
              style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                  color: color,
                  height: 1.1)),
          const SizedBox(width: 6),
          Flexible(
            child: Text(label,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: color)),
          ),
        ],
      ),
    );
  }
}

// ── Tab bar — horizontally scrollable column selector ───────────────

class _ColumnTabBar extends StatelessWidget {
  final List<_KanbanColumn> columns;
  final int activeIndex;
  final Map<String, int> counts;
  final void Function(int) onTap;
  const _ColumnTabBar({
    required this.columns,
    required this.activeIndex,
    required this.counts,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: List.generate(columns.length, (i) {
          final c = columns[i];
          final isActive = i == activeIndex;
          final count = counts[c.key] ?? 0;
          return GestureDetector(
            onTap: () => onTap(i),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 160),
              margin: const EdgeInsets.symmetric(horizontal: 4),
              padding: const EdgeInsets.symmetric(
                  horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: isActive
                    ? c.color.withOpacity(0.14)
                    : Colors.transparent,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: isActive ? c.color : AppColors.border,
                  width: 1,
                ),
              ),
              child: Row(
                children: [
                  Icon(c.icon,
                      size: 16,
                      color: isActive ? c.color : AppColors.textSecondary),
                  const SizedBox(width: 6),
                  Text(c.label,
                      style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: isActive
                              ? c.color
                              : AppColors.textSecondary)),
                  const SizedBox(width: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: isActive ? c.color : AppColors.border,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      '$count',
                      style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                          color: isActive
                              ? Colors.white
                              : AppColors.textSecondary),
                    ),
                  ),
                ],
              ),
            ),
          );
        }),
      ),
    );
  }
}

// ── Card ────────────────────────────────────────────────────────────

class _ApplicationCard extends StatelessWidget {
  final ApplicationModel app;
  final _KanbanColumn column;
  final Future<void> Function(ApplicationModel) onChangeStatus;
  const _ApplicationCard({
    required this.app,
    required this.column,
    required this.onChangeStatus,
  });

  int? get _daysUntilDeadline {
    if (app.deadline == null) return null;
    final d = DateTime.tryParse(app.deadline!);
    if (d == null) return null;
    return d.difference(DateTime.now()).inDays;
  }

  String get _statusLabel => app.status
      .split('_')
      .map((p) => p.isEmpty ? p : '${p[0].toUpperCase()}${p.substring(1)}')
      .join(' ');

  @override
  Widget build(BuildContext context) {
    final days = _daysUntilDeadline;
    final urgent = days != null && days >= 0 && days <= 7;
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: () => onChangeStatus(app),
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.border),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.025),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 4,
                    height: 36,
                    decoration: BoxDecoration(
                      color: column.color,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          app.courseName ?? 'General application',
                          style: const TextStyle(
                              fontSize: 14.5,
                              fontWeight: FontWeight.w800,
                              height: 1.2),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 2),
                        Text(
                          app.institutionName,
                          style: const TextStyle(
                              fontSize: 12,
                              color: AppColors.textSecondary),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  if (app.isPriority)
                    const Icon(Icons.star_rounded,
                        color: AppColors.accent, size: 18),
                ],
              ),
              const SizedBox(height: 12),
              // Status pill + days-left badge
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: column.color.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(_statusLabel,
                        style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w800,
                            color: column.color)),
                  ),
                  const Spacer(),
                  if (days != null && app.status != 'accepted' &&
                      app.status != 'rejected' && app.status != 'withdrawn')
                    Row(
                      children: [
                        Icon(
                            urgent
                                ? Icons.warning_amber_rounded
                                : Icons.event_outlined,
                            size: 12,
                            color: urgent
                                ? AppColors.error
                                : AppColors.textHint),
                        const SizedBox(width: 4),
                        Text(
                          days < 0
                              ? 'Closed'
                              : days == 0
                                  ? 'Closes today'
                                  : '${days}d left',
                          style: TextStyle(
                              fontSize: 11,
                              fontWeight:
                                  urgent ? FontWeight.w800 : FontWeight.w600,
                              color: urgent
                                  ? AppColors.error
                                  : AppColors.textSecondary),
                        ),
                      ],
                    ),
                ],
              ),
              const SizedBox(height: 10),
              // Progress
              ClipRRect(
                borderRadius: BorderRadius.circular(20),
                child: LinearProgressIndicator(
                  value: app.progress / 100,
                  backgroundColor: AppColors.surface,
                  valueColor:
                      AlwaysStoppedAnimation<Color>(column.color),
                  minHeight: 5,
                ),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Text(
                    '${app.progress}% complete',
                    style: const TextStyle(
                        fontSize: 10,
                        color: AppColors.textHint,
                        fontWeight: FontWeight.w600),
                  ),
                  const Spacer(),
                  TextButton.icon(
                    onPressed: () => onChangeStatus(app),
                    icon: Icon(Icons.swap_horiz_rounded,
                        size: 14, color: column.color),
                    label: Text('Move',
                        style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w800,
                            color: column.color)),
                    style: TextButton.styleFrom(
                      minimumSize: Size.zero,
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 4),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Empty states ─────────────────────────────────────────────────────

class _ColumnEmptyView extends StatelessWidget {
  final _KanbanColumn column;
  const _ColumnEmptyView({required this.column});

  @override
  Widget build(BuildContext context) {
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(40),
      children: [
        const SizedBox(height: 80),
        Center(
          child: Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              color: column.color.withOpacity(0.12),
              shape: BoxShape.circle,
            ),
            child: Icon(column.icon, color: column.color, size: 36),
          ),
        ),
        const SizedBox(height: 16),
        Text('No applications in ${column.label}',
            textAlign: TextAlign.center,
            style: const TextStyle(
                fontSize: 16, fontWeight: FontWeight.w700)),
        const SizedBox(height: 6),
        const Text(
          'Move an application here from another column to track progress.',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
        ),
      ],
    );
  }
}

class _EmptyView extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.assignment_outlined,
                size: 64, color: AppColors.textHint),
            const SizedBox(height: 12),
            const Text('No applications yet',
                style: TextStyle(
                    fontSize: 16, fontWeight: FontWeight.w700)),
            const SizedBox(height: 6),
            const Text(
              'Save a course or bursary, then mark it as an application here to track progress.',
              textAlign: TextAlign.center,
              style: TextStyle(
                  fontSize: 12, color: AppColors.textSecondary),
            ),
            const SizedBox(height: 18),
            ElevatedButton.icon(
              onPressed: () => context.push('/courses'),
              icon: const Icon(Icons.search, size: 16),
              label: const Text('Browse courses'),
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
            const Text('Could not load your applications'),
            const SizedBox(height: 12),
            OutlinedButton(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }
}
