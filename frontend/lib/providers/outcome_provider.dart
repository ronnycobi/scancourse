import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/models/outcome_model.dart';
import '../data/services/api/api_client.dart';

final courseOutcomeProvider = FutureProvider.family<OutcomeData?, int>((ref, courseId) async {
  try {
    final resp = await ApiClient.instance.get('/outcomes/courses/$courseId/');
    final primary = resp.data['primary'];
    if (primary == null) return null;
    return OutcomeData.fromJson(Map<String, dynamic>.from(primary));
  } catch (_) {
    return null;
  }
});

final topPayingProvider = FutureProvider.family<List<dynamic>, String>((ref, level) async {
  final resp = await ApiClient.instance.get('/outcomes/top-paying/', queryParams: {'level': level});
  return resp.data as List;
});
