import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/constants/app_constants.dart';
import '../../../providers/auth_provider.dart';
import '../../../providers/aps_provider.dart';
import '../../widgets/cards/aps_score_card.dart';
// import '../../widgets/common/language_picker.dart';  // disabled — English only for now

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  static const _storage = FlutterSecureStorage();
  File? _localImage;

  /// Grade-aware subtitle for the consolidated APS+Plan tile.
  /// Grade 10/11 → still in school → can improve marks
  /// Grade 12/gap year → marks locked → focus on applications
  static String _planTileSubtitle(String? grade) {
    if (grade == 'grade_10' || grade == 'grade_11') {
      return 'AI plan to lift your marks';
    }
    if (grade == 'grade_12' || grade == 'gap_year' || grade == 'other') {
      return 'AI plan to apply, win bursaries + plan your route';
    }
    return 'AI plan tailored to where you are right now';
  }

  @override
  void initState() {
    super.initState();
    _loadLocalImage();
  }

  Future<void> _loadLocalImage() async {
    final path = await _storage.read(key: 'profile_image_path');
    if (path == null) return;
    final file = File(path);
    if (await file.exists() && mounted) {
      setState(() => _localImage = file);
    }
  }

  /// Multi-select-aware display: show every preferred field the user
  /// picked (not just the first/singular one). Falls back to the legacy
  /// singular field, then 'Not set'.
  static String _fieldsDisplay(dynamic user) {
    final list = (user?.preferredFields as List?)?.cast<String>() ?? const [];
    if (list.isNotEmpty) {
      return list
          .map((f) => AppConstants.studyFields[f] ?? f)
          .join(', ');
    }
    final single = user?.preferredField as String?;
    if (single != null && single.isNotEmpty) {
      return AppConstants.studyFields[single] ?? single;
    }
    return 'Not set';
  }

  static String _provincesDisplay(dynamic user) {
    final list = (user?.preferredStudyProvinces as List?)?.cast<String>() ??
        const [];
    if (list.isNotEmpty) {
      return list
          .map((p) => AppConstants.provinces[p] ?? p)
          .join(', ');
    }
    final single = user?.preferredStudyProvince as String?;
    if (single != null && single.isNotEmpty) {
      return AppConstants.provinces[single] ?? single;
    }
    return 'Not set';
  }

  static String _careersDisplay(dynamic user) {
    final list =
        (user?.dreamCareers as List?)?.cast<String>() ?? const [];
    if (list.isNotEmpty) return list.join(', ');
    final single = user?.dreamCareer as String?;
    if (single != null && single.isNotEmpty) return single;
    return 'Not set';
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authStateProvider).user;
    final apsAsync = ref.watch(latestApsProvider);
    final reportsAsync = ref.watch(reportListProvider);
    final hasReports = reportsAsync.valueOrNull?.isNotEmpty ?? false;
    final firstReportId = (reportsAsync.valueOrNull?.isNotEmpty ?? false)
        ? reportsAsync.value!.first.id
        : null;

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Profile'),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit_outlined),
            tooltip: 'Edit profile',
            onPressed: () async {
              await context.push('/edit-profile');
              _loadLocalImage(); // refresh image after returning from edit
            },
          ),
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            tooltip: 'Settings',
            onPressed: () => context.push('/settings'),
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),
              color: Colors.white,
              child: Column(
                children: [
                  CircleAvatar(
                    radius: 44,
                    backgroundColor: AppColors.primaryLight,
                    backgroundImage: _localImage != null ? FileImage(_localImage!) : null,
                    child: _localImage == null
                        ? Text(
                            user?.firstName.isNotEmpty == true ? user!.firstName[0].toUpperCase() : 'S',
                            style: const TextStyle(
                              color: AppColors.primary,
                              fontSize: 36,
                              fontWeight: FontWeight.w700,
                            ),
                          )
                        : null,
                  ),
                  const SizedBox(height: 12),
                  Text(user?.fullName ?? 'Student',
                      style: Theme.of(context).textTheme.headlineSmall),
                  const SizedBox(height: 4),
                  Text(user?.email ?? '', style: Theme.of(context).textTheme.bodyMedium),
                  const SizedBox(height: 12),
                  if (user?.grade != null)
                    Chip(
                      label: Text(AppConstants.grades[user!.grade] ?? user.grade!),
                      backgroundColor: AppColors.primaryLight,
                      labelStyle: const TextStyle(color: AppColors.primary),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 12),

            // APS Score
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: apsAsync.when(
                data: (aps) => aps != null
                    ? Column(
                        children: [
                          ApsScoreCard(totalAps: aps.totalAps, subjects: aps.subjects),
                          OutlinedButton.icon(
                            onPressed: () => context.push('/manual-entry'),
                            icon: const Icon(Icons.edit_outlined, size: 16),
                            label: const Text('Edit Marks'),
                            style: OutlinedButton.styleFrom(
                              minimumSize: const Size(double.infinity, 44),
                              textStyle: const TextStyle(fontSize: 14),
                            ),
                          ),
                          const SizedBox(height: 8),
                        ],
                      )
                    : _EmptyApsCard(
                        hasReports: hasReports,
                        onEditReport: firstReportId != null
                            ? () => context.push('/reports/$firstReportId')
                            : null,
                      ),
                loading: () => const SizedBox.shrink(),
                error: (_, __) => const SizedBox.shrink(),
              ),
            ),

            // Profile Details
            Padding(
              padding: const EdgeInsets.all(16),
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.border),
                ),
                child: Column(
                  children: [
                    _ProfileTile(
                      icon: Icons.location_on_outlined,
                      label: 'Province',
                      value: user?.province != null ? (AppConstants.provinces[user!.province] ?? user.province!) : 'Not set',
                    ),
                    _ProfileTile(
                      icon: Icons.category_outlined,
                      label: 'Preferred Fields',
                      value: _fieldsDisplay(user),
                    ),
                    _ProfileTile(
                      icon: Icons.star_outline,
                      label: 'Dream Careers',
                      value: _careersDisplay(user),
                    ),
                    _ProfileTile(
                      icon: Icons.school_outlined,
                      label: 'Preferred Study Provinces',
                      value: _provincesDisplay(user),
                      isLast: true,
                    ),
                  ],
                ),
              ),
            ),

            // Actions
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.border),
                ),
                child: Column(
                  children: [
                    // Personal data — things that are YOURS, not settings.
                    // (My APS Journey + My Plan were merged into one screen.)
                    ListTile(
                      leading: const Icon(Icons.show_chart_rounded,
                          color: AppColors.primary),
                      title: const Text('My APS & Next Steps'),
                      subtitle: Text(
                          _planTileSubtitle(user?.grade),
                          style: const TextStyle(
                              fontSize: 12,
                              color: AppColors.textSecondary)),
                      trailing: const Icon(Icons.arrow_forward_ios, size: 14),
                      onTap: () => context.push('/aps-journey'),
                    ),
                    ListTile(
                      leading: const Icon(Icons.description_outlined, color: AppColors.primary),
                      title: const Text('My Reports'),
                      subtitle: const Text('Uploaded report cards',
                          style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                      trailing: const Icon(Icons.arrow_forward_ios, size: 14),
                      onTap: () => context.push('/reports'),
                    ),
                    ListTile(
                      leading: const Icon(Icons.assignment_outlined, color: AppColors.primary),
                      title: const Text('My Applications'),
                      subtitle: const Text('Track courses + bursaries you\'ve applied to',
                          style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                      trailing: const Icon(Icons.arrow_forward_ios, size: 14),
                      onTap: () => context.push('/applications'),
                    ),
                    ListTile(
                      leading: const Icon(Icons.bookmark_outline, color: AppColors.primary),
                      title: const Text('Saved Items'),
                      subtitle: const Text('Bookmarked courses + bursaries',
                          style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                      trailing: const Icon(Icons.arrow_forward_ios, size: 14),
                      onTap: () => context.push('/saved'),
                    ),
                    const Divider(height: 1, indent: 56),
                    // Single entry point to everything else.
                    ListTile(
                      leading: const Icon(Icons.settings_outlined, color: AppColors.textSecondary),
                      title: const Text('Settings'),
                      subtitle: const Text(
                          'Notifications, security, privacy, about',
                          style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                      trailing: const Icon(Icons.arrow_forward_ios, size: 14),
                      onTap: () => context.push('/settings'),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}

class _ProfileTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final bool isLast;

  const _ProfileTile({required this.icon, required this.label, required this.value, this.isLast = false});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        ListTile(
          leading: Icon(icon, color: AppColors.primary),
          title: Text(label, style: Theme.of(context).textTheme.bodySmall),
          subtitle: Text(value, style: Theme.of(context).textTheme.titleMedium),
        ),
        if (!isLast) const Divider(height: 1, indent: 56),
      ],
    );
  }
}

class _EmptyApsCard extends StatelessWidget {
  final bool hasReports;
  final VoidCallback? onEditReport;
  const _EmptyApsCard({this.hasReports = false, this.onEditReport});

  @override
  Widget build(BuildContext context) {
    // If the user already uploaded something but we couldn't extract marks
    // (still processing or OCR failed), nudge them to fix it rather than
    // suggesting "upload your report card" — they already did.
    final String title = hasReports ? 'Finish your APS' : 'No APS score yet';
    final String body = hasReports
        ? 'We couldn\'t read all your marks yet. Tap your report to check and edit the subjects.'
        : 'Upload your report card or enter marks to calculate your APS';

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          Icon(
            hasReports
                ? Icons.edit_document
                : Icons.document_scanner_outlined,
            size: 48,
            color: AppColors.textHint,
          ),
          const SizedBox(height: 12),
          Text(title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(body,
              style: Theme.of(context).textTheme.bodySmall,
              textAlign: TextAlign.center),
          if (hasReports && onEditReport != null) ...[
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: onEditReport,
              icon: const Icon(Icons.edit_outlined, size: 16),
              label: const Text('Open My Report'),
              style: OutlinedButton.styleFrom(
                minimumSize: const Size(double.infinity, 44),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
