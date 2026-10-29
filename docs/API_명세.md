# GARAKLAND V3 API (Local Beta)

공통: `http://127.0.0.1:8769`, JSON. POST에는 `Content-Type: application/json`, `X-Garak-Client: 1`. 식별은 임시 익명 세션 쿠키로 수행; 영구 회원 인증 미구현.

| Method | Path | Function | Authentication |
|---|---|---|---|
| GET | `/api/experience` | 공개 매장·메뉴·이미지·캠페인 | 공개 |
| GET | `/api/progress` | 본인 XP·배지·일별 방문 | 익명 쿠키 |
| GET | `/api/wallet` | 본인 쿠폰 | 익명 쿠키 |
| POST | `/api/demo/checkin` | 가상 매장 시연 방문 | 로컬 데모 활성화 필요 |
| POST | `/api/checkin` | 상인 QR+GPS 실방문 기록 | QR 서명 + 매장 검증 좌표 + 75m 이하 GPS 정확도 + 반경 110m |
| POST | `/api/recognize` | 이미지 vs 등록 기준 사진 ORB 대조 | OpenCV + NumPy 필요 |
| POST | `/api/coupons/claim` | 쿠폰 발행/기간/재고/중복 검증 | 익명 쿠키 |
| GET/POST | `/api/orders` | 주문 **시연 요청** 조회/저장 | 익명 쿠키 |
| GET | `/api/merchant/qr?shopId=...` | 유효기간 3분 QR 서명 생성 | 상인 키 또는 관리자 토큰 |
| POST | `/api/merchant/campaign` | DAILY/WEEKLY/ONCE 쿠폰 캠페인 발행 | 상인 키 또는 관리자 토큰 |
| POST | `/api/merchant/redeem` | 쿠폰 사용 및 재사용 방지 | 상인 키 또는 관리자 토큰 |
| POST | `/api/merchant/order-status` | 주문 시연 승인/취소 | 상인 키 또는 관리자 토큰 |
| POST | `/api/merchant/profile` | 블로그·공식 주문 URL·메뉴 정보 | 상인 키 또는 관리자 토큰 |
| POST | `/api/merchant/upload-photo` | 기준 사진·메뉴판·대표사진 등록 | 상인 키 또는 관리자 토큰 + Pillow |
| POST | `/api/admin/merchant-key` | 1회 표시되는 비밀 상인 키 생성 | 관리자 토큰 |
| POST | `/api/admin/metadata` | 관리자의 메뉴·주문 URL 수정 | 관리자 토큰 |
| GET | `/api/stores` | V2 점포 CSV 관리 데이터 | 공개(V2) |
| POST | `/api/import` | V2 점포 대장 등록 | `X-Garak-Admin-Token` |
| GET | `/map.html` | 기존 Google 위성/3D 지도 UI | 공개, API 키 별도 |

POST 예시:

```json
{"shopId":"demo-sea","qrToken":"demo-sea.1790000000.xxxxxxx","latitude":37.49,"longitude":127.11,"accuracy":10}
```

`/api/recognize`: `{"image":"<base64 JPEG>"}`. `/api/merchant/upload-photo`: `{"shopId":"...","kind":"reference|menu|hero","image":"<base64 JPEG>"}`. `/api/merchant/profile`: `{"shopId":"...","blogUrl":"https://...","deliveryUrl":"https://...","menu":[{"name":"메뉴","price":9900}]}`.

실주문 API, 결제/배달 시스템은 외부 연동 전 **모의 상태값(`DEMO_REQUESTED`, `DEMO_ACKNOWLEDGED`, `DEMO_CANCELLED`)**만 제공한다.
