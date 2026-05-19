import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/constants/app_constants.dart';
import '../../../providers/course_provider.dart';
import '../../../providers/aps_provider.dart';
import '../../../data/models/course_model.dart';
import '../../widgets/common/remote_logo.dart';

class CoursesScreen extends ConsumerStatefulWidget {
  const CoursesScreen({super.key});

  @override
  ConsumerState<CoursesScreen> createState() => _CoursesScreenState();
}

class _CoursesScreenState extends ConsumerState<CoursesScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabCtrl;
  static const _categories = ['eligible', 'subject_gap', 'aps_gap'];
  static const _tabLabels = ['Qualify ✅', 'Subject Gap 📚', 'APS Gap 📊'];
  static const _pageSize = 20;

  final TextEditingController _searchCtrl = TextEditingController();
  String _query = '';
  Timer? _searchDebounce;
  // Page index per tab category — reset to 0 when filters/search change.
  final Map<String, int> _pageByCat = {'eligible': 0, 'subject_gap': 0, 'aps_gap': 0};

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: 3, vsync: this);
    _tabCtrl.addListener(() {
      if (!_tabCtrl.indexIsChanging) {
        ref.read(courseFilterProvider.notifier).setCategory(_categories[_tabCtrl.index]);
        setState(() {});
      }
    });
  }

  @override
  void dispose() {
    _tabCtrl.dispose();
    _searchCtrl.dispose();
    _searchDebounce?.cancel();
    super.dispose();
  }

  void _resetPagination() {
    _pageByCat.updateAll((_, __) => 0);
  }

  String? _lastParamStr;

  @override
  Widget build(BuildContext context) {
    final filter = ref.watch(courseFilterProvider);
    final paramParts = [
      if (filter.field != null) 'field=${filter.field}',
      if (filter.province != null) 'province=${filter.province}',
      if (filter.institutionType != null) 'type=${filter.institutionType}',
      if (_query.isNotEmpty) 'search=${Uri.encodeComponent(_query)}',
    ];
    final paramStr = paramParts.isEmpty ? null : paramParts.join('&');
    if (paramStr != _lastParamStr) {
      _lastParamStr = paramStr;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) setState(_resetPagination);
      });
    }
    final apsAsync = ref.watch(latestApsProvider);
    // Show personalised matcher only when the user has an APS result;
    // otherwise fall back to a plain browse-and-search experience.
    final hasAps = apsAsync.valueOrNull != null;
    final matchAsync =
        hasAps ? ref.watch(courseMatchProvider(paramStr)) : null;
    final listAsync =
        hasAps ? null : ref.watch(courseListProvider(paramStr));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Find Courses'),
        bottom: hasAps
            ? TabBar(
                controller: _tabCtrl,
                tabs: _tabLabels.map((l) => Tab(text: l)).toList(),
                labelColor: AppColors.primary,
                unselectedLabelColor: AppColors.textSecondary,
                indicatorColor: AppColors.primary,
                isScrollable: true,
                tabAlignment: TabAlignment.start,
              )
            : null,
      ),
      body: Column(
        children: [
          // Search input
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: TextField(
              controller: _searchCtrl,
              textInputAction: TextInputAction.search,
              decoration: InputDecoration(
                hintText: 'Search courses or universities…',
                prefixIcon: const Icon(Icons.search, size: 20, color: AppColors.textHint),
                suffixIcon: (_searchCtrl.text.isEmpty && _query.isEmpty)
                    ? null
                    : IconButton(
                        icon: const Icon(Icons.close, size: 18),
                        onPressed: () {
                          // Kill any pending debounce so it can't re-apply
                          // the previous query after we've cleared.
                          _searchDebounce?.cancel();
                          _searchCtrl.clear();
                          FocusScope.of(context).unfocus();
                          setState(() {
                            _query = '';
                            _resetPagination();
                          });
                        },
                      ),
                isDense: true,
                contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                filled: true,
                fillColor: AppColors.surface,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
              ),
              onChanged: (v) {
                _searchDebounce?.cancel();
                _searchDebounce = Timer(const Duration(milliseconds: 350), () {
                  if (!mounted) return;
                  setState(() {
                    _query = v.trim().toLowerCase();
                    _resetPagination();
                  });
                });
              },
            ),
          ),

          // Filter bar
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  _FilterChip(
                    label: 'Field',
                    value: filter.field,
                    options: AppConstants.studyFields,
                    onSelected: (v) =>
                        ref.read(courseFilterProvider.notifier).setField(v),
                  ),
                  const SizedBox(width: 8),
                  _FilterChip(
                    label: 'Province',
                    value: filter.province,
                    options: AppConstants.provinces,
                    onSelected: (v) =>
                        ref.read(courseFilterProvider.notifier).setProvince(v),
                  ),
                  const SizedBox(width: 8),
                  _FilterChip(
                    label: 'Type',
                    value: filter.institutionType,
                    options: const {
                      'university': 'University',
                      'university_of_technology': 'University of Technology',
                      'tvet': 'TVET College',
                      'private': 'Private',
                    },
                    onSelected: (v) =>
                        ref.read(courseFilterProvider.notifier).setInstitutionType(v),
                  ),
                  const SizedBox(width: 8),
                  apsAsync.when(
                    data: (aps) => aps != null
                        ? Chip(
                            avatar: const Icon(Icons.stars,
                                size: 16, color: AppColors.primary),
                            label: Text('APS ${aps.totalAps}',
                                style: const TextStyle(
                                    color: AppColors.primary,
                                    fontWeight: FontWeight.w600)),
                            backgroundColor: AppColors.primaryLight,
                            side: BorderSide.none,
                          )
                        : const SizedBox.shrink(),
                    loading: () => const SizedBox.shrink(),
                    error: (_, __) => const SizedBox.shrink(),
                  ),
                ],
              ),
            ),
          ),

          // Browse-mode banner: invites no-APS users to scan for personalised matches.
          if (!hasAps)
            Container(
              margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.primaryLight,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Row(
                children: [
                  const Icon(Icons.auto_awesome,
                      size: 18, color: AppColors.primary),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      'Scan your marks for personalised matches',
                      style: TextStyle(
                          color: AppColors.primary,
                          fontSize: 13,
                          fontWeight: FontWeight.w600),
                    ),
                  ),
                  TextButton(
                    onPressed: () => context.push('/scanner'),
                    style: TextButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 8),
                        minimumSize: const Size(0, 32)),
                    child: const Text('Scan'),
                  ),
                ],
              ),
            ),

          // Results: matcher when APS, plain list when no APS.
          Expanded(
            child: hasAps
                ? _buildMatcherBody(context, ref, matchAsync!, paramStr)
                : _buildBrowseBody(context, ref, listAsync!, paramStr),
          ),
        ],
      ),
    );
  }

  Widget _buildBrowseBody(
    BuildContext context,
    WidgetRef ref,
    AsyncValue<List<CourseModel>> async,
    String? paramStr,
  ) {
    return async.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.wifi_off_outlined,
                  size: 56, color: AppColors.textHint),
              const SizedBox(height: 12),
              Text(
                e.toString().contains('timed out')
                    ? 'Connection timed out'
                    : 'Could not load courses',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: () =>
                    ref.invalidate(courseListProvider(paramStr)),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      ),
      data: (courses) {
        if (courses.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.search_off,
                    size: 56, color: AppColors.textHint),
                const SizedBox(height: 12),
                Text('No courses found',
                    style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 6),
                const Text('Try adjusting your filters or search term',
                    style: TextStyle(color: AppColors.textSecondary)),
              ],
            ),
          );
        }
        final pageSize = _pageSize;
        final totalPages = (courses.length / pageSize).ceil().clamp(1, 9999);
        int currentPage = _pageByCat['eligible'] ?? 0;
        if (currentPage >= totalPages) currentPage = totalPages - 1;
        if (currentPage < 0) currentPage = 0;
        final start = currentPage * pageSize;
        final end = (start + pageSize).clamp(0, courses.length);
        final pageCourses = courses.sublist(start, end);

        return Column(
          children: [
            Expanded(
              child: ListView.separated(
                padding: const EdgeInsets.symmetric(
                    horizontal: 16, vertical: 8),
                itemCount: pageCourses.length,
                separatorBuilder: (_, __) => const SizedBox(height: 10),
                itemBuilder: (_, i) => _BrowseCourseCard(
                  course: pageCourses[i],
                  onTap: () =>
                      context.push('/courses/${pageCourses[i].id}'),
                ),
              ),
            ),
            if (totalPages > 1)
              _PaginationBar(
                currentPage: currentPage,
                totalPages: totalPages,
                totalResults: courses.length,
                onPageChanged: (p) =>
                    setState(() => _pageByCat['eligible'] = p),
              ),
          ],
        );
      },
    );
  }

  Widget _buildMatcherBody(
    BuildContext context,
    WidgetRef ref,
    AsyncValue<Map<String, dynamic>> matchAsync,
    String? paramStr,
  ) {
    return matchAsync.when(
              data: (data) {
                final summary =
                    data['summary'] as Map<String, dynamic>? ?? {};
                final allResults = (data['results'] as List? ?? [])
                    .map((e) => OfferingMatchModel.fromJson(
                        Map<String, dynamic>.from(e as Map)))
                    .toList();

                final category = _categories[_tabCtrl.index];
                final results = allResults
                    .where((r) => r.match.category == category)
                    .toList();

                final totalPages =
                    (results.length / _pageSize).ceil().clamp(1, 9999);
                int currentPage = _pageByCat[category] ?? 0;
                if (currentPage >= totalPages) currentPage = totalPages - 1;
                if (currentPage < 0) currentPage = 0;
                final pageStart = currentPage * _pageSize;
                final pageEnd = (pageStart + _pageSize).clamp(0, results.length);
                final pageResults = results.isEmpty
                    ? <OfferingMatchModel>[]
                    : results.sublist(pageStart, pageEnd);

                return Column(
                  children: [
                    _SummaryRow(summary: summary),
                    Expanded(
                      child: results.isEmpty
                          ? Center(
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(
                                    category == 'eligible'
                                        ? Icons.check_circle_outline
                                        : Icons.search_off,
                                    size: 64,
                                    color: AppColors.textHint,
                                  ),
                                  const SizedBox(height: 16),
                                  Text(
                                    category == 'eligible'
                                        ? 'No eligible courses found'
                                        : 'No results in this category',
                                    style: Theme.of(context)
                                        .textTheme
                                        .titleMedium,
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    'Try adjusting your filters',
                                    style:
                                        Theme.of(context).textTheme.bodyMedium,
                                  ),
                                ],
                              ),
                            )
                          : Column(
                              children: [
                                Expanded(
                                  child: ListView.separated(
                                    padding: const EdgeInsets.symmetric(
                                        horizontal: 16, vertical: 8),
                                    itemCount: pageResults.length,
                                    separatorBuilder: (_, __) =>
                                        const SizedBox(height: 10),
                                    itemBuilder: (context, i) => _OfferingCard(
                                      offering: pageResults[i],
                                      onTap: () => context.push(
                                          '/courses/${pageResults[i].courseId}'),
                                    ),
                                  ),
                                ),
                                if (totalPages > 1)
                                  _PaginationBar(
                                    currentPage: currentPage,
                                    totalPages: totalPages,
                                    totalResults: results.length,
                                    onPageChanged: (p) => setState(
                                        () => _pageByCat[category] = p),
                                  ),
                              ],
                            ),
                    ),
                  ],
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) {
                final msg = e.toString();
                if (msg.contains('400') || msg.contains('APS result') || msg.contains('No APS')) {
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.all(32),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.document_scanner_outlined,
                              size: 64, color: AppColors.textHint),
                          const SizedBox(height: 16),
                          Text('No APS result yet',
                              style: Theme.of(context).textTheme.titleLarge),
                          const SizedBox(height: 8),
                          Text(
                            'Scan your report card or enter your marks to see personalised course matches.',
                            style: Theme.of(context).textTheme.bodyMedium,
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 24),
                          ElevatedButton.icon(
                            onPressed: () => context.push('/scanner'),
                            icon: const Icon(Icons.document_scanner_outlined),
                            label: const Text('Scan Report Card'),
                          ),
                          const SizedBox(height: 12),
                          OutlinedButton.icon(
                            onPressed: () => context.push('/manual-entry'),
                            icon: const Icon(Icons.edit_outlined),
                            label: const Text('Enter Marks Manually'),
                          ),
                        ],
                      ),
                    ),
                  );
                }
                return Center(
                  child: Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.wifi_off_outlined, size: 64, color: AppColors.textHint),
                        const SizedBox(height: 16),
                        Text(
                          msg.contains('timed out') ? 'Connection timed out' : 'Could not load courses',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 8),
                        Text('Check your connection and try again',
                            style: Theme.of(context).textTheme.bodySmall,
                            textAlign: TextAlign.center),
                        const SizedBox(height: 20),
                        ElevatedButton(
                          onPressed: () => ref.invalidate(courseMatchProvider(paramStr)),
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                );
              },
            );
  }
}

class _BrowseCourseCard extends StatelessWidget {
  final CourseModel course;
  final VoidCallback onTap;
  const _BrowseCourseCard({required this.course, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              course.name,
              style: const TextStyle(
                  fontSize: 15, fontWeight: FontWeight.w700),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 6,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppColors.primaryLight,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    course.level.toUpperCase().replaceAll('_', ' '),
                    style: const TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w600,
                        color: AppColors.primary),
                  ),
                ),
                if (course.minAps != null)
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppColors.surface,
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: Text(
                      'APS ${course.minAps}+',
                      style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textSecondary),
                    ),
                  ),
                Text(
                  AppConstants.studyFields[course.field] ?? course.field,
                  style: const TextStyle(
                      fontSize: 12, color: AppColors.textSecondary),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _SummaryRow extends StatelessWidget {
  final Map<String, dynamic> summary;
  const _SummaryRow({required this.summary});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: Row(
        children: [
          _SummaryChip(
              count: summary['eligible'] ?? 0,
              label: 'Qualify',
              color: AppColors.eligible),
          const SizedBox(width: 8),
          _SummaryChip(
              count: summary['subject_gap'] ?? 0,
              label: 'Gap',
              color: AppColors.subjectGap),
          const SizedBox(width: 8),
          _SummaryChip(
              count: summary['aps_gap'] ?? 0,
              label: 'APS Short',
              color: AppColors.apsGap),
          const Spacer(),
          Text(
            '${(summary['eligible'] ?? 0) + (summary['subject_gap'] ?? 0) + (summary['aps_gap'] ?? 0)} matches',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}

class _SummaryChip extends StatelessWidget {
  final int count;
  final String label;
  final Color color;
  const _SummaryChip(
      {required this.count, required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        '$count $label',
        style: TextStyle(
            color: color, fontSize: 11, fontWeight: FontWeight.w600),
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  final String label;
  final String? value;
  final Map<String, String> options;
  final void Function(String?) onSelected;
  const _FilterChip(
      {required this.label,
      this.value,
      required this.options,
      required this.onSelected});

  @override
  Widget build(BuildContext context) {
    return ActionChip(
      avatar: Icon(Icons.filter_list,
          size: 16,
          color: value != null ? AppColors.primary : AppColors.textHint),
      label: Text(
          value != null ? (options[value] ?? label) : label,
          style: TextStyle(
              color: value != null
                  ? AppColors.primary
                  : AppColors.textSecondary,
              fontSize: 13)),
      backgroundColor:
          value != null ? AppColors.primaryLight : Colors.white,
      side: BorderSide(
          color: value != null ? AppColors.primary : AppColors.border),
      onPressed: () async {
        final selected = await showModalBottomSheet<String>(
          context: context,
          builder: (_) => _PickerSheet(options: options, current: value),
        );
        // null means dismissed without choosing OR clear was tapped
        // only call onSelected if user actively made a choice (non-null key)
        // or if there was a prior value (meaning clear was tapped)
        if (selected != null || value != null) {
          onSelected(selected);
        }
      },
    );
  }
}

class _PickerSheet extends StatelessWidget {
  final Map<String, String> options;
  final String? current;
  const _PickerSheet({required this.options, this.current});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            margin: const EdgeInsets.symmetric(vertical: 8),
            width: 40,
            height: 4,
            decoration: BoxDecoration(
                color: AppColors.border,
                borderRadius: BorderRadius.circular(2)),
          ),
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 8, 16, 0),
            child: Text('Select an option',
                style:
                    TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
          ),
          if (current != null)
            ListTile(
              leading: const Icon(Icons.clear, color: AppColors.error),
              title: const Text('Clear filter'),
              onTap: () => Navigator.pop(context, null),
            ),
          Flexible(
            child: ListView(
              shrinkWrap: true,
              children: options.entries
                  .map((e) => ListTile(
                        trailing: current == e.key
                            ? const Icon(Icons.check,
                                color: AppColors.primary)
                            : null,
                        title: Text(e.value),
                        onTap: () => Navigator.pop(context, e.key),
                      ))
                  .toList(),
            ),
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}

class _OfferingCard extends StatelessWidget {
  final OfferingMatchModel offering;
  final VoidCallback onTap;
  const _OfferingCard({required this.offering, required this.onTap});

  Color get _categoryColor {
    switch (offering.match.category) {
      case 'eligible':
        return AppColors.eligible;
      case 'subject_gap':
        return AppColors.subjectGap;
      case 'aps_gap':
        return AppColors.apsGap;
      default:
        return AppColors.textSecondary;
    }
  }

  String get _categoryLabel {
    switch (offering.match.category) {
      case 'eligible':
        return 'Qualify';
      case 'subject_gap':
        return 'Subject Gap';
      case 'aps_gap':
        return 'APS Short';
      default:
        return 'Not Qualified';
    }
  }

  @override
  Widget build(BuildContext context) {
    final m = offering.match;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Course name + match badge
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(offering.courseName,
                      style: Theme.of(context).textTheme.titleMedium),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: _categoryColor.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    _categoryLabel,
                    style: TextStyle(
                        color: _categoryColor,
                        fontSize: 11,
                        fontWeight: FontWeight.w600),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),

            // Institution — logo + bold name + city
            Row(
              children: [
                RemoteLogo(
                  url: offering.institutionLogoUrl,
                  fallbackInitial: offering.institutionShort?.isNotEmpty == true
                      ? offering.institutionShort!
                      : offering.institutionName,
                  size: 32,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: RichText(
                    overflow: TextOverflow.ellipsis,
                    text: TextSpan(
                      children: [
                        TextSpan(
                          text: offering.institutionName,
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w700,
                            color: AppColors.textPrimary,
                          ),
                        ),
                        if (offering.institutionCity != null)
                          TextSpan(
                            text: ' · ${offering.institutionCity}',
                            style: const TextStyle(
                              fontSize: 12,
                              color: AppColors.textSecondary,
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Text(offering.institutionProvince,
                      style: const TextStyle(
                          fontSize: 10,
                          color: AppColors.textSecondary)),
                ),
              ],
            ),
            const SizedBox(height: 10),

            // Info chips row
            Row(
              children: [
                _InfoChip(
                    icon: Icons.auto_awesome,
                    label: 'APS ${offering.minAps}'),
                const SizedBox(width: 6),
                _InfoChip(
                    icon: Icons.schedule,
                    label:
                        '${offering.courseDurationYears?.toStringAsFixed(0) ?? "?"} yr'),
                const SizedBox(width: 6),
                _InfoChip(
                  icon: Icons.category_outlined,
                  label: AppConstants.studyFields[offering.courseField] ??
                      offering.courseField,
                  maxWidth: 110,
                ),
                const Spacer(),
                if (m.category == 'eligible' && m.apsSurplus > 0)
                  Text('+${m.apsSurplus} APS',
                      style: const TextStyle(
                          color: AppColors.eligible,
                          fontSize: 11,
                          fontWeight: FontWeight.w600))
                else if (m.category == 'aps_gap')
                  Text('${m.apsSurplus} APS',
                      style: const TextStyle(
                          color: AppColors.apsGap,
                          fontSize: 11,
                          fontWeight: FontWeight.w600)),
              ],
            ),

            // Subject gap detail
            if (m.missingSubjects.isNotEmpty ||
                m.lowSubjects.isNotEmpty) ...[
              const SizedBox(height: 8),
              const Divider(height: 1),
              const SizedBox(height: 8),
              if (m.mathsLitBlocked)
                _GapRow(
                    icon: Icons.block,
                    label:
                        'Requires Pure Maths (Maths Lit not accepted)',
                    color: AppColors.error),
              ...m.missingSubjects.take(2).map((s) => _GapRow(
                    icon: Icons.add_circle_outline,
                    label:
                        'Needs ${s['subject']} (level ${s['required_level']})',
                    color: AppColors.subjectGap,
                  )),
              ...m.lowSubjects.take(2).map((s) => _GapRow(
                    icon: Icons.trending_up,
                    label:
                        '${s['subject']}: level ${s['student_level']} → need ${s['required_level']}',
                    color: AppColors.apsGap,
                  )),
              if ((m.missingSubjects.length + m.lowSubjects.length) > 4)
                Text(
                  '+${m.missingSubjects.length + m.lowSubjects.length - 4} more requirements',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
            ],
          ],
        ),
      ),
    );
  }
}

class _GapRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  const _GapRow(
      {required this.icon, required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        children: [
          Icon(icon, size: 13, color: color),
          const SizedBox(width: 6),
          Expanded(
              child: Text(label,
                  style: TextStyle(fontSize: 12, color: color))),
        ],
      ),
    );
  }
}

class _InfoChip extends StatelessWidget {
  final IconData icon;
  final String label;
  final double? maxWidth;
  const _InfoChip({required this.icon, required this.label, this.maxWidth});

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints:
          maxWidth != null ? BoxConstraints(maxWidth: maxWidth!) : null,
      padding:
          const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 11, color: AppColors.textSecondary),
          const SizedBox(width: 3),
          Flexible(
            child: Text(label,
                style: const TextStyle(
                    fontSize: 11, color: AppColors.textSecondary),
                overflow: TextOverflow.ellipsis),
          ),
        ],
      ),
    );
  }
}

class _PaginationBar extends StatelessWidget {
  final int currentPage;
  final int totalPages;
  final int totalResults;
  final ValueChanged<int> onPageChanged;

  const _PaginationBar({
    required this.currentPage,
    required this.totalPages,
    required this.totalResults,
    required this.onPageChanged,
  });

  @override
  Widget build(BuildContext context) {
    final showing = '${currentPage * 20 + 1}–${((currentPage + 1) * 20).clamp(0, totalResults)} of $totalResults';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        children: [
          Text(showing,
              style: const TextStyle(
                  fontSize: 12, color: AppColors.textSecondary)),
          const Spacer(),
          IconButton(
            visualDensity: VisualDensity.compact,
            icon: const Icon(Icons.chevron_left),
            onPressed: currentPage > 0
                ? () => onPageChanged(currentPage - 1)
                : null,
          ),
          Text('${currentPage + 1} / $totalPages',
              style: const TextStyle(
                  fontWeight: FontWeight.w600, color: AppColors.textPrimary)),
          IconButton(
            visualDensity: VisualDensity.compact,
            icon: const Icon(Icons.chevron_right),
            onPressed: currentPage < totalPages - 1
                ? () => onPageChanged(currentPage + 1)
                : null,
          ),
        ],
      ),
    );
  }
}
