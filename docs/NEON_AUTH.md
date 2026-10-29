# Neon Auth (Managed Better Auth)

## 프로비저닝 (완료)

- Neon 프로젝트: `garakland` (`ancient-grass-26115554`)
- Branch: `main` (`br-billowing-surf-b5bt84al`)
- Auth URL: `auth/config.public.json` 참조
- Trusted domain: `https://garakland.vercel.app`

## 사이트

| 경로 | 설명 |
|------|------|
| `/login.html` | 이메일 가입·로그인 |
| `/auth/banner.mjs` | 홈·마켓 상단 로그인 상태 |

## 로컬 개발

Neon Console → Auth → Trusted domains에 `http://localhost:8769` 추가.

## 사용자 DB

```sql
SELECT id, email, name, created_at FROM neon_auth."user" ORDER BY created_at DESC LIMIT 20;
```

## 다음 단계 (선택)

- Google/GitHub OAuth: Neon Console Auth → Social providers
- API 보호: JWT (`jwks_url` in get_auth) 검증을 Python API에 연결
- `@neondatabase/auth-ui` 컴포넌트로 UI 교체
