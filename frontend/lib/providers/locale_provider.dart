import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// English-only build. The multi-language plumbing is intentionally
/// stripped — no FlutterSecureStorage read, no backend sync, no isiZulu /
/// isiXhosa / Afrikaans / Sesotho options. Add them back when localised
/// strings + ARB files are ready.
class LocaleNotifier extends StateNotifier<Locale> {
  LocaleNotifier() : super(const Locale('en'));

  static const supportedLocales = [Locale('en')];
  static const languageNames = {'en': 'English'};

  Future<void> setLanguage(String code) async {
    // No-op — locked to English.
  }
}

final localeProvider = StateNotifierProvider<LocaleNotifier, Locale>(
  (ref) => LocaleNotifier(),
);
