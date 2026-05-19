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

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              height: 120,
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(16),
                  topRight: Radius.circular(16),
                ),
              ),
              child: const Center(
                child: Icon(Icons.apartment_outlined, size: 48, color: AppColors.textHint),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(child: Text(item.name, style: Theme.of(context).textTheme.titleMedium)),
                      Text(
                        'R${item.pricePerMonth.toStringAsFixed(0)}/mo',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(color: AppColors.primary),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text('${item.city}, ${AppConstants.provinces[item.province] ?? item.province}',
                      style: Theme.of(context).textTheme.bodySmall),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      if (item.nsfasAccredited)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: AppColors.secondaryLight,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Text('NSFAS ✓',
                              style: TextStyle(color: AppColors.secondary, fontSize: 11, fontWeight: FontWeight.w600)),
                        ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: AppColors.primaryLight,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(item.roomType.replaceAll('_', ' ').toUpperCase(),
                            style: const TextStyle(color: AppColors.primary, fontSize: 11, fontWeight: FontWeight.w600)),
                      ),
                      if (item.distanceKm != null) ...[
                        const Spacer(),
                        const Icon(Icons.directions_walk, size: 13, color: AppColors.textHint),
                        const SizedBox(width: 4),
                        Text('${item.distanceKm}km', style: Theme.of(context).textTheme.bodySmall),
                      ],
                    ],
                  ),
                  if (item.contactPhone?.isNotEmpty == true) ...[
                    const SizedBox(height: 10),
                    OutlinedButton.icon(
                      onPressed: () => launchUrl(Uri.parse('tel:${item.contactPhone}')),
                      icon: const Icon(Icons.phone_outlined, size: 16),
                      label: const Text('Call'),
                      style: OutlinedButton.styleFrom(minimumSize: const Size(80, 34), textStyle: const TextStyle(fontSize: 13)),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
