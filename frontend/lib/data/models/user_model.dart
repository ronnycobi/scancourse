import 'package:json_annotation/json_annotation.dart';

part 'user_model.g.dart';

@JsonSerializable()
class UserModel {
  final int id;
  final String email;
  final String username;
  @JsonKey(name: 'first_name')
  final String firstName;
  @JsonKey(name: 'last_name')
  final String lastName;
  @JsonKey(name: 'phone_number')
  final String? phoneNumber;
  @JsonKey(name: 'profile_picture')
  final String? profilePicture;
  final String? grade;
  final String? province;
  @JsonKey(name: 'preferred_field')
  final String? preferredField;
  @JsonKey(name: 'preferred_study_province')
  final String? preferredStudyProvince;
  @JsonKey(name: 'dream_career')
  final String? dreamCareer;
  @JsonKey(name: 'onboarding_completed')
  final bool onboardingCompleted;
  @JsonKey(name: 'created_at')
  final DateTime? createdAt;

  const UserModel({
    required this.id,
    required this.email,
    required this.username,
    this.firstName = '',
    this.lastName = '',
    this.phoneNumber,
    this.profilePicture,
    this.grade,
    this.province,
    this.preferredField,
    this.preferredStudyProvince,
    this.dreamCareer,
    this.onboardingCompleted = false,
    this.createdAt,
  });

  String get fullName => '$firstName $lastName'.trim().isEmpty ? email : '$firstName $lastName'.trim();

  factory UserModel.fromJson(Map<String, dynamic> json) => _$UserModelFromJson(json);
  Map<String, dynamic> toJson() => _$UserModelToJson(this);
}


@JsonSerializable()
class AuthResponse {
  final String access;
  final String refresh;
  final UserModel user;

  const AuthResponse({required this.access, required this.refresh, required this.user});

  factory AuthResponse.fromJson(Map<String, dynamic> json) => _$AuthResponseFromJson(json);
  Map<String, dynamic> toJson() => _$AuthResponseToJson(this);
}
