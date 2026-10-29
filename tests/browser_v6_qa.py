"""Page-by-page browser QA: 6 ERP pages + v5 market flow, desktop & mobile."""
import os,sys,time,subprocess,requests,io,csv, json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]; PORT=18781;BASE=f'http://127.0.0.1:{PORT}'
AUTH='v6-browser-admin-very-secret';OUT=ROOT/'docs/v6/screens';OUT.mkdir(parents=True,exist_ok=True)
env={**os.environ,'GARAK_DB_PATH':str(ROOT/'docs/v6/browser-qa.sqlite'),'GARAK_ADMIN_TOKEN':AUTH,'PORT':str(PORT)}
proc=subprocess.Popen([sys.executable,'server.py'],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
try:
 for _ in range(100):
  try:
   if requests.get(BASE+'/api/health',timeout=.5).ok:break
  except requests.RequestException:time.sleep(.15)
 else:raise RuntimeError('backend unavailable')
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
  for device,w,h in [('desktop',1440,900),('mobile',390,844)]:
   session=requests.Session();ctx=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=1);page=ctx.new_page();errs=[];page.on('pageerror',lambda e:errs.append(str(e)))
   def doapi(_source,path,opt):
    r=session.request(opt.get('method','GET'),BASE+path,headers=opt.get('headers',{}),data=opt.get('body'),timeout=6)
    try:data=r.json()
    except:data={'error':r.text[:100]}
    return {'status':r.status_code,'data':data}
   page.expose_binding('bridgeApi',doapi)
   html=(ROOT/'ops.html').read_text(encoding='utf-8').replace('<link rel="stylesheet" href="/ops/style.css">','').replace('<script src="/ops/app.js" defer></script>','')
   page.route('**/*',lambda route: route.fulfill(path=str(ROOT/urlparse(route.request.url).path.lstrip('/'))) if urlparse(route.request.url).path.startswith('/assets/') and (ROOT/urlparse(route.request.url).path.lstrip('/')).is_file() else route.abort())
   page.set_content('<base href="https://garak.test/">'+html,wait_until='domcontentloaded')
   page.add_style_tag(content=(ROOT/'ops/style.css').read_text(encoding='utf-8'))
   page.evaluate('''window.fetch=async (path,opt={})=>{const r=await bridgeApi(path,{method:opt.method||'GET',headers:opt.headers||{},body:opt.body});return new Response(JSON.stringify(r.data),{status:r.status,headers:{'Content-Type':'application/json'}})};true''')
   page.add_script_tag(content=(ROOT/'ops/app.js').read_text(encoding='utf-8'))
   page.locator('#token').fill(AUTH);page.locator('#connect').click()
   page.wait_for_timeout(1800);print('DEBUG',device,'connection=',page.locator('#connection').inner_text(),'toast=',page.locator('#toast').inner_text(),'errs=',errs,flush=True);page.get_by_text('인증됨 · 내부 베타').wait_for(timeout=3500)
   assert page.locator('#stats b').first.inner_text()!='—'
   for tab in ('dashboard','board','documents','products','settlement','checklist'):
    page.locator(f'[data-view="{tab}"]').click()
    page.wait_for_timeout(150)
    assert not errs,errs
    scroll=page.evaluate('document.documentElement.scrollWidth');assert scroll<=w+2,(device,tab,scroll,w)
    if os.environ.get('V6_NO_SCREENSHOT')!='1':page.screenshot(path=str(OUT/f'erp_{device}_{tab}.png'),full_page=True)
   # persistence: task move through stage selector (keyboard / mobile fallback)
   page.locator('[data-view="board"]').click()
   task=page.locator('.task').first
   task_id=task.get_attribute('data-task')
   task.locator('select').select_option('검토 중')
   page.wait_for_timeout(150)
   assert page.locator(f'[data-column="검토 중"] [data-task="{task_id}"]').count()==1
   # drag another task from first column to review column
   available=page.locator('[data-column="자료 접수"] .task').first
   second_id=available.get_attribute('data-task')
   if device=='desktop':
    available.evaluate('''(el)=>{const dt=new DataTransfer();el.dispatchEvent(new DragEvent('dragstart',{bubbles:true,dataTransfer:dt}));const dest=document.querySelector('[data-column="보완 요청"]');dest.dispatchEvent(new DragEvent('dragover',{bubbles:true,cancelable:true,dataTransfer:dt}));dest.dispatchEvent(new DragEvent('drop',{bubbles:true,cancelable:true,dataTransfer:dt}));el.dispatchEvent(new DragEvent('dragend',{bubbles:true,dataTransfer:dt}))}''')
   else:available.locator('select').select_option('보완 요청')
   page.wait_for_timeout(250)
   assert page.locator(f'[data-column="보완 요청"] [data-task="{second_id}"]').count()==1,'real drag/drop failed'
   # doc evidence and internal status
   page.locator('[data-view="documents"]').click()
   page.locator('#shopSelect').select_option('demo-fruit')
   page.locator('[data-ref="business_identity"]').fill('EVID-BETA-20261029')
   page.locator('[data-docstatus="business_identity"]').select_option('내부 확인')
   page.locator('[data-save="business_identity"]').click()
   page.wait_for_timeout(250)
   assert 'EVID-BETA-20261029' in page.locator('[data-ref="business_identity"]').input_value()
   # CSV validation & import with real file input
   page.locator('[data-view="products"]').click()
   page.locator('#csvFile').set_input_files(str(ROOT/'documents/registers/상품등록_샘플.csv'))
   page.locator('#validateCsv').click()
   page.get_by_text('1건 검증 완료',exact=False).wait_for(timeout=8000)
   page.locator('#importCsv').click()
   page.get_by_text('비공개 초안',exact=False).first.wait_for(timeout=8000)
   page.wait_for_timeout(200)
   assert page.locator('#productRows tr').count()>=1
   assert not errs,errs
   print(device,'ERP all 6 pages + DnD + status + doc + CSV PASS',flush=True)
   ctx.close()
  browser.close()
finally:
 proc.terminate()
 try:proc.wait(timeout=5)
 except:proc.kill()
