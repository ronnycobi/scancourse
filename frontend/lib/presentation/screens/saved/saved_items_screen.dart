import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/repositories/saved_repository.dart';
import '../../../providers/saved_provider.dart';

class SavedItemsScreen extends ConsumerStatefulWidget {
  const SavedItemsScreen({super.key});

  @override
  ConsumerState<SavedItemsScreen> createState() => _SavedItemsScreenState();
}

class _SavedItemsScreenState extends ConsumerState<SavedItemsScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tab;
  static const _types = ['course', 'bursary', 'accommodation'];
  static const _labels = ['Courses', 'Bursaries', 'Accommodation'];

  @override
  void initState() {
    super.initState();
    _tab = TabController(length: _types.length, vsync: this);
  }

  @override
  void dispose() {
    _tab.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(savedItemsProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Saved'),
        leading: BackButton(onPressed: () => context.pop()),
        bottom: TabBar(
          controller: _tab,
          labelColor: AppColors.primary,
          unselectedLabelColor: AppColors.textSecondary,
          indicatorColor: AppColors.primary,
          tabs: _labels.map((l) => Tab(text: l)).toList(),
        ),
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.wifi_off_outlined,
                    size: 56, color: AppColors.textHint),
                const SizedBox(height: 12),
                Text('Could not load saved items',
                    style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 16),
                OutlinedButton(
                  onPressed: () => ref.invalidate(savedItemsProvider),
                  child: const Text('Retry'),
                ),
              ],
            ),
          ),
        ),
        data: (items) {
          return TabBarView(
            controller: _tab,
            children: _types
                .map((t) => _SavedTab(
                      items: items.where((i) => i.itemType == t).toList(),
                      itemType: t,
                    ))
                .toList(),
          );
        },
      ),
    );
  }
}

class _SavedTab extends ConsumerWidget {
  final List<SavedItemModel> items;
  final String itemType;
  const _SavedTab({required this.items, required this.itemType});

  IconData get _icon {
    switch (itemType) {
      case 'course':
        return Icons.school_outlined;
      case 'bursary':
        return Icons.card_giftcard_outlined;
      case 'accommodation':
        return Icons.home_outlined;
      default:
        return Icons.bookmark_outline;
    }
  }

  String get _route {
    switch (itemType) {
      case 'course':
        return '/courses';
      case 'bursary':
        return '/bursaries';
      case 'accommodation':
        return '/accommodation';
      default:
        return '/home';
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(_icon, size: 56, color: AppColors.textHint),
            const SizedBox(height: 16),
            Text('Nothing saved yet',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 32),
              child: Text(
                'Tap the bookmark icon on any item you want to come back to.',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppColors.textSecondary),
              ),
            ),
            const SizedBox(height: 16),
            OutlinedButton(
              onPressed: () => context.push(_route),
              child: const Text('Browse'),
            ),
          ],
        ),
      );
    }
    return ListView.separated(
      padding: const EdgeInsets.all(12),
      itemCount: items.length,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (_, i) {
        final item = items[i];
        return Dismissible(
          key: ValueKey(item.id),
          direction: DismissDirection.endToStart,
          background: Container(
            alignment: Alignment.centerRight,
            padding: const EdgeInsets.only(right: 20),
            color: AppColors.error,
            child: const Icon(Icons.delete_outline, color: Colors.white),
          ),
          onDismissed: (_) async {
            try {
              await ref.read(savedRepositoryProvider).unsave(item.id);
              ref.invalidate(savedItemsProvider);
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Removed from saved')),
                );
              }
            } catch (_) {}
          },
          child: ListTile(
            tileColor: Colors.white,
            shape: RoundedRectangleBorder(
              side: const BorderSide(color: AppColors.border),
              borderRadius: BorderRadius.circular(10),
            ),
            leading: CircleAvatar(
              backgroundColor: AppColors.primaryLight,
              child: Icon(_icon, color: AppColors.primary, size: 20),
            ),
            title: Text(
              item.itemName?.isNotEmpty == true
                  ? item.itemName!
                  : '${itemType[0].toUpperCase()}${itemType.substring(1)} #${item.itemId}',
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                if (item.itemSubtitle?.isNotEmpty == true)
                  Text(
                    item.itemSubtitle!,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                        fontSize: 12, color: AppColors.textSecondary),
                  ),
                if (item.savedAt != null)
                  Text(
                    'Saved ${item.savedAt!.substring(0, 10)}',
                    style: const TextStyle(
                        fontSize: 11, color: AppColors.textHint),
                  ),
              ],
            ),
            trailing: const Icon(Icons.arrow_forward_ios, size: 14),
            onTap: () => context.push('$_route/${item.itemId}'),
          ),
        );
      },
    );
  }
}
