# GARAKLAND 디자인 릴리스 · 2026-11-02

**기준:** 운영 중이던 Vercel 프로덕션 커밋 `c4c7c968ed1c44369dc3f0c78e81618cb4695191`. 기존 테마파크 브랜딩, Android 작업, 운영 백엔드, 인증/DB/결제 코드는 보존.

**릴리스 브랜치:** `release/garakland-design-20261102`.

- 7개 고객 페이지에 공통 디자인 토큰 로드 (기존 `garakland-themepark.css`, `delivery-polish.css` 유지).
- AR 탐험 콘텐츠의 상대 이미지 경로를 배포 루트 기준으로 교정.
- SPA 가이드/미션 해시 링크 직접 진입을 연결하고 디자인 템플릿 앵커 정리.
- 실제 존재하지 않는 V5 갤러리 이미지 참조를 저장된 이미지와 라이브 페이지 링크로 대체.
- 수신거부 페이지 390px 가로 넘침 보완.
- 브랜드 사업자료실 5개 페이지의 이미지·CSS·JS 경로 복구. 가락한상 브랜드북·기획 문서는 실제 사업권리/계약자료와 별도 검증 필요.
- 새로운 로고/메인 브랜딩으로 되돌리지 않고 **이미 운영 중인 테마파크 디자인** 보존.
- 품질 검증: `scripts/web_quality_gate.py`와 `tests/delivery_page_audit.py --strict`를 릴리스 브랜치에서 GitHub Actions 실행.

**배포 제한:** 이 브랜치에는 작업공간의 실험적 `db_adapter.py`, `server.py`, Neon Auth 변경, 쿠폰/결제 변경, Android 소스를 반영하지 않음. 새 운영 배포는 릴리스 검증 통과 이후 진행. 
