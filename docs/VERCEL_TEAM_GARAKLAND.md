# Vercel 팀 프로젝트 (garakland)

## 현재 연결 (CLI 로그인 팀)

| 항목 | 값 |
|------|-----|
| 팀 | `shinkang888-codes-projects` |
| 프로젝트 | `garakland` |
| Production URL | https://garakland.lexid.site (also https://garakland.vercel.app) |
| Project ID | `prj_toA7ObGL6Nn7JzkklP9W0YxPAnIz` |
| Team ID | `team_iqF07oRNVoofJGj4ypBtucPn` |
| GitHub 소스 | https://github.com/skvive/garakland |

로컬:

```powershell
cd E:\currsor_C\blog\garakland
vercel link --yes --project garakland --scope shinkang888-codes-projects
vercel --prod --yes --scope shinkang888-codes-projects
```

## Git 자동 배포

### 방법 1 — Vercel ↔ GitHub (권장)

1. [Project Git Settings](https://vercel.com/shinkang888-codes-projects/garakland/settings/git)
2. GitHub **skvive** 조직에 Vercel 앱 설치 · `garakland` 리포 선택
3. Production branch: `master`

### 방법 2 — GitHub Actions

1. `VERCEL_TOKEN` 시크릿 등록 (Account Token)
2. `docs/vercel-production.workflow.yml` → `.github/workflows/vercel-production.yml`
3. `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`는 리포 Secrets에 이미 등록됨

## 환경 변수 (Production)

`DATABASE_URL`, `GARAK_ADMIN_TOKEN`, `GARAK_QR_SECRET`, `GARAK_V5_OPT_OUT_SIGNING_KEY`,  
`GARAK_ENABLE_DEMO`, `GARAK_V5_LIVE_MARKETING`, `GARAK_V7_MODE`, `GARAK_PUBLIC_BASE_URL`

확인: `vercel env ls --scope shinkang888-codes-projects`
