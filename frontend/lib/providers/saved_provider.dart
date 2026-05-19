import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/repositories/saved_repository.dart';

final savedRepositoryProvider = Provider((_) => SavedRepository());

final savedItemsProvider =
    FutureProvider<List<SavedItemModel>>((ref) async {
  return ref.read(savedRepositoryProvider).list();
});

/// Quick lookup: is (type, id) saved? Used by detail-screen heart icons.
final savedLookupProvider =
    FutureProvider.family<int?, String>((ref, key) async {
  // key format: "course:42"
  final items = await ref.watch(savedItemsProvider.future);
  final parts = key.split(':');
  if (parts.length != 2) return null;
  final type = parts[0];
  final id = int.tryParse(parts[1]);
  if (id == null) return null;
  for (final s in items) {
    if (s.itemType == type && s.itemId == id) return s.id;
  }
  return null;
});
