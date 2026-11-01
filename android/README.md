# 가락랜드 Android 빌드 · 에뮬레이터 작업공간

웹 원본을 수정하지 않고 네이티브 Android WebView 컨테이너를 추가했습니다.

- 앱 ID: `site.lexid.garakland`
- 첫 화면: `https://garakland.lexid.site/market.html`
- 최소 Android 8.0 (API 26), target/compile API 35
- Java 17, Android Gradle Plugin 8.9.2, Gradle 8.11.1
- 디버그 APK: `android/app/build/outputs/apk/debug/app-debug.apk`

## 로컬 개발

Android Studio에서 이 `android/` 폴더를 열거나, Android SDK (platform 35, build-tools 35.0.0), Java 17+, Gradle 8.11.1을 설치하십시오.

```bash
# Android SDK/Gradle이 설치된 호스트
gradle -p android :app:lintDebug :app:testDebugUnitTest :app:assembleDebug
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
adb shell am start -n site.lexid.garakland/.MainActivity

# AVD를 실행한 다음
gradle -p android :app:connectedDebugAndroidTest
```

Android Virtual Device(API 35, Pixel 기종)를 실행하고 네트워크/위치 허용/사이트 이동/뒤로가기/업로드/회전/에러 화면을 확인하십시오. `Android Studio > Device Manager`에서 새 AVD를 생성할 수 있습니다.

## 자동 CI

`.github/workflows/garakland-android-ci.yml`은 작업 브랜치 push/PR/수동 실행 시:
1. Java/SDK/Gradle 준비, lint/JUnit/Debug APK 빌드
2. 에뮬레이터 기동 후 실제 설치 + UI Smoke 테스트
3. 검증 로그와 디버그 APK를 Actions artifact로 저장

에뮬레이터 작업에 /dev/kvm이 가능한 GitHub 호스트가 필요합니다. CI 실행 결과가 성공하기 전에는 빌드 또는 에뮬레이터 검증 완료라고 표시하지 마십시오.

## 보안 및 출시 제한

이 빌드는 **온라인 웹앱 WebView 셸**입니다. 서버 접속이 필요하며 네이티브 결제/Google 로그인/카메라/AR 등을 자동으로 보장하지 않습니다. 허용된 HTTPS 호스트 내부만 WebView에 표시하고 지도 및 외부 로그인 링크는 외부 앱/브라우저로 보냅니다. 위치 권한은 사용자가 실제 요청을 승인할 때만 허용합니다. 인증 토큰/DB 비밀번호/업로드 키는 앱에 포함하지 않습니다.

Google Play 제출 전 실단말 테스트, 개인정보 처리방침, 계정 삭제/로그인 플로우, 권한 설명, Play 정책, 광고·결제 정책, 앱 서명과 소유권 검증이 필요합니다. 
