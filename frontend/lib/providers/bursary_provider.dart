import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/services/api/api_client.dart';
import '../data/models/bursary_match_model.dart';

class BursaryStats {
  final int total;
  final int open;
  final int closed;
  final int closingSoon;
  final int? qualified;
  final int? checkDetails;
  final int? gradeGap;

  const BursaryStats({
    required this.total,
    required this.open,
    required this.closed,
    required this.closingSoon,
    this.qualified,
    this.checkDetails,
    this.gradeGap,
  });

  factory BursaryStats.fromJson(Map<String, dynamic> j) {
    final summary = (j['match_summary'] as Map?) ?? {};
    return BursaryStats(
      total: j['total'] as int? ?? 0,
      open: j['open'] as int? ?? 0,
      closed: j['closed'] as int? ?? 0,
      closingSoon: j['closing_soon'] as int? ?? 0,
      qualified: summary['qualified'] as int?,
      checkDetails: summary['check_details'] as int?,
      gradeGap: summary['grade_gap'] as int?,
    );
  }
}

final bursaryStatsProvider = FutureProvider<BursaryStats>((ref) async {
  final resp = await ApiClient.instance.get('/bursaries/stats/').timeout(
        const Duration(seconds: 15),
        onTimeout: () => throw Exception('Request timed out.'),
      );
  return BursaryStats.fromJson(Map<String, dynamic>.from(resp.data));
});

final bursaryRecommendationsProvider =
    FutureProvider<List<BursaryWithMatch>>((ref) async {
  final resp =
      await ApiClient.instance.get('/bursaries/recommend/', queryParams: {
    'limit': '5',
  }).timeout(
    const Duration(seconds: 15),
    onTimeout: () => throw Exception('Request timed out.'),
  );
  final list = (resp.data['results'] as List? ?? []);
  return list.map((e) {
    final m = Map<String, dynamic>.from(e as Map);
    final bjson = Map<String, dynamic>.from(m['bursary'] as Map);
    if (m['match'] != null) bjson['match'] = m['match'];
    return BursaryWithMatch.fromJson(bjson);
  }).toList();
});
