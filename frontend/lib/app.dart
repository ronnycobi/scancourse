import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme/app_theme.dart';
import 'core/routes/app_router.dart';
import 'providers/locale_provider.dart';
import 'data/services/push/push_service.dart';
import 'presentation/widgets/common/notification_bell.dart';

class ScancourseApp extends ConsumerStatefulWidget {
  const ScancourseApp({super.key});

  @override
  ConsumerState<ScancourseApp> createState() => _ScancourseAppState();
}

class _ScancourseAppState extends ConsumerState<ScancourseApp>
    with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    // Refresh the unread-count badge whenever a push arrives in the
    // foreground or the app is opened from a notification.
    PushService.instance.onInboxChanged = () {
      if (mounted) ref.invalidate(unreadCountProvider);
    };
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // Coming back to the app — a notification may have arrived while it
    // was backgrounded, so refresh the badge.
    if (state == AppLifecycleState.resumed) {
      ref.invalidate(unreadCountProvider);
    }
  }

  @override
  Widget build(BuildContext context) {
    final router = ref.watch(routerProvider);
    final locale = ref.watch(localeProvider);

    return MaterialApp.router(
      title: 'Scancourse',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      routerConfig: router,
      locale: locale,
      supportedLocales: LocaleNotifier.supportedLocales,
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
    );
  }
}
