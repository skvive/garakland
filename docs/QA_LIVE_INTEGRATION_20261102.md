# GARAKLAND 운영 연동 QA · 2차 기술보고서

- 일자: 2026-11-02 KST
- 대상: `skvive/garakland`, `chatgpt/garakland-web-workspace-20261101`
- 운영 URL: https://garakland.lexid.site
- 정책: Production 기존 배포 보존; SQLite 격리 테스트 + 공개 읽기 전용 API만 확인. Vercel 운영 비밀키/실고객 데이터 출력 금지.

## 운영 API 직접 테스트

GitHub Actions **41335928340** 의 `live-readonly` job에서 네트워크를 통해 직접 검증.

| 경로 | 예상 | 관측 |
|---|---:|---:|
| GET /api/health | 200 | 200 |
| GET /api/v5/public | 200 | 200 |
| GET /api/stores?limit=2 | 200 | 200 |
| GET /api/public/config | 200 | 200 |
| GET /auth/config.public.json | 200 | 200 |
| GET /api/v8/dashboard (무자격) | 403 | 403 |
| GET /api/merchant/qr?shopId=demo-sea (무자격) | 403 | 403 |

최종 **7건 중 7건 통과**. 테스트는 인증 토큰·쿠키·결제·실발송·폼 제출 등을 사용하지 않음. 테스트 코드: `tests/live_readonly_smoke.py`, GitHub Workflow: `.github/workflows/garakland-web-qa.yml`.

## 실제 Vercel 로그에서 확인한 DB 오류 이력

- Production 함수 로그에 2026-11-01 01:50:29 UTC경 `pg8000.exceptions.DatabaseError`, SQLSTATE `26000`, 메시지 `unnamed prepared statement does not exist` 기록.
- PostgreSQL extended-query protocol과 Neon/PgBouncer transaction pooler 사용 환경에서 발생 가능한 유형이다. **이 로그 하나로 운영 DB URL이 -pooler인지 확정할 수는 없다.**
- 당시와 다른 시점에 `/api/v5/public`, `/api/v5/me` 등에 200 기록도 확인됨.
- 선택 기간의 Vercel 집계 runtime error 없음이라는 결과는 과거 로그의 오류 부재를 뜻하지 않음.

### 보완 커밋

`db_adapter.py`에 `pg8000_connection_target()`을 추가.

1. `GARAK_DB_DIRECT_URL`이 존재하면 그것을 우선 사용(실제 DB 연결 시점에만).
2. 그 외에 `DATABASE_URL`이 `-pooler.*.neon.tech` 형식이면 **pg8000 연결에 한해서** Neon 직접 연결 호스트로 변환.
3. Neon 외부 호스트는 변형하지 않음. SSL 인증 유지, 연결 timeout 15초, 기존 커넥션/트랜잭션 정리 보존.
4. 실 URL/비밀번호 로그 출력 금지. `.env.example`에 보안·연결 수 주의사항 명기.
5. `tests/test_db_connection_routing.py`에 pure unit 테스트 5건 추가.

**주의:** 기존 Production `master`에 미배포이므로 운영 환경에서 실제 `26000` 오류가 해결됐다는 판정은 아직 불가. 서버리스 직결은 연결 개수 상한/지연 부하가 증가할 수 있어 운영 롤아웃 전 부하와 연결 수 확인 필요. 장기적으로 pooling-safe driver/adapter도 검토.

## 연결된 Neon 프로젝트 Read Only 확인

사용자가 소유한 두 조직의 `garak*` 프로젝트를 검사한 결과 `garakland` 명칭 Neon 프로젝트 `ancient-grass-26115554`를 찾음.

- Neon 주 브랜치 조회 성공, public schema 27개 테이블 조회 성공.
- 읽기 전용 집계에서 매장 6, 캠페인 4, 관리 모듈 12, 게임 세션 17, 특가 4, ERP 태스크 8건 확인.
- **이 프로젝트가 Vercel 운영 `DATABASE_URL`의 실제 대상인지 아직 연결 식별이 검증되지 않음.** 서로 다른 프로젝트에 대한 확인 결과를 혼용하지 않는다.

## 전체 자동화 재검증

- Python unittest **108건 실행, 107 통과, 1건 선택 라이브러리 검사 건너뜀**.
- 정적 자산 참조 477건 정상, JavaScript 19개 문법 검사 정상.
- 26개 페이지 × 데스크톱/모바일 브라우저 테스트는 별도 `browser-acceptance` job에서 검증 (Actions 결과 확인).

## 최종 인수 판정

- 격리 베타 UI와 핵심 API 기본 smoke: **PASS**.
- 공개 운영 API의 7개 읽기 전용 체크: **PASS**.
- 운영 DB 트랜잭션 안정성 / 연결 소유관계 / 로그인 실제 OAuth / 관리자 역할 및 실사업 데이터 / 현장 GPS·QR / 유상 결제 및 실제 마케팅 발송: **HOLD**.
- Production 배포 `master`를 이 브랜치와 병합하지 않음. PR #2는 Draft 상태 유지.
