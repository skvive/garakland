# 가락랜드 웹 전체 QA / 고객 인수 전 사전점검
**검수일:** 2026-11-01 (KST)  
**저장소:** `skvive/garakland`  
**원본:** `master` `1724924ee29c2695d69da55a7b757804ebc6116b`  
**검수 브랜치:** `chatgpt/garakland-web-workspace-20261101`  
**최종 증빙 커밋:** `60597b2b50381a2a89e0a19d51a1c219fdcedab2`  
**운영배포:** 미변경. 별도 Vercel Preview `dpl_8jH1FWboGB19nnqEfYd899Qdmsbk` READY.  

## 1. 객관적 증빙 (실제 도구 수행)

- GitHub Actions: https://github.com/skvive/garakland/actions/runs/41319273070
- 고립된 SQLite 데모 + 로컬 HTTP 서버에서 **26개 URL × 1440×900 / 390×844 = 52개 브라우저 화면** 로딩, 본문 가시성, JS 예외, 내부 정적 자산 404, 수평 오버플로우 검사.
- **실제 Chromium 클릭 157회, 해당 smoke 검사에서 실패 0건**. 주요 페이지의 탭/필터/링크 선택 동선 포함. *모든 DOM 버튼을 전수 클릭한 기록은 아니다.* 결제/민감 데이터 변이/실제 외부 알림은 제외.
- Python unittest 103개 실행: **102 passed / 1 skipped / 0 failed**. 건너뛴 검사는 선택적 이미지 라이브러리(OpenCV/NumPy/Pillow) 환경의 사진 매칭 테스트.
- 로컬 HTML·CSS 참조 477건, JS 19개 파일 문법 검사: 0건 실패.
- 자동 촬영 원본: 같은 GitHub Actions run의 **`garakland-52-page-screenshots`** 아티팩트(52 PNG, 약 44.7 MB, 7일 보존).
- 기준 SHA에 대한 Vercel Preview: https://garakland-3xc6cfdjo-shinkang888-codes-projects.vercel.app — 빌드 READY. SSO 설정으로 직접 접근 시 로그인이 필요할 수 있음.

## 2. 페이지별 브라우저 확인 범위

| 영역 | 경로 | 1440px | 390px | 중요 기능 보완/조건 |
|---|---|---|---|---|
| 브랜드 홈 | /index.html | PASS | PASS | 시연용 데이터 |
| 플랫폼 홈 | /home.html | PASS | PASS | 특가 API 응답 실운영 검증 필요 |
| 프로모션 | /market.html | PASS | PASS | 쿠폰/방송 실제 발송 비활성화 |
| 지도 | /map.html | PASS | PASS | Google Maps API, 현장 GPS 별도 검증 |
| AR 탐험 | /ar-quest.html | PASS | PASS | 카메라/QR 실제 장치 검증 별도 |
| 매장 검색 | /stores.html | PASS | PASS | 가상 매장 목록 |
| 매장 상세 | /store.html?id=demo-sea | PASS | PASS | 메뉴/가격 시연 |
| 시장 구역 지도 | /market-map.html | PASS | PASS | 테마형 도식, 실제 실내좌표 아님 |
| 쿠폰 | /coupons.html | PASS | PASS | localStorage 브랜드 시연 |
| 이벤트 | /events.html | PASS | PASS | 가상 행사 |
| 브랜드 소개 | /market-guide.html | PASS | PASS | 브랜드 소유/업력 확인 필요 |
| 상인센터 | /merchant-center.html | PASS | PASS | 신청서는 브라우저 임시 저장 |
| 통합 운영 허브 | /hub.html | PASS | PASS | 브라우저 캡처는 비인증 초기 화면 |
| ERP | /ops.html | PASS | PASS | 일부 API는 독립 테스트로 확인 |
| 법률·서류 | /documents.html | PASS | PASS | 제출자료 진위 별도 |
| Neon 로그인 | /login.html | PASS | PASS | 실제 Google OAuth 종단간 테스트 별도 |
| 광고 수신거부 | /unsubscribe.html | PASS | PASS | 실제 서명 토큰·발송 채널 검증 별도 |
| 디자인 검수 갤러리 | /design_gallery.html | PASS | PASS | 유효 이미지로 연결 수정 |
| 디자인 시스템 | /design/design-system.html | PASS | PASS | 디자인 가이드용 |
| 홈 템플릿 선택 | /design/home-templates.html | PASS | PASS | 내부 시안 도구, 일부 템플릿 미리보기 빈 영역 검토 필요 |
| 보관 캡처 | /previews/index.html | PASS | PASS | 과거 렌더 스냅샷 |
| 사업 자료실 | /brand_strategy_docs/index.html | PASS | PASS | 비공식 기획자료 |
| 사업계획서 | /brand_strategy_docs/business-plan.html | PASS | PASS | 모바일 폭/에셋 보완 |
| 투자제안서 | /brand_strategy_docs/investment-proposal.html | PASS | PASS | 모바일 폭/에셋 보완 |
| 브랜드북 | /brand_strategy_docs/brandbook.html | PASS | PASS | 이미지/디자인 CSS 복구 |
| 저작권 준비서류 | /brand_strategy_docs/copyright-dossier.html | PASS | PASS | 권리/출처 별도 확인 |

위 PASS는 **브라우저 smoke test** 통과를 의미한다. 비즈니스 성과, 도메인 운영 상태, 정산 계약, 데이터 정확성, 실제 관리자 업무 승인 또는 보안 적합성까지 통과했다고 해석하지 않는다.

## 3. 확인된 결함과 수정사항

1. 관리자 v8의 GET 요청에서 정의되지 않은 `body`를 읽던 잘못된 분기를 삭제하고 알 수 없는 API에 JSON 404 제공; 회귀 테스트 신규 추가.
2. `game/app.js`·`ar-quest.html`의 잘못된 상대경로로 인해 `/game/assets/editorial/*.webp`를 요청하던 AR 이미지 404 수정.
3. 브랜드 전략 문서 5개에서 CSS/JS 링크가 존재하지 않던 문제 해결(새 CSS/JS 추가), 브랜드 이미지 19곳을 실제 저장소 자산으로 전환.
4. 디자인 갤러리의 존재하지 않는 V4 PNG 18개 참조를 실제 `/previews/` 촬영 보관 이미지 16장으로 교체. 미보유 V5 스크린샷과 관련하여 명확한 과거 자료 안내 유지.
5. 디자인 토큰 누락 브랜드 페이지 8개 수정, 디자인 시스템 회귀 통과.
6. 모바일 수신거부 가로 넘침, 사업계획서·투자제안서의 모바일 폭 문제 수정.
7. Neon 로그인 UI: 비동기 네트워크/설정 오류 안내, 중복 제출 방지, 클라이언트 초기화 재시도 구현. **실제 공급자 로그인 정상 작동 주장 금지**.
8. `tests/test_adapt_sql.py`가 테스트 모듈 import 시 전체 프로세스 `DATABASE_URL`을 오염시키던 테스트 환경 버그 수정.
9. `scripts/web_quality_gate.py`, `tests/browser_site_acceptance.py`, GitHub Actions 품질 게이트와 52장 스크린샷 증빙 자동화 추가.

## 4. 인수 전 차단 위험 / 남은 검수 작업

| 우선순위 | 상태 | 출고 전 별도 증빙이 필요한 항목 |
|---|---|---|
| P0 | HOLD | 실환경 Neon Auth 로그인/Google OAuth 리디렉션/세션/로그아웃, 권한 오류/보안 테스트 |
| P0 | HOLD | 운영 Neon DB 연결에서 실제 영속성·재시도·트랜잭션·초기화 검증, 개인정보 검토 |
| P0 | HOLD | 실제 상인 승인 자료/점포 위치 GPS/상품가/재고/쿠폰 유효성 및 결제·정산 계약 |
| P0 | HOLD | 실물카메라 QR/GPS 위치 허용·거부·접근성·정확도 검증; 사진 인식 OpenCV 선택 테스트 skipped |
| P1 | 확인 필요 | 실제 Google Maps API 키, 할당량, 3D 환경/지도 타일/외부 링크 확인 |
| P1 | 확인 필요 | 상인별 승인·구독/마케팅 SMS·카카오·이메일 전달, 수신거부 token 서명과 발송 보장 |
| P1 | 확인 필요 | 색 대비, 키보드 탐색, 스크린리더, 실제 기기(삼성 Android/iOS) 및 네트워크 지연 성능의 심화 검수 |
| P2 | 확인 필요 | 디자인 템플릿 편집기 내부 미리보기 플레이스홀더 교체 |

**납품 판정:** 정적 웹/UI·격리 서버 베타 테스트 기준 **PASS**. 실제 운영 서비스 및 고객 납품 최종 승인 기준 **HOLD**. 미확인 실외부서비스를 임의로 연결하거나 유상 결제·문자 발송을 활성화하지 않는다.

## 5. 반복 실행

```bash
python -m pip install 'pg8000>=1.31,<2' requests playwright
python -m playwright install chromium
python scripts/web_quality_gate.py
python -m unittest discover -s tests -p 'test_*.py' -v
node tests/test_navigation.mjs
QA_CAPTURE_SCREENSHOTS=1 python tests/browser_site_acceptance.py
```

증빙 원본은 Actions 아티팩트에서 다운로드. 비밀키/API 토큰, 실제 개인정보는 CI 테스트에 반입하지 않는다. 운영 원본 `master`와 `garakland.lexid.site` 변경 없음.
