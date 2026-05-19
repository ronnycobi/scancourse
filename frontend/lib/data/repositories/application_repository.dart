import '../services/api/api_client.dart';

class ApplicationModel {
  final int id;
  final int institutionId;
  final String institutionName;
  final int? courseId;
  final String? courseName;
  final String status;
  final String? deadline;
  final String? applicationUrl;
  final String? applicationReference;
  final bool isPriority;
  final int progress;

  ApplicationModel.fromJson(Map<String, dynamic> j)
      : id = j['id'] as int,
        institutionId = (j['institution'] is Map
                ? j['institution']['id']
                : j['institution']) as int,
        institutionName = (j['institution'] is Map
                ? j['institution']['name']
                : j['institution_name']) as String? ??
            'Unknown',
        courseId = j['course'] is Map ? j['course']['id'] : j['course'],
        courseName = j['course'] is Map ? j['course']['name'] : j['course_name'],
        status = (j['status'] as String?) ?? 'draft',
        deadline = j['deadline'] as String?,
        applicationUrl = j['application_url'] as String?,
        applicationReference = j['application_reference'] as String?,
        isPriority = (j['is_priority'] as bool?) ?? false,
        progress = (j['progress'] as int?) ?? 0;
}

class ApplicationStats {
  final int total;
  final int inProgress;
  final int submitted;
  final int offers;
  final int rejected;
  final int closingSoon;

  ApplicationStats.fromJson(Map<String, dynamic> j)
      : total = j['total'] as int? ?? 0,
        inProgress = j['in_progress'] as int? ?? 0,
        submitted = j['submitted'] as int? ?? 0,
        offers = j['offers'] as int? ?? 0,
        rejected = j['rejected'] as int? ?? 0,
        closingSoon = j['closing_soon'] as int? ?? 0;
}

class ApplicationRepository {
  final ApiClient _api = ApiClient.instance;

  Future<List<ApplicationModel>> list({String? statusFilter}) async {
    final resp = await _api.get('/applications/', queryParams: {
      if (statusFilter != null) 'status': statusFilter,
    }).timeout(
      const Duration(seconds: 15),
      onTimeout: () => throw Exception('Request timed out.'),
    );
    final list = (resp.data['results'] ?? resp.data) as List;
    return list
        .map((e) => ApplicationModel.fromJson(Map<String, dynamic>.from(e)))
        .toList();
  }

  Future<ApplicationStats> stats() async {
    final resp = await _api.get('/applications/stats/').timeout(
      const Duration(seconds: 15),
      onTimeout: () => throw Exception('Request timed out.'),
    );
    return ApplicationStats.fromJson(Map<String, dynamic>.from(resp.data));
  }

  Future<int> create({
    required int institutionId,
    int? courseId,
    String? applicationUrl,
    String? deadline,
  }) async {
    final resp = await _api.post('/applications/create/', data: {
      'institution': institutionId,
      if (courseId != null) 'course': courseId,
      if (applicationUrl != null) 'application_url': applicationUrl,
      if (deadline != null) 'deadline': deadline,
    });
    return resp.data['id'] as int;
  }

  Future<void> updateStatus(int id, String newStatus, {String? note}) async {
    await _api.post('/applications/$id/status/', data: {
      'status': newStatus,
      if (note != null) 'note': note,
    });
  }

  Future<void> delete(int id) => _api.delete('/applications/$id/');
}
