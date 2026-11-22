#!/usr/bin/env python3
"""Browse responsive GARAKLAND pages in the GitHub runner; no live claims."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
from functools import partial
from playwright.sync_api import sync_playwright
import json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"qa-artifacts"/"brand-refresh";OUT.mkdir(parents=True,exist_ok=True)
http=ThreadingHTTPServer(("127.0.0.1",0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
Thread(target=http.serve_forever,daemon=True).start()
origin=f"http://127.0.0.1:{http.server_port}"
routes=["/","/home.html","/project.html","/culture.html","/commerce.html","/stores.html","/events.html","/market-guide.html","/lotteworld-next.html"]
widths=[320,360,390,430,768,1024,1440]
issues=[];samples=[]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
 try:
  for route in routes:
   for width in widths:
    page=browser.new_page(viewport={"width":width,"height":900},device_scale_factor=1)
    try:
     response=page.goto(origin+route,wait_until="domcontentloaded",timeout=30000)
     page.wait_for_timeout(200)
     if not response or response.status>=400:issues.append(f"{route}@{width}:HTTP")
     d=page.evaluate("""() => ({ doc:document.documentElement.scrollWidth, vw:document.documentElement.clientWidth, imgs:[...document.images].filter(x=>x.complete&&x.naturalWidth===0).map(x=>x.src), title:document.title })""")
     if d["doc"]>d["vw"]+2:issues.append(f"{route}@{width}:overflow {d['doc']}/{d['vw']}")
     for broken in d["imgs"]:issues.append(f"{route}@{width}:image "+broken)
     if route in ["/","/project.html","/culture.html","/commerce.html"] and width in [390,1440]:
      fn=f"{route.strip('/').replace('.html','') or 'index'}-{width}.png"
      page.screenshot(path=str(OUT/fn),full_page=True)
      samples.append(fn)
    except Exception as exc:issues.append(f"{route}@{width}:{type(exc).__name__}:{exc}")
    finally:page.close()
 finally:browser.close();http.shutdown()
(OUT/"qa-results.json").write_text(json.dumps({"routes":routes,"widths":widths,"issues":issues,"screenshots":samples},ensure_ascii=False,indent=2),encoding="utf-8")
print("responsive-qa",len(routes),"routes",len(widths),"widths",len(issues),"issues",issues[:25])
if issues:raise SystemExit(1)
