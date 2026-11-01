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
 "login.html","documents.html","unsubscribe.html","design_gallery.html"
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
    findings=[r for r in results if r.get("fatal") or r.get("status")!=200 or r.get("overflow",0)>4 or r.get("brokenImages")]
    print("CAPTURED:",len(results),"FINDINGS:",len(findings),flush=True)
    if "--strict" in sys.argv and findings:
        print(json.dumps(findings[:8],ensure_ascii=False,indent=2),flush=True)
        sys.exit(1)
if __name__=="__main__":main()
