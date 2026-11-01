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
                assert page.locator('a[href="/indoor-layout-lab.html"]').count() >= 1
                checks += 1
                # Floor-plan workbench must run locally and never auto-publish imported data.
                response = page.goto(base + "/indoor-layout-lab.html", wait_until="networkidle")
                assert response and response.status == 200
                assert "검수" in page.title()
                assert "미게시" in page.locator("#status").inner_text()
                page.locator("#shopName").fill("QA 임시상점")
                page.locator("#shopCategory").fill("식당")
                page.locator("#startPin").click()
                page.locator("#preview").click(position={"x": 280, "y": 230})
                assert page.locator("#shopRows .shop-record").count() == 1
                assert "미게시" in page.locator("#status").inner_text()
                checks += 1
                page.locator("#hall").select_option("3")
                assert page.locator("#shopRows .shop-record").count() == 0, "floor change must clear stale geometry"
                checks += 1
                import json
                draft = {
                  "schemaVersion":1,"hall":"5","floor":"1F",
                  "source":{"id":"qa-floor","title":"QA 임시 도면","kind":"illustrative",
                            "status":"draft","permissionRef":"","reviewer":"","reviewDate":""},
                  "outline":[[8,20],[72,18],[90,45],[78,70],[10,72]],
                  "entrances":[],"shops":[],"nodes":[],"edges":[]
                }
                page.locator("#inputFile").set_input_files({
                    "name":"qa-floor.json","mimeType":"application/json",
                    "buffer":json.dumps(draft,ensure_ascii=False).encode("utf-8")
                })
                page.wait_for_function("document.querySelector('#sourceTitle')?.value === 'QA 임시 도면'", timeout=8000)
                assert page.locator("#hall").input_value() == "5"
                assert page.locator("#floor").input_value() == "1F"
                assert "미게시" in page.locator("#status").inner_text()
                page.locator("#calculateRoute").click()
                assert "실측" in page.locator("#routeResult").inner_text()
                checks += 1
                if label != "compact":
                    page.screenshot(path=str(OUT / (label + "_layout_workbench.png")),full_page=True)
                # Entirely synthetic approval fixture: verifies route-graph gate,
                # not that any real Garak Mall path has been surveyed.
                approved = dict(draft)
                approved["source"] = {
                    "id":"test-approved","title":"QA TEST-ONLY","kind":"owner-authorized-drawing",
                    "status":"approved","permissionRef":"TEST-NOT-REAL",
                    "reviewer":"QA TEST","reviewDate":"2026-11-02"
                }
                approved["shops"] = [{
                    "id":"test-shop","name":"TEST SHOP","category":"food",
                    "polygon":[[40,20],[50,20],[50,30],[40,30]],"verified":True
                }]
                approved["nodes"] = [
                    {"id":"start","xy":[10,20],"type":"entry","verified":True},
                    {"id":"finish","xy":[70,20],"type":"passage","verified":True}
                ]
                approved["edges"] = [{
                    "id":"short-stairs","from":"start","to":"finish",
                    "mode":"stairs","lengthMeters":7,"verified":True
                }]
                page.locator("#inputFile").set_input_files({
                    "name":"test-approved.json","mimeType":"application/json",
                    "buffer":json.dumps(approved,ensure_ascii=False).encode("utf-8")
                })
                page.locator("#calculateRoute").click()
                assert "7m" in page.locator("#routeResult").inner_text()
                page.locator("#wheelchairMode").check()
                page.locator("#calculateRoute").click()
                assert "검증된 연결 동선" in page.locator("#routeResult").inner_text()
                checks += 1
                # Multi-floor graph is a separate offline planning lab.
                response = page.goto(base + "/indoor-campus-lab.html", wait_until="networkidle")
                assert response and response.status == 200
                assert "실제 길안내 아님" in page.locator(".warning").inner_text()
                page.locator("#testExample").click()
                assert "테스트 예제" in page.locator("#graphStatus").inner_text()
                assert page.locator("#transferRows .shop-record").count() == 3
                page.locator("#routeButton").click()
                assert "49m" in page.locator("#routeResult").inner_text()
                assert "TEST ONLY" in page.locator("#routeResult").inner_text()
                checks += 1
                page.locator("#wheelchairMode").check()
                page.locator("#routeButton").click()
                assert "67m" in page.locator("#routeResult").inner_text()
                assert "TEST ONLY" in page.locator("#routeResult").inner_text()
                checks += 1
                if label != "compact":
                    page.screenshot(path=str(OUT / (label + "_campus_graph.png")),full_page=True)
                # Phase 4: signboard roster, CSV conflicts and staged shop polygons.
                response = page.goto(base + "/indoor-tenant-lab.html", wait_until="networkidle")
                assert response and response.status == 200
                assert page.locator("#tenantRows tr").count() == 14
                assert "14개" in page.locator("#summary").inner_text()
                checks += 1
                page.locator("#tenantRows button[data-id='h5-dolgorae']").click()
                assert page.locator("#editHall").input_value() == "5"
                assert page.locator("#editFloor").input_value() == "3F"
                page.locator("#stageMap").click(position={"x": 210, "y": 195})
                assert page.locator("#stageMap polygon").count() == 2
                assert page.locator("#tenantRows tr.selected .unverified").inner_text() == "초안 위치 지정"
                assert "미반영" in page.locator("#stageStatus").inner_text()
                checks += 1
                if label != "compact":
                    page.screenshot(path=str(OUT / (label + "_tenant_registry.png")), full_page=True)
                page.locator("#csvPaste").fill("\n".join([
                    "shop_id,name,hall,floor,room,category,source_ref",
                    "t1,Test Shop,5,3F,A1,food,test-sign",
                    "t2,Test Shop,5,3F,A1,food,test-sign",
                ]))
                page.locator("#loadPaste").click()
                assert "오류 또는 중복" in page.locator("#warning").inner_text()
                assert page.locator("#errorList li").count() >= 1
                page.locator("#seedButton").click()
                assert page.locator("#tenantRows tr").count() == 14
                checks += 1
                context.close()
            browser.close()
        assert not errors, errors
        print(f"PASS indoor beta Chromium: {checks} assertions, 3 viewports, 20 screenshots (floors, workbench, campus and tenant review), {len(errors)} JS exceptions")
    finally:
        server.terminate()
        try:
            server.wait(timeout=6)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    run()
