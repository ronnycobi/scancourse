import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../providers/auth_provider.dart';
import '../../widgets/common/app_text_field.dart';
import '../../widgets/common/brand_header.dart';
import '../../widgets/common/error_banner.dart';
import '../../widgets/common/loading_button.dart';
import '../../widgets/common/password_strength_meter.dart';

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

  // Live error state, one per field. Updated on every keystroke.
  String? _firstNameError;
  String? _lastNameError;
  String? _emailError;
  String? _usernameError;
  String? _passwordError;
  String? _confirmError;
  // True after the user has interacted with a field once — prevents
  // showing "required" errors before they've even typed.
  final _touched = <String>{};

  @override
  void initState() {
    super.initState();
    _firstNameCtrl.addListener(() => _liveCheck('first'));
    _lastNameCtrl.addListener(() => _liveCheck('last'));
    _emailCtrl.addListener(() => _liveCheck('email'));
    _usernameCtrl.addListener(() => _liveCheck('username'));
    _passwordCtrl.addListener(() => _liveCheck('password'));
    _confirmCtrl.addListener(() => _liveCheck('confirm'));
  }

  @override
  void dispose() {
    for (final c in [
      _firstNameCtrl,
      _lastNameCtrl,
      _emailCtrl,
      _usernameCtrl,
      _passwordCtrl,
      _confirmCtrl
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  // ── Live validators (called on every keystroke) ────────────────────

  String? _validateName(String v) {
    if (v.isEmpty) return null; // don't shout while empty
    if (RegExp(r'\d').hasMatch(v)) {
      return 'No numbers allowed in names';
    }
    if (!RegExp(r"^[A-Za-zÀ-ɏ'\- ]+$").hasMatch(v)) {
      return 'Only letters, spaces, hyphens and apostrophes';
    }
    if (v.length < 2) return 'At least 2 letters';
    return null;
  }

  String? _validateEmail(String v) {
    if (v.isEmpty) return null;
    if (!v.contains('@') || !v.contains('.')) return 'Not a valid email';
    if (!RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(v)) {
      return 'Not a valid email';
    }
    return null;
  }

  String? _validateUsername(String v) {
    if (v.isEmpty) return null;
    if (v.length < 3) return 'At least 3 characters';
    if (!RegExp(r'^[A-Za-z0-9_.]+$').hasMatch(v)) {
      return 'Letters, numbers, _ and . only';
    }
    return null;
  }

  String? _validatePassword(String v) {
    if (v.isEmpty) return null;
    if (v.length < 8) return 'Must be at least 8 characters';
    if (!RegExp(r'[A-Za-z]').hasMatch(v)) {
      return 'Must include at least one letter';
    }
    if (!RegExp(r'\d').hasMatch(v)) return 'Must include at least one digit';
    if (RegExp(r'^\d+$').hasMatch(v)) return 'Can\'t be all numbers';
    return null;
  }

  String? _validateConfirm(String v) {
    if (v.isEmpty) return null;
    if (v != _passwordCtrl.text) return 'Passwords don\'t match';
    return null;
  }

  void _liveCheck(String field) {
    setState(() {
      _touched.add(field);
      switch (field) {
        case 'first':
          _firstNameError = _validateName(_firstNameCtrl.text.trim());
          break;
        case 'last':
          _lastNameError = _validateName(_lastNameCtrl.text.trim());
          break;
        case 'email':
          _emailError = _validateEmail(_emailCtrl.text.trim());
          break;
        case 'username':
          _usernameError = _validateUsername(_usernameCtrl.text.trim());
          break;
        case 'password':
          _passwordError = _validatePassword(_passwordCtrl.text);
          // confirm also depends on password
          _confirmError = _validateConfirm(_confirmCtrl.text);
          break;
        case 'confirm':
          _confirmError = _validateConfirm(_confirmCtrl.text);
          break;
      }
    });
  }

  /// All fields must be non-empty AND pass live validation.
  bool get _isFormValid {
    if (_firstNameCtrl.text.trim().isEmpty) return false;
    if (_lastNameCtrl.text.trim().isEmpty) return false;
    if (_emailCtrl.text.trim().isEmpty) return false;
    if (_usernameCtrl.text.trim().isEmpty) return false;
    if (_passwordCtrl.text.isEmpty) return false;
    if (_confirmCtrl.text.isEmpty) return false;
    return _firstNameError == null &&
        _lastNameError == null &&
        _emailError == null &&
        _usernameError == null &&
        _passwordError == null &&
        _confirmError == null;
  }

  Future<void> _register() async {
    ref.read(authStateProvider.notifier).clearError();
    // Force a final touch of every field so any missing-required errors
    // become visible before we send.
    setState(() {
      _firstNameError = _validateName(_firstNameCtrl.text.trim()) ??
          (_firstNameCtrl.text.trim().isEmpty ? 'Required' : null);
      _lastNameError = _validateName(_lastNameCtrl.text.trim()) ??
          (_lastNameCtrl.text.trim().isEmpty ? 'Required' : null);
      _emailError = _validateEmail(_emailCtrl.text.trim()) ??
          (_emailCtrl.text.trim().isEmpty ? 'Required' : null);
      _usernameError = _validateUsername(_usernameCtrl.text.trim()) ??
          (_usernameCtrl.text.trim().isEmpty ? 'Required' : null);
      _passwordError = _validatePassword(_passwordCtrl.text) ??
          (_passwordCtrl.text.isEmpty ? 'Required' : null);
      _confirmError = _validateConfirm(_confirmCtrl.text) ??
          (_confirmCtrl.text.isEmpty ? 'Required' : null);
    });
    if (!_isFormValid) return;

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
                Text('Create account',
                    style: Theme.of(context).textTheme.headlineLarge),
                const SizedBox(height: 8),
                Text(
                    'Join thousands of South African students',
                    style: Theme.of(context).textTheme.bodyMedium),
                const SizedBox(height: 24),
                ErrorBanner(
                  message: authState.error,
                  onDismiss: () =>
                      ref.read(authStateProvider.notifier).clearError(),
                ),
                const SizedBox(height: 8),

                // First name + Last name now stack vertically, full-width
                // each — matches the email/password fields below for a
                // cleaner, more readable form on small SA phone screens.
                _LiveField(
                  label: 'First name',
                  hint: 'Thandi',
                  controller: _firstNameCtrl,
                  prefixIcon: Icons.person_outline,
                  errorText: _firstNameError,
                  isValid: _touched.contains('first') &&
                      _firstNameError == null &&
                      _firstNameCtrl.text.trim().isNotEmpty,
                ),
                const SizedBox(height: 16),
                _LiveField(
                  label: 'Last name',
                  hint: 'Mokoena',
                  controller: _lastNameCtrl,
                  prefixIcon: Icons.person_outline,
                  errorText: _lastNameError,
                  isValid: _touched.contains('last') &&
                      _lastNameError == null &&
                      _lastNameCtrl.text.trim().isNotEmpty,
                ),
                const SizedBox(height: 16),
                _LiveField(
                  label: 'Email address',
                  hint: 'you@email.com',
                  controller: _emailCtrl,
                  keyboardType: TextInputType.emailAddress,
                  prefixIcon: Icons.email_outlined,
                  errorText: _emailError,
                  isValid: _touched.contains('email') &&
                      _emailError == null &&
                      _emailCtrl.text.trim().isNotEmpty,
                ),
                const SizedBox(height: 16),
                _LiveField(
                  label: 'Username',
                  hint: 'Choose a username',
                  controller: _usernameCtrl,
                  prefixIcon: Icons.alternate_email,
                  errorText: _usernameError,
                  isValid: _touched.contains('username') &&
                      _usernameError == null &&
                      _usernameCtrl.text.trim().isNotEmpty,
                ),
                const SizedBox(height: 16),
                _LiveField(
                  label: 'Password',
                  hint: 'At least 8 characters, with a number',
                  controller: _passwordCtrl,
                  obscureText: _obscure,
                  prefixIcon: Icons.lock_outline,
                  suffixIcon: IconButton(
                    icon: Icon(_obscure
                        ? Icons.visibility_outlined
                        : Icons.visibility_off_outlined),
                    onPressed: () => setState(() => _obscure = !_obscure),
                  ),
                  errorText: _passwordError,
                  isValid: _touched.contains('password') &&
                      _passwordError == null &&
                      _passwordCtrl.text.isNotEmpty,
                ),
                // Live strength meter + checklist
                PasswordStrengthMeter(password: _passwordCtrl.text),
                PasswordChecklist(
                  password: _passwordCtrl.text,
                  username: _usernameCtrl.text,
                  email: _emailCtrl.text,
                ),
                const SizedBox(height: 16),
                _LiveField(
                  label: 'Confirm password',
                  controller: _confirmCtrl,
                  obscureText: _obscure,
                  prefixIcon: Icons.lock_outline,
                  errorText: _confirmError,
                  isValid: _touched.contains('confirm') &&
                      _confirmError == null &&
                      _confirmCtrl.text.isNotEmpty,
                ),
                const SizedBox(height: 24),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: Wrap(
                    alignment: WrapAlignment.center,
                    children: [
                      const Text(
                          'By creating an account you agree to our ',
                          style: TextStyle(
                              fontSize: 12,
                              color: AppColors.textSecondary)),
                      GestureDetector(
                        onTap: () => context.push('/legal/terms'),
                        child: const Text('Terms',
                            style: TextStyle(
                                fontSize: 12,
                                color: AppColors.primary,
                                fontWeight: FontWeight.w600)),
                      ),
                      const Text(' and ',
                          style: TextStyle(
                              fontSize: 12,
                              color: AppColors.textSecondary)),
                      GestureDetector(
                        onTap: () => context.push('/legal/privacy'),
                        child: const Text('Privacy Policy',
                            style: TextStyle(
                                fontSize: 12,
                                color: AppColors.primary,
                                fontWeight: FontWeight.w600)),
                      ),
                      const Text('.',
                          style: TextStyle(
                              fontSize: 12,
                              color: AppColors.textSecondary)),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                LoadingButton(
                  label: 'Create Account',
                  isLoading: isLoading,
                  onPressed: _isFormValid ? _register : _register,
                ),
                const SizedBox(height: 20),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text('Already have an account? ',
                        style: Theme.of(context).textTheme.bodyMedium),
                    GestureDetector(
                      onTap: () => context.go('/login'),
                      child: Text('Sign in',
                          style: Theme.of(context)
                              .textTheme
                              .bodyMedium
                              ?.copyWith(
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

/// A wrapper around AppTextField that adds a live error message AND
/// a green tick when the field is valid. Updates as the user types.
class _LiveField extends StatelessWidget {
  final String label;
  final String? hint;
  final TextEditingController controller;
  final IconData? prefixIcon;
  final Widget? suffixIcon;
  final bool obscureText;
  final TextInputType? keyboardType;
  final String? errorText;
  final bool isValid;

  const _LiveField({
    required this.label,
    this.hint,
    required this.controller,
    this.prefixIcon,
    this.suffixIcon,
    this.obscureText = false,
    this.keyboardType,
    this.errorText,
    this.isValid = false,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AppTextField(
          label: label,
          hint: hint,
          controller: controller,
          obscureText: obscureText,
          keyboardType: keyboardType,
          prefixIcon: prefixIcon,
          suffixIcon: isValid
              ? const Padding(
                  padding: EdgeInsets.only(right: 12),
                  child: Icon(Icons.check_circle,
                      color: AppColors.eligible, size: 20),
                )
              : suffixIcon,
        ),
        if (errorText != null && errorText!.isNotEmpty)
          AnimatedSize(
            duration: const Duration(milliseconds: 180),
            curve: Curves.easeOut,
            alignment: Alignment.topLeft,
            child: Padding(
              padding: const EdgeInsets.only(top: 4, left: 4),
              child: Row(
                children: [
                  const Icon(Icons.error_outline,
                      size: 13, color: AppColors.error),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      errorText!,
                      style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.error,
                          fontWeight: FontWeight.w500),
                    ),
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }
}
