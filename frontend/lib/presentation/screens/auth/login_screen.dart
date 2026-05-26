import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_sign_in/google_sign_in.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/constants/app_constants.dart';
import '../../../providers/auth_provider.dart';
import '../../widgets/common/app_text_field.dart';
import '../../widgets/common/loading_button.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  bool _obscurePassword = true;

  /// Locally-held error so we can show it INLINE (red banner above the form)
  /// instead of relying on a snackbar that flashes for 2 seconds at the
  /// bottom of the screen where the keyboard usually hides it.
  String? _inlineError;
  bool _googleBusy = false;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    setState(() => _inlineError = null);
    if (!_formKey.currentState!.validate()) return;
    await ref.read(authStateProvider.notifier).login(
      _emailCtrl.text.trim(),
      _passwordCtrl.text,
    );
    if (!mounted) return;
    final state = ref.read(authStateProvider);
    if (state.error != null) {
      setState(() => _inlineError = state.error);
    } else if (state.user != null) {
      context.go('/home');
    }
  }

  Future<void> _googleSignIn() async {
    setState(() {
      _googleBusy = true;
      _inlineError = null;
    });
    try {
      // serverClientId is the Web OAuth client ID from Google Cloud Console.
      // Required so we get an idToken the Django backend can verify.
      // If it's empty, the call still works but no idToken is returned →
      // we surface a clear error message.
      final google = GoogleSignIn(
        scopes: ['email', 'profile', 'openid'],
        serverClientId: AppConstants.googleServerClientId.isNotEmpty
            ? AppConstants.googleServerClientId
            : null,
      );
      final account = await google.signIn();
      if (account == null) {
        // User cancelled the chooser
        setState(() => _googleBusy = false);
        return;
      }
      final auth = await account.authentication;
      final idToken = auth.idToken;
      if (idToken == null || idToken.isEmpty) {
        setState(() {
          _googleBusy = false;
          _inlineError =
              'Google sign-in is not fully configured yet. Please use email + password.';
        });
        await google.signOut();
        return;
      }
      await ref.read(authStateProvider.notifier).googleSignIn(idToken);
      if (!mounted) return;
      final state = ref.read(authStateProvider);
      if (state.error != null) {
        setState(() {
          _googleBusy = false;
          _inlineError = state.error;
        });
      } else if (state.user != null) {
        context.go('/home');
      } else {
        setState(() => _googleBusy = false);
      }
    } catch (e) {
      setState(() {
        _googleBusy = false;
        _inlineError = 'Could not sign in with Google. ${e.toString()}';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = ref.watch(authStateProvider).isLoading;

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 40),
                // ── Brand row: real logo + wordmark ──────────────────
                Row(
                  children: [
                    ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Image.asset(
                        'assets/icons/scancourse-logo.png',
                        width: 48,
                        height: 48,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => Container(
                          width: 48,
                          height: 48,
                          decoration: BoxDecoration(
                            color: AppColors.primaryLight,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Icon(Icons.document_scanner_rounded,
                              color: AppColors.primary, size: 28),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Text(
                      AppConstants.appName,
                      style: Theme.of(context)
                          .textTheme
                          .headlineLarge
                          ?.copyWith(color: AppColors.primary),
                    ),
                  ],
                ),
                const SizedBox(height: 40),
                Text('Welcome back!',
                    style: Theme.of(context).textTheme.headlineLarge),
                const SizedBox(height: 8),
                Text('Sign in to plan your future',
                    style: Theme.of(context).textTheme.bodyMedium),
                const SizedBox(height: 24),

                // ── Inline error banner ─────────────────────────────
                if (_inlineError != null)
                  Container(
                    margin: const EdgeInsets.only(bottom: 16),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.errorLight,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                          color: AppColors.error.withOpacity(0.4)),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.error_outline,
                            color: AppColors.error, size: 18),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            _inlineError!,
                            style: const TextStyle(
                                color: AppColors.error,
                                fontSize: 13,
                                fontWeight: FontWeight.w500),
                          ),
                        ),
                        GestureDetector(
                          onTap: () => setState(() => _inlineError = null),
                          child: const Icon(Icons.close,
                              color: AppColors.error, size: 16),
                        ),
                      ],
                    ),
                  ),

                AppTextField(
                  label: 'Email address',
                  hint: 'you@email.com',
                  controller: _emailCtrl,
                  keyboardType: TextInputType.emailAddress,
                  prefixIcon: Icons.email_outlined,
                  validator: (v) {
                    final s = v?.trim() ?? '';
                    if (s.isEmpty) return 'Please enter your email';
                    if (!s.contains('@') || !s.contains('.')) {
                      return 'Enter a valid email address';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                AppTextField(
                  label: 'Password',
                  hint: 'Your password',
                  controller: _passwordCtrl,
                  obscureText: _obscurePassword,
                  prefixIcon: Icons.lock_outline,
                  suffixIcon: IconButton(
                    icon: Icon(_obscurePassword
                        ? Icons.visibility_outlined
                        : Icons.visibility_off_outlined),
                    onPressed: () =>
                        setState(() => _obscurePassword = !_obscurePassword),
                  ),
                  validator: (v) {
                    if (v == null || v.isEmpty) return 'Please enter your password';
                    if (v.length < 6) return 'Password is too short';
                    return null;
                  },
                ),
                const SizedBox(height: 12),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton(
                    onPressed: () => context.push('/forgot-password'),
                    child: const Text('Forgot password?'),
                  ),
                ),
                const SizedBox(height: 24),
                LoadingButton(
                  label: 'Sign In',
                  isLoading: isLoading,
                  onPressed: _login,
                ),
                // Google sign-in section is only shown when the Web OAuth
                // client ID has been provided at build time via
                // --dart-define=GOOGLE_SERVER_CLIENT_ID=...
                // Hiding it until then avoids confusing users with a button
                // that can't complete the flow.
                if (AppConstants.googleServerClientId.isNotEmpty) ...[
                  const SizedBox(height: 20),
                  Row(
                    children: [
                      const Expanded(child: Divider()),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        child: Text('or',
                            style: Theme.of(context).textTheme.bodySmall),
                      ),
                      const Expanded(child: Divider()),
                    ],
                  ),
                  const SizedBox(height: 20),
                  OutlinedButton.icon(
                    onPressed: _googleBusy ? null : _googleSignIn,
                    icon: _googleBusy
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const _GoogleGlyph(),
                    label: Text(_googleBusy
                        ? 'Signing in…'
                        : 'Continue with Google'),
                    style: OutlinedButton.styleFrom(
                      minimumSize: const Size(double.infinity, 48),
                      side: const BorderSide(color: AppColors.border),
                    ),
                  ),
                ],
                const SizedBox(height: 32),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text("Don't have an account? ",
                        style: Theme.of(context).textTheme.bodyMedium),
                    GestureDetector(
                      onTap: () => context.go('/register'),
                      child: Text('Sign up',
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

/// Small Google "G" multicolour glyph drawn with vector text so we don't
/// have to ship a logo asset.
class _GoogleGlyph extends StatelessWidget {
  const _GoogleGlyph();
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 20,
      height: 20,
      child: ShaderMask(
        blendMode: BlendMode.srcIn,
        shaderCallback: (rect) => const LinearGradient(
          colors: [
            Color(0xFF4285F4), // blue
            Color(0xFF34A853), // green
            Color(0xFFFBBC05), // yellow
            Color(0xFFEA4335), // red
          ],
          stops: [0.0, 0.33, 0.66, 1.0],
        ).createShader(rect),
        child: const Center(
          child: Text(
            'G',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w900,
              color: Colors.white,
              height: 1.0,
            ),
          ),
        ),
      ),
    );
  }
}
