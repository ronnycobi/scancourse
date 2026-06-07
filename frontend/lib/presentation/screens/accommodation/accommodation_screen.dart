import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/constants/app_constants.dart';
import '../../../data/services/api/api_client.dart';
import '../../widgets/common/bookmark_button.dart';

class AccommodationItem {
  final int id;
  final String name;
  final String city;
  final String province;
  final String roomType;
  final double pricePerMonth;
  final bool nsfasAccredited;
  final double? distanceKm;
  final String? contactPhone;
  final int? nearbyInstitutionId;
  final String? nearbyInstitution;
  final List<String> features;
  final List images;

  AccommodationItem.fromJson(Map<String, dynamic> j)
      // Defensive defaults so a sparse scraped record (null name/city/etc.)
      // doesn't crash the whole list page with a Null-is-not-String cast.
      : id = (j['id'] as num).toInt(),
        name = (j['name'] as String?)?.trim() ?? 'Accommodation',
        city = (j['city'] as String?)?.trim() ?? '',
        province = (j['province'] as String?)?.trim() ?? '',
        roomType = (j['room_type'] as String?) ?? '',
        pricePerMonth =
            double.tryParse((j['price_per_month'] ?? '').toString()) ?? 0,
        nsfasAccredited = j['nsfas_accredited'] == true,
        distanceKm = j['distance_km'] == null
            ? null
            : double.tryParse(j['distance_km'].toString()),
        contactPhone = j['contact_phone'] as String?,
        nearbyInstitutionId = (j['nearby_institution'] as num?)?.toInt(),
        nearbyInstitution = j['nearby_institution_name'] as String?,
        features = ((j['features'] as List?) ?? const [])
            .map((e) => e.toString())
            .toList(),
        images = (j['images'] as List?) ?? const [];
}

/// Distinct universities that actually have accommodation listed — powers
/// the "University" filter dropdown ({id: name}).
final accommodationUniversitiesProvider =
    FutureProvider<Map<String, String>>((ref) async {
  final resp = await ApiClient.instance
      .get('/accommodation/', queryParams: {'page_size': '500'});
  final list = (resp.data['results'] ?? resp.data) as List;
  final out = <String, String>{};
  for (final e in list) {
    final id = e['nearby_institution'];
    final name = e['nearby_institution_name'];
    if (id != null && name != null) out['$id'] = name.toString();
  }
  // Sorted by name for a tidy picker.
  final sorted = out.entries.toList()
    ..sort((a, b) => a.value.compareTo(b.value));
  return {for (final e in sorted) e.key: e.value};
});

// Stable String key (Maps are reference-equal in Dart and cause endless refetching).
final accommodationProvider = FutureProvider.family<List<AccommodationItem>, String?>((ref, paramStr) async {
  final params = <String, String>{};
  if (paramStr != null && paramStr.isNotEmpty) {
    for (final part in paramStr.split('&')) {
      final kv = part.split('=');
      if (kv.length == 2) params[kv[0]] = Uri.decodeComponent(kv[1]);
    }
  }
  final resp = await ApiClient.instance.get('/accommodation/', queryParams: params).timeout(
    const Duration(seconds: 20),
    onTimeout: () => throw Exception('Request timed out. Check your connection.'),
  );
  final list = (resp.data['results'] ?? resp.data) as List;
  return list.map((e) => AccommodationItem.fromJson(Map<String, dynamic>.from(e))).toList();
});

class AccommodationScreen extends ConsumerStatefulWidget {
  const AccommodationScreen({super.key});

  @override
  ConsumerState<AccommodationScreen> createState() => _AccommodationScreenState();
}

class _AccommodationScreenState extends ConsumerState<AccommodationScreen> {
  String? _province;
  String? _roomType;
  String? _university; // nearby_institution id
  int? _maxPrice;
  bool _nsfasOnly = false;

  static const _roomTypes = {
    'single': 'Single Room',
    'sharing': 'Sharing Room',
    'bachelor': 'Bachelor Flat',
    'one_bed': '1 Bedroom',
    'two_bed': '2 Bedroom',
  };
  static const _priceOptions = {3000: 'Under R3 000', 4000: 'Under R4 000',
    5000: 'Under R5 000', 7000: 'Under R7 000'};

  /// A chip that opens a bottom-sheet picker. `onPicked(null)` clears it.
  Widget _pickerChip({
    required String label,
    required bool active,
    required String title,
    required Map<String, String> options,
    required String? current,
    required void Function(String?) onPicked,
  }) {
    return ActionChip(
      label: Text(label),
      backgroundColor: active ? AppColors.primaryLight : null,
      labelStyle: TextStyle(
          color: active ? AppColors.primary : AppColors.textPrimary,
          fontWeight: active ? FontWeight.w700 : FontWeight.w500),
      side: BorderSide(color: active ? AppColors.primary : AppColors.border),
      onPressed: () async {
        final picked = await showModalBottomSheet<String?>(
          context: context,
          builder: (_) => SafeArea(
            child: ListView(
              shrinkWrap: true,
              children: [
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(title,
                      style: const TextStyle(fontWeight: FontWeight.w700)),
                ),
                ListTile(
                  title: const Text('Any'),
                  trailing: current == null
                      ? const Icon(Icons.check, color: AppColors.primary)
                      : null,
                  onTap: () => Navigator.pop(context, '__clear__'),
                ),
                ...options.entries.map((e) => ListTile(
                      title: Text(e.value),
                      trailing: current == e.key
                          ? const Icon(Icons.check, color: AppColors.primary)
                          : null,
                      onTap: () => Navigator.pop(context, e.key),
                    )),
                const SizedBox(height: 8),
              ],
            ),
          ),
        );
        if (picked == null) return; // dismissed
        onPicked(picked == '__clear__' ? null : picked);
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final filterParts = [
      if (_province != null) 'province=${Uri.encodeComponent(_province!)}',
      if (_roomType != null) 'room_type=${Uri.encodeComponent(_roomType!)}',
      if (_university != null) 'nearby_institution=$_university',
      if (_maxPrice != null) 'max_price=$_maxPrice',
      if (_nsfasOnly) 'nsfas_accredited=true',
    ];
    final universities =
        ref.watch(accommodationUniversitiesProvider).valueOrNull ?? const {};
    final paramStr = filterParts.isEmpty ? null : filterParts.join('&');
    final accAsync = ref.watch(accommodationProvider(paramStr));

    return Scaffold(
      appBar: AppBar(title: const Text('Accommodation')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            // Wrap so every filter is visible (flows onto a second line).
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                // NSFAS — prominent green accreditation filter, up front.
                FilterChip(
                  avatar: Icon(Icons.verified_outlined,
                      size: 18,
                      color: _nsfasOnly
                          ? AppColors.eligible
                          : AppColors.textSecondary),
                  label: const Text('NSFAS'),
                  selected: _nsfasOnly,
                  onSelected: (v) => setState(() => _nsfasOnly = v),
                  selectedColor: AppColors.eligible.withOpacity(0.15),
                  checkmarkColor: AppColors.eligible,
                  side: BorderSide(
                      color: _nsfasOnly ? AppColors.eligible : AppColors.border),
                  labelStyle: TextStyle(
                      color: _nsfasOnly
                          ? AppColors.eligible
                          : AppColors.textPrimary,
                      fontWeight: FontWeight.w700),
                ),
                _pickerChip(
                  label: _university != null
                      ? (universities[_university] ?? 'University')
                      : 'University',
                  active: _university != null,
                  title: 'University',
                  options: universities,
                  current: _university,
                  onPicked: (v) => setState(() => _university = v),
                ),
                _pickerChip(
                  label: _province != null
                      ? (AppConstants.provinces[_province] ?? 'Province')
                      : 'Province',
                  active: _province != null,
                  title: 'Province',
                  options: AppConstants.provinces,
                  current: _province,
                  onPicked: (v) => setState(() => _province = v),
                ),
                _pickerChip(
                  label: _roomType != null
                      ? (_roomTypes[_roomType] ?? 'Room type')
                      : 'Room type',
                  active: _roomType != null,
                  title: 'Room type',
                  options: _roomTypes,
                  current: _roomType,
                  onPicked: (v) => setState(() => _roomType = v),
                ),
                _pickerChip(
                  label: _maxPrice != null
                      ? (_priceOptions[_maxPrice] ?? 'Price')
                      : 'Max price',
                  active: _maxPrice != null,
                  title: 'Maximum monthly price',
                  options: {
                    for (final e in _priceOptions.entries)
                      e.key.toString(): e.value
                  },
                  current: _maxPrice?.toString(),
                  onPicked: (v) => setState(
                      () => _maxPrice = v == null ? null : int.parse(v)),
                ),
              ],
            ),
          ),
          Expanded(
            child: accAsync.when(
              data: (items) => RefreshIndicator(
                onRefresh: () async =>
                    ref.invalidate(accommodationProvider(paramStr)),
                child: items.isEmpty
                    // Empty state is now scrollable so the parent
                    // RefreshIndicator still triggers a pull-down.
                    ? ListView(
                        physics: const AlwaysScrollableScrollPhysics(),
                        padding: const EdgeInsets.symmetric(
                            vertical: 80, horizontal: 24),
                        children: [
                          const Icon(Icons.home_work_outlined,
                              size: 64, color: AppColors.textHint),
                          const SizedBox(height: 16),
                          Center(
                            child: Text('No accommodation found',
                                style: Theme.of(context).textTheme.titleMedium),
                          ),
                          const SizedBox(height: 8),
                          Center(
                            child: Text('Try adjusting your filters',
                                style: Theme.of(context).textTheme.bodySmall),
                          ),
                        ],
                      )
                    : ListView.separated(
                        physics: const AlwaysScrollableScrollPhysics(),
                        padding: EdgeInsets.fromLTRB(16, 0, 16,
                            48 + MediaQuery.of(context).padding.bottom),
                        itemCount: items.length,
                        separatorBuilder: (_, __) =>
                            const SizedBox(height: 12),
                        itemBuilder: (context, i) => _AccommodationCard(
                          item: items[i],
                          onTap: () =>
                              context.push('/accommodation/${items[i].id}'),
                        ),
                      ),
              ),
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(
                child: Padding(
                  padding: const EdgeInsets.all(32),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.wifi_off_outlined, size: 64, color: AppColors.textHint),
                      const SizedBox(height: 16),
                      Text('Could not load accommodation', style: Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: 8),
                      Text('Check your connection and try again', style: Theme.of(context).textTheme.bodySmall),
                      const SizedBox(height: 20),
                      OutlinedButton(
                        onPressed: () => ref.invalidate(accommodationProvider(paramStr)),
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Title-case a snake_case room type for chip labels — "single_room" →
/// "Single Room". Replaces the previous all-caps shouting label.
String _prettyRoom(String raw) {
  if (raw.isEmpty) return 'Room';
  return raw
      .split('_')
      .where((w) => w.isNotEmpty)
      .map((w) => '${w[0].toUpperCase()}${w.substring(1)}')
      .join(' ');
}

/// "City, Province" line that copes with either field being missing —
/// returns null when neither is present so the row can be hidden.
String? _locationLineParts(String city, String province) {
  final p = province.isEmpty
      ? ''
      : (AppConstants.provinces[province] ?? province);
  final parts = [
    if (city.isNotEmpty) city,
    if (p.isNotEmpty) p,
  ];
  return parts.isEmpty ? null : parts.join(', ');
}

/// "R12 500" with a thin-space thousands separator.
String _formatRand(num value) {
  final whole = value.round().toString();
  final buf = StringBuffer();
  for (var i = 0; i < whole.length; i++) {
    if (i > 0 && (whole.length - i) % 3 == 0) buf.write(' ');
    buf.write(whole[i]);
  }
  return 'R$buf';
}

class _AccommodationCard extends StatelessWidget {
  final AccommodationItem item;
  final VoidCallback onTap;

  const _AccommodationCard({required this.item, required this.onTap});

  IconData get _roomIcon {
    final t = item.roomType.toLowerCase();
    if (t.contains('single')) return Icons.single_bed_outlined;
    if (t.contains('shar') || t.contains('double')) return Icons.bedroom_parent_outlined;
    if (t.contains('bachelor') || t.contains('studio')) return Icons.meeting_room_outlined;
    if (t.contains('res') || t.contains('dorm')) return Icons.apartment_outlined;
    return Icons.house_outlined;
  }

  @override
  Widget build(BuildContext context) {
    final roomLabel = _prettyRoom(item.roomType);
    final locationLine = _locationLineParts(item.city, item.province);
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.border),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 10,
                offset: const Offset(0, 3),
              ),
            ],
          ),
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Image-free gradient tile keyed to room type.
                  Container(
                    width: 64,
                    height: 64,
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [AppColors.primary, AppColors.primaryDark],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Icon(_roomIcon, color: Colors.white, size: 30),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item.name,
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w800,
                            color: AppColors.textPrimary,
                            height: 1.2,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        if (locationLine != null) ...[
                          const SizedBox(height: 3),
                          Row(
                            children: [
                              const Icon(Icons.place_outlined,
                                  size: 13, color: AppColors.textSecondary),
                              const SizedBox(width: 3),
                              Expanded(
                                child: Text(
                                  locationLine,
                                  style: const TextStyle(
                                      fontSize: 12,
                                      color: AppColors.textSecondary),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ),
                        ],
                        if (item.nearbyInstitution != null) ...[
                          const SizedBox(height: 2),
                          Row(
                            children: [
                              const Icon(Icons.school_outlined,
                                  size: 13, color: AppColors.primary),
                              const SizedBox(width: 3),
                              Expanded(
                                child: Text(
                                  item.distanceKm != null
                                      ? '${item.distanceKm!.toStringAsFixed(1)} km from ${item.nearbyInstitution}'
                                      : 'Near ${item.nearbyInstitution}',
                                  style: const TextStyle(
                                    fontSize: 11.5,
                                    color: AppColors.primary,
                                    fontWeight: FontWeight.w600,
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
                  const SizedBox(width: 8),
                  // Price + Save
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        item.pricePerMonth > 0
                            ? _formatRand(item.pricePerMonth)
                            : '—',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w900,
                          color: AppColors.primary,
                          height: 1,
                        ),
                      ),
                      if (item.pricePerMonth > 0)
                        const Text('per month',
                            style: TextStyle(
                                fontSize: 10, color: AppColors.textHint)),
                      BookmarkButton(
                        itemType: 'accommodation',
                        itemId: item.id,
                        size: 20,
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 10),
              // Chips: NSFAS, room type, a couple of features.
              Wrap(
                spacing: 6,
                runSpacing: 6,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  if (item.nsfasAccredited)
                    _chip('NSFAS ✓', AppColors.eligible,
                        AppColors.eligible.withOpacity(0.12)),
                  _chip(roomLabel, AppColors.primary, AppColors.primaryLight),
                  ...item.features.take(2).map(
                        (f) => _chip(f, AppColors.textSecondary,
                            AppColors.surface,
                            bordered: true),
                      ),
                  if (item.distanceKm != null)
                    _chip('${item.distanceKm!.toStringAsFixed(1)} km',
                        AppColors.textSecondary, AppColors.surface,
                        icon: Icons.directions_walk, bordered: true),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _chip(String label, Color fg, Color bg,
      {IconData? icon, bool bordered = false}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(8),
        border: bordered ? Border.all(color: AppColors.border) : null,
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 12, color: fg),
            const SizedBox(width: 3),
          ],
          Text(label,
              style: TextStyle(
                  color: fg, fontSize: 11, fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}
