# v3.1 쿠폰 → Google 지도 내비게이션 연동

## 고객 동선
1. 쿠폰을 받으면 길안내 창이 자동 표시된다. 받지 않고 쿠폰 화면에서 `위치 안내`를 눌러도 된다.
2. `내 쿠폰 지갑`에서 쿠폰 번호 표를 누르면 구역·층·호실·길찾기가 표시된다.
3. `🧭 이 매장으로 길찾기`를 누르면 공식 Google Maps URL이 새 창 또는 스마트폰 지도 앱에서 열린다.
4. 상인은 기존 쿠폰 번호를 입력해 쿠폰을 사용 처리한다. 지도 링크를 누른 것만으로 쿠폰이 소모되지 않는다.
5. 매장 간판을 AR 카메라로 인식한 후에도 `Google 지도 길안내` 버튼이 표시된다.

## 위치 정확도와 Google 지도 범위
- 좌표가 검증된 **실제 매장**: Google 지도 목적지로 등록된 위·경도 사용.
- 좌표 검증 전인 실제 매장: 매장 좌표를 조작하지 않으며 **가락시장 공통 주소**까지 길찾기. 층·호실을 같이 표시.
- 가상 시연 매장: 실제 매장이 아니므로 Google 지도는 **가락시장**까지 길찾기 시연만 함. 시연 쿠폰은 실제 사용 불가.
- Google 지도 외부 실행에는 API 키가 필요 없음. 사이트 내 Google 위성/3D 렌더링에는 별도 API 설정 필요.
- Google 지도는 개별 실내 점포의 층·호실 경로를 자동 보장하지 않음. 실제 실내 내비게이션은 공식 층별 평면도·실측 데이터 확보 후 구현할 별도 기능.

## 연결 규칙 및 유지 보수
- `wallet.campaign_id` → `campaigns.shop_id` → `stores.id` 관계. 쿠폰 → 올바른 매장 자동 연결.
- GPS `coordinateStatus='verified'`인 실매장만 위·경도를 직접 목적지로 사용.
- Google Maps URLs `https://www.google.com/maps/dir/?api=1&destination=...&travelmode=walking&dir_action=navigate`.
- 출발지 `origin`은 의도적으로 생략: Google 지도 앱이 사용자의 현재 위치를 사용하거나 출발지 입력을 요청함. 앱 서버가 GPS 기록을 저장할 필요 없음.
- 위치 업데이트는 현재 `POST /api/import`의 인증된 관리자 데이터 등록 기능 이용. 새 매장 좌표는 실측과 공식 자료 검수 후 `coordinateStatus=verified`로 표시.
- 상인에게는 QR 또는 점포 ID를 발급하고 담당 매장 좌표와 쿠폰 캠페인 연결 여부를 검수할 것.

## 자동검증 범위
- `node tests/test_navigation.mjs`: URL 구성·검증 좌표·대체 목적지·악성 travelmode 문자열 검증.
- `python -m unittest discover -s tests -p 'test_beta.py' -v`: 기존 주문/쿠폰/스탬프 서버 통합.
- 브라우저에서 쿠폰 발행·쿠폰 지갑 클릭·길안내 버튼 이동 경로·PC/모바일 레이아웃을 추가 점검.
- Google 지도 외부 서버의 경로 계산과 스마트폰 네이티브 지도 앱 동작은 여기서 보장할 수 없음. 현장 네트워크·실측 위경도·기기별 검사 필요.

## 출처
Google Maps URLs, https://developers.google.com/maps/documentation/urls/get-started (2026-10 확인)

## v3.1 오프라인 브라우저 검수
Chromium UI 모의 테스트에서 1440px/390px 페이지 모두 쿠폰 발행→안내창→Google 지도 URL 생성 및 쿠폰 지갑 재방문, 실매장 검증 좌표 사용, 가상매장 공통 위치 전환, JavaScript 오류 없음, 가로 넘침 없음이 확인됨. 실제 Google 지도 사이트/지도 앱을 호출하는 기기별 테스트는 미수행.
