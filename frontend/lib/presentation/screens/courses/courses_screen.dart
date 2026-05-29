import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/constants/app_constants.dart';
import '../../../providers/course_provider.dart';
import '../../../providers/aps_provider.dart';
import '../../../data/models/course_model.dart';
import '../../widgets/common/bookmark_button.dart';

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
    final searching = _query.isNotEmpty;
    // While searching, IGNORE the field/province/type filter chips and hit
    // the whole catalogue for the search term — "bring what the user
    // searched for, whatever is in the DB". The chips only constrain the
    // personalised browse/matcher views, not free-text search.
    final paramParts = searching
        ? ['search=${Uri.encodeComponent(_query)}']
        : [
            if (filter.field != null) 'field=${filter.field}',
            if (filter.province != null) 'province=${filter.province}',
            if (filter.institutionType != null)
              'institution_type=${filter.institutionType}',
          ];
    final paramStr = paramParts.isEmpty ? null : paramParts.join('&');
    if (paramStr != _lastParamStr) {
      _lastParamStr = paramStr;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) setState(_resetPagination);
      });
    }
    final apsAsync = ref.watch(latestApsProvider);
    final reportsAsync = ref.watch(reportListProvider);
    // Show personalised matcher only when the user has an APS result;
    // otherwise fall back to a plain browse-and-search experience.
    final hasAps = apsAsync.valueOrNull != null;
    // Hide the "scan your marks" banner once the user has uploaded ANY report,
    // even if the OCR is still pending and APS is 0.
    final hasReports = (reportsAsync.valueOrNull?.isNotEmpty) ?? false;
    // Three modes:
    //  • searching + has APS → ranked, comprehensive search (best-fit-first,
    //    every matching course shown — qualify or not).
    //  • not searching + has APS → personalised matcher with Qualify/Gap tabs.
    //  • no APS → plain DB browse/search.
    final isSearching = _query.isNotEmpty;
    final searchWithAps = isSearching && hasAps;
    final showMatcher = hasAps && !isSearching;
    final matchAsync =
        showMatcher ? ref.watch(courseMatchProvider(paramStr)) : null;
    final searchAsync =
        searchWithAps ? ref.watch(courseSearchProvider(_query)) : null;
    final listAsync = hasAps ? null : ref.watch(courseListProvider(paramStr));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Find Courses'),
        bottom: showMatcher
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

          // Browse-mode banner: invites users with no APS *and* no reports
          // to scan for personalised matches. Hide as soon as they've uploaded
          // anything — pestering them with "Scan your marks" looks broken.
          if (!hasAps && !hasReports)
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

          // Results: ranked search (APS users) → matcher tabs → plain browse.
          Expanded(
            child: searchWithAps
                ? _buildSearchBody(context, ref, searchAsync!)
                : showMatcher
                    ? _buildMatcherBody(context, ref, matchAsync!, paramStr)
                    : _buildBrowseBody(context, ref, listAsync!, paramStr),
          ),
        ],
      ),
    );
  }

  /// Ranked search results — one flat best-fit-first list, every matching
  /// course (qualify or not), each card showing its verdict.
  Widget _buildSearchBody(
    BuildContext context,
    WidgetRef ref,
    AsyncValue<List<OfferingMatchModel>> async,
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
              const Text('Could not run your search'),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: () => ref.invalidate(courseSearchProvider(_query)),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      ),
      data: (results) {
        if (results.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.search_off, size: 56, color: AppColors.textHint),
                const SizedBox(height: 12),
                Text('No courses match "$_query"',
                    style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 6),
                const Text('Try a different word or check the spelling',
                    style: TextStyle(color: AppColors.textSecondary)),
              ],
            ),
          );
        }
        return ListView.separated(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
          physics: const AlwaysScrollableScrollPhysics(),
          itemCount: results.length,
          separatorBuilder: (_, __) => const SizedBox(height: 10),
          itemBuilder: (_, i) => _OfferingCard(
            offering: results[i],
            onTap: () => context.push('/courses/${results[i].courseId}'),
          ),
        );
      },
    );
  }

  Future<void> _refreshAll(WidgetRef ref, String? paramStr) async {
    ref.invalidate(latestApsProvider);
    ref.invalidate(reportListProvider);
    ref.invalidate(courseListProvider(paramStr));
    ref.invalidate(courseMatchProvider(paramStr));
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
              child: RefreshIndicator(
                onRefresh: () => _refreshAll(ref, paramStr),
                child: ListView.separated(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 16, vertical: 8),
                  physics: const AlwaysScrollableScrollPhysics(),
                  itemCount: pageCourses.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (_, i) => _BrowseCourseCard(
                    course: pageCourses[i],
                    onTap: () =>
                        context.push('/courses/${pageCourses[i].id}'),
                  ),
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
                                  child: RefreshIndicator(
                                    onRefresh: () => _refreshAll(ref, paramStr),
                                    child: ListView.separated(
                                      padding: const EdgeInsets.symmetric(
                                          horizontal: 16, vertical: 8),
                                      physics: const AlwaysScrollableScrollPhysics(),
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

/// Premium course card shown when the user hasn't scanned their marks
/// yet (browse mode). Shows institution + APS + level/field — minus the
/// "Qualify / Subject Gap" verdict (we have no marks to compare against).
class _BrowseCourseCard extends StatelessWidget {
  final CourseModel course;
  final VoidCallback onTap;
  const _BrowseCourseCard({required this.course, required this.onTap});

  CourseOffering? get _bestOffering {
    final offerings = course.offerings;
    if (offerings == null || offerings.isEmpty) return null;
    // Show the offering with the lowest APS — most accessible entry point.
    final sorted = [...offerings]
      ..sort((a, b) => a.minAps.compareTo(b.minAps));
    return sorted.first;
  }

  // Deadline from the flat list field, falling back to the best offering.
  String? get _rawDeadline =>
      course.applicationDeadline ?? _bestOffering?.applicationDeadline;

  // "Closes 30 Sep" / "Closed", or null if no deadline on record.
  String? get _deadlineLabel {
    final raw = _rawDeadline;
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
    final raw = _rawDeadline;
    if (raw == null) return false;
    final date = DateTime.tryParse(raw);
    if (date == null) return false;
    final days = date.difference(DateTime.now()).inDays;
    return days >= 0 && days <= 14;
  }

  // Full institution name (e.g. "University of KwaZulu-Natal"), never the
  // short code. Mirrors the home recommended card.
  String? get _fullInstitutionName {
    if (course.institutionName != null &&
        course.institutionName!.isNotEmpty) {
      return course.institutionName;
    }
    final inst = _bestOffering?.institution;
    if (inst != null && inst.name.isNotEmpty) return inst.name;
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final minAps = _bestOffering?.minAps ?? course.minAps ?? 0;
    final fieldLabel = AppConstants.studyFields[course.field] ?? course.field;
    final levelLabel = course.level.toUpperCase().replaceAll('_', ' ');
    final fullName = _fullInstitutionName;

    return _CardChrome(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Course name + bookmark ───────────────────────────────────
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Text(
                  course.name,
                  style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      height: 1.25,
                      color: AppColors.textPrimary),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              BookmarkButton(
                itemType: 'course',
                itemId: course.id,
                inactiveColor: AppColors.textHint,
                activeColor: AppColors.primary,
              ),
            ],
          ),
          const SizedBox(height: 4),

          // ── Institution name (below the course name) ─────────────────
          if (fullName != null)
            Text(
              fullName,
              style: const TextStyle(
                fontSize: 12.5,
                fontWeight: FontWeight.w700,
                color: AppColors.textSecondary,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          const SizedBox(height: 8),

          // ── Meta chips: level + field + duration ─────────────────────
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              _SoftChip(
                label: levelLabel,
                background: AppColors.primaryLight,
                foreground: AppColors.primary,
              ),
              _SoftChip(
                label: fieldLabel,
                icon: Icons.category_outlined,
                background: AppColors.surface,
                foreground: AppColors.textSecondary,
                bordered: true,
              ),
              if (course.durationYears != null)
                _SoftChip(
                  label: '${course.durationYears!.toStringAsFixed(0)} yr',
                  icon: Icons.schedule,
                  background: AppColors.surface,
                  foreground: AppColors.textSecondary,
                  bordered: true,
                ),
            ],
          ),
          const SizedBox(height: 12),

          // ── Bottom: Min APS chip (left) + closing date (right) ───────
          Row(
            children: [
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: AppColors.primary.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.auto_awesome,
                        size: 14, color: AppColors.primary),
                    const SizedBox(width: 6),
                    Text(
                      minAps > 0 ? 'Min APS  $minAps' : 'Open',
                      style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: AppColors.primary),
                    ),
                  ],
                ),
              ),
              const Spacer(),
              if (_deadlineLabel != null)
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.event_outlined,
                        size: 14,
                        color: _deadlineUrgent
                            ? AppColors.error
                            : AppColors.textSecondary),
                    const SizedBox(width: 4),
                    Text(
                      _deadlineLabel!,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: _deadlineUrgent
                            ? AppColors.error
                            : AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
            ],
          ),
        ],
      ),
    );
  }
}

/// Reusable card chrome — soft shadow, rounded, ripple on tap. Used by
/// every course card so they share the same visual DNA.
class _CardChrome extends StatelessWidget {
  final Widget child;
  final VoidCallback onTap;
  const _CardChrome({required this.child, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(16),
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
          child: child,
        ),
      ),
    );
  }
}

/// Compact pill used for level / field / duration etc.
class _SoftChip extends StatelessWidget {
  final String label;
  final IconData? icon;
  final Color background;
  final Color foreground;
  final bool bordered;
  const _SoftChip({
    required this.label,
    required this.background,
    required this.foreground,
    this.icon,
    this.bordered = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(8),
        border: bordered ? Border.all(color: AppColors.border) : null,
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 11, color: foreground),
            const SizedBox(width: 4),
          ],
          Text(
            label,
            style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                color: foreground,
                letterSpacing: 0.1),
          ),
        ],
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

  IconData get _categoryIcon {
    switch (offering.match.category) {
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

  // "Closes 30 Sep" / "Closed", or null if no deadline on record.
  String? get _deadlineLabel {
    final raw = offering.applicationDeadline;
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
    final raw = offering.applicationDeadline;
    if (raw == null) return false;
    final date = DateTime.tryParse(raw);
    if (date == null) return false;
    final days = date.difference(DateTime.now()).inDays;
    return days >= 0 && days <= 14;
  }

  @override
  Widget build(BuildContext context) {
    final m = offering.match;
    return _CardChrome(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Course name + bookmark (mirrors the home card) ───────────
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Text(
                  offering.courseName,
                  style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      height: 1.25,
                      color: AppColors.textPrimary),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              BookmarkButton(
                itemType: 'course',
                itemId: offering.courseId,
                inactiveColor: AppColors.textHint,
                activeColor: AppColors.primary,
              ),
            ],
          ),
          const SizedBox(height: 4),

          // ── Institution name (below the course name) ─────────────────
          Text(
            offering.institutionName.isNotEmpty
                ? offering.institutionName
                : (offering.institutionShort ?? ''),
            style: const TextStyle(
              fontSize: 12.5,
              fontWeight: FontWeight.w700,
              color: AppColors.textSecondary,
            ),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          // For collapsed TVET courses — hint that more colleges offer it.
          if (offering.offeringCount > 1) ...[
            const SizedBox(height: 4),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.account_balance_outlined,
                    size: 13, color: AppColors.primary),
                const SizedBox(width: 4),
                Text(
                  'Offered at ${offering.offeringCount} colleges · tap to choose',
                  style: const TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w600,
                    color: AppColors.primary,
                  ),
                ),
              ],
            ),
          ],
          const SizedBox(height: 8),

          // ── Meta chips ───────────────────────────────────────────────
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              _SoftChip(
                label: AppConstants.studyFields[offering.courseField] ??
                    offering.courseField,
                icon: Icons.category_outlined,
                background: AppColors.surface,
                foreground: AppColors.textSecondary,
                bordered: true,
              ),
              if (offering.courseDurationYears != null)
                _SoftChip(
                  label: '${offering.courseDurationYears!.toStringAsFixed(0)} yr',
                  icon: Icons.schedule,
                  background: AppColors.surface,
                  foreground: AppColors.textSecondary,
                  bordered: true,
                ),
            ],
          ),
          const SizedBox(height: 14),

          // ── Verdict banner (no APS pill — APS sits at the bottom) ─────
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: _categoryColor.withOpacity(0.10),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: _categoryColor.withOpacity(0.35)),
            ),
            child: Row(
              children: [
                Container(
                  width: 28,
                  height: 28,
                  decoration: BoxDecoration(
                    color: _categoryColor,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(_categoryIcon, size: 16, color: Colors.white),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _categoryLabel,
                        style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w800,
                            color: _categoryColor),
                      ),
                      Text(
                        _verdictSubtitle(m),
                        style: const TextStyle(
                            fontSize: 11.5,
                            color: AppColors.textSecondary),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // ── Subject gap detail (only when relevant) ──────────────────
          if (m.missingSubjects.isNotEmpty ||
              m.lowSubjects.isNotEmpty ||
              m.mathsLitBlocked) ...[
            const SizedBox(height: 10),
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
              Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Text(
                  '+${m.missingSubjects.length + m.lowSubjects.length - 4} more requirement(s)',
                  style: const TextStyle(
                      fontSize: 11, color: AppColors.textHint),
                ),
              ),
          ],

          const SizedBox(height: 12),
          // ── Bottom: Min APS chip (left) + closing date (right) ───────
          Row(
            children: [
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: AppColors.primary.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.auto_awesome,
                        size: 14, color: AppColors.primary),
                    const SizedBox(width: 6),
                    Text(
                      offering.minAps > 0 ? 'Min APS  ${offering.minAps}' : 'Open',
                      style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: AppColors.primary),
                    ),
                  ],
                ),
              ),
              const Spacer(),
              if (_deadlineLabel != null)
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.event_outlined,
                        size: 14,
                        color: _deadlineUrgent
                            ? AppColors.error
                            : AppColors.textSecondary),
                    const SizedBox(width: 4),
                    Text(
                      _deadlineLabel!,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: _deadlineUrgent
                            ? AppColors.error
                            : AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
            ],
          ),
        ],
      ),
    );
  }

  /// Plain-language tagline shown under the big "Qualify / Subject Gap"
  /// banner. We feed users the most actionable summary we can derive
  /// from the match payload without needing an AI call.
  String _verdictSubtitle(dynamic m) {
    final cat = m.category as String;
    final surplus = m.apsSurplus as int;
    if (cat == 'eligible') {
      return surplus > 0
          ? 'You\'re above the cutoff by $surplus APS'
          : 'Your APS meets the requirement';
    }
    if (cat == 'aps_gap') {
      return 'Short ${surplus.abs()} APS for entry';
    }
    if (cat == 'subject_gap') {
      final n = (m.missingSubjects as List).length +
          (m.lowSubjects as List).length;
      return n == 1
          ? '1 subject requirement not yet met'
          : '$n subject requirements not yet met';
    }
    return 'See details';
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
