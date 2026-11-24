# Garakland Android 0.2.0 Native MVP

App ID: site.lexid.garakland · minSdk 26 · targetSdk 35 · Java 17 · Android Gradle Plugin 8.9.2.

## Implemented
- Native Android Activity + Layout screens: Home, searchable demo stores, demo coupon previews, member gateway, bottom navigation.
- Native store filtering matches brand/data.js four explicitly DEMO fixtures; no real-store claims.
- Restricted existing WebView used ONLY for the existing interactive 3D map, not the entire app shell.
- Google OAuth / member coupons / favorite stores use Chrome/system browser and existing website's Neon Auth session; passwords/tokens are not embedded or copied by app.
- User's existing Android package and icon, Gradle project, CI and map WebView are reused rather than duplicated.

## Security and limitations
- Chrome browser account session is not automatically available in the native app. Per-member native API synchronization is NOT yet implemented.
- Coupons are demo display only, no redemption, payment, or real discount.
- 3D map, Google login and member wallet require internet.
- Debug APK is development-signed, not production Play release.
- No new backend secrets, databases or app permissions were introduced.

## Build
Open android/ in Android Studio; run :app:assembleDebug, :app:testDebugUnitTest, :app:lintDebug.
GitHub Actions garakland-android-ci builds debug APK and runs API35 emulator UI test.
APK path android/app/build/outputs/apk/debug/app-debug.apk.

## QA checklist
1. Launch native home, verify five bottom tabs and device back navigation.
2. Search 청과/수산 and filter fixtures.
3. Open coupons, ensure DEMO label appears.
4. Open native MY page, verify Google login opens external system browser (not embedded).
5. Open 3D map in restricted WebView and return to native home.
6. Verify signed-in browser account can independently open /mypage.html.
7. Native per-account sync and Google OAuth session handoff remain future development; do not mark completed.
8. Run GitHub Actions CI and inspect actual result before claiming build/emulator success.