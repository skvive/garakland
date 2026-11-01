# 가락랜드 디자인·반응형 고객 납품 QA 결과 — 2026-11-01

## 검수 기준
- 원본: skvive/garakland, protected working convention: only `chatgpt/garakland-android-workspace-20261101` writes. `master` unchanged.
- 실행 방법: 실제 코드의 Python localhost 시연 서버 + **격리된 임시 SQLite**. Chrome/Playwright screenshot, real JS click events.
- 디바이스: 1440×900 desktop, 390×844 mobile, 360×780 compact.
- 접근 경로: index, home, stores, store, coupons, events, market-map, market-guide, merchant-center, market, ar-quest, map, ops, hub, login, documents, unsubscribe, design_gallery = 18 paths.

## 수치 검증
| 항목 | 수정 전 | 수정 후 |
|---|---:|---:|
| URL/뷰포트 기본 화면 | 54 | 54 |
| 추가 내부 탭 화면 | 0 | 28 (시장 특가 6, ERP 10, AR 12) |
| 가로 넘침·이미지 유실·HTTP/브라우저/내부뷰 검수 장애 | 5개 기본 화면 조합 | 0 |
| 첫 뷰포트에서 38px 미만 작은 컨트롤 자동 감지 | 213 | 62 |
| 실제 모바일 클릭 검사 | — | 23 통과 |

최종 CI(strict, 모든 화면): https://github.com/skvive/garakland/actions/runs/41318803788
별도 SQL 및 백엔드 회귀 테스트: https://github.com/skvive/garakland/actions/runs/41318690783

## 화면별 수정·판정
1. 브랜드 홈(index): 메뉴/검색 터치 높이 및 이미지 크롭, 운영 허브 고정 버튼을 모바일 탭과 겹치지 않도록 이동.
2. 스튜디오 홈(home): 히어로 사진 초점, CTA 및 헤더 최소 터치 영역, 안내 이미지 비율 보정.
3. 매장 탐색(stores): 카드 이미지 4:3, 필터칩 최소 44px, 모바일 탐색 및 빈 검색 결과 클릭 검증.
4. 매장 상세(store): 상세 이미지 반응형 높이, 줄바꿈, 브레드크럼 터치 영역.
5. 쿠폰/이벤트(coupons/events): 버튼 및 필터 터치 영역, 데모 쿠폰 담기 및 이벤트 카테고리 클릭 검사.
6. 테마지도/시장 이야기(market-map/market-guide): 모바일 360px 및 이미지/콘텐츠 경계 검사.
7. 상인센터(merchant-center): 하단 고정 운영허브 CTA 위치 교정.
8. 오늘의 특가(market): 메인 히어로/상품 이미지 비율, 모바일 버튼 및 접히는 내비, 지갑·소식·상인 내부 탭별 검수.
9. AR 퀘스트(ar-quest): 탐험·매장찾기·미션·쿠폰·주문·상인·가이드 UI, 내부 탭 렌더와 모바일 전용 내비 확인.
10. 3D 지도(map): 지도 이미지 contain 정책, 작은 메뉴 및 버튼 터치 영역.
11. ERP(ops): 업무 보드·서류·상품·정산·체크리스트 탭별 모바일/PC 검수, 사진 가독성 및 스크롤.
12. 운영 허브(hub): 비로그인 상태 대시보드 잠금 UI/헤더/레이아웃 확인. **인증 후 내부 화면은 별도**.
13. 로그인(login): 폼 영역과 모바일 터치 타깃.
14. 운영문서(documents): 파일 다운로드 CTA 카드 간격/터치 타깃.
15. 광고수신거부(unsubscribe): padding 포함으로 발생한 모바일 31~34px 가로 넘침 해결, 100dvh/box-sizing 적용.
16. 갤러리(design_gallery): 없는 v4 PNG 18건을 지우고 저장소에 있는 브랜드 페이지 미리보기 16건으로 교체.

## 비판적 남은 과제 및 출시 게이트
- 여전히 62개 **38px 미만 컨트롤 감지**가 남습니다. 이에는 작은 텍스트 내비와 컨텍스트 링크가 포함되며, 자동 계측 수치만으로 WCAG 터치 타깃 전수 합격이라고 판단하지 않습니다.
- 매장 이미지는 실점포 증빙이 아닌 AI 시연·샘플 사진. 실제 이미지 라이선스 및 가맹점 계약, 메타데이터 확보 필요.
- 본 검수는 데모 DB 기반 실제 Chromium 렌더 및 제한된 클릭 검사로서 운영 Neon DB, 실제 카메라·GPS·Google 3D, 실결제·광고발송, 관리자 실계정 인증 뒤 내부 화면, 실제 Android 기기의 다중 해상도/접근성 검수는 포함하지 않습니다.
- 실제 고객 납품·상용 개통 전 개인정보처리, 로그인, 정확한 매장 좌표, 금융·마케팅 운영 조건을 별도 승인/테스트해야 합니다.
- 웹 코드 변경과 별도 Android APK 래퍼가 웹 최신 디자인을 네트워크로 로드하는지는 정식 사이트 배포 및 실단말 후 최종 확인해야 합니다. 이번 커밋은 운영 배포를 자동으로 요청하거나 실행하지 않았습니다.
