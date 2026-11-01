"""Non-mutating external smoke probe for public GARAKLAND API endpoints.

Only GET requests with no cookies, auth tokens, payment calls, or customer records.
Never print JSON bodies, session IDs, secrets, or public API key values.
Run from CI with a reachable HTTPS endpoint:
    GARAK_READONLY_BASE=https://garakland.lexid.site python tests/live_readonly_smoke.py
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from urllib.parse import urlparse

BASE = os.environ.get("GARAK_READONLY_BASE", "https://garakland.lexid.site").rstrip("/")
ALLOWED = {
    "/api/health": (200,),
    "/api/v5/public": (200,),
    "/api/stores?limit=2": (200,),
    "/api/public/config": (200,),
    "/auth/config.public.json": (200,),
    "/api/v8/dashboard": (403,),
    "/api/merchant/qr?shopId=demo-sea": (403,),
}


def main() -> None:
    parsed = urlparse(BASE)
    if parsed.scheme != "https" or parsed.username or parsed.password or not parsed.hostname:
        raise SystemExit("An HTTPS base URL without credentials is required.")
    failures = []
    for path, expected in ALLOWED.items():
        req = urllib.request.Request(
            BASE + path,
            method="GET",
            headers={"User-Agent": "Garakland-QA-ReadOnly/1.0", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=22) as response:
                code = response.status
                content_type = response.headers.get("Content-Type", "")
                body = response.read(128_000)
        except urllib.error.HTTPError as exc:
            code = exc.code
            content_type = exc.headers.get("Content-Type", "")
            body = exc.read(128_000)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            failures.append(f"{path}: transport error ({type(exc).__name__})")
            continue

        print(f"{path}: HTTP {code}")
        if code not in expected:
            failures.append(f"{path}: expected {expected}, received {code}")
        if "application/json" not in content_type:
            failures.append(f"{path}: expected JSON, got {content_type.split(';')[0]}")
            continue
        try:
            payload = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            failures.append(f"{path}: malformed JSON")
            continue
        if path == "/api/health" and code == 200 and payload.get("ok") is not True:
            failures.append(f"{path}: health ok flag missing")
        if path == "/auth/config.public.json" and code == 200:
            url = payload.get("authUrl", "")
            if not isinstance(url, str) or not url.startswith("https://"):
                failures.append(f"{path}: invalid public auth URL")

    print(f"Read-only live smoke: {len(ALLOWED)} endpoints, {len(failures)} failures")
    for failure in failures:
        print("FAIL:", failure)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
