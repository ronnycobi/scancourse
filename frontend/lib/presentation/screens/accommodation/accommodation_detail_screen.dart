import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/constants/app_constants.dart';
import '../../../data/services/api/api_client.dart';
import '../../widgets/common/bookmark_button.dart';

/// Heuristic: an on-campus residence (vs private/off-campus). We have no
/// explicit flag, so infer from the name ("...Residence") or a tiny
/// distance to the institution.
bool _isOnCampusRes(Map<String, dynamic> a) {
  final name = (a['name'] as String? ?? '').toLowerCase();
  if (name.contains('residence') || name.contains(' res ') ||
      name.endsWith(' res')) {
    return true;
  }
  final d = double.tryParse((a['distance_km'] ?? '').toString());
  return a['nearby_institution'] != null && d != null && d <= 0.5;
}

/// Friendly "Cape Town, Western Cape" line that copes with either field
/// being missing — the old code rendered "Cape Town, " when province
/// was null and rendered nothing at all when city was null.
String? _locationLine(Map<String, dynamic> a) {
  final city = (a['city'] as String?)?.trim();
  final provinceRaw = (a['province'] as String?)?.trim();
  final province = provinceRaw == null || provinceRaw.isEmpty
      ? null
      : (AppConstants.provinces[provinceRaw] ?? provinceRaw);
  final parts = [
    if (city != null && city.isNotEmpty) city,
    if (province != null && province.isNotEmpty) province,
  ];
  return parts.isEmpty ? null : parts.join(', ');
}

/// Title-case a snake_case room type like "single_room" → "Single Room".
String _prettyRoom(String raw) => raw
    .split('_')
    .where((w) => w.isNotEmpty)
    .map((w) => '${w[0].toUpperCase()}${w.substring(1)}')
    .join(' ');

/// Format an integer rand price with a thin space thousands separator —
/// "R12 500" reads cleaner than "R12500".
String _formatRand(num value) {
  final whole = value.round().toString();
  final buf = StringBuffer();
  for (var i = 0; i < whole.length; i++) {
    if (i > 0 && (whole.length - i) % 3 == 0) buf.write(' ');
    buf.write(whole[i]);
  }
  return 'R$buf';
}

/// Prepend a scheme if the user/database dropped one — "scancourse.co.za"
/// alone would fail to launch.
Uri? _safeWebUri(String raw) {
  final trimmed = raw.trim();
  if (trimmed.isEmpty) return null;
  final withScheme =
      trimmed.startsWith('http') ? trimmed : 'https://$trimmed';
  return Uri.tryParse(withScheme);
}

IconData _roomIcon(String? roomType) {
  final t = (roomType ?? '').toLowerCase();
  if (t.contains('single')) return Icons.single_bed_outlined;
  if (t.contains('shar') || t.contains('double')) {
    return Icons.bedroom_parent_outlined;
  }
  if (t.contains('bachelor') || t.contains('studio')) {
    return Icons.meeting_room_outlined;
  }
  if (t.contains('bed')) return Icons.apartment_outlined;
  return Icons.house_outlined;
}

final accommodationDetailProvider =
    FutureProvider.family<Map<String, dynamic>, int>((ref, id) async {
  final resp = await ApiClient.instance.get('/accommodation/$id/').timeout(
        const Duration(seconds: 15),
        onTimeout: () => throw Exception('Request timed out.'),
      );
  return Map<String, dynamic>.from(resp.data);
});

class AccommodationDetailScreen extends ConsumerWidget {
  final int id;

  const AccommodationDetailScreen({super.key, required this.id});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(accommodationDetailProvider(id));
    return Scaffold(
      appBar: AppBar(
        title: const Text('Accommodation'),
        leading: BackButton(onPressed: () {
          if (context.canPop()) {
            context.pop();
          } else {
            context.go('/home');
          }
        }),
        actions: [
          async.maybeWhen(
            data: (a) => IconButton(
              icon: const Icon(Icons.share),
              tooltip: 'Share',
              onPressed: () => Share.share(
                '${a['name']}'
                '${a['city'] != null ? ' in ${a['city']}' : ''} '
                'on Scancourse · https://scancourse.co.za',
                subject: (a['name'] as String?) ?? 'Accommodation',
              ),
            ),
            orElse: () => const SizedBox(width: 48),
          ),
          BookmarkButton(itemType: 'accommodation', itemId: id),
        ],
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
                Text('Could not load details',
                    style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 16),
                OutlinedButton(
                  onPressed: () =>
                      ref.invalidate(accommodationDetailProvider(id)),
                  child: const Text('Retry'),
                ),
              ],
            ),
          ),
        ),
        data: (a) => RefreshIndicator(
          onRefresh: () async =>
              ref.invalidate(accommodationDetailProvider(id)),
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
              // ── Header (matches the list card's look) ────────────────
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
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
                    child: Icon(_roomIcon(a['room_type'] as String?),
                        color: Colors.white, size: 30),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text((a['name'] as String?) ?? 'Accommodation',
                            style: Theme.of(context).textTheme.titleLarge),
                        const SizedBox(height: 2),
                        if (_locationLine(a) != null)
                          Text(
                            _locationLine(a)!,
                            style: const TextStyle(
                                fontSize: 13,
                                color: AppColors.textSecondary),
                          ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  if (a['price_per_month'] != null)
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          _formatRand(
                              double.tryParse(a['price_per_month'].toString()) ??
                                  0),
                          style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.w900,
                              color: AppColors.primary,
                              height: 1),
                        ),
                        const Text('per month',
                            style: TextStyle(
                                fontSize: 10, color: AppColors.textHint)),
                      ],
                    ),
                ],
              ),
              const SizedBox(height: 12),
              // On-campus vs private residence tag.
              Builder(builder: (_) {
                final onCampus = _isOnCampusRes(a);
                final c = onCampus ? AppColors.primary : AppColors.textSecondary;
                return Container(
                  margin: const EdgeInsets.only(bottom: 10),
                  padding: const EdgeInsets.symmetric(
                      horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: c.withOpacity(0.10),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: c.withOpacity(0.35)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(onCampus ? Icons.apartment : Icons.house_outlined,
                          size: 15, color: c),
                      const SizedBox(width: 6),
                      Text(
                        onCampus ? 'On-campus residence' : 'Private accommodation',
                        style: TextStyle(
                            color: c, fontWeight: FontWeight.w700, fontSize: 12.5),
                      ),
                    ],
                  ),
                );
              }),
              // Campus the residence belongs to / is nearest to.
              if (a['nearby_institution_name'] != null)
                _row(Icons.school_outlined,
                    'Campus: ${a['nearby_institution_name']}'),
              const SizedBox(height: 4),
              // NSFAS accreditation — prominent.
              if (a['nsfas_accredited'] == true)
                Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.symmetric(
                      horizontal: 12, vertical: 7),
                  decoration: BoxDecoration(
                    color: AppColors.eligible.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                        color: AppColors.eligible.withOpacity(0.4)),
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.verified_outlined,
                          size: 16, color: AppColors.eligible),
                      SizedBox(width: 6),
                      Text('NSFAS Accredited',
                          style: TextStyle(
                              color: AppColors.eligible,
                              fontWeight: FontWeight.w700)),
                    ],
                  ),
                ),
              if (a['address'] != null)
                _row(Icons.location_on_outlined, a['address'].toString()),
              if (a['room_type'] != null)
                _row(Icons.bed_outlined,
                    _prettyRoom(a['room_type'].toString())),
              if (a['distance_km'] != null)
                _row(
                  Icons.directions_walk,
                  // Format to one decimal so "1.5000" doesn't reach the
                  // user, and round 0.x to 1 dp not 0.
                  '${(double.tryParse(a['distance_km'].toString()) ?? 0).toStringAsFixed(1)} km from campus',
                ),

              // Features
              if ((a['features'] as List?)?.isNotEmpty == true) ...[
                const SizedBox(height: 16),
                Text('Features',
                    style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final f in (a['features'] as List))
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 5),
                        decoration: BoxDecoration(
                          color: AppColors.surface,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: AppColors.border),
                        ),
                        child: Text(f.toString(),
                            style: const TextStyle(
                                fontSize: 12,
                                color: AppColors.textSecondary,
                                fontWeight: FontWeight.w600)),
                      ),
                  ],
                ),
              ],

              if (a['description'] != null) ...[
                const SizedBox(height: 16),
                Text('About',
                    style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 6),
                Text(a['description'].toString()),
              ],

              const SizedBox(height: 20),
              Text('Contact',
                  style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              if (a['contact_name'] != null &&
                  a['contact_name'].toString().isNotEmpty)
                _row(Icons.person_outline, a['contact_name'].toString()),
              const SizedBox(height: 8),
              if (a['contact_phone'] != null &&
                  a['contact_phone'].toString().isNotEmpty)
                ElevatedButton.icon(
                  // tel: URIs need spaces stripped on some Android
                  // dialers — and we keep the user-friendly number on
                  // the button label.
                  onPressed: () => launchUrl(Uri.parse(
                      'tel:${a['contact_phone'].toString().replaceAll(RegExp(r"\s+"), "")}')),
                  icon: const Icon(Icons.phone),
                  label: Text('Call ${a['contact_phone']}',
                      maxLines: 1, overflow: TextOverflow.ellipsis),
                  style: ElevatedButton.styleFrom(
                      minimumSize: const Size(double.infinity, 48)),
                ),
              if (a['contact_email'] != null &&
                  a['contact_email'].toString().isNotEmpty) ...[
                const SizedBox(height: 8),
                OutlinedButton.icon(
                  onPressed: () => launchUrl(
                      Uri.parse('mailto:${a['contact_email'].toString().trim()}')),
                  icon: const Icon(Icons.email_outlined),
                  label: Text('Email ${a['contact_email']}',
                      maxLines: 1, overflow: TextOverflow.ellipsis),
                  style: OutlinedButton.styleFrom(
                      minimumSize: const Size(double.infinity, 48)),
                ),
              ],
              if (a['website'] != null &&
                  a['website'].toString().isNotEmpty) ...[
                const SizedBox(height: 8),
                OutlinedButton.icon(
                  onPressed: () async {
                    final uri = _safeWebUri(a['website'].toString());
                    if (uri == null) return;
                    final ok = await launchUrl(uri,
                        mode: LaunchMode.externalApplication);
                    if (!ok && context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                            content: Text("Couldn't open the website")),
                      );
                    }
                  },
                  icon: const Icon(Icons.language_outlined),
                  label: const Text('Visit website'),
                  style: OutlinedButton.styleFrom(
                      minimumSize: const Size(double.infinity, 48)),
                ),
              ],
              SizedBox(height: 32 + MediaQuery.of(context).padding.bottom),
            ],
          ),
          ),
        ),
      ),
    );
  }

  Widget _row(IconData icon, String text) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          children: [
            Icon(icon, size: 18, color: AppColors.primary),
            const SizedBox(width: 8),
            Expanded(child: Text(text)),
          ],
        ),
      );
}
