import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../../core/theme/app_theme.dart';
import '../../../providers/auth_provider.dart';

/// Watches the locally-stored profile image path and the current user.
/// Pull-in widget so the avatar can be reused everywhere without each
/// screen re-implementing file lookup.
final profileImagePathProvider = FutureProvider<String?>((ref) async {
  const storage = FlutterSecureStorage();
  return storage.read(key: 'profile_image_path');
});

class AppAvatar extends ConsumerWidget {
  final double radius;
  final VoidCallback? onTap;

  const AppAvatar({super.key, this.radius = 18, this.onTap});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authStateProvider).user;
    final pathAsync = ref.watch(profileImagePathProvider);

    final initial = user?.firstName.isNotEmpty == true
        ? user!.firstName[0].toUpperCase()
        : 'S';

    Widget avatar = CircleAvatar(
      radius: radius,
      backgroundColor: AppColors.primaryLight,
      child: Text(
        initial,
        style: TextStyle(
          color: AppColors.primary,
          fontSize: radius * 0.85,
          fontWeight: FontWeight.w700,
        ),
      ),
    );

    pathAsync.whenData((path) {
      if (path != null && File(path).existsSync()) {
        avatar = CircleAvatar(
          radius: radius,
          backgroundColor: AppColors.primaryLight,
          backgroundImage: FileImage(File(path)),
        );
      }
    });

    if (onTap != null) {
      return GestureDetector(onTap: onTap, child: avatar);
    }
    return avatar;
  }
}
