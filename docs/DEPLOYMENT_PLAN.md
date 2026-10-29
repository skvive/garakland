# GARAKLAND 배포 기획 (Vercel + Neon)

## 제품 구조 (핸드오프 V7)

| 모듈 | 진입 | 역할 |
|------|------|------|
| Map+3D | `/map.html` | Google Maps (키 없으면 폴백) |
| AR Quest | `/` | AR·쿠폰·시연 주문 |
| Coupon | `/market.html` | 특가·쿠폰·시연 상품권·상인 대시 |
| ERP | `/ops.html` | 출시 차단·증빙·감사 |
| Documents | `/documents.html` | 서류·계약 체크리스트 |
| Share kit | `/api/v7/*` | 광고 문구 복사용 (실발송 차단) |

## 아키텍처

```
[Browser] → Vercel Edge (정적 HTML/CSS/JS/이미지)
         → /api/* → Python Serverless (api/index.py → server.Handler)
         → Neon Postgres (DATABASE_URL, db_adapter.py)
```

- **로컬**: `python server.py` + SQLite (`data/garakland.sqlite`)
- **프로덕션**: Vercel 환경변수 + Neon 연결 문자열
- **실결제·실발송·실GPS 검증**: 기본 차단 유지 (`GARAK_V5_LIVE_MARKETING=0`)

## 필수 환경변수 (Vercel)

| 변수 | 설명 |
|------|------|
| `DATABASE_URL` | Neon pooled connection string |
| `GARAK_ADMIN_TOKEN` | 40+ chars random (ERP·상인키 발급) |
| `GARAK_QR_SECRET` | QR 서명용 |
| `GARAK_PUBLIC_BASE_URL` | `https://garakland.vercel.app` 등 HTTPS |
| `GARAK_V7_MODE` | `demo` |
| `GARAK_V5_OPT_OUT_SIGNING_KEY` | 수신거부 토큰 서명 |
| `GARAK_ENABLE_DEMO` | `1` (시연 데이터) |
| `GOOGLE_MAPS_API_KEY` | (선택) map.html 3D |

## Neon CLI

```powershell
neonctl projects create --name garakland --org-id org-red-cake-60363177
neonctl connection-string --project-id <id> --role-name neondb_owner
$env:DATABASE_URL = "<connection-string>"
python scripts/bootstrap_neon.py
```

## Vercel CLI

```powershell
cd garakland
vercel link --yes
vercel env add DATABASE_URL
vercel env add GARAK_ADMIN_TOKEN
vercel --prod --yes
```

## QA

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Cron: `vercel.json` 15분마다 `/api/v5/admin/dispatch` (관리자 토큰은 POST 본문/헤더 — cron은 별도 CRON_SECRET 연동 권장).

## 출시 전 차단 (핸드오프)

실운영 전 `03_EXTERNAL_CONNECTION_CHECKLIST.md` 전 항목 완료 필요.
