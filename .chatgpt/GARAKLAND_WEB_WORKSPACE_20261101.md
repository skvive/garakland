# GARAKLAND — ChatGPT Web Workspace (2026-11-01)

## Scope and source of truth
- GitHub repo: `skvive/garakland`
- Production/base branch: `master`
- Base commit: `1724924ee29c2695d69da55a7b757804ebc6116b`
- Isolated working branch: `chatgpt/garakland-web-workspace-20261101`
- Existing Android work branch (do not overwrite): `chatgpt/garakland-android-workspace-20261101`
- PR #1, responsive/UI mascot cleanup, was merged to `master` on 2026-11-01.

This branch is for the ChatGPT conversation dedicated to editing Garakland. Preserve the existing production website, database, authentication, maps, coupons, merchant center, games/AR, and Android project while refining pages.

## Main page entry points
- `index.html`: AR/game landing
- `market.html`: market/growth/offer landing; `market/theme.css`, `market/ui.js`
- `home.html`: platform home, `platform-home.css`, `platform-home.js`
- `hub.html`: administrator hub; `hub/`
- `ops.html`: operations/ERP; `ops/`
- `stores.html`, `store.html`, `market-map.html`, `coupons.html`, `events.html`, `merchant-center.html`: brand-site routes backed by `brand/`
- `map.html`, `game/`: navigation and AR
- `design/`, `assets/`: brand design system and imagery
- `server.py`, `api/index.py`, `auth/`, `data/`: backend/auth/data
- `tests/`, `scripts/`: quality checks

## Local development
```bash
git clone https://github.com/skvive/garakland.git
cd garakland
git fetch origin
git switch --track origin/chatgpt/garakland-web-workspace-20261101
python -m unittest discover -s tests -p "test_*.py" -v
python server.py
# Open http://127.0.0.1:8769/market.html
```
Require Python 3.10+; some browser/node and Android tests need additional dependencies. The GitHub repo is the canonical source, not the text in this document.

## Modification rules
1. Commit all user-requested website/design fixes to this branch first. Do not push directly to `master`, force-push, or merge without review.
2. Edit and inspect affected pages at 390px/768px/1440px, test links and CTAs, ensure text contrast, no overflow and correct image cropping.
3. Preserve logo/brand identity and avoid floating decorative mascot overlays removed by PR #1.
4. Keep sample store/pricing data and simulated coupon/gift card functionality explicitly marked DEMO. Do not represent unverified store details, payment, live marketing, GPS, or AR features as production-ready.
5. Never commit API secrets, .env, personal contact data, or production DB exports.
6. Run Python regression checks and relevant JS/HTML/browser tests; record failed/skipped/untested checks explicitly.
7. Verify Vercel preview and domain behavior before a future production deployment; do not change the production domain or deploy to production implicitly.
8. Keep the Android branch independent; reconcile both branches deliberately if modifying shared web resources that the app loads.

## Change log
- 2026-11-01: Workspace established from the merged production baseline. No website content or functionality changed yet. Local full git clone and live browser execution not yet verified in the ChatGPT sandbox.
