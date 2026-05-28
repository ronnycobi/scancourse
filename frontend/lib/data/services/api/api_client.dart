import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../../core/constants/app_constants.dart';

class ApiClient {
  static ApiClient? _instance;
  late final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  ApiClient._() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConstants.baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 60),
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: _onRequest,
      onError: _onError,
    ));
  }

  static ApiClient get instance {
    _instance ??= ApiClient._();
    return _instance!;
  }

  Dio get dio => _dio;

  /// Endpoints that must NEVER receive a Bearer header. If a stale
  /// access token from a previous session lingered in secure storage,
  /// DRF's JWTAuthentication would reject the request with 401 before
  /// it ever reached the login/register view — making fresh logins
  /// fail on the first attempt and only succeed after the 401-driven
  /// token refresh ran. Strip auth on these paths so credentials are
  /// always validated cleanly.
  static const _unauthedPaths = <String>{
    '/auth/login/',
    '/auth/register/',
    '/auth/google/',
    '/auth/token/refresh/',
    '/auth/password/reset/',
    '/auth/password/reset/confirm/',
  };

  bool _isUnauthed(String path) {
    for (final p in _unauthedPaths) {
      if (path.endsWith(p)) return true;
    }
    return false;
  }

  Future<void> _onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    if (_isUnauthed(options.path)) {
      options.headers.remove('Authorization');
      handler.next(options);
      return;
    }
    final token = await _storage.read(key: AppConstants.accessTokenKey);
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  Future<void> _onError(DioException error, ErrorInterceptorHandler handler) async {
    // Never try to refresh-and-retry on auth endpoints — a 401 there
    // means the credentials are wrong, not that the session expired.
    final path = error.requestOptions.path;
    if (error.response?.statusCode == 401 && !_isUnauthed(path)) {
      final refreshed = await _refreshToken();
      if (refreshed) {
        final retryOptions = error.requestOptions;
        final token = await _storage.read(key: AppConstants.accessTokenKey);
        retryOptions.headers['Authorization'] = 'Bearer $token';
        try {
          final response = await _dio.fetch(retryOptions);
          handler.resolve(response);
          return;
        } catch (_) {}
      }
    }
    handler.next(error);
  }

  Future<bool> _refreshToken() async {
    final refresh = await _storage.read(key: AppConstants.refreshTokenKey);
    if (refresh == null) return false;
    try {
      final response =
          await _dio.post('/auth/token/refresh/', data: {'refresh': refresh});
      final newAccess = response.data['access'] as String?;
      // The backend has ROTATE_REFRESH_TOKENS + BLACKLIST_AFTER_ROTATION
      // enabled, so each refresh returns a BRAND NEW refresh token and
      // immediately blacklists the old one. We MUST persist the new
      // refresh token — otherwise the next refresh would reuse the old
      // (now-blacklisted) token, fail, and silently log the user out a
      // couple of hours after every login.
      final newRefresh = response.data['refresh'] as String?;
      if (newAccess != null) {
        await _storage.write(
            key: AppConstants.accessTokenKey, value: newAccess);
        if (newRefresh != null) {
          await _storage.write(
              key: AppConstants.refreshTokenKey, value: newRefresh);
        }
        return true;
      }
    } catch (_) {}
    return false;
  }

  Future<Response> get(String path, {Map<String, dynamic>? queryParams}) async {
    return _dio.get(path, queryParameters: queryParams);
  }

  Future<Response> post(String path, {dynamic data, Map<String, dynamic>? queryParams}) async {
    return _dio.post(path, data: data, queryParameters: queryParams);
  }

  Future<Response> patch(String path, {dynamic data}) async {
    return _dio.patch(path, data: data);
  }

  Future<Response> delete(String path) async {
    return _dio.delete(path);
  }

  Future<Response> upload(String path, FormData formData) async {
    // Override Content-Type so Dio can write the multipart boundary; the
    // default 'application/json' from BaseOptions would otherwise break
    // Django's multipart parser and return HTTP 400.
    return _dio.post(
      path,
      data: formData,
      options: Options(contentType: 'multipart/form-data'),
    );
  }
}
