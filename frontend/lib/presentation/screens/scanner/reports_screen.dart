import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/models/aps_model.dart';
import '../../../data/services/api/api_client.dart';
import '../../../providers/aps_provider.dart';

class ReportsScreen extends ConsumerWidget {
  const ReportsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(reportListProvider);
    final apsAsync = ref.watch(latestApsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Reports'),
        leading: BackButton(onPressed: () {
          if (context.canPop()) {
            context.pop();
          } else {
            context.go('/home');
          }
        }),
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(reportListProvider);
          ref.invalidate(latestApsProvider);
        },
        child: ListView(
          padding: EdgeInsets.fromLTRB(
              16, 16, 16, 48 + MediaQuery.of(context).padding.bottom),
          children: [
            // Merged APS card — explains the "best marks across reports" logic.
            apsAsync.when(
              loading: () => const SizedBox.shrink(),
              error: (_, __) => const SizedBox.shrink(),
              data: (aps) {
                if (aps == null || aps.totalAps == 0) return const SizedBox.shrink();
                return Container(
                  padding: const EdgeInsets.all(16),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [AppColors.primary, AppColors.primaryDark],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Your Best APS',
                          style: TextStyle(
                              color: Colors.white70, fontSize: 12, fontWeight: FontWeight.w600)),
                      const SizedBox(height: 4),
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text('${aps.totalAps}',
                              style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 44,
                                  fontWeight: FontWeight.w900,
                                  height: 1)),
                          const SizedBox(width: 4),
                          const Padding(
                            padding: EdgeInsets.only(bottom: 8),
                            child: Text('/42',
                                style: TextStyle(
                                    color: Colors.white70,
                                    fontSize: 16,
                                    fontWeight: FontWeight.w600)),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        'Calculated using the best mark per subject across all your reports.',
                        style: TextStyle(color: Colors.white70, fontSize: 12),
                      ),
                    ],
                  ),
                );
              },
            ),

            // Upload-another CTA
            OutlinedButton.icon(
              onPressed: () => context.push('/scanner'),
              icon: const Icon(Icons.add_circle_outline),
              label: const Text('Upload another report'),
              style: OutlinedButton.styleFrom(
                minimumSize: const Size(double.infinity, 48),
              ),
            ),
            const SizedBox(height: 16),

            // Reports list
            async.when(
              loading: () => const Padding(
                padding: EdgeInsets.all(40),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (e, _) => Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    const Icon(Icons.wifi_off_outlined,
                        size: 48, color: AppColors.textHint),
                    const SizedBox(height: 12),
                    const Text('Could not load reports'),
                    const SizedBox(height: 12),
                    OutlinedButton(
                      onPressed: () => ref.invalidate(reportListProvider),
                      child: const Text('Retry'),
                    ),
                  ],
                ),
              ),
              data: (reports) {
                if (reports.isEmpty) {
                  return Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      children: [
                        const Icon(Icons.document_scanner_outlined,
                            size: 56, color: AppColors.textHint),
                        const SizedBox(height: 12),
                        Text('No reports uploaded yet',
                            style: Theme.of(context).textTheme.titleMedium),
                        const SizedBox(height: 6),
                        const Padding(
                          padding: EdgeInsets.symmetric(horizontal: 24),
                          child: Text(
                            'Scan or upload your report card — you can add multiple sittings '
                            '(Grade 11, NSC final, supplementary or upgrades). We keep the '
                            'best mark per subject.',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: AppColors.textSecondary),
                          ),
                        ),
                      ],
                    ),
                  );
                }
                return Column(
                  children: [
                    Align(
                      alignment: Alignment.centerLeft,
                      child: Padding(
                        padding: const EdgeInsets.only(bottom: 8, left: 4),
                        child: Text(
                          '${reports.length} report${reports.length == 1 ? "" : "s"}',
                          style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: AppColors.textSecondary),
                        ),
                      ),
                    ),
                    ...reports.map((r) => _ReportCard(report: r)),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _ReportCard extends ConsumerWidget {
  final ReportModel report;
  const _ReportCard({required this.report});

  String get _statusLabel {
    switch (report.status) {
      case 'processing':
        return 'Processing…';
      case 'pending':
        return 'Queued';
      case 'failed':
        return 'Failed';
      case 'verified':
        return 'Verified';
      case 'completed':
        return 'Ready';
      default:
        // Capitalise the raw status as a graceful fallback for any
        // future state we haven't mapped yet.
        final s = report.status;
        return s.isEmpty ? '—' : s[0].toUpperCase() + s.substring(1);
    }
  }

  Color get _statusColor {
    switch (report.status) {
      case 'failed':
        return AppColors.error;
      case 'processing':
      case 'pending':
        return AppColors.accent;
      case 'verified':
      case 'completed':
        return AppColors.eligible;
      default:
        return AppColors.textHint;
    }
  }

  String _formatDate() {
    final d = report.createdAt;
    if (d == null) return '';
    const months = [
      '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    return '${d.day} ${months[d.month]} ${d.year}';
  }

  Future<void> _confirmDelete(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Delete report?'),
        content: Text(
          'This removes the report and its subjects from your account. '
          'Your APS will recalculate from your remaining reports.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(c, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
            onPressed: () => Navigator.pop(c, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await ApiClient.instance.delete('/ocr/reports/${report.id}/');
      ref.invalidate(reportListProvider);
      ref.invalidate(latestApsProvider);
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not delete report.')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final aps = report.apsResult?.totalAps ?? 0;
    final nSubjects = (report.subjects?.length ?? 0);
    return GestureDetector(
      onTap: () => context.push('/reports/${report.id}'),
      child: Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: AppColors.primaryLight,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(
                  report.fileType == 'pdf'
                      ? Icons.picture_as_pdf_outlined
                      : Icons.image_outlined,
                  color: AppColors.primary,
                  size: 22,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      report.schoolName?.isNotEmpty == true
                          ? report.schoolName!
                          // Title falls back to a friendlier label —
                          // the date already appears in the subtitle so
                          // don't repeat it.
                          : 'Uploaded report',
                      style: const TextStyle(
                          fontSize: 14, fontWeight: FontWeight.w700),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    Text(
                      [
                        _formatDate(),
                        '$nSubjects subjects',
                        if (aps > 0) 'APS $aps',
                      ].where((s) => s.isNotEmpty).join('  •  '),
                      style: const TextStyle(
                          fontSize: 12, color: AppColors.textSecondary),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: _statusColor.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(_statusLabel,
                    style: TextStyle(
                        color: _statusColor,
                        fontSize: 10,
                        fontWeight: FontWeight.w700)),
              ),
              IconButton(
                visualDensity: VisualDensity.compact,
                icon: const Icon(Icons.delete_outline,
                    color: AppColors.textHint, size: 20),
                tooltip: 'Delete report',
                onPressed: () => _confirmDelete(context, ref),
              ),
            ],
          ),
        ],
      ),
    ),
    );
  }
}
