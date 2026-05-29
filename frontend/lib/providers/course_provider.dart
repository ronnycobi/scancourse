import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/models/course_model.dart';
import '../data/repositories/course_repository.dart';

final courseRepositoryProvider = Provider((ref) => CourseRepository());

// Stable String key — Maps are reference-equal in Dart and cause endless refetching.
final courseListProvider =
    FutureProvider.family<List<CourseModel>, String?>((ref, paramStr) async {
  final params = <String, String>{};
  if (paramStr != null && paramStr.isNotEmpty) {
    for (final part in paramStr.split('&')) {
      final kv = part.split('=');
      if (kv.length == 2) params[kv[0]] = Uri.decodeComponent(kv[1]);
    }
  }
  final repo = ref.read(courseRepositoryProvider);
  return repo.getCourses(
    field: params['field'],
    province: params['province'],
    institutionType: params['institution_type'],
    minAps: params['min_aps'] != null ? int.tryParse(params['min_aps']!) : null,
    maxAps: params['max_aps'] != null ? int.tryParse(params['max_aps']!) : null,
    search: params['search'],
  );
});

final courseDetailProvider = FutureProvider.family<CourseModel, int>((ref, id) async {
  final repo = ref.read(courseRepositoryProvider);
  return repo.getCourse(id);
});

/// Ranked, comprehensive search for users WITH an APS: returns the whole
/// catalogue matching the query (qualify or not) ordered best-fit-first.
final courseSearchProvider =
    FutureProvider.family<List<OfferingMatchModel>, String>((ref, query) async {
  if (query.trim().isEmpty) return [];
  final repo = ref.read(courseRepositoryProvider);
  final data = await repo.getMatches(
    search: query,
    includeNotQualified: true,
    limit: 80,
  );
  final results = (data['results'] as List? ?? []);
  return results
      .map((e) => OfferingMatchModel.fromJson(Map<String, dynamic>.from(e as Map)))
      .toList();
});

final courseRecommendationsProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final repo = ref.read(courseRepositoryProvider);
  return repo.getRecommendations(limit: 20);
});

// Key is a canonical query string like "field=business&province=GP" (or null/empty).
// Using String instead of Map because Map equality is reference-based in Dart,
// which causes FutureProvider.family to create a new instance on every rebuild.
final courseMatchProvider = FutureProvider.family<Map<String, dynamic>, String?>((ref, paramStr) async {
  final params = <String, String?>{};
  if (paramStr != null && paramStr.isNotEmpty) {
    for (final part in paramStr.split('&')) {
      final kv = part.split('=');
      if (kv.length == 2) params[kv[0]] = kv[1];
    }
  }
  final repo = ref.read(courseRepositoryProvider);
  return repo.getMatches(
    field: params['field'],
    province: params['province'],
    institutionType: params['institution_type'] ?? params['type'],
    level: params['level'],
    search: params['search'],
  ).timeout(
    const Duration(seconds: 30),
    onTimeout: () => throw Exception('Request timed out. Check your connection.'),
  );
});

class CourseFilterState {
  final String? field;
  final String? province;
  final String? institutionType;
  final String? level;
  final int? userAps;
  final String? search;
  final String category;

  const CourseFilterState({
    this.field,
    this.province,
    this.institutionType,
    this.level,
    this.userAps,
    this.search,
    this.category = 'eligible',
  });

  CourseFilterState copyWith({
    String? field,
    String? province,
    String? institutionType,
    String? level,
    int? userAps,
    String? search,
    String? category,
    bool clearField = false,
    bool clearProvince = false,
    bool clearInstitutionType = false,
  }) {
    return CourseFilterState(
      field: clearField ? null : (field ?? this.field),
      province: clearProvince ? null : (province ?? this.province),
      institutionType: clearInstitutionType ? null : (institutionType ?? this.institutionType),
      level: level ?? this.level,
      userAps: userAps ?? this.userAps,
      search: search ?? this.search,
      category: category ?? this.category,
    );
  }
}

final courseFilterProvider =
    StateNotifierProvider<CourseFilterNotifier, CourseFilterState>((ref) {
  // Filters start at their default (unset) — nothing is applied until the
  // user taps a chip and chooses a value. We no longer pre-seed the field
  // from the profile, which silently constrained results on first open.
  return CourseFilterNotifier();
});

class CourseFilterNotifier extends StateNotifier<CourseFilterState> {
  CourseFilterNotifier({String? initialField})
      : super(CourseFilterState(field: initialField));

  void setField(String? v) => state = state.copyWith(field: v, clearField: v == null);
  void setProvince(String? v) => state = state.copyWith(province: v, clearProvince: v == null);
  void setInstitutionType(String? v) => state = state.copyWith(institutionType: v, clearInstitutionType: v == null);
  void setLevel(String? v) => state = state.copyWith(level: v);
  void setSearch(String? v) => state = state.copyWith(search: v);
  void setCategory(String v) => state = state.copyWith(category: v);
  void reset() => state = const CourseFilterState();
}
