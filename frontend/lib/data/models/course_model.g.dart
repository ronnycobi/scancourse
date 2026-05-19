// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'course_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CourseModel _$CourseModelFromJson(Map<String, dynamic> json) => CourseModel(
      id: (json['id'] as num).toInt(),
      name: json['name'] as String,
      field: json['field'] as String,
      level: json['level'] as String,
      description: json['description'] as String?,
      durationYears: (json['duration_years'] as num?)?.toDouble(),
      feesPerYear: (json['fees_per_year'] as num?)?.toDouble(),
      careerOpportunities: json['career_opportunities'] as String?,
      modules: json['modules'] as List<dynamic>?,
      salaryMin: (json['salary_min'] as num?)?.toInt(),
      salaryMax: (json['salary_max'] as num?)?.toInt(),
      minAps: (json['min_aps'] as num?)?.toInt(),
      offerings: (json['offerings'] as List<dynamic>?)
          ?.map((e) => CourseOffering.fromJson(e as Map<String, dynamic>))
          .toList(),
      matchCategory: json['match_category'] as String?,
    );

Map<String, dynamic> _$CourseModelToJson(CourseModel instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'field': instance.field,
      'level': instance.level,
      'description': instance.description,
      'duration_years': instance.durationYears,
      'fees_per_year': instance.feesPerYear,
      'career_opportunities': instance.careerOpportunities,
      'modules': instance.modules,
      'salary_min': instance.salaryMin,
      'salary_max': instance.salaryMax,
      'min_aps': instance.minAps,
      'offerings': instance.offerings,
      'match_category': instance.matchCategory,
    };

CourseOffering _$CourseOfferingFromJson(Map<String, dynamic> json) =>
    CourseOffering(
      id: (json['id'] as num).toInt(),
      institution: json['institution'] == null
          ? null
          : InstitutionModel.fromJson(
              json['institution'] as Map<String, dynamic>),
      minAps: (json['min_aps'] as num).toInt(),
      applicationDeadline: json['application_deadline'] as String?,
      applicationUrl: json['application_url'] as String?,
    );

Map<String, dynamic> _$CourseOfferingToJson(CourseOffering instance) =>
    <String, dynamic>{
      'id': instance.id,
      'institution': instance.institution,
      'min_aps': instance.minAps,
      'application_deadline': instance.applicationDeadline,
      'application_url': instance.applicationUrl,
    };
