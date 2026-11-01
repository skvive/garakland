#!/usr/bin/env python3
"""Evidence-oriented Garakland page-by-page responsive design audit.

Launches the actual Python demo server with an isolated SQLite database.
Does NOT authenticate admin, exercise live payment, or claim external map validation.
Outputs JSON and real Chromium screenshots.
"""
import json, os, pathlib, subprocess, sys, tempfile, time, urllib.request
from playwright.sync_api import sync_playwright

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"qa-artifacts"/"design-delivery"
OUT.mkdir(parents=True,exist_ok=True)
PAGES=[
 "index.html","home.html","stores.html","store.html","coupons.html",
 "events.html","market-map.html","market-guide.html","merchant-center.html",
 "market.html","ar-quest.html","map.html","ops.html","hub.html",
 "login.html","documents.html","unsubscribe.html","design_gallery.html",
 "brand_strategy_docs/index.html","brand_strategy_docs/brandbook.html",
 "brand_strategy_docs/business-plan.html","brand_strategy_docs/copyright-dossier.html",
 "brand_strategy_docs/investment-proposal.html","design/design-system.html",
 "design/home-templates.html","previews/index.html"
]
SIZES=[("desktop",1440,900),("mobile",390,844),("compact",360,780)]
AUDIT_JS="""() => {
 const d=document.documentElement;
 const overflow=Math.max(0,d.scrollWidth-window.innerWidth);
 const images=Array.from(document.querySelectorAll('img')).map(x=>{
   const r=x.getBoundingClientRect();
   return {src:(x.getAttribute('src')||'').slice(0,120),broken:x.complete&&x.naturalWidth===0,
     alt:!!(x.getAttribute('alt')||'').trim(),w:Math.round(r.width),h:Math.round(r.height),
     naturalW:x.naturalWidth,naturalH:x.naturalHeight,fit:getComputedStyle(x).objectFit};
 }).filter(x=>x.w>0);
 const tooSmall=Array.from(document.querySelectorAll('button,a,input,select,textarea'))
   .filter(x=>{const s=getComputedStyle(x),r=x.getBoundingClientRect();
     return s.visibility!=='hidden'&&s.display!=='none'&&r.width>0&&r.height>0&&
       r.top<window.innerHeight&&r.bottom>0&&r.width>=12&&r.height<38})
   .slice(0,20).map(x=>({tag:x.tagName,label:(x.innerText||x.getAttribute('aria-label')||'').trim().slice(0,45),
    height:Math.round(x.getBoundingClientRect().height)}));
 const wide=Array.from(document.querySelectorAll('body *'))
   .filter(x=>{const s=getComputedStyle(x),r=x.getBoundingClientRect();
     return s.display!=='none'&&s.position!=='fixed'&&r.width>0&&r.right>window.innerWidth+3 &&
       r.left<window.innerWidth && r.right>0})
   .slice(0,15).map(x=>({tag:x.tagName,cls:(x.className||'').toString().slice(0,70),right:Math.round(x.getBoundingClientRect().right)}));
 return {title:document.title,heading:document.querySelector('h1')?.innerText?.slice(0,100)||'',
   overflow,brokenImages:images.filter(x=>x.broken),imagesCount:images.length,
   smallControls:tooSmall,wideElements:wide,bodyHeight:document.body.scrollHeight};
}"""

def verify_controls(page, page_path, viewport):
    """Exercise representative real click handlers, not visual-only screenshots."""
    if viewport != "compact":
        return []
    notes=[]
    def check(ok, title):
        if not ok: raise AssertionError(title)
        notes.append(title)
    if page_path in ("index.html","stores.html","store.html","coupons.html","events.html","market-guide.html","merchant-center.html"):
        toggle=page.locator("#menu-toggle")
        toggle.click(timeout=3000)
        check(page.locator("#primary-nav").evaluate("(e)=>e.classList.contains('open')"),"brand mobile menu opens")
        toggle.click(timeout=3000)
        check(not page.locator("#primary-nav").evaluate("(e)=>e.classList.contains('open')"),"brand mobile menu closes")
    if page_path=="market-map.html":
        check(page.url.split("?")[0].endswith("/map.html"),"legacy thematic map redirects to interactive 3D atlas")
    if page_path=="stores.html":
        page.locator('button[data-category="수산"]').click(timeout=3000)
        check(page.locator('button[data-category="수산"]').evaluate("(e)=>e.classList.contains('active')"),"category filter selects")
        page.locator("#store-search").fill("qwertyuiopnomatch")
        check(page.locator("#shop-empty").is_visible(),"search empty state appears")
    if page_path=="events.html":
        page.locator('button[data-event-filter="수산"]').click(timeout=3000)
        check(page.locator('button[data-event-filter="수산"]').evaluate("(e)=>e.classList.contains('active')"),"event category changes")
    if page_path=="coupons.html":
        button=page.locator("[data-claim]").first
        button.click(timeout=3000)
        check(page.locator("#wallet-qty").inner_text().strip()!="0","demo coupon added")
    if page_path=="market.html":
        page.locator("#menuToggle").click(timeout=3000)
        check(page.locator("#marketNav").evaluate("(e)=>e.classList.contains('open')"),"market mobile menu opens")
        page.locator('button[data-page="wallet"]').first.click(timeout=3000)
        check(page.locator("#wallet").evaluate("(e)=>e.classList.contains('active')"),"market wallet tab works")
    if page_path=="map.html":
        pins=page.locator(".concept-building-3d")
        check(pins.count()==9,"all nine conceptual building pins render")
        page.locator('[data-zone="seafood"]').click(timeout=3000)
        chosen=page.locator('.concept-building-3d.is-selected')
        check(chosen.count()==1,"selected map pin is unique")
        check("수산" in chosen.inner_text(),"selected building location pin matches tapped building")
    if page_path in ("index.html","home.html","coupons.html","events.html","market.html","map.html"):
        guide=page.locator('.gl-park-guide[data-gl-injected="true"]')
        check(guide.count()==1,"context mascot guide is injected")
        check(guide.locator('img').get_attribute("src")=="/assets/brand/mascot-sticker.png",
              "mascot preserves the canonical stored character")
    if page_path=="ops.html":
        page.locator('[data-view="board"]').click(timeout=3000)
        check(page.locator("#board").evaluate("(e)=>e.classList.contains('active')"),"ERP board tab works")
    return notes


def capture_inner_views(page, route, viewport):
    """Check tab pages hidden behind a single URL; capture each rendered state."""
    if viewport not in ("desktop","mobile"):
        return []
    configs={
        "market.html": ["wallet","marketing","merchant"],
        "ops.html": ["board","documents","products","settlement","checklist"],
        "ar-quest.html": ["directory","missions","coupons","delivery","merchant","guide"],
    }
    out=[]
    for state in configs.get(route,[]):
        try:
            if route=="market.html":
                if viewport=="mobile" and not page.locator("#marketNav").evaluate("(e)=>e.classList.contains('open')"):
                    page.locator("#menuToggle").click(timeout=3500)
                page.locator("#marketNav button[data-page='"+state+"']").click(timeout=3500)
                active=page.locator("#"+state).evaluate("(e)=>e.classList.contains('active')")
            elif route=="ops.html":
                page.locator('button[data-view="'+state+'"]').click(timeout=3500)
                active=page.locator("#"+state).evaluate("(e)=>e.classList.contains('active')")
            else:
                page.locator('button[data-page="'+state+'"]:visible').first.click(timeout=3500)
                active=page.locator("#page-"+state).evaluate("(e)=>e.classList.contains('active')")
            if not active: raise AssertionError("tab did not activate")
            page.wait_for_timeout(220)
            metrics=page.evaluate(AUDIT_JS)
            fname=route.replace(".html","")+"_"+state+"_"+viewport+".png"
            page.screenshot(path=str(OUT/fname),full_page=True,animations="disabled",timeout=20000)
            out.append({"view":state,"screenshot":fname,"overflow":metrics["overflow"],
                        "brokenImages":metrics["brokenImages"],"ok":True})
        except Exception as e:
            out.append({"view":state,"ok":False,"error":str(e)[:250]})
    return out

def main():
    tmp=tempfile.TemporaryDirectory()
    env=os.environ.copy()
    env.update(GARAK_DB_PATH=str(pathlib.Path(tmp.name)/"audit.sqlite"),
               GARAK_ADMIN_TOKEN="local-audit-not-production-123456789-abc",
               GARAK_QR_SECRET="local-audit-not-production-123456789-xyz",
               GARAK_ENABLE_DEMO="1",GARAK_V5_LIVE_MARKETING="0")
    env.pop("DATABASE_URL",None)
    env.pop("POSTGRES_URL",None)
    proc=subprocess.Popen([sys.executable,"server.py"],cwd=ROOT,env=env,
                         stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    results=[]
    try:
        for _ in range(80):
            try:
                urllib.request.urlopen("http://127.0.0.1:8769/index.html",timeout=1)
                break
            except Exception:
                time.sleep(.25)
        else:
            raise RuntimeError("Demo HTTP server did not start")
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
            for page_path in PAGES:
                for label,w,h in SIZES:
                    page=browser.new_page(viewport={"width":w,"height":h},
                                          device_scale_factor=1,reduced_motion="reduce")
                    errors=[]
                    page.on("pageerror",lambda exc, out=errors:out.append(str(exc)[:200]))
                    try:
                        response=page.goto("http://127.0.0.1:8769/"+page_path,
                                           wait_until="domcontentloaded",timeout=25000)
                        page.wait_for_timeout(1000 if page_path in ("market.html","ar-quest.html","map.html") else 420)
                        d=page.evaluate(AUDIT_JS)
                        d.update(path=page_path,device=label,width=w,status=response.status if response else None,
                                 errors=errors[:7])
                        fname=page_path.replace("/","_").replace(".html","")+"_"+label+".png"
                        page.screenshot(path=str(OUT/fname),full_page=True,
                                        animations="disabled",timeout=20000)
                        d["screenshot"]=fname
                        try:
                            d["interactionChecks"]=verify_controls(page,page_path,label)
                        except Exception as interaction_error:
                            d["interactionError"]=str(interaction_error)[:250]
                        d["innerViews"]=capture_inner_views(page,page_path,label)
                    except Exception as exc:
                        d={"path":page_path,"device":label,"width":w,"fatal":str(exc)[:320]}
                    results.append(d)
                    print(json.dumps({k:d.get(k) for k in ("path","device","status","overflow","imagesCount","fatal")},ensure_ascii=False),flush=True)
                    page.close()
            browser.close()
    finally:
        proc.terminate()
        try:proc.wait(timeout=5)
        except subprocess.TimeoutExpired:proc.kill()
        tmp.cleanup()
    (OUT/"audit.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
    findings=[r for r in results if r.get("fatal") or r.get("status")!=200 or r.get("overflow",0)>4 or r.get("brokenImages") or r.get("interactionError") or any((not v.get("ok")) or v.get("overflow",0)>4 or v.get("brokenImages") for v in r.get("innerViews",[]))]
    print("CAPTURED:",len(results),"FINDINGS:",len(findings),flush=True)
    if "--strict" in sys.argv and findings:
        print(json.dumps(findings[:8],ensure_ascii=False,indent=2),flush=True)
        sys.exit(1)
if __name__=="__main__":main()
