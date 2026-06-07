import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../../core/theme/app_theme.dart';
import '../../../providers/auth_provider.dart';

/// Watches the locally-stored profile image path AND validates that
/// the file at that path still exists on disk — a stale path (camera
/// cache cleared, OS pruned the temp dir, user reinstalled the app)
/// is treated as no image rather than showing a broken image icon.
final profileImagePathProvider = FutureProvider<String?>((ref) async {
  const storage = FlutterSecureStorage();
  final path = await storage.read(key: 'profile_image_path');
  if (path == null || path.isEmpty) return null;
  try {
    final exists = await File(path).exists();
    if (!exists) {
      // Clean up the stale pointer so we don't re-check every rebuild.
      await storage.delete(key: 'profile_image_path');
      return null;
    }
  } catch (_) {
    return null;
  }
  return path;
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

    final fallback = CircleAvatar(
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

    // Pull the path; only switch to the image once the provider has
    // resolved and confirmed the file is still on disk.
    final path = pathAsync.valueOrNull;
    Widget avatar = fallback;
    if (path != null && path.isNotEmpty) {
      avatar = CircleAvatar(
        radius: radius,
        backgroundColor: AppColors.primaryLight,
        // onBackgroundImageError fires if FileImage decode fails after
        // resolution — invalidate the provider so the next rebuild
        // falls back to the initial instead of looping on a broken file.
        backgroundImage: FileImage(File(path)),
        onBackgroundImageError: (_, __) {
          ref.invalidate(profileImagePathProvider);
        },
      );
    }

    if (onTap != null) {
      return GestureDetector(onTap: onTap, child: avatar);
    }
    return avatar;
  }
}
