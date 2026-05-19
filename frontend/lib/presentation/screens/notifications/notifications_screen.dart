import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/services/api/api_client.dart';

class NotificationItem {
  final int id;
  final String type;
  final String title;
  final String body;
  final Map<String, dynamic>? data;
  final bool isRead;
  final String? sentAt;

  NotificationItem.fromJson(Map<String, dynamic> j)
      : id = j['id'] as int,
        type = (j['notification_type'] as String?) ?? 'info',
        title = (j['title'] as String?) ?? '',
        body = (j['body'] as String?) ?? '',
        data = (j['data'] as Map?)?.cast<String, dynamic>(),
        isRead = (j['is_read'] as bool?) ?? false,
        sentAt = j['sent_at'] as String?;
}

final notificationListProvider =
    FutureProvider<List<NotificationItem>>((ref) async {
  final resp =
      await ApiClient.instance.get('/notifications/').timeout(
    const Duration(seconds: 15),
    onTimeout: () =>
        throw Exception('Request timed out. Check your connection.'),
  );
  final list = (resp.data['results'] ?? resp.data) as List;
  return list
      .map((e) => NotificationItem.fromJson(Map<String, dynamic>.from(e)))
      .toList();
});

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(notificationListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        leading: BackButton(onPressed: () => context.pop()),
        actions: [
          IconButton(
            tooltip: 'Mark all as read',
            icon: const Icon(Icons.done_all_rounded),
            onPressed: () async {
              try {
                await ApiClient.instance
                    .post('/notifications/mark-read/', data: {'all': true});
                ref.invalidate(notificationListProvider);
              } catch (_) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Could not update.')),
                  );
                }
              }
            },
          ),
        ],
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.wifi_off_outlined,
                    size: 64, color: AppColors.textHint),
                const SizedBox(height: 16),
                Text('Could not load notifications',
                    style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                Text('Check your connection and try again',
                    style: Theme.of(context).textTheme.bodySmall),
                const SizedBox(height: 20),
                OutlinedButton(
                  onPressed: () => ref.invalidate(notificationListProvider),
                  child: const Text('Retry'),
                ),
              ],
            ),
          ),
        ),
        data: (items) {
          if (items.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.notifications_off_outlined,
                      size: 64, color: AppColors.textHint),
                  const SizedBox(height: 16),
                  Text('You\'re all caught up',
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  Text(
                    'New deadlines, matches and bursary alerts will show here.',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(notificationListProvider),
            child: ListView.separated(
              padding: const EdgeInsets.all(12),
              itemCount: items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (_, i) => _NotificationTile(item: items[i]),
            ),
          );
        },
      ),
    );
  }
}

class _NotificationTile extends StatelessWidget {
  final NotificationItem item;
  const _NotificationTile({required this.item});

  IconData get _icon {
    switch (item.type) {
      case 'deadline':
        return Icons.event_outlined;
      case 'match':
        return Icons.school_outlined;
      case 'bursary':
        return Icons.card_giftcard_outlined;
      case 'application':
        return Icons.assignment_outlined;
      default:
        return Icons.notifications_outlined;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: item.isRead ? Colors.white : AppColors.primaryLight.withOpacity(0.4),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(
            radius: 18,
            backgroundColor: AppColors.primaryLight,
            child: Icon(_icon, color: AppColors.primary, size: 18),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.title,
                    style: const TextStyle(
                        fontWeight: FontWeight.w600, fontSize: 14)),
                const SizedBox(height: 4),
                Text(item.body,
                    style: const TextStyle(
                        fontSize: 13, color: AppColors.textSecondary)),
              ],
            ),
          ),
          if (!item.isRead)
            Container(
              width: 8,
              height: 8,
              margin: const EdgeInsets.only(left: 8, top: 4),
              decoration: const BoxDecoration(
                  color: AppColors.primary, shape: BoxShape.circle),
            ),
        ],
      ),
    );
  }
}
