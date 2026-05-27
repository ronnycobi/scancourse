// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'user_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

UserModel _$UserModelFromJson(Map<String, dynamic> json) => UserModel(
      id: (json['id'] as num).toInt(),
      email: json['email'] as String,
      username: json['username'] as String,
      firstName: json['first_name'] as String? ?? '',
      lastName: json['last_name'] as String? ?? '',
      phoneNumber: json['phone_number'] as String?,
      profilePicture: json['profile_picture'] as String?,
      grade: json['grade'] as String?,
      province: json['province'] as String?,
      preferredField: json['preferred_field'] as String?,
      preferredStudyProvince: json['preferred_study_province'] as String?,
      dreamCareer: json['dream_career'] as String?,
      preferredFields: (json['preferred_fields'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      preferredStudyProvinces:
          (json['preferred_study_provinces'] as List<dynamic>?)
                  ?.map((e) => e as String)
                  .toList() ??
              [],
      dreamCareers: (json['dream_careers'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      onboardingCompleted: json['onboarding_completed'] as bool? ?? false,
      createdAt: json['created_at'] == null
          ? null
          : DateTime.parse(json['created_at'] as String),
    );

Map<String, dynamic> _$UserModelToJson(UserModel instance) => <String, dynamic>{
      'id': instance.id,
      'email': instance.email,
      'username': instance.username,
      'first_name': instance.firstName,
      'last_name': instance.lastName,
      'phone_number': instance.phoneNumber,
      'profile_picture': instance.profilePicture,
      'grade': instance.grade,
      'province': instance.province,
      'preferred_field': instance.preferredField,
      'preferred_study_province': instance.preferredStudyProvince,
      'dream_career': instance.dreamCareer,
      'preferred_fields': instance.preferredFields,
      'preferred_study_provinces': instance.preferredStudyProvinces,
      'dream_careers': instance.dreamCareers,
      'onboarding_completed': instance.onboardingCompleted,
      'created_at': instance.createdAt?.toIso8601String(),
    };

AuthResponse _$AuthResponseFromJson(Map<String, dynamic> json) => AuthResponse(
      access: json['access'] as String,
      refresh: json['refresh'] as String,
      user: UserModel.fromJson(json['user'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$AuthResponseToJson(AuthResponse instance) =>
    <String, dynamic>{
      'access': instance.access,
      'refresh': instance.refresh,
      'user': instance.user,
    };
