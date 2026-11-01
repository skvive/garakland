"""Production GET-only verification of Garakland's deployed design release.
No cookies, user data writes, administrative calls, or credentials."""
from __future__ import annotations
import json
import urllib.error
import urllib.request

BASE = "https://garakland.lexid.site"
PAGES = {
    "/": ("text/html", "/design/tokens.css"),
    "/design_gallery.html": ("text/html", "실사용 동선 바로가기"),
    "/design/home-templates.html": ("text/html", "/ar-quest.html#page-guide"),
    "/brand_strategy_docs/brandbook.html": ("text/html", "css/site.css"),
    "/ar-quest.html": ("text/html", "/assets/editorial/market.webp"),
    "/design/garakland-themepark.css": ("text/css", "gl-theme"),
    "/brand_strategy_docs/css/site.css": ("text/css", ".hero"),
    "/assets/editorial/market.webp": ("image/webp", None),
    "/api/health": ("application/json", '"ok": true'),
}
errors = []
for path, (mime, marker) in PAGES.items():
    req = urllib.request.Request(
        BASE + path,
        headers={"User-Agent": "Garakland-design-release-verification/1.0", "Cache-Control": "no-cache"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            status = r.status
            content_type = r.headers.get("Content-Type", "")
            body = r.read(512_000)
    except urllib.error.HTTPError as exc:
        errors.append(f"{path}: HTTP {exc.code}")
        continue
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        errors.append(f"{path}: transport failure ({type(exc).__name__})")
        continue
    if status != 200 or mime not in content_type:
        errors.append(f"{path}: HTTP {status}, MIME {content_type.split(';')[0]}")
        continue
    if marker:
        text = body.decode("utf-8", "replace")
        if path == "/api/health":
            try:
                if json.loads(text).get("ok") is not True:
                    errors.append(f"{path}: unhealthy response")
            except json.JSONDecodeError:
                errors.append(f"{path}: malformed JSON")
        elif marker not in text:
            errors.append(f"{path}: expected release marker missing")
    print(f"GET {path}: 200, {mime}")
print(f"PRODUCTION DESIGN QA: {len(PAGES)} endpoints, {len(errors)} failures")
for err in errors:
    print("FAIL:", err)
if errors:
    raise SystemExit(1)
