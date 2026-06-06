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
  /// Per-type metadata from the backend (currently {deadline: ISO date}
  /// for bursaries). Empty map if the backend didn't provide any.
  final Map<String, dynamic> meta;

  /// Bursary deadline parsed from [meta], if present. Null otherwise.
  DateTime? get bursaryDeadline {
    final raw = meta['deadline'];
    if (raw is String && raw.isNotEmpty) return DateTime.tryParse(raw);
    return null;
  }

  SavedItemModel.fromJson(Map<String, dynamic> j)
      : id = j['id'] as int,
        itemType = j['item_type'] as String,
        itemId = j['item_id'] as int,
        savedAt = j['saved_at'] as String?,
        itemName = j['item_name'] as String?,
        itemSubtitle = j['item_subtitle'] as String?,
        meta = (j['meta'] is Map)
            ? Map<String, dynamic>.from(j['meta'] as Map)
            : const {};
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
