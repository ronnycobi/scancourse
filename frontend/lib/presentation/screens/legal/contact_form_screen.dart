import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/services/api/api_client.dart';
import '../../widgets/common/app_text_field.dart';
import '../../widgets/common/error_banner.dart';
import '../../widgets/common/loading_button.dart';

/// Real-world Contact Us screen: a form (name / email / subject / message)
/// that POSTs to /api/v1/legal/contact/, which emails the submission to
/// info@scancourse.co.za. Mirrors the /legal/contact/ web page.
class ContactFormScreen extends StatefulWidget {
  const ContactFormScreen({super.key});

  @override
  State<ContactFormScreen> createState() => _ContactFormScreenState();
}

class _ContactFormScreenState extends State<ContactFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _messageCtrl = TextEditingController();

  String _subject = 'General';
  bool _busy = false;
  bool _sent = false;
  String? _error;

  static const _subjects = [
    'General',
    'Bug report',
    'Feature request',
    'Wrong data',
    'Privacy / POPIA',
    'Account issue',
    'Other',
  ];

  @override
  void dispose() {
    _nameCtrl.dispose();
    _emailCtrl.dispose();
    _messageCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() => _error = null);
    if (!_formKey.currentState!.validate()) return;
    setState(() => _busy = true);
    try {
      await ApiClient.instance.post('/legal/contact/', data: {
        'name': _nameCtrl.text.trim(),
        'email': _emailCtrl.text.trim(),
        'subject': _subject,
        'message': _messageCtrl.text.trim(),
      });
      if (mounted) setState(() => _sent = true);
    } catch (e) {
      if (mounted) {
        setState(() => _error =
            'Couldn\'t send your message. Check your connection or email info@scancourse.co.za directly.');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Contact Us'),
        leading: BackButton(onPressed: () => context.pop()),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: _sent ? _successView(context) : _formView(context),
        ),
      ),
    );
  }

  Widget _formView(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Get in touch',
              style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 8),
          const Text(
            'Bug reports, feature requests, privacy questions or just a wave hello — we read every message and reply within 2 business days.',
            style:
                TextStyle(fontSize: 14, color: AppColors.textSecondary),
          ),
          const SizedBox(height: 16),

          // Info card
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.primaryLight,
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Row(
              children: [
                Icon(Icons.email_outlined, color: AppColors.primary),
                SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Or email us directly: info@scancourse.co.za',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: AppColors.primary,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          ErrorBanner(
            message: _error,
            onDismiss: () => setState(() => _error = null),
          ),

          AppTextField(
            label: 'Your name',
            hint: 'Thandi Mokoena',
            controller: _nameCtrl,
            prefixIcon: Icons.person_outline,
            validator: (v) =>
                (v?.trim().isEmpty ?? true) ? 'Please enter your name' : null,
          ),
          const SizedBox(height: 16),
          AppTextField(
            label: 'Your email',
            hint: 'you@email.com',
            controller: _emailCtrl,
            keyboardType: TextInputType.emailAddress,
            prefixIcon: Icons.email_outlined,
            validator: (v) {
              final s = v?.trim() ?? '';
              if (s.isEmpty) return 'Please enter your email';
              if (!s.contains('@') || !s.contains('.')) {
                return 'Enter a valid email address';
              }
              return null;
            },
          ),
          const SizedBox(height: 16),

          // Subject dropdown — styled like our other fields
          const Text('Subject',
              style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary)),
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: BoxDecoration(
              border: Border.all(color: AppColors.border),
              borderRadius: BorderRadius.circular(12),
              color: Colors.white,
            ),
            child: DropdownButton<String>(
              value: _subject,
              isExpanded: true,
              underline: const SizedBox.shrink(),
              icon: const Icon(Icons.expand_more),
              items: _subjects
                  .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                  .toList(),
              onChanged: (v) => setState(() => _subject = v ?? 'General'),
            ),
          ),
          const SizedBox(height: 16),

          AppTextField(
            label: 'Message',
            hint: 'What\'s on your mind?',
            controller: _messageCtrl,
            maxLines: 6,
            prefixIcon: Icons.chat_bubble_outline,
            validator: (v) =>
                (v?.trim().isEmpty ?? true) ? 'Please write a message' : null,
          ),
          const SizedBox(height: 24),

          LoadingButton(
            label: 'Send message',
            isLoading: _busy,
            onPressed: _submit,
          ),
          const SizedBox(height: 12),
          Center(
            child: Text(
              'By sending you accept our Privacy Policy.',
              style: TextStyle(
                  fontSize: 11,
                  color: AppColors.textHint,
                  fontStyle: FontStyle.italic),
            ),
          ),
          const SizedBox(height: 8),
          Center(
            child: TextButton(
              onPressed: () => context.push('/legal/privacy'),
              child: const Text('Read Privacy Policy'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _successView(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 40),
      child: Column(
        children: [
          const Icon(Icons.mark_email_read_outlined,
              size: 80, color: AppColors.eligible),
          const SizedBox(height: 20),
          Text('Message sent',
              style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 8),
          const Text(
            'Thanks! We\'ll be in touch within 2 business days.',
            style: TextStyle(color: AppColors.textSecondary),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 32),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => context.pop(),
              child: const Text('Done'),
            ),
          ),
          const SizedBox(height: 8),
          TextButton(
            onPressed: () {
              setState(() {
                _sent = false;
                _nameCtrl.clear();
                _emailCtrl.clear();
                _messageCtrl.clear();
                _subject = 'General';
              });
            },
            child: const Text('Send another'),
          ),
        ],
      ),
    );
  }
}
