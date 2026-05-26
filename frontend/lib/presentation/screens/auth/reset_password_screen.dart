import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/services/api/api_client.dart';
import '../../widgets/common/app_text_field.dart';
import '../../widgets/common/brand_header.dart';
import '../../widgets/common/error_banner.dart';
import '../../widgets/common/loading_button.dart';

/// Step 2 of the password-reset flow: user pastes the UID + token they
/// received by email and sets a new password. Routes here from a deep
/// link OR from a "I have a code" button on the forgot-password screen.
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
  final _uidCtrl = TextEditingController();
  final _tokenCtrl = TextEditingController();
  final _pwCtrl = TextEditingController();
  final _confirmCtrl = TextEditingController();
  bool _obscure = true;
  bool _busy = false;
  bool _done = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _uidCtrl.text = widget.initialUid ?? '';
    _tokenCtrl.text = widget.initialToken ?? '';
  }

  @override
  void dispose() {
    _uidCtrl.dispose();
    _tokenCtrl.dispose();
    _pwCtrl.dispose();
    _confirmCtrl.dispose();
    super.dispose();
  }

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
          'uid': _uidCtrl.text.trim(),
          'token': _tokenCtrl.text.trim(),
          'new_password': _pwCtrl.text,
        },
      );
      if (mounted) setState(() => _done = true);
    } catch (e) {
      final msg = e.toString().toLowerCase();
      String pretty = 'Could not reset password. Check the code and try again.';
      if (msg.contains('invalid')) {
        pretty = 'That reset code is invalid. Request a new one.';
      } else if (msg.contains('expired')) {
        pretty = 'That reset link has expired. Request a new one.';
      } else if (msg.contains('8 characters') || msg.contains('at least 8')) {
        pretty = 'Password must be at least 8 characters with a letter and digit.';
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
          child: _done ? _SuccessView() : _form(context),
        ),
      ),
    );
  }

  Widget _form(BuildContext context) {
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
            'Paste the UID and Token from the reset email we sent you, then choose a new password.',
            style: TextStyle(color: AppColors.textSecondary, fontSize: 14),
          ),
          const SizedBox(height: 24),
          ErrorBanner(
              message: _error,
              onDismiss: () => setState(() => _error = null)),
          AppTextField(
            label: 'UID (from email)',
            hint: 'e.g. MQ',
            controller: _uidCtrl,
            prefixIcon: Icons.tag,
            validator: (v) => (v?.trim().isEmpty ?? true) ? 'Paste your UID' : null,
          ),
          const SizedBox(height: 16),
          AppTextField(
            label: 'Token (from email)',
            hint: 'e.g. cdh-a1b2c3...',
            controller: _tokenCtrl,
            prefixIcon: Icons.vpn_key_outlined,
            validator: (v) =>
                (v?.trim().isEmpty ?? true) ? 'Paste your reset token' : null,
          ),
          const SizedBox(height: 24),
          AppTextField(
            label: 'New password',
            controller: _pwCtrl,
            obscureText: _obscure,
            prefixIcon: Icons.lock_outline,
            suffixIcon: IconButton(
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
            validator: (v) => (v?.isEmpty ?? true) ? 'Confirm your password' : null,
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
