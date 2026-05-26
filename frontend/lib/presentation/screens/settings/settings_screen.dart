import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/services/api/api_client.dart';
import '../../../providers/auth_provider.dart';
import '../../widgets/common/app_avatar.dart';

/// Facebook-style settings: grouped sections, account card at top, each row
/// is icon + label + optional value preview + chevron. Toggles inline where
/// it makes sense (notifications). Destructive actions at the bottom in red.
class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  // Local UI toggles for now — wiring to a real notifications-prefs
  // endpoint can come later. The values default to "on" because that's
  // what most users want.
  bool _pushNotificationsOn = true;
  bool _emailRemindersOn = true;

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authStateProvider).user;

    return Scaffold(
      backgroundColor: const Color(0xFFF2F4F7),
      appBar: AppBar(
        title: const Text('Settings'),
        leading: BackButton(onPressed: () => context.pop()),
        backgroundColor: Colors.white,
        elevation: 0,
        scrolledUnderElevation: 0.5,
      ),
      body: ListView(
        padding: const EdgeInsets.only(bottom: 32),
        children: [
          // ── Account header card ─────────────────────────────────────
          Container(
            margin: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.border),
            ),
            child: Row(
              children: [
                const AppAvatar(radius: 28),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        user?.fullName.isNotEmpty == true
                            ? user!.fullName
                            : 'Your account',
                        style: Theme.of(context)
                            .textTheme
                            .titleMedium
                            ?.copyWith(fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        user?.email ?? '',
                        style: const TextStyle(
                            fontSize: 13, color: AppColors.textSecondary),
                      ),
                    ],
                  ),
                ),
                TextButton(
                  onPressed: () => context.push('/edit-profile'),
                  child: const Text('Edit'),
                ),
              ],
            ),
          ),

          // ── Account ─────────────────────────────────────────────────
          _Section(
            title: 'Account',
            children: [
              _Row(
                icon: Icons.person_outline,
                label: 'Edit profile',
                onTap: () => context.push('/edit-profile'),
              ),
              _Row(
                icon: Icons.lock_outline,
                label: 'Change password',
                onTap: () => context.push('/change-password'),
              ),
              _Row(
                icon: Icons.email_outlined,
                label: 'Email',
                trailingText: user?.email ?? '',
                onTap: null, // read-only — email is the account identifier
              ),
              _Row(
                icon: Icons.phone_outlined,
                label: 'Phone',
                trailingText: (user?.phoneNumber?.isNotEmpty == true)
                    ? user!.phoneNumber!
                    : 'Not set',
                onTap: () => context.push('/edit-profile'),
              ),
            ],
          ),

          // ── Notifications ───────────────────────────────────────────
          _Section(
            title: 'Notifications',
            children: [
              _SwitchRow(
                icon: Icons.notifications_active_outlined,
                label: 'Push notifications',
                subtitle:
                    'New course matches, bursary deadlines, AI insights',
                value: _pushNotificationsOn,
                onChanged: (v) => setState(() => _pushNotificationsOn = v),
              ),
              _SwitchRow(
                icon: Icons.mark_email_unread_outlined,
                label: 'Email reminders',
                subtitle: 'Weekly digest + critical deadline alerts',
                value: _emailRemindersOn,
                onChanged: (v) => setState(() => _emailRemindersOn = v),
              ),
              _Row(
                icon: Icons.inbox_outlined,
                label: 'Inbox',
                trailingText: 'See your notifications',
                onTap: () => context.push('/notifications'),
              ),
            ],
          ),

          // ── Preferences ─────────────────────────────────────────────
          _Section(
            title: 'Preferences',
            children: [
              _Row(
                icon: Icons.language_outlined,
                label: 'Language',
                trailingText: 'English',
                onTap: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text(
                          'Other South African languages are coming soon.'),
                    ),
                  );
                },
              ),
              _Row(
                icon: Icons.location_on_outlined,
                label: 'Region',
                trailingText: 'South Africa',
                onTap: null,
              ),
            ],
          ),

          // ── Privacy & Data ──────────────────────────────────────────
          _Section(
            title: 'Privacy & Data',
            children: [
              _Row(
                icon: Icons.privacy_tip_outlined,
                label: 'Privacy Policy',
                onTap: () => context.push('/legal/privacy'),
              ),
              _Row(
                icon: Icons.download_outlined,
                label: 'Download my data',
                subtitle: 'POPIA: export everything we have on you',
                onTap: () => _requestDataExport(context),
              ),
              _Row(
                icon: Icons.delete_outline,
                label: 'Delete account',
                subtitle: '30-day grace period — you can cancel',
                onTap: () => _confirmDeleteAccount(context),
                destructive: true,
              ),
            ],
          ),

          // ── About & Legal ───────────────────────────────────────────
          _Section(
            title: 'About',
            children: [
              _Row(
                icon: Icons.info_outline,
                label: 'About Scancourse',
                onTap: () => context.push('/legal/about'),
              ),
              _Row(
                icon: Icons.gavel_outlined,
                label: 'Terms & Conditions',
                onTap: () => context.push('/legal/terms'),
              ),
              _Row(
                icon: Icons.policy_outlined,
                label: 'Acceptable Use',
                onTap: () => context.push('/legal/acceptable-use'),
              ),
              _Row(
                icon: Icons.warning_amber_outlined,
                label: 'Disclaimer',
                onTap: () => context.push('/legal/disclaimer'),
              ),
            ],
          ),

          // ── Help & support ──────────────────────────────────────────
          _Section(
            title: 'Help',
            children: [
              _Row(
                icon: Icons.contact_mail_outlined,
                label: 'Contact us',
                trailingText: 'info@scancourse.co.za',
                onTap: () => context.push('/legal/contact'),
              ),
              _Row(
                icon: Icons.bug_report_outlined,
                label: 'Report a bug',
                onTap: () => _emailBugReport(context),
              ),
            ],
          ),

          // ── Sign out ────────────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 24, 16, 0),
            child: SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () => _confirmSignOut(context),
                icon: const Icon(Icons.logout, color: AppColors.error),
                label: const Text('Sign out',
                    style: TextStyle(
                        color: AppColors.error,
                        fontWeight: FontWeight.w700)),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: AppColors.error),
                  minimumSize: const Size(0, 48),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 20),
          const Center(
            child: Text(
              'Scancourse · scancourse.co.za',
              style: TextStyle(fontSize: 11, color: AppColors.textHint),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _confirmSignOut(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Sign out?'),
        content: const Text('You\'ll need to sign in again next time.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(c, false),
              child: const Text('Cancel')),
          TextButton(
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
            onPressed: () => Navigator.pop(c, true),
            child: const Text('Sign out'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    await ref.read(authStateProvider.notifier).logout();
    if (mounted) context.go('/login');
  }

  Future<void> _requestDataExport(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Download my data'),
        content: const Text(
            'We\'ll email you a download link with everything we have about you (profile, marks, applications, saved items, AI chats, consent records). Continue?'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(c, false),
              child: const Text('Cancel')),
          TextButton(
              onPressed: () => Navigator.pop(c, true),
              child: const Text('Request export')),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    try {
      await ApiClient.instance.post('/legal/data-export/', data: {});
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text(
                  'Export requested. We\'ll email you when it\'s ready.')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
                'Could not request export right now. Try again later.'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  Future<void> _confirmDeleteAccount(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Delete account?'),
        content: const Text(
            'This starts a 30-day deletion process. You can cancel anytime by signing in during that window. After 30 days all your data is permanently erased.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(c, false),
              child: const Text('Cancel')),
          TextButton(
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
            onPressed: () => Navigator.pop(c, true),
            child: const Text('Delete my account'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    try {
      await ApiClient.instance.post('/legal/delete-account/', data: {});
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text(
                  'Account scheduled for deletion in 30 days. Sign in to cancel.')),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
                'Could not start deletion right now. Try again later.'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  Future<void> _emailBugReport(BuildContext context) async {
    final uri = Uri.parse(
        'mailto:info@scancourse.co.za?subject=Bug%20report%20%E2%80%94%20Scancourse'
        '&body=What%20happened%3F%0A%0AWhat%20did%20you%20expect%3F%0A%0AYour%20phone%20model%3A%0A');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    } else if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text(
                'No email app set up. Email info@scancourse.co.za directly.')),
      );
    }
  }
}

// ── Reusable atoms ───────────────────────────────────────────────────

class _Section extends StatelessWidget {
  final String title;
  final List<Widget> children;
  const _Section({required this.title, required this.children});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 18, 16, 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(left: 8, bottom: 8),
            child: Text(
              title.toUpperCase(),
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w800,
                letterSpacing: 0.7,
                color: AppColors.textSecondary,
              ),
            ),
          ),
          Container(
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.border),
            ),
            child: Column(
              children: [
                for (int i = 0; i < children.length; i++) ...[
                  children[i],
                  if (i < children.length - 1)
                    const Divider(height: 1, indent: 56, endIndent: 8),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Row extends StatelessWidget {
  final IconData icon;
  final String label;
  final String? subtitle;
  final String? trailingText;
  final VoidCallback? onTap;
  final bool destructive;

  const _Row({
    required this.icon,
    required this.label,
    this.subtitle,
    this.trailingText,
    this.onTap,
    this.destructive = false,
  });

  @override
  Widget build(BuildContext context) {
    final color = destructive ? AppColors.error : AppColors.textPrimary;
    final iconColor = destructive ? AppColors.error : AppColors.primary;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        child: Row(
          children: [
            Container(
              width: 30,
              height: 30,
              decoration: BoxDecoration(
                color: iconColor.withOpacity(0.12),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(icon, size: 18, color: iconColor),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                        color: color),
                  ),
                  if (subtitle != null) ...[
                    const SizedBox(height: 2),
                    Text(
                      subtitle!,
                      style: const TextStyle(
                          fontSize: 12, color: AppColors.textSecondary),
                    ),
                  ],
                ],
              ),
            ),
            if (trailingText != null) ...[
              const SizedBox(width: 8),
              Flexible(
                child: Text(
                  trailingText!,
                  textAlign: TextAlign.right,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                      fontSize: 13, color: AppColors.textSecondary),
                ),
              ),
            ],
            if (onTap != null) ...[
              const SizedBox(width: 4),
              const Icon(Icons.chevron_right,
                  size: 22, color: AppColors.textHint),
            ],
          ],
        ),
      ),
    );
  }
}

class _SwitchRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String? subtitle;
  final bool value;
  final ValueChanged<bool> onChanged;

  const _SwitchRow({
    required this.icon,
    required this.label,
    this.subtitle,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      child: Row(
        children: [
          Container(
            width: 30,
            height: 30,
            decoration: BoxDecoration(
              color: AppColors.primary.withOpacity(0.12),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, size: 18, color: AppColors.primary),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label,
                    style: const TextStyle(
                        fontSize: 15, fontWeight: FontWeight.w600)),
                if (subtitle != null) ...[
                  const SizedBox(height: 2),
                  Text(subtitle!,
                      style: const TextStyle(
                          fontSize: 12, color: AppColors.textSecondary)),
                ],
              ],
            ),
          ),
          Switch.adaptive(
            value: value,
            onChanged: onChanged,
            activeColor: AppColors.primary,
          ),
        ],
      ),
    );
  }
}
