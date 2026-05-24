import 'dart:io';
import 'package:dio/dio.dart';
import '../models/aps_model.dart';
import '../services/api/api_client.dart';

class OcrRepository {
  final ApiClient _api = ApiClient.instance;

  Future<ReportModel> uploadReport(File file) async {
    final ext = file.path.split('.').last.toLowerCase();
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(file.path, filename: 'report.$ext'),
    });
    final response = await _api.upload('/ocr/upload/', formData);
    return ReportModel.fromJson(response.data);
  }

  Future<ReportModel> getReport(int id) async {
    final response = await _api.get('/ocr/reports/$id/');
    return ReportModel.fromJson(response.data);
  }

  Future<List<ReportModel>> getReports() async {
    final response = await _api.get('/ocr/reports/');
    final results = (response.data['results'] ?? response.data) as List;
    return results.map((e) => ReportModel.fromJson(Map<String, dynamic>.from(e))).toList();
  }

  Future<ReportModel> verifySubjects(int reportId, List<Map<String, dynamic>> subjects) async {
    final response = await _api.patch('/ocr/reports/$reportId/verify/', data: {'subjects': subjects});
    return ReportModel.fromJson(response.data);
  }

  Future<ApsResult> submitManualEntry(List<Map<String, dynamic>> subjects) async {
    final response = await _api.post('/ocr/manual/', data: {'subjects': subjects});
    return ApsResult.fromJson(response.data);
  }

  Future<ApsResult?> getLatestAps() async {
    final response = await _api.get('/ocr/aps/');
    final data = response.data as Map<String, dynamic>;
    if (data['total_aps'] == 0) return null;
    return ApsResult.fromJson(data);
  }

  /// AI quality check on an image BEFORE the heavy upload. Returns the
  /// raw Gemini verdict including a `should_upload` flag.
  Future<Map<String, dynamic>> precheckImage(File file) async {
    final ext = file.path.split('.').last.toLowerCase();
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(file.path, filename: 'check.$ext'),
    });
    final response = await _api.upload('/ocr/precheck/', formData);
    return Map<String, dynamic>.from(response.data as Map);
  }

  /// AI improvement plan based on current marks + saved courses.
  Future<Map<String, dynamic>> getImprovementPlan() async {
    final response = await _api.get('/ocr/improvement-plan/');
    return Map<String, dynamic>.from(response.data as Map);
  }

  /// Gemini-powered "why didn't I qualify" explainer for a course.
  Future<Map<String, dynamic>> explainCourseGap(int courseId) async {
    final response = await _api.get('/courses/$courseId/explain-gap/');
    return Map<String, dynamic>.from(response.data as Map);
  }
}
