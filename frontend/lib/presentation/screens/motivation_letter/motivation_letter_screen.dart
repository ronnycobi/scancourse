import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:share_plus/share_plus.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/services/api/api_client.dart';
import '../../widgets/common/app_text_field.dart';
import '../../widgets/common/loading_button.dart';

class MotivationLetterScreen extends ConsumerStatefulWidget {
  const MotivationLetterScreen({super.key});

  @override
  ConsumerState<MotivationLetterScreen> createState() => _MotivationLetterScreenState();
}

class _MotivationLetterScreenState extends ConsumerState<MotivationLetterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _course = TextEditingController();
  final _institution = TextEditingController();
  final _background = TextEditingController();
  final _achievements = TextEditingController();
  final _whyCourse = TextEditingController();
  final _whyInstitution = TextEditingController();
  String _tone = 'professional';

  String? _generatedLetter;
  int? _letterId;
  bool _isGenerating = false;
  bool _isRefining = false;

  @override
  void dispose() {
    for (final c in [_course, _institution, _background, _achievements, _whyCourse, _whyInstitution]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _generate() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() { _isGenerating = true; _generatedLetter = null; });

    try {
      final resp = await ApiClient.instance.post('/ai/motivation-letters/generate/', data: {
        'course_name': _course.text.trim(),
        'institution_name': _institution.text.trim(),
        'student_background': _background.text.trim(),
        'key_achievements': _achievements.text.trim(),
        'why_this_course': _whyCourse.text.trim(),
        'why_this_institution': _whyInstitution.text.trim(),
        'tone': _tone,
      });
      setState(() {
        _generatedLetter = resp.data['content'];
        _letterId = resp.data['id'];
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Generation failed: $e'), backgroundColor: AppColors.error),
        );
      }
    } finally {
      if (mounted) setState(() => _isGenerating = false);
    }
  }

  Future<void> _refine() async {
    if (_letterId == null) return;
    final feedback = await showDialog<String>(
      context: context,
      builder: (ctx) {
        final ctrl = TextEditingController();
        return AlertDialog(
          title: const Text('What should we change?'),
          content: TextField(
            controller: ctrl,
            maxLines: 4,
            decoration: const InputDecoration(
              hintText: 'e.g. Make it more confident · Mention my volunteer work · Shorten it',
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () => Navigator.pop(ctx, ctrl.text.trim()),
              child: const Text('Refine'),
            ),
          ],
        );
      },
    );

    if (feedback == null || feedback.isEmpty) return;
    setState(() => _isRefining = true);

    try {
      final resp = await ApiClient.instance.post(
        '/ai/motivation-letters/$_letterId/refine/',
        data: {'feedback': feedback},
      );
      setState(() => _generatedLetter = resp.data['content']);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Refine failed: $e'), backgroundColor: AppColors.error),
        );
      }
    } finally {
      if (mounted) setState(() => _isRefining = false);
    }
  }

  void _copy() {
    if (_generatedLetter == null) return;
    Clipboard.setData(ClipboardData(text: _generatedLetter!));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Copied to clipboard ✓')),
    );
  }

  void _share() {
    if (_generatedLetter == null) return;
    Share.share(_generatedLetter!, subject: 'Motivation Letter — ${_course.text}');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Motivation Letter')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(colors: [AppColors.primary, AppColors.secondary]),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.auto_awesome, color: Colors.white, size: 32),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('AI Motivation Letter Helper',
                                style: Theme.of(context).textTheme.titleLarge?.copyWith(color: Colors.white)),
                            Text('Powered by Gemini · Tailored for SA universities',
                                style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.white70)),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                AppTextField(
                  label: 'Course / Programme',
                  hint: 'e.g. BCom Accounting',
                  controller: _course,
                  validator: (v) => v != null && v.isNotEmpty ? null : 'Required',
                ),
                const SizedBox(height: 14),
                AppTextField(
                  label: 'Institution',
                  hint: 'e.g. University of Cape Town',
                  controller: _institution,
                  validator: (v) => v != null && v.isNotEmpty ? null : 'Required',
                ),
                const SizedBox(height: 14),
                AppTextField(
                  label: 'Tell us about yourself',
                  hint: 'School, family background, aspirations...',
                  controller: _background,
                  maxLines: 4,
                  validator: (v) => v != null && v.length >= 30 ? null : 'At least 30 characters',
                ),
                const SizedBox(height: 14),
                AppTextField(
                  label: 'Key achievements (optional)',
                  hint: 'Awards, leadership, top marks, hackathons...',
                  controller: _achievements,
                  maxLines: 3,
                ),
                const SizedBox(height: 14),
                AppTextField(
                  label: 'Why this course? (optional)',
                  hint: 'What draws you to this field?',
                  controller: _whyCourse,
                  maxLines: 3,
                ),
                const SizedBox(height: 14),
                AppTextField(
                  label: 'Why this institution? (optional)',
                  hint: 'Reputation, location, specific programme...',
                  controller: _whyInstitution,
                  maxLines: 3,
                ),
                const SizedBox(height: 14),
                Text('Tone', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontSize: 14)),
                const SizedBox(height: 6),
                Wrap(spacing: 8, runSpacing: 8, children: [
                  for (final t in const [
                    {'v': 'professional', 'l': 'Professional'},
                    {'v': 'warm', 'l': 'Warm & Personal'},
                    {'v': 'confident', 'l': 'Confident'},
                    {'v': 'humble', 'l': 'Humble & Earnest'},
                  ])
                    ChoiceChip(
                      label: Text(t['l']!),
                      selected: _tone == t['v'],
                      onSelected: (_) => setState(() => _tone = t['v']!),
                    ),
                ]),

                const SizedBox(height: 24),
                LoadingButton(
                  label: _generatedLetter == null ? 'Generate Letter' : 'Regenerate',
                  isLoading: _isGenerating,
                  onPressed: _generate,
                ),

                if (_generatedLetter != null) ...[
                  const SizedBox(height: 28),
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      border: Border.all(color: AppColors.border),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.description_outlined, color: AppColors.primary),
                            const SizedBox(width: 8),
                            Text('Your Letter', style: Theme.of(context).textTheme.titleMedium),
                            const Spacer(),
                            IconButton(
                              icon: const Icon(Icons.copy, size: 20),
                              onPressed: _copy,
                              tooltip: 'Copy',
                            ),
                            IconButton(
                              icon: const Icon(Icons.share, size: 20),
                              onPressed: _share,
                              tooltip: 'Share',
                            ),
                          ],
                        ),
                        const Divider(),
                        const SizedBox(height: 8),
                        SelectableText(
                          _generatedLetter!,
                          style: Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.6),
                        ),
                        const SizedBox(height: 16),
                        OutlinedButton.icon(
                          onPressed: _isRefining ? null : _refine,
                          icon: _isRefining
                              ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2))
                              : const Icon(Icons.auto_fix_high),
                          label: const Text('Refine with feedback'),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
