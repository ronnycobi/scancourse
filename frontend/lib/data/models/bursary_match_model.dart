import 'bursary_model.dart';

class BursaryMatch {
  /// 'qualified' | 'check_details' | 'grade_gap' | 'field_mismatch' | 'closed'
  final String status;
  final String reason;
  final int? gradeGap;
  final int? daysUntilDeadline;

  const BursaryMatch({
    required this.status,
    required this.reason,
    this.gradeGap,
    this.daysUntilDeadline,
  });

  factory BursaryMatch.fromJson(Map<String, dynamic> j) => BursaryMatch(
        status: (j['status'] as String?) ?? 'check_details',
        reason: (j['reason'] as String?) ?? '',
        gradeGap: j['grade_gap'] as int?,
        daysUntilDeadline: j['days_until_deadline'] as int?,
      );

  bool get isClosed => status == 'closed';
  bool get isQualified => status == 'qualified';

  String get label {
    switch (status) {
      case 'qualified':
        return 'Qualify ✓';
      case 'check_details':
        return 'Check Details';
      case 'grade_gap':
        return 'Grade Gap';
      case 'field_mismatch':
        return 'Different Field';
      case 'closed':
        return 'Closed';
      default:
        return status;
    }
  }
}

/// Wraps a `BursaryModel` together with the per-user match info returned
/// alongside it by /bursaries/ and /bursaries/{id}/.
class BursaryWithMatch {
  final BursaryModel bursary;
  final BursaryMatch? match;

  const BursaryWithMatch({required this.bursary, this.match});

  factory BursaryWithMatch.fromJson(Map<String, dynamic> j) {
    final matchJson = j['match'];
    return BursaryWithMatch(
      bursary: BursaryModel.fromJson(j),
      match: matchJson is Map<String, dynamic>
          ? BursaryMatch.fromJson(matchJson)
          : null,
    );
  }
}
