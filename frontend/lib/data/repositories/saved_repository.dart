import '../services/api/api_client.dart';

class SavedItemModel {
  final int id;
  final String itemType; // 'course' | 'bursary' | 'accommodation' | 'institution'
  final int itemId;
  final String? savedAt;
  /// Real display name of the underlying object (course name, bursary name,
  /// accommodation name…). Null if the backend couldn't resolve it.
  final String? itemName;
  /// A small secondary line (e.g. course field, bursary provider, city).
  final String? itemSubtitle;

  SavedItemModel.fromJson(Map<String, dynamic> j)
      : id = j['id'] as int,
        itemType = j['item_type'] as String,
        itemId = j['item_id'] as int,
        savedAt = j['saved_at'] as String?,
        itemName = j['item_name'] as String?,
        itemSubtitle = j['item_subtitle'] as String?;
}

class SavedRepository {
  final ApiClient _api = ApiClient.instance;

  Future<List<SavedItemModel>> list() async {
    final resp = await _api.get('/auth/saved/').timeout(
          const Duration(seconds: 15),
          onTimeout: () => throw Exception('Request timed out.'),
        );
    final list = (resp.data['results'] ?? resp.data) as List;
    return list
        .map((e) => SavedItemModel.fromJson(Map<String, dynamic>.from(e)))
        .toList();
  }

  Future<void> save(String itemType, int itemId) async {
    await _api.post('/auth/saved/', data: {
      'item_type': itemType,
      'item_id': itemId,
    });
  }

  Future<void> unsave(int savedId) async {
    await _api.delete('/auth/saved/$savedId/');
  }
}
