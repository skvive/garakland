"""Integration tests for V8 hub module/API, safe controls, metrics and scheduling."""
import unittest,os,sys,tempfile,subprocess,time,requests,datetime,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:19189'
TOKEN='hub-beta-test-admin-token-do-not-use-prod'
class HubV8Test(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory()
  env={**os.environ,'GARAK_DB_PATH':str(Path(cls.temp.name)/'hub-test.sqlite'),'GARAK_ADMIN_TOKEN':TOKEN,'PORT':'19189','GARAK_HOST':'127.0.0.1','GARAK_ENABLE_DEMO':'1','GARAK_V7_MODE':'demo'}
  cls.proc=subprocess.Popen([sys.executable,str(ROOT/'server.py')],cwd=str(ROOT),env=env,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  for _ in range(100):
   try:
    if requests.get(BASE+'/api/health',timeout=.5).ok:break
   except requests.RequestException:time.sleep(.1)
  else:raise RuntimeError('Hub server not running')
 @classmethod
 def tearDownClass(cls):
  cls.proc.terminate();cls.proc.wait(timeout=5);cls.temp.cleanup()
 def req(self,method,path,payload=None,auth=True):
  headers={'X-Garak-Client':'1'}
  if auth:headers['X-Garak-Admin-Token']=TOKEN
  return requests.request(method,BASE+path,headers=headers,json=payload,timeout=10)
 def test_a_01_auth_get(self):self.assertEqual(self.req('GET','/api/v8/dashboard',auth=False).status_code,403)
 def test_a_02_auth_post(self):self.assertEqual(self.req('POST','/api/v8/module/config',{'id':'map','enabled':False},False).status_code,403)
 def test_a_03_dashboard_has_12(self):
  d=self.req('GET','/api/v8/dashboard').json();self.assertEqual(len(d['modules']),12);self.assertFalse(d['readiness']['releaseApproved'])
 def test_a_04_initial_stats(self):
  m=self.req('GET','/api/v8/dashboard').json()['metrics'];self.assertGreaterEqual(m['stores'],4);self.assertGreaterEqual(m['demoStores'],4);self.assertEqual(m['verifiedLocations'],0)
 def test_a_05_analytics_periods(self):
  for d in (7,14,30,90):
   a=self.req('GET',f'/api/v8/analytics?days={d}');self.assertEqual(a.status_code,200);self.assertEqual(len(a.json()['daily']),d)
 def test_a_06_analytics_bad_period(self):self.assertEqual(self.req('GET','/api/v8/analytics?days=999').status_code,400)
 def test_a_07_modules_no_unknown(self):self.assertEqual(self.req('POST','/api/v8/module/config',{'id':'hack','enabled':False}).status_code,400)
 def test_a_08_modules_bool_type(self):self.assertEqual(self.req('POST','/api/v8/module/config',{'id':'map','enabled':'false'}).status_code,400)
 def test_a_09_dependency_guard(self):
  r=self.req('POST','/api/v8/module/config',{'id':'stores','enabled':False});self.assertEqual(r.status_code,409);self.assertIn('dependents',r.json())
 def test_a_10_toggle_and_api_gate(self):
  try:
   r=self.req('POST','/api/v8/module/config',{'id':'ar','enabled':False,'note':'베타 모듈 중지 검증'});self.assertEqual(r.status_code,200,r.text)
   self.assertEqual(self.req('GET','/api/experience').status_code,503)
   self.assertEqual(self.req('GET','/api/v8/modules').status_code,200)
  finally:self.req('POST','/api/v8/module/config',{'id':'ar','enabled':True})
  self.assertEqual(self.req('GET','/api/experience').status_code,200)
 def test_a_11_note_limit(self):self.assertEqual(self.req('POST','/api/v8/module/config',{'id':'ar','enabled':True,'note':'A'*300}).status_code,400)
 def test_a_12_jobs_list(self):self.assertEqual(self.req('GET','/api/v8/jobs').status_code,200)
 def test_a_13_jobs_bad_kind(self):self.assertEqual(self.req('POST','/api/v8/jobs/create',{'kind':'send_sms','label':'실발송','dueAt':'2026-10-29T12:00:00+09:00'}).status_code,400)
 def test_a_14_jobs_bad_due(self):self.assertEqual(self.req('POST','/api/v8/jobs/create',{'kind':'metrics_snapshot','label':'no zone','dueAt':'2026-11-01T12:00:00'}).status_code,400)
 def test_a_15_job_create_and_once(self):
  r=self.req('POST','/api/v8/jobs/create',{'kind':'metrics_snapshot','label':'일회 통계', 'dueAt':(datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))+datetime.timedelta(minutes=5)).isoformat(),'cadence':'once'});self.assertEqual(r.status_code,201,r.text)
  id_=r.json()['id'];self.assertFalse(r.json()['autoExecution'])
  job=next(x for x in self.req('GET','/api/v8/jobs').json()['items'] if x['id']==id_);self.assertEqual(job['run_count'],0)
  run=self.req('POST','/api/v8/jobs/run',{'id':id_});self.assertEqual(run.status_code,200,run.text);self.assertEqual(run.json()['status'],'completed')
  self.assertEqual(self.req('POST','/api/v8/jobs/run',{'id':id_}).status_code,409)
 def test_a_16_coupon_audit_job(self):
  id_=self.req('POST','/api/v8/jobs/create',{'kind':'coupon_audit','label':'쿠폰', 'dueAt':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()}).json()['id']
  res=self.req('POST','/api/v8/jobs/run',{'id':id_}).json();self.assertEqual(res['result']['duplicates'],0)
 def test_a_17_preview_no_messaging(self):
  id_=self.req('POST','/api/v8/jobs/create',{'kind':'marketing_preview','label':'홍보 예행연습', 'dueAt':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()}).json()['id']
  r=self.req('POST','/api/v8/jobs/run',{'id':id_}).json();self.assertFalse(r['result']['actualSendEnabled']);self.assertEqual(r['result']['sent'],0)
 def test_a_18_recurring(self):
  id_=self.req('POST','/api/v8/jobs/create',{'kind':'readiness_check','label':'주간 점검','cadence':'weekly','dueAt':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()}).json()['id']
  a=self.req('POST','/api/v8/jobs/run',{'id':id_});self.assertEqual(a.status_code,200);self.assertEqual(a.json()['status'],'scheduled')
  job=next(x for x in self.req('GET','/api/v8/jobs').json()['items'] if x['id']==id_);self.assertEqual(job['run_count'],1)
 def test_a_19_cancel(self):
  id_=self.req('POST','/api/v8/jobs/create',{'kind':'metrics_snapshot','label':'취소 테스트','dueAt':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()}).json()['id']
  self.assertEqual(self.req('POST','/api/v8/jobs/cancel',{'id':id_}).status_code,200)
  self.assertEqual(self.req('POST','/api/v8/jobs/run',{'id':id_}).status_code,409)
 def test_a_20_readiness(self):
  x=self.req('GET','/api/v8/readiness').json();self.assertFalse(x['releaseApproved']);self.assertEqual(len(x['checklist']),6)
 def test_a_21_audit(self):
  x=self.req('GET','/api/v8/audit').json()['items'];self.assertTrue(any(e['action']=='module.disabled' for e in x))
 def test_a_22_snapshots(self):self.assertGreaterEqual(len(self.req('GET','/api/v8/snapshots').json()['items']),1)
 def test_a_23_hub_page(self):
  x=requests.get(BASE+'/hub.html',timeout=3);self.assertEqual(x.status_code,200);self.assertIn('모듈형 운영 허브',x.text)
 def test_a_24_hub_js(self):self.assertEqual(requests.get(BASE+'/hub/app.js',timeout=3).status_code,200)
 def test_a_25_no_secret(self):
  for path in ('/hub/core.py','/data/garakland.sqlite','/.env.example'):
   self.assertNotEqual(requests.get(BASE+path,timeout=3).status_code,200,path)
 def test_z_26_cross_module_metrics(self):
  before=self.req('GET','/api/v8/dashboard').json()['metrics']
  buyer=requests.Session()
  hdr={'X-Garak-Client':'1'}
  claim=buyer.post(BASE+'/api/coupons/claim',json={'campaignId':'c-sea'},headers=hdr,timeout=5)
  self.assertEqual(claim.status_code,200,claim.text)
  stamp=buyer.post(BASE+'/api/demo/checkin',json={'shopId':'demo-sea'},headers=hdr,timeout=5)
  self.assertEqual(stamp.status_code,200,stamp.text)
  order=buyer.post(BASE+'/api/orders',json={'shopId':'demo-sea','menuName':'참돔 모둠','quantity':1,'mode':'pickup'},headers=hdr,timeout=5)
  self.assertEqual(order.status_code,200,order.text)
  after=self.req('GET','/api/v8/dashboard').json()['metrics']
  self.assertEqual(after['legacyCoupons'],before['legacyCoupons']+1)
  self.assertEqual(after['visits'],before['visits']+1)
  self.assertEqual(after['demoOrders'],before['demoOrders']+1)
 def test_z_27_product_api_gate(self):
  try:
   self.assertEqual(self.req('POST','/api/v8/module/config',{'id':'products','enabled':False}).status_code,200)
   self.assertEqual(self.req('GET','/api/v6/products').status_code,503)
   self.assertEqual(self.req('GET','/api/v6/dashboard').status_code,200)
  finally:self.req('POST','/api/v8/module/config',{'id':'products','enabled':True})
 def test_z_28_marketing_api_gate(self):
  try:
   self.assertEqual(self.req('POST','/api/v8/module/config',{'id':'marketing','enabled':False}).status_code,200)
   self.assertEqual(self.req('POST','/api/v5/consent',{'email':'opt@example.com'}).status_code,503)
  finally:self.req('POST','/api/v8/module/config',{'id':'marketing','enabled':True})
 def test_z_29_create_custom_linked_module(self):
  data={'id':'local-guide','name':'시연 콘텐츠 연결','description':'기존 브랜드 페이지의 운영 허브 바로가기','url':'/market-guide.html'}
  r=self.req('POST','/api/v8/modules/register',data);self.assertEqual(r.status_code,201,r.text)
  mods=self.req('GET','/api/v8/modules').json()['items']
  found=next(x for x in mods if x['id']=='local-guide');self.assertTrue(found['custom']);self.assertEqual(found['url'],'/market-guide.html')
  self.assertEqual(self.req('POST','/api/v8/modules/register',data).status_code,409)
 def test_z_30_register_missing_file_and_bad_url(self):
  a={'id':'unsafe-module','name':'테스트','description':'입력 데이터 검증','url':'https://evil.example/site'}
  self.assertEqual(self.req('POST','/api/v8/modules/register',a).status_code,400)
  a['url']='/unavailable.html';self.assertEqual(self.req('POST','/api/v8/modules/register',a).status_code,400)
 def test_z_31_custom_toggle_persists(self):
  got=self.req('POST','/api/v8/module/config',{'id':'local-guide','enabled':False});self.assertEqual(got.status_code,200,got.text)
  self.assertFalse(next(m for m in self.req('GET','/api/v8/dashboard').json()['modules'] if m['id']=='local-guide')['enabled'])
  self.assertEqual(self.req('POST','/api/v8/module/config',{'id':'local-guide','enabled':True}).status_code,200)
if __name__=='__main__':unittest.main(verbosity=2)
