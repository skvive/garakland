# 가락한상 Cursor 인수 및 실행
1. Windows에 Python 3.10 이상 설치 후 `RUN_HUB_WINDOWS.bat` 실행.
2. http://localhost:8769 에서 브랜드 사이트, /hub.html 에서 관리자 허브 확인.
3. `RUN_HUB_TESTS_WINDOWS.bat` 으로 전체 자동 회귀검사 실행.
4. 브랜드 기준 시안: `assets/brand/user-approved-concept.png`; 로고/마스코트 원본: `assets/brand/`.
5. 브랜드 사이트는 index, stores, store, market-map, coupons, events, market-guide, merchant-center 페이지로 구성.
6. 상용 전 필수: 실점포 DB/실측 위치, Google API 키와 라이선스, 계약/결제/광고 승인, Windows 실기기 브라우저 E2E 검증.
7. 이 패키지는 **베타/시연판**이며 결제·실발송·실측 3D를 완성한 운영판이 아님.
8. Python 서버의 출력에서 로컬 관리자 토큰 확인. 공개 서버에 기본 설정 그대로 노출 금지.
