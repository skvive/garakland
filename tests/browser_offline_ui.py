"""Browser UI test via DOM injection because this environment administratively blocks page navigation.
Exercises actual HTML, CSS, JS and a deterministic API response mock; not Google or physical camera.
"""
import sys,base64,json,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));import server
server.setup()
dummy=object.__new__(server.Handler)
fixture=server.Handler.experience(dummy)
css=(ROOT/'game/style.css').read_text();css='\n'.join(x for x in css.splitlines() if not x.strip().startswith('@import'))
html=(ROOT/'index.html').read_text()
html=html.replace('<link rel="stylesheet" href="./game/style.css">','').replace('<script type="module" src="./game/app.js"></script>','')
js=(ROOT/'game/app.js').read_text().replace('export {esc,won,link};','')
assets={f.name:'data:image/png;base64,'+base64.b64encode(f.read_bytes()).decode() for f in (ROOT/'assets/demo').glob('*.png')}
prelude='''
window.fixture=%s;window.wallet=[];window.orders=[];window.progress={visits:[],badges:[{id:'first',label:'첫 발견',emoji:'🧭',earned:false}],xp:0,level:1,streak:0,uniqueShops:0,totalVisits:0};
window.fetch=async (url,opts={})=>{let res=null;const b=opts.body?JSON.parse(opts.body):{};
 if(url.startsWith('/api/experience'))res=window.fixture;
 else if(url.startsWith('/api/progress'))res=window.progress;
 else if(url.startsWith('/api/wallet'))res={items:window.wallet};
 else if(url.startsWith('/api/orders')&& !opts.method)res={items:window.orders};
 else if(url.includes('/api/demo/checkin')){window.progress.xp=40;window.progress.level=1;window.progress.uniqueShops=1;window.progress.totalVisits=1;window.progress.visits=[{shop_id:b.shopId,day:'2026-10-29',method:'DEMO'}];window.progress.badges[0].earned=true;res={ok:true,newVisit:true,earnedXp:40,message:'획득'};}
 else if(url.includes('/api/coupons/claim')){let c=window.fixture.campaigns.find(c=>c.id===b.campaignId);window.wallet.push({id:'x',campaign_id:c.id,period:'2026-10-29',code:'1A2B3C4D5E',issued_at:'2026-10-29',expires_at:'2026-10-29T23:59',redeemed_at:null,shop_name:'가상 매장',discount_label:c.discount_label,title:c.title,expired:false});res={ok:true,code:'1A2B3C4D5E',notice:'시연'};}
 else if(url==='/api/orders' && opts.method==='POST'){window.orders.push({id:'GQ-ABC123',shop_id:b.shopId,menu_name:b.menuName,quantity:b.quantity,total:22000,mode:b.mode,status:'DEMO_REQUESTED'});res={ok:true,orderId:'GQ-ABC123',total:22000};}
 else res={ok:true};return new Response(JSON.stringify(res),{status:200,headers:{'Content-Type':'application/json'}})
};
window.inlineAssets=%s;
const imObserver=new MutationObserver(()=>{for(const img of document.querySelectorAll('img')){for(const [name,uri] of Object.entries(window.inlineAssets)){if(img.getAttribute('src')?.includes(name)){img.setAttribute('src',uri);break}}}});
imObserver.observe(document,{childList:true,subtree:true});
'''%(json.dumps(fixture,ensure_ascii=False),json.dumps(assets))
with sync_playwright() as p:
 for device,size in [('desktop',{'width':1440,'height':900}),('mobile',{'width':390,'height':844})]:
  browser=p.chromium.launch(headless=True,executable_path=shutil.which('chromium') or None,args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
  page=browser.new_page(viewport=size)
  errors=[];page.on('pageerror',lambda e: errors.append(str(e)))
  page.set_content(html,wait_until='domcontentloaded');page.add_style_tag(content=css);page.add_script_tag(content=prelude);page.add_script_tag(content=js)
  page.wait_for_selector('.shop-card',timeout=5000)
  assert page.locator('.shop-card').count()==4
  print(device,'loaded',page.locator('.shop-card').count(),'cards')
  page.screenshot(path=str(ROOT/f'preview_{device}.png'),full_page=True)
  page.locator('.shop-card').first.click();assert page.locator('#shopDialog').evaluate('(x)=>x.open')
  assert page.locator('#shopDialog img').count()==2
  page.screenshot(path=str(ROOT/f'preview_{device}_shop.png'))
  page.locator('.modal-close').click()
  page.locator('button[data-page="coupons"]:visible').first.click();assert page.locator('.coupon-card').count()==4
  page.locator('.coupon-card button').first.click();page.wait_for_timeout(200)
  assert page.locator('.wallet-item').count()==1
  page.screenshot(path=str(ROOT/f'preview_{device}_coupons.png'))
  page.locator('button[data-page="delivery"]:visible').first.click();page.locator('[data-order-shop]').first.click()
  assert page.locator('#orderDialog').evaluate('(x)=>x.open')
  page.locator('#sendOrder').click();page.wait_for_timeout(200)
  assert page.locator('#ordersList .history-row').count()==1
  page.locator('button[data-page="explore"]:visible').first.click();page.locator('#startCamera').click()
  page.locator('#manualCode').fill('GARAKLAND:demo-sea');page.locator('#manualSearch').click()
  assert not page.locator('#arDiscovery').evaluate('(x)=>x.hidden')
  page.locator('#arOpenShop').click();assert page.locator('#shopDialog').evaluate('(x)=>x.open')
  page.locator('#demoVisit').click();page.wait_for_timeout(200)
  page.locator('.modal-close').click();page.locator('button[data-page="missions"]:visible').first.click()
  assert page.locator('#missionXp').inner_text()=='40 XP'
  overflow=page.evaluate('document.documentElement.scrollWidth-innerWidth')
  assert overflow<=2,overflow
  assert not errors,errors
  print(device,'interactive UI pass; overflow',overflow)
  browser.close()
print('OFFLINE BROWSER UI PASS (network+camera not tested)')
