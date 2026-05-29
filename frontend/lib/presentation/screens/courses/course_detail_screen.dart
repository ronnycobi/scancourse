import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/constants/app_constants.dart';
import '../../../providers/course_provider.dart';
import '../../../providers/aps_provider.dart';
import '../../../providers/auth_provider.dart';
import '../../../providers/application_provider.dart';
import '../../../data/models/course_model.dart';
import '../../widgets/common/bookmark_button.dart';
import '../../widgets/common/remote_logo.dart';

class CourseDetailScreen extends ConsumerStatefulWidget {
  final int id;

  const CourseDetailScreen({super.key, required this.id});

  @override
  ConsumerState<CourseDetailScreen> createState() => _CourseDetailScreenState();
}

class _CourseDetailScreenState extends ConsumerState<CourseDetailScreen> {
  @override
  void initState() {
    super.initState();
    // Record a 'view' interaction so the recommender learns.
    Future.microtask(() {
      ref.read(courseRepositoryProvider).trackInteraction(widget.id, 'view');
    });
  }

  /// Provinces the student cares about — their home province plus any
  /// preferred study provinces. Offerings in these rank first.
  Set<String> _userProvinces() {
    final user = ref.read(authStateProvider).user;
    final set = <String>{};
    if (user?.province != null && user!.province!.isNotEmpty) {
      set.add(user.province!);
    }
    set.addAll(user?.preferredStudyProvinces ?? const []);
    return set;
  }

  /// "City, Province" for a college, using the full province name.
  String _location(CourseOffering o) {
    final inst = o.institution;
    if (inst == null) return '';
    final city = (inst.city ?? '').trim();
    final prov = AppConstants.provinces[inst.province] ?? inst.province;
    if (city.isNotEmpty && prov.isNotEmpty) return '$city, $prov';
    return city.isNotEmpty ? city : prov;
  }

  /// Quality proxy for ranking colleges that are equally near: NSFAS
  /// accreditation + a real published APS cutoff + having an apply link.
  int _quality(CourseOffering o) {
    final inst = o.institution;
    var q = 0;
    if (inst?.nsfasAccredited == true) q += 2;
    if ((o.minAps) > 0) q += 1;
    if ((inst?.applicationUrl?.isNotEmpty == true) ||
        (inst?.website?.isNotEmpty == true)) q += 1;
    return q;
  }

  /// Nearby colleges first, then best-rated, then by name.
  List<CourseOffering> _sortedOfferings(List<CourseOffering> offerings) {
    final near = _userProvinces();
    final list = [...offerings];
    list.sort((a, b) {
      final aNear = near.contains(a.institution?.province) ? 0 : 1;
      final bNear = near.contains(b.institution?.province) ? 0 : 1;
      if (aNear != bNear) return aNear - bNear;
      final q = _quality(b).compareTo(_quality(a));
      if (q != 0) return q;
      return (a.institution?.name ?? '').compareTo(b.institution?.name ?? '');
    });
    return list;
  }

  /// Add this institution+course to the student's Applications board.
  Future<void> _trackApplication(
    BuildContext context,
    WidgetRef ref, {
    required int? institutionId,
    required int courseId,
    String? applyUrl,
    String? deadline,
  }) async {
    if (institutionId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Institution info missing.')),
      );
      return;
    }
    try {
      await ref.read(applicationRepositoryProvider).create(
            institutionId: institutionId,
            courseId: courseId,
            applicationUrl: applyUrl,
            deadline: deadline,
          );
      ref.invalidate(applicationListProvider);
      ref.invalidate(applicationStatsProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('Added to My Applications'),
            backgroundColor: AppColors.eligible,
            action: SnackBarAction(
              label: 'VIEW',
              textColor: Colors.white,
              onPressed: () => context.push('/applications'),
            ),
          ),
        );
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Could not add to applications. Try again.'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final courseAsync = ref.watch(courseDetailProvider(widget.id));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Course Details'),
        leading: BackButton(onPressed: () => context.pop()),
        actions: [
          BookmarkButton(itemType: 'course', itemId: widget.id),
        ],
      ),
      body: courseAsync.when(
        data: (course) => SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                course.name,
                style: Theme.of(context).textTheme.headlineSmall,
                softWrap: true,
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 6,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: AppColors.primaryLight,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(course.level.toUpperCase(),
                        style: const TextStyle(color: AppColors.primary, fontSize: 12, fontWeight: FontWeight.w600)),
                  ),
                  Text(AppConstants.studyFields[course.field] ?? course.field,
                      style: Theme.of(context).textTheme.bodyMedium),
                ],
              ),
              const SizedBox(height: 20),

              _InfoRow(icon: Icons.timer_outlined, label: 'Duration', value: '${course.durationYears ?? "?"} years'),
              if (course.feesPerYear != null)
                _InfoRow(icon: Icons.attach_money, label: 'Fees (est.)',
                    value: 'R${course.feesPerYear!.toStringAsFixed(0)}/year'),
              if (course.salaryMin != null && course.salaryMax != null)
                _InfoRow(icon: Icons.trending_up, label: 'Avg Salary',
                    value: 'R${course.salaryMin!.toStringAsFixed(0)} - R${course.salaryMax!.toStringAsFixed(0)}/month'),

              const SizedBox(height: 20),
              if (course.description?.isNotEmpty == true) ...[
                Text('About this course', style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 8),
                Text(course.description!, style: Theme.of(context).textTheme.bodyMedium),
                const SizedBox(height: 20),
              ],

              if (course.careerOpportunities?.isNotEmpty == true) ...[
                Text('Career Opportunities', style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 8),
                Text(course.careerOpportunities!, style: Theme.of(context).textTheme.bodyMedium),
                const SizedBox(height: 20),
              ],

              if (course.offerings?.isNotEmpty == true) ...[
                Text('Institutions Offering This', style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 4),
                Text(
                  'Closest to you first',
                  style: TextStyle(fontSize: 12, color: AppColors.textHint),
                ),
                const SizedBox(height: 12),
                ..._sortedOfferings(course.offerings!).map((o) {
                  // Prefer offering-level apply URL, then institution apply URL,
                  // finally fall back to the institution's website.
                  final applyUrl = (o.applicationUrl?.isNotEmpty == true)
                      ? o.applicationUrl!
                      : (o.institution?.applicationUrl?.isNotEmpty == true)
                          ? o.institution!.applicationUrl!
                          : (o.institution?.website?.isNotEmpty == true)
                              ? o.institution!.website!
                              : null;
                  final isFallback = applyUrl != null &&
                      (o.applicationUrl == null || o.applicationUrl!.isEmpty);
                  return Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.center,
                          children: [
                            RemoteLogo(
                              url: o.institution?.logoUrl,
                              fallbackInitial:
                                  o.institution?.shortName?.isNotEmpty == true
                                      ? o.institution!.shortName![0]
                                      : (o.institution?.name.isNotEmpty == true
                                          ? o.institution!.name[0]
                                          : 'U'),
                              size: 42,
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    o.institution?.name ?? 'Unknown',
                                    style: const TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.w700,
                                      color: AppColors.textPrimary,
                                    ),
                                    softWrap: true,
                                  ),
                                  if (_location(o).isNotEmpty) ...[
                                    const SizedBox(height: 2),
                                    Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        const Icon(Icons.place_outlined,
                                            size: 13,
                                            color: AppColors.textSecondary),
                                        const SizedBox(width: 3),
                                        Flexible(
                                          child: Text(
                                            _location(o),
                                            style: const TextStyle(
                                              fontSize: 12.5,
                                              color: AppColors.textSecondary,
                                              fontWeight: FontWeight.w500,
                                            ),
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 16,
                          runSpacing: 4,
                          children: [
                            Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(Icons.auto_awesome, size: 14, color: AppColors.primary),
                                const SizedBox(width: 4),
                                Text('Min APS: ${o.minAps}',
                                    style: Theme.of(context).textTheme.bodyMedium),
                              ],
                            ),
                            if (o.applicationDeadline != null)
                              Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(Icons.calendar_today, size: 14, color: AppColors.accent),
                                  const SizedBox(width: 4),
                                  Text('Closes: ${o.applicationDeadline}',
                                      style: Theme.of(context).textTheme.bodyMedium),
                                ],
                              ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: [
                            // Track → adds this institution+course to the
                            // student's Applications (Kanban) board.
                            OutlinedButton.icon(
                              onPressed: () => _trackApplication(
                                context, ref,
                                institutionId: o.institution?.id,
                                courseId: course.id,
                                applyUrl: applyUrl,
                                deadline: o.applicationDeadline,
                              ),
                              icon: const Icon(Icons.bookmark_add_outlined,
                                  size: 16),
                              label: const Text('Track'),
                              style: OutlinedButton.styleFrom(
                                foregroundColor: AppColors.primary,
                                minimumSize: const Size(0, 34),
                                tapTargetSize:
                                    MaterialTapTargetSize.shrinkWrap,
                                textStyle: const TextStyle(
                                    fontSize: 13, fontWeight: FontWeight.w600),
                              ),
                            ),
                            const SizedBox(width: 8),
                            ElevatedButton(
                              onPressed: applyUrl != null
                                  ? () => launchUrl(
                                        Uri.parse(applyUrl),
                                        mode: LaunchMode.externalApplication,
                                      )
                                  : () {},
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppColors.primary,
                                foregroundColor: Colors.white,
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 16, vertical: 8),
                                minimumSize: const Size(0, 34),
                                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                textStyle: const TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w600,
                                ),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(8),
                                ),
                              ),
                              child: const Text('Apply'),
                            ),
                          ],
                        ),
                      ],
                    ),
                  );
                }),
              ],

              const SizedBox(height: 16),
              // Career outcomes CTA — high-trust feature
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [AppColors.secondary, AppColors.primary],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.trending_up, color: Colors.white, size: 32),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Career Outcomes',
                              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                color: Colors.white, fontWeight: FontWeight.w700,
                              )),
                          Text('Employment rates · Salaries · Top employers',
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.white70)),
                        ],
                      ),
                    ),
                    IconButton(
                      onPressed: () => context.push('/outcomes/${widget.id}'),
                      icon: const Icon(Icons.arrow_forward, color: Colors.white),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              // Gemini-powered: "Do I qualify and why?"
              OutlinedButton.icon(
                onPressed: () => _showExplainSheet(context, ref, widget.id),
                icon: const Icon(Icons.psychology_alt_outlined),
                label: const Text('Do I qualify? Ask AI'),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 44),
                ),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: () => context.push('/ai'),
                icon: const Icon(Icons.auto_awesome),
                label: const Text('Ask AI about this course'),
              ),
            ],
          ),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoRow({required this.icon, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Icon(icon, size: 18, color: AppColors.primary),
          const SizedBox(width: 10),
          Text('$label:', style: Theme.of(context).textTheme.bodyMedium),
          const SizedBox(width: 8),
          Expanded(child: Text(value, style: Theme.of(context).textTheme.titleMedium)),
        ],
      ),
    );
  }
}

/// Shows a bottom sheet with the Gemini-generated "do I qualify and why" answer.
void _showExplainSheet(BuildContext context, WidgetRef ref, int courseId) {
  showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (_) => _ExplainGapSheet(courseId: courseId),
  );
}

class _ExplainGapSheet extends ConsumerStatefulWidget {
  final int courseId;
  const _ExplainGapSheet({required this.courseId});
  @override
  ConsumerState<_ExplainGapSheet> createState() => _ExplainGapSheetState();
}

class _ExplainGapSheetState extends ConsumerState<_ExplainGapSheet> {
  late Future<Map<String, dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = ref.read(ocrRepositoryProvider).explainCourseGap(widget.courseId);
  }

  Color _verdictColor(String v) {
    switch (v) {
      case 'qualify':
        return AppColors.eligible;
      case 'subject_gap':
        return AppColors.subjectGap;
      case 'aps_gap':
        return AppColors.apsGap;
      case 'both':
        return AppColors.error;
      default:
        return AppColors.textSecondary;
    }
  }

  String _verdictLabel(String v) {
    switch (v) {
      case 'qualify':
        return 'You qualify ✅';
      case 'subject_gap':
        return 'Subject gap';
      case 'aps_gap':
        return 'APS short';
      case 'both':
        return 'Subject + APS gap';
      default:
        return 'Checking…';
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: FutureBuilder<Map<String, dynamic>>(
          future: _future,
          builder: (ctx, snap) {
            if (snap.connectionState != ConnectionState.done) {
              return const SizedBox(
                height: 220,
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.psychology_alt_outlined,
                          color: AppColors.primary, size: 32),
                      SizedBox(height: 12),
                      CircularProgressIndicator(strokeWidth: 3),
                      SizedBox(height: 16),
                      Text('Checking your marks against this course…'),
                    ],
                  ),
                ),
              );
            }
            if (snap.hasError) {
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 40),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.error_outline,
                        color: AppColors.error, size: 40),
                    const SizedBox(height: 12),
                    const Text(
                      'Add your marks first so we can compare them to this course.',
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 16),
                    OutlinedButton(
                      onPressed: () {
                        Navigator.pop(context);
                        context.push('/scanner');
                      },
                      child: const Text('Scan your report'),
                    ),
                  ],
                ),
              );
            }
            final data = snap.data!;
            final verdict = (data['verdict'] as String?) ?? 'unknown';
            final explanation = (data['explanation'] as String?) ?? '';
            final actions =
                ((data['action_items'] as List?) ?? const []).cast<String>();
            return Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 40,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 14),
                  decoration: BoxDecoration(
                    color: AppColors.border,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                Row(
                  children: [
                    const Icon(Icons.psychology_alt_outlined,
                        color: AppColors.primary),
                    const SizedBox(width: 8),
                    const Text('AI verdict',
                        style: TextStyle(
                            fontSize: 16, fontWeight: FontWeight.w700)),
                    const Spacer(),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: _verdictColor(verdict).withOpacity(0.12),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        _verdictLabel(verdict),
                        style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: _verdictColor(verdict)),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                Text(
                  explanation,
                  style: const TextStyle(
                      fontSize: 14, height: 1.5, color: AppColors.textPrimary),
                ),
                if (actions.isNotEmpty) ...[
                  const SizedBox(height: 16),
                  const Text('What to do',
                      style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                          color: AppColors.textSecondary)),
                  const SizedBox(height: 8),
                  ...actions.map(
                    (a) => Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(Icons.check_circle_outline,
                              size: 18, color: AppColors.primary),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(a,
                                style: const TextStyle(
                                    fontSize: 13, height: 1.45)),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: 14),
                Text(
                  'AI suggestions can be wrong — always verify with the university.',
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
