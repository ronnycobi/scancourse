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
import '../../../providers/application_provider.dart';
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
    final reportsAsync = ref.watch(reportListProvider);
    // 'Qualify' / 'Recommended' badges only make sense once we know the
    // user's APS. Until they scan, gate any APS-dependent sections.
    final hasAps = apsAsync.valueOrNull != null;
    // Hide upload/CTAs as soon as the user has uploaded ANYTHING — even
    // if APS is still 0 while the OCR processes — so the home screen
    // stops nagging them to do something they've already done.
    final hasReports = (reportsAsync.valueOrNull?.isNotEmpty) ?? false;
    final hasUploadedSomething = hasAps || hasReports;

    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async {
            ref.invalidate(latestApsProvider);
            ref.invalidate(reportListProvider);
            ref.invalidate(courseRecommendationsProvider);
            ref.invalidate(bursaryRecommendationsProvider);
            ref.invalidate(bursaryListProvider('status=open'));
            ref.invalidate(unreadCountProvider);
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
                    // Smart APS hero — single blue card, state-machined.
                    _ApsHero(
                      apsAsync: apsAsync,
                      reportsAsync: reportsAsync,
                      userGrade: user?.grade,
                    ),
                    const SizedBox(height: 20),

                    // Quick Actions sit directly below the hero so the
                    // three primary shortcuts are always one tap away.
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

                    // Recommended courses — personalised content follows
                    // the quick shortcuts. Falls back to the unlock CTA
                    // when there's nothing on file.
                    if (hasAps) ...[
                      SectionHeader(
                          title: 'Recommended for You',
                          actionLabel: 'See all',
                          onAction: () => context.go('/courses')),
                      const SizedBox(height: 12),
                      const _RecommendedCourses(),
                      const SizedBox(height: 24),
                    ] else if (!hasUploadedSomething) ...[
                      const _UnlockRecommendationsCta(),
                      const SizedBox(height: 24),
                    ],

                    SectionHeader(title: 'Universities Still Open', actionLabel: 'See all', onAction: () => context.go('/courses')),
                    const SizedBox(height: 12),
                    _UniversitiesOpenBanner(onTap: () => context.go('/courses')),
                    const SizedBox(height: 24),

                    // 'Recommended' for bursaries also requires APS for
                    // honest matching. Without APS we show 'Browse all'.
                    if (hasAps) ...[
                      SectionHeader(
                          title: 'Recommended Bursaries',
                          actionLabel: 'See all',
                          onAction: () => context.go('/bursaries')),
                      const SizedBox(height: 12),
                      const _RecommendedBursaries(),
                      const SizedBox(height: 24),
                    ],

                    SectionHeader(title: 'Bursaries Closing Soon', actionLabel: 'See all', onAction: () => context.go('/bursaries')),
                    const SizedBox(height: 12),
                    _BursaryTeaserList(onTap: () => context.go('/bursaries')),
                    const SizedBox(height: 24),

                    const SectionHeader(title: 'Explore Pathways'),
                    const SizedBox(height: 12),
                    const _PathwayCards(),
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
        height: 150,
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
        // Premium taller carousel — 210px tall, snap-paged so each
        // card stops cleanly. Bigger institution name, gradient
        // header strip coloured by match verdict.
        return SizedBox(
          height: 150,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            physics: const BouncingScrollPhysics(),
            padding: const EdgeInsets.symmetric(horizontal: 2),
            itemCount: recs.length.clamp(0, 10),
            separatorBuilder: (_, __) => const SizedBox(width: 12),
            itemBuilder: (_, i) {
              final r = recs[i];
              final rec = (r['recommendation'] as Map?) ?? const {};
              final match = (r['match'] as Map?) ?? const {};
              final reason =
                  (rec['reason'] as String?) ?? 'matches_your_interests';
              return _RecommendationCard(
                courseId: (r['course_id'] as num?)?.toInt() ?? 0,
                courseName: (r['course_name'] as String?) ?? '',
                institution: (r['institution_name'] as String?) ??
                    (r['institution_short'] as String?) ??
                    '',
                institutionLogoUrl:
                    (r['institution_logo_url'] as String?) ?? '',
                field: (r['course_field'] as String?) ?? '',
                minAps: (r['min_aps'] as num?)?.toInt() ?? 0,
                durationYears: (r['course_duration_years'] as num?)?.toDouble(),
                applicationDeadline: r['application_deadline'] as String?,
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
  final String institutionLogoUrl;
  final String field;
  final int minAps;
  final double? durationYears;
  final String? applicationDeadline;
  final String reasonKey;
  final String matchCategory;
  final int apsSurplus;

  const _RecommendationCard({
    required this.courseId,
    required this.courseName,
    required this.institution,
    required this.institutionLogoUrl,
    required this.field,
    required this.minAps,
    this.durationYears,
    this.applicationDeadline,
    required this.reasonKey,
    required this.matchCategory,
    required this.apsSurplus,
  });

  // "3-year" / "1½-year" friendly label, or null if unknown.
  String? get _durationLabel {
    final d = durationYears;
    if (d == null || d <= 0) return null;
    if (d == d.roundToDouble()) return '${d.toInt()}-year';
    return '${d.toStringAsFixed(1)}-year';
  }

  // "Closes 30 Sep" or "Closed", or null if no deadline on record.
  String? get _deadlineLabel {
    final raw = applicationDeadline;
    if (raw == null || raw.isEmpty) return null;
    final date = DateTime.tryParse(raw);
    if (date == null) return null;
    const months = [
      '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    final now = DateTime.now();
    if (date.isBefore(DateTime(now.year, now.month, now.day))) return 'Closed';
    return 'Closes ${date.day} ${months[date.month]}';
  }

  bool get _deadlineUrgent {
    final raw = applicationDeadline;
    if (raw == null) return false;
    final date = DateTime.tryParse(raw);
    if (date == null) return false;
    final days = date.difference(DateTime.now()).inDays;
    return days >= 0 && days <= 14;
  }

  // Colour set used by the gradient header strip — the verdict drives
  // the whole card mood: green for qualify, amber for subject gap,
  // blue-primary for aps gap, neutral for everything else.
  ({Color top, Color bottom}) get _headerGradient {
    switch (matchCategory) {
      case 'eligible':
        return (top: const Color(0xFF10B981), bottom: AppColors.eligible);
      case 'subject_gap':
        return (top: const Color(0xFFF59E0B), bottom: AppColors.subjectGap);
      case 'aps_gap':
        return (top: AppColors.primary, bottom: AppColors.primaryDark);
      default:
        return (top: AppColors.primary, bottom: AppColors.primaryDark);
    }
  }

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
        return apsSurplus > 0 ? 'Qualify +$apsSurplus' : 'Qualify';
      case 'subject_gap':
        return 'Subject gap';
      case 'aps_gap':
        return 'APS short';
      default:
        return '';
    }
  }

  IconData get _matchIcon {
    switch (matchCategory) {
      case 'eligible':
        return Icons.check_circle;
      case 'subject_gap':
        return Icons.menu_book_outlined;
      case 'aps_gap':
        return Icons.trending_up;
      default:
        return Icons.info_outline;
    }
  }

  String get _reasonLabel {
    switch (reasonKey) {
      case 'similar_students':
        return 'Popular nearby';
      case 'matches_your_subjects_and_career':
        return 'Perfect fit';
      case 'matches_your_subjects':
        return 'Matches subjects';
      case 'matches_your_career':
        return 'Fits your career';
      case 'matches_your_profile':
        return 'Matches your profile';
      default:
        return 'Recommended';
    }
  }

  @override
  Widget build(BuildContext context) {
    final grad = _headerGradient;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () => context.push('/courses/$courseId'),
        borderRadius: BorderRadius.circular(18),
        child: Container(
          width: 260,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: AppColors.border),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.06),
                blurRadius: 14,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(14, 10, 14, 10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      courseName,
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w800,
                        color: AppColors.textPrimary,
                        height: 1.2,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    // Full institution name (e.g. "Cape Peninsula University
                    // of Technology") — replaces the old "Matches subjects".
                    Text(
                      institution,
                      style: const TextStyle(
                        fontSize: 10.5,
                        color: AppColors.textSecondary,
                        fontWeight: FontWeight.w600,
                        height: 1.25,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (_durationLabel != null || _deadlineLabel != null) ...[
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          if (_durationLabel != null) ...[
                            const Icon(Icons.schedule,
                                size: 12, color: AppColors.textHint),
                            const SizedBox(width: 3),
                            Text(
                              _durationLabel!,
                              style: const TextStyle(
                                fontSize: 10.5,
                                color: AppColors.textSecondary,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                          if (_durationLabel != null && _deadlineLabel != null)
                            const Text('  ·  ',
                                style: TextStyle(
                                    fontSize: 10.5,
                                    color: AppColors.textHint)),
                          if (_deadlineLabel != null)
                            Flexible(
                              child: Text(
                                _deadlineLabel!,
                                style: TextStyle(
                                  fontSize: 10.5,
                                  fontWeight: FontWeight.w700,
                                  color: _deadlineUrgent
                                      ? AppColors.error
                                      : AppColors.textSecondary,
                                ),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                        ],
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 8),
                // Bottom row: APS chip next to qualify badge.
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppColors.primary.withOpacity(0.10),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        minAps > 0 ? 'APS $minAps' : 'Open',
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                          color: AppColors.primary,
                        ),
                      ),
                    ),
                    const SizedBox(width: 6),
                    if (_matchLabel.isNotEmpty)
                      Flexible(
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: _matchColor.withOpacity(0.12),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(
                                color: _matchColor.withOpacity(0.35)),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(_matchIcon,
                                  size: 12, color: _matchColor),
                              const SizedBox(width: 4),
                              Flexible(
                                child: Text(
                                  _matchLabel,
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w800,
                                    color: _matchColor,
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _logoFallback(String inst) {
    final initial = inst.isNotEmpty ? inst[0].toUpperCase() : 'U';
    return Container(
      decoration: BoxDecoration(
        color: AppColors.primaryLight,
        borderRadius: BorderRadius.circular(8),
      ),
      alignment: Alignment.center,
      child: Text(
        initial,
        style: const TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.w900,
          color: AppColors.primary,
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
        final top = upcoming.take(2).toList();
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

/// Single blue hero at the top of the home screen. State-machine that
/// adapts to whether the user has an APS and what grade they're in,
/// so the message always lines up with what they should do next.
class _ApsHero extends ConsumerWidget {
  final AsyncValue apsAsync;
  final AsyncValue reportsAsync;
  final String? userGrade;

  const _ApsHero({
    required this.apsAsync,
    required this.reportsAsync,
    required this.userGrade,
  });

  bool get _isMatricOrPostSchool =>
      userGrade == 'grade_12' ||
      userGrade == 'gap_year' ||
      userGrade == 'other';

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Has the user actually started tracking any applications? If not,
    // the "Courses" + "My applications" CTAs lead to empty screens, so
    // we hide them and let the hero shrink to its text content only.
    final hasApplications =
        (ref.watch(applicationListProvider).valueOrNull?.isNotEmpty) ?? false;
    final aps = apsAsync.valueOrNull;
    final apsLoading = apsAsync.isLoading;
    final reportsLoading = reportsAsync.isLoading;
    final hasReports =
        (reportsAsync.valueOrNull as List?)?.isNotEmpty ?? false;

    // Only show the processing pulse during ACTUAL network loading,
    // not when both have settled and APS is just 0. Previously this
    // looped forever because `apsAsync.valueOrNull` is null both
    // during loading AND when APS=0.
    if (apsLoading || reportsLoading) {
      return _ProcessingPulse(
          message: 'Loading your dashboard…');
    }

    // Has reports but APS still 0 — OCR couldn't read marks. Don't
    // tell them "calculate your APS" (they already tried). Tell them
    // we struggled and offer to retry / edit manually.
    if (aps == null && hasReports) {
      return _heroShell(
        context,
        icon: Icons.warning_amber_rounded,
        title: 'We couldn\'t read your marks',
        body: 'OCR didn\'t pick anything up. Open your report and add the marks, or scan a clearer photo.',
        actions: [
          _HeroButton(
            icon: Icons.edit_outlined,
            label: 'Open report',
            onTap: () => context.push('/reports'),
          ),
          _HeroButton(
            icon: Icons.camera_alt_outlined,
            label: 'Scan again',
            onTap: () => context.push('/scanner'),
          ),
        ],
      );
    }

    // No APS, no reports → upload prompt
    if (aps == null) {
      return _heroShell(
        context,
        icon: Icons.document_scanner_rounded,
        title: 'Calculate your APS',
        body: 'Upload your report card to find matching courses.',
        actions: [
          _HeroButton(
            icon: Icons.upload_file_outlined,
            label: 'Upload',
            onTap: () => context.push('/scanner'),
          ),
          _HeroButton(
            icon: Icons.camera_alt_outlined,
            label: 'Camera',
            onTap: () => context.push('/scanner'),
          ),
          _HeroButton(
            icon: Icons.edit_outlined,
            label: 'Enter Marks',
            onTap: () => context.push('/manual-entry'),
          ),
        ],
      );
    }
    // Has APS. Branch on grade.
    if (_isMatricOrPostSchool) {
      return _heroShell(
        context,
        icon: Icons.celebration_rounded,
        title: 'Your APS is ${aps.totalAps}. Time to apply.',
        body:
            'See every course and bursary you qualify for, and start tracking your applications.',
        // If the user hasn't started any applications yet, drop the CTA
        // buttons entirely — the hero shrinks to fit just the message.
        actions: hasApplications
            ? [
                _HeroButton(
                  icon: Icons.school_outlined,
                  label: 'Courses',
                  onTap: () => context.push('/courses'),
                ),
                _HeroButton(
                  icon: Icons.assignment_outlined,
                  label: 'My applications',
                  onTap: () => context.push('/applications'),
                ),
              ]
            : const [],
      );
    }
    // Grade 10/11 (or grade unset) — still in school, can improve.
    return _heroShell(
      context,
      icon: Icons.trending_up_rounded,
      title: 'Your APS is ${aps.totalAps}. Push it higher?',
      body:
          'Tap to see 3 specific things you can do this term to lift your marks.',
      actions: [
        _HeroButton(
          icon: Icons.psychology_alt_outlined,
          label: 'See plan',
          onTap: () => context.push('/improvement-plan'),
        ),
        _HeroButton(
          icon: Icons.show_chart_rounded,
          label: 'APS Journey',
          onTap: () => context.push('/aps-journey'),
        ),
      ],
    );
  }

  Widget _heroShell(
    BuildContext context, {
    IconData? icon, // legacy — no longer rendered (kept for call-site compat)
    required String title,
    required String body,
    required List<Widget> actions,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.primary, AppColors.primaryDark],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withOpacity(0.20),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style: const TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.w800)),
          const SizedBox(height: 4),
          Text(body,
              style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 13,
                  height: 1.35)),
          if (actions.isNotEmpty) ...[
            const SizedBox(height: 12),
            Row(
              children: [
                for (int i = 0; i < actions.length; i++) ...[
                  Expanded(child: actions[i]),
                  if (i < actions.length - 1) const SizedBox(width: 8),
                ],
              ],
            ),
          ],
        ],
      ),
    );
  }
}

/// Calm pulse shown only during actual network loading, never as a
/// permanent state. Customisable headline so callers can say e.g.
/// 'Loading your dashboard…' vs 'Reading your report card…'.
class _ProcessingPulse extends StatelessWidget {
  final String message;
  const _ProcessingPulse({this.message = 'Loading…'});

  @override
  Widget build(BuildContext context) {
    return Container(
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
      child: Row(
        children: [
          const SizedBox(
            width: 22,
            height: 22,
            child: CircularProgressIndicator(
              strokeWidth: 2.5,
              color: Colors.white,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(message,
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 15,
                        fontWeight: FontWeight.w800)),
                const SizedBox(height: 4),
                const Text(
                  'Pull down to refresh if this hangs.',
                  style: TextStyle(color: Colors.white70, fontSize: 12),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Big CTA shown when the user has no APS yet. Replaces the misleading
/// "Recommended for You / Recommended Bursaries" sections because we
/// can't honestly recommend without knowing their marks.
class _UnlockRecommendationsCta extends StatelessWidget {
  const _UnlockRecommendationsCta();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
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
          Row(
            children: const [
              Icon(Icons.auto_awesome, color: Colors.white, size: 22),
              SizedBox(width: 8),
              Text('Unlock personalised matches',
                  style: TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w800)),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            'Scan your report card or type your marks in — we\'ll calculate your APS and show only the courses and bursaries you actually qualify for.',
            style: TextStyle(color: Colors.white70, fontSize: 13, height: 1.45),
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => context.push('/scanner'),
                  icon: const Icon(Icons.document_scanner_outlined, size: 16),
                  label: const Text('Scan'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white,
                    foregroundColor: AppColors.primary,
                    minimumSize: const Size(0, 44),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => context.push('/manual-entry'),
                  icon: const Icon(Icons.edit_outlined,
                      size: 16, color: Colors.white),
                  label: const Text('Enter marks',
                      style: TextStyle(color: Colors.white)),
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: Colors.white70),
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

