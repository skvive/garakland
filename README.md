# 가락랜드 MARKET GROWTH v5.0 BETA — 시장 공동 마케팅·특가 쿠폰·연합 시연권

**2026-10-29 기준 데모 / 시연용 기술 제품. 실제 쿠폰 사용·유료 상품권 발행·전자금융업·대량 광고 발송·배달 주문·시장 모든 점포의 실측 좌표는 상용 개통 전 검증/계약이 필요합니다.**

## 가장 간단한 Windows 실행

1. ZIP 전체 압축 해제 → Python 3.10 이상 설치.
2. `start_windows.bat` 더블클릭 → `http://localhost:8769/market.html` 열기.
3. **오늘의 특가**: 청과·수산·축산·먹거리 카드 → **쿠폰 받기** → Google 지도 길찾기.
4. **내 쿠폰·상품권**: 받은 쿠폰 확인. `30,000 / 50,000 / 100,000원` 시연권 누르면 **결제 없이** 데모 잔액 발급. 안내되는 확인코드를 안전하게 기록.
5. **소식 받기**: 이메일·문자·카카오 채널별로 체크 후 광고 수신동의 저장/철회.
6. **상인 대시보드**: 콘솔의 관리자 토큰 → 매장 키 발급 → 해당 키로 로그인 → 정상가·할인가·한정 수량·시작/종료 시각을 입력하여 쿠폰 예약 발행. 쿠폰번호 사용 승인 / 시연권 카드번호+확인코드+사용 금액으로 모의 결제 / 광고 메시지 일정 등록 / 모의 대량발송 검사.
7. 기존 v4의 AR 탐험 앱은 `/`, Google 지도는 `/map.html`입니다.

> **주의:** `market.html`을 더블클릭하는 `file://` 접속으로는 서버 쿠폰/장부/동의 API가 작동하지 않습니다. 서버를 실행한 뒤 localhost로 열어야 합니다.

## v5 주요 기능 및 실질 검증

| 구성 | 코드 상태 | 상용 운영 조건 |
|---|---|---|
| 특가 공개 / 업종 필터 | 동작 | 실매장 상품·가격 승인 |
| 매장별 쿠폰 발행/예약/중단 | 동작 | 실제 상인 인증/소비자 표시 의무 |
| 쿠폰 1인 1회 발급 및 사용 중복 차단 | 통합 테스트 통과 | 실계정·위변조·고부하 테스트 |
| 쿠폰 → Google Maps 길찾기 | 공식 Maps URL 생성 테스트 통과 | 실점포 실측 GPS·실내 호실 도면 필요 |
| 여러 상점의 연합 시연권 | **모의 잔액**·PIN·가맹승인·사용·취소 장부 동작 | 전금법 법률 검토, 등록/면제 판정, 예치/보호, 실결제·정산 계약 |
| 이메일·SMS·카카오톡 광고 대상 선택 | 채널별 자기동의·동의철회·예약·모의 큐 구현 | 인증된 고객, 수신자격, 공급사 계약, 발신번호·채널 승인 |
| SMTP/SOLAPI 및 카카오 브랜드 메시지용 어댑터 | 서명/요청 페이로드 단위검사 통과 | **실제 발송 미실시**, 승인된 환경에서만 별도 운영 |
| 예약 마케팅 작업 | 서버 실행 중 1분 간격 동의 기반 **모의 발송** | 운영 동의/광고표시/야간/수신거부 정책 승인 |
| 상인별 통계 패널 | 데이터 연결 동작 | 정산·성과 데이터 신뢰성 확보 |
| 기존 AR·지도·시연 주문/게임 | v4 코드 그대로 포함, 12개 회귀 테스트 통과 | 실GPS/카메라/Google API/현장 점포 데이터 검증 필요 |

## v5 파일 구조

- `market.html` + `market/theme.css` + `market/ui.js`: 신디자인 가락시장 쿠폰/상품권/상인 마케팅 대시보드.
- `market/core.py`: 쿠폰, 예약, 할인, 고객 동의, 중복 차단, 가맹점 승인, 시연 상품권 잔액 및 원장, 해제 및 사용 확인 API.
- `market/providers.py`: 외부 SMTP 이메일 및 SOLAPI SMS/카카오 브랜드 메시지용 **옵션형** API 어댑터. 실제 발송은 기본 차단.
- `unsubscribe.html`: 서명 토큰이 있는 광고 수신거부 랜딩.
- `server.py` 및 `registry_server.py`: 기존 가락랜드 및 신규 v5 API 통합, 표준 라이브러리 HTTP+SQLite 서버.
- `assets/v5`: AI 생성 시장/상품/시연권 이미지 포함 (실제 점포 이미지 아님).
- `game/`, `src/`, `map.html`, `index.html`: 이전 AR QUEST/Google Maps 3D/시장 탐방 프로그램 **보존**.
- `tests/test_growth_v5.py`, `tests/test_marketing_adapters.py`, `tests/test_beta.py`: API 통합·보안·기존 회귀 검수.
- `tests/browser_offline_v5.py`: 1440px/390px Chromium 화면·클릭 검증 (브라우저 네트워크 제한 때문에 Python 브리지로 실제 로컬 API 호출).

## 테스트 실행

```bash
python -m unittest tests.test_growth_v5 tests.test_marketing_adapters tests.test_beta -v
# Chromium 설치 시(이 검수 환경에서는 시스템 chromium 바이너리 이용)
python tests/browser_offline_v5.py
```

2026-10-29 검수 기록: **서버/어댑터/기존 기능 37개 테스트 통과**, PC·모바일 렌더링 및 4개 앱 화면 전환과 쿠폰/동의 UI 브라우저 검사 통과. 실제 이메일/SMS/카카오 전송이나 실돈 결제, 실점포 GPS, Google 지도 앱에서의 최종 이동 과정은 이 환경에서 검증하지 않았습니다.

## 외부 API 및 비밀키

- **Google 지도:** 본 베타의 길찾기는 `https://www.google.com/maps/dir/?api=1&destination=...&travelmode=walking` 공식 URL 사용. 외부 길찾기 링크 자체에는 API 키가 필요하지 않지만 이전 v4의 자체 삽입 Google 3D 지도는 별도 Cloud 키가 필요합니다. 검증된 점포 좌표가 없는 경우 **가락시장 공통 주소**만 안내합니다.
- **발송:** `market/providers.py`는 SMTP 메일, SOLAPI SMS/브랜드 메시지의 HMAC-SHA256/페이로드를 예시로 구현합니다. 단체 카카오톡 **그룹방 무단 자동발송** 기능이 아닙니다. 실제 발송에는 제휴 채널 및 발송 사업자와 동의자격이 필요합니다.
- **상품권:** **실제 결제 API를 연결하지 않았습니다.** 시연권 카드의 `simulated_paid`는 가상 구매 금액이고 `balance`는 시연 잔액입니다. 환불은 실제 환급이 아니라 거래 취소 원장 복원입니다. 상용 전환 시 소비자 자금 보호 및 선불업 적용 여부를 법무/금융 전문가와 검토해야 합니다.
- **비밀번호:** 관리자 토큰은 실행 콘솔에 무작위 생성되며, 상인 키는 매장별로 새로 발급합니다. 실제 운영 시 조직별 계정/OAuth/MFA/HTTPS/CSRF 대책과 정밀 권한관리 필요.

### 프로덕션 대비 환경변수 예시 (베타에서 실제 광고/결제 활성화하지 마세요)

```text
GARAK_DB_PATH=/secure/path/garakland.sqlite
GARAK_ADMIN_TOKEN=<random-long-secret>
GARAK_V5_OPT_OUT_SIGNING_KEY=<persistent-random-secret-for-signed-unsubscribe>
GARAK_PUBLIC_BASE_URL=https://example.your-approved-domain.kr
GARAK_V5_LIVE_MARKETING=0
GARAK_V5_APPROVED_LIVE_SEND=NO
SOLAPI_API_KEY=<provider-issued>
SOLAPI_API_SECRET=<provider-issued>
SOLAPI_SENDER=<pre-registered-number>
SOLAPI_KAKAO_PF_ID=<approved-channel-id>
GARAK_SMTP_HOST=<approved-smtp-server>
GARAK_SMTP_FROM=<registered-sender-email>
GARAK_SMTP_USER=<smtp-user>
GARAK_SMTP_PASSWORD=<smtp-password>
```

**초기값에서는 실발송과 실결제가 비활성화되어 있습니다.** 개발 어댑터를 임의로 활성화한다고 자동으로 합법적인 금융·광고 서비스가 되는 것은 아닙니다. 실발송은 관리자 명시적 요청·서버 측 공급사 심사·정식 수신 동의·무료 수신거부 등 선행 조건이 확보된 배포 환경에서만 가능합니다.

## 법·운영 이슈

1. **금융위 2025.3 선불업 등록 공지:** 가맹점이 둘 이상인 상품권은 단일 상점 선수금과 구분해 전자금융거래법 검토가 필요합니다. 발행잔액/연간 발행액 등 면제 기준을 포함해 실제 운영 주체와 적용 범위를 검토하세요. 면제 대상이라고 고객 충전금 보호가 보장되지는 않습니다.
2. **KISA 2026.3 개정 스팸 가이드:** 쿠폰 발급·소멸 알림도 광고성 정보가 될 수 있습니다. 가입시 약관 일괄 체크로 광고 동의를 대신하면 안 됩니다. 이메일·문자·카카오톡 수신동의를 별도로 받는 것이 안전합니다. 광고 표기, 발신자/수신거부 정보, 야간 제한, 동의 증빙을 검증해야 합니다.
3. **Kakao Business:** 쿠폰·특가 프로모션은 정보성 알림톡이 아니라 적합한 **광고성 브랜드/채널 메시지**로 운영해야 합니다. 승인 채널, 채널 친구 또는 광고 동의 등 적법한 수신자 자격이 필요합니다.
4. **지도·GPS:** 내장 Google 지도와 실외 경로 URL은 실내 호실 길찾기를 제공하지 않습니다. 서울시농수산식품공사 승인 도면 및 정확한 출입구/호실 좌표 확인이 필요합니다.
5. **운영 수준 추가:** 신원확인, 실제 결제 이벤트 기반 잔액 발행, 부분취소, 정산/세금계산서, PCI/PG/Webhook 서명, 속도제한, 악용 탐지, 고객센터, 개인정보 암호화 및 파기, 정기 보안 점검을 추가해야 합니다.

공식 출처:
- Google Maps URL: https://developers.google.com/maps/documentation/urls/get-started
- 금융위원회: https://fsc.go.kr/po010106/84178
- KISA 안내: https://xn--3e0bx5e6xzftae3gxzpskhile.kr/402/form?page=1&postSeq=2577
- 카카오 브랜드메시지 안내: https://docs.kakaoi.ai/kakao_i_connect_message/bizmessage/api/api_reference/
- SOLAPI 메시지 발송: https://solapi.com/developers/api/messages
- SOLAPI 인증: https://solapi.com/developers/api/authentication-api-key
