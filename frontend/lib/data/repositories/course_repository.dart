import '../models/course_model.dart';
import '../services/api/api_client.dart';

class CourseRepository {
  final ApiClient _api = ApiClient.instance;

  Future<List<CourseModel>> getCourses({
    String? field,
    String? province,
    String? institutionType,
    int? minAps,
    int? maxAps,
    String? search,
  }) async {
    final response = await _api.get('/courses/', queryParams: {
      if (field != null) 'field': field,
      if (province != null) 'province': province,
      if (institutionType != null) 'institution_type': institutionType,
      if (minAps != null) 'min_aps': minAps,
      if (maxAps != null) 'max_aps': maxAps,
      if (search != null) 'search': search,
    });
    final results = (response.data['results'] ?? response.data) as List;
    return results.map((e) => CourseModel.fromJson(Map<String, dynamic>.from(e))).toList();
  }

  Future<CourseModel> getCourse(int id) async {
    final response = await _api.get('/courses/$id/');
    return CourseModel.fromJson(response.data);
  }

  Future<Map<String, dynamic>> getMatches({
    String? field,
    String? province,
    String? institutionType,
    String? level,
    String? category,
    String? search,
    bool includeNotQualified = false,
    int limit = 200,
  }) async {
    final response = await _api.get('/courses/match/', queryParams: {
      if (field != null) 'field': field,
      if (province != null) 'province': province,
      if (institutionType != null) 'institution_type': institutionType,
      if (level != null) 'level': level,
      if (category != null) 'category': category,
      if (search != null && search.isNotEmpty) 'search': search,
      if (includeNotQualified) 'include_not_qualified': 'true',
      'limit': limit.toString(),
    });
    return response.data as Map<String, dynamic>;
  }

  Future<List<Map<String, dynamic>>> getRecommendations({int limit = 20}) async {
    final response = await _api.get('/courses/recommend/', queryParams: {
      'limit': limit.toString(),
    });
    final results = (response.data['results'] ?? []) as List;
    return results.map((e) => Map<String, dynamic>.from(e)).toList();
  }

  Future<void> trackInteraction(int courseId, String kind) async {
    try {
      await _api.post('/courses/$courseId/interact/', data: {'kind': kind});
    } catch (_) {
      // Best-effort — don't surface interaction errors to the user.
    }
  }
}
