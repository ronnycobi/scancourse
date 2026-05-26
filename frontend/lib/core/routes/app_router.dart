import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../presentation/screens/auth/login_screen.dart';
import '../../presentation/screens/auth/register_screen.dart';
import '../../presentation/screens/auth/forgot_password_screen.dart';
import '../../presentation/screens/auth/reset_password_screen.dart';
import '../../presentation/screens/onboarding/onboarding_screen.dart';
import '../../presentation/screens/onboarding/splash_screen.dart';
import '../../presentation/screens/home/home_screen.dart';
import '../../presentation/screens/scanner/scanner_screen.dart';
import '../../presentation/screens/scanner/manual_entry_screen.dart';
import '../../presentation/screens/scanner/reports_screen.dart';
import '../../presentation/screens/scanner/results_screen.dart';
import '../../presentation/screens/scanner/report_edit_screen.dart';
import '../../presentation/screens/scanner/improvement_plan_screen.dart';
import '../../presentation/screens/courses/courses_screen.dart';
import '../../presentation/screens/courses/course_detail_screen.dart';
import '../../presentation/screens/bursaries/bursaries_screen.dart';
import '../../presentation/screens/bursaries/bursary_detail_screen.dart';
import '../../presentation/screens/accommodation/accommodation_screen.dart';
import '../../presentation/screens/accommodation/accommodation_detail_screen.dart';
import '../../presentation/screens/ai_assistant/ai_assistant_screen.dart';
import '../../presentation/screens/profile/profile_screen.dart';
import '../../presentation/screens/motivation_letter/motivation_letter_screen.dart';
import '../../presentation/screens/outcomes/outcomes_screen.dart';
import '../../presentation/screens/profile/edit_profile_screen.dart';
import '../../presentation/screens/profile/change_password_screen.dart';
import '../../presentation/screens/settings/settings_screen.dart';
import '../../presentation/screens/notifications/notifications_screen.dart';
import '../../presentation/screens/saved/saved_items_screen.dart';
import '../../presentation/screens/applications/applications_screen.dart';
import '../../presentation/screens/legal/legal_screen.dart';
import '../../presentation/screens/home/main_shell.dart';
import '../../providers/auth_provider.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authStateProvider);

  return GoRouter(
    initialLocation: '/splash',
    redirect: (context, state) {
      final isLoggedIn = authState.isAuthenticated;
      final isOnboarded = authState.isOnboarded;
      final location = state.matchedLocation;

      if (location == '/splash') return null;

      final authRoutes = ['/login', '/register', '/forgot-password', '/reset-password'];
      // Public routes that should be accessible without authentication.
      final publicPrefixes = ['/legal/'];
      final isPublic = publicPrefixes.any(location.startsWith);

      if (!isLoggedIn && !authRoutes.contains(location) && !isPublic) return '/login';
      if (isLoggedIn && authRoutes.contains(location)) return '/home';
      if (isLoggedIn && !isOnboarded && location != '/onboarding' && !isPublic) return '/onboarding';

      return null;
    },
    routes: [
      GoRoute(path: '/splash', builder: (_, __) => const SplashScreen()),
      GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
      GoRoute(path: '/register', builder: (_, __) => const RegisterScreen()),
      GoRoute(path: '/forgot-password', builder: (_, __) => const ForgotPasswordScreen()),
      GoRoute(
        path: '/reset-password',
        builder: (_, state) {
          final params = state.uri.queryParameters;
          return ResetPasswordScreen(
            initialUid: params['uid'],
            initialToken: params['token'],
          );
        },
      ),
      GoRoute(path: '/onboarding', builder: (_, __) => const OnboardingScreen()),
      ShellRoute(
        builder: (context, state, child) => MainShell(child: child),
        routes: [
          GoRoute(path: '/home', builder: (_, __) => const HomeScreen()),
          GoRoute(path: '/courses', builder: (_, __) => const CoursesScreen()),
          GoRoute(
            path: '/courses/:id',
            builder: (_, state) => CourseDetailScreen(id: int.parse(state.pathParameters['id']!)),
          ),
          GoRoute(path: '/bursaries', builder: (_, __) => const BursariesScreen()),
          GoRoute(
            path: '/bursaries/:id',
            builder: (_, state) => BursaryDetailScreen(id: int.parse(state.pathParameters['id']!)),
          ),
          GoRoute(path: '/accommodation', builder: (_, __) => const AccommodationScreen()),
          GoRoute(
            path: '/accommodation/:id',
            builder: (_, state) => AccommodationDetailScreen(id: int.parse(state.pathParameters['id']!)),
          ),
          GoRoute(path: '/ai', builder: (_, __) => const AiAssistantScreen()),
          GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen()),
        ],
      ),
      GoRoute(path: '/scanner', builder: (_, __) => const ScannerScreen()),
      GoRoute(path: '/manual-entry', builder: (_, __) => const ManualEntryScreen()),
      GoRoute(path: '/reports', builder: (_, __) => const ReportsScreen()),
      GoRoute(
        path: '/reports/:id',
        builder: (_, state) =>
            ReportEditScreen(reportId: int.parse(state.pathParameters['id']!)),
      ),
      GoRoute(
        path: '/results',
        builder: (_, state) => ResultsScreen(extra: state.extra as Map<String, dynamic>?),
      ),
      GoRoute(path: '/edit-profile', builder: (_, __) => const EditProfileScreen()),
      GoRoute(path: '/change-password', builder: (_, __) => const ChangePasswordScreen()),
      GoRoute(path: '/settings', builder: (_, __) => const SettingsScreen()),
      GoRoute(path: '/improvement-plan', builder: (_, __) => const ImprovementPlanScreen()),
      GoRoute(path: '/notifications', builder: (_, __) => const NotificationsScreen()),
      GoRoute(path: '/saved', builder: (_, __) => const SavedItemsScreen()),
      GoRoute(path: '/applications', builder: (_, __) => const ApplicationsScreen()),
      GoRoute(
        path: '/legal/:doc',
        builder: (_, state) => LegalScreen(docKey: state.pathParameters['doc']!),
      ),
      GoRoute(path: '/motivation-letter', builder: (_, __) => const MotivationLetterScreen()),
      GoRoute(
        path: '/outcomes/:courseId',
        builder: (_, state) => OutcomesScreen(courseId: int.parse(state.pathParameters['courseId']!)),
      ),
    ],
  );
});
