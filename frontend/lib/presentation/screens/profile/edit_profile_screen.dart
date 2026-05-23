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
  final _dreamCareerCtrl = TextEditingController();

  String? _grade;
  String? _province;
  String? _preferredField;
  String? _preferredStudyProvince;

  File? _pickedImage;
  bool _isSaving = false;

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
    _dreamCareerCtrl.text = user.dreamCareer ?? '';
    _grade = user.grade;
    _province = user.province;
    _preferredField = user.preferredField;
    _preferredStudyProvince = user.preferredStudyProvince;
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
    _dreamCareerCtrl.dispose();
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
    setState(() => _isSaving = true);
    try {
      final data = <String, dynamic>{};

      final firstName = _firstNameCtrl.text.trim();
      final lastName = _lastNameCtrl.text.trim();
      final phone = _phoneCtrl.text.trim();
      final dreamCareer = _dreamCareerCtrl.text.trim();

      data['first_name'] = firstName;
      data['last_name'] = lastName;
      if (phone.isNotEmpty) {
        final digits = phone.replaceAll(RegExp(r'\D'), '');
        if (digits.length != 9) {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Phone number must be 9 digits after +27.'),
                backgroundColor: AppColors.error,
              ),
            );
          }
          setState(() => _isSaving = false);
          return;
        }
        data['phone_number'] = '+27$digits';
      } else {
        // explicitly clear if user cleared the field
        data['phone_number'] = '';
      }
      data['grade'] = _grade;
      data['province'] = _province;
      data['preferred_field'] = _preferredField;
      data['preferred_study_province'] = _preferredStudyProvince;
      data['dream_career'] = dreamCareer;

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
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(ref.read(authStateProvider).error ?? 'Failed to save profile.'),
            backgroundColor: AppColors.error,
          ),
        );
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
                    const Divider(height: 1, indent: 56),
                    _PickerTile(
                      icon: Icons.category_outlined,
                      label: 'Preferred Field',
                      value: _preferredField != null
                          ? AppConstants.studyFields[_preferredField] ?? _preferredField!
                          : null,
                      onTap: () => _showPickerSheet<String>(
                        title: 'Select Preferred Field',
                        options: AppConstants.studyFields,
                        currentValue: _preferredField,
                        onSelected: (v) => setState(() => _preferredField = v),
                      ),
                    ),
                    const Divider(height: 1, indent: 56),
                    _PickerTile(
                      icon: Icons.flight_outlined,
                      label: 'Preferred Study Province',
                      value: _preferredStudyProvince != null
                          ? AppConstants.provinces[_preferredStudyProvince] ?? _preferredStudyProvince!
                          : null,
                      isLast: true,
                      onTap: () => _showPickerSheet<String>(
                        title: 'Preferred Study Province',
                        options: AppConstants.provinces,
                        currentValue: _preferredStudyProvince,
                        onSelected: (v) => setState(() => _preferredStudyProvince = v),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 20),

            // Dream Career section
            _SectionHeader(title: 'Dream Career'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.border),
                ),
                padding: const EdgeInsets.all(16),
                child: AppTextField(
                  label: 'Dream Career',
                  hint: 'e.g. Software Engineer, Doctor, Lawyer…',
                  controller: _dreamCareerCtrl,
                  prefixIcon: Icons.star_outline,
                  maxLines: 2,
                ),
              ),
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
