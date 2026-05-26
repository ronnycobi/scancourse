import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../providers/auth_provider.dart';
import '../../widgets/common/app_text_field.dart';
import '../../widgets/common/brand_header.dart';
import '../../widgets/common/error_banner.dart';
import '../../widgets/common/loading_button.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _firstNameCtrl = TextEditingController();
  final _lastNameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _usernameCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  final _confirmCtrl = TextEditingController();
  bool _obscure = true;

  @override
  void dispose() {
    for (final c in [_firstNameCtrl, _lastNameCtrl, _emailCtrl, _usernameCtrl, _passwordCtrl, _confirmCtrl]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _register() async {
    ref.read(authStateProvider.notifier).clearError();
    if (!_formKey.currentState!.validate()) return;
    await ref.read(authStateProvider.notifier).register(
      email: _emailCtrl.text.trim(),
      username: _usernameCtrl.text.trim(),
      firstName: _firstNameCtrl.text.trim(),
      lastName: _lastNameCtrl.text.trim(),
      password: _passwordCtrl.text,
      passwordConfirm: _confirmCtrl.text,
    );
    if (!mounted) return;
    final state = ref.read(authStateProvider);
    // No snackbar — the build() method watches the provider error and the
    // ErrorBanner renders automatically when something goes wrong.
    if (state.error == null && state.user != null) {
      context.go('/onboarding');
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authStateProvider);
    final isLoading = authState.isLoading;

    return Scaffold(
      appBar: AppBar(leading: const BackButton()),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const BrandHeader(),
                const SizedBox(height: 28),
                Text('Create account', style: Theme.of(context).textTheme.headlineLarge),
                const SizedBox(height: 8),
                Text('Join thousands of South African students', style: Theme.of(context).textTheme.bodyMedium),
                const SizedBox(height: 24),
                ErrorBanner(
                  message: authState.error,
                  onDismiss: () =>
                      ref.read(authStateProvider.notifier).clearError(),
                ),
                const SizedBox(height: 8),
                Row(children: [
                  Expanded(
                    child: AppTextField(
                      label: 'First name',
                      controller: _firstNameCtrl,
                      validator: (v) => v != null && v.isNotEmpty ? null : 'Required',
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: AppTextField(
                      label: 'Last name',
                      controller: _lastNameCtrl,
                      validator: (v) => v != null && v.isNotEmpty ? null : 'Required',
                    ),
                  ),
                ]),
                const SizedBox(height: 16),
                AppTextField(
                  label: 'Email address',
                  hint: 'you@email.com',
                  controller: _emailCtrl,
                  keyboardType: TextInputType.emailAddress,
                  prefixIcon: Icons.email_outlined,
                  validator: (v) => v != null && v.contains('@') ? null : 'Enter a valid email',
                ),
                const SizedBox(height: 16),
                AppTextField(
                  label: 'Username',
                  hint: 'Choose a username',
                  controller: _usernameCtrl,
                  prefixIcon: Icons.alternate_email,
                  validator: (v) => v != null && v.length >= 3 ? null : 'Minimum 3 characters',
                ),
                const SizedBox(height: 16),
                AppTextField(
                  label: 'Password',
                  controller: _passwordCtrl,
                  obscureText: _obscure,
                  prefixIcon: Icons.lock_outline,
                  suffixIcon: IconButton(
                    icon: Icon(_obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                    onPressed: () => setState(() => _obscure = !_obscure),
                  ),
                  validator: (v) => v != null && v.length >= 8 ? null : 'Minimum 8 characters',
                ),
                const SizedBox(height: 16),
                AppTextField(
                  label: 'Confirm password',
                  controller: _confirmCtrl,
                  obscureText: _obscure,
                  prefixIcon: Icons.lock_outline,
                  validator: (v) => v == _passwordCtrl.text ? null : 'Passwords do not match',
                ),
                const SizedBox(height: 24),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: Wrap(
                    alignment: WrapAlignment.center,
                    children: [
                      const Text('By creating an account you agree to our ',
                          style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                      GestureDetector(
                        onTap: () => context.push('/legal/terms'),
                        child: const Text('Terms',
                            style: TextStyle(
                                fontSize: 12,
                                color: AppColors.primary,
                                fontWeight: FontWeight.w600)),
                      ),
                      const Text(' and ',
                          style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                      GestureDetector(
                        onTap: () => context.push('/legal/privacy'),
                        child: const Text('Privacy Policy',
                            style: TextStyle(
                                fontSize: 12,
                                color: AppColors.primary,
                                fontWeight: FontWeight.w600)),
                      ),
                      const Text('.', style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                LoadingButton(
                  label: 'Create Account',
                  isLoading: isLoading,
                  onPressed: _register,
                ),
                const SizedBox(height: 20),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text('Already have an account? ', style: Theme.of(context).textTheme.bodyMedium),
                    GestureDetector(
                      onTap: () => context.go('/login'),
                      child: Text('Sign in',
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppColors.primary,
                            fontWeight: FontWeight.w600,
                          )),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
