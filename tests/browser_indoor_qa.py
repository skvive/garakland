"""Browser acceptance for independent Garak Mall indoor map beta.

Runs against a local static server only. Does not read production DB, GPS,
camera, checkout or private credentials. Screenshots are deterministic.
"""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "qa-artifacts" / "indoor"
OUT.mkdir(parents=True, exist_ok=True)


def port_available():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def run():
    port = port_available()
    base = "http://127.0.0.1:" + str(port)
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
    )
    checks = 0
    errors = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            for label, width, height in [
                ("desktop", 1440, 900), ("mobile", 390, 844),
                ("compact", 360, 740)
            ]:
                context = browser.new_context(
                    viewport={"width": width, "height": height},
                    reduced_motion="reduce"
                )
                page = context.new_page()
                page.on("pageerror", lambda e, errors=errors: errors.append(str(e)[:300]))
                response = page.goto(base + "/indoor-map.html", wait_until="networkidle", timeout=30000)
                assert response and response.status == 200
                assert "가락몰 실내" in page.title()
                page.get_by_role("button", name="5관", exact=True).click()
                page.get_by_role("button", name="3F", exact=True).click()
                page.wait_for_timeout(130)
                assert page.locator(".store-item").count() == 4, (label, "5관 3F", page.locator(".store-item").count())
                checks += 1
                # Preserve 5관 signage view; use the all-hall overview for the six floor snapshots.
                if label != "compact":
                    page.screenshot(path=str(OUT / (label + "_hall5_3F.png")), full_page=True)
                page.get_by_role("button", name="전체", exact=True).click()
                for floor in ["B3", "B2", "B1", "1F", "2F", "3F"]:
                    page.get_by_role("button", name=floor, exact=True).click()
                    assert floor in page.locator("#mapHeading").inner_text()
                    assert page.locator("#floorSvg .zone").count() > 0
                    assert "개략" in page.locator(".verification-banner").inner_text()
                    if label != "compact":
                        page.screenshot(path=str(OUT / (label + "_" + floor + ".png")), full_page=True)
                    checks += 1
                page.get_by_role("button", name="전체", exact=True).click()
                page.locator("#searchInput").fill("이디야")
                assert page.locator(".store-item").count() == 1
                page.locator(".store-item").first.click()
                assert "3관" in page.locator("#routeSteps").inner_text()
                assert "이디야" in page.locator("#routeSteps").inner_text()
                assert page.locator("#mapHeading").inner_text().startswith("3F")
                checks += 1
                page.locator("#originFloor").select_option("B1")
                assert "층 이동" in page.locator("#routeSteps").inner_text()
                checks += 1
                page.get_by_role("button", name="1F", exact=True).click()
                page.locator("#zoneQuickList button").first.click()
                assert page.locator("#routeSteps").get_by_text("구역", exact=False).count() > 0
                checks += 1
                page.locator("#zoomIn").click()
                assert "140%" in page.locator("#zoomValue").inner_text()
                page.locator("#zoomReset").click()
                assert "100%" in page.locator("#zoomValue").inner_text()
                checks += 1
                # Document-width overflow is a bug; the map viewport itself may scroll horizontally.
                document_overflow = page.evaluate(
                    "document.documentElement.scrollWidth - document.documentElement.clientWidth"
                )
                assert document_overflow <= 4, (label, "document overflow", document_overflow)
                checks += 1
                # Legacy outdoor map link remains available.
                assert page.locator('a[href="/map.html"]').count() >= 1
                checks += 1
                context.close()
            browser.close()
        assert not errors, errors
        print(f"PASS indoor beta Chromium: {checks} assertions, 3 viewports, 14 floor/hall screenshots, {len(errors)} JS exceptions")
    finally:
        server.terminate()
        try:
            server.wait(timeout=6)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    run()
