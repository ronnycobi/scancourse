import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/services/api/api_client.dart';
import '../../widgets/common/bookmark_button.dart';

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
        leading: BackButton(onPressed: () => context.pop()),
        actions: [BookmarkButton(itemType: 'accommodation', itemId: id)],
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
        data: (a) => SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text((a['name'] as String?) ?? 'Accommodation',
                  style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 8),
              // NSFAS accreditation — prominent, right under the name.
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
              if (a['city'] != null)
                _row(Icons.location_city_outlined, a['city'].toString()),
              if (a['nearby_institution_name'] != null)
                _row(Icons.school_outlined,
                    'Near ${a['nearby_institution_name']}'),
              if (a['room_type'] != null)
                _row(Icons.bed_outlined,
                    a['room_type'].toString().replaceAll('_', ' ')),
              if (a['price_per_month'] != null)
                _row(Icons.attach_money,
                    'R${a['price_per_month']} / month'),
              if (a['distance_km'] != null)
                _row(Icons.directions_walk,
                    '${a['distance_km']} km from campus'),

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
              if (a['contact_phone'] != null)
                ElevatedButton.icon(
                  onPressed: () => launchUrl(
                      Uri.parse('tel:${a['contact_phone']}')),
                  icon: const Icon(Icons.phone),
                  label: Text('Call ${a['contact_phone']}'),
                  style: ElevatedButton.styleFrom(
                      minimumSize: const Size(double.infinity, 48)),
                ),
              if (a['contact_email'] != null) ...[
                const SizedBox(height: 8),
                OutlinedButton.icon(
                  onPressed: () => launchUrl(
                      Uri.parse('mailto:${a['contact_email']}')),
                  icon: const Icon(Icons.email_outlined),
                  label: Text('Email ${a['contact_email']}'),
                  style: OutlinedButton.styleFrom(
                      minimumSize: const Size(double.infinity, 48)),
                ),
              ],
              if (a['website'] != null &&
                  a['website'].toString().isNotEmpty) ...[
                const SizedBox(height: 8),
                OutlinedButton.icon(
                  onPressed: () => launchUrl(
                      Uri.parse(a['website'].toString()),
                      mode: LaunchMode.externalApplication),
                  icon: const Icon(Icons.language_outlined),
                  label: const Text('Visit website'),
                  style: OutlinedButton.styleFrom(
                      minimumSize: const Size(double.infinity, 48)),
                ),
              ],
            ],
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
