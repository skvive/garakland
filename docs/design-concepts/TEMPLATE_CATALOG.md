# 메인(/) 디자인 템플릿 카탈로그 · 검수·선택

[v1.0 · 2026-10-30 · garakland.lexid.site 통합 홈]

외부 AI PNG(`01_테마파크` … `05_마켓가이드`)는 git 미포함. **구현 템플릿 = 아래 라이브 URL + 검수 PNG + HTML 정본**으로 대체합니다.

---

## 템플릿 ① 테마파크 3D · STUDIO

| 항목 | 내용 |
|------|------|
| 키워드 | 탐험, AR, XP, 지도, 에디토리얼 |
| **정본 HTML** | `index.html` `#page-explore` · `game/studio.css` |
| **라이브** | [AR 탐험](https://garakland.lexid.site/index.html) |
| **검수 캡처** | `v4_desktop_home.png` (갤러리/ZIP) · Playwright `test_studio_browser.py` |
| **히어로 패턴** | split card · deep green · lime CTA · `assets/editorial/market.webp` · orb/XP 장식 |
| **강점** | 브랜드(가락랜드 STUDIO) 명확, 4-rail·district 카드와 IA 일치 |
| **약점** | 특가·쿠폰 전환 약함, 이모지·게임 UI 비중 큼 |

---

## 템플릿 ② 프리미엄 마켓 · EDITORIAL

| 항목 | 내용 |
|------|------|
| 키워드 | 매거진, 가이드북, 디렉터리 |
| **정본 HTML** | `index.html` `#page-guide` · `#page-directory` |
| **라이브** | [가이드북 탭](https://garakland.lexid.site/index.html#page-guide) |
| **검수 캡처** | `v4_desktop_guide.png` · `v4_desktop_directory.png` |
| **히어로 패턴** | 챕터형 카드 · 필터·검색 중심 |
| **강점** | 콘텐츠 깊이, 신뢰 톤 |
| **약점** | 랜딩 1화면 CTA 밀도 낮음 — **홈 단독 템플릿으로는 비추**

---

## 템플릿 ③ 특가 커머스 · MARKET v5

| 항목 | 내용 |
|------|------|
| 키워드 | 할인, 쿠폰, 필터, 상인 |
| **정본 HTML** | `market.html` `#explore` · `market/theme.css` |
| **라이브** | [오늘의 특가](https://garakland.lexid.site/market.html) |
| **검수 캡처** | `v5_desktop_home.png` · `v5_mobile_home.png` |
| **히어로 패턴** | full-bleed photo (`v6/market-hero.webp`) · gold em · 4칸 action-row · TODAY'S PICK |
| **강점** | 전환(특가·지갑) 최적, AI 라벨·disclaimer 위치 명확 |
| **약점** | AR·탐험 내러티브 약함, 헤더가 `gl-site-header`와 상이 |

---

## 템플릿 ④ 몰입 탐험 · MISSIONS

| 항목 | 내용 |
|------|------|
| 키워드 | 미션, XP, 배지, 카메라 |
| **정본 HTML** | `index.html` missions 페이지 |
| **라이브** | [미션](https://garakland.lexid.site/index.html#page-missions) |
| **검수 캡처** | `v4_desktop_missions.png` |
| **강점** | 리텐션·게임 루프 |
| **약점** | 신규 방문자 랜딩으로는 진입 장벽 — **홈 보조 섹션만 권장**

---

## 템플릿 ⑤ 마켓 가이드 · LEAFLET

| 항목 | 내용 |
|------|------|
| 키워드 | 전단, 필터, share-kit, 마케팅 동의 |
| **정본 HTML** | `market.html` `#marketing` · v7 share |
| **라이브** | [소식 받기](https://garakland.lexid.site/market.html#marketing) |
| **검수 캡처** | `v5_mobile_marketing.png` |
| **강점** | 수신동의·캠페인 UX |
| **약점** | 홈 첫 화면용 아님 — **푸터·2depth 링크**

---

## 비교·선택 매트릭스

| 후보 | 탐험 | 특가 전환 | 모바일 CTA | 디자인 패키지 정합 | **홈(/) 적합** |
|------|:---:|:---:|:---:|:---:|:---:|
| ① STUDIO | ★★★ | ★★ | ★★★ | tokens lime | **필수** |
| ② Editorial | ★★ | ★ | ★★ | editorial webp | 보조 |
| ③ MARKET | ★ | ★★★ | ★★★ | gold + v6 hero | **필수** |
| ④ Missions | ★★★ | ★ | ★★ | studio | 보조 |
| ⑤ Leaflet | ★ | ★★ | ★★ | market form | 2depth |

### ✅ 채택안 (디자이너·기획 정본)

**통합 홈 `/` = ① STUDIO 히어로·구역·4-rail + ③ MARKET 풀블리드 특가 히어로·action-row·TODAY'S PICK**

- 근거: `docs/DESIGN_SYSTEM_INTEGRATION_PLAN.md` · `docs/PLATFORM_V1_INTEGRATION.md` · `design/DESIGNER_DELIVERABLES.md`
- 시각 비교 페이지: [/design/home-templates.html](https://garakland.lexid.site/design/home-templates.html)

### 반영 체크 (패키지)

- [x] `design/tokens.css` + `design/components.css` on `/`
- [x] `gl-cta-explore` / `gl-cta-deal` 역할 분리
- [x] `gl-disclaimer` 푸터
- [x] ③ 히어로를 `design/home-deal-hero.css` + `home.html` (market.html과 동일 패턴)
- [ ] 외부 `01~05` PNG import → `docs/design-concepts/` (수령 시)

---

## 다음 검수

1. `/design/home-templates.html` 에서 ① vs ③ 스크롤 비교  
2. `/design_gallery.html` LIVE vs PNG diff  
3. `python scripts/capture_review_screens.py` 재촬영 (선택)
