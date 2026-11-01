# Garakland development workspace — 2026-11-01

- Source repository: skvive/garakland
- Protected production base: master, commit 1724924ee29c2695d69da55a7b757804ebc6116b
- Working branch: chatgpt/garakland-android-workspace-20261101
- Web production reference: https://garakland.lexid.site (not redeployed by this branch)
- Existing architecture: Python standard library HTTP API, SQLite by default, Neon Postgres using DATABASE_URL, HTML/CSS/JS frontend, ERP/market/hub/game modules.
- Android app module: android/ (Java WebView shell, separate from web/Python implementation).
- No live customer data, keys, or signing material may be committed.
- Build and emulator CI: .github/workflows/garakland-android-ci.yml
- CI debug APK is not a signed production APK.
- Keep merchant/coupon/wallet marketing simulation safeguards intact; real transactions are not enabled by Android wrapper.
- Validate database backend credentials only in the correct provisioned secure environment. Never connect the emulator to production admin tools with production credentials for smoke tests.
- Branch gate: static analysis, JUnit, debug APK, Android emulator instrumentation, device checks and release signing are distinct steps.
- Current local ChatGPT container lacks Android SDK, adb, emulator, /dev/kvm, and internet DNS. It cannot run an Android emulator here. Use CI runners with Android virtualization, and label actual test results instead of assuming success.
