import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/services/api/api_client.dart';
import '../../widgets/common/app_text_field.dart';
import '../../widgets/common/error_banner.dart';
import '../../widgets/common/loading_button.dart';

/// Authenticated password change. User must enter their current password,
/// then the new password (twice). Hits POST /auth/change-password/ which
/// only succeeds if the current password is correct.
class ChangePasswordScreen extends StatefulWidget {
  const ChangePasswordScreen({super.key});

  @override
  State<ChangePasswordScreen> createState() => _ChangePasswordScreenState();
}

class _ChangePasswordScreenState extends State<ChangePasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _currentCtrl = TextEditingController();
  final _newCtrl = TextEditingController();
  final _confirmCtrl = TextEditingController();

  bool _busy = false;
  bool _done = false;
  bool _obscureCurrent = true;
  bool _obscureNew = true;
  String? _error;

  @override
  void dispose() {
    _currentCtrl.dispose();
    _newCtrl.dispose();
    _confirmCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() => _error = null);
    if (!_formKey.currentState!.validate()) return;
    setState(() => _busy = true);
    try {
      await ApiClient.instance.post(
        '/auth/change-password/',
        data: {
          'current_password': _currentCtrl.text,
          'new_password': _newCtrl.text,
        },
      );
      if (mounted) setState(() => _done = true);
    } catch (e) {
      final msg = e.toString().toLowerCase();
      String pretty;
      if (msg.contains('current password is incorrect')) {
        pretty = 'Your current password is wrong. Please try again.';
      } else if (msg.contains('must be different')) {
        pretty = 'Your new password must be different from the current one.';
      } else if (msg.contains('too common')) {
        pretty = 'That password is too easy to guess — pick something stronger.';
      } else if (msg.contains('entirely numeric')) {
        pretty = 'Password can\'t be all numbers. Add some letters too.';
      } else if (msg.contains('too similar')) {
        pretty = 'Password is too similar to your name or email — make it more different.';
      } else if (msg.contains('letter and')) {
        pretty = 'Password must include a letter AND a number.';
      } else {
        pretty = 'Could not change password. Please try again.';
      }
      if (mounted) setState(() => _error = pretty);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Change Password'),
        leading: BackButton(onPressed: () => context.pop()),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: _done ? _successView(context) : _formView(context),
        ),
      ),
    );
  }

  Widget _formView(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.primaryLight,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.shield_outlined,
                    color: AppColors.primary, size: 22),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'For your security, please enter your current password before choosing a new one.',
                    style: TextStyle(
                      fontSize: 13,
                      color: AppColors.primary.withOpacity(0.85),
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          ErrorBanner(
            message: _error,
            onDismiss: () => setState(() => _error = null),
          ),
          AppTextField(
            label: 'Current password',
            controller: _currentCtrl,
            obscureText: _obscureCurrent,
            prefixIcon: Icons.lock_outline,
            suffixIcon: IconButton(
              icon: Icon(_obscureCurrent
                  ? Icons.visibility_outlined
                  : Icons.visibility_off_outlined),
              onPressed: () =>
                  setState(() => _obscureCurrent = !_obscureCurrent),
            ),
            validator: (v) =>
                (v?.isEmpty ?? true) ? 'Enter your current password' : null,
          ),
          const SizedBox(height: 20),
          AppTextField(
            label: 'New password',
            hint: 'At least 8 characters, with a number',
            controller: _newCtrl,
            obscureText: _obscureNew,
            prefixIcon: Icons.vpn_key_outlined,
            suffixIcon: IconButton(
              icon: Icon(_obscureNew
                  ? Icons.visibility_outlined
                  : Icons.visibility_off_outlined),
              onPressed: () => setState(() => _obscureNew = !_obscureNew),
            ),
            validator: (v) {
              if (v == null || v.isEmpty) return 'Choose a new password';
              if (v.length < 8) return 'At least 8 characters';
              if (!RegExp(r'[A-Za-z]').hasMatch(v) ||
                  !RegExp(r'\d').hasMatch(v)) {
                return 'Must include a letter AND a digit';
              }
              if (v == _currentCtrl.text) {
                return 'New password must be different';
              }
              return null;
            },
          ),
          const SizedBox(height: 16),
          AppTextField(
            label: 'Confirm new password',
            controller: _confirmCtrl,
            obscureText: _obscureNew,
            prefixIcon: Icons.vpn_key_outlined,
            validator: (v) {
              if (v == null || v.isEmpty) return 'Confirm your new password';
              if (v != _newCtrl.text) return 'Passwords do not match';
              return null;
            },
          ),
          const SizedBox(height: 24),
          LoadingButton(
            label: 'Update Password',
            isLoading: _busy,
            onPressed: _submit,
          ),
          const SizedBox(height: 12),
          Center(
            child: TextButton(
              onPressed: () => context.pop(),
              child: const Text('Cancel'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _successView(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 40),
      child: Column(
        children: [
          const Icon(Icons.check_circle, size: 80, color: AppColors.eligible),
          const SizedBox(height: 20),
          Text('Password updated',
              style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 8),
          const Text(
            'Your password has been changed successfully.',
            style: TextStyle(color: AppColors.textSecondary),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 32),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => context.pop(),
              child: const Text('Done'),
            ),
          ),
        ],
      ),
    );
  }
}
