"""Integration tests against in-process HTTP server, isolated SQLite, no Google key needed."""
import os,sys,io,base64,json,time,threading,tempfile,unittest,urllib.request,urllib.error,http.cookiejar
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import server,registry_server
from http.server import ThreadingHTTPServer

class BetaTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory()
  registry_server.DB=Path(cls.temp.name)/'test.sqlite';server.DB=registry_server.DB
  server.setup()
  cls.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
  cls.port=cls.http.server_address[1]
  cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start()
 @classmethod
 def tearDownClass(cls):cls.http.shutdown();cls.http.server_close();cls.temp.cleanup()
 def setUp(self):self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
 def request(self,path,body=None,headers=None,opener=None):
  h=headers or {}
  if body is not None:
   h={'Content-Type':'application/json','X-Garak-Client':'1',**h};body=json.dumps(body,ensure_ascii=False).encode()
  req=urllib.request.Request(f'http://127.0.0.1:{self.port}{path}',data=body,headers=h)
  try:
   resp=(opener or self.opener).open(req,timeout=8)
   raw=resp.read();return resp.status,json.loads(raw) if path.startswith('/api/') else raw
  except urllib.error.HTTPError as e:
   raw=e.read();return e.code,json.loads(raw) if path.startswith('/api/') else raw
 def test_01_catalog_and_map(self):
  code,p=self.request('/api/experience');self.assertEqual(code,200)
  self.assertEqual(len([x for x in p['shops'] if x['isDemo']]),4)
  self.assertGreaterEqual(len(p['campaigns']),4)
  self.assertFalse(any(x['id']=='source-danong' for x in p['shops']))
  status,body=self.request('/map.html');self.assertEqual(status,200)
  self.assertIn(b'<!doctype html>',body.lower())
 def test_02_checkin_and_progress(self):
  code,x=self.request('/api/demo/checkin',{'shopId':'demo-fruit'});self.assertEqual(code,200);self.assertTrue(x['newVisit']);self.assertEqual(x['earnedXp'],40)
  code,y=self.request('/api/demo/checkin',{'shopId':'demo-fruit'});self.assertEqual(code,200);self.assertFalse(y['newVisit']);self.assertEqual(y['earnedXp'],0)
  _,p=self.request('/api/progress');self.assertEqual(p['totalVisits'],1);self.assertEqual(p['xp'],40)
  _,invalid=self.request('/api/demo/checkin',{'shopId':'demo-anything'});self.assertFalse(invalid.get('ok',False))
 def test_03_session_isolation(self):
  self.request('/api/demo/checkin',{'shopId':'demo-sea'})
  other=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
  _,p=self.request('/api/progress',opener=other);self.assertEqual(p['xp'],0)
 def test_04_coupon_once_per_period_and_redeem(self):
  _,a=self.request('/api/coupons/claim',{'campaignId':'c-fruit'});self.assertEqual(a['ok'],True)
  status,b=self.request('/api/coupons/claim',{'campaignId':'c-fruit'});self.assertEqual(status,409)
  _,w=self.request('/api/wallet');self.assertEqual(len(w['items']),1)
  status,_=self.request('/api/merchant/redeem',{'shopId':'demo-fruit','code':a['code']});self.assertEqual(status,403)
  h={'X-Garak-Admin-Token':server.ADMIN_TOKEN}
  _,result=self.request('/api/merchant/redeem',{'shopId':'demo-fruit','code':a['code']},headers=h);self.assertTrue(result['ok'])
  status,_=self.request('/api/merchant/redeem',{'shopId':'demo-fruit','code':a['code']},headers=h);self.assertEqual(status,409)
 def test_05_order_validation(self):
  status,x=self.request('/api/orders',{'shopId':'demo-sea','menuName':'참돔 모둠','quantity':2,'mode':'delivery_request','total':1})
  self.assertEqual(status,200);self.assertEqual(x['total'],44000)
  _,a=self.request('/api/orders');self.assertTrue(any(v['id']==x['orderId'] for v in a['items']))
  h={'X-Garak-Admin-Token':server.ADMIN_TOKEN}
  status,b=self.request('/api/merchant/order-status',{'shopId':'demo-sea','orderId':x['orderId'],'status':'DEMO_ACKNOWLEDGED'},headers=h);self.assertEqual(status,200)
  status,_=self.request('/api/orders',{'shopId':'demo-sea','menuName':'nonexistent','quantity':1,'mode':'pickup'});self.assertEqual(status,400)
 def test_06_merchant_permissions_qr(self):
  status,_=self.request('/api/merchant/qr?shopId=demo-sea');self.assertEqual(status,403)
  h={'X-Garak-Admin-Token':server.ADMIN_TOKEN}
  _,a=self.request('/api/admin/merchant-key',{'shopId':'demo-sea'},headers=h);self.assertTrue(a['merchantKey'])
  status,q=self.request('/api/merchant/qr?shopId=demo-sea',headers={'X-Garak-Merchant-Key':a['merchantKey']});self.assertEqual(status,200);self.assertTrue(q['token']);self.assertTrue(q['image'] or q['image'] is None)
  status,p=self.request('/api/checkin',{'shopId':'demo-sea','qrToken':q['token'],'latitude':37.494,'longitude':127.112,'accuracy':7});self.assertEqual(status,403)
  self.assertIn('좌표',p['error'])
 def test_07_merchant_coupon_and_metadata(self):
  h={'X-Garak-Admin-Token':server.ADMIN_TOKEN}
  status,p=self.request('/api/merchant/campaign',{'shopId':'demo-fruit','title':'테스트 정기 혜택','details':'검증용','discountLabel':'5% 할인','recurrence':'DAILY','stock':2},headers=h);self.assertEqual(status,200)
  self.assertTrue(p['campaignId'])
  status,_=self.request('/api/merchant/campaign',{'shopId':'demo-fruit','title':'a','discountLabel':'b','recurrence':'HOURLY','stock':2},headers=h);self.assertEqual(status,400)
  status,p=self.request('/api/admin/metadata',{'shopId':'demo-fruit','menu':[{'name':'과일도시락','price':7000}],'deliveryUrl':'javascript:alert(1)'},headers=h);self.assertEqual(status,200)
  _,a=self.request('/api/experience');r=next(x for x in a['shops'] if x['id']=='demo-fruit');self.assertEqual(r['delivery_url'],'');self.assertEqual(r['menu'][0]['price'],7000)
 def test_08_photo_match(self):
  try:
   import cv2, numpy, PIL
  except ImportError:
   self.skipTest('Optional OpenCV/NumPy/Pillow not installed')
  from PIL import Image
  image=Image.open(ROOT/'assets/demo/sea-poster.png').convert('RGB')
  image.thumbnail((800,900));buffer=io.BytesIO();image.save(buffer,format='JPEG',quality=82)
  status,r=self.request('/api/recognize',{'image':base64.b64encode(buffer.getvalue()).decode()});self.assertEqual(status,200)
  self.assertTrue(r['supported']);self.assertTrue(r['matched'],str(r));self.assertEqual(r['shopId'],'demo-sea')
  status,_=self.request('/api/recognize',{'image':'!notimage'});self.assertEqual(status,400)
 def test_09_permissions_and_legacy_import(self):
  status,_=self.request('/data/garakland.sqlite');self.assertEqual(status,404)
  status,_=self.request('/api/import',{'items':[]});self.assertEqual(status,403)
  status,_=self.request('/api/demo/checkin',{'shopId':'demo-sea'},headers={'X-Garak-Client':'0'});self.assertEqual(status,400)
 def test_10_geofence_math_and_period(self):
  self.assertLess(server.haversine(37.49,127.11,37.49,127.11),.1)
  self.assertGreater(server.haversine(37.49,127.11,37.50,127.11),1000)
  self.assertRegex(server.period_key('WEEKLY'),r'^\d{4}-W\d{2}$')
 def test_11_verified_shop_gps_qr(self):
  h={'X-Garak-Admin-Token':server.ADMIN_TOKEN}
  record={'id':'verified-test','name':'[테스트] 좌표 인증 매장','category':'수산','building':'seafood','floor':'1F','room':'TEST1','description':'검증 테스트','address':'서울 송파구','latitude':37.494,'longitude':127.112,'coordinateStatus':'verified','blogUrl':'https://example.com/shop','websiteUrl':'','phone':'','sourceUrl':'https://example.com/source','verifiedAt':'2026-10-29','status':'published','featured':False}
  status,z=self.request('/api/import',{'items':[record]},headers=h);self.assertEqual(status,200,str(z))
  status,q=self.request('/api/merchant/qr?shopId=verified-test',headers=h);self.assertEqual(status,200)
  token=q['token']
  status,_=self.request('/api/checkin',{'shopId':'verified-test','qrToken':token,'latitude':37.45,'longitude':127.112,'accuracy':6});self.assertEqual(status,403)
  status,_=self.request('/api/checkin',{'shopId':'verified-test','qrToken':token+'0','latitude':37.494,'longitude':127.112,'accuracy':6});self.assertEqual(status,403)
  status,_=self.request('/api/checkin',{'shopId':'verified-test','qrToken':token,'latitude':37.494,'longitude':127.112,'accuracy':100});self.assertEqual(status,400)
  status,r=self.request('/api/checkin',{'shopId':'verified-test','qrToken':token,'latitude':37.494,'longitude':127.112,'accuracy':6});self.assertEqual(status,200,str(r));self.assertTrue(r['newVisit'])
  status,r2=self.request('/api/checkin',{'shopId':'verified-test','qrToken':token,'latitude':37.494,'longitude':127.112,'accuracy':6});self.assertEqual(status,200);self.assertFalse(r2['newVisit'])
 def test_12_photo_upload_and_partner_links(self):
  try:
   from PIL import Image
  except ImportError:
   self.skipTest('Optional Pillow not installed')
  h={'X-Garak-Admin-Token':server.ADMIN_TOKEN}
  status,x=self.request('/api/merchant/profile',{'shopId':'demo-meat','blogUrl':'https://example.com/merchant-blog','deliveryUrl':'https://example.com/official-orders','menu':[{'name':'양념갈비','price':23000}]},headers=h)
  self.assertEqual(status,200,str(x))
  _,a=self.request('/api/experience');r=next(x for x in a['shops'] if x['id']=='demo-meat')
  self.assertEqual(r['blogUrl'],'https://example.com/merchant-blog');self.assertEqual(r['delivery_url'],'https://example.com/official-orders')
  buf=io.BytesIO();Image.new('RGB',(80,90),(180,70,30)).save(buf,'JPEG')
  status,up=self.request('/api/merchant/upload-photo',{'shopId':'demo-meat','kind':'menu','image':base64.b64encode(buf.getvalue()).decode()},headers=h)
  self.assertEqual(status,200,str(up));path=ROOT/up['path'].lstrip('/');self.assertTrue(path.exists());path.unlink()
  status,_=self.request('/api/merchant/profile',{'shopId':'demo-meat','blogUrl':'javascript:alert(1)','deliveryUrl':'','menu':[]},headers=h);self.assertEqual(status,400)
if __name__=='__main__':unittest.main(verbosity=2)
