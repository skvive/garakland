"""Offline UI test without external network: Chromium rendering + real frontend JS."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import base64, json, re
P=Path(__file__).resolve().parent.parent
HTML=(P/'index.html').read_text(encoding='utf-8')
DATA=(P/'brand/data.js').read_text(encoding='utf-8')
APP=(P/'brand/app.js').read_text(encoding='utf-8')
CSS=(P/'brand/style.css').read_text(encoding='utf-8')
PAGES=['home','map','stores','store','coupons','events','merchant','guide']
PRE=P/'previews';PRE.mkdir(exist_ok=True)
ERRS=[];REPORT=[]
def setup(page,typ,photo=True):
    body=f'<!doctype html><html lang="ko"><head><meta charset="utf-8"></head><body data-page="{typ}"><div id="app"></div></body></html>'
    page.set_content(body,wait_until='domcontentloaded')
    page.evaluate('''() => {let m={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>m[k]??null,setItem:(k,v)=>{m[k]=v},removeItem:k=>{delete m[k]}}})}''')
    css=CSS
    if photo:
        f=P/'assets/editorial/market.webp'
        mime='image/webp'
        uri=f'data:{mime};base64,{base64.b64encode(f.read_bytes()).decode()}'
        css=css.replace("../assets/editorial/market.webp",uri)
    page.add_style_tag(content=css)
    page.add_script_tag(content=DATA)
    page.add_script_tag(content=APP)
    if photo:
        unique=set(page.locator('img').evaluate_all('(es)=>es.map(e=>e.getAttribute("src"))'))
        files={}
        for src in unique:
            f=P/src
            if f.exists():
                typemime='image/webp' if src.endswith('.webp') else 'image/png' if src.endswith('.png') else 'image/jpeg'
                files[src]=f'data:{typemime};base64,{base64.b64encode(f.read_bytes()).decode()}'
        page.evaluate('''d => {document.querySelectorAll('img').forEach(im=>{let x=im.getAttribute('src');if(d[x])im.src=d[x]})}''',files)
    page.wait_for_timeout(120)
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
 for view,w,h in [('pc',1440,900),('mobile',390,844)]:
  ctx=b.new_context(viewport={'width':w,'height':h},device_scale_factor=1)
  for i,typ in enumerate(PAGES,1):
   pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e: errs.append(str(e)))
   try:
    setup(pg,typ)
    widths=pg.evaluate('({page:document.documentElement.scrollWidth,viewport:window.innerWidth})')
    missing=pg.evaluate('''() => [...document.querySelectorAll('img')].filter(i=>!i.complete || i.naturalWidth===0).map(i=>i.alt)''')
    heading=pg.locator('h1').first.inner_text() if pg.locator('h1').count() else ''
    pg.screenshot(path=str(PRE/f'{i:02d}_{typ}_{view}.png'),full_page=True)
    ok=not errs and not missing and widths['page']<=widths['viewport']+2 and bool(heading)
    REPORT.append({'page':typ,'viewport':view,'ok':ok,'widths':widths,'missingPhotos':missing,'jsErrors':errs,'h1':heading.replace('\n',' ')[:48]})
   except Exception as e:
    REPORT.append({'page':typ,'viewport':view,'ok':False,'error':str(e)})
   pg.close()
  ctx.close()
 # logic tests in a single isolated document
 ctx=b.new_context(viewport={'width':1280,'height':780}); pg=ctx.new_page();setup(pg,'stores',False)
 pg.locator('#store-search').fill('과일');REPORT.append({'check':'store keyword search','ok':pg.locator('.shop-card').count()==1})
 pg.locator('#store-search').fill('');pg.locator('[data-category="수산"]').click();REPORT.append({'check':'category filter','ok':pg.locator('.shop-card').count()==1})
 pg.locator('[data-like="demo-sea"]').click();REPORT.append({'check':'favorites toggle','ok':pg.locator('[data-like="demo-sea"]').first.inner_text()=='♥'})
 # switch app page with same JS runtime by changing body and reloading app script in document
 pg.close();pg=ctx.new_page();setup(pg,'coupons',False)
 pg.locator('[data-claim="c-sea"]').first.click();REPORT.append({'check':'coupon claim','ok':pg.locator('#wallet-count').inner_text()=='1장'})
 pg.locator('[data-claim="c-sea"]').first.click();REPORT.append({'check':'coupon duplicate protection','ok':pg.locator('#wallet-count').inner_text()=='1장'})
 pg.locator('[data-remove-coupon="c-sea"]').click();REPORT.append({'check':'coupon remove','ok':pg.locator('#wallet-count').inner_text()=='0장'})
 pg.close();pg=ctx.new_page();setup(pg,'map',False);pg.locator('[data-zone="청과"]').click();REPORT.append({'check':'schematic map zone','ok':pg.locator('#zone-results .zone-shop').count()==1})
 pg.close();pg=ctx.new_page();setup(pg,'merchant',False);pg.locator('input[name="storeName"]').fill('시연점포');pg.locator('input[name="contact"]').fill('담당자');pg.locator('#merchant-demo-form button[type=submit]').click();REPORT.append({'check':'merchant draft form','ok':'임시 저장' in pg.locator('#merchant-save-result').inner_text()})
 pg.close();pg=ctx.new_page();setup(pg,'store',False);pg.locator('[data-add-cart]').first.click();REPORT.append({'check':'cart demo storage','ok':pg.evaluate('JSON.parse(localStorage.getItem("garak-brand-cart")).length')==1})
 pg.close();ctx.close();b.close()
res={'total':len(REPORT),'passed':sum(r['ok'] for r in REPORT),'failed':sum(not r['ok'] for r in REPORT),'checks':REPORT,'limitations':['External Google Maps 3D/merchant GPS/AR camera/real payment not tested','Offline Chromium render via set_content due to browser navigation blocked by environment','Images supplied as same-file data URIs for offline screenshot testing']}
(P/'docs'/'BRAND_V1_BROWSER_QA.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
for r in REPORT:print('PASS' if r['ok'] else 'FAIL',r)
print('TOTAL',res['total'],'PASS',res['passed'],'FAIL',res['failed'])
if res['failed']:raise SystemExit(1)
