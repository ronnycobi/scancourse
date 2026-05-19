// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'institution_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

InstitutionModel _$InstitutionModelFromJson(Map<String, dynamic> json) =>
    InstitutionModel(
      id: (json['id'] as num).toInt(),
      name: json['name'] as String,
      shortName: json['short_name'] as String?,
      slug: json['slug'] as String,
      institutionType: json['institution_type'] as String,
      province: json['province'] as String,
      city: json['city'] as String?,
      logo: json['logo'] as String?,
      logoUrl: json['logo_url'] as String?,
      coverImageUrl: json['cover_image_url'] as String?,
      applicationOpen: json['application_open'] as bool? ?? false,
      applicationDeadline: json['application_deadline'] as String?,
      nsfasAccredited: json['nsfas_accredited'] as bool? ?? false,
      minAps: (json['min_aps'] as num?)?.toInt() ?? 0,
      description: json['description'] as String?,
      website: json['website'] as String?,
      applicationUrl: json['application_url'] as String?,
    );

Map<String, dynamic> _$InstitutionModelToJson(InstitutionModel instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'short_name': instance.shortName,
      'slug': instance.slug,
      'institution_type': instance.institutionType,
      'province': instance.province,
      'city': instance.city,
      'logo': instance.logo,
      'logo_url': instance.logoUrl,
      'cover_image_url': instance.coverImageUrl,
      'application_open': instance.applicationOpen,
      'application_deadline': instance.applicationDeadline,
      'nsfas_accredited': instance.nsfasAccredited,
      'min_aps': instance.minAps,
      'description': instance.description,
      'website': instance.website,
      'application_url': instance.applicationUrl,
    };
