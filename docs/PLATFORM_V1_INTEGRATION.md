# 가락랜드 플랫폼 v1 통합 기획 (기획서 + v7 코드)

## 입력 자료

| 출처 | 상태 |
|------|------|
| `가락랜드플랫폼v1.zip` | 지정 경로 미발견 → **v7 핸드오프 + 기존 garakland 리포** 기준 통합 |
| v5/v6/v7 기획 본문 | 본 문서·`home.html` 반영 |
| GitHub `skvive/garakland` | 배포 정본 |
| Neon + Vercel | `garakland.lexid.site` |

## 플랫폼 모듈 맵

| 모듈 | URL | 버전 |
|------|-----|------|
| 플랫폼 홈 | `/home.html`, `/` | v1 랜딩 |
| AR 탐험 | `/index.html` | v4+ |
| 특가·쿠폰·상품권·마케팅 | `/market.html` | v5 |
| Google 지도 | `/map.html` | v4+ |
| ERP 운영 | `/ops.html` | v6 |
| 서류 | `/documents.html` | v6 |
| UI 검수 | `/design_gallery.html` | v4 |
| 로그인 | `/login.html` | Neon Auth |
| API | `/api/*` | v5–v7 |

## 마케팅·쿠폰·상품권 (구현됨)

- 특가 발행·일정·중단, 1인 1회 쿠폰, Google 길찾기 URL
- 이메일·SMS·카카오 **채널별 동의**, 캠페인 예약, **모의 발송** (`GARAK_V5_LIVE_MARKETING=0`)
- 연합 **시연권** 잔액·PIN·가맹·장부 (실결제 없음)
- v7 **share-kit** 광고 문구 복사

## ERP (구현됨)

- 6화면 대시보드, **드래그앤드롭** 업무 보드, CSV 상품 검증·등록
- 계약 증빙 그리드, 모의 정산 내보내기
- Word 서류 5종 (`documents/templates/`)

## 의료·건강 API (범위 외)

기획 본문 일부에 병원 쿠폰·출석·공공 의료 API가 포함되어 있으나, **전자금융·의료정보·공공 API 연동**은 별도 인허가·계약이 필요합니다.  
가락시장 상용 베타(v5–v7)와 분리하여 **본 배포에 미포함**합니다.

## 디자인 시안 5종

1. 테마파크 3D → `index.html`  
2. 프리미엄 마켓 → 에디토리얼·가이드  
3. 특가 커머스 → `market.html`  
4. 몰입 탐험 → 미션·AR  
5. 마켓 가이드 → 특가+전단형 CTA  

**랜딩 `home.html` = ①+③ 결합**

## 납품 ZIP

```powershell
cd E:\currsor_C\blog\garakland
powershell -File scripts\build-platform-zip.ps1
```

출력: `release/GARAKLAND_PLATFORM_v1.zip`

## 검증

```powershell
$env:PYTHONPATH='.'
python -m unittest discover -s tests -p "test_*.py" -v
```

브라우저: `/`, `/market.html`, `/ops.html`, `/login.html`, `/api/health`
