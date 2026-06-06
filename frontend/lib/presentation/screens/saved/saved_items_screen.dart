import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/repositories/application_repository.dart';
import '../../../data/repositories/saved_repository.dart';
import '../../../providers/application_provider.dart';
import '../../../providers/saved_provider.dart';

class SavedItemsScreen extends ConsumerStatefulWidget {
  const SavedItemsScreen({super.key});

  @override
  ConsumerState<SavedItemsScreen> createState() => _SavedItemsScreenState();
}

class _SavedItemsScreenState extends ConsumerState<SavedItemsScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tab;
  static const _types = ['course', 'bursary', 'accommodation'];
  static const _labels = ['Courses', 'Bursaries', 'Accommodation'];

  @override
  void initState() {
    super.initState();
    _tab = TabController(length: _types.length, vsync: this);
  }

  @override
  void dispose() {
    _tab.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(savedItemsProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Saved'),
        leading: BackButton(onPressed: () {
          if (context.canPop()) {
            context.pop();
          } else {
            context.go('/home');
          }
        }),
        bottom: TabBar(
          controller: _tab,
          labelColor: AppColors.primary,
          unselectedLabelColor: AppColors.textSecondary,
          indicatorColor: AppColors.primary,
          tabs: _labels.map((l) => Tab(text: l)).toList(),
        ),
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.wifi_off_outlined,
                    size: 56, color: AppColors.textHint),
                const SizedBox(height: 12),
                Text('Could not load saved items',
                    style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 16),
                OutlinedButton(
                  onPressed: () => ref.invalidate(savedItemsProvider),
                  child: const Text('Retry'),
                ),
              ],
            ),
          ),
        ),
        data: (items) {
          return TabBarView(
            controller: _tab,
            children: _types
                .map((t) => RefreshIndicator(
                      onRefresh: () async =>
                          ref.invalidate(savedItemsProvider),
                      child: _SavedTab(
                        items:
                            items.where((i) => i.itemType == t).toList(),
                        itemType: t,
                      ),
                    ))
                .toList(),
          );
        },
      ),
    );
  }
}

class _SavedTab extends ConsumerWidget {
  final List<SavedItemModel> items;
  final String itemType;
  const _SavedTab({required this.items, required this.itemType});

  IconData get _icon {
    switch (itemType) {
      case 'course':
        return Icons.school_outlined;
      case 'bursary':
        return Icons.card_giftcard_outlined;
      case 'accommodation':
        return Icons.home_outlined;
      default:
        return Icons.bookmark_outline;
    }
  }

  String get _route {
    switch (itemType) {
      case 'course':
        return '/courses';
      case 'bursary':
        return '/bursaries';
      case 'accommodation':
        return '/accommodation';
      default:
        return '/home';
    }
  }

  /// For the Courses tab, build a lookup of courseId → latest application
  /// so we can mirror the application status as a badge on the saved row.
  /// Keeps Saved usable as a quick dashboard instead of forcing the user
  /// to flip to My Applications. Returns an empty map outside the courses
  /// tab so we don't pay for the watch.
  Map<int, ApplicationModel> _appsByCourseId(WidgetRef ref) {
    if (itemType != 'course') return const {};
    final apps =
        ref.watch(applicationListProvider).valueOrNull ?? const [];
    final out = <int, ApplicationModel>{};
    for (final a in apps) {
      if (a.courseId == null) continue;
      // Prefer the most "advanced" status if a course somehow has more
      // than one application (e.g. tracked at two institutions). Order
      // mirrors _statusRank — accepted > offered > submitted > draft.
      final existing = out[a.courseId!];
      if (existing == null ||
          _statusRank(a.status) > _statusRank(existing.status)) {
        out[a.courseId!] = a;
      }
    }
    return out;
  }

  static int _statusRank(String s) {
    switch (s) {
      case 'accepted':
        return 6;
      case 'firm_offer':
        return 5;
      case 'conditional_offer':
        return 4;
      case 'submitted':
      case 'under_review':
      case 'waitlisted':
        return 3;
      case 'in_progress':
        return 2;
      case 'draft':
        return 1;
      case 'rejected':
      case 'withdrawn':
        return 0;
    }
    return 0;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final appsByCourse = _appsByCourseId(ref);
    if (items.isEmpty) {
      // Wrap the empty state in a scrollable so the parent
      // RefreshIndicator can still pull-to-refresh.
      return ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.symmetric(vertical: 80, horizontal: 24),
        children: [
          Icon(_icon, size: 56, color: AppColors.textHint),
          const SizedBox(height: 16),
          Center(
            child: Text('Nothing saved yet',
                style: Theme.of(context).textTheme.titleMedium),
          ),
          const SizedBox(height: 8),
          const Text(
            'Tap the bookmark icon on any item you want to come back to.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.textSecondary),
          ),
          const SizedBox(height: 16),
          Center(
            child: OutlinedButton(
              // _route (/courses, /bursaries, /accommodation) sits inside the
              // bottom-nav ShellRoute — go(), not push(), or it shows blank.
              onPressed: () => context.go(_route),
              child: const Text('Browse'),
            ),
          ),
        ],
      );
    }
    // Compute sectioned groups so Saved doubles as a triage view rather
    // than a flat append-only log. Order matters — headers render in
    // this order top to bottom.
    final groups = _buildSections(items, appsByCourse);
    final closed = itemType == 'bursary'
        ? items.where(_isPastDeadline).toList()
        : const <SavedItemModel>[];

    final children = <Widget>[];
    if (closed.isNotEmpty) {
      children.add(_ClearClosedBanner(
        count: closed.length,
        onClear: () => _confirmAndClearClosed(context, ref, closed),
      ));
      children.add(const SizedBox(height: 8));
    }
    for (final g in groups) {
      if (g.header != null) {
        children.add(Padding(
          padding: const EdgeInsets.fromLTRB(4, 6, 4, 6),
          child: Row(
            children: [
              Icon(g.icon, size: 14, color: g.color),
              const SizedBox(width: 6),
              Text(
                g.header!,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w800,
                  color: g.color,
                  letterSpacing: 0.2,
                ),
              ),
              const SizedBox(width: 6),
              Text(
                '${g.items.length}',
                style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textHint),
              ),
            ],
          ),
        ));
      }
      for (final item in g.items) {
        children.add(_buildRow(context, ref, item, appsByCourse));
        children.add(const SizedBox(height: 8));
      }
    }

    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: EdgeInsets.fromLTRB(
          12, 12, 12, 48 + MediaQuery.of(context).padding.bottom),
      children: children,
    );
  }

  Widget _buildRow(
    BuildContext context,
    WidgetRef ref,
    SavedItemModel item,
    Map<int, ApplicationModel> appsByCourse,
  ) {
    final linkedApp = appsByCourse[item.itemId];
    return Dismissible(
          key: ValueKey(item.id),
          direction: DismissDirection.endToStart,
          background: Container(
            alignment: Alignment.centerRight,
            padding: const EdgeInsets.only(right: 20),
            color: AppColors.error,
            child: const Icon(Icons.delete_outline, color: Colors.white),
          ),
          onDismissed: (_) async {
            try {
              await ref.read(savedRepositoryProvider).unsave(item.id);
              ref.invalidate(savedItemsProvider);
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Removed from saved')),
                );
              }
            } catch (_) {
              // Unsave failed — refresh so the row reappears, and tell
              // the user instead of silently pretending it worked.
              ref.invalidate(savedItemsProvider);
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Could not remove. Try again.'),
                    backgroundColor: AppColors.error,
                  ),
                );
              }
            }
          },
          child: ListTile(
            tileColor: Colors.white,
            shape: RoundedRectangleBorder(
              side: const BorderSide(color: AppColors.border),
              borderRadius: BorderRadius.circular(10),
            ),
            leading: CircleAvatar(
              backgroundColor: AppColors.primaryLight,
              child: Icon(_icon, color: AppColors.primary, size: 20),
            ),
            title: Text(
              item.itemName?.isNotEmpty == true
                  ? item.itemName!
                  : '${itemType[0].toUpperCase()}${itemType.substring(1)} #${item.itemId}',
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                if (item.itemSubtitle?.isNotEmpty == true)
                  Text(
                    item.itemSubtitle!,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                        fontSize: 12, color: AppColors.textSecondary),
                  ),
                if (linkedApp != null) ...[
                  const SizedBox(height: 4),
                  _ApplicationStatusBadge(status: linkedApp.status),
                ],
                if (item.savedAt != null && item.savedAt!.length >= 10)
                  Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: Text(
                      'Saved ${item.savedAt!.substring(0, 10)}',
                      style: const TextStyle(
                          fontSize: 11, color: AppColors.textHint),
                    ),
                  ),
              ],
            ),
            trailing: const Icon(Icons.arrow_forward_ios, size: 14),
            // Detail routes (/courses/:id etc.) are inside the bottom-nav
            // ShellRoute — go() mounts the shell so the detail renders.
            onTap: () => context.go('$_route/${item.itemId}'),
          ),
        );
  }

  // ── Sectioning ─────────────────────────────────────────────────────

  /// Build display groups for the current tab. Each group renders its
  /// own header (or no header if [header] is null) then its items in
  /// order. Sections that would be empty are dropped.
  List<_SavedSection> _buildSections(
    List<SavedItemModel> items,
    Map<int, ApplicationModel> appsByCourse,
  ) {
    if (itemType == 'course') {
      final tracking = <SavedItemModel>[];
      final just = <SavedItemModel>[];
      for (final it in items) {
        if (appsByCourse.containsKey(it.itemId)) {
          tracking.add(it);
        } else {
          just.add(it);
        }
      }
      // Inside Tracking, sort by status rank (most-advanced first) so
      // accepted/offered float to the top.
      tracking.sort((a, b) {
        final ra = _statusRank(appsByCourse[a.itemId]!.status);
        final rb = _statusRank(appsByCourse[b.itemId]!.status);
        return rb.compareTo(ra);
      });
      return [
        if (tracking.isNotEmpty)
          _SavedSection(
            header: 'Tracking',
            icon: Icons.flag_outlined,
            color: AppColors.primary,
            items: tracking,
          ),
        if (just.isNotEmpty)
          _SavedSection(
            header: tracking.isEmpty ? null : 'Just saved',
            icon: Icons.bookmark_border_rounded,
            color: AppColors.textSecondary,
            items: just,
          ),
      ];
    }
    if (itemType == 'bursary') {
      final now = DateTime.now();
      final soonCut = now.add(const Duration(days: 14));
      final closingSoon = <SavedItemModel>[];
      final open = <SavedItemModel>[];
      final closed = <SavedItemModel>[];
      for (final it in items) {
        final d = it.bursaryDeadline;
        if (d != null && d.isBefore(now)) {
          closed.add(it);
        } else if (d != null && d.isBefore(soonCut)) {
          closingSoon.add(it);
        } else {
          open.add(it);
        }
      }
      // Closing soon — soonest first.
      closingSoon.sort(
          (a, b) => a.bursaryDeadline!.compareTo(b.bursaryDeadline!));
      return [
        if (closingSoon.isNotEmpty)
          _SavedSection(
            header: 'Closing soon',
            icon: Icons.warning_amber_rounded,
            color: AppColors.error,
            items: closingSoon,
          ),
        if (open.isNotEmpty)
          _SavedSection(
            header: closingSoon.isNotEmpty || closed.isNotEmpty
                ? 'Open'
                : null,
            icon: Icons.event_available_outlined,
            color: AppColors.primary,
            items: open,
          ),
        if (closed.isNotEmpty)
          _SavedSection(
            header: 'Closed',
            icon: Icons.archive_outlined,
            color: AppColors.textHint,
            items: closed,
          ),
      ];
    }
    // Accommodation — flat list, no sectioning yet.
    return [
      _SavedSection(
          header: null,
          icon: Icons.home_outlined,
          color: AppColors.primary,
          items: items),
    ];
  }

  bool _isPastDeadline(SavedItemModel it) {
    final d = it.bursaryDeadline;
    return d != null && d.isBefore(DateTime.now());
  }

  Future<void> _confirmAndClearClosed(
    BuildContext context,
    WidgetRef ref,
    List<SavedItemModel> closed,
  ) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Clear closed bursaries?'),
        content: Text(
            'Remove ${closed.length} closed bursar${closed.length == 1 ? "y" : "ies"} from your saved list?'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancel')),
          ElevatedButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Clear')),
        ],
      ),
    );
    if (ok != true) return;
    final repo = ref.read(savedRepositoryProvider);
    var failed = 0;
    for (final it in closed) {
      try {
        await repo.unsave(it.id);
      } catch (_) {
        failed++;
      }
    }
    ref.invalidate(savedItemsProvider);
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(failed == 0
              ? 'Cleared ${closed.length} closed bursar${closed.length == 1 ? "y" : "ies"}'
              : 'Cleared ${closed.length - failed}, $failed failed'),
          backgroundColor:
              failed == 0 ? AppColors.eligible : AppColors.error,
        ),
      );
    }
  }
}

/// A header + a slice of saved items, used by [_SavedTab] to render
/// "Tracking / Just saved" on courses and "Closing soon / Open / Closed"
/// on bursaries.
class _SavedSection {
  final String? header;
  final IconData icon;
  final Color color;
  final List<SavedItemModel> items;
  const _SavedSection({
    required this.header,
    required this.icon,
    required this.color,
    required this.items,
  });
}

/// Sticky-feeling banner that appears above the Bursaries list when any
/// saved bursaries are past their deadline. Tapping it bulk-removes them
/// after a confirmation dialog.
class _ClearClosedBanner extends StatelessWidget {
  final int count;
  final VoidCallback onClear;
  const _ClearClosedBanner({required this.count, required this.onClear});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.error.withOpacity(0.08),
      borderRadius: BorderRadius.circular(10),
      child: InkWell(
        onTap: onClear,
        borderRadius: BorderRadius.circular(10),
        child: Padding(
          padding:
              const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: Row(
            children: [
              const Icon(Icons.cleaning_services_outlined,
                  size: 18, color: AppColors.error),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  '$count closed bursar${count == 1 ? "y" : "ies"} in your saved list',
                  style: const TextStyle(
                    fontSize: 12.5,
                    fontWeight: FontWeight.w700,
                    color: AppColors.error,
                  ),
                ),
              ),
              const Text(
                'Clear all',
                style: TextStyle(
                  fontSize: 12.5,
                  fontWeight: FontWeight.w800,
                  color: AppColors.error,
                ),
              ),
              const SizedBox(width: 2),
              const Icon(Icons.chevron_right,
                  size: 16, color: AppColors.error),
            ],
          ),
        ),
      ),
    );
  }
}

/// Tiny pill that mirrors an application's status onto a saved-course
/// row, so Saved doubles as a quick "what have I done about each of
/// these?" dashboard.
class _ApplicationStatusBadge extends StatelessWidget {
  final String status;
  const _ApplicationStatusBadge({required this.status});

  // Bucketed for compactness — the saved list shouldn't render 9
  // distinct pills, just the headline state.
  ({String label, Color color, IconData icon}) get _meta {
    switch (status) {
      case 'accepted':
        return (
          label: 'Accepted',
          color: AppColors.eligible,
          icon: Icons.check_circle_outline,
        );
      case 'firm_offer':
      case 'conditional_offer':
        return (
          label: 'Offered',
          color: AppColors.secondary,
          icon: Icons.workspace_premium_outlined,
        );
      case 'submitted':
      case 'under_review':
      case 'waitlisted':
        return (
          label: 'Submitted',
          color: AppColors.primary,
          icon: Icons.send_outlined,
        );
      case 'in_progress':
      case 'draft':
        return (
          label: 'Draft started',
          color: AppColors.accent,
          icon: Icons.edit_note_rounded,
        );
      case 'rejected':
      case 'withdrawn':
        return (
          label: 'Closed',
          color: AppColors.textHint,
          icon: Icons.archive_outlined,
        );
    }
    return (
      label: status,
      color: AppColors.textHint,
      icon: Icons.flag_outlined,
    );
  }

  @override
  Widget build(BuildContext context) {
    final m = _meta;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: m.color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(m.icon, size: 11, color: m.color),
          const SizedBox(width: 4),
          Text(
            m.label,
            style: TextStyle(
              fontSize: 10.5,
              fontWeight: FontWeight.w800,
              color: m.color,
            ),
          ),
        ],
      ),
    );
  }
}
