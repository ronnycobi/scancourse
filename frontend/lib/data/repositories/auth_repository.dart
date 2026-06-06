import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/user_model.dart';
import '../services/api/api_client.dart';
import '../../core/constants/app_constants.dart';

class AuthRepository {
  final ApiClient _api = ApiClient.instance;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  Future<AuthResponse> login(String email, String password) async {
    final response = await _api.post('/auth/login/', data: {
      'email': email,
      'password': password,
    });
    final auth = AuthResponse.fromJson(response.data);
    await _saveTokens(auth.access, auth.refresh);
    await _saveUser(auth.user);
    return auth;
  }

  Future<AuthResponse> register({
    required String email,
    required String username,
    required String firstName,
    required String lastName,
    required String password,
    required String passwordConfirm,
  }) async {
    final response = await _api.post('/auth/register/', data: {
      'email': email,
      'username': username,
      'first_name': firstName,
      'last_name': lastName,
      'password': password,
      'password_confirm': passwordConfirm,
    });
    final auth = AuthResponse.fromJson(response.data);
    await _saveTokens(auth.access, auth.refresh);
    await _saveUser(auth.user);
    return auth;
  }

  Future<AuthResponse> googleSignIn(String idToken) async {
    final response = await _api.post('/auth/google/', data: {'id_token': idToken});
    final auth = AuthResponse.fromJson(response.data);
    await _saveTokens(auth.access, auth.refresh);
    await _saveUser(auth.user);
    return auth;
  }

  Future<UserModel> getProfile() async {
    final response = await _api.get('/auth/profile/');
    final user = UserModel.fromJson(response.data);
    await _saveUser(user);
    return user;
  }

  Future<UserModel?> getCachedUser() async {
    final json = await _storage.read(key: AppConstants.userKey);
    if (json == null) return null;
    try {
      return UserModel.fromJson(Map<String, dynamic>.from(jsonDecode(json)));
    } catch (_) {
      return null;
    }
  }

  Future<UserModel> updateProfile(Map<String, dynamic> data) async {
    final response = await _api.patch('/auth/profile/', data: data);
    final user = UserModel.fromJson(response.data);
    await _saveUser(user);
    return user;
  }

  Future<UserModel> completeOnboarding(Map<String, dynamic> data) async {
    final response = await _api.patch('/auth/onboarding/', data: data);
    final user = UserModel.fromJson(response.data);
    await _saveUser(user);
    return user;
  }

  Future<void> logout() async {
    try {
      final refresh = await _storage.read(key: AppConstants.refreshTokenKey);
      if (refresh != null) {
        await _api.post('/auth/logout/', data: {'refresh': refresh});
      }
    } catch (_) {}
    await _storage.deleteAll();
  }

  Future<bool> isLoggedIn() async {
    final token = await _storage.read(key: AppConstants.accessTokenKey);
    return token != null;
  }

  Future<void> _saveTokens(String access, String refresh) async {
    await _storage.write(key: AppConstants.accessTokenKey, value: access);
    await _storage.write(key: AppConstants.refreshTokenKey, value: refresh);
  }

  Future<void> _saveUser(UserModel user) async {
    await _storage.write(key: AppConstants.userKey, value: jsonEncode(user.toJson()));
  }
}
