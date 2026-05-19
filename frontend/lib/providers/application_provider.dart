import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/repositories/application_repository.dart';

final applicationRepositoryProvider = Provider((_) => ApplicationRepository());

final applicationListProvider =
    FutureProvider<List<ApplicationModel>>((ref) async {
  return ref.read(applicationRepositoryProvider).list();
});

final applicationStatsProvider =
    FutureProvider<ApplicationStats>((ref) async {
  return ref.read(applicationRepositoryProvider).stats();
});
