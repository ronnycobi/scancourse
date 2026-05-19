import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../providers/aps_provider.dart';
import '../../widgets/common/loading_button.dart';

class _SubjectEntry {
  final TextEditingController name;
  final TextEditingController mark;
  final bool compulsory;
  final bool isLo;

  _SubjectEntry({String? defaultName, this.compulsory = false, this.isLo = false})
      : name = TextEditingController(text: defaultName ?? ''),
        mark = TextEditingController();

  void dispose() {
    name.dispose();
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
  bool _useMathsLit = false;

  // 4 compulsory + 3 electives = 7 fixed; 8th is optional
  late final List<_SubjectEntry> _compulsory;
  late final List<_SubjectEntry> _electives;
  _SubjectEntry? _extraElective;

  @override
  void initState() {
    super.initState();
    _compulsory = [
      _SubjectEntry(defaultName: 'Home Language', compulsory: true),
      _SubjectEntry(defaultName: 'First Additional Language', compulsory: true),
      _SubjectEntry(defaultName: 'Mathematics', compulsory: true),
      _SubjectEntry(defaultName: 'Life Orientation', compulsory: true, isLo: true),
    ];
    _electives = List.generate(3, (_) => _SubjectEntry());
  }

  @override
  void dispose() {
    for (final s in _compulsory) s.dispose();
    for (final s in _electives) s.dispose();
    _extraElective?.dispose();
    super.dispose();
  }

  void _toggleMathsLit(bool useLit) {
    setState(() {
      _useMathsLit = useLit;
      _compulsory[2].name.text = useLit ? 'Mathematical Literacy' : 'Mathematics';
    });
  }

  void _addExtra() {
    setState(() => _extraElective = _SubjectEntry());
  }

  void _removeExtra() {
    _extraElective?.dispose();
    setState(() => _extraElective = null);
  }

  Future<void> _calculate() async {
    if (!_formKey.currentState!.validate()) return;

    final all = [..._compulsory, ..._electives, if (_extraElective != null) _extraElective!];
    final entries = all
        .where((s) => s.name.text.isNotEmpty && s.mark.text.isNotEmpty)
        .map((s) => {'name': s.name.text.trim(), 'mark': s.mark.text.trim()})
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
                    const SizedBox(height: 24),

                    // --- Compulsory subjects ---
                    _SectionLabel(label: 'Compulsory Subjects', count: 4),
                    const SizedBox(height: 12),

                    // Maths vs Maths Lit toggle
                    Container(
                      margin: const EdgeInsets.only(bottom: 12),
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: AppColors.primaryLight,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.calculate_outlined, size: 18, color: AppColors.primary),
                          const SizedBox(width: 8),
                          const Expanded(
                            child: Text('Mathematics type',
                                style: TextStyle(color: AppColors.primary, fontWeight: FontWeight.w500, fontSize: 13)),
                          ),
                          SegmentedButton<bool>(
                            segments: const [
                              ButtonSegment(value: false, label: Text('Maths', style: TextStyle(fontSize: 12))),
                              ButtonSegment(value: true, label: Text('Maths Lit', style: TextStyle(fontSize: 12))),
                            ],
                            selected: {_useMathsLit},
                            onSelectionChanged: (s) => _toggleMathsLit(s.first),
                            style: ButtonStyle(
                              visualDensity: VisualDensity.compact,
                            ),
                          ),
                        ],
                      ),
                    ),

                    ..._compulsory.asMap().entries.map((entry) {
                      final s = entry.value;
                      return _SubjectRow(
                        entry: s,
                        index: entry.key,
                        compulsory: true,
                        showLoNote: s.isLo,
                      );
                    }),

                    const SizedBox(height: 20),

                    // --- Elective subjects ---
                    _SectionLabel(label: 'Elective Subjects', count: _extraElective != null ? 4 : 3),
                    const SizedBox(height: 4),
                    Text('Choose from approved NSC elective subjects',
                        style: Theme.of(context).textTheme.bodySmall),
                    const SizedBox(height: 12),

                    ..._electives.asMap().entries.map((entry) => _SubjectRow(
                          entry: entry.value,
                          index: entry.key,
                          compulsory: false,
                        )),

                    // Optional 8th subject
                    if (_extraElective != null) ...[
                      Stack(
                        children: [
                          _SubjectRow(entry: _extraElective!, index: 3, compulsory: false),
                          Positioned(
                            top: 0,
                            right: 0,
                            child: IconButton(
                              icon: const Icon(Icons.remove_circle, color: AppColors.error, size: 22),
                              onPressed: _removeExtra,
                              tooltip: 'Remove optional subject',
                            ),
                          ),
                        ],
                      ),
                    ] else ...[
                      TextButton.icon(
                        onPressed: _addExtra,
                        icon: const Icon(Icons.add_circle_outline, size: 18),
                        label: const Text('Add optional 8th subject'),
                        style: TextButton.styleFrom(foregroundColor: AppColors.primary),
                      ),
                    ],

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
  final int index;
  final bool compulsory;
  final bool showLoNote;

  const _SubjectRow({
    required this.entry,
    required this.index,
    required this.compulsory,
    this.showLoNote = false,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                flex: 3,
                child: TextFormField(
                  controller: entry.name,
                  textInputAction: TextInputAction.next,
                  textCapitalization: TextCapitalization.words,
                  style: const TextStyle(fontSize: 14),
                  decoration: InputDecoration(
                    hintText: compulsory ? 'e.g. English Home Language' : 'Subject name',
                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  validator: (v) {
                    if (compulsory && !entry.isLo && (v == null || v.trim().isEmpty)) return 'Required';
                    if (!compulsory && entry.mark.text.isNotEmpty && (v == null || v.trim().isEmpty)) return 'Enter name';
                    return null;
                  },
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: TextFormField(
                  controller: entry.mark,
                  keyboardType: const TextInputType.numberWithOptions(decimal: false),
                  textInputAction: TextInputAction.next,
                  decoration: InputDecoration(
                    hintText: '%',
                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                  ),
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
          if (showLoNote)
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
}
