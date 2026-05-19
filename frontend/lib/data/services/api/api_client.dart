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

  Future<void> _onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _storage.read(key: AppConstants.accessTokenKey);
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  Future<void> _onError(DioException error, ErrorInterceptorHandler handler) async {
    if (error.response?.statusCode == 401) {
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
      final response = await _dio.post('/auth/token/refresh/', data: {'refresh': refresh});
      final newAccess = response.data['access'] as String?;
      if (newAccess != null) {
        await _storage.write(key: AppConstants.accessTokenKey, value: newAccess);
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
