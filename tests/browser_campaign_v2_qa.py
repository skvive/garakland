"""Chromium campaign acceptance at 360/390/768/1440. Local HTTP-only QA."""
import functools
import http.server
import socketserver
import threading
from io import BytesIO
from PIL import Image,ImageStat
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'qa-artifacts'/'campaign-v2'
OUT.mkdir(parents=True,exist_ok=True)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args): pass
class Server(socketserver.ThreadingTCPServer): allow_reuse_address=True
handler=functools.partial(Quiet,directory=str(ROOT))
httpd=Server(('127.0.0.1',0),handler)
threading.Thread(target=httpd.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{httpd.server_address[1]}/lotteworld-next.html'
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True)
  for name,width,height in [('mobile360',360,740),('mobile390',390,844),('tablet',768,1024),('desktop',1440,900)]:
   page=browser.new_page(viewport={'width':width,'height':height},reduced_motion='reduce')
   failures=[];js_errors=[]
   page.on('pageerror',lambda e:js_errors.append(str(e)))
   page.on('requestfailed',lambda r:failures.append(r.url))
   response=page.goto(url,wait_until='networkidle',timeout=30000)
   assert response is not None and response.status==200
   assert '가락랜드' in page.title()
   assert '롯데월드 다음 코스' in page.locator('#campaignTitle').inner_text()
   assert page.locator('.lot-v2-hero-visual img').first.evaluate('x=>x.complete && x.naturalWidth>0')
   assert page.locator('.lot-v2-experience-card').count()==3
   assert page.locator('a[href*="indoor-map.html?floor="]').count()>=5
   assert page.locator('a[href*="travelmode=transit"]').count()==1
   assert page.locator('.lot-v2-disclaimer').count()==1
   assert page.locator('img[src*="garak-hansang-official-guide"]').count()>=2
   for img in page.locator('main img').all():
    img.scroll_into_view_if_needed(timeout=6000)
    assert img.evaluate('x=>x.complete && x.naturalWidth>0'),img.get_attribute('src')
    img.evaluate('x=>x.decode()')
   # A loaded-but-unpainted lazy image is a delivery defect for a visual landing page.
   for card in page.locator('.lot-v2-card-media').all():
    card.scroll_into_view_if_needed(timeout=6000)
    page.wait_for_timeout(160)
    image=Image.open(BytesIO(card.screenshot())).convert('RGB')
    variance=ImageStat.Stat(image).stddev
    assert max(variance)>12,(name,'card is a blank color block',variance)
   page.evaluate('window.scrollTo(0,0)')
   page.wait_for_timeout(160)
   overflow=page.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')
   assert overflow<=4,(name,'horizontal overflow',overflow)
   assert not failures,(name,'request failures',failures)
   assert not js_errors,(name,'JS errors',js_errors)
   page.screenshot(path=str(OUT/(name+'.png')),full_page=True)
   print(f'PASS campaign {name} images loaded, nav/CTA, overflow={overflow}, JS errors=0')
   page.close()
  browser.close()
finally:
 httpd.shutdown();httpd.server_close()
