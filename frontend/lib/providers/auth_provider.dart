import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/models/user_model.dart';
import '../data/repositories/auth_repository.dart';
import '../data/services/push/push_service.dart';

class AuthState {
  final UserModel? user;
  final bool isLoading;
  final String? error;

  const AuthState({this.user, this.isLoading = false, this.error});

  bool get isAuthenticated => user != null;
  bool get isOnboarded => user?.onboardingCompleted ?? false;

  AuthState copyWith({UserModel? user, bool? isLoading, String? error, bool clearUser = false}) {
    return AuthState(
      user: clearUser ? null : (user ?? this.user),
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthRepository _repo = AuthRepository();

  AuthNotifier() : super(const AuthState(isLoading: true)) {
    _init();
  }

  /// Clear the last-seen error so dismissing the banner sticks.
  void clearError() {
    if (state.error != null) {
      state = state.copyWith(error: null);
    }
  }

  Future<void> _init() async {
    final loggedIn = await _repo.isLoggedIn();
    if (!loggedIn) {
      state = const AuthState();
      return;
    }

    // Restore from cache immediately so the app feels instant.
    final cached = await _repo.getCachedUser();
    if (cached != null) {
      state = AuthState(user: cached);
    }

    // Refresh profile from network in the background.
    try {
      final fresh = await _repo.getProfile();
      state = AuthState(user: fresh);
    } catch (_) {
      // Keep cached user if network fails — don't log out.
      if (cached == null) state = const AuthState();
    }
    // Register this device for push once we know we're authenticated.
    if (state.isAuthenticated) PushService.instance.syncToken();
  }

  Future<void> login(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final auth = await _repo.login(email, password);
      state = AuthState(user: auth.user);
      PushService.instance.syncToken();
    } catch (e) {
      state = state.copyWith(isLoading: false, error: _parseError(e));
    }
  }

  Future<void> register({
    required String email,
    required String username,
    required String firstName,
    required String lastName,
    required String password,
    required String passwordConfirm,
  }) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final auth = await _repo.register(
        email: email,
        username: username,
        firstName: firstName,
        lastName: lastName,
        password: password,
        passwordConfirm: passwordConfirm,
      );
      state = AuthState(user: auth.user);
      PushService.instance.syncToken();
    } catch (e) {
      state = state.copyWith(isLoading: false, error: _parseError(e));
    }
  }

  Future<void> googleSignIn(String idToken) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final auth = await _repo.googleSignIn(idToken);
      state = AuthState(user: auth.user);
      PushService.instance.syncToken();
    } catch (e) {
      state = state.copyWith(isLoading: false, error: _parseError(e));
    }
  }

  Future<void> updateProfile(Map<String, dynamic> data) async {
    try {
      final user = await _repo.updateProfile(data);
      state = state.copyWith(user: user);
    } catch (e) {
      state = state.copyWith(error: _parseError(e));
      rethrow;
    }
  }

  Future<void> completeOnboarding(Map<String, dynamic> data) async {
    try {
      final user = await _repo.completeOnboarding(data);
      state = AuthState(user: user);
    } catch (e) {
      state = state.copyWith(error: _parseError(e));
      rethrow;
    }
  }

  Future<void> logout() async {
    await _repo.logout();
    state = const AuthState();
  }

  String _parseError(dynamic e) {
    String _humanise(String raw) {
      // Translate the most common Django auth error strings into friendlier
      // wording. The backend keeps the original generic phrasing on purpose
      // (e.g. one message for "user doesn't exist" + "wrong password" to
      // avoid leaking account existence) — we just say it more humanly.
      final lower = raw.toLowerCase();
      if (lower.contains('invalid credentials')) {
        return 'Wrong email or password. Please check and try again.';
      }
      if (lower.contains('email') &&
          (lower.contains('already exists') || lower.contains('already in use'))) {
        return 'That email is already registered. Try signing in instead.';
      }
      if (lower.contains('username') && lower.contains('already exists')) {
        return 'That username is taken — pick another.';
      }
      if (lower.contains('too common') || lower.contains('common password')) {
        return 'That password is too easy to guess — pick something stronger.';
      }
      if (lower.contains('too similar')) {
        return 'Password is too similar to your name or email — make it more different.';
      }
      if (lower.contains('entirely numeric')) {
        return 'Password can\'t be all numbers. Add some letters too.';
      }
      if (lower.contains('at least one letter') &&
          lower.contains('at least one number') == false &&
          lower.contains('digit')) {
        return 'Password must include a letter AND a number.';
      }
      if (lower.contains('passwords do not match')) {
        return 'Passwords don\'t match. Please retype them.';
      }
      if (lower.contains('this field is required')) {
        return 'Please fill in every field.';
      }
      return raw;
    }

    if (e is DioException) {
      final data = e.response?.data;
      if (data is Map) {
        if (data['detail'] != null) return _humanise(data['detail'].toString());
        if (data['non_field_errors'] != null) {
          final v = data['non_field_errors'];
          final raw = v is List ? v.join(', ') : v.toString();
          return _humanise(raw);
        }
        // Field-level errors — collect all
        final msgs = <String>[];
        for (final entry in (data as Map<String, dynamic>).entries) {
          final v = entry.value;
          msgs.add(v is List ? v.join(', ') : v.toString());
        }
        if (msgs.isNotEmpty) return _humanise(msgs.join('\n'));
      }
      if (e.response?.statusCode == 401) {
        return 'Wrong email or password. Please check and try again.';
      }
      if (e.type == DioExceptionType.connectionTimeout ||
          e.type == DioExceptionType.receiveTimeout) {
        return 'Connection timed out. Check your network.';
      }
      if (e.type == DioExceptionType.connectionError) {
        return 'Cannot reach server. Check your connection.';
      }
    }
    return 'Something went wrong. Please try again.';
  }
}

final authStateProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) => AuthNotifier());
