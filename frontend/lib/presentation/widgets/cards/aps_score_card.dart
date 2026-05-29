import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/models/aps_model.dart';

class ApsScoreCard extends StatefulWidget {
  final int totalAps;
  final List<ApsSubject> subjects;

  const ApsScoreCard({super.key, required this.totalAps, required this.subjects});

  @override
  State<ApsScoreCard> createState() => _ApsScoreCardState();
}

class _ApsScoreCardState extends State<ApsScoreCard> {
  bool _expanded = false;

  Color get _apsColor {
    if (widget.totalAps >= 35) return AppColors.apsExcellent;
    if (widget.totalAps >= 28) return AppColors.apsGood;
    if (widget.totalAps >= 20) return AppColors.apsFair;
    return AppColors.apsLow;
  }

  String get _apsLabel {
    if (widget.totalAps >= 35) return 'Excellent';
    if (widget.totalAps >= 28) return 'Good';
    if (widget.totalAps >= 20) return 'Fair';
    return 'Below Average';
  }

  @override
  Widget build(BuildContext context) {
    // Show the subjects that count toward APS first (highest points), then
    // the excluded ones (LO / AP / not-in-top-6) — so the preview always
    // surfaces the 6 that actually made the score.
    final subjects = [...widget.subjects]..sort((a, b) {
        if (a.countedInAps != b.countedInAps) {
          return a.countedInAps ? -1 : 1;
        }
        return b.apsPoints.compareTo(a.apsPoints);
      });
    final preview = subjects.take(4).toList();
    final hasMore = subjects.length > 4;
    final displayed = _expanded ? subjects : preview;

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Your APS Score', style: Theme.of(context).textTheme.bodyMedium),
                    const SizedBox(height: 4),
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          '${widget.totalAps}',
                          style: Theme.of(context).textTheme.displayMedium?.copyWith(
                            color: _apsColor,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: _apsColor.withOpacity(0.15),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Text(
                              _apsLabel,
                              style: TextStyle(
                                color: _apsColor,
                                fontWeight: FontWeight.w600,
                                fontSize: 13,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              _ApsProgressRing(aps: widget.totalAps, color: _apsColor),
            ],
          ),
          if (subjects.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Divider(),
            const SizedBox(height: 12),
            ...displayed.map((s) {
              final excluded = s.excludedReason != null;
              // Compact pill tag for excluded subjects.
              final tag = s.isLifeOrientation
                  ? 'LO'
                  : s.isAdvancedProgramme
                      ? 'AP'
                      : !s.countedInAps
                          ? 'Extra'
                          : '${s.apsPoints} pts';
              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            s.name,
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                  color: excluded
                                      ? AppColors.textHint
                                      : AppColors.textPrimary,
                                ),
                          ),
                          if (excluded)
                            Text(
                              s.excludedReason!,
                              style: const TextStyle(
                                fontSize: 11,
                                color: AppColors.textHint,
                                fontStyle: FontStyle.italic,
                              ),
                            ),
                        ],
                      ),
                    ),
                    Text(
                      '${s.mark}%',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: excluded ? AppColors.textHint : null,
                          ),
                    ),
                    const SizedBox(width: 12),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: excluded ? AppColors.surface : AppColors.primaryLight,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        tag,
                        style: TextStyle(
                          color: excluded ? AppColors.textHint : AppColors.primary,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              );
            }),
            if (hasMore)
              GestureDetector(
                onTap: () => setState(() => _expanded = !_expanded),
                child: Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        _expanded ? 'Collapse' : 'View all ${subjects.length} subjects',
                        style: const TextStyle(
                          color: AppColors.primary,
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(width: 4),
                      Icon(
                        _expanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                        color: AppColors.primary,
                        size: 18,
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ],
      ),
    );
  }
}

class _ApsProgressRing extends StatelessWidget {
  final int aps;
  final Color color;

  const _ApsProgressRing({required this.aps, required this.color});

  @override
  Widget build(BuildContext context) {
    final progress = (aps / 42).clamp(0.0, 1.0);
    return SizedBox(
      width: 80,
      height: 80,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CircularProgressIndicator(
            value: progress,
            strokeWidth: 8,
            backgroundColor: color.withOpacity(0.15),
            valueColor: AlwaysStoppedAnimation<Color>(color),
          ),
          Text('/42', style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
    );
  }
}
