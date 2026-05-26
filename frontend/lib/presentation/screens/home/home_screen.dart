import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/constants/app_constants.dart';
import '../../../providers/auth_provider.dart';
import '../../../providers/aps_provider.dart';
import '../../../providers/course_provider.dart';
import '../../../data/models/bursary_model.dart';
import '../../../data/models/bursary_match_model.dart';
import '../../../providers/bursary_provider.dart';
import '../bursaries/bursaries_screen.dart';
import '../../widgets/cards/aps_score_card.dart';
import '../../widgets/common/app_avatar.dart';
import '../../widgets/common/notification_bell.dart';
import '../../widgets/cards/quick_action_card.dart';
import '../../widgets/cards/section_header.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authStateProvider).user;
    final apsAsync = ref.watch(latestApsProvider);

    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async {
            ref.invalidate(latestApsProvider);
            ref.invalidate(courseRecommendationsProvider);
            ref.invalidate(bursaryRecommendationsProvider);
            ref.invalidate(bursaryListProvider('status=open'));
          },
          child: CustomScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            slivers: [
            SliverAppBar(
              floating: true,
              backgroundColor: Colors.white,
              elevation: 0,
              title: Row(
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Hi, ${user?.firstName.isNotEmpty == true ? user!.firstName : "there"} 👋',
                          style: Theme.of(context).textTheme.titleLarge),
                      Text(AppConstants.tagline,
                          style: Theme.of(context).textTheme.bodySmall),
                    ],
                  ),
                ],
              ),
              actions: [
                const NotificationBell(),
                Padding(
                  padding: const EdgeInsets.only(right: 16),
                  child: AppAvatar(
                    radius: 18,
                    onTap: () => context.go('/profile'),
                  ),
                ),
              ],
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Hero upload banner
                    Container(
                      width: double.infinity,
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
                          const Icon(Icons.document_scanner_rounded, color: Colors.white, size: 32),
                          const SizedBox(height: 12),
                          Text('Calculate your APS',
                              style: Theme.of(context).textTheme.headlineSmall?.copyWith(color: Colors.white)),
                          const SizedBox(height: 6),
                          Text('Upload your report card to find matching courses',
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.white70)),
                          const SizedBox(height: 16),
                          Row(
                            children: [
                              Expanded(
                                child: _HeroButton(
                                  icon: Icons.upload_file_outlined,
                                  label: 'Upload',
                                  onTap: () => context.push('/scanner'),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: _HeroButton(
                                  icon: Icons.camera_alt_outlined,
                                  label: 'Camera',
                                  onTap: () => context.push('/scanner'),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: _HeroButton(
                                  icon: Icons.edit_outlined,
                                  label: 'Enter Marks',
                                  onTap: () => context.push('/manual-entry'),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 24),

                    // APS Dashboard Cards
                    apsAsync.when(
                      data: (aps) => aps != null
                          ? Column(
                              children: [
                                ApsScoreCard(totalAps: aps.totalAps, subjects: aps.subjects),
                                OutlinedButton.icon(
                                  onPressed: () => context.push('/manual-entry'),
                                  icon: const Icon(Icons.edit_outlined, size: 16),
                                  label: const Text('Edit Marks'),
                                  style: OutlinedButton.styleFrom(
                                    minimumSize: const Size(double.infinity, 44),
                                    textStyle: const TextStyle(fontSize: 14),
                                  ),
                                ),
                                const SizedBox(height: 8),
                              ],
                            )
                          : const SizedBox.shrink(),
                      loading: () => const SizedBox.shrink(),
                      error: (_, __) => const SizedBox.shrink(),
                    ),

                    // Quick Actions
                    const SectionHeader(title: 'Quick Actions'),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: QuickActionCard(
                            icon: Icons.school_outlined,
                            label: 'Find Courses',
                            color: AppColors.primary,
                            onTap: () => context.go('/courses'),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: QuickActionCard(
                            icon: Icons.card_giftcard_outlined,
                            label: 'Bursaries',
                            color: AppColors.secondary,
                            onTap: () => context.go('/bursaries'),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: QuickActionCard(
                            icon: Icons.auto_awesome_outlined,
                            label: 'Ask AI',
                            color: AppColors.accent,
                            onTap: () => context.go('/ai'),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),

                    // Sections
                    SectionHeader(title: 'Recommended for You', actionLabel: 'See all', onAction: () => context.go('/courses')),
                    const SizedBox(height: 12),
                    const _RecommendedCourses(),
                    const SizedBox(height: 24),

                    const SectionHeader(title: 'Explore Pathways'),
                    const SizedBox(height: 12),
                    const _PathwayCards(),
                    const SizedBox(height: 24),

                    SectionHeader(title: 'Universities Still Open', actionLabel: 'See all', onAction: () => context.go('/courses')),
                    const SizedBox(height: 12),
                    _UniversitiesOpenBanner(onTap: () => context.go('/courses')),
                    const SizedBox(height: 24),

                    SectionHeader(title: 'Recommended Bursaries', actionLabel: 'See all', onAction: () => context.go('/bursaries')),
                    const SizedBox(height: 12),
                    const _RecommendedBursaries(),
                    const SizedBox(height: 24),

                    SectionHeader(title: 'Bursaries Closing Soon', actionLabel: 'See all', onAction: () => context.go('/bursaries')),
                    const SizedBox(height: 12),
                    _BursaryTeaserList(onTap: () => context.go('/bursaries')),
                  ],
                ),
              ),
            ),
            ],
          ),
        ),
      ),
    );
  }
}

class _RecommendedCourses extends ConsumerWidget {
  const _RecommendedCourses();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(courseRecommendationsProvider);

    return async.when(
      loading: () => const SizedBox(
        height: 130,
        child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
      ),
      error: (e, _) => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            const Icon(Icons.info_outline, color: AppColors.textHint, size: 18),
            const SizedBox(width: 8),
            const Expanded(
              child: Text(
                'Scan your marks to see recommendations tailored to you.',
                style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
              ),
            ),
            TextButton(
              onPressed: () => context.push('/scanner'),
              child: const Text('Scan'),
            ),
          ],
        ),
      ),
      data: (recs) {
        if (recs.isEmpty) {
          return Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Text(
              'No recommendations yet. Complete your profile and scan your marks to see courses matched to you.',
              style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
            ),
          );
        }
        return SizedBox(
          height: 130,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 2),
            itemCount: recs.length.clamp(0, 10),
            separatorBuilder: (_, __) => const SizedBox(width: 10),
            itemBuilder: (_, i) {
              final r = recs[i];
              final rec = (r['recommendation'] as Map?) ?? const {};
              final match = (r['match'] as Map?) ?? const {};
              final reason =
                  (rec['reason'] as String?) ?? 'matches_your_interests';
              return _RecommendationCard(
                courseId: r['course_id'] as int,
                courseName: (r['course_name'] as String?) ?? '',
                institution: (r['institution_short'] as String?) ??
                    (r['institution_name'] as String?) ??
                    '',
                field: (r['course_field'] as String?) ?? '',
                minAps: (r['min_aps'] as num?)?.toInt() ?? 0,
                matchCategory: (match['category'] as String?) ?? '',
                apsSurplus: (match['aps_surplus'] as num?)?.toInt() ?? 0,
                reasonKey: reason,
              );
            },
          ),
        );
      },
    );
  }
}

class _RecommendationCard extends StatelessWidget {
  final int courseId;
  final String courseName;
  final String institution;
  final String field;
  final int minAps;
  final String reasonKey;
  final String matchCategory;
  final int apsSurplus;

  const _RecommendationCard({
    required this.courseId,
    required this.courseName,
    required this.institution,
    required this.field,
    required this.minAps,
    required this.reasonKey,
    required this.matchCategory,
    required this.apsSurplus,
  });

  Color get _matchColor {
    switch (matchCategory) {
      case 'eligible':
        return AppColors.eligible;
      case 'subject_gap':
        return AppColors.subjectGap;
      case 'aps_gap':
        return AppColors.apsGap;
      default:
        return AppColors.textHint;
    }
  }

  String get _matchLabel {
    switch (matchCategory) {
      case 'eligible':
        return apsSurplus > 0 ? 'Qualify +$apsSurplus' : 'Qualify ✓';
      case 'subject_gap':
        return 'Subject Gap';
      case 'aps_gap':
        return 'APS Gap';
      default:
        return '';
    }
  }

  String get _reasonLabel {
    switch (reasonKey) {
      case 'similar_students':
        return 'Popular with similar students';
      case 'matches_your_subjects_and_career':
        return 'Perfect fit for you';
      case 'matches_your_subjects':
        return 'Matches your subjects';
      case 'matches_your_career':
        return 'Fits your dream career';
      case 'matches_your_profile':
        return 'Matches your marks & career';
      default:
        return 'Matches your interests';
    }
  }

  IconData get _reasonIcon {
    switch (reasonKey) {
      case 'similar_students':
        return Icons.groups_outlined;
      case 'matches_your_subjects_and_career':
        return Icons.workspace_premium_outlined;
      case 'matches_your_subjects':
        return Icons.school_outlined;
      case 'matches_your_career':
        return Icons.star_outline;
      case 'matches_your_profile':
        return Icons.verified_outlined;
      default:
        return Icons.auto_awesome_outlined;
    }
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => context.push('/courses/$courseId'),
      child: Container(
        width: 220,
        padding: const EdgeInsets.all(11),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.border),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.03),
              blurRadius: 6,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                Icon(_reasonIcon, size: 12, color: AppColors.primary),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    _reasonLabel,
                    style: const TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: AppColors.primary,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              courseName,
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: AppColors.textPrimary,
                height: 1.2,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 3),
            Text(
              institution,
              style: const TextStyle(
                fontSize: 11,
                color: AppColors.textSecondary,
                fontWeight: FontWeight.w600,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 6),
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppColors.primaryLight,
                    borderRadius: BorderRadius.circular(5),
                  ),
                  child: Text(
                    minAps > 0 ? 'APS $minAps+' : 'Open',
                    style: const TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: AppColors.primary,
                    ),
                  ),
                ),
                const SizedBox(width: 4),
                if (_matchLabel.isNotEmpty)
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: _matchColor.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(5),
                    ),
                    child: Text(
                      _matchLabel,
                      style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          color: _matchColor),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _PathwayCards extends ConsumerWidget {
  const _PathwayCards();

  void _openUniversities(BuildContext context, WidgetRef ref) {
    // Clear type so the user sees all uni / UoT offerings.
    ref.read(courseFilterProvider.notifier).setInstitutionType(null);
    context.go('/courses');
  }

  void _openColleges(BuildContext context, WidgetRef ref) {
    // Pre-set the filter to TVET so they land on college programmes only.
    ref.read(courseFilterProvider.notifier).setInstitutionType('tvet');
    context.go('/courses');
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Row(
      children: [
        Expanded(
          child: _PathwayCard(
            icon: Icons.school_rounded,
            title: 'Universities',
            subtitle: 'Bachelor degrees & diplomas',
            gradient: const [AppColors.primary, AppColors.primaryDark],
            onTap: () => _openUniversities(context, ref),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _PathwayCard(
            icon: Icons.build_outlined,
            title: 'TVET Colleges',
            subtitle: 'NC(V) & N1–N6 programmes',
            gradient: const [AppColors.accent, AppColors.secondary],
            onTap: () => _openColleges(context, ref),
          ),
        ),
      ],
    );
  }
}

class _PathwayCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final List<Color> gradient;
  final VoidCallback onTap;

  const _PathwayCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.gradient,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 110,
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: gradient,
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: gradient[0].withOpacity(0.25),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Icon(icon, color: Colors.white, size: 28),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 15,
                        fontWeight: FontWeight.w800)),
                const SizedBox(height: 2),
                Text(subtitle,
                    style: TextStyle(
                        color: Colors.white.withOpacity(0.85), fontSize: 11),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _HeroButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _HeroButton({required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 9),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.2),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: Colors.white.withOpacity(0.4)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: Colors.white, size: 16),
            const SizedBox(width: 4),
            Flexible(
              child: Text(
                label,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
                overflow: TextOverflow.ellipsis,
                maxLines: 1,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _UniversitiesOpenBanner extends StatelessWidget {
  final VoidCallback onTap;
  const _UniversitiesOpenBanner({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.secondaryLight,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.secondary.withOpacity(0.3)),
        ),
        child: Row(
          children: [
            const Icon(Icons.check_circle_outline, color: AppColors.secondary, size: 28),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Applications are open!',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(color: AppColors.secondary)),
                  Text('Browse institutions currently accepting applications',
                      style: Theme.of(context).textTheme.bodySmall),
                ],
              ),
            ),
            const Icon(Icons.arrow_forward_ios, size: 14, color: AppColors.secondary),
          ],
        ),
      ),
    );
  }
}

class _RecommendedBursaries extends ConsumerWidget {
  const _RecommendedBursaries();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(bursaryRecommendationsProvider);
    return async.when(
      loading: () => const SizedBox(
        height: 110,
        child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
      ),
      error: (_, __) => const SizedBox.shrink(),
      data: (recs) {
        if (recs.isEmpty) {
          return Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Text(
              'No bursary matches yet. Scan your marks for personalised recommendations.',
              style:
                  TextStyle(fontSize: 12, color: AppColors.textSecondary),
            ),
          );
        }
        return SizedBox(
          height: 130,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 2),
            itemCount: recs.length.clamp(0, 5),
            separatorBuilder: (_, __) => const SizedBox(width: 10),
            itemBuilder: (_, i) => _RecommendedBursaryCard(item: recs[i]),
          ),
        );
      },
    );
  }
}

class _RecommendedBursaryCard extends StatelessWidget {
  final BursaryWithMatch item;
  const _RecommendedBursaryCard({required this.item});

  Color _badgeColor() {
    switch (item.match?.status) {
      case 'qualified':
        return AppColors.eligible;
      case 'check_details':
        return AppColors.secondary;
      case 'grade_gap':
        return AppColors.apsGap;
      default:
        return AppColors.primary;
    }
  }

  String _shortDeadline() {
    final raw = item.bursary.applicationDeadline;
    if (raw == null) return '';
    final d = DateTime.tryParse(raw);
    if (d == null) return raw;
    const months = [
      '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    return '${d.day} ${months[d.month]}';
  }

  @override
  Widget build(BuildContext context) {
    final b = item.bursary;
    final m = item.match;
    final days = m?.daysUntilDeadline;
    return GestureDetector(
      onTap: () => context.push('/bursaries/${b.id}'),
      child: Container(
        width: 220,
        padding: const EdgeInsets.all(11),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                const Icon(Icons.card_giftcard_outlined,
                    size: 14, color: AppColors.accent),
                const SizedBox(width: 4),
                if (m != null)
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: _badgeColor().withOpacity(0.15),
                      borderRadius: BorderRadius.circular(5),
                    ),
                    child: Text(
                      m.label,
                      style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          color: _badgeColor()),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              b.name,
              style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  height: 1.2),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 3),
            Text(b.provider,
                style: const TextStyle(
                    fontSize: 11,
                    color: AppColors.textSecondary,
                    fontWeight: FontWeight.w600),
                maxLines: 1,
                overflow: TextOverflow.ellipsis),
            const SizedBox(height: 6),
            Row(
              children: [
                const Icon(Icons.calendar_today,
                    size: 11, color: AppColors.textHint),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    'Closes ${_shortDeadline()}'
                    '${days != null && days >= 0 && days <= 30 ? "  •  ${days}d" : ""}',
                    style: TextStyle(
                        fontSize: 11,
                        fontWeight: days != null && days <= 7 && days >= 0
                            ? FontWeight.w700
                            : FontWeight.w500,
                        color: days != null && days <= 7 && days >= 0
                            ? AppColors.error
                            : AppColors.textSecondary),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _BursaryTeaserList extends ConsumerWidget {
  final VoidCallback onTap;
  const _BursaryTeaserList({required this.onTap});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(bursaryListProvider('status=open'));
    return async.when(
      loading: () => const SizedBox(
        height: 80,
        child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
      ),
      error: (_, __) => const SizedBox.shrink(),
      data: (all) {
        final today = DateTime.now();
        final upcoming = all.where((b) {
          final raw = b.bursary.applicationDeadline;
          if (raw == null) return false;
          final d = DateTime.tryParse(raw);
          return d != null &&
              d.isAfter(today.subtract(const Duration(days: 1)));
        }).toList()
          ..sort((a, b) => (a.bursary.applicationDeadline ?? '')
              .compareTo(b.bursary.applicationDeadline ?? ''));
        final top = upcoming.take(3).toList();
        if (top.isEmpty) {
          return Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Text(
              'No bursaries with upcoming deadlines.',
              style: TextStyle(color: AppColors.textSecondary),
            ),
          );
        }
        return Column(
          children: [
            for (int i = 0; i < top.length; i++) ...[
              _BursaryTeaser(
                item: top[i],
                onTap: () =>
                    context.push('/bursaries/${top[i].bursary.id}'),
              ),
              if (i < top.length - 1) const SizedBox(height: 10),
            ],
          ],
        );
      },
    );
  }
}

class _BursaryTeaser extends StatelessWidget {
  final BursaryWithMatch item;
  final VoidCallback onTap;

  const _BursaryTeaser({required this.item, required this.onTap});

  BursaryModel get bursary => item.bursary;
  BursaryMatch? get m => item.match;

  String get _formattedDeadline {
    final raw = bursary.applicationDeadline;
    if (raw == null) return 'TBA';
    final d = DateTime.tryParse(raw);
    if (d == null) return raw;
    const months = [
      '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    return '${d.day} ${months[d.month]} ${d.year}';
  }

  int? get _daysLeft {
    final raw = bursary.applicationDeadline;
    if (raw == null) return null;
    final d = DateTime.tryParse(raw);
    if (d == null) return null;
    return d.difference(DateTime.now()).inDays;
  }

  @override
  Widget build(BuildContext context) {
    final fieldLabel =
        AppConstants.studyFields[bursary.field] ?? bursary.field;
    final days = _daysLeft;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.border),
        ),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: AppColors.accentLight,
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.card_giftcard_outlined,
                  color: AppColors.accent),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    bursary.name,
                    style: Theme.of(context).textTheme.titleMedium,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    '$fieldLabel • Closes $_formattedDeadline',
                    style: Theme.of(context).textTheme.bodySmall,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  if (days != null && days >= 0 && days <= 30)
                    Padding(
                      padding: const EdgeInsets.only(top: 2),
                      child: Text(
                        days == 0
                            ? 'Closes today'
                            : '$days day${days == 1 ? '' : 's'} left',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: days <= 7
                              ? AppColors.error
                              : AppColors.accent,
                        ),
                      ),
                    ),
                ],
              ),
            ),
            const Icon(Icons.arrow_forward_ios,
                size: 14, color: AppColors.textHint),
          ],
        ),
      ),
    );
  }
}
