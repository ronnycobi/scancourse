import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../providers/aps_provider.dart';
import '../../widgets/cards/aps_score_card.dart';
import '../../widgets/common/loading_button.dart';

class ResultsScreen extends ConsumerStatefulWidget {
  final Map<String, dynamic>? extra;

  const ResultsScreen({super.key, this.extra});

  @override
  ConsumerState<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends ConsumerState<ResultsScreen> {
  @override
  Widget build(BuildContext context) {
    final scannerState = ref.watch(scannerProvider);
    final report = scannerState.report;
    final apsResult = report?.apsResult;

    if (report == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Results'), leading: const BackButton()),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Your Results'),
        leading: const BackButton(),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (report.status == 'processing') ...[
                const Center(child: CircularProgressIndicator()),
                const SizedBox(height: 16),
                const Center(child: Text('Processing your report card...')),
              ] else if (apsResult != null) ...[
                ApsScoreCard(totalAps: apsResult.totalAps, subjects: apsResult.subjects),
                const SizedBox(height: 20),
                Text('Extracted Subjects', style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 12),
                Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Column(
                    children: apsResult.subjects.asMap().entries.map((entry) {
                      final subj = entry.value;
                      return ListTile(
                        title: Text(subj.name, style: Theme.of(context).textTheme.bodyLarge),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text('${subj.mark}%',
                                style: Theme.of(context).textTheme.titleMedium),
                            const SizedBox(width: 12),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: subj.isLifeOrientation ? AppColors.border : AppColors.primaryLight,
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: Text(
                                subj.isLifeOrientation ? 'LO' : '${subj.apsPoints} pts',
                                style: TextStyle(
                                  color: subj.isLifeOrientation ? AppColors.textHint : AppColors.primary,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ],
                        ),
                        subtitle: subj.isLifeOrientation
                            ? Text('Not counted in APS', style: Theme.of(context).textTheme.bodySmall)
                            : null,
                      );
                    }).toList(),
                  ),
                ),
                const SizedBox(height: 24),
                LoadingButton(
                  label: 'Find Matching Courses',
                  isLoading: false,
                  onPressed: () => context.go('/courses'),
                ),
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed: () => context.go('/home'),
                  child: const Text('Back to Home'),
                ),
              ] else if (report.status == 'failed') ...[
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: AppColors.errorLight,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    children: [
                      const Icon(Icons.error_outline, color: AppColors.error, size: 48),
                      const SizedBox(height: 16),
                      Text('Extraction failed', style: Theme.of(context).textTheme.titleLarge),
                      const SizedBox(height: 8),
                      Text(
                        'We couldn\'t extract your results automatically. Try entering them manually.',
                        style: Theme.of(context).textTheme.bodyMedium,
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 20),
                      LoadingButton(
                        label: 'Enter Marks Manually',
                        isLoading: false,
                        onPressed: () => context.push('/manual-entry'),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
