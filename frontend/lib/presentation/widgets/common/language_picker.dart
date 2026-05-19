import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../../../providers/locale_provider.dart';

class LanguagePicker extends ConsumerWidget {
  const LanguagePicker({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final locale = ref.watch(localeProvider);

    return ListTile(
      leading: const Icon(Icons.language, color: AppColors.primary),
      title: const Text('Language'),
      subtitle: Text(LocaleNotifier.languageNames[locale.languageCode] ?? 'English'),
      trailing: const Icon(Icons.arrow_forward_ios, size: 14),
      onTap: () async {
        final selected = await showModalBottomSheet<String>(
          context: context,
          builder: (_) => Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Padding(
                padding: EdgeInsets.all(16),
                child: Text('Choose Language', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
              ),
              ...LocaleNotifier.languageNames.entries.map((e) => ListTile(
                title: Text(e.value),
                trailing: locale.languageCode == e.key
                    ? const Icon(Icons.check, color: AppColors.primary)
                    : null,
                onTap: () => Navigator.pop(context, e.key),
              )),
            ],
          ),
        );
        if (selected != null) {
          await ref.read(localeProvider.notifier).setLanguage(selected);
        }
      },
    );
  }
}
