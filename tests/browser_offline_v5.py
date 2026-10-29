"""Chromium UI test with isolated offline document and real HTTP API via Python bridge.
This avoids restricted Chromium localhost networking in the evaluation container.
"""
import os,time,subprocess,sys,requests
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
env={**os.environ,'GARAK_DB_PATH':str(ROOT/'data'/'v5_browser_bridge.sqlite'),'GARAK_ADMIN_TOKEN':'bridge-admin-key-999','PORT':'18741'}
proc=subprocess.Popen([sys.executable,'server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 for i in range(30):
  try:
   if requests.get('http://127.0.0.1:18741/api/v5/public',timeout=1).ok:break
  except Exception:time.sleep(.15)
 else:raise RuntimeError('server unavailable')
 html=(ROOT/'market.html').read_text(encoding='utf8').replace('<link rel="stylesheet" href="/market/theme.css">','').replace('<script src="/market/ui.js" defer></script>','')
 html=html.replace('<head>','<head><base href="https://garak.test/">')
 css=(ROOT/'market/theme.css').read_text(encoding='utf8')
 css=css.replace(css.split('\n')[0],'')
 js=(ROOT/'market/ui.js').read_text(encoding='utf8')
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
  for device,w,h in [('desktop',1440,900),('mobile',390,844)]:
   sess=requests.Session()
   def call(source,path,opt):
    if not path.startswith('/api/'):return {'status':404,'body':{'error':'unrecognized path'}}
    headers=dict(opt.get('headers') or {})
    r=sess.request(opt.get('method') or 'GET','http://127.0.0.1:18741'+path,data=opt.get('body'),headers=headers,timeout=8)
    try: body=r.json()
    except:body={'error':r.text[:300]}
    return {'status':r.status_code,'body':body}
   ctx=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=1)
   page=ctx.new_page()
   page.expose_binding('bridgeAPI',call)
   def route_asset(route):
    path=urlparse(route.request.url).path
    f=(ROOT/path.lstrip('/')).resolve()
    if f.is_file() and f.is_relative_to(ROOT) and path.startswith('/assets/'):
     route.fulfill(path=str(f))
    else:route.abort()
   page.route('**/*',route_asset)
   page.set_content(html,wait_until='domcontentloaded')
   page.add_style_tag(content=css)
   page.evaluate('''window.fetch=async function(path,opt={}) {const r=await window.bridgeAPI(path,{method:opt.method||'GET',headers:opt.headers||{},body:opt.body});return new Response(JSON.stringify(r.body),{status:r.status,headers:{'Content-Type':'application/json'}})};true''')
   errs=[];page.on('pageerror',lambda e:errs.append(str(e)))
   page.on('dialog',lambda dialog:dialog.dismiss())
   page.add_script_tag(content=js)
   page.locator('.card').first.wait_for(timeout=10000)
   n=page.locator('.card').count()
   assert n==4,n
   assert not errs,errs
   assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2'),f'{device} home overflow'
   page.screenshot(path=str(ROOT/f'v5_{device}_home.png'),full_page=True)
   page.locator('[data-claim="V5-DEMO-FRUIT"]').click()
   page.wait_for_timeout(450)
   if device=='mobile':
    page.locator('#menuToggle').click()
   page.locator('nav [data-page="wallet"]').first.click()
   page.wait_for_timeout(400)
   assert page.locator('#myTicketCount').inner_text()=='1',page.locator('#myTicketCount').inner_text()
   page.screenshot(path=str(ROOT/f'v5_{device}_wallet.png'),full_page=True)
   if device=='mobile':page.locator('#menuToggle').click()
   page.locator('nav [data-page="marketing"]').first.click()
   page.locator('#consentForm input[name=email]').fill(f'v5-{device}@example.org')
   page.locator('#consentForm input[name=email_opt]').check()
   page.locator('#consentForm button[type=submit]').click()
   page.locator('#consentMsg').filter(has_text='저장').wait_for(timeout=5000)
   page.screenshot(path=str(ROOT/f'v5_{device}_marketing.png'),full_page=True)
   if device=='mobile':page.locator('#menuToggle').click()
   page.locator('nav [data-page="merchant"]').first.click()
   page.screenshot(path=str(ROOT/f'v5_{device}_merchant.png'),full_page=True)
   assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2'),f'{device} merchant overflow'
   print(device,'cards',n,'wallet',page.locator('#myTicketCount').inner_text(),'JS errors',errs,flush=True)
   assert not errs,errs
   ctx.close()
  browser.close()
finally:
 proc.terminate()
 try:proc.wait(timeout=3)
 except Exception:proc.kill()
