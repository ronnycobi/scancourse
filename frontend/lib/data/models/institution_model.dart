import 'package:json_annotation/json_annotation.dart';

part 'institution_model.g.dart';

@JsonSerializable()
class InstitutionModel {
  final int id;
  final String name;
  @JsonKey(name: 'short_name')
  final String? shortName;
  final String slug;
  @JsonKey(name: 'institution_type')
  final String institutionType;
  final String province;
  final String? city;
  final String? logo;
  @JsonKey(name: 'logo_url')
  final String? logoUrl;
  @JsonKey(name: 'cover_image_url')
  final String? coverImageUrl;
  @JsonKey(name: 'application_open')
  final bool applicationOpen;
  @JsonKey(name: 'application_deadline')
  final String? applicationDeadline;
  @JsonKey(name: 'nsfas_accredited')
  final bool nsfasAccredited;
  @JsonKey(name: 'min_aps')
  final int minAps;
  final String? description;
  final String? website;
  @JsonKey(name: 'application_url')
  final String? applicationUrl;

  const InstitutionModel({
    required this.id,
    required this.name,
    this.shortName,
    required this.slug,
    required this.institutionType,
    required this.province,
    this.city,
    this.logo,
    this.logoUrl,
    this.coverImageUrl,
    this.applicationOpen = false,
    this.applicationDeadline,
    this.nsfasAccredited = false,
    this.minAps = 0,
    this.description,
    this.website,
    this.applicationUrl,
  });

  factory InstitutionModel.fromJson(Map<String, dynamic> json) => _$InstitutionModelFromJson(json);
  Map<String, dynamic> toJson() => _$InstitutionModelToJson(this);
}
