// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'aps_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ApsSubject _$ApsSubjectFromJson(Map<String, dynamic> json) => ApsSubject(
      name: json['name'] as String,
      normalizedName: json['normalized_name'] as String?,
      mark: (json['mark'] as num).toInt(),
      apsPoints: (json['aps_points'] as num).toInt(),
      isLifeOrientation: json['is_life_orientation'] as bool? ?? false,
    );

Map<String, dynamic> _$ApsSubjectToJson(ApsSubject instance) =>
    <String, dynamic>{
      'name': instance.name,
      'normalized_name': instance.normalizedName,
      'mark': instance.mark,
      'aps_points': instance.apsPoints,
      'is_life_orientation': instance.isLifeOrientation,
    };

ApsResult _$ApsResultFromJson(Map<String, dynamic> json) => ApsResult(
      id: (json['id'] as num?)?.toInt(),
      totalAps: (json['total_aps'] as num).toInt(),
      subjectsData: json['subjects_data'] as List<dynamic>,
      createdAt: json['created_at'] == null
          ? null
          : DateTime.parse(json['created_at'] as String),
    );

Map<String, dynamic> _$ApsResultToJson(ApsResult instance) => <String, dynamic>{
      'id': instance.id,
      'total_aps': instance.totalAps,
      'subjects_data': instance.subjectsData,
      'created_at': instance.createdAt?.toIso8601String(),
    };

ReportModel _$ReportModelFromJson(Map<String, dynamic> json) => ReportModel(
      id: (json['id'] as num).toInt(),
      file: json['file'] as String?,
      fileType: json['file_type'] as String,
      status: json['status'] as String,
      grade: json['grade'] as String?,
      academicYear: json['academic_year'] as String?,
      schoolName: json['school_name'] as String?,
      subjects: json['subjects'] as List<dynamic>?,
      apsResult: json['aps_result'] == null
          ? null
          : ApsResult.fromJson(json['aps_result'] as Map<String, dynamic>),
      createdAt: json['created_at'] == null
          ? null
          : DateTime.parse(json['created_at'] as String),
    );

Map<String, dynamic> _$ReportModelToJson(ReportModel instance) =>
    <String, dynamic>{
      'id': instance.id,
      'file': instance.file,
      'file_type': instance.fileType,
      'status': instance.status,
      'grade': instance.grade,
      'academic_year': instance.academicYear,
      'school_name': instance.schoolName,
      'subjects': instance.subjects,
      'aps_result': instance.apsResult,
      'created_at': instance.createdAt?.toIso8601String(),
    };
