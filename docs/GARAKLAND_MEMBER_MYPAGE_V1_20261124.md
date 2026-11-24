# GARAKLAND | 회원 마이페이지 설계·운영 명세 (v1.0)
2026-11-24 · 회원별 데이터 분리 MVP

## 목적
Google 또는 이메일로 Neon Auth에 가입한 회원이 본인의 시연 쿠폰과 즐겨찾기 업소를 여러 기기에서 확인·저장·해제한다.

## 사용 흐름
1. Google 로그인 완료 시 /mypage.html 로 이동한다.
2. 회원은 상단 메뉴의 마이페이지를 누른다.
3. 업소 카드의 하트 버튼을 누르면 회원 UUID에 해당하는 업소만 서버 저장된다.
4. 쿠폰 담기는 회원 UUID와 시연 쿠폰 ID 조합으로 저장된다.
5. 마이페이지의 내 쿠폰, 찜한 업소, 계정 정보 3개 탭을 이용한다.
6. 로그아웃 상태에서는 저장 API가 실행되지 않고 로그인 안내가 표시된다.

## 재사용 자산
- Neon Auth: auth/client.mjs, auth/config.public.json
- 브랜드 UI: brand/app.js, brand/style.css, 공통 헤더 design/global-site-header.js
- 매장·시연 쿠폰 정의: brand/data.js
- 기존 Neon PostgreSQL 연결: db_adapter.py

## 데이터 구조
- member_favorite_stores: user_id TEXT + store_id TEXT PK, created_at TEXT
- member_demo_coupons: user_id TEXT + coupon_id TEXT PK, created_at TEXT
- user_id는 서버에서 검증한 Neon Auth JWT sub 클레임으로만 도출한다.
- 고객의 비밀번호·OAuth 액세스 토큰·이메일은 별도 테이블에 복제하지 않는다.

## API
- GET /api/member/state: 본인 시연 쿠폰·저장 업소 목록
- POST /api/member/favorites: storeId와 action(add/remove)
- POST /api/member/coupons: couponId와 action(add/remove)
- JWKS 서명 및 iss·exp·sub·aud 검증, SQL에서 회원 소유권 제한, 응답 no-store.

## 서비스 경계
- 현재 쿠폰은 시연용 북마크이며 실제 결제·할인·QR 교환권 기능은 아니다.
- 기존 비회원 브라우저 임시 저장(localStorage)은 사용자별 DB로 자동 이전하지 않는다.
- 기존 파일·브라우저 임시 저장은 임의 삭제하지 않는다.
- 실매장 및 실제 쿠폰 연동은 승인·기한·사용내역·사기방지 검증 후 추가한다.

## 검증 기준
- A/B 회원의 쿠폰·즐겨찾기 데이터 격리
- 무인증 API 401, 유효하지 않은 JWT 401, JWKS 오류 시 fail-closed
- 중복 저장 허용 없이 재요청에 대해 멱등성 유지
- 네비게이션 일관성, 로그인/로그아웃, 모바일 UI 점검