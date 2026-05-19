import 'dart:io';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/models/aps_model.dart';
import '../data/repositories/ocr_repository.dart';

final ocrRepositoryProvider = Provider((ref) => OcrRepository());

final latestApsProvider = FutureProvider<ApsResult?>((ref) async {
  final repo = ref.read(ocrRepositoryProvider);
  return repo.getLatestAps();
});

final reportListProvider = FutureProvider<List<ReportModel>>((ref) async {
  final repo = ref.read(ocrRepositoryProvider);
  return repo.getReports();
});

class ScannerState {
  final bool isUploading;
  final bool isProcessing;
  final ReportModel? report;
  final String? error;

  const ScannerState({
    this.isUploading = false,
    this.isProcessing = false,
    this.report,
    this.error,
  });

  bool get hasResult => report?.apsResult != null;

  ScannerState copyWith({
    bool? isUploading,
    bool? isProcessing,
    ReportModel? report,
    String? error,
  }) {
    return ScannerState(
      isUploading: isUploading ?? this.isUploading,
      isProcessing: isProcessing ?? this.isProcessing,
      report: report ?? this.report,
      error: error,
    );
  }
}

class ScannerNotifier extends StateNotifier<ScannerState> {
  final OcrRepository _repo;

  ScannerNotifier(this._repo) : super(const ScannerState());

  Future<void> uploadFile(File file) async {
    state = const ScannerState(isUploading: true);
    try {
      final report = await _repo.uploadReport(file);
      state = ScannerState(report: report, isProcessing: true);
      await _pollReport(report.id);
    } catch (e) {
      state = ScannerState(error: e.toString());
    }
  }

  Future<void> _pollReport(int id) async {
    for (int i = 0; i < 30; i++) {
      await Future.delayed(const Duration(seconds: 2));
      try {
        final report = await _repo.getReport(id);
        state = state.copyWith(report: report);
        if (report.status == 'completed' || report.status == 'failed') {
          state = state.copyWith(isProcessing: false);
          return;
        }
      } catch (_) {}
    }
    state = state.copyWith(isProcessing: false, error: 'Processing timed out. Please try again.');
  }

  Future<void> verifyAndRecalculate(int reportId, List<Map<String, dynamic>> subjects) async {
    try {
      final report = await _repo.verifySubjects(reportId, subjects);
      state = state.copyWith(report: report);
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }

  void reset() => state = const ScannerState();
}

final scannerProvider = StateNotifierProvider<ScannerNotifier, ScannerState>(
  (ref) => ScannerNotifier(ref.read(ocrRepositoryProvider)),
);
