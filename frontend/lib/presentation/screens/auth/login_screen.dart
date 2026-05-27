import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_sign_in/google_sign_in.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/constants/app_constants.dart';
import '../../../providers/auth_provider.dart';
import '../../widgets/common/app_text_field.dart';
import '../../widgets/common/brand_header.dart';
import '../../widgets/common/error_banner.dart';
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
  bool _googleBusy = false;
  /// Local override — set when the Google flow itself fails (the global
  /// auth provider only tracks email/password errors). Cleared on next
  /// attempt or dismiss.
  String? _googleError;

  // Live field errors. Updated on every keystroke.
  String? _emailError;
  String? _passwordError;
  final _touched = <String>{};

  @override
  void initState() {
    super.initState();
    _emailCtrl.addListener(_liveEmail);
    _passwordCtrl.addListener(_livePassword);
  }

  void _liveEmail() {
    final v = _emailCtrl.text.trim();
    setState(() {
      _touched.add('email');
      if (v.isEmpty) {
        _emailError = null;
      } else if (!RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(v)) {
        _emailError = 'Not a valid email';
      } else {
        _emailError = null;
      }
    });
  }

  void _livePassword() {
    final v = _passwordCtrl.text;
    setState(() {
      _touched.add('password');
      if (v.isEmpty) {
        _passwordError = null;
      } else if (v.length < 6) {
        _passwordError = 'Password too short';
      } else {
        _passwordError = null;
      }
    });
  }

  bool get _canSubmit =>
      _emailCtrl.text.trim().isNotEmpty &&
      _passwordCtrl.text.isNotEmpty &&
      _emailError == null &&
      _passwordError == null;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    setState(() => _googleError = null);
    ref.read(authStateProvider.notifier).clearError();
    // Trigger live validation by "touching" both fields first
    _liveEmail();
    _livePassword();
    if (!_canSubmit) {
      setState(() {
        if (_emailCtrl.text.trim().isEmpty) {
          _emailError = 'Please enter your email';
        }
        if (_passwordCtrl.text.isEmpty) {
          _passwordError = 'Please enter your password';
        }
      });
      return;
    }
    await ref.read(authStateProvider.notifier).login(
      _emailCtrl.text.trim(),
      _passwordCtrl.text,
    );
    if (!mounted) return;
    final state = ref.read(authStateProvider);
    // No need to copy state.error into local state — the build() method
    // watches the provider directly and the ErrorBanner shows automatically.
    if (state.error == null && state.user != null) {
      context.go('/home');
    }
  }

  Future<void> _googleSignIn() async {
    setState(() {
      _googleBusy = true;
      _googleError = null;
    });
    ref.read(authStateProvider.notifier).clearError();
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
          _googleError =
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
          _googleError = state.error;
        });
      } else if (state.user != null) {
        context.go('/home');
      } else {
        setState(() => _googleBusy = false);
      }
    } catch (e) {
      setState(() {
        _googleBusy = false;
        _googleError = 'Could not sign in with Google. ${e.toString()}';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authStateProvider);
    final isLoading = authState.isLoading;
    // Show whichever error is current: the provider's (email/password
    // failures) or the local Google-flow error.
    final displayedError = _googleError ?? authState.error;

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
                const BrandHeader(),
                const SizedBox(height: 40),
                Text('Welcome back!',
                    style: Theme.of(context).textTheme.headlineLarge),
                const SizedBox(height: 8),
                Text('Sign in to plan your future',
                    style: Theme.of(context).textTheme.bodyMedium),
                const SizedBox(height: 24),

                // ── Inline error banner (watches the provider) ───────
                ErrorBanner(
                  message: displayedError,
                  onDismiss: () {
                    setState(() => _googleError = null);
                    ref.read(authStateProvider.notifier).clearError();
                  },
                ),

                AppTextField(
                  label: 'Email address',
                  hint: 'you@email.com',
                  controller: _emailCtrl,
                  keyboardType: TextInputType.emailAddress,
                  prefixIcon: Icons.email_outlined,
                  suffixIcon: (_touched.contains('email') &&
                          _emailError == null &&
                          _emailCtrl.text.trim().isNotEmpty)
                      ? const Padding(
                          padding: EdgeInsets.only(right: 12),
                          child: Icon(Icons.check_circle,
                              color: AppColors.eligible, size: 20),
                        )
                      : null,
                ),
                if (_emailError != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 4, left: 4),
                    child: Row(children: [
                      const Icon(Icons.error_outline,
                          size: 13, color: AppColors.error),
                      const SizedBox(width: 4),
                      Text(_emailError!,
                          style: const TextStyle(
                              fontSize: 12,
                              color: AppColors.error,
                              fontWeight: FontWeight.w500)),
                    ]),
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
                ),
                if (_passwordError != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 4, left: 4),
                    child: Row(children: [
                      const Icon(Icons.error_outline,
                          size: 13, color: AppColors.error),
                      const SizedBox(width: 4),
                      Text(_passwordError!,
                          style: const TextStyle(
                              fontSize: 12,
                              color: AppColors.error,
                              fontWeight: FontWeight.w500)),
                    ]),
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
