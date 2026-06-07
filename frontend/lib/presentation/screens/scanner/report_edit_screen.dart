import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/models/aps_model.dart';
import '../../../providers/aps_provider.dart';
import '../../widgets/cards/aps_score_card.dart';
import '../../widgets/common/loading_button.dart';

/// Edit an *existing* uploaded report — fetches by id, lets the user fix
/// OCR'd subject names + marks, then PATCHes the verify endpoint which
/// re-runs the APS calculation server-side.
class ReportEditScreen extends ConsumerStatefulWidget {
  final int reportId;
  const ReportEditScreen({super.key, required this.reportId});

  @override
  ConsumerState<ReportEditScreen> createState() => _ReportEditScreenState();
}

class _SubjectRow {
  final int id;
  final TextEditingController name;
  final TextEditingController mark;
  _SubjectRow({required this.id, required String name, required int mark})
      : name = TextEditingController(text: name),
        mark = TextEditingController(text: mark > 0 ? '$mark' : '');

  void dispose() {
    name.dispose();
    mark.dispose();
  }
}

class _ReportEditScreenState extends ConsumerState<ReportEditScreen> {
  ReportModel? _report;
  List<_SubjectRow> _rows = [];
  bool _loading = true;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    for (final r in _rows) {
      r.dispose();
    }
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final repo = ref.read(ocrRepositoryProvider);
      final report = await repo.getReport(widget.reportId);
      for (final r in _rows) {
        r.dispose();
      }
      final rows = <_SubjectRow>[];
      for (final s in (report.subjects ?? const [])) {
        final m = Map<String, dynamic>.from(s as Map);
        rows.add(_SubjectRow(
          id: (m['id'] as num).toInt(),
          name: (m['name'] as String?) ?? '',
          mark: (m['mark'] as num?)?.toInt() ?? 0,
        ));
      }
      setState(() {
        _report = report;
        _rows = rows;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _loading = false;
        _error = 'Could not load report.';
      });
    }
  }

  Future<void> _save() async {
    // Validate
    for (final r in _rows) {
      final name = r.name.text.trim();
      final markText = r.mark.text.trim();
      if (name.isEmpty) {
        _toast('Subject name cannot be empty.');
        return;
      }
      final m = int.tryParse(markText);
      if (m == null || m < 0 || m > 100) {
        _toast('Mark for $name must be 0–100.');
        return;
      }
    }

    // Drop focus so the keyboard collapses while we save — gives the
    // success snackbar room and prevents an accidental re-edit while
    // the request is in flight.
    FocusScope.of(context).unfocus();
    setState(() => _saving = true);
    try {
      final payload = _rows
          .map((r) => {
                'id': r.id,
                'name': r.name.text.trim(),
                'mark': int.parse(r.mark.text.trim()),
              })
          .toList();
      final repo = ref.read(ocrRepositoryProvider);
      final updated = await repo.verifySubjects(widget.reportId, payload);
      ref.invalidate(reportListProvider);
      ref.invalidate(latestApsProvider);
      if (mounted) {
        setState(() {
          _report = updated;
          _saving = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Report saved'),
            backgroundColor: AppColors.eligible,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _saving = false);
        _toast('Save failed. Please try again.');
      }
    }
  }

  void _toast(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), backgroundColor: AppColors.error),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Edit Report'),
        leading: BackButton(onPressed: () {
          if (context.canPop()) {
            context.pop();
          } else {
            context.go('/reports');
          }
        }),
      ),
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.error_outline,
                            size: 48, color: AppColors.error),
                        const SizedBox(height: 12),
                        Text(_error!),
                        const SizedBox(height: 12),
                        OutlinedButton(
                          onPressed: _load,
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  )
                : Column(
                    children: [
                      Expanded(
                        child: ListView(
                          padding: const EdgeInsets.all(16),
                          children: [
                            if (_report?.apsResult != null) ...[
                              ApsScoreCard(
                                totalAps: _report!.apsResult!.totalAps,
                                subjects: _report!.apsResult!.subjects,
                              ),
                              const SizedBox(height: 16),
                            ],
                            Text('Subjects',
                                style:
                                    Theme.of(context).textTheme.titleMedium),
                            const SizedBox(height: 4),
                            const Text(
                              'Fix any wrong names or marks below. We\'ll '
                              'recalculate your APS when you save.',
                              style: TextStyle(
                                  fontSize: 12,
                                  color: AppColors.textSecondary),
                            ),
                            const SizedBox(height: 12),
                            if (_rows.isEmpty)
                              Container(
                                padding: const EdgeInsets.all(16),
                                decoration: BoxDecoration(
                                  color: AppColors.surface,
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: const Text(
                                  'No subjects were extracted from this report. '
                                  'Try entering your marks manually instead.',
                                  style: TextStyle(
                                      color: AppColors.textSecondary),
                                ),
                              ),
                            ..._rows.map((r) => _EditRow(row: r)),
                            const SizedBox(height: 8),
                            if (_rows.isEmpty)
                              OutlinedButton.icon(
                                onPressed: () =>
                                    context.push('/manual-entry'),
                                icon: const Icon(Icons.edit_outlined),
                                label: const Text('Enter Marks Manually'),
                              ),
                          ],
                        ),
                      ),
                      if (_rows.isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.all(16),
                          child: LoadingButton(
                            label: 'Save Changes',
                            isLoading: _saving,
                            onPressed: _save,
                          ),
                        ),
                    ],
                  ),
      ),
    );
  }
}

class _EditRow extends StatelessWidget {
  final _SubjectRow row;
  const _EditRow({required this.row});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          Expanded(
            flex: 3,
            child: TextField(
              controller: row.name,
              textCapitalization: TextCapitalization.words,
              decoration: InputDecoration(
                labelText: 'Subject',
                contentPadding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10)),
              ),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: TextField(
              controller: row.mark,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: false),
              decoration: InputDecoration(
                labelText: 'Mark %',
                contentPadding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
