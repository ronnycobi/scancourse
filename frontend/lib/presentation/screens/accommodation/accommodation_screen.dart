import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/constants/app_constants.dart';
import '../../../data/services/api/api_client.dart';

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
  final String? nearbyInstitution;
  final List<String> features;
  final List images;

  AccommodationItem.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        name = j['name'],
        city = j['city'],
        province = j['province'],
        roomType = j['room_type'],
        pricePerMonth = double.tryParse(j['price_per_month'].toString()) ?? 0,
        nsfasAccredited = j['nsfas_accredited'] ?? false,
        distanceKm = j['distance_km'] != null ? double.tryParse(j['distance_km'].toString()) : null,
        contactPhone = j['contact_phone'],
        nearbyInstitution = j['nearby_institution_name'] as String?,
        features = ((j['features'] as List?) ?? [])
            .map((e) => e.toString())
            .toList(),
        images = j['images'] ?? [];
}

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
  bool _nsfasOnly = false;

  @override
  Widget build(BuildContext context) {
    final filterParts = [
      if (_province != null) 'province=${Uri.encodeComponent(_province!)}',
      if (_roomType != null) 'room_type=${Uri.encodeComponent(_roomType!)}',
      if (_nsfasOnly) 'nsfas_accredited=true',
    ];
    final paramStr = filterParts.isEmpty ? null : filterParts.join('&');
    final accAsync = ref.watch(accommodationProvider(paramStr));

    return Scaffold(
      appBar: AppBar(title: const Text('Accommodation')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  FilterChip(
                    label: const Text('NSFAS Accredited'),
                    selected: _nsfasOnly,
                    onSelected: (v) => setState(() => _nsfasOnly = v),
                    selectedColor: AppColors.secondaryLight,
                  ),
                  const SizedBox(width: 8),
                  ActionChip(
                    label: Text(_province != null ? AppConstants.provinces[_province] ?? 'Province' : 'Province'),
                    backgroundColor: _province != null ? AppColors.primaryLight : null,
                    onPressed: () async {
                      final v = await showModalBottomSheet<String>(
                        context: context,
                        builder: (_) => ListView(
                          children: [
                            const Padding(padding: EdgeInsets.all(16), child: Text('Province', style: TextStyle(fontWeight: FontWeight.w600))),
                            ListTile(title: const Text('All provinces'), onTap: () => Navigator.pop(context, null)),
                            ...AppConstants.provinces.entries.map((e) => ListTile(
                              title: Text(e.value),
                              trailing: _province == e.key ? const Icon(Icons.check, color: AppColors.primary) : null,
                              onTap: () => Navigator.pop(context, e.key),
                            )),
                          ],
                        ),
                      );
                      setState(() => _province = v);
                    },
                  ),
                ],
              ),
            ),
          ),
          Expanded(
            child: accAsync.when(
              data: (items) => items.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.home_work_outlined, size: 64, color: AppColors.textHint),
                          const SizedBox(height: 16),
                          Text('No accommodation found', style: Theme.of(context).textTheme.titleMedium),
                          const SizedBox(height: 8),
                          Text('Try adjusting your filters', style: Theme.of(context).textTheme.bodySmall),
                        ],
                      ),
                    )
                  : ListView.separated(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      itemCount: items.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 12),
                      itemBuilder: (context, i) => _AccommodationCard(
                        item: items[i],
                        onTap: () => context.push('/accommodation/${items[i].id}'),
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
    final roomLabel = item.roomType.replaceAll('_', ' ').toUpperCase();
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
                        const SizedBox(height: 3),
                        Row(
                          children: [
                            const Icon(Icons.place_outlined,
                                size: 13, color: AppColors.textSecondary),
                            const SizedBox(width: 3),
                            Expanded(
                              child: Text(
                                '${item.city}, ${AppConstants.provinces[item.province] ?? item.province}',
                                style: const TextStyle(
                                    fontSize: 12,
                                    color: AppColors.textSecondary),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
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
                  // Price block
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        'R${item.pricePerMonth.toStringAsFixed(0)}',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w900,
                          color: AppColors.primary,
                          height: 1,
                        ),
                      ),
                      const Text('per month',
                          style: TextStyle(
                              fontSize: 10, color: AppColors.textHint)),
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
              if (item.contactPhone?.isNotEmpty == true) ...[
                const SizedBox(height: 10),
                Align(
                  alignment: Alignment.centerRight,
                  child: OutlinedButton.icon(
                    onPressed: () =>
                        launchUrl(Uri.parse('tel:${item.contactPhone}')),
                    icon: const Icon(Icons.phone_outlined, size: 16),
                    label: const Text('Call'),
                    style: OutlinedButton.styleFrom(
                        minimumSize: const Size(80, 34),
                        textStyle: const TextStyle(fontSize: 13)),
                  ),
                ),
              ],
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
