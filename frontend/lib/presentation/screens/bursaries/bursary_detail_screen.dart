import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/constants/app_constants.dart';
import '../../../data/models/bursary_model.dart';
import '../../../data/services/api/api_client.dart';
import '../../widgets/common/bookmark_button.dart';

final bursaryDetailProvider =
    FutureProvider.family<BursaryModel, int>((ref, id) async {
  final resp = await ApiClient.instance.get('/bursaries/$id/');
  return BursaryModel.fromJson(resp.data as Map<String, dynamic>);
});

class BursaryDetailScreen extends ConsumerWidget {
  final int id;
  const BursaryDetailScreen({super.key, required this.id});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bursaryAsync = ref.watch(bursaryDetailProvider(id));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Bursary Details'),
        leading: BackButton(onPressed: () => context.pop()),
        actions: [BookmarkButton(itemType: 'bursary', itemId: id)],
      ),
      body: bursaryAsync.when(
        data: (b) => SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                children: [
                  Container(
                    width: 56,
                    height: 56,
                    decoration: BoxDecoration(
                      color: AppColors.accentLight,
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: const Icon(Icons.card_giftcard,
                        color: AppColors.accent, size: 28),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(b.name,
                            style:
                                Theme.of(context).textTheme.headlineSmall),
                        Text(b.provider,
                            style:
                                Theme.of(context).textTheme.bodyMedium),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // Deadline banner
              if (b.applicationDeadline != null)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(14),
                  margin: const EdgeInsets.only(bottom: 20),
                  decoration: BoxDecoration(
                    color: AppColors.errorLight,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.timer_outlined,
                          color: AppColors.error, size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Application Deadline',
                                style: TextStyle(
                                    color: AppColors.error,
                                    fontWeight: FontWeight.w600,
                                    fontSize: 13)),
                            Text(b.applicationDeadline!,
                                style: const TextStyle(
                                    color: AppColors.error,
                                    fontSize: 12)),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

              // Chips
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  _InfoTag(
                    label: b.fundingType
                        .replaceAll('_', ' ')
                        .toUpperCase(),
                    color: AppColors.secondary,
                  ),
                  _InfoTag(
                    label: AppConstants.studyFields[b.field] ?? b.field,
                    color: AppColors.primary,
                  ),
                  if (b.province.isNotEmpty)
                    _InfoTag(
                      label: AppConstants.provinces[b.province] ??
                          b.province,
                      color: AppColors.accent,
                    ),
                ],
              ),
              const SizedBox(height: 20),

              // Amount
              if (b.amount != null) ...[
                _DetailSection(
                  title: 'Funding Amount',
                  child: Text(
                    'R${b.amount!.toStringAsFixed(0)} per year',
                    style: Theme.of(context)
                        .textTheme
                        .headlineMedium
                        ?.copyWith(color: AppColors.secondary),
                  ),
                ),
              ],

              // Description
              if (b.description?.isNotEmpty == true)
                _DetailSection(
                  title: 'About This Bursary',
                  child: Text(b.description!,
                      style: Theme.of(context).textTheme.bodyMedium),
                ),

              // Eligibility
              if (b.eligibility?.isNotEmpty == true)
                _DetailSection(
                  title: 'Eligibility Requirements',
                  child: Text(b.eligibility!,
                      style: Theme.of(context).textTheme.bodyMedium),
                ),

              // Coverage
              if (b.coverage?.isNotEmpty == true)
                _DetailSection(
                  title: 'What\'s Covered',
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: b.coverage!
                        .map((c) => Padding(
                              padding: const EdgeInsets.only(bottom: 6),
                              child: Row(
                                children: [
                                  const Icon(
                                      Icons.check_circle_outline,
                                      size: 16,
                                      color: AppColors.secondary),
                                  const SizedBox(width: 8),
                                  Text(c.toString(),
                                      style: Theme.of(context)
                                          .textTheme
                                          .bodyMedium),
                                ],
                              ),
                            ))
                        .toList(),
                  ),
                ),

              // Academic requirements
              if (b.minGradeAverage != null || b.maxHouseholdIncome != null)
                _DetailSection(
                  title: 'Requirements',
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (b.minGradeAverage != null)
                        _RequirementRow(
                          icon: Icons.school_outlined,
                          label: 'Minimum grade average',
                          value: '${b.minGradeAverage}%',
                        ),
                      if (b.maxHouseholdIncome != null)
                        _RequirementRow(
                          icon: Icons.family_restroom,
                          label: 'Maximum household income',
                          value: 'R${b.maxHouseholdIncome!} p.a.',
                        ),
                    ],
                  ),
                ),

              const SizedBox(height: 24),

              // Apply CTA
              ElevatedButton.icon(
                onPressed: () async {
                  final uri = Uri.parse(b.applicationUrl);
                  if (await canLaunchUrl(uri)) {
                    launchUrl(uri, mode: LaunchMode.externalApplication);
                  }
                },
                icon: const Icon(Icons.open_in_new),
                label: const Text('Apply Now'),
              ),
            ],
          ),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) =>
            Center(child: Text('Error loading bursary: $e')),
      ),
    );
  }
}

class _InfoTag extends StatelessWidget {
  final String label;
  final Color color;
  const _InfoTag({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(label,
          style: TextStyle(
              color: color, fontSize: 12, fontWeight: FontWeight.w600)),
    );
  }
}

class _DetailSection extends StatelessWidget {
  final String title;
  final Widget child;
  const _DetailSection({required this.title, required this.child});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 10),
          child,
        ],
      ),
    );
  }
}

class _RequirementRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  const _RequirementRow(
      {required this.icon, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          Icon(icon, size: 18, color: AppColors.primary),
          const SizedBox(width: 10),
          Expanded(
              child: Text(label,
                  style: Theme.of(context).textTheme.bodyMedium)),
          Text(value, style: Theme.of(context).textTheme.titleMedium),
        ],
      ),
    );
  }
}
