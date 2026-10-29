"""Full integration smoke test: starts actual HTTP server against temporary SQLite."""
import os,sys,time,tempfile,subprocess,unittest,datetime,concurrent.futures
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import requests

ROOT=Path(__file__).resolve().parents[1]
ADMIN='integration-admin-token-12345'

class GrowthV5Integration(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory()
  cls.port=18739
  cls.url=f'http://127.0.0.1:{cls.port}'
  env={**os.environ,'PORT':str(cls.port),'GARAK_DB_PATH':cls.temp.name+'/integration.sqlite',
       'GARAK_ADMIN_TOKEN':ADMIN,'GARAK_HOST':'127.0.0.1','GARAK_V5_DEMO':'1','GARAK_ENABLE_DEMO':'1'}
  cls.process=subprocess.Popen([sys.executable,'server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  for _ in range(100):
   try:
    x=requests.get(cls.url+'/api/v5/public',timeout=.5)
    if x.ok:break
   except requests.RequestException:time.sleep(.1)
  else:raise RuntimeError('v5 server did not start')
  cls.buyer=requests.Session()
  cls.operator=requests.Session()
  cls.first=requests.Session()
  cls.offer_id='V5-DEMO-FRUIT'
  cls.admin_header={'X-Garak-Admin-Token':ADMIN}
  key=cls.operator.post(cls.url+'/api/admin/merchant-key',json={'shopId':'demo-fruit'},headers={**cls.admin_header,'X-Garak-Client':'1'},timeout=4)
  assert key.ok,key.text
  cls.merchant_key=key.json()['merchantKey']
  cls.merchant_header={'X-Garak-Merchant-Key':cls.merchant_key}
 @classmethod
 def tearDownClass(cls):
  cls.process.terminate()
  try:cls.process.wait(3)
  except subprocess.TimeoutExpired:cls.process.kill()
  cls.temp.cleanup()
 def get(self,path,client=None,headers=None):
  return (client or self.buyer).get(self.url+path,headers=headers or {},timeout=5)
 def post(self,path,data,client=None,headers=None):
  return (client or self.buyer).post(self.url+path,json=data,headers={'X-Garak-Client':'1',**(headers or {})},timeout=5)
 def test_01_public_offers(self):
  r=self.get('/api/v5/public');self.assertEqual(r.status_code,200,r.text)
  data=r.json();self.assertGreaterEqual(len(data['offers']),4)
  self.assertFalse(data['moneyEnabled']);self.assertEqual(data['marketingMode'],'simulation')
  self.assertTrue(all('google.com/maps/dir/' in o['directions_url'] for o in data['offers']))
  url=data['offers'][0]['directions_url'];q=parse_qs(urlparse(url).query)
  self.assertEqual(q['api'],['1']);self.assertEqual(q['travelmode'],['walking'])
 def test_02_coupon_and_repeat(self):
  r=self.post('/api/v5/offers/claim',{'offerId':self.offer_id});self.assertEqual(r.status_code,200,r.text)
  self.coupon=r.json()['code'];self.__class__.coupon=self.coupon
  self.assertEqual(self.post('/api/v5/offers/claim',{'offerId':self.offer_id}).status_code,409)
  self.assertEqual(len(self.get('/api/v5/me').json()['tickets']),1)
 def test_03_coupon_wrong_store_no_auth(self):
  self.assertEqual(self.post('/api/v5/merchant/offer/redeem',{'shopId':'demo-fruit','code':self.coupon}).status_code,403)
  r=self.post('/api/v5/merchant/offer/redeem',{'shopId':'demo-sea','code':self.coupon},headers=self.merchant_header)
  self.assertEqual(r.status_code,403)
 def test_04_coupon_redeem_once(self):
  data={'shopId':'demo-fruit','code':self.coupon}
  ok=self.post('/api/v5/merchant/offer/redeem',data,headers=self.merchant_header)
  self.assertEqual(ok.status_code,200,ok.text)
  self.assertEqual(self.post('/api/v5/merchant/offer/redeem',data,headers=self.merchant_header).status_code,409)
 def test_05_merchant_create_invalid_prices(self):
  payload={'shopId':'demo-fruit','item':'딸기 선물팩','description':'테스트','originalPrice':11000,'offerPrice':12000,'limitCount':2,
    'startsAt':(datetime.datetime.now()+datetime.timedelta(days=-1)).isoformat(timespec='seconds'),
    'endsAt':(datetime.datetime.now()+datetime.timedelta(days=3)).isoformat(timespec='seconds')}
  self.assertEqual(self.post('/api/v5/merchant/offer',payload,headers=self.merchant_header).status_code,400)
  payload['offerPrice']=9000
  result=self.post('/api/v5/merchant/offer',payload,headers=self.merchant_header)
  self.assertEqual(result.status_code,200,result.text)
  self.__class__.new_offer=result.json()['offerId']
 def test_06_gift_demo_and_balance(self):
  res=self.post('/api/v5/gift/demo-purchase',{'face':50000});self.assertEqual(res.status_code,200,res.text)
  obj=res.json();self.assertEqual(obj['balance'],50000)
  self.__class__.card=obj['cardId'];self.__class__.pin=obj['redeemPin']
  self.assertEqual(obj['simulatedPrice'],47500)
  self.assertNotIn('pin_hash',self.get('/api/v5/me').text)
  self.assertEqual(self.post('/api/v5/gift/demo-purchase',{'face':35000}).status_code,400)
 def test_07_gift_wrong_pin(self):
  payload={'shopId':'demo-fruit','cardId':self.card,'pin':'0000000000000000','amount':3000,'requestId':'ORDER-A'}
  r=self.post('/api/v5/merchant/gift/redeem',payload,headers=self.merchant_header)
  self.assertEqual(r.status_code,403,r.text)
 def test_08_gift_redeem_idempotent(self):
  payload={'shopId':'demo-fruit','cardId':self.card,'pin':self.pin,'amount':13000,'requestId':'ORDER-B'}
  r=self.post('/api/v5/merchant/gift/redeem',payload,headers=self.merchant_header)
  self.assertEqual(r.status_code,200,r.text);self.assertEqual(r.json()['balance'],37000)
  same=self.post('/api/v5/merchant/gift/redeem',payload,headers=self.merchant_header)
  self.assertTrue(same.json()['idempotent']);self.assertEqual(same.json()['balance'],37000)
  payload['amount']=14000
  self.assertEqual(self.post('/api/v5/merchant/gift/redeem',payload,headers=self.merchant_header).status_code,409)
 def test_09_gift_insufficient_and_refund(self):
  payload={'shopId':'demo-fruit','cardId':self.card,'pin':self.pin,'amount':38000,'requestId':'ORDER-C'}
  self.assertEqual(self.post('/api/v5/merchant/gift/redeem',payload,headers=self.merchant_header).status_code,409)
  ledger=self.get('/api/v5/me').json()['ledger']
  target=next(r for r in ledger if r['kind']=='REDEEM')
  r=self.post('/api/v5/admin/gift/refund',{'ledgerId':target['id']},headers=self.admin_header)
  self.assertEqual(r.status_code,200,r.text);self.assertEqual(r.json()['balance'],50000)
  self.assertEqual(self.post('/api/v5/admin/gift/refund',{'ledgerId':target['id']},headers=self.admin_header).status_code,409)
 def test_10_consent_separate(self):
  payload={'email':'testmarketuser@example.org','phone':'01098765432','emailOpt':True,'smsOpt':True,'kakaoOpt':False}
  self.assertEqual(self.post('/api/v5/consent',payload).status_code,200)
  own=self.get('/api/v5/me').json()['contact'];self.assertEqual(own['email_opt'],1);self.assertEqual(own['sms_opt'],1)
  self.assertEqual(own['kakao_opt'],0)
  self.assertNotIn('testmarketuser@example.org',self.get('/api/v5/admin',headers=self.admin_header).text)
 def test_11_schedule_and_dispatch_simulation(self):
  t=(datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))-datetime.timedelta(minutes=1)).isoformat(timespec='seconds')
  data={'shopId':'demo-fruit','channel':'email','title':'제철 특가 시연','message':'딸기 할인 쿠폰 받으세요','sendAt':t}
  r=self.post('/api/v5/merchant/broadcast',data,headers=self.merchant_header)
  self.assertEqual(r.status_code,200,r.text)
  sent=self.post('/api/v5/admin/dispatch',{'forceDemo':True},headers=self.admin_header)
  self.assertEqual(sent.status_code,200,sent.text);self.assertGreaterEqual(sent.json()['processed'],1)
  self.assertEqual(sent.json()['liveSent'],0)
 def test_12_consent_withdraw(self):
  payload={'email':'testmarketuser@example.org','phone':'01098765432','emailOpt':False,'smsOpt':False,'kakaoOpt':False}
  self.assertEqual(self.post('/api/v5/consent',payload).status_code,200)
  own=self.get('/api/v5/me').json()['contact'];self.assertEqual(own['sms_opt'],0)
 def test_13_admin_approve_permissions(self):
  self.assertEqual(self.post('/api/v5/admin/member',{'shopId':'demo-fruit','approved':True}).status_code,403)
  r=self.post('/api/v5/admin/member',{'shopId':'demo-fruit','approved':True,'proofNote':'시연 계약'},headers=self.admin_header)
  self.assertEqual(r.status_code,200,r.text)
 def test_14_scheduled_offer_visibility(self):
  t=datetime.datetime.now()+datetime.timedelta(days=1)
  payload={'shopId':'demo-fruit','item':'내일 행사','description':'내일부터 노출','originalPrice':15000,'offerPrice':14000,'limitCount':5,
    'startsAt':t.isoformat(timespec='seconds'),'endsAt':(t+datetime.timedelta(days=2)).isoformat(timespec='seconds')}
  r=self.post('/api/v5/merchant/offer',payload,headers=self.merchant_header)
  self.assertEqual(r.status_code,200,r.text)
  offer=r.json()['offerId'];ids=[x['id'] for x in self.get('/api/v5/public').json()['offers']]
  self.assertNotIn(offer,ids)
  self.assertEqual(self.post('/api/v5/offers/claim',{'offerId':offer}).status_code,409)
 def test_15_merchant_dashboard_auth(self):
  self.assertEqual(self.get('/api/v5/merchant?shopId=demo-fruit').status_code,403)
  r=self.get('/api/v5/merchant?shopId=demo-fruit',headers=self.merchant_header)
  self.assertEqual(r.status_code,200,r.text)
  self.assertGreaterEqual(r.json()['redeemedTickets'],1)
 def test_17_signed_unsubscribe(self):
  self.assertEqual(self.post('/api/v5/consent',{'email':'testmarketuser@example.org','emailOpt':True}).status_code,200)
  token=self.get('/api/v5/my-unsubscribe-link').json()['token']
  r=self.post('/api/v5/optout',{'token':token,'channel':'email'},client=self.operator)
  self.assertEqual(r.status_code,200,r.text)
  self.assertEqual(self.get('/api/v5/me').json()['contact']['email_opt'],0)
  self.assertEqual(self.post('/api/v5/optout',{'token':token[:-1]+'0','channel':'email'}).status_code,403)
 def test_18_live_marketing_fail_closed(self):
  r=self.post('/api/v5/admin/dispatch-live',{'liveApproved':True,'broadcastId':'no-such','limit':5},headers=self.admin_header)
  self.assertEqual(r.status_code,403)
 def test_19_unsubscribe_screen(self):
  self.assertEqual(self.get('/unsubscribe.html').status_code,200)
 def test_16_public_static_security(self):
  self.assertEqual(self.get('/market.html').status_code,200)
  self.assertEqual(self.get('/market/theme.css').status_code,200)
  self.assertEqual(self.get('/market/ui.js').status_code,200)
  self.assertEqual(self.get('/market/core.py').status_code,404)
  self.assertEqual(self.get('/data/garakland.sqlite').status_code,404)

if __name__=='__main__':unittest.main(verbosity=2)
