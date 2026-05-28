import 'package:json_annotation/json_annotation.dart';

part 'aps_model.g.dart';

@JsonSerializable()
class ApsSubject {
  final String name;
  @JsonKey(name: 'normalized_name')
  final String? normalizedName;
  final int mark;
  @JsonKey(name: 'aps_points')
  final int apsPoints;
  @JsonKey(name: 'is_life_orientation')
  final bool isLifeOrientation;

  const ApsSubject({
    required this.name,
    this.normalizedName,
    required this.mark,
    required this.apsPoints,
    this.isLifeOrientation = false,
  });

  factory ApsSubject.fromJson(Map<String, dynamic> json) => _$ApsSubjectFromJson(json);
  Map<String, dynamic> toJson() => _$ApsSubjectToJson(this);
}

@JsonSerializable()
class ApsResult {
  // Nullable: the merged "best APS across reports" endpoint returns
  // id=null because the result is synthesized from multiple APSResults.
  final int? id;
  @JsonKey(name: 'total_aps')
  final int totalAps;
  @JsonKey(name: 'subjects_data')
  final List<dynamic> subjectsData;
  @JsonKey(name: 'created_at')
  final DateTime? createdAt;

  const ApsResult({
    this.id,
    required this.totalAps,
    required this.subjectsData,
    this.createdAt,
  });

  List<ApsSubject> get subjects => subjectsData
      .map((s) => ApsSubject.fromJson(Map<String, dynamic>.from(s as Map)))
      .toList();

  factory ApsResult.fromJson(Map<String, dynamic> json) => _$ApsResultFromJson(json);
  Map<String, dynamic> toJson() => _$ApsResultToJson(this);
}

@JsonSerializable()
class ReportModel {
  final int id;
  final String? file;
  @JsonKey(name: 'file_type')
  final String fileType;
  final String status;
  final String? grade;
  @JsonKey(name: 'academic_year')
  final String? academicYear;
  @JsonKey(name: 'school_name')
  final String? schoolName;
  final List<dynamic>? subjects;
  @JsonKey(name: 'aps_result')
  final ApsResult? apsResult;
  @JsonKey(name: 'created_at')
  final DateTime? createdAt;

  const ReportModel({
    required this.id,
    this.file,
    required this.fileType,
    required this.status,
    this.grade,
    this.academicYear,
    this.schoolName,
    this.subjects,
    this.apsResult,
    this.createdAt,
  });

  factory ReportModel.fromJson(Map<String, dynamic> json) => _$ReportModelFromJson(json);
  Map<String, dynamic> toJson() => _$ReportModelToJson(this);
}
