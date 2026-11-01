> v1.0: 연결 실패 시 Keystore 키 보존, 화면 요청 경합 보호, URL 포트 검사. Android SDK 빌드와 실기기 테스트는 미완료.

# LogShield Console — Native Android (Java, not WebView)

**Artifact state:** SOURCE_READY / API_CONTRACT_TESTED / APK_NOT_BUILT / DEVICE_NOT_TESTED.

## Architecture

The native Android app is a **mobile administrative console**. It talks to the central FastAPI control plane over HTTPS and authenticates with an administrator account key. It is not a Windows endpoint DLP driver, does not read employee devices directly, and performs no stealth monitoring.

Native screens: login, dashboard, endpoints & device inventory, security alerts and acknowledgement, policy history/edit/rollback, install invitations, read-only Defender/USB signals, print audit, audit-chain verification. Safe notify and refresh commands plus device revocation are available only when the authenticated server role grants permission.

Security controls: Android Keystore AES-256-GCM for saved key, FLAG_SECURE for privileged screens, TLS validation with normal platform trust store, disabled redirects, no cleartext traffic, no app data backup, limited API paths and no WebView. Device admin APIs are **not** requested. Administrator keys are not bundled with the app.

## Building on Android Studio

1. Open `mobile-android` as an Android Studio Gradle project. Use JDK 17 and the Android 36 SDK.
2. Sync Gradle 8.13 and Android Gradle Plugin 8.13.2 (`build.gradle`). For command line: `gradle --no-daemon :app:assembleDebug :app:lintDebug`.
3. The generated debug install file is `app/build/outputs/apk/debug/app-debug.apk`; run `adb install -r <path>` or `test-on-device.sh`.
4. This environment did **not** have Android SDK/Gradle, so there is no verified APK in this ZIP. This is not a signed Play Store release. Keep the release keystore in secured CI only.
5. An Android CI workflow is included at the unified package `.github/workflows/android-build.yml`. Once committed to a repository, GitHub Actions can build and upload the debug APK to its build artifacts.

## Deployment prerequisites

The FastAPI server must be accessible through a secure HTTPS reverse proxy with valid TLS certificate and protected authentication. Create an authorized administrator account via the server CLI. Log in with HTTPS server URL, administrator ID and API key. Direct IP+HTTP lab access is intentionally refused in the production mobile UI.

The v0.8 backend relies on API keys; it does not expose a user-facing Entra login flow for this native client. Organization-wide SSO/MFA in the Android app requires additional OAuth system-browser PKCE integration and compatible server-side session API before production use. API keys should be scoped, rotated and revocable; prefer managed distribution and VPN/Zero Trust networking.

## Test coverage

- `tests/test_native_contract.py` starts an **actual** Uvicorn/SQLite backend, makes HTTP calls following Android contracts, and verifies RBAC/registration/alerts/policy/print/command/revocation.
- `tests/NativeSecurityRulesTest.java` tests HTTPS/URL validation and RBAC menu visibility using `javac` and `java`.
- `qa/create_android_compile_stubs.py` is a **syntax-only** Android API mock for offline Java compilation; it is NOT an Android SDK or an emulator.
- `test-on-device.sh` is a reproducible future real-device acceptance test entrypoint, not evidence it was executed here.

## Play Store

As of October 2026, new Android phone apps submitted to Google Play must target API 36 or higher. This app targets API 36, but actual Gradle build, Android lint, release signing, privacy/data safety disclosure, and device smoke testing are still required.
