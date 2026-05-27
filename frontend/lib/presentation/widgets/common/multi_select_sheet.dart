import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

/// Bottom-sheet multi-select picker.
///
/// Used for "Preferred fields", "Preferred study provinces" etc.
/// Returns the chosen list (or null if dismissed). The current selection
/// is passed in so the sheet opens with those items pre-ticked.
class MultiSelectSheet extends StatefulWidget {
  final String title;
  final String? subtitle;
  final Map<String, String> options;
  final List<String> initiallySelected;
  final int? maxSelections;
  final String? confirmLabel;

  const MultiSelectSheet({
    super.key,
    required this.title,
    required this.options,
    this.subtitle,
    this.initiallySelected = const [],
    this.maxSelections,
    this.confirmLabel,
  });

  /// Convenience launcher.
  static Future<List<String>?> show(
    BuildContext context, {
    required String title,
    String? subtitle,
    required Map<String, String> options,
    List<String> initiallySelected = const [],
    int? maxSelections,
    String? confirmLabel,
  }) {
    return showModalBottomSheet<List<String>>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => MultiSelectSheet(
        title: title,
        subtitle: subtitle,
        options: options,
        initiallySelected: initiallySelected,
        maxSelections: maxSelections,
        confirmLabel: confirmLabel,
      ),
    );
  }

  @override
  State<MultiSelectSheet> createState() => _MultiSelectSheetState();
}

class _MultiSelectSheetState extends State<MultiSelectSheet> {
  late Set<String> _selected;
  String _filter = '';

  @override
  void initState() {
    super.initState();
    _selected = widget.initiallySelected.toSet();
  }

  void _toggle(String key) {
    setState(() {
      if (_selected.contains(key)) {
        _selected.remove(key);
      } else {
        if (widget.maxSelections != null &&
            _selected.length >= widget.maxSelections!) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                  'You can pick up to ${widget.maxSelections} options.'),
            ),
          );
          return;
        }
        _selected.add(key);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final filtered = widget.options.entries
        .where((e) =>
            e.value.toLowerCase().contains(_filter.toLowerCase()) ||
            e.key.toLowerCase().contains(_filter.toLowerCase()))
        .toList();
    return DraggableScrollableSheet(
      initialChildSize: 0.7,
      minChildSize: 0.45,
      maxChildSize: 0.92,
      expand: false,
      builder: (_, scrollController) {
        return Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            children: [
              const SizedBox(height: 8),
              Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: AppColors.border,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 12),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            widget.title,
                            style: const TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.w800),
                          ),
                          if (widget.subtitle != null)
                            Padding(
                              padding: const EdgeInsets.only(top: 2),
                              child: Text(
                                widget.subtitle!,
                                style: const TextStyle(
                                    fontSize: 12,
                                    color: AppColors.textSecondary),
                              ),
                            ),
                        ],
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: _selected.isEmpty
                            ? AppColors.surface
                            : AppColors.primaryLight,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        widget.maxSelections != null
                            ? '${_selected.length}/${widget.maxSelections}'
                            : '${_selected.length}',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w800,
                          color: _selected.isEmpty
                              ? AppColors.textSecondary
                              : AppColors.primary,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),

              // Search bar — handy when option list is long (provinces is fine,
              // but study fields can be 20+).
              if (widget.options.length > 8)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: TextField(
                    decoration: InputDecoration(
                      hintText: 'Search…',
                      prefixIcon: const Icon(Icons.search,
                          size: 20, color: AppColors.textHint),
                      isDense: true,
                      contentPadding:
                          const EdgeInsets.symmetric(vertical: 12),
                      filled: true,
                      fillColor: AppColors.surface,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: BorderSide.none,
                      ),
                    ),
                    onChanged: (v) => setState(() => _filter = v),
                  ),
                ),
              const SizedBox(height: 8),

              const Divider(height: 1),
              Expanded(
                child: ListView.builder(
                  controller: scrollController,
                  itemCount: filtered.length,
                  itemBuilder: (_, i) {
                    final entry = filtered[i];
                    final isSelected = _selected.contains(entry.key);
                    return InkWell(
                      onTap: () => _toggle(entry.key),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 20, vertical: 12),
                        child: Row(
                          children: [
                            AnimatedContainer(
                              duration: const Duration(milliseconds: 140),
                              width: 22,
                              height: 22,
                              decoration: BoxDecoration(
                                color: isSelected
                                    ? AppColors.primary
                                    : Colors.white,
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(
                                  color: isSelected
                                      ? AppColors.primary
                                      : AppColors.border,
                                  width: 1.5,
                                ),
                              ),
                              child: isSelected
                                  ? const Icon(Icons.check,
                                      size: 16, color: Colors.white)
                                  : null,
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                entry.value,
                                style: TextStyle(
                                  fontSize: 15,
                                  fontWeight: isSelected
                                      ? FontWeight.w700
                                      : FontWeight.w500,
                                  color: AppColors.textPrimary,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
              const Divider(height: 1),
              Padding(
                padding: EdgeInsets.fromLTRB(
                    20, 12, 20,
                    12 + MediaQuery.of(context).padding.bottom),
                child: Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () => setState(() => _selected.clear()),
                        style: OutlinedButton.styleFrom(
                          minimumSize: const Size(0, 48),
                          foregroundColor: AppColors.textSecondary,
                          side: const BorderSide(color: AppColors.border),
                        ),
                        child: const Text('Clear'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      flex: 2,
                      child: ElevatedButton(
                        onPressed: () =>
                            Navigator.pop(context, _selected.toList()),
                        style: ElevatedButton.styleFrom(
                          minimumSize: const Size(0, 48),
                          backgroundColor: AppColors.primary,
                        ),
                        child: Text(widget.confirmLabel ?? 'Done'),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
