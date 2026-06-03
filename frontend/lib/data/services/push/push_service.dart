import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../api/api_client.dart';

/// Storage key for the per-device foreground-notifications toggle.
/// Mirrors the Settings screen's local pref.
const _kPrefPushLocal = 'pref_push_local';

/// Background / terminated-state handler. Must be a top-level function.
/// FCM auto-displays messages that carry a `notification` block in the
/// system tray, so there's nothing to do here — but the handler must be
/// registered or Android drops data-only messages.
@pragma('vm:entry-point')
Future<void> firebaseBackgroundHandler(RemoteMessage message) async {}

/// Owns Firebase Cloud Messaging: permission, token sync to our backend,
/// and showing a heads-up notification while the app is in the foreground.
class PushService {
  PushService._();
  static final PushService instance = PushService._();

  final FlutterLocalNotificationsPlugin _local =
      FlutterLocalNotificationsPlugin();
  bool _ready = false;

  /// Fired whenever the unread inbox likely changed (a push arrived in the
  /// foreground, or the app was opened from a notification). The UI sets
  /// this to refresh the notification-bell badge live.
  void Function()? onInboxChanged;

  static const AndroidNotificationChannel _channel = AndroidNotificationChannel(
    'scancourse_default',
    'Scancourse',
    description: 'Course matches, bursary deadlines and APS updates',
    importance: Importance.high,
  );

  /// One-time setup — safe to call before the user logs in. Wires up
  /// permission, the foreground display channel, and refresh listeners.
  Future<void> bootstrap() async {
    if (_ready) return;
    _ready = true;

    await FirebaseMessaging.instance.requestPermission();

    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    await _local.initialize(
      const InitializationSettings(android: androidInit),
    );
    await _local
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(_channel);

    // Foreground messages don't show automatically — render them ourselves.
    FirebaseMessaging.onMessage.listen(_showLocal);

    // Tapped a notification that opened the app → refresh the badge.
    FirebaseMessaging.onMessageOpenedApp.listen((_) => onInboxChanged?.call());

    // Keep the backend in sync if Firebase rotates the token.
    FirebaseMessaging.instance.onTokenRefresh.listen(_sendToken);
  }

  /// Call once the user is authenticated — registers this device's token
  /// against their account so the backend can target them.
  Future<void> syncToken() async {
    try {
      final token = await FirebaseMessaging.instance.getToken();
      if (token != null && token.isNotEmpty) await _sendToken(token);
    } catch (_) {
      // No Firebase / no network — push just won't work; not fatal.
    }
  }

  Future<void> _sendToken(String token) async {
    try {
      await ApiClient.instance
          .post('/auth/fcm-token/', data: {'fcm_token': token});
    } catch (_) {}
  }

  Future<void> _showLocal(RemoteMessage m) async {
    // A push arrived while the app is open → bump the bell badge.
    onInboxChanged?.call();
    // Respect the Settings → Push notifications toggle (per device,
    // controls foreground heads-up only — backgrounded messages are still
    // shown by the OS).
    try {
      final v = await const FlutterSecureStorage().read(key: _kPrefPushLocal);
      if (v == 'false') return;
    } catch (_) {}
    final n = m.notification;
    if (n == null) return;
    _local.show(
      n.hashCode,
      n.title,
      n.body,
      NotificationDetails(
        android: AndroidNotificationDetails(
          _channel.id,
          _channel.name,
          channelDescription: _channel.description,
          importance: Importance.high,
          priority: Priority.high,
          icon: '@mipmap/ic_launcher',
        ),
      ),
    );
  }
}
