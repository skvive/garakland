# GARAKLAND (가락랜드) V7 — Vercel + Neon 배포판

핸드오프: `GARAKLAND_GITHUB_AI_HANDOFF_V7_20261029_COMPLETE.zip` 기반.

## 로컬 실행

```powershell
cd garakland
python server.py
# http://127.0.0.1:8769/market.html
```

## 클라우드

- 배포 기획: [docs/DEPLOYMENT_PLAN.md](docs/DEPLOYMENT_PLAN.md)
- DB: Neon (`DATABASE_URL`) 또는 로컬 SQLite
- 호스팅: Vercel (정적 페이지 + `/api/*` Python 함수)

## 테스트

```powershell
$env:PYTHONPATH='.'
python -m unittest discover -s tests -p "test_*.py" -v
```

## 안전

시연 데이터·모의 상품권·모의 발송만 기본 활성. 실결제·실발송·실운영 전 법·계약·현장 검증 필요.
