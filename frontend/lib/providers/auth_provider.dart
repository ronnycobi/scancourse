import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/models/user_model.dart';
import '../data/repositories/auth_repository.dart';

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
  }

  Future<void> login(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final auth = await _repo.login(email, password);
      state = AuthState(user: auth.user);
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
    } catch (e) {
      state = state.copyWith(isLoading: false, error: _parseError(e));
    }
  }

  Future<void> googleSignIn(String idToken) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final auth = await _repo.googleSignIn(idToken);
      state = AuthState(user: auth.user);
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
      // Friendlier wording for the most common login failure. The backend
      // intentionally uses one generic message for both "user doesn't
      // exist" and "wrong password" so we don't leak which emails are
      // registered — keep that, but say it in plain English.
      final lower = raw.toLowerCase();
      if (lower.contains('invalid credentials')) {
        return 'Wrong email or password. Please check and try again.';
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
