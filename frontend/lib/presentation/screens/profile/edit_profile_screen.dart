import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/theme/app_theme.dart';
import '../../../providers/auth_provider.dart';
import '../../widgets/common/app_text_field.dart';
import '../../widgets/common/multi_select_sheet.dart';
import '../../widgets/common/error_banner.dart';
import '../../widgets/common/loading_button.dart';

class EditProfileScreen extends ConsumerStatefulWidget {
  const EditProfileScreen({super.key});

  @override
  ConsumerState<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends ConsumerState<EditProfileScreen> {
  static const _storage = FlutterSecureStorage();
  static const _imagePathKey = 'profile_image_path';

  final _firstNameCtrl = TextEditingController();
  final _lastNameCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  // Used for the "Add a career" text input inside the chip picker.
  final _careerInputCtrl = TextEditingController();

  String? _grade;
  String? _province;
  // Lists — users can pick MULTIPLE fields / study provinces / dream
  // careers. We keep these in sync with the new server-side plural
  // fields; the single-value variants on the backend will still get
  // populated from index [0] for legacy consumers.
  List<String> _preferredFields = [];
  List<String> _preferredStudyProvinces = [];
  List<String> _dreamCareers = [];

  File? _pickedImage;
  bool _isSaving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _prefillFromUser();
    _loadStoredImage();
  }

  // Strip any leading +27 / 27 / 0 so the field shows the local 9 digits.
  String _localPhoneFrom(String? raw) {
    if (raw == null) return '';
    var s = raw.replaceAll(RegExp(r'[\s\-()]'), '');
    if (s.startsWith('+27')) s = s.substring(3);
    else if (s.startsWith('27') && s.length > 9) s = s.substring(2);
    else if (s.startsWith('0')) s = s.substring(1);
    return s;
  }

  void _prefillFromUser() {
    final user = ref.read(authStateProvider).user;
    if (user == null) return;
    _firstNameCtrl.text = user.firstName;
    _lastNameCtrl.text = user.lastName;
    _phoneCtrl.text = _localPhoneFrom(user.phoneNumber);
    _grade = user.grade;
    _province = user.province;
    // Prefer plural lists, fall back to singular for users created
    // before the migration.
    _preferredFields = user.preferredFields.isNotEmpty
        ? List.of(user.preferredFields)
        : (user.preferredField != null && user.preferredField!.isNotEmpty
            ? [user.preferredField!]
            : []);
    _preferredStudyProvinces = user.preferredStudyProvinces.isNotEmpty
        ? List.of(user.preferredStudyProvinces)
        : (user.preferredStudyProvince != null &&
                user.preferredStudyProvince!.isNotEmpty
            ? [user.preferredStudyProvince!]
            : []);
    _dreamCareers = user.dreamCareers.isNotEmpty
        ? List.of(user.dreamCareers)
        : (user.dreamCareer != null && user.dreamCareer!.isNotEmpty
            ? [user.dreamCareer!]
            : []);
  }

  Future<void> _loadStoredImage() async {
    final path = await _storage.read(key: _imagePathKey);
    if (path != null && File(path).existsSync()) {
      setState(() => _pickedImage = File(path));
    }
  }

  @override
  void dispose() {
    _firstNameCtrl.dispose();
    _lastNameCtrl.dispose();
    _phoneCtrl.dispose();
    _careerInputCtrl.dispose();

    super.dispose();
  }

  Future<void> _pickImage(ImageSource source) async {
    Navigator.of(context).pop();
    final picker = ImagePicker();
    final xFile = await picker.pickImage(source: source, imageQuality: 85);
    if (xFile == null) return;
    await _storage.write(key: _imagePathKey, value: xFile.path);
    setState(() => _pickedImage = File(xFile.path));
  }

  void _showImageSourceSheet() {
    showModalBottomSheet<void>(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 8),
            Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: AppColors.border,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(height: 16),
            ListTile(
              leading: const Icon(Icons.photo_library_outlined, color: AppColors.primary),
              title: const Text('Choose from Gallery'),
              onTap: () => _pickImage(ImageSource.gallery),
            ),
            ListTile(
              leading: const Icon(Icons.camera_alt_outlined, color: AppColors.primary),
              title: const Text('Take a Photo'),
              onTap: () => _pickImage(ImageSource.camera),
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  Future<void> _showPickerSheet<T>({
    required String title,
    required Map<String, String> options,
    required T? currentValue,
    required void Function(T?) onSelected,
  }) async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => DraggableScrollableSheet(
        initialChildSize: 0.55,
        minChildSize: 0.35,
        maxChildSize: 0.85,
        expand: false,
        builder: (_, scrollController) => Column(
          children: [
            const SizedBox(height: 8),
            Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: AppColors.border,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(height: 12),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                  if (currentValue != null)
                    TextButton(
                      onPressed: () {
                        onSelected(null);
                        Navigator.of(context).pop();
                      },
                      child: const Text('Clear', style: TextStyle(color: AppColors.error)),
                    ),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: ListView(
                controller: scrollController,
                children: options.entries.map((entry) {
                  final isSelected = currentValue == entry.key;
                  return ListTile(
                    title: Text(entry.value),
                    trailing: isSelected
                        ? const Icon(Icons.check_circle_rounded, color: AppColors.primary)
                        : null,
                    tileColor: isSelected ? AppColors.primaryLight.withOpacity(0.4) : null,
                    onTap: () {
                      onSelected(entry.key as T);
                      Navigator.of(context).pop();
                    },
                  );
                }).toList(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _save() async {
    setState(() {
      _isSaving = true;
      _error = null;
    });
    try {
      final data = <String, dynamic>{};

      final firstName = _firstNameCtrl.text.trim();
      final lastName = _lastNameCtrl.text.trim();
      final phone = _phoneCtrl.text.trim();

      if (firstName.isEmpty) {
        setState(() {
          _isSaving = false;
          _error = 'First name can\'t be empty.';
        });
        return;
      }
      if (lastName.isEmpty) {
        setState(() {
          _isSaving = false;
          _error = 'Last name can\'t be empty.';
        });
        return;
      }

      data['first_name'] = firstName;
      data['last_name'] = lastName;
      if (phone.isNotEmpty) {
        final digits = phone.replaceAll(RegExp(r'\D'), '');
        if (digits.length != 9) {
          setState(() {
            _isSaving = false;
            _error = 'Phone number must be 9 digits after +27 (e.g. 812345678).';
          });
          return;
        }
        data['phone_number'] = '+27$digits';
      } else {
        // explicitly clear if user cleared the field
        data['phone_number'] = '';
      }
      data['grade'] = _grade;
      data['province'] = _province;
      // Send the new plural fields. The serializer also syncs the singular
      // versions to the first item so legacy code keeps working.
      data['preferred_fields'] = _preferredFields;
      data['preferred_study_provinces'] = _preferredStudyProvinces;
      data['dream_careers'] = _dreamCareers;

      await ref.read(authStateProvider.notifier).updateProfile(data);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Profile saved'),
            backgroundColor: AppColors.eligible,
          ),
        );
        context.pop();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = ref.read(authStateProvider).error ??
              'Could not save your profile. Please try again.';
        });
      }
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authStateProvider).user;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Edit Profile'),
        actions: [
          IconButton(
            icon: const Icon(Icons.check_rounded),
            onPressed: _isSaving ? null : _save,
            tooltip: 'Save',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).padding.bottom + 48),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (_error != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
                child: ErrorBanner(
                  message: _error,
                  onDismiss: () => setState(() => _error = null),
                ),
              ),
            // Avatar
            Center(
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 28),
                child: GestureDetector(
                  onTap: _showImageSourceSheet,
                  child: Stack(
                    alignment: Alignment.bottomRight,
                    children: [
                      CircleAvatar(
                        radius: 80,
                        backgroundColor: AppColors.primaryLight,
                        backgroundImage: _pickedImage != null ? FileImage(_pickedImage!) : null,
                        child: _pickedImage == null
                            ? Text(
                                user?.firstName.isNotEmpty == true
                                    ? user!.firstName[0].toUpperCase()
                                    : 'S',
                                style: const TextStyle(
                                  fontSize: 56,
                                  fontWeight: FontWeight.w700,
                                  color: AppColors.primary,
                                ),
                              )
                            : null,
                      ),
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: const BoxDecoration(
                          color: AppColors.primary,
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.camera_alt_rounded, size: 20, color: Colors.white),
                      ),
                    ],
                  ),
                ),
              ),
            ),

            // Personal Info section
            _SectionHeader(title: 'Personal Info'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.border),
                ),
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    AppTextField(
                      label: 'First Name',
                      hint: 'Enter your first name',
                      controller: _firstNameCtrl,
                      prefixIcon: Icons.person_outline,
                    ),
                    const SizedBox(height: 16),
                    AppTextField(
                      label: 'Last Name',
                      hint: 'Enter your last name',
                      controller: _lastNameCtrl,
                      prefixIcon: Icons.person_outline,
                    ),
                    const SizedBox(height: 16),
                    AppTextField(
                      label: 'Phone Number',
                      hint: '81 234 5678',
                      controller: _phoneCtrl,
                      keyboardType: TextInputType.phone,
                      prefixText: '+27 ',
                      validator: (v) {
                        if (v == null || v.trim().isEmpty) return null;
                        final digits = v.replaceAll(RegExp(r'\D'), '');
                        if (digits.length != 9) {
                          return 'Enter 9 digits after +27 (e.g. 812345678)';
                        }
                        return null;
                      },
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 20),

            // Academic Profile section
            _SectionHeader(title: 'Academic Profile'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.border),
                ),
                child: Column(
                  children: [
                    _PickerTile(
                      icon: Icons.school_outlined,
                      label: 'Grade',
                      value: _grade != null ? AppConstants.grades[_grade] ?? _grade! : null,
                      onTap: () => _showPickerSheet<String>(
                        title: 'Select Grade',
                        options: AppConstants.grades,
                        currentValue: _grade,
                        onSelected: (v) => setState(() => _grade = v),
                      ),
                    ),
                    const Divider(height: 1, indent: 56),
                    _PickerTile(
                      icon: Icons.location_on_outlined,
                      label: 'Province',
                      value: _province != null ? AppConstants.provinces[_province] ?? _province! : null,
                      onTap: () => _showPickerSheet<String>(
                        title: 'Select Province',
                        options: AppConstants.provinces,
                        currentValue: _province,
                        onSelected: (v) => setState(() => _province = v),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 20),

            // ── Interested Fields (multi-select) ──────────────────────
            _SectionHeader(title: 'Interested Fields'),
            _MultiSelectCard(
              icon: Icons.category_outlined,
              prompt: _preferredFields.isEmpty
                  ? 'Pick the study fields you\'re curious about'
                  : 'Tap to edit your interested fields',
              labels: _preferredFields
                  .map((k) => AppConstants.studyFields[k] ?? k)
                  .toList(),
              onTap: () async {
                final result = await MultiSelectSheet.show(
                  context,
                  title: 'Interested fields',
                  subtitle: 'Pick all that catch your eye',
                  options: AppConstants.studyFields,
                  initiallySelected: _preferredFields,
                  maxSelections: 5,
                );
                if (result != null) {
                  setState(() => _preferredFields = result);
                }
              },
              onRemove: (i) => setState(() => _preferredFields.removeAt(i)),
            ),

            const SizedBox(height: 20),

            // ── Preferred Study Provinces (multi-select) ──────────────
            _SectionHeader(title: 'Where would you study?'),
            _MultiSelectCard(
              icon: Icons.flight_outlined,
              prompt: _preferredStudyProvinces.isEmpty
                  ? 'Pick provinces you\'d consider studying in'
                  : 'Tap to edit your preferred study provinces',
              labels: _preferredStudyProvinces
                  .map((k) => AppConstants.provinces[k] ?? k)
                  .toList(),
              onTap: () async {
                final result = await MultiSelectSheet.show(
                  context,
                  title: 'Preferred study provinces',
                  subtitle: 'Pick any number you\'d be open to',
                  options: AppConstants.provinces,
                  initiallySelected: _preferredStudyProvinces,
                );
                if (result != null) {
                  setState(() => _preferredStudyProvinces = result);
                }
              },
              onRemove: (i) =>
                  setState(() => _preferredStudyProvinces.removeAt(i)),
            ),

            const SizedBox(height: 20),

            // ── Dream Careers (multi-select free text) ────────────────
            _SectionHeader(title: 'Dream Careers'),
            _DreamCareerEditor(
              careers: _dreamCareers,
              controller: _careerInputCtrl,
              onAdd: (c) {
                final t = c.trim();
                if (t.isEmpty || _dreamCareers.contains(t)) return;
                if (_dreamCareers.length >= 5) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text(
                        'You can list up to 5 dream careers.')),
                  );
                  return;
                }
                setState(() => _dreamCareers.add(t));
                _careerInputCtrl.clear();
              },
              onRemove: (i) =>
                  setState(() => _dreamCareers.removeAt(i)),
            ),

            const SizedBox(height: 28),

            // Save button
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: LoadingButton(
                label: 'Save Changes',
                isLoading: _isSaving,
                onPressed: _save,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;

  const _SectionHeader({required this.title});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 20, bottom: 8),
      child: Text(
        title,
        style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w600,
            ),
      ),
    );
  }
}

class _PickerTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String? value;
  final VoidCallback onTap;
  final bool isLast;

  const _PickerTile({
    required this.icon,
    required this.label,
    required this.onTap,
    this.value,
    this.isLast = false,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon, color: AppColors.primary),
      title: Text(
        label,
        style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textSecondary),
      ),
      subtitle: Text(
        value ?? 'Not set',
        style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: value != null ? AppColors.textPrimary : AppColors.textHint,
            ),
      ),
      trailing: const Icon(Icons.chevron_right_rounded, color: AppColors.textHint),
      onTap: onTap,
    );
  }
}

/// Card that shows the current multi-select selection as removable chips
/// and lets the user tap to open the picker.
class _MultiSelectCard extends StatelessWidget {
  final IconData icon;
  final String prompt;
  final List<String> labels;
  final VoidCallback onTap;
  final void Function(int index) onRemove;

  const _MultiSelectCard({
    required this.icon,
    required this.prompt,
    required this.labels,
    required this.onTap,
    required this.onRemove,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          children: [
            InkWell(
              onTap: onTap,
              borderRadius: BorderRadius.circular(16),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Container(
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(
                        color: AppColors.primaryLight,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Icon(icon,
                          color: AppColors.primary, size: 18),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        prompt,
                        style: const TextStyle(
                            fontSize: 14,
                            color: AppColors.textPrimary,
                            fontWeight: FontWeight.w600),
                      ),
                    ),
                    const Icon(Icons.add_circle_outline,
                        color: AppColors.primary, size: 22),
                  ],
                ),
              ),
            ),
            if (labels.isNotEmpty) ...[
              const Divider(height: 1, indent: 16, endIndent: 16),
              Padding(
                padding: const EdgeInsets.all(14),
                child: Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: List.generate(labels.length, (i) {
                    return InputChip(
                      label: Text(labels[i]),
                      onDeleted: () => onRemove(i),
                      backgroundColor: AppColors.primaryLight,
                      labelStyle: const TextStyle(
                          color: AppColors.primary,
                          fontWeight: FontWeight.w600,
                          fontSize: 12),
                      deleteIconColor: AppColors.primary,
                      side: BorderSide.none,
                      visualDensity: VisualDensity.compact,
                    );
                  }),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Free-text version for dream careers — add via keyboard, remove via chip.
class _DreamCareerEditor extends StatelessWidget {
  final List<String> careers;
  final TextEditingController controller;
  final void Function(String) onAdd;
  final void Function(int index) onRemove;

  const _DreamCareerEditor({
    required this.careers,
    required this.controller,
    required this.onAdd,
    required this.onRemove,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.border),
        ),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: controller,
                    textCapitalization: TextCapitalization.words,
                    decoration: const InputDecoration(
                      hintText: 'e.g. Software Engineer, Doctor…',
                      prefixIcon: Icon(Icons.star_outline,
                          color: AppColors.primary),
                    ),
                    onSubmitted: onAdd,
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton.icon(
                  onPressed: () => onAdd(controller.text),
                  icon: const Icon(Icons.add, size: 16),
                  label: const Text('Add'),
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(0, 44),
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                  ),
                ),
              ],
            ),
            if (careers.isNotEmpty) ...[
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: List.generate(careers.length, (i) {
                  return InputChip(
                    label: Text(careers[i]),
                    onDeleted: () => onRemove(i),
                    backgroundColor: AppColors.accentLight,
                    labelStyle: const TextStyle(
                        color: AppColors.accent,
                        fontWeight: FontWeight.w600,
                        fontSize: 12),
                    deleteIconColor: AppColors.accent,
                    side: BorderSide.none,
                    visualDensity: VisualDensity.compact,
                  );
                }),
              ),
            ] else
              const Padding(
                padding: EdgeInsets.only(top: 8),
                child: Text(
                  'List 1 to 5 careers you\'re aiming for. Helps the AI tailor better recommendations.',
                  style: TextStyle(
                      fontSize: 12,
                      color: AppColors.textSecondary,
                      fontStyle: FontStyle.italic),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
