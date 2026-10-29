"""v4 full-page Chrome offline mock smoke tests. Screenshots are genuine browser renders.
No claim of live Google API, real camera, payments, or market geodata validation."""
from pathlib import Path
import json, base64, re, sys
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import server
server.setup()
fixture=server.Handler.experience(object.__new__(server.Handler))
html=(ROOT/'index.html').read_text()
html=re.sub(r'<link rel="stylesheet" href="\./game/[^\"]+">','',html)
html=html.replace('<script type="module" src="./game/app.js"></script>','')
css='\n'.join((ROOT/x).read_text() for x in ['game/style.css','game/studio.css'])
css=re.sub(r'@import url\([^;]+;', '', css)
assets={p.name:'data:image/webp;base64,'+base64.b64encode(p.read_bytes()).decode() for p in (ROOT/'assets/editorial').glob('*.webp')}
for k,uri in assets.items():
 css=css.replace("url('./assets/editorial/"+k+"')","url('"+uri+"')")
 html=html.replace("url('./assets/editorial/"+k+"')","url('"+uri+"')")
nav=(ROOT/'game/navigation.mjs').read_text().replace('export const ','const ').replace('export function ','function ')
app=(ROOT/'game/app.js').read_text().replace("import {buildDirections,hasVerifiedGps} from './navigation.mjs';",'').replace('export {esc,won,link};','')
prelude='''
const fixture=__FIX__;let wallet=[];let orders=[];let xp=0;
const progress=()=>({visits:xp?[{shop_id:'demo-sea',day:'2026-10-29',method:'DEMO'}]:[],badges:[],xp,level:1,uniqueShops:xp?1:0,streak:xp?1:0,totalVisits:xp?1:0});
const respond=(value,status=200)=>Promise.resolve(new Response(JSON.stringify(value),{status,headers:{'Content-Type':'application/json'}}));
window.fetch=async (url,opts={})=>{const data=opts.body?JSON.parse(opts.body):{};
 if(url.startsWith('/api/experience'))return respond(fixture);
 if(url.startsWith('/api/progress'))return respond(progress());
 if(url.startsWith('/api/orders')&&opts.method==='POST'){orders.push({id:'GQ-UI-TEST',shop_id:data.shopId,menu_name:data.menuName,quantity:data.quantity,total:22000,mode:data.mode,status:'DEMO_REQUESTED'});return respond({orderId:'GQ-UI-TEST',ok:true})}
 if(url.startsWith('/api/orders'))return respond({items:orders});
 if(url.startsWith('/api/wallet'))return respond({items:wallet});
 if(url.startsWith('/api/demo/checkin')){xp=40;return respond({ok:true,earnedXp:40,message:'시연 스탬프'})}
 if(url.startsWith('/api/coupons/claim')){const campaign=fixture.campaigns.find(c=>c.id===data.campaignId),shop=fixture.shops.find(s=>s.id===campaign.shop_id); wallet.push({id:'ui',campaign_id:campaign.id,period:'2026-10-29',code:'12345ABCDE',shop_id:shop.id,shop_name:shop.name,discount_label:campaign.discount_label,title:campaign.title,expires_at:'2026-12-31T23:59:59',expired:false});return respond({ok:true,code:'12345ABCDE',notice:'시연'})}
 return respond({ok:true})
};
window.editorialData=__IMAGES__;
const fix=(n)=>{if(n.nodeType!==1)return;for(const img of n.matches?.('img')?[n,...n.querySelectorAll('img')]:n.querySelectorAll?.('img')||[]){const src=img.getAttribute('src')||'';for(const [key,data] of Object.entries(editorialData)){if(src.includes('/editorial/'+key)){img.src=data;break}}}};
const obs=new MutationObserver(m=>{for(const item of m){if(item.type==='attributes'){fix(item.target)}else for(const n of item.addedNodes)fix(n)}});
obs.observe(document,{childList:true,subtree:true,attributes:true,attributeFilter:['src']});fix(document.documentElement);
'''.replace('__FIX__',json.dumps(fixture,ensure_ascii=False)).replace('__IMAGES__',json.dumps(assets))

def click_nav(pg,page):
 pg.locator('button[data-page="'+page+'"]:visible').first.click()
 assert pg.locator('#page-'+page).evaluate('(e)=>e.classList.contains("active")')

def test():
 with sync_playwright() as pw:
  b=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
  for device,size in [('desktop',{'width':1440,'height':900}),('mobile',{'width':390,'height':844})]:
   pg=b.new_page(viewport=size)
   pg.on('dialog',lambda d:d.dismiss())
   errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
   pg.set_content(html,wait_until='domcontentloaded');pg.add_style_tag(content=css);pg.add_script_tag(content=prelude);pg.add_script_tag(content=nav+'\n'+app)
   pg.locator('.shop-card').first.wait_for(timeout=20000)
   assert pg.locator('.shop-card').count()==4
   assert pg.locator('.district-card').count()==3
   pg.screenshot(path=str(ROOT/f'v4_{device}_home.png'),full_page=True)
   # Guided photo navigation and category fast pills
   pg.locator('.district-card').first.click()
   assert pg.locator('#page-directory.active').count()==1
   assert pg.locator('#shopFilterPills .active').count()==1
   click_nav(pg,'directory')
   pg.screenshot(path=str(ROOT/f'v4_{device}_directory.png'),full_page=True)
   pg.locator('#shopSearch').fill('가상')  # may not match; clear and open
   pg.locator('#shopSearch').fill('')
   pg.locator('#shopFilterPills [data-filter-pill="all"]').click()
   pg.locator('.directory-row').first.click()
   assert pg.locator('#shopDialog').evaluate('(e)=>e.open')
   assert pg.locator('#modalFavorite').count()==1
   pg.locator('#modalFavorite').click();assert '저장됨' in pg.locator('#modalFavorite').inner_text()
   pg.screenshot(path=str(ROOT/f'v4_{device}_shop.png'))
   pg.locator('#shopDialog .modal-close').click()
   pg.locator('#shopFilterPills [data-filter-pill="favorites"]').click()
   assert pg.locator('.directory-row').count()==1
   # Coupon -> Google URL bridge (mock UI, real URL generation)
   click_nav(pg,'coupons');assert pg.locator('.coupon-card').count()==4
   pg.screenshot(path=str(ROOT/f'v4_{device}_coupons.png'),full_page=True)
   pg.locator('[data-claim]').first.click()
   pg.wait_for_function("document.getElementById('routeDialog').open",timeout=10000)
   assert pg.locator('#routeDialog').evaluate('(e)=>e.open')
   assert 'google.com/maps/dir' in pg.locator('#routeWalk').get_attribute('href')
   pg.screenshot(path=str(ROOT/f'v4_{device}_navigation.png'))
   pg.locator('#routeDialog [data-close]').click()
   # AR and shop information
   click_nav(pg,'explore');pg.locator('#startCamera').click();pg.locator('#manualCode').fill('GARAKLAND:demo-sea');pg.locator('#manualSearch').click()
   assert not pg.locator('#arDiscovery').evaluate('(e)=>e.hidden')
   pg.locator('#arOpenShop').click()
   pg.locator('#demoVisit').click();pg.locator('#shopDialog .modal-close').click()
   click_nav(pg,'missions');assert pg.locator('#missionXp').inner_text()=='40 XP'
   pg.screenshot(path=str(ROOT/f'v4_{device}_missions.png'),full_page=True)
   # Food / ordering demo
   click_nav(pg,'delivery');assert pg.locator('.order-shop').count()>=4
   pg.screenshot(path=str(ROOT/f'v4_{device}_delivery.png'),full_page=True)
   pg.locator('[data-order-shop]').first.click();assert pg.locator('#orderDialog').evaluate('(e)=>e.open')
   pg.locator('#sendOrder').click();pg.locator('#ordersList .history-row').first.wait_for(timeout=10000);assert pg.locator('#ordersList .history-row').count()==1
   # Merchant and editorial guide
   click_nav(pg,'merchant');assert pg.locator('.merchant-welcome').count()==1
   pg.screenshot(path=str(ROOT/f'v4_{device}_merchant.png'),full_page=True)
   click_nav(pg,'guide');assert pg.locator('.guide-card').count()==3
   pg.screenshot(path=str(ROOT/f'v4_{device}_guide.png'),full_page=True)
   assert pg.locator('#page-guide').is_visible()
   # Source must contain no invisible oversized horizontal content
   overflow=pg.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth')
   assert overflow<=2,(device,overflow)
   visible_images=pg.locator('#page-guide img').count()
   assert visible_images==4,(device,visible_images)
   assert not errors,(device,errors)
   print(device,'PASS; 7 pages, favorite, filtered directory, coupon, navigation, AR, stamp, ordering, guide; horizontal overflow:',overflow)
   pg.close()
  b.close()

if __name__=='__main__':test()
