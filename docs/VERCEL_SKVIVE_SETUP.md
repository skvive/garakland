# Vercel skvive 계정 · Git 연동

## 1. 홈 404 원인 (해결)

`vercel.json`에 `@vercel/python`만 있으면 **정적 HTML이 배포되지 않음**.  
`@vercel/static` 빌드를 추가하고 `/` → `index.html` 라우트를 넣었습니다.

## 2. skvive로 옮기는 방법

### A. Vercel 대시보드 (권장)

1. **skvive** 계정으로 [vercel.com](https://vercel.com) 로그인
2. Add New → Project → Import **skvive/garakland**
3. Environment Variables 복사:
   - `DATABASE_URL`, `GARAK_ADMIN_TOKEN`, `GARAK_QR_SECRET`, `GARAK_V5_OPT_OUT_SIGNING_KEY`
   - `GARAK_ENABLE_DEMO=1`, `GARAK_V5_LIVE_MARKETING=0`, `GARAK_V7_MODE=demo`
   - `GARAK_PUBLIC_BASE_URL=https://garakland.vercel.app` (또는 새 도메인)
4. Deploy → Git 연동 자동

### B. GitHub Actions

`docs/vercel-production.workflow.yml` 내용을  
`.github/workflows/vercel-production.yml` 로 복사한 뒤 push (토큰에 `workflow` scope 필요).

### C. 기존 shinkang888-code 프로젝트

`shinkang888-codes-projects/garakland`는 Git connect 권한 오류로 skvive 리포와 미연동.  
skvive 쪽 신규 프로젝트 또는 Actions로 대체.

## 3. 로컬 CLI (skvive)

```powershell
vercel logout
vercel login
vercel link --scope <skvive-team-slug>
vercel env pull
vercel --prod
```
