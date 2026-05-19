import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/services/api/api_client.dart';
import '../../widgets/common/app_text_field.dart';
import '../../widgets/common/loading_button.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailCtrl = TextEditingController();
  bool _sending = false;
  bool _sent = false;
  String? _error;

  @override
  void dispose() {
    _emailCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _sending = true;
      _error = null;
    });
    try {
      await ApiClient.instance.post(
        '/auth/password-reset/',
        data: {'email': _emailCtrl.text.trim()},
      );
      if (mounted) setState(() => _sent = true);
    } catch (e) {
      if (mounted) setState(() => _error = 'Could not send reset email. Try again.');
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Forgot Password')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: _sent
            ? Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.mark_email_read_outlined,
                      size: 72, color: AppColors.secondary),
                  const SizedBox(height: 24),
                  Text('Check your email!',
                      style: Theme.of(context).textTheme.headlineMedium),
                  const SizedBox(height: 12),
                  Text(
                    'If a Scancourse account exists for ${_emailCtrl.text}, we\'ve sent a reset link.',
                    style: Theme.of(context).textTheme.bodyMedium,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 24),
                  OutlinedButton(
                    onPressed: () => Navigator.of(context).pop(),
                    child: const Text('Back to Login'),
                  ),
                ],
              )
            : Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 24),
                    Text('Reset your password',
                        style: Theme.of(context).textTheme.headlineMedium),
                    const SizedBox(height: 8),
                    Text(
                      'Enter your email address and we\'ll send you a link to reset your password.',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                    const SizedBox(height: 32),
                    AppTextField(
                      label: 'Email address',
                      hint: 'you@email.com',
                      controller: _emailCtrl,
                      keyboardType: TextInputType.emailAddress,
                      prefixIcon: Icons.email_outlined,
                      validator: (v) => v != null && v.contains('@')
                          ? null
                          : 'Enter a valid email',
                    ),
                    if (_error != null) ...[
                      const SizedBox(height: 12),
                      Text(_error!,
                          style: const TextStyle(
                              color: AppColors.error, fontSize: 13)),
                    ],
                    const SizedBox(height: 24),
                    LoadingButton(
                      label: 'Send Reset Link',
                      isLoading: _sending,
                      onPressed: _submit,
                    ),
                  ],
                ),
              ),
      ),
    );
  }
}
