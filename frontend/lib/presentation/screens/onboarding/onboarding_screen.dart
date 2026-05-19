import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:smooth_page_indicator/smooth_page_indicator.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/constants/app_constants.dart';
import '../../../providers/auth_provider.dart';
import '../../widgets/common/loading_button.dart';

class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  final _pageCtrl = PageController();
  int _currentPage = 0;
  bool _isSubmitting = false;

  String? _selectedGrade;
  String? _selectedProvince;
  String? _selectedField;
  String? _selectedStudyProvince;
  final _careerCtrl = TextEditingController();

  static const int _totalPages = 5;

  @override
  void dispose() {
    _pageCtrl.dispose();
    _careerCtrl.dispose();
    super.dispose();
  }

  bool get _canProceed {
    switch (_currentPage) {
      case 0: return _selectedGrade != null;
      case 1: return _selectedProvince != null;
      case 2: return _selectedField != null;
      case 3: return _selectedStudyProvince != null;
      case 4: return true;
      default: return false;
    }
  }

  void _next() {
    if (_currentPage < _totalPages - 1) {
      _pageCtrl.nextPage(
        duration: const Duration(milliseconds: 350),
        curve: Curves.easeInOut,
      );
    } else {
      _complete();
    }
  }

  void _back() {
    if (_currentPage > 0) {
      _pageCtrl.previousPage(
        duration: const Duration(milliseconds: 350),
        curve: Curves.easeInOut,
      );
    }
  }

  Future<void> _complete() async {
    setState(() => _isSubmitting = true);
    try {
      await ref.read(authStateProvider.notifier).completeOnboarding({
        if (_selectedGrade != null) 'grade': _selectedGrade,
        if (_selectedProvince != null) 'province': _selectedProvince,
        if (_selectedField != null) 'preferred_field': _selectedField,
        if (_selectedStudyProvince != null)
          'preferred_study_province': _selectedStudyProvince,
        if (_careerCtrl.text.trim().isNotEmpty)
          'dream_career': _careerCtrl.text.trim(),
      });
      if (mounted) context.go('/home');
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Could not save: $e'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  Widget _buildChip(String label, String value, String? selected, void Function(String) onSelect) {
    final isSelected = selected == value;
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: () => setState(() => onSelect(value)),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 13),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primary : Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isSelected ? AppColors.primary : AppColors.border,
            width: isSelected ? 2 : 1.5,
          ),
          boxShadow: isSelected
              ? [BoxShadow(color: AppColors.primary.withOpacity(0.25), blurRadius: 8, offset: const Offset(0, 2))]
              : null,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (isSelected) ...[
              const Icon(Icons.check_circle, color: Colors.white, size: 16),
              const SizedBox(width: 6),
            ],
            Text(
              label,
              style: TextStyle(
                color: isSelected ? Colors.white : AppColors.textPrimary,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
                fontSize: 14,
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      body: SafeArea(
        child: Column(
          children: [
            // Top bar
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
              child: Row(
                children: [
                  if (_currentPage > 0)
                    IconButton(
                      onPressed: _back,
                      icon: const Icon(Icons.arrow_back_ios_new, size: 20),
                      style: IconButton.styleFrom(
                        backgroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                    )
                  else
                    const SizedBox(width: 40),
                  const Spacer(),
                  SmoothPageIndicator(
                    controller: _pageCtrl,
                    count: _totalPages,
                    effect: WormEffect(
                      dotColor: AppColors.border,
                      activeDotColor: AppColors.primary,
                      dotHeight: 8,
                      dotWidth: 8,
                    ),
                  ),
                  const Spacer(),
                  TextButton(
                    onPressed: _complete,
                    child: Text(
                      'Skip',
                      style: TextStyle(color: AppColors.textSecondary, fontSize: 14),
                    ),
                  ),
                ],
              ),
            ),

            // Pages — NeverScrollableScrollPhysics prevents swipe stealing taps
            Expanded(
              child: PageView(
                controller: _pageCtrl,
                physics: const NeverScrollableScrollPhysics(),
                onPageChanged: (p) => setState(() => _currentPage = p),
                children: [
                  // Page 1 — Grade
                  _StepPage(
                    emoji: '🎓',
                    title: 'What grade are you in?',
                    subtitle: "We'll personalise your experience",
                    child: Wrap(
                      spacing: 10,
                      runSpacing: 10,
                      children: AppConstants.grades.entries
                          .map((e) => _buildChip(e.value, e.key, _selectedGrade, (v) => _selectedGrade = v))
                          .toList(),
                    ),
                  ),

                  // Page 2 — Province
                  _StepPage(
                    emoji: '📍',
                    title: 'Which province are you in?',
                    subtitle: "We'll show local opportunities",
                    child: Wrap(
                      spacing: 10,
                      runSpacing: 10,
                      children: AppConstants.provinces.entries
                          .map((e) => _buildChip(e.value, e.key, _selectedProvince, (v) => _selectedProvince = v))
                          .toList(),
                    ),
                  ),

                  // Page 3 — Field
                  _StepPage(
                    emoji: '📚',
                    title: 'What field interests you?',
                    subtitle: "We'll match courses to your passion",
                    child: Wrap(
                      spacing: 10,
                      runSpacing: 10,
                      children: AppConstants.studyFields.entries
                          .map((e) => _buildChip(e.value, e.key, _selectedField, (v) => _selectedField = v))
                          .toList(),
                    ),
                  ),

                  // Page 4 — Study province
                  _StepPage(
                    emoji: '🏫',
                    title: 'Where do you want to study?',
                    subtitle: 'Your preferred study province',
                    child: Wrap(
                      spacing: 10,
                      runSpacing: 10,
                      children: AppConstants.provinces.entries
                          .map((e) => _buildChip(e.value, e.key, _selectedStudyProvince, (v) => _selectedStudyProvince = v))
                          .toList(),
                    ),
                  ),

                  // Page 5 — Dream career
                  _StepPage(
                    emoji: '🌟',
                    title: "What's your dream career?",
                    subtitle: 'Optional — helps us find the best path for you',
                    child: TextField(
                      controller: _careerCtrl,
                      autofocus: false,
                      textCapitalization: TextCapitalization.words,
                      decoration: InputDecoration(
                        hintText: 'e.g. Software Engineer, Doctor, Teacher...',
                        prefixIcon: const Icon(Icons.star_outline, color: AppColors.accent),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      maxLines: 2,
                    ),
                  ),
                ],
              ),
            ),

            // Bottom button
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
              child: Column(
                children: [
                  // Selection hint when nothing chosen
                  if (!_canProceed && _currentPage < 4)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Text(
                        'Please select an option to continue',
                        style: TextStyle(color: AppColors.textHint, fontSize: 13),
                      ),
                    ),
                  LoadingButton(
                    label: _currentPage == _totalPages - 1 ? 'Get Started 🚀' : 'Continue',
                    isLoading: _isSubmitting,
                    onPressed: _canProceed ? _next : null,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StepPage extends StatelessWidget {
  final String emoji;
  final String title;
  final String subtitle;
  final Widget child;

  const _StepPage({
    required this.emoji,
    required this.title,
    required this.subtitle,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(emoji, style: const TextStyle(fontSize: 52)),
          const SizedBox(height: 16),
          Text(title, style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 8),
          Text(subtitle, style: Theme.of(context).textTheme.bodyMedium),
          const SizedBox(height: 28),
          child,
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}
