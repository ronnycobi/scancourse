import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:file_picker/file_picker.dart';
import 'package:image_picker/image_picker.dart';
import '../../../core/theme/app_theme.dart';
import '../../../providers/aps_provider.dart';

class ScannerScreen extends ConsumerStatefulWidget {
  const ScannerScreen({super.key});

  @override
  ConsumerState<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends ConsumerState<ScannerScreen> {
  final ImagePicker _picker = ImagePicker();

  Future<void> _pickFromGallery() async {
    final result = await _picker.pickImage(source: ImageSource.gallery, imageQuality: 90);
    if (result != null) {
      await _uploadFile(File(result.path));
    }
  }

  Future<void> _pickFromCamera() async {
    final result = await _picker.pickImage(source: ImageSource.camera, imageQuality: 90);
    if (result != null) {
      await _uploadFile(File(result.path));
    }
  }

  static const _allowedExts = ['pdf', 'jpg', 'jpeg', 'png', 'heic'];

  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: _allowedExts,
    );
    if (result != null && result.files.single.path != null) {
      await _uploadFile(File(result.files.single.path!));
    }
  }

  Future<void> _uploadFile(File file) async {
    // Client-side guard so users get a clear message before the round-trip.
    final ext = file.path.split('.').last.toLowerCase();
    if (!_allowedExts.contains(ext)) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Unsupported file type ".$ext". Use PDF, JPG, PNG or HEIC.',
            ),
            backgroundColor: AppColors.error,
          ),
        );
      }
      return;
    }
    await ref.read(scannerProvider.notifier).uploadFile(file);
    if (mounted) {
      context.push('/results', extra: {'from': 'scanner'});
    }
  }

  @override
  Widget build(BuildContext context) {
    final scannerState = ref.watch(scannerProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Scan Report Card'),
        leading: const CloseButton(),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: scannerState.isUploading || scannerState.isProcessing
              ? _ProcessingView(isUploading: scannerState.isUploading)
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Upload your report card', style: Theme.of(context).textTheme.headlineMedium),
                    const SizedBox(height: 8),
                    Text(
                      'We\'ll automatically extract your subjects and calculate your APS score.',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                    const SizedBox(height: 40),
                    _UploadOption(
                      icon: Icons.camera_alt_outlined,
                      title: 'Take a Photo',
                      subtitle: 'Use your camera to scan the report card',
                      color: AppColors.primary,
                      onTap: _pickFromCamera,
                    ),
                    const SizedBox(height: 16),
                    _UploadOption(
                      icon: Icons.photo_library_outlined,
                      title: 'Choose from Gallery',
                      subtitle: 'Select a photo from your device',
                      color: AppColors.secondary,
                      onTap: _pickFromGallery,
                    ),
                    const SizedBox(height: 16),
                    _UploadOption(
                      icon: Icons.attach_file_outlined,
                      title: 'Upload File',
                      subtitle: 'Pick a PDF or image (JPG, PNG, HEIC)',
                      color: AppColors.accent,
                      onTap: _pickFile,
                    ),
                    const Spacer(),
                    OutlinedButton.icon(
                      onPressed: () => context.push('/manual-entry'),
                      icon: const Icon(Icons.edit_outlined),
                      label: const Text('Enter marks manually instead'),
                    ),
                    if (scannerState.error != null) ...[
                      const SizedBox(height: 16),
                      Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: AppColors.errorLight,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.error_outline, color: AppColors.error),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Text(scannerState.error!,
                                  style: const TextStyle(color: AppColors.error, fontSize: 13)),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
        ),
      ),
    );
  }
}

class _UploadOption extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  final VoidCallback onTap;

  const _UploadOption({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.border),
        ),
        child: Row(
          children: [
            Container(
              width: 52,
              height: 52,
              decoration: BoxDecoration(
                color: color.withOpacity(0.12),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Icon(icon, color: color, size: 26),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 2),
                  Text(subtitle, style: Theme.of(context).textTheme.bodySmall),
                ],
              ),
            ),
            const Icon(Icons.arrow_forward_ios, size: 14, color: AppColors.textHint),
          ],
        ),
      ),
    );
  }
}

class _ProcessingView extends StatelessWidget {
  final bool isUploading;

  const _ProcessingView({required this.isUploading});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const CircularProgressIndicator(strokeWidth: 3),
          const SizedBox(height: 24),
          Text(
            isUploading ? 'Uploading your report...' : 'Extracting subjects and marks...',
            style: Theme.of(context).textTheme.titleMedium,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'This usually takes 10-30 seconds',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}
