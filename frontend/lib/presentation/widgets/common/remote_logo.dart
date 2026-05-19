import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

/// Loads a remote logo with graceful fallback to a coloured initial badge.
class RemoteLogo extends StatelessWidget {
  final String? url;
  final String fallbackInitial;
  final double size;
  final Color fallbackBg;
  final Color fallbackFg;

  const RemoteLogo({
    super.key,
    required this.url,
    required this.fallbackInitial,
    this.size = 44,
    this.fallbackBg = AppColors.primaryLight,
    this.fallbackFg = AppColors.primary,
  });

  Widget _fallback() {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: fallbackBg,
        borderRadius: BorderRadius.circular(size * 0.22),
      ),
      alignment: Alignment.center,
      child: Text(
        fallbackInitial.isEmpty ? '?' : fallbackInitial[0].toUpperCase(),
        style: TextStyle(
          color: fallbackFg,
          fontWeight: FontWeight.w700,
          fontSize: size * 0.42,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (url == null || url!.isEmpty) return _fallback();
    return ClipRRect(
      borderRadius: BorderRadius.circular(size * 0.22),
      child: Container(
        width: size,
        height: size,
        color: Colors.white,
        padding: EdgeInsets.all(size * 0.1),
        child: Image.network(
          url!,
          fit: BoxFit.contain,
          errorBuilder: (_, __, ___) => _fallback(),
          loadingBuilder: (_, child, progress) {
            if (progress == null) return child;
            return Container(
              width: size,
              height: size,
              color: AppColors.surface,
              alignment: Alignment.center,
              child: SizedBox(
                width: 14,
                height: 14,
                child: CircularProgressIndicator(
                  strokeWidth: 1.5,
                  color: AppColors.textHint,
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
