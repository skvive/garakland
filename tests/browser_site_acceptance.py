"""Run real Chromium page/navigation/button smoke tests against an isolated local demo server.

No production domain, credentials, messages, orders, payment or financial APIs are used.
Usage: python tests/browser_site_acceptance.py
Requires: pip install playwright requests pg8000 ; python -m playwright install chromium
"""
from __future__ import annotations
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    "/index.html", "/home.html", "/market.html", "/map.html", "/ar-quest.html",
    "/stores.html", "/store.html?id=demo-sea", "/market-map.html", "/coupons.html",
    "/events.html", "/market-guide.html", "/merchant-center.html",
    "/hub.html", "/ops.html", "/documents.html", "/login.html",
    "/unsubscribe.html", "/design_gallery.html", "/design/design-system.html",
    "/design/home-templates.html", "/previews/index.html",
    "/brand_strategy_docs/index.html", "/brand_strategy_docs/business-plan.html",
    "/brand_strategy_docs/investment-proposal.html", "/brand_strategy_docs/brandbook.html",
    "/brand_strategy_docs/copyright-dossier.html",
]
INTERACT = {
    "/market.html": ["button[data-page='wallet']", "button[data-page='marketing']", "button[data-page='merchant']", "button[data-page='explore']"],
    "/ar-quest.html": ["button[data-page='directory']", "button[data-page='missions']", "button[data-page='coupons']", "button[data-page='guide']"],
    "/map.html": ["button[data-tab='stores']", "button[data-tab='guide']", "button[data-tab='explore']"],
    "/stores.html": ["button[data-category='수산']", "button[data-category='청과']", "button[data-category='전체']"],
    "/events.html": ["button[data-event-filter='수산']", "button[data-event-filter='전체']"],
    "/market-map.html": ["button[data-zone='수산']", "button[data-zone='청과']"],
    "/store.html": ["button[data-claim]"],
    "/coupons.html": ["button[data-claim]"],
    "/ops.html": ["button[data-view='dashboard']", "button[data-view='board']", "button[data-view='documents']", "button[data-view='products']", "button[data-view='settlement']", "button[data-view='checklist']"],
}


def reserve_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def main():
    failures = []
    count = 0
    port = reserve_port()
    base = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory() as scratch:
        env = dict(os.environ)
        env.update({
            "GARAK_DB_PATH": str(Path(scratch) / "qa.sqlite"),
            "GARAK_HOST": "127.0.0.1",
            "PORT": str(port),
            "GARAK_ADMIN_TOKEN": "QA-local-only-20261101-TEST-TOKEN",
            "GARAK_ENABLE_DEMO": "1",
            "GARAK_V5_LIVE_MARKETING": "0",
            "GARAK_V5_APPROVED_LIVE_SEND": "NO",
            "GARAK_V7_MODE": "demo",
            "DATABASE_URL": "",
            "POSTGRES_URL": "",
        })
        srv = subprocess.Popen([sys.executable, "server.py"], cwd=ROOT, env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        try:
            for _ in range(70):
                try:
                    if requests.get(base + "/api/health", timeout=1).status_code == 200:
                        break
                except requests.RequestException:
                    pass
                if srv.poll() is not None:
                    raise RuntimeError("Isolated QA server exited during startup")
                time.sleep(.2)
            else:
                raise RuntimeError("QA server did not start")

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                for label, width, height in [("desktop", 1440, 900), ("mobile", 390, 844)]:
                    context = browser.new_context(viewport={"width": width, "height": height},
                                                  reduced_motion="reduce", accept_downloads=False)
                    for route in PAGES:
                        page = context.new_page()
                        issues = []
                        page.on("pageerror", lambda e, issues=issues: issues.append("JS: " + str(e)[:180]))
                        page.on("response", lambda r, issues=issues: issues.append("HTTP404 " + r.url)
                                if r.status == 404 and r.url.startswith(base) and not urlparse(r.url).path.startswith("/api/")
                                else None)
                        url = base + route
                        try:
                            response = page.goto(url, wait_until="domcontentloaded", timeout=20000)
                            if not response or response.status != 200:
                                issues.append(f"Page HTTP {response.status if response else 'no-response'}")
                            page.wait_for_timeout(450)
                            if not page.locator("body").inner_text().strip():
                                issues.append("Blank body")
                            overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
                            if overflow > 3:
                                issues.append(f"Horizontal overflow {overflow}px")
                            pathname = urlparse(route).path
                            if pathname == "/ops.html":
                                if page.locator("#token").count():
                                    page.locator("#token").fill(env["GARAK_ADMIN_TOKEN"])
                                    page.locator("#connect").click()
                                    page.wait_for_timeout(450)
                            for selector in INTERACT.get(pathname, []):
                                locator = page.locator(selector).first
                                if locator.count() and locator.is_visible() and locator.is_enabled():
                                    locator.click(timeout=5000)
                                    page.wait_for_timeout(130)
                                    count += 1
                            # Validate clickable navigation, not just href strings.
                            candidates = page.locator("a[href]").evaluate_all(
                                """nodes => [...new Set(nodes.map(a=>a.getAttribute('href'))
                                .filter(h=>h && !h.startsWith('#') && !h.startsWith('http')
                                && !h.startsWith('mailto:') && !h.startsWith('tel:')
                                && /\.html(?:[?#]|$)/.test(h)))].slice(0,3)"""
                            )
                            for href in candidates:
                                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                                locator = page.locator("a[href]").filter(has=page.locator("NOT_A_SELECTOR")) if False else None
                                # Use element.click() on the matching anchor; JS can handle this navigation.
                                link = page.locator("a[href]").filter(visible=True) if False else page.locator("a[href]")
                                target = link.evaluate_all(
                                    "(nodes, href) => nodes.findIndex(a=>a.getAttribute('href')===href && a.getClientRects().length>0)",
                                    href,
                                )
                                if target < 0:
                                    continue
                                original = page.locator("a[href]").nth(target)
                                try:
                                    with page.expect_navigation(wait_until="domcontentloaded", timeout=6000):
                                        original.click(timeout=4000)
                                    if not page.url.startswith(base):
                                        issues.append("Unexpected outbound navigation")
                                    count += 1
                                except Exception as exc:
                                    issues.append(f"Navigation click {href}: {str(exc)[:110]}")
                            if issues:
                                failures.append(f"{label} {route}: " + "; ".join(issues[:5]))
                        except Exception as exc:
                            failures.append(f"{label} {route}: {str(exc)[:200]}")
                        finally:
                            page.close()
                    context.close()
                browser.close()
        finally:
            srv.terminate()
            try:
                srv.wait(timeout=6)
            except subprocess.TimeoutExpired:
                srv.kill()
    print(f"BROWSER ACCEPTANCE: {len(PAGES)} routes x 2 viewports, {count} safe clicks, {len(failures)} failures")
    for problem in failures:
        print("FAIL:", problem)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
