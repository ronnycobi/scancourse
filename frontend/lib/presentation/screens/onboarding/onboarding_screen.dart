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
  // Field interests + study provinces are multi-select.
  final Set<String> _selectedFields = {};
  final Set<String> _selectedStudyProvinces = {};
  final _careerCtrl = TextEditingController();

  static const int _totalPages = 6;

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
      case 2: return _selectedFields.isNotEmpty;
      case 3: return _selectedStudyProvinces.isNotEmpty;
      case 4: return true;
      case 5: return true;  // Scan-report step always available
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

  /// Saves the profile, then routes to either /home (default) or
  /// /scanner — driven by the last onboarding page's "Scan now" CTA.
  Future<void> _complete({bool scanNow = false}) async {
    setState(() => _isSubmitting = true);
    try {
      await ref.read(authStateProvider.notifier).completeOnboarding({
        if (_selectedGrade != null) 'grade': _selectedGrade,
        if (_selectedProvince != null) 'province': _selectedProvince,
        if (_selectedFields.isNotEmpty)
          'preferred_fields': _selectedFields.toList(),
        if (_selectedStudyProvinces.isNotEmpty)
          'preferred_study_provinces': _selectedStudyProvinces.toList(),
        if (_careerCtrl.text.trim().isNotEmpty)
          'dream_career': _careerCtrl.text.trim(),
      });
      if (mounted) context.go(scanNow ? '/scanner' : '/home');
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

  /// Bullet row used in the "Add reports" final step.
  Widget _bullet(String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.only(top: 6, right: 8),
            child: Icon(Icons.check_circle,
                color: AppColors.primary, size: 14),
          ),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                  fontSize: 13.5,
                  color: AppColors.textPrimary,
                  height: 1.4),
            ),
          ),
        ],
      ),
    );
  }

  /// Multi-select variant — toggles membership in [selected] set.
  Widget _buildMultiChip(String label, String value, Set<String> selected) {
    return _chipBody(
      label,
      selected.contains(value),
      () => setState(() {
        if (!selected.add(value)) selected.remove(value);
      }),
    );
  }

  Widget _buildChip(String label, String value, String? selected, void Function(String) onSelect) {
    return _chipBody(label, selected == value,
        () => setState(() => onSelect(value)));
  }

  Widget _chipBody(String label, bool isSelected, VoidCallback onTap) {
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: onTap,
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

                  // Page 3 — Field (multi-select)
                  _StepPage(
                    emoji: '📚',
                    title: 'What fields interest you?',
                    subtitle: 'Pick one or more — tap again to deselect',
                    child: Wrap(
                      spacing: 10,
                      runSpacing: 10,
                      children: AppConstants.studyFields.entries
                          .map((e) =>
                              _buildMultiChip(e.value, e.key, _selectedFields))
                          .toList(),
                    ),
                  ),

                  // Page 4 — Study province (multi-select)
                  _StepPage(
                    emoji: '🏫',
                    title: 'Where do you want to study?',
                    subtitle: 'Pick one or more provinces',
                    child: Wrap(
                      spacing: 10,
                      runSpacing: 10,
                      children: AppConstants.provinces.entries
                          .map((e) => _buildMultiChip(
                              e.value, e.key, _selectedStudyProvinces))
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

                  // Page 6 — Add reports (final step). Encourages the
                  // user to scan their report card now so the rest of
                  // the app (APS, course matching, recommendations) is
                  // useful from the very first home-screen view.
                  _StepPage(
                    emoji: '📄',
                    title: 'Add your report card',
                    subtitle:
                        "We'll calculate your APS and match you to courses, bursaries, and accommodation that fit your marks.",
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Container(
                          padding: const EdgeInsets.all(20),
                          decoration: BoxDecoration(
                            color: AppColors.primaryLight,
                            borderRadius: BorderRadius.circular(14),
                            border:
                                Border.all(color: AppColors.primary.withOpacity(0.25)),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Row(
                                children: [
                                  Icon(Icons.bolt,
                                      color: AppColors.primary, size: 20),
                                  SizedBox(width: 8),
                                  Text("Why it's worth doing now",
                                      style: TextStyle(
                                          fontSize: 14,
                                          fontWeight: FontWeight.w800,
                                          color: AppColors.primary)),
                                ],
                              ),
                              const SizedBox(height: 10),
                              _bullet('Instant APS — scanned in seconds.'),
                              _bullet(
                                  'Courses you qualify for show up first on the home screen.'),
                              _bullet(
                                  'Get tailored Next Steps and bursary matches.'),
                            ],
                          ),
                        ),
                        const SizedBox(height: 14),
                        Text(
                          "You can also do this later from the home screen — but the app is way more useful with your marks in.",
                          style: TextStyle(
                            fontSize: 12.5,
                            color: AppColors.textHint,
                            height: 1.45,
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ],
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
                    label: _currentPage == _totalPages - 1
                        ? 'Scan my report'
                        : 'Continue',
                    isLoading: _isSubmitting,
                    onPressed: _canProceed
                        ? (_currentPage == _totalPages - 1
                            ? () => _complete(scanNow: true)
                            : _next)
                        : null,
                  ),
                  // Skip option only appears on the final "Add reports"
                  // page — let the user enter the home screen without
                  // scanning yet if they want to look around first.
                  if (_currentPage == _totalPages - 1)
                    Padding(
                      padding: const EdgeInsets.only(top: 10),
                      child: TextButton(
                        onPressed:
                            _isSubmitting ? null : () => _complete(scanNow: false),
                        child: const Text(
                          "Skip for now",
                          style: TextStyle(
                            color: AppColors.textSecondary,
                            fontWeight: FontWeight.w600,
                            fontSize: 13,
                          ),
                        ),
                      ),
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
