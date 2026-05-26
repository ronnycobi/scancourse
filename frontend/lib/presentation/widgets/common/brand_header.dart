import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/constants/app_constants.dart';

/// Logo + "Scancourse" wordmark. Used across auth screens for consistency.
class BrandHeader extends StatelessWidget {
  final double logoSize;
  final double? wordmarkSize;
  final Color wordmarkColor;
  final MainAxisAlignment alignment;

  const BrandHeader({
    super.key,
    this.logoSize = 48,
    this.wordmarkSize,
    this.wordmarkColor = AppColors.primary,
    this.alignment = MainAxisAlignment.start,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: alignment,
      mainAxisSize: MainAxisSize.min,
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(logoSize / 4),
          child: Image.asset(
            'assets/icons/scancourse-logo.png',
            width: logoSize,
            height: logoSize,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => Container(
              width: logoSize,
              height: logoSize,
              decoration: BoxDecoration(
                color: AppColors.primaryLight,
                borderRadius: BorderRadius.circular(logoSize / 4),
              ),
              child: Icon(
                Icons.document_scanner_rounded,
                color: AppColors.primary,
                size: logoSize * 0.6,
              ),
            ),
          ),
        ),
        SizedBox(width: logoSize / 4),
        Text(
          AppConstants.appName,
          style: (wordmarkSize != null
                  ? TextStyle(fontSize: wordmarkSize)
                  : Theme.of(context).textTheme.headlineLarge)
              ?.copyWith(
            color: wordmarkColor,
            fontWeight: FontWeight.w800,
            letterSpacing: -0.3,
          ),
        ),
      ],
    );
  }
}

/// Standalone logo only (no wordmark). Use it where you want the icon
/// without the text — e.g. splash screen.
class BrandLogo extends StatelessWidget {
  final double size;
  final Color background;
  final Color foreground;

  const BrandLogo({
    super.key,
    this.size = 96,
    this.background = Colors.white,
    this.foreground = AppColors.primary,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(size / 4),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.12),
            blurRadius: size / 4,
            offset: Offset(0, size / 16),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(size / 4),
        child: Image.asset(
          'assets/icons/scancourse-logo.png',
          width: size,
          height: size,
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) => Icon(
            Icons.document_scanner_rounded,
            size: size * 0.58,
            color: foreground,
          ),
        ),
      ),
    );
  }
}
