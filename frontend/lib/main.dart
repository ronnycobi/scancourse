import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'app.dart';
import 'data/services/push/push_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Push notifications — wrapped so a missing/misconfigured Firebase
  // never blocks app start.
  try {
    await Firebase.initializeApp();
    FirebaseMessaging.onBackgroundMessage(firebaseBackgroundHandler);
    await PushService.instance.bootstrap();
  } catch (_) {}
  runApp(const ProviderScope(child: ScancourseApp()));
}
