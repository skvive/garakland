"""Offline Chromium UI verification with stubbed API. External Google Maps launch is NOT tested."""
import re,json
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'index.html').read_text()
HTML=re.sub(r'<link rel="stylesheet" href="\./game/style\.css">','',HTML)
HTML=re.sub(r'<script type="module" src="\./game/app\.js"></script>','',HTML)
CSS=(ROOT/'game/style.css').read_text()
CSS=re.sub(r"@import url\([^;]+;",'',CSS)
NAV=(ROOT/'game/navigation.mjs').read_text().replace('export const ','const ').replace('export function ','function ')
APP=(ROOT/'game/app.js').read_text()
APP=APP.replace("import {buildDirections,hasVerifiedGps} from './navigation.mjs';",'')
APP=APP.replace('export {esc,won,link};','')
# Explicit mock API responses as close as possible to live server response shapes.
MOCK=r'''
const shops=[
 {id:'demo-fruit',name:'[시연] 색동과일',category:'청과',building:'produce',floor:'1F',room:'P-02',coordinateStatus:'unverified',latitude:null,longitude:null,isDemo:true,hero:'',menu_image:'',menu:[{name:'과일컵',price:7500}],blogUrl:'',delivery_url:''},
 {id:'test-real',name:'[테스트] 실측 인증 매장',category:'수산',building:'sales',floor:'1F',room:'C-10',coordinateStatus:'verified',latitude:37.494321,longitude:127.112345,isDemo:false,hero:'',menu_image:'',menu:[{name:'광어회',price:22000}],blogUrl:'',delivery_url:''}
];
const campaigns=[
 {id:'c-fruit',shop_id:'demo-fruit',title:'제철 과일 쿠폰',discount_label:'10% 할인',details:'시연',recurrence:'WEEKLY',stock:30},
 {id:'c-real',shop_id:'test-real',title:'등록 상인 쿠폰',discount_label:'1천원 할인',details:'테스트',recurrence:'ONCE',stock:30}
];
const wallet=[];
const json=(payload,status=200)=>Promise.resolve(new Response(JSON.stringify(payload),{status,headers:{'Content-Type':'application/json'}}));
window.fetch=async(url,opts={})=>{
 const u=new URL(url,'https://garakland.test');const path=u.pathname;
 if(path==='/api/experience')return json({shops,campaigns,demoMode:true});
 if(path==='/api/progress')return json({xp:0,level:1,streak:0,uniqueShops:0,visits:[],badges:[]});
 if(path==='/api/orders')return json({items:[]});
 if(path==='/api/wallet')return json({items:wallet});
 if(path==='/api/coupons/claim'){
  const {campaignId}=JSON.parse(opts.body);const c=campaigns.find(x=>x.id===campaignId);
  if(wallet.some(x=>x.campaign_id===campaignId))return json({error:'이미 발급'},409);
  const s=shops.find(x=>x.id===c.shop_id);
  wallet.push({id:campaignId,code:campaignId==='c-real'?'REAL123456':'DEMO123456',campaign_id:campaignId,period:'ONCE',shop_id:c.shop_id,shop_name:s.name,title:c.title,discount_label:c.discount_label,expires_at:'2026-12-01T23:59:59',expired:false,redeemed_at:null});
  return json({ok:true,code:wallet.at(-1).code,notice:'테스트 쿠폰'});
 }
 return json({error:'미구현 Mock: '+path},404);
};
'''
def test():
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
  for device,viewport in [('desktop',{'width':1440,'height':900}),('mobile',{'width':390,'height':844})]:
   page=browser.new_page(viewport=viewport)
   errors=[];page.on('pageerror',lambda exc:errors.append(str(exc)))
   page.set_content(HTML,wait_until='domcontentloaded')
   page.add_style_tag(content=CSS)
   page.add_script_tag(content=MOCK)
   page.add_script_tag(content=NAV+'\n'+APP)
   page.locator('#featuredShops [data-shop]').first.wait_for(timeout=12000)
   page.locator('[data-page="coupons"]:visible').first.click()
   page.locator('[data-claim="c-fruit"]').click()
   page.wait_for_function("document.getElementById('routeDialog').open",timeout=12000)
   assert '가상' in page.locator('#routeNotice').inner_text()
   href=page.locator('#routeWalk').get_attribute('href')
   assert '가락시장' in parse_qs(urlsplit(href).query)['destination'][0]
   assert 'navigate' in href
   page.locator('[data-close="routeDialog"]').click()
   page.locator('#walletItems .wallet-click').first.click()
   page.wait_for_function("document.getElementById('routeDialog').open",timeout=12000)
   page.locator('[data-close="routeDialog"]').click()
   # Real verified coordinates, correct coupon->shop mapping, and accurate Google Map URL
   page.locator('[data-claim="c-real"]').click()
   page.wait_for_function("document.getElementById('routeDialog').open",timeout=12000)
   assert '확인된 매장 GPS' in page.locator('#routeAccuracy').inner_text()
   href=page.locator('#routeWalk').get_attribute('href')
   dest=parse_qs(urlsplit(href).query)['destination'][0]
   assert dest=='37.494321,127.112345',dest
   page.locator('[data-close="routeDialog"]').click()
   assert page.locator('#walletItems .wallet-nav').count()==2
   assert not errors, str(errors)
   overflow=page.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth')
   assert overflow<=2, f'layout overflow {device}: {overflow}px'
   # Only screenshots internal UI (no actual Google navigation)
   page.locator('#walletItems .wallet-click').last.click()
   page.screenshot(path=str(ROOT/f'preview_nav_{device}.png'),full_page=True)
   print(f'{device}: coupon claim + wallet tapping + verified GPS route + demo safe fallback + no overflow: PASS')
   page.close()
  browser.close()
if __name__=='__main__':test()
