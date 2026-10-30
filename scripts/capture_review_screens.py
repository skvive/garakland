"""Capture UI review PNGs for design_gallery.html (production or local BASE_URL)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get("GARAK_CAPTURE_BASE", "https://garakland.lexid.site").rstrip("/")

SHOTS: list[tuple[str, str, int, int]] = [
    ("preview_home_desktop.png", "/", 1440, 900),
    ("preview_home_mobile.png", "/", 390, 844),
    ("v5_desktop_home.png", "/market.html", 1440, 900),
    ("v5_mobile_home.png", "/market.html", 390, 844),
    ("preview_ops_desktop.png", "/ops.html", 1440, 900),
]


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Install: pip install playwright && playwright install chromium", file=sys.stderr)
        return 1

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name, path, w, h in SHOTS:
            ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=1)
            page = ctx.new_page()
            url = BASE + path
            page.goto(url, wait_until="networkidle", timeout=120_000)
            page.wait_for_timeout(800)
            out = ROOT / name
            page.screenshot(path=str(out), full_page=True)
            print("wrote", out.name, w, "x", h)
            ctx.close()
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
