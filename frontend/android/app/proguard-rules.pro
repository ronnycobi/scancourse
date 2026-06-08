# Project-specific ProGuard/R8 rules. R8 already keeps Flutter's engine
# classes via the default rules — this file is for extra keep rules our
# native libraries need.

# Flutter embedding
-keep class io.flutter.embedding.** { *; }
-keep class io.flutter.plugin.** { *; }

# Image picker (uses reflection at runtime)
-keep class androidx.lifecycle.DefaultLifecycleObserver

# Firebase Messaging / Google Play Services / Google Sign-In keep their
# generated classes — covered by their own consumer rules, but keep the
# fallback so a missing rule doesn't crash release builds.
-keep class com.google.firebase.** { *; }
-keep class com.google.android.gms.** { *; }
-dontwarn com.google.firebase.**
-dontwarn com.google.android.gms.**

# Stripe / share_plus / url_launcher etc. are pure-Dart-facing — no
# extra rules needed.

# Play Core split-install — Flutter's FlutterPlayStoreSplitApplication
# references these classes for deferred-components, but we don't use
# deferred components so the library isn't on the classpath. Silence
# R8 instead of forcing an unused library in.
-dontwarn com.google.android.play.core.**

# Keep the line numbers in stack traces post-obfuscation so the
# mapping.txt we ship to Play actually maps back to source lines.
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile
