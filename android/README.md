# YT Downloader for Android

Native Android app (Kotlin + Jetpack Compose) built on
[youtubedl-android](https://github.com/JunkFood02/youtubedl-android), which bundles yt-dlp,
Python, ffmpeg and QuickJS (for YouTube's JavaScript challenges).

- **Min Android:** 8.0 (API 26) · **Target:** API 36 · **Compile:** API 37
- **Package:** `com.thevoid.ytdownloader` (debug builds: `com.thevoid.ytdownloader.debug`)

## How it works

| Piece | File |
|---|---|
| Share sheet and permissions | `MainActivity.kt` |
| UI (THE VOID theme) | `ui/MainScreen.kt`, `ui/SettingsDialog.kt`, `ui/theme/Theme.kt` |
| Queue, persisted with WorkManager | `download/DownloadRepository.kt` |
| Background download, notifications, cancel | `download/DownloadWorker.kt` |
| yt-dlp arguments (unit-tested) | `download/DownloadSpec.kt` |
| Saving to `Download/YT Downloader` | `download/MediaSaver.kt` (MediaStore on Android 10+) |
| First-run unpack and yt-dlp self-update | `download/YtDl.kt` |

Videos prefer H.264 + AAC in MP4 at each resolution, so they play on every phone.

## Build

You need JDK 17+ and the Android SDK; Android Studio includes both.

```bash
./gradlew testDebugUnitTest   # unit tests
./gradlew assembleDebug       # app/build/outputs/apk/debug/*.apk
./gradlew assembleRelease     # app/build/outputs/apk/release/*.apk
```

Each build produces one APK per CPU type (`arm64-v8a`, `armeabi-v7a`, `x86_64`, `x86`) plus a `universal` APK.

## Release signing

Without a signing key, release builds are signed with the **debug key**. That's fine for testing, but **don't publish them**: Android only lets users update an app that was signed with the same key, so you need one permanent key from day one.

1. Create a key once, and **back it up somewhere safe**. If it's lost, you can never update the app again.
   ```bash
   keytool -genkeypair -v -keystore ytd-release.jks -alias ytd \
           -keyalg RSA -keysize 4096 -validity 10000
   ```
2. **Local builds:** create `android/keystore.properties` (this file is git-ignored):
   ```properties
   storeFile=/absolute/path/to/ytd-release.jks
   storePassword=…
   keyAlias=ytd
   keyPassword=…
   ```
3. **GitHub Actions:** add these repository secrets. The `Android build` workflow uses them automatically.

   | Secret | Value |
   |---|---|
   | `ANDROID_KEYSTORE_BASE64` | output of `base64 -w0 ytd-release.jks` |
   | `ANDROID_KEYSTORE_PASSWORD` | keystore password |
   | `ANDROID_KEY_ALIAS` | `ytd` |
   | `ANDROID_KEY_PASSWORD` | key password |

## Releasing a new version

Bump `versionCode` (+1) and `versionName` in `app/build.gradle.kts`, then tag the repository (`vX.Y.Z`). The workflow attaches the signed APKs to the GitHub release.

## Distribution note

Google Play's policies don't allow apps that download YouTube videos. Distribute the APKs through GitHub Releases. You can also submit to F-Droid or IzzyOnDroid (both accept this kind of app).
