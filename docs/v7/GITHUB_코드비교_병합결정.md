# GitHub 비공개 저장소 비교 및 안전 병합 결과 (v7)

확인 일자: 2026-10-29. GitHub 연결 계정 `shinkang888-code`, `skvive`에 접근하여 소유/접근 가능한 저장소를 살폈습니다. GitHub 검색 API는 일부 호출이 422 오류를 반환하여 전체 저장소·브랜치·파일에 대한 전수 검증은 하지 못했습니다.

## 확인한 실제 저장소

| 연결된 저장소 | 실제 확인 파일 | 참고한 요소 | 병합 방식 |
| --- | --- | --- | --- |
| `shinkangteam/skvive` (비공개) | `README.md`, `app/actions/switch-mode.ts`, `lib/db/schema.ts` | 시연/실운영 자료 식별과 전환 승인 | v7 `demo/review` 모드 및 상용 승인 차단 개념만 새로 구현 |
| `shinkangteam/gbsales` (비공개) | `README.md`, `src/pages/MarketPage.tsx`, `src/pages/WalletPage.tsx` | 상품 가격 표시·거래 내역 UX | 원화 가격/잔액 분리 유지, 결제 코드는 미복사 |
| `shinkangteam/helloapp` (비공개) | `src/services/kakao.ts` | OAuth 동의 스코프·토큰 만료·발송 결과 기록 | 별도 카카오 승인 필요 사항을 대조, 실발송 미연결 |
| `shinkangteam/greenbean-ledger` (비공개) | `README.md` | DB/인증/거래원장 분리 | 감사용 조회·기존 원장 분리 유지, 회계 코드 미복사 |
| `shinkangteam/marketingsodong` (공개) | `README.md`, `src/App.tsx`, 페이지 구성 | 상점 등록·SNS 공유·에러 화면 | 쿠폰 홍보 문구 생성·복사 기능 새로 구현 |
| `shinkangteam/partnerssc`, `ma`, `linkervs` | README 및 디렉터리 | 마케팅/전문직/IDE 도구 | 직접 병합 불필요(도메인·런타임 상이) |

## 실제 추가 코드

- `bridge_v7.py`: 점포 쿠폰별 광고 문구·Google 길찾기 URL·공유 링크 생성, 상용화 준비도 점검 API
- `server.py`: `/api/v7/meta`, `/api/v7/share-kit`, `/api/v7/readiness` GET 등록
- `market/ui.js`, `market/theme.css`: 특가 카드의 **홍보 문구 복사** 버튼 및 반응 처리
- `market/core.py`: `GARAK_V7_MODE=review`에서 시연 점포 쿠폰을 고객 특가 조회에서 제외
- `tests/test_bridge_v7.py`: 최소 9개 추가 자동 테스트

## 병합하지 않은 코드와 이유

- 타 프로젝트 전체 React/Vite/NestJS 소스를 Python 표준 라이브러리 기반 가락랜드에 강제로 합치지 않음: 빌드 툴/인증/DB 스키마 충돌 방지.
- GreenBean 거래·충전 기능과 Kakao OAuth 발송 핸들러를 복사하지 않음: 서로 다른 서비스이고 유료 발행/전자금융·광고 발송 승인이 없음.
- 기존 GitHub 비공개 저장소를 수정하거나 공개 저장소로 푸시하지 않음. 소스 비교만 진행.
- README의 공용 소스와 개인 비공개 소스를 무단으로 외부 공개하지 않도록 실제 GitHub 원본 파일은 ZIP 안에 복사하지 않음.

## 한계

현재 확인 가능한 저장소 목록에서 **가락랜드 전용 이름의 리포지터리는 발견하지 못했습니다**. 이름이 다른 숨은 리포/다른 브랜치/별도 계정까지 확인한 것은 아닙니다. 따라서 이 ZIP은 *관련 기술 패턴을 대조하여 v6을 안전 확장한 v7*이며, 특정 가락랜드 GitHub 저장소의 전체 소스를 원본 그대로 병합했다고 주장하지 않습니다.
