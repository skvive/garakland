# 운영 연동 체크리스트 (상용 전 필수)

> 법·계약·현장 검증은 **코드로 대체 불가**. 아래는 진행 상태 추적용입니다.  
> 최종 갱신: 2026-10-29

| # | 항목 | 상태 | 기술/운영 메모 |
|---|------|------|----------------|
| 1 | 서울시농수산식품공사 점포 및 배치도 사용권한 계약 | ⬜ 미완 | 시연 도면·AI 이미지 사용 중, 공식 도면 권한 없음 |
| 2 | 실제 점포 및 상인 참여계약서 원본 서명 | ⬜ 미완 | demo-* 시연 매장만 시드 |
| 3 | 건물별 입구·점포 GPS·실내 층별 호실 현장 검증 | ⬜ 미완 | `coordinateStatus=unverified` 기본, ERP GPS 검수 UI만 |
| 4 | Google Maps JS API 키, 청구, 사용제한, 프라이버시 표시 | 🟡 부분 | 길찾기 URL 동작; 3D 임베드는 `GOOGLE_MAPS_API_KEY` Vercel env 필요 |
| 5 | HTTPS·도메인·운영자·상인 인증(MFA)·재해복구 | 🟡 부분 | HTTPS(Vercel), `GARAK_ADMIN_TOKEN` 시크릿; MFA·DR 미구현 |
| 6 | 개인정보처리방침·광고 동의/철회·수탁사 계약 | 🟡 부분 | v5 동의/철회·`unsubscribe.html` 구현; 법무 문서·수탁 계약 미체결 |
| 7 | 이메일/문자/카카오 발송업체 승인·발신번호·수신거부 | 🟡 부분 | 어댑터·모의 큐만; `GARAK_V5_LIVE_MARKETING=0` |
| 8 | 선불전자지급수단·PG·환불·정산 | ⬜ 미완 | 시연권만, 실결제 API 없음 |
| 9 | 물류/배달 제휴·재고·클레임 | ⬜ 미완 | 시연 주문만 |
| 10 | 접근성·모바일 GPS/카메라·3D·현장 인수 | 🟡 부분 | 반응형 UI; 현장 QA 미실시 |

## 배포·연동 (2026-10-29)

- [x] GitHub `skvive/garakland`
- [x] Vercel **`shinkang888-codes-projects/garakland`** → https://garakland.vercel.app
- [x] 로컬 `vercel link` (`.vercel/project.json`)
- [x] Neon + Vercel env (`DATABASE_URL`, `GARAK_*`, `GARAK_PUBLIC_BASE_URL`)
- [x] GitHub Secrets: `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` (Actions용)
- [ ] **`VERCEL_TOKEN`** — [Vercel Account Token](https://vercel.com/account/tokens) 발급 후  
  `gh secret set VERCEL_TOKEN --repo skvive/garakland`
- [ ] **Git 자동 배포** — Vercel 대시보드에서 Git 연결 (아래) 또는 Actions 워크플로

### Vercel Git 연결 (skvive/garakland)

1. https://vercel.com/shinkang888-codes-projects/garakland/settings/git  
2. Connect **GitHub** → Organization **skvive** 에 Vercel 앱 권한 부여  
3. Repository **`garakland`** 선택 → Production branch `master`

> CLI `vercel git connect`는 Vercel 앱이 skvive 리포에 쓰기 권한이 없으면 400 오류.

## GitHub Actions 시크릿 설정 (skvive 리포)

1. [Vercel Account Tokens](https://vercel.com/account/tokens) — **skvive** 계정으로 발급 → `VERCEL_TOKEN`
2. 프로젝트 Settings → General → Project ID → `VERCEL_PROJECT_ID`
3. Team Settings → Team ID → `VERCEL_ORG_ID` (개인이면 User ID)
4. Repository `skvive/garakland` → Settings → Secrets → Actions 에 등록

## 출시 차단 게이트 (코드)

- `GARAK_V5_LIVE_MARKETING=0`, `GARAK_V5_APPROVED_LIVE_SEND=NO`
- `ops.html` ERP 출시 승인 워크플로 (법적 승인 아님)
