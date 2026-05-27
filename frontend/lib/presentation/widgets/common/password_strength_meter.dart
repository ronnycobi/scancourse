import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

/// 4-step strength meter that updates as the user types.
///
/// Strength is computed the same way the backend validates:
///   - At least 8 characters → 1 point
///   - Contains a letter AND a digit → 1 point
///   - Mixes upper + lower case → 1 point
///   - Contains a special character OR is ≥ 12 chars → 1 point
///
/// Score: 0 (empty) → 4 (strong). Shows a coloured bar + label.
class PasswordStrengthMeter extends StatelessWidget {
  final String password;
  const PasswordStrengthMeter({super.key, required this.password});

  int get _score {
    final pw = password;
    if (pw.isEmpty) return 0;
    int s = 0;
    if (pw.length >= 8) s++;
    if (RegExp(r'[A-Za-z]').hasMatch(pw) && RegExp(r'\d').hasMatch(pw)) s++;
    if (RegExp(r'[a-z]').hasMatch(pw) && RegExp(r'[A-Z]').hasMatch(pw)) s++;
    if (pw.length >= 12 || RegExp(r'[^A-Za-z0-9]').hasMatch(pw)) s++;
    return s;
  }

  Color get _color {
    switch (_score) {
      case 1:
        return AppColors.error;
      case 2:
        return AppColors.accent;
      case 3:
        return AppColors.secondary;
      case 4:
        return AppColors.eligible;
      default:
        return AppColors.border;
    }
  }

  String get _label {
    switch (_score) {
      case 0:
        return '';
      case 1:
        return 'Too weak';
      case 2:
        return 'Weak';
      case 3:
        return 'Good';
      case 4:
        return 'Strong';
      default:
        return '';
    }
  }

  @override
  Widget build(BuildContext context) {
    if (password.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(top: 8, bottom: 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 4 segments
          Row(
            children: List.generate(4, (i) {
              final isActive = i < _score;
              return Expanded(
                child: Container(
                  height: 4,
                  margin: EdgeInsets.only(right: i < 3 ? 4 : 0),
                  decoration: BoxDecoration(
                    color: isActive ? _color : AppColors.border,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              );
            }),
          ),
          const SizedBox(height: 4),
          Text(
            _label,
            style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                color: _color),
          ),
        ],
      ),
    );
  }
}

/// Live checklist of password requirements. Each item turns from
/// grey/× to green/✓ as the user types.
class PasswordChecklist extends StatelessWidget {
  final String password;
  final String username;
  final String email;
  const PasswordChecklist({
    super.key,
    required this.password,
    this.username = '',
    this.email = '',
  });

  bool _hasLength() => password.length >= 8;
  bool _hasLetterAndDigit() =>
      RegExp(r'[A-Za-z]').hasMatch(password) &&
      RegExp(r'\d').hasMatch(password);
  bool _notTooSimilar() {
    if (password.isEmpty) return false;
    final pwLower = password.toLowerCase();
    if (username.isNotEmpty && pwLower.contains(username.toLowerCase())) {
      return false;
    }
    if (email.isNotEmpty) {
      final emailPart = email.split('@').first.toLowerCase();
      if (emailPart.length >= 4 && pwLower.contains(emailPart)) return false;
    }
    return true;
  }

  bool _notAllNumbers() =>
      password.isNotEmpty && !RegExp(r'^\d+$').hasMatch(password);

  @override
  Widget build(BuildContext context) {
    if (password.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(top: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _check('At least 8 characters', _hasLength()),
          _check('Includes a letter AND a digit', _hasLetterAndDigit()),
          _check('Not all numbers', _notAllNumbers()),
          _check("Doesn't repeat your name or email", _notTooSimilar()),
        ],
      ),
    );
  }

  Widget _check(String label, bool ok) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 2),
      child: Row(
        children: [
          Icon(
            ok ? Icons.check_circle : Icons.radio_button_unchecked,
            size: 14,
            color: ok ? AppColors.eligible : AppColors.textHint,
          ),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              fontSize: 11.5,
              color: ok ? AppColors.eligible : AppColors.textSecondary,
              fontWeight: ok ? FontWeight.w600 : FontWeight.w400,
            ),
          ),
        ],
      ),
    );
  }
}
