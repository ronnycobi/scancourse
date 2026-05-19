// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'bursary_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

BursaryModel _$BursaryModelFromJson(Map<String, dynamic> json) => BursaryModel(
      id: (json['id'] as num).toInt(),
      name: json['name'] as String,
      provider: json['provider'] as String,
      description: json['description'] as String?,
      field: json['field'] as String,
      fundingType: json['funding_type'] as String,
      coverage: json['coverage'] as List<dynamic>?,
      amount: (json['amount'] as num?)?.toDouble(),
      province: json['province'] as String,
      eligibility: json['eligibility'] as String?,
      minGradeAverage: (json['min_grade_average'] as num?)?.toInt(),
      maxHouseholdIncome: (json['max_household_income'] as num?)?.toInt(),
      applicationUrl: json['application_url'] as String,
      applicationDeadline: json['application_deadline'] as String?,
      logo: json['logo'] as String?,
      logoUrl: json['logo_url'] as String?,
    );

Map<String, dynamic> _$BursaryModelToJson(BursaryModel instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'provider': instance.provider,
      'description': instance.description,
      'field': instance.field,
      'funding_type': instance.fundingType,
      'coverage': instance.coverage,
      'amount': instance.amount,
      'province': instance.province,
      'eligibility': instance.eligibility,
      'min_grade_average': instance.minGradeAverage,
      'max_household_income': instance.maxHouseholdIncome,
      'application_url': instance.applicationUrl,
      'application_deadline': instance.applicationDeadline,
      'logo': instance.logo,
      'logo_url': instance.logoUrl,
    };
