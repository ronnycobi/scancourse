import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/services/api/api_client.dart';

/// Reusable bell-with-badge button. Polls `/notifications/unread-count/`
/// every time it's rebuilt and shows a red badge with the count.
final unreadCountProvider = FutureProvider<int>((ref) async {
  try {
    final resp = await ApiClient.instance.get('/notifications/unread-count/');
    final d = resp.data;
    if (d is Map && d['count'] is int) return d['count'] as int;
    if (d is Map && d['count'] is num) return (d['count'] as num).toInt();
    return 0;
  } catch (_) {
    return 0;
  }
});

class NotificationBell extends ConsumerWidget {
  const NotificationBell({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final count = ref.watch(unreadCountProvider).valueOrNull ?? 0;
    return Stack(
      clipBehavior: Clip.none,
      children: [
        IconButton(
          icon: const Icon(Icons.notifications_outlined),
          tooltip: 'Notifications',
          onPressed: () async {
            await context.push('/notifications');
            // refresh count when returning
            ref.invalidate(unreadCountProvider);
          },
        ),
        if (count > 0)
          Positioned(
            right: 8,
            top: 8,
            child: Container(
              padding: EdgeInsets.symmetric(
                  horizontal: count > 9 ? 4 : 5, vertical: 1),
              constraints: const BoxConstraints(minWidth: 16, minHeight: 16),
              decoration: BoxDecoration(
                color: AppColors.error,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.white, width: 1.5),
              ),
              child: Text(
                count > 9 ? '9+' : '$count',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 9,
                  fontWeight: FontWeight.w800,
                  height: 1.1,
                ),
              ),
            ),
          ),
      ],
    );
  }
}
