import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/models/aps_model.dart';
import '../../../providers/aps_provider.dart';
import '../../widgets/common/loading_button.dart';

/// The 11 official SA languages, used to build the Home Language and
/// First Additional Language dropdowns (so the names always match the
/// canonical forms the APS calculator normalises against).
const _officialLanguages = [
  'English',
  'Afrikaans',
  'isiZulu',
  'isiXhosa',
  'Sepedi',
  'Setswana',
  'Sesotho',
  'Xitsonga',
  'siSwati',
  'Tshivenda',
  'isiNdebele',
];

List<String> get _homeLanguageOptions =>
    _officialLanguages.map((l) => '$l Home Language').toList();

List<String> get _falOptions =>
    _officialLanguages.map((l) => '$l First Additional Language').toList();

/// The compulsory Mathematics slot — Pure Maths or Maths Literacy.
const _mathOptions = ['Mathematics', 'Mathematical Literacy'];

/// Approved NSC elective subjects (Maths / Maths Lit excluded — those are
/// the compulsory Mathematics slot).
const _electiveSubjects = [
  'Accounting',
  'Agricultural Sciences',
  'Agricultural Management Practices',
  'Agricultural Technology',
  'Business Studies',
  'Civil Technology',
  'Computer Applications Technology',
  'Consumer Studies',
  'Dance Studies',
  'Design',
  'Dramatic Arts',
  'Economics',
  'Electrical Technology',
  'Engineering Graphics and Design',
  'Geography',
  'History',
  'Hospitality Studies',
  'Information Technology',
  'Life Sciences',
  'Maritime Economics',
  'Mechanical Technology',
  'Music',
  'Nautical Science',
  'Physical Sciences',
  'Religion Studies',
  'Sport and Exercise Science',
  'Technical Mathematics',
  'Technical Sciences',
  'Tourism',
  'Visual Arts',
];

/// IEB Advanced Programme subjects — taken in addition to the 7 NSC
/// subjects, ONLY by IEB learners. Not counted in standard APS (the
/// backend flags + excludes them). Shown in the dropdown only when the
/// learner selects the IEB curriculum.
const _advancedProgrammeList = [
  'Advanced Programme Mathematics',
  'Advanced Programme English',
  'Advanced Programme Afrikaans',
];
final _advancedProgrammeSubjects = _advancedProgrammeList.toSet();

/// DBE learners see only the standard NSC electives; IEB learners also
/// get the Advanced Programme subjects appended.
List<String> electiveOptionsFor({required bool isIeb}) =>
    isIeb ? [..._electiveSubjects, ..._advancedProgrammeList] : _electiveSubjects;

class _SubjectEntry {
  // Selected subject name. For fixed rows (Maths / LO) this is set in code
  // and not user-editable. For dropdown rows the user picks from [options].
  String? name;
  final TextEditingController mark;
  final bool compulsory;
  final bool isLo;
  final bool fixed; // Maths + LO — name shown read-only
  List<String>? options; // null → fixed/read-only (mutable: board switch)

  _SubjectEntry({
    this.name,
    this.compulsory = false,
    this.isLo = false,
    this.fixed = false,
    this.options,
  }) : mark = TextEditingController();

  void dispose() {
    mark.dispose();
  }
}

class ManualEntryScreen extends ConsumerStatefulWidget {
  const ManualEntryScreen({super.key});

  @override
  ConsumerState<ManualEntryScreen> createState() => _ManualEntryScreenState();
}

class _ManualEntryScreenState extends ConsumerState<ManualEntryScreen> {
  final _formKey = GlobalKey<FormState>();
  bool _isLoading = false;
  // Curriculum board — defaults to DBE (public schools); IEB learners
  // switch this to reveal the Advanced Programme subjects.
  bool _isIeb = false;

  // NSC minimum is 7 subjects: 4 compulsory + 3 electives. Learners
  // (especially IEB) can take more, so electives grow up to _maxElectives
  // (→ 11 subjects total) and shrink back to _minElectives.
  static const int _minElectives = 3;
  static const int _maxElectives = 7;

  late final List<_SubjectEntry> _compulsory;
  late final List<_SubjectEntry> _electives;

  List<String> get _electiveOptions => electiveOptionsFor(isIeb: _isIeb);

  @override
  void initState() {
    super.initState();
    _compulsory = [
      _SubjectEntry(compulsory: true, options: _homeLanguageOptions),
      _SubjectEntry(compulsory: true, options: _falOptions),
      _SubjectEntry(name: 'Mathematics', compulsory: true, options: _mathOptions),
      _SubjectEntry(
          name: 'Life Orientation', compulsory: true, isLo: true, fixed: true),
    ];
    _electives =
        List.generate(_minElectives, (_) => _SubjectEntry(options: _electiveOptions));

    // Pre-fill from the user's latest APS so "Edit Marks" opens with their
    // existing subjects + marks instead of a blank form.
    final aps = ref.read(latestApsProvider).valueOrNull;
    if (aps != null && aps.subjects.isNotEmpty) {
      _prefill(aps.subjects);
    }
  }

  void _prefill(List<ApsSubject> subjects) {
    // Switch to IEB if any Advanced Programme subject is present.
    _isIeb = subjects.any((s) =>
        s.isAdvancedProgramme ||
        s.name.toLowerCase().contains('advanced programme'));
    final opts = _electiveOptions;
    for (final e in _electives) {
      e.options = opts;
    }

    final leftovers = <ApsSubject>[];
    for (final s in subjects) {
      final lower = s.name.toLowerCase();
      final markStr = s.mark > 0 ? s.mark.toString() : '';
      if (s.isLifeOrientation || lower == 'life orientation' || lower == 'lo') {
        _compulsory[3].mark.text = markStr;
      } else if (lower.contains('home language')) {
        _compulsory[0].name = s.name;
        _compulsory[0].mark.text = markStr;
      } else if (lower.contains('first additional language')) {
        _compulsory[1].name = s.name;
        _compulsory[1].mark.text = markStr;
      } else if (s.normalizedName == 'mathematics' ||
          s.normalizedName == 'mathematical literacy' ||
          lower == 'mathematics' ||
          lower == 'mathematical literacy') {
        _compulsory[2].name =
            lower.contains('lit') ? 'Mathematical Literacy' : 'Mathematics';
        _compulsory[2].mark.text = markStr;
      } else {
        leftovers.add(s);
      }
    }

    // Fill / grow elective rows from whatever's left.
    for (var i = 0; i < leftovers.length; i++) {
      final s = leftovers[i];
      if (i < _electives.length) {
        _electives[i].name = s.name;
        _electives[i].mark.text = s.mark > 0 ? s.mark.toString() : '';
      } else if (_electives.length < _maxElectives) {
        final e = _SubjectEntry(options: opts);
        e.name = s.name;
        e.mark.text = s.mark > 0 ? s.mark.toString() : '';
        _electives.add(e);
      }
    }
  }

  void _setBoard(bool ieb) {
    setState(() {
      _isIeb = ieb;
      final opts = _electiveOptions;
      for (final e in _electives) {
        e.options = opts;
        // Switching back to DBE: clear any Advanced Programme picks that
        // are no longer valid options.
        if (!ieb && _advancedProgrammeSubjects.contains(e.name)) {
          e.name = null;
        }
      }
    });
  }

  @override
  void dispose() {
    for (final s in _compulsory) s.dispose();
    for (final s in _electives) s.dispose();
    super.dispose();
  }

  void _addElective() {
    if (_electives.length >= _maxElectives) return;
    setState(() => _electives.add(_SubjectEntry(options: _electiveOptions)));
  }

  void _removeElective(_SubjectEntry e) {
    if (_electives.length <= _minElectives) return;
    e.dispose();
    setState(() => _electives.remove(e));
  }

  Future<void> _calculate() async {
    if (!_formKey.currentState!.validate()) return;

    final all = [..._compulsory, ..._electives];
    final entries = all
        .where((s) =>
            (s.name?.trim().isNotEmpty ?? false) && s.mark.text.isNotEmpty)
        .map((s) => {'name': s.name!.trim(), 'mark': s.mark.text.trim()})
        .toList();

    setState(() => _isLoading = true);
    try {
      await ref.read(ocrRepositoryProvider).submitManualEntry(entries);
      ref.invalidate(latestApsProvider);
      if (mounted) context.go('/home');
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString()), backgroundColor: AppColors.error),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Enter Marks Manually'),
        leading: const CloseButton(),
      ),
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              Expanded(
                child: ListView(
                  padding: const EdgeInsets.all(20),
                  children: [
                    Text('Enter your NSC subjects and marks',
                        style: Theme.of(context).textTheme.headlineSmall),
                    const SizedBox(height: 6),
                    Text('Standard NSC: 7 subjects (4 compulsory + 3 elective). '
                        'An optional 8th subject can be added.',
                        style: Theme.of(context).textTheme.bodySmall),
                    const SizedBox(height: 20),

                    // --- Curriculum board (DBE default / IEB) ---
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: AppColors.primaryLight,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.school_outlined,
                              size: 18, color: AppColors.primary),
                          const SizedBox(width: 8),
                          const Expanded(
                            child: Text('Exam board',
                                style: TextStyle(
                                    color: AppColors.primary,
                                    fontWeight: FontWeight.w500,
                                    fontSize: 13)),
                          ),
                          SegmentedButton<bool>(
                            segments: const [
                              ButtonSegment(
                                  value: false,
                                  label: Text('DBE',
                                      style: TextStyle(fontSize: 12))),
                              ButtonSegment(
                                  value: true,
                                  label: Text('IEB',
                                      style: TextStyle(fontSize: 12))),
                            ],
                            selected: {_isIeb},
                            onSelectionChanged: (s) => _setBoard(s.first),
                            style: const ButtonStyle(
                                visualDensity: VisualDensity.compact),
                          ),
                        ],
                      ),
                    ),
                    if (_isIeb)
                      Padding(
                        padding: const EdgeInsets.only(top: 6, left: 4),
                        child: Text(
                          'IEB: Advanced Programme subjects are available below '
                          '(recorded but not counted in APS).',
                          style: TextStyle(
                              fontSize: 11,
                              color: AppColors.textHint,
                              fontStyle: FontStyle.italic),
                        ),
                      ),
                    const SizedBox(height: 20),

                    // --- Compulsory subjects ---
                    _SectionLabel(label: 'Compulsory Subjects', count: 4),
                    const SizedBox(height: 12),

                    ..._compulsory.map((s) => _SubjectRow(
                          entry: s,
                          compulsory: true,
                          hint: s.options == _homeLanguageOptions
                              ? 'Home Language'
                              : s.options == _falOptions
                                  ? 'First Additional Language'
                                  : s.options == _mathOptions
                                      ? 'Mathematics'
                                      : 'Subject',
                          showLoNote: s.isLo,
                          onChanged: () => setState(() {}),
                        )),

                    const SizedBox(height: 20),

                    // --- Elective subjects (growable: 3 to 7) ---
                    _SectionLabel(
                        label: 'Elective Subjects', count: _electives.length),
                    const SizedBox(height: 4),
                    Text('Choose from approved NSC elective subjects',
                        style: Theme.of(context).textTheme.bodySmall),
                    const SizedBox(height: 12),

                    ..._electives.map((e) {
                      final canRemove = _electives.length > _minElectives;
                      final row = _SubjectRow(
                        entry: e,
                        compulsory: false,
                        hint: 'Select subject',
                        onChanged: () => setState(() {}),
                      );
                      if (!canRemove) return row;
                      return Stack(
                        children: [
                          Padding(
                            padding: const EdgeInsets.only(right: 36),
                            child: row,
                          ),
                          Positioned(
                            top: 0,
                            right: 0,
                            child: IconButton(
                              icon: const Icon(Icons.remove_circle,
                                  color: AppColors.error, size: 22),
                              onPressed: () => _removeElective(e),
                              tooltip: 'Remove subject',
                            ),
                          ),
                        ],
                      );
                    }),

                    // Add another subject (up to 11 subjects total)
                    if (_electives.length < _maxElectives)
                      TextButton.icon(
                        onPressed: _addElective,
                        icon: const Icon(Icons.add_circle_outline, size: 18),
                        label: const Text('Add another subject'),
                        style: TextButton.styleFrom(
                            foregroundColor: AppColors.primary),
                      ),

                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.accentLight,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(Icons.info_outline, size: 16, color: AppColors.accent),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'APS is calculated from your best 6 subjects (excluding Life Orientation). '
                              'Life Orientation is compulsory but not counted in APS.',
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.all(20),
                child: LoadingButton(
                  label: 'Calculate My APS',
                  isLoading: _isLoading,
                  onPressed: _calculate,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  final String label;
  final int count;

  const _SectionLabel({required this.label, required this.count});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Text(label, style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(width: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
          decoration: BoxDecoration(
            color: AppColors.primaryLight,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text('$count', style: const TextStyle(color: AppColors.primary, fontSize: 12, fontWeight: FontWeight.w600)),
        ),
      ],
    );
  }
}

class _SubjectRow extends StatelessWidget {
  final _SubjectEntry entry;
  final bool compulsory;
  final String hint;
  final bool showLoNote;
  final VoidCallback onChanged;

  const _SubjectRow({
    required this.entry,
    required this.compulsory,
    required this.hint,
    required this.onChanged,
    this.showLoNote = false,
  });

  @override
  Widget build(BuildContext context) {
    final nameField = entry.fixed
        // Maths / Life Orientation — name is fixed, show read-only.
        ? InputDecorator(
            decoration: _dec(null),
            child: Text(
              entry.name ?? '',
              style: const TextStyle(fontSize: 14, color: AppColors.textPrimary),
            ),
          )
        // Languages + electives — dropdown of canonical names. Include the
        // current value even if it's not in the base list (e.g. a pre-filled
        // name from OCR) so it displays instead of asserting/crashing.
        : DropdownButtonFormField<String>(
            value: entry.name,
            isExpanded: true,
            decoration: _dec(hint),
            style: const TextStyle(fontSize: 14, color: AppColors.textPrimary),
            items: <String>[
              ...(entry.options ?? const []),
              if (entry.name != null &&
                  entry.name!.isNotEmpty &&
                  !(entry.options ?? const []).contains(entry.name))
                entry.name!,
            ]
                .map((o) => DropdownMenuItem(
                      value: o,
                      child: Text(o,
                          maxLines: 1, overflow: TextOverflow.ellipsis),
                    ))
                .toList(),
            onChanged: (v) {
              entry.name = v;
              onChanged();
            },
            validator: (v) {
              if (compulsory && (v == null || v.isEmpty)) return 'Required';
              if (!compulsory &&
                  entry.mark.text.isNotEmpty &&
                  (v == null || v.isEmpty)) {
                return 'Pick subject';
              }
              return null;
            },
          );

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(flex: 3, child: nameField),
              const SizedBox(width: 10),
              Expanded(
                child: TextFormField(
                  controller: entry.mark,
                  keyboardType: const TextInputType.numberWithOptions(decimal: false),
                  textInputAction: TextInputAction.next,
                  decoration: _dec('%'),
                  onChanged: (_) => onChanged(),
                  validator: (v) {
                    if (compulsory && !entry.isLo) {
                      if (v == null || v.trim().isEmpty) return 'Required';
                    }
                    if (v != null && v.isNotEmpty) {
                      final m = int.tryParse(v);
                      if (m == null || m < 0 || m > 100) return '0–100';
                    }
                    return null;
                  },
                ),
              ),
            ],
          ),
          if (showLoNote ||
              _advancedProgrammeSubjects.contains(entry.name))
            Padding(
              padding: const EdgeInsets.only(top: 4, left: 2),
              child: Text(
                'Not counted in APS',
                style: TextStyle(fontSize: 11, color: AppColors.textHint, fontStyle: FontStyle.italic),
              ),
            ),
        ],
      ),
    );
  }

  InputDecoration _dec(String? hint) => InputDecoration(
        hintText: hint,
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
      );
}
