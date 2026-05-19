import 'package:json_annotation/json_annotation.dart';

part 'bursary_model.g.dart';

@JsonSerializable()
class BursaryModel {
  final int id;
  final String name;
  final String provider;
  final String? description;
  final String field;
  @JsonKey(name: 'funding_type')
  final String fundingType;
  final List<dynamic>? coverage;
  final double? amount;
  final String province;
  final String? eligibility;
  @JsonKey(name: 'min_grade_average')
  final int? minGradeAverage;
  @JsonKey(name: 'max_household_income')
  final int? maxHouseholdIncome;
  @JsonKey(name: 'application_url')
  final String applicationUrl;
  @JsonKey(name: 'application_deadline')
  final String? applicationDeadline;
  final String? logo;
  @JsonKey(name: 'logo_url')
  final String? logoUrl;

  const BursaryModel({
    required this.id,
    required this.name,
    required this.provider,
    this.description,
    required this.field,
    required this.fundingType,
    this.coverage,
    this.amount,
    required this.province,
    this.eligibility,
    this.minGradeAverage,
    this.maxHouseholdIncome,
    required this.applicationUrl,
    this.applicationDeadline,
    this.logo,
    this.logoUrl,
  });

  factory BursaryModel.fromJson(Map<String, dynamic> json) => _$BursaryModelFromJson(json);
  Map<String, dynamic> toJson() => _$BursaryModelToJson(this);
}
