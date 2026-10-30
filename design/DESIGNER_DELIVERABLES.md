# 디자이너 산출물 패키지 v1.0

[v1.0 · 2026-10-30 · Phase 0~2 반영]

## 1. 산출물 목록 (정본 경로)

| # | 산출물 | 경로 | 용도 |
|---|--------|------|------|
| 1 | **Design Tokens** | `design/tokens.css` | 색·폰트·radius·모듈 alias |
| 2 | **Components** | `design/components.css` | Header · Mobile 5-tab · Disclaimer |
| 3 | **Site Chrome** | `design/site-chrome.mjs` | 모바일 내비 주입·active 상태 |
| 4 | **Style Guide (HTML)** | `design/design-system.html` | 디자이너·개발 공통 레퍼런스 |
| 5 | **통합 기획** | `docs/DESIGN_SYSTEM_INTEGRATION_PLAN.md` | IA·로드맵 |
| 6 | **시안 5종 가이드** | `docs/design-concepts/` · `TEMPLATE_CATALOG.md` | 컨셉 ↔ 구현 · `/design/home-templates.html` |
| 7 | **검수 캡처** | `design_gallery.html` + `design/qa.css` + `v4_*` `v5_*` PNG (ZIP) | 회귀·라이브 링크 |
| 8 | **Asset map** | `design/assets.json` | 카테고리 webp 매핑 |

## 2. CTA 규칙 (디자이너 승인본)

| 클래스 | 색 | 사용 |
|--------|-----|------|
| `.gl-cta-explore` | lime `#d6ef72` | AR·탐험·지도 진입 |
| `.gl-cta-deal` | gold `#e8c547` | 특가·쿠폰·구매 |

## 3. 글로벌 내비

**데스크톱:** `gl-site-header` — 홈 · AR · **특가(Primary)** · 지도 · ERP · 로그인  
**모바일 5탭:** 홈 · 탐험 · 특가 · 지도 · 지갑 (`site-chrome.mjs`)

**예외:** `index.html` — 앱 내 7→6탭 유지 + 홈/특가/지도 링크 (`data-gl-mobile-nav="off"`)  
**예외:** `ops.html` — ERP 전용 (`data-gl-mobile-nav="off"`)

## 4. body 데이터 속성

```html
<body data-gl-active="home|explore|market|map" data-gl-mobile-nav="off">
```

## 5. 페이지별 CSS 로드 순서

```html
<link rel="stylesheet" href="/design/tokens.css">
<link rel="stylesheet" href="/design/components.css">
<!-- 모듈 CSS: studio / theme / ops / styles -->
```

## 6. 이미지 역할 (변경 금지)

- `assets/editorial/` — 스토리·AR  
- `assets/v5/` — 특가 썸네일  
- `assets/v6/market-hero.webp` — 히어로 BG only  

## 7. Figma 대체 워크플로

1. `design/design-system.html` 브라우저로 열기  
2. 토큰 변경 → `design/tokens.css`만 수정  
3. 컴포넌트 변경 → `design/components.css`  
4. `design_gallery.html` + Playwright로 스크린 diff  

## 8. 체크리스트 (납품 전)

- [x] lime / gold CTA 역할 분리 (`components.css`)  
- [x] 모든 고객 페이지 `tokens.css` 로드  
- [x] ERP·login 홈 링크 `/`  
- [x] AI 시연 disclaimer 노출 (홈·market footer 등)  
- [x] 모바일 5탭 active (`data-gl-active` + `site-chrome.mjs`)  

---

Phase 3~5 반영: `market/theme.css` token bridge · `platform.css` 삭제 · 갤러리 v5/v6·라이브 섹션 · `tests/test_design_tokens.py`. Playwright PNG 재촬영은 CI/릴리스 시 선택 실행.
