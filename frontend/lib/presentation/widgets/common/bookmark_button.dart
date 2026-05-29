import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../../../providers/saved_provider.dart';
import '../../../providers/course_provider.dart';
import '../../screens/accommodation/accommodation_screen.dart';

/// Heart icon that toggles a saved-item record on the backend.
/// Drop it into any AppBar's `actions` or a card row.
class BookmarkButton extends ConsumerWidget {
  final String itemType; // 'course' | 'bursary' | 'accommodation' | 'institution'
  final int itemId;
  final Color? activeColor;
  final Color? inactiveColor;
  final double size;

  const BookmarkButton({
    super.key,
    required this.itemType,
    required this.itemId,
    this.activeColor,
    this.inactiveColor,
    this.size = 22,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final lookup = ref.watch(savedLookupProvider('$itemType:$itemId'));
    final repo = ref.read(savedRepositoryProvider);

    Future<void> toggle() async {
      final savedId = lookup.valueOrNull;
      try {
        if (savedId == null) {
          await repo.save(itemType, itemId);
        } else {
          await repo.unsave(savedId);
        }
        ref.invalidate(savedItemsProvider);
        // Saving/unsaving a course changes the personalised ranking that
        // depends on saved courses — refresh accommodation (ranked by
        // saved-course institutions) and the recommendation feeds.
        if (itemType == 'course') {
          ref.invalidate(accommodationProvider);
          ref.invalidate(courseRecommendationsProvider);
        }
      } catch (_) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Could not update saved items.')),
          );
        }
      }
    }

    return lookup.when(
      loading: () => SizedBox(
        width: size + 16,
        height: size + 16,
        child: const Center(
          child: SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        ),
      ),
      error: (_, __) => IconButton(
        iconSize: size,
        icon: Icon(Icons.bookmark_border, color: inactiveColor),
        onPressed: toggle,
      ),
      data: (savedId) => IconButton(
        iconSize: size,
        tooltip: savedId == null ? 'Save' : 'Saved',
        icon: Icon(
          savedId == null ? Icons.bookmark_border : Icons.bookmark,
          color: savedId == null
              ? (inactiveColor ?? AppColors.textHint)
              : (activeColor ?? AppColors.primary),
        ),
        onPressed: toggle,
      ),
    );
  }
}
