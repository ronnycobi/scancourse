import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/services/api/api_client.dart';
import '../../widgets/common/app_text_field.dart';
import '../../widgets/common/brand_header.dart';
import '../../widgets/common/error_banner.dart';
import '../../widgets/common/loading_button.dart';

/// Final step of the password-reset flow.
///
/// Two states:
///   - Deep-link arrival (uid + token present in route): show only the
///     new-password + confirm fields. The uid/token are already in
///     memory and never displayed to the user.
///   - Direct navigation (no uid/token): show a friendly "check your
///     email" card pointing the user back to the reset email. We don't
///     ask them to paste anything anymore — the email button does it.
class ResetPasswordScreen extends StatefulWidget {
  /// Pre-populated values when arriving via deep link.
  final String? initialUid;
  final String? initialToken;

  const ResetPasswordScreen({super.key, this.initialUid, this.initialToken});

  @override
  State<ResetPasswordScreen> createState() => _ResetPasswordScreenState();
}

class _ResetPasswordScreenState extends State<ResetPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _pwCtrl = TextEditingController();
  final _confirmCtrl = TextEditingController();
  bool _obscure = true;
  bool _busy = false;
  bool _done = false;
  String? _error;

  @override
  void dispose() {
    _pwCtrl.dispose();
    _confirmCtrl.dispose();
    super.dispose();
  }

  bool get _hasDeepLink =>
      (widget.initialUid?.isNotEmpty ?? false) &&
      (widget.initialToken?.isNotEmpty ?? false);

  Future<void> _submit() async {
    setState(() => _error = null);
    if (!_formKey.currentState!.validate()) return;
    if (_pwCtrl.text != _confirmCtrl.text) {
      setState(() => _error = 'Passwords do not match.');
      return;
    }
    setState(() => _busy = true);
    try {
      await ApiClient.instance.post(
        '/auth/password-reset/confirm/',
        data: {
          'uid': widget.initialUid!.trim(),
          'token': widget.initialToken!.trim(),
          'new_password': _pwCtrl.text,
        },
      );
      if (mounted) setState(() => _done = true);
    } catch (e) {
      final msg = e.toString().toLowerCase();
      String pretty =
          'Could not reset password. The reset link may have expired — request a new one.';
      if (msg.contains('invalid')) {
        pretty = 'That reset link is invalid. Request a new one.';
      } else if (msg.contains('expired')) {
        pretty = 'That reset link has expired. Request a new one.';
      } else if (msg.contains('8 characters') || msg.contains('at least 8')) {
        pretty =
            'Password must be at least 8 characters with a letter and digit.';
      }
      if (mounted) setState(() => _error = pretty);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Reset Password')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: _done
              ? _SuccessView()
              : (_hasDeepLink ? _passwordForm(context) : _checkEmailCard(context)),
        ),
      ),
    );
  }

  // ── Deep-link arrival: short password form ────────────────────────
  Widget _passwordForm(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const BrandHeader(),
          const SizedBox(height: 28),
          Text('Set a new password',
              style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 8),
          const Text(
            'Choose a new password for your Scancourse account. At least 8 characters with a letter and a digit.',
            style: TextStyle(color: AppColors.textSecondary, fontSize: 14),
          ),
          const SizedBox(height: 24),
          ErrorBanner(
              message: _error,
              onDismiss: () => setState(() => _error = null)),
          AppTextField(
            label: 'New password',
            controller: _pwCtrl,
            obscureText: _obscure,
            prefixIcon: Icons.lock_outline,
            suffixIcon: IconButton(
              tooltip: _obscure ? 'Show password' : 'Hide password',
              icon: Icon(_obscure
                  ? Icons.visibility_outlined
                  : Icons.visibility_off_outlined),
              onPressed: () => setState(() => _obscure = !_obscure),
            ),
            validator: (v) {
              if (v == null || v.length < 8) return 'At least 8 characters';
              if (!RegExp(r'[A-Za-z]').hasMatch(v) ||
                  !RegExp(r'\d').hasMatch(v)) {
                return 'Must include a letter AND a digit';
              }
              return null;
            },
          ),
          const SizedBox(height: 16),
          AppTextField(
            label: 'Confirm new password',
            controller: _confirmCtrl,
            obscureText: _obscure,
            prefixIcon: Icons.lock_outline,
            validator: (v) =>
                (v?.isEmpty ?? true) ? 'Confirm your password' : null,
          ),
          const SizedBox(height: 28),
          LoadingButton(
            label: 'Set new password',
            isLoading: _busy,
            onPressed: _submit,
          ),
          const SizedBox(height: 16),
          Center(
            child: TextButton(
              onPressed: () => context.go('/login'),
              child: const Text('Back to login'),
            ),
          ),
        ],
      ),
    );
  }

  // ── No deep link: explain how to use the email ────────────────────
  Widget _checkEmailCard(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const BrandHeader(),
        const SizedBox(height: 28),
        Text('Check your email',
            style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 8),
        const Text(
          "We sent you a reset link. Tap the button in the email to choose a new password.",
          style: TextStyle(color: AppColors.textSecondary, fontSize: 14),
        ),
        const SizedBox(height: 24),
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: AppColors.primaryLight,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppColors.primary.withOpacity(0.25)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: const [
              Row(
                children: [
                  Icon(Icons.mark_email_read_outlined,
                      color: AppColors.primary, size: 22),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      "Look for an email from info@scancourse.co.za",
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ),
                ],
              ),
              SizedBox(height: 12),
              Text(
                "Subject: \"Reset your Scancourse password\".\n"
                "Tap the big blue button inside — that's it.",
                style: TextStyle(
                  fontSize: 13,
                  color: AppColors.textSecondary,
                  height: 1.5,
                ),
              ),
              SizedBox(height: 14),
              Text(
                "Can't find it? Check your spam folder.",
                style: TextStyle(
                  fontSize: 12.5,
                  color: AppColors.textHint,
                  fontStyle: FontStyle.italic,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        OutlinedButton.icon(
          onPressed: () => context.go('/forgot-password'),
          icon: const Icon(Icons.refresh_outlined),
          label: const Text('Send a new reset email'),
          style: OutlinedButton.styleFrom(
            minimumSize: const Size(double.infinity, 48),
          ),
        ),
        const SizedBox(height: 10),
        TextButton(
          onPressed: () => context.go('/login'),
          child: const Text('Back to login'),
        ),
      ],
    );
  }
}

class _SuccessView extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const SizedBox(height: 40),
        const Icon(Icons.check_circle, size: 80, color: AppColors.eligible),
        const SizedBox(height: 20),
        Text('Password reset!',
            style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 8),
        const Text(
          'You can now log in with your new password.',
          style: TextStyle(color: AppColors.textSecondary),
        ),
        const SizedBox(height: 28),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: () => context.go('/login'),
            child: const Text('Go to login'),
          ),
        ),
      ],
    );
  }
}
