import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/constants/app_constants.dart';
import '../../../data/models/bursary_model.dart';
import '../../../data/models/bursary_match_model.dart';
import '../../../data/services/api/api_client.dart';
import '../../../providers/bursary_provider.dart';
import '../../widgets/common/remote_logo.dart';
import '../../widgets/common/app_avatar.dart';

/// Stable String-keyed family. Returns BursaryWithMatch so qualify badges work.
final bursaryListProvider =
    FutureProvider.family<List<BursaryWithMatch>, String?>((ref, paramStr) async {
  final params = <String, String>{'page_size': '500'};
  if (paramStr != null && paramStr.isNotEmpty) {
    for (final part in paramStr.split('&')) {
      final kv = part.split('=');
      if (kv.length == 2) params[kv[0]] = Uri.decodeComponent(kv[1]);
    }
  }
  final resp = await ApiClient.instance
      .get('/bursaries/', queryParams: params)
      .timeout(
        const Duration(seconds: 20),
        onTimeout: () => throw Exception('Request timed out. Check your connection.'),
      );
  final list = (resp.data['results'] ?? resp.data) as List;
  return list
      .map((e) => BursaryWithMatch.fromJson(Map<String, dynamic>.from(e)))
      .toList();
});

class BursariesScreen extends ConsumerStatefulWidget {
  const BursariesScreen({super.key});

  @override
  ConsumerState<BursariesScreen> createState() => _BursariesScreenState();
}

class _BursariesScreenState extends ConsumerState<BursariesScreen> {
  String? _fieldFilter;
  String? _provinceFilter;
  String? _typeFilter;
  String _statusFilter = 'open'; // 'all' | 'open' | 'closing_soon' | 'closed' | 'qualified'
  final TextEditingController _searchCtrl = TextEditingController();
  String _query = '';
  Timer? _debounce;
  final ScrollController _scrollCtrl = ScrollController();
  int _displayCount = 20;
  static const int _pageStep = 20;

  @override
  void initState() {
    super.initState();
    _scrollCtrl.addListener(() {
      // Load more when near the bottom.
      if (_scrollCtrl.position.pixels >=
          _scrollCtrl.position.maxScrollExtent - 200) {
        setState(() => _displayCount += _pageStep);
      }
    });
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    _scrollCtrl.dispose();
    _debounce?.cancel();
    super.dispose();
  }

  void _resetPagination() {
    _displayCount = _pageStep;
    if (_scrollCtrl.hasClients) _scrollCtrl.jumpTo(0);
  }

  @override
  Widget build(BuildContext context) {
    // Status filter goes to backend, except 'qualified' which is post-filtered locally.
    final backendStatus =
        _statusFilter == 'qualified' || _statusFilter == 'all' ? null : _statusFilter;
    final filterParts = [
      if (_fieldFilter != null) 'field=${Uri.encodeComponent(_fieldFilter!)}',
      if (_provinceFilter != null) 'province=${Uri.encodeComponent(_provinceFilter!)}',
      if (_typeFilter != null) 'funding_type=${Uri.encodeComponent(_typeFilter!)}',
      if (backendStatus != null) 'status=$backendStatus',
      if (_query.isNotEmpty) 'search=${Uri.encodeComponent(_query)}',
    ];
    final paramStr = filterParts.isEmpty ? null : filterParts.join('&');
    final bursariesAsync = ref.watch(bursaryListProvider(paramStr));
    final statsAsync = ref.watch(bursaryStatsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Bursaries'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: AppAvatar(radius: 16, onTap: () => context.go('/profile')),
          ),
        ],
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
                hintText: 'Search bursaries or providers…',
                prefixIcon: const Icon(Icons.search, size: 20, color: AppColors.textHint),
                suffixIcon: (_searchCtrl.text.isEmpty && _query.isEmpty)
                    ? null
                    : IconButton(
                        icon: const Icon(Icons.close, size: 18),
                        onPressed: () {
                          // Kill the pending debounce so it can't re-apply
                          // the previous query after we've cleared.
                          _debounce?.cancel();
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
                _debounce?.cancel();
                _debounce = Timer(const Duration(milliseconds: 350), () {
                  if (!mounted) return;
                  setState(() {
                    _query = v.trim().toLowerCase();
                    _resetPagination();
                  });
                });
              },
            ),
          ),

          // Status chips (open / closing soon / closed / qualified)
          SizedBox(
            height: 44,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
              children: [
                _StatusChip(
                  label: 'Open',
                  selected: _statusFilter == 'open',
                  count: statsAsync.value?.open,
                  onTap: () => setState(() { _statusFilter = 'open'; _resetPagination(); }),
                ),
                const SizedBox(width: 8),
                _StatusChip(
                  label: 'Qualify ✓',
                  selected: _statusFilter == 'qualified',
                  count: statsAsync.value?.qualified,
                  onTap: () => setState(() { _statusFilter = 'qualified'; _resetPagination(); }),
                ),
                const SizedBox(width: 8),
                _StatusChip(
                  label: 'Closing ≤30d',
                  selected: _statusFilter == 'closing_soon',
                  count: statsAsync.value?.closingSoon,
                  onTap: () => setState(() { _statusFilter = 'closing_soon'; _resetPagination(); }),
                ),
                const SizedBox(width: 8),
                _StatusChip(
                  label: 'Closed',
                  selected: _statusFilter == 'closed',
                  count: statsAsync.value?.closed,
                  onTap: () => setState(() { _statusFilter = 'closed'; _resetPagination(); }),
                ),
                const SizedBox(width: 8),
                _StatusChip(
                  label: 'All',
                  selected: _statusFilter == 'all',
                  count: statsAsync.value?.total,
                  onTap: () => setState(() { _statusFilter = 'all'; _resetPagination(); }),
                ),
              ],
            ),
          ),

          // Field/province/type filters
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  _FilterButton(
                    label: _fieldFilter != null
                        ? (AppConstants.studyFields[_fieldFilter] ?? 'Field')
                        : 'Field',
                    active: _fieldFilter != null,
                    onTap: () async {
                      final v = await _showPicker(
                          context, AppConstants.studyFields, _fieldFilter);
                      setState(() => _fieldFilter = v);
                    },
                  ),
                  const SizedBox(width: 8),
                  _FilterButton(
                    label: _provinceFilter != null
                        ? (AppConstants.provinces[_provinceFilter] ?? 'Province')
                        : 'Province',
                    active: _provinceFilter != null,
                    onTap: () async {
                      final v = await _showPicker(
                          context, AppConstants.provinces, _provinceFilter);
                      setState(() => _provinceFilter = v);
                    },
                  ),
                  const SizedBox(width: 8),
                  _FilterButton(
                    label: _typeFilter != null
                        ? _typeFilter!.replaceAll('_', ' ').toUpperCase()
                        : 'Type',
                    active: _typeFilter != null,
                    onTap: () async {
                      final v = await _showPicker(context, const {
                        'full': 'Full Bursary',
                        'partial': 'Partial Bursary',
                        'nsfas': 'NSFAS',
                        'scholarship': 'Scholarship',
                        'loan': 'Study Loan',
                      }, _typeFilter);
                      setState(() => _typeFilter = v);
                    },
                  ),
                  if (_fieldFilter != null ||
                      _provinceFilter != null ||
                      _typeFilter != null) ...[
                    const SizedBox(width: 8),
                    ActionChip(
                      label: const Text('Clear', style: TextStyle(fontSize: 12)),
                      onPressed: () => setState(() {
                        _fieldFilter = null;
                        _provinceFilter = null;
                        _typeFilter = null;
                      }),
                      backgroundColor: AppColors.errorLight,
                    ),
                  ],
                ],
              ),
            ),
          ),

          Expanded(
            child: bursariesAsync.when(
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
                      const Text('Could not load bursaries'),
                      const SizedBox(height: 12),
                      OutlinedButton(
                        onPressed: () =>
                            ref.invalidate(bursaryListProvider(paramStr)),
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                ),
              ),
              data: (items) {
                // Apply 'qualified' filter client-side (uses match data from backend).
                var filtered = items;
                if (_statusFilter == 'qualified') {
                  filtered = items
                      .where((b) => b.match?.isQualified == true)
                      .toList();
                }
                if (filtered.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.card_giftcard_outlined,
                            size: 56, color: AppColors.textHint),
                        const SizedBox(height: 12),
                        Text('No bursaries match',
                            style: Theme.of(context).textTheme.titleMedium),
                        const SizedBox(height: 6),
                        const Text('Try clearing some filters',
                            style: TextStyle(color: AppColors.textSecondary)),
                      ],
                    ),
                  );
                }
                final visible =
                    filtered.take(_displayCount).toList();
                final hasMore = _displayCount < filtered.length;
                return Column(
                  children: [
                    Padding(
                      padding: const EdgeInsets.fromLTRB(20, 4, 20, 4),
                      child: Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          'Showing ${visible.length} of ${filtered.length}',
                          style: const TextStyle(
                              fontSize: 12,
                              color: AppColors.textSecondary,
                              fontWeight: FontWeight.w600),
                        ),
                      ),
                    ),
                    Expanded(
                      child: ListView.separated(
                        controller: _scrollCtrl,
                        padding: const EdgeInsets.fromLTRB(16, 4, 16, 12),
                        itemCount: visible.length + (hasMore ? 1 : 0),
                        separatorBuilder: (_, __) =>
                            const SizedBox(height: 10),
                        itemBuilder: (_, i) {
                          if (i >= visible.length) {
                            return const Padding(
                              padding: EdgeInsets.symmetric(vertical: 16),
                              child: Center(
                                child: SizedBox(
                                  width: 22,
                                  height: 22,
                                  child: CircularProgressIndicator(
                                      strokeWidth: 2),
                                ),
                              ),
                            );
                          }
                          return _BursaryCard(item: visible[i]);
                        },
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Future<String?> _showPicker(
      BuildContext context, Map<String, String> options, String? current) {
    return showModalBottomSheet<String>(
      context: context,
      builder: (_) => ListView(
        children: [
          const Padding(
            padding: EdgeInsets.all(16),
            child: Text('Select option',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
          ),
          if (current != null)
            ListTile(
              leading: const Icon(Icons.clear, color: AppColors.error),
              title: const Text('Clear filter'),
              onTap: () => Navigator.pop(context, null),
            ),
          ...options.entries.map((e) => ListTile(
                title: Text(e.value),
                trailing: current == e.key
                    ? const Icon(Icons.check, color: AppColors.primary)
                    : null,
                onTap: () => Navigator.pop(context, e.key),
              )),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final String label;
  final bool selected;
  final int? count;
  final VoidCallback onTap;
  const _StatusChip(
      {required this.label,
      required this.selected,
      required this.count,
      required this.onTap});

  @override
  Widget build(BuildContext context) {
    return ChoiceChip(
      label: Text(count != null ? '$label ($count)' : label,
          style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: selected ? AppColors.primary : AppColors.textSecondary)),
      selected: selected,
      onSelected: (_) => onTap(),
      selectedColor: AppColors.primaryLight,
      backgroundColor: Colors.white,
      side: BorderSide(
          color: selected ? AppColors.primary : AppColors.border),
      showCheckmark: false,
    );
  }
}

class _FilterButton extends StatelessWidget {
  final String label;
  final bool active;
  final VoidCallback onTap;
  const _FilterButton(
      {required this.label, required this.active, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return ActionChip(
      avatar: Icon(Icons.filter_list,
          size: 16, color: active ? AppColors.primary : AppColors.textHint),
      label: Text(label, style: const TextStyle(fontSize: 12)),
      backgroundColor: active ? AppColors.primaryLight : Colors.white,
      side: BorderSide(color: active ? AppColors.primary : AppColors.border),
      onPressed: onTap,
    );
  }
}

class _BursaryCard extends StatelessWidget {
  final BursaryWithMatch item;
  const _BursaryCard({required this.item});

  BursaryModel get b => item.bursary;
  BursaryMatch? get m => item.match;

  String get _formattedDeadline {
    final raw = b.applicationDeadline;
    if (raw == null) return '';
    final d = DateTime.tryParse(raw);
    if (d == null) return raw;
    const months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return '${d.day} ${months[d.month]} ${d.year}';
  }

  Color _badgeColor() {
    if (m == null) return AppColors.textHint;
    switch (m!.status) {
      case 'qualified':
        return AppColors.eligible;
      case 'check_details':
        return AppColors.secondary;
      case 'grade_gap':
        return AppColors.apsGap;
      case 'field_mismatch':
        return AppColors.textHint;
      case 'closed':
        return AppColors.error;
    }
    return AppColors.textHint;
  }

  @override
  Widget build(BuildContext context) {
    final isClosed = m?.isClosed == true;
    final days = m?.daysUntilDeadline;
    return GestureDetector(
      onTap: () => context.push('/bursaries/${b.id}'),
      child: Opacity(
        opacity: isClosed ? 0.55 : 1.0,
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
                color: isClosed ? AppColors.border : AppColors.border),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  RemoteLogo(
                    url: b.logoUrl,
                    fallbackInitial: b.provider.isNotEmpty ? b.provider[0] : 'B',
                    size: 40,
                    fallbackBg: AppColors.accentLight,
                    fallbackFg: AppColors.accent,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(b.name,
                            style: const TextStyle(
                                fontSize: 14, fontWeight: FontWeight.w700),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis),
                        Text(b.provider,
                            style: const TextStyle(
                                fontSize: 12, color: AppColors.textSecondary),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis),
                      ],
                    ),
                  ),
                  if (m != null)
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: _badgeColor().withOpacity(0.15),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        m!.label,
                        style: TextStyle(
                            color: _badgeColor(),
                            fontSize: 11,
                            fontWeight: FontWeight.w700),
                      ),
                    ),
                ],
              ),
              if (b.eligibility?.isNotEmpty == true) ...[
                const SizedBox(height: 8),
                Text(b.eligibility!,
                    style: const TextStyle(
                        fontSize: 12, color: AppColors.textSecondary),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis),
              ],
              const SizedBox(height: 10),
              Wrap(
                spacing: 8,
                runSpacing: 6,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppColors.surface,
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: Text(
                        b.fundingType.replaceAll('_', ' ').toUpperCase(),
                        style: const TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            color: AppColors.textSecondary)),
                  ),
                  if (_formattedDeadline.isNotEmpty)
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          isClosed ? Icons.event_busy : Icons.calendar_today,
                          size: 12,
                          color: AppColors.error,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          isClosed
                              ? 'Closed $_formattedDeadline'
                              : 'Closes $_formattedDeadline'
                                  '${days != null && days >= 0 && days <= 30 ? "  •  $days days left" : ""}',
                          style: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: AppColors.error,
                          ),
                        ),
                      ],
                    ),
                  const Spacer(),
                  SizedBox(
                    height: 28,
                    child: TextButton(
                      onPressed: isClosed
                          ? null
                          : () => launchUrl(
                                Uri.parse(b.applicationUrl),
                                mode: LaunchMode.externalApplication,
                              ),
                      style: TextButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 10),
                        backgroundColor: isClosed
                            ? AppColors.surface
                            : AppColors.primary,
                        foregroundColor:
                            isClosed ? AppColors.textHint : Colors.white,
                        textStyle: const TextStyle(
                            fontSize: 12, fontWeight: FontWeight.w600),
                      ),
                      child: Text(isClosed ? 'Closed' : 'Apply'),
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
