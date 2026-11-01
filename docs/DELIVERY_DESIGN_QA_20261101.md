# 가락랜드 납품 디자인 QA · 2026-11-01
실제 Chromium + 임시 SQLite 시연 서버로 18개 페이지 × 1440/390/360px = 54회 캡처.
초기 결함: unsubscribe 모바일 가로 스크롤 31~34px; 디자인 갤러리 v4_* PNG 이미지 다수 유실; 일부 검색/필터/쿠폰/찜 버튼 34~36px.
수정: 18개 페이지 공통 responsive CSS, 브랜드 사진 비율/포컬 위치/터치 타깃, 수신거부 box-sizing, 운영허브 고정 버튼 위치, 갤러리 16장 실제 존재하는 미리보기 연결.
검증: GitHub Actions 'Garakland Visual QA · all pages'에서 routes/404/broken images/overflow와 screenshots, 백엔드 회귀 테스트 검사.
제외: 실제 점포 사진·현장 GPS, 실결제, 승인 없는 상인 운영정보, 실 Google 3D/AR 카메라, 로그인 후 운영관리 화면.