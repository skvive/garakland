# v7 API

- `GET /api/v7/meta` — 버전, demo/review 상태, 외부서비스 차단 상태
- `GET /api/v7/share-kit?offerId=<식별자>` — 활성 특가의 광고용 문구/Google 길찾기 링크; 자동발송 없음
- `GET /api/v7/readiness` — `X-Garak-Admin-Token` 관리자 헤더 필수, 점포 데이터 통계·출시 차단 항목

시연 모드: `GARAK_V7_MODE=demo` (기본)
검토 모드: `GARAK_V7_MODE=review` (시연 쿠폰 대외 노출 제외)
실결제·광고발송 활성화 명령은 제공하지 않습니다.

공유용 URL: HTTPS 도메인 구성 시만 `GARAK_PUBLIC_BASE_URL=https://verified.example.com` 을 설정합니다. 미설정 시 복사 문구에는 Google 길찾기 URL만 포함됩니다.

테스트:
```
python -m unittest discover -s tests -p 'test_*.py' -v
node tests/test_navigation.mjs
```
