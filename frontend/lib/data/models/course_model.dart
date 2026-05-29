import 'package:json_annotation/json_annotation.dart';
import 'institution_model.dart';

part 'course_model.g.dart';

// ── New flat match models (manual fromJson, no codegen) ──────────────────────

class MatchDetail {
  final String category;
  final int apsSurplus;
  final List<Map<String, dynamic>> missingSubjects;
  final List<Map<String, dynamic>> lowSubjects;
  final bool mathsLitBlocked;
  final int score;
  final bool tvet;

  const MatchDetail({
    required this.category,
    required this.apsSurplus,
    required this.missingSubjects,
    required this.lowSubjects,
    required this.mathsLitBlocked,
    required this.score,
    required this.tvet,
  });

  factory MatchDetail.fromJson(Map<String, dynamic> json) => MatchDetail(
        category: json['category'] as String,
        apsSurplus: json['aps_surplus'] as int,
        missingSubjects:
            (json['missing_subjects'] as List).cast<Map<String, dynamic>>(),
        lowSubjects:
            (json['low_subjects'] as List).cast<Map<String, dynamic>>(),
        mathsLitBlocked: json['maths_lit_blocked'] as bool,
        score: json['score'] as int,
        tvet: json['tvet'] as bool? ?? false,
      );
}

class OfferingMatchModel {
  final int offeringId;
  final int courseId;
  final String courseName;
  final String courseField;
  final String courseLevel;
  final double? courseDurationYears;
  final String? courseDescription;
  final int institutionId;
  final String institutionName;
  final String? institutionShort;
  final String institutionType;
  final String institutionProvince;
  final String? institutionCity;
  final String? institutionWebsite;
  final String? institutionLogoUrl;
  final String? institutionApplyUrl;
  final String? campus;
  final int minAps;
  final String? applicationDeadline;
  final String? programmeCode;
  final List<dynamic> subjectRequirements;
  final MatchDetail match;
  // How many colleges offer this (TVET courses are collapsed to one card).
  final int offeringCount;

  const OfferingMatchModel({
    required this.offeringId,
    required this.courseId,
    required this.courseName,
    required this.courseField,
    required this.courseLevel,
    this.courseDurationYears,
    this.courseDescription,
    required this.institutionId,
    required this.institutionName,
    this.institutionShort,
    required this.institutionType,
    required this.institutionProvince,
    this.institutionCity,
    this.institutionWebsite,
    this.institutionLogoUrl,
    this.institutionApplyUrl,
    this.campus,
    required this.minAps,
    this.applicationDeadline,
    this.programmeCode,
    required this.subjectRequirements,
    required this.match,
    this.offeringCount = 1,
  });

  factory OfferingMatchModel.fromJson(Map<String, dynamic> json) =>
      OfferingMatchModel(
        offeringId: json['offering_id'] as int,
        courseId: json['course_id'] as int,
        courseName: json['course_name'] as String,
        courseField: json['course_field'] as String,
        courseLevel: json['course_level'] as String,
        courseDurationYears: (json['course_duration_years'] as num?)?.toDouble(),
        courseDescription: json['course_description'] as String?,
        institutionId: json['institution_id'] as int,
        institutionName: json['institution_name'] as String,
        institutionShort: json['institution_short'] as String?,
        institutionType: json['institution_type'] as String,
        institutionProvince: json['institution_province'] as String,
        institutionCity: json['institution_city'] as String?,
        institutionWebsite: json['institution_website'] as String?,
        institutionLogoUrl: json['institution_logo_url'] as String?,
        institutionApplyUrl: json['institution_apply_url'] as String?,
        campus: json['campus'] as String?,
        minAps: json['min_aps'] as int,
        applicationDeadline: json['application_deadline'] as String?,
        programmeCode: json['programme_code'] as String?,
        subjectRequirements: json['subject_requirements'] as List? ?? [],
        match: MatchDetail.fromJson(
            json['match'] as Map<String, dynamic>),
        offeringCount: (json['offering_count'] as num?)?.toInt() ?? 1,
      );
}

// ── Existing codegen models ───────────────────────────────────────────────────

@JsonSerializable()
class CourseModel {
  final int id;
  final String name;
  final String field;
  final String level;
  final String? description;
  @JsonKey(name: 'duration_years')
  final double? durationYears;
  @JsonKey(name: 'fees_per_year')
  final double? feesPerYear;
  @JsonKey(name: 'career_opportunities')
  final String? careerOpportunities;
  final List<dynamic>? modules;
  @JsonKey(name: 'salary_min')
  final int? salaryMin;
  @JsonKey(name: 'salary_max')
  final int? salaryMax;
  @JsonKey(name: 'min_aps')
  final int? minAps;
  final List<CourseOffering>? offerings;
  @JsonKey(name: 'match_category')
  final String? matchCategory;
  // Flat institution fields populated by the list endpoint so cards
  // can show "BCom · Wits" without needing the offerings array.
  @JsonKey(name: 'institution_name')
  final String? institutionName;
  @JsonKey(name: 'institution_short')
  final String? institutionShort;
  @JsonKey(name: 'institution_city')
  final String? institutionCity;
  @JsonKey(name: 'institution_logo_url')
  final String? institutionLogoUrl;
  @JsonKey(name: 'application_deadline')
  final String? applicationDeadline;

  const CourseModel({
    required this.id,
    required this.name,
    required this.field,
    required this.level,
    this.description,
    this.durationYears,
    this.feesPerYear,
    this.careerOpportunities,
    this.modules,
    this.salaryMin,
    this.salaryMax,
    this.minAps,
    this.offerings,
    this.matchCategory,
    this.institutionName,
    this.institutionShort,
    this.institutionCity,
    this.institutionLogoUrl,
    this.applicationDeadline,
  });

  factory CourseModel.fromJson(Map<String, dynamic> json) => _$CourseModelFromJson(json);
  Map<String, dynamic> toJson() => _$CourseModelToJson(this);
}

@JsonSerializable()
class CourseOffering {
  final int id;
  final InstitutionModel? institution;
  @JsonKey(name: 'min_aps')
  final int minAps;
  @JsonKey(name: 'application_deadline')
  final String? applicationDeadline;
  @JsonKey(name: 'application_url')
  final String? applicationUrl;

  const CourseOffering({
    required this.id,
    this.institution,
    required this.minAps,
    this.applicationDeadline,
    this.applicationUrl,
  });

  factory CourseOffering.fromJson(Map<String, dynamic> json) => _$CourseOfferingFromJson(json);
  Map<String, dynamic> toJson() => _$CourseOfferingToJson(this);
}
