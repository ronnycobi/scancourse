import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/services/api/api_client.dart';

/// One card in the "For You" feed. Server returns ranked items with a
/// fixed shape — we just map type → icon + accent → colour.
class FeedItem {
  final String id;
  final String type;
  final int priority;
  final String? icon;
  final String accent;
  final String title;
  final String? body;
  final String? cta;
  final String? deepLink;

  FeedItem.fromJson(Map<String, dynamic> j)
      : id = (j['id'] ?? '').toString(),
        type = (j['type'] as String?) ?? 'tip',
        priority = (j['priority'] as num?)?.toInt() ?? 0,
        icon = j['icon'] as String?,
        accent = (j['accent'] as String?) ?? 'primary',
        title = (j['title'] as String?) ?? '',
        body = j['body'] as String?,
        cta = j['cta'] as String?,
        deepLink = j['deep_link'] as String?;
}

final homeFeedProvider = FutureProvider<List<FeedItem>>((ref) async {
  try {
    final resp = await ApiClient.instance.get('/auth/feed/').timeout(
      const Duration(seconds: 12),
      onTimeout: () => throw Exception('Request timed out.'),
    );
    final list = (resp.data['items'] ?? []) as List;
    return list
        .map((e) => FeedItem.fromJson(Map<String, dynamic>.from(e as Map)))
        .toList();
  } catch (_) {
    return <FeedItem>[];
  }
});

/// Renders one feed card. Tap → navigate.
class FeedCard extends StatelessWidget {
  final FeedItem item;
  const FeedCard({super.key, required this.item});

  IconData get _icon {
    switch (item.icon) {
      case 'bursary':
        return Icons.card_giftcard_outlined;
      case 'course':
        return Icons.school_outlined;
      case 'school':
        return Icons.school_outlined;
      case 'trending_up':
        return Icons.trending_up_rounded;
      case 'celebration':
        return Icons.celebration_rounded;
      case 'person':
        return Icons.person_outline;
      case 'deadline':
        return Icons.event_outlined;
      case 'tip':
      default:
        return Icons.lightbulb_outline;
    }
  }

  Color get _accentColor {
    switch (item.accent) {
      case 'error':
        return AppColors.error;
      case 'accent':
        return AppColors.accent;
      case 'success':
        return AppColors.eligible;
      case 'secondary':
        return AppColors.secondary;
      case 'primary':
      default:
        return AppColors.primary;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _accentColor;
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        onTap: () {
          if (item.deepLink != null && item.deepLink!.isNotEmpty) {
            context.push(item.deepLink!);
          }
        },
        borderRadius: BorderRadius.circular(14),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppColors.border),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.13),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(_icon, color: color, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.title,
                      style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w800,
                          color: AppColors.textPrimary,
                          height: 1.25),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (item.body != null && item.body!.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(
                        item.body!,
                        style: const TextStyle(
                            fontSize: 12.5,
                            color: AppColors.textSecondary,
                            height: 1.4),
                        maxLines: 3,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                    if (item.cta != null && item.cta!.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Text(
                            item.cta!,
                            style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                                color: color),
                          ),
                          const SizedBox(width: 2),
                          Icon(Icons.arrow_forward_rounded,
                              size: 14, color: color),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
