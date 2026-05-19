import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/models/course_model.dart';
import '../data/repositories/course_repository.dart';
import 'auth_provider.dart';

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
    institutionType: params['type'],
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

final courseFilterProvider = StateNotifierProvider<CourseFilterNotifier, CourseFilterState>((ref) {
  final user = ref.read(authStateProvider).user;
  // Use preferred_field from profile, or map dream career to a field as fallback.
  final initialField = user?.preferredField ?? _dreamCareerToField(user?.dreamCareer);
  return CourseFilterNotifier(initialField: initialField);
});

String? _dreamCareerToField(String? career) {
  if (career == null) return null;
  final c = career.toLowerCase();
  if (c.contains('account') || c.contains('finance') || c.contains('business') ||
      c.contains('econom') || c.contains('bank') || c.contains('commerce') ||
      c.contains('audit') || c.contains('tax')) return 'business';
  if (c.contains('doctor') || c.contains('nurse') || c.contains('pharm') ||
      c.contains('medic') || c.contains('dentist') || c.contains('surgeon') ||
      c.contains('health') || c.contains('physio')) return 'health';
  if (c.contains('engineer') || c.contains('mechanic') || c.contains('electrical') ||
      c.contains('civil') || c.contains('chemical') || c.contains('mining')) return 'engineering';
  if (c.contains('teach') || c.contains('educat') || c.contains('lecturer')) return 'education';
  if (c.contains('law') || c.contains('attorney') || c.contains('advocate') ||
      c.contains('legal') || c.contains('judge')) return 'law';
  if (c.contains('artist') || c.contains('design') || c.contains('graphic') ||
      c.contains('fashion') || c.contains('film') || c.contains('music')) return 'arts';
  if (c.contains('farm') || c.contains('agricultur') || c.contains('vet')) return 'agriculture';
  if (c.contains('program') || c.contains('develop') || c.contains('software') ||
      c.contains('computer') || c.contains('cyber') || c.contains('data scien') ||
      c.contains('it ') || c.contains('network')) return 'ict';
  if (c.contains('scientist') || c.contains('biolog') || c.contains('chemist') ||
      c.contains('physics') || c.contains('research') || c.contains('geolog')) return 'science';
  if (c.contains('architect') || c.contains('plann') || c.contains('survey') ||
      c.contains('construct') || c.contains('propert')) return 'built_environment';
  return null;
}

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
