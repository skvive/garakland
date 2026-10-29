"""v6 ERP operational API integration and security tests using isolated SQLite."""
import unittest, os, sys, tempfile, subprocess, time, requests, csv,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PORT=18771
BASE=f'http://127.0.0.1:{PORT}'
ADMIN='v6-test-admin-token-keep-private'
class ERPIntegration(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory()
  env={**os.environ,'GARAK_DB_PATH':str(Path(cls.temp.name)/'erp.sqlite'),'GARAK_ADMIN_TOKEN':ADMIN,'PORT':str(PORT),'GARAK_HOST':'127.0.0.1'}
  cls.proc=subprocess.Popen([sys.executable,str(ROOT/'server.py')],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  for i in range(100):
   try:
    if requests.get(BASE+'/api/health',timeout=.5).ok:break
   except requests.RequestException:time.sleep(.1)
  else:raise RuntimeError('Server unavailable')
 @classmethod
 def tearDownClass(cls):
  cls.proc.terminate();cls.proc.wait(timeout=5);cls.temp.cleanup()
 def call(self,path,data=None,auth=True):
  h={'X-Garak-Client':'1'}
  if auth:h['X-Garak-Admin-Token']=ADMIN
  if data is None:return requests.get(BASE+path,headers=h,timeout=5)
  return requests.post(BASE+path,json=data,headers=h,timeout=5)
 def sample(self,rows=None):
  f=io.StringIO(newline='');w=csv.writer(f)
  w.writerow(['product_code','shop_id','product_name','unit','regular_price','special_price','stock','starts_at','ends_at'])
  if rows is None:rows=[['P6-FRUIT-1','demo-fruit','[시연] 단감','1상자',13000,11000,40,'2026-10-29T08:00:00+09:00','2026-11-25T19:00:00+09:00']]
  w.writerows(rows);return f.getvalue()
 def test_01_auth_get_required(self):self.assertEqual(self.call('/api/v6/dashboard',auth=False).status_code,403)
 def test_02_auth_post_required(self):self.assertEqual(self.call('/api/v6/task/add',{'title':'테스트','detail':'테스트'},auth=False).status_code,403)
 def test_03_dashboard(self):
  d=self.call('/api/v6/dashboard').json();self.assertGreaterEqual(len(d['shops']),4);self.assertEqual(d['officialApproval'],False);self.assertEqual(len(d['documents']),8)
 def test_04_board_add(self):
  r=self.call('/api/v6/task/add',{'title':'상인 현장사진 최종 확인','detail':'사전 합의 매장 이미지 실사 검증'});self.assertTrue(r.json()['ok']);self.__class__.task=r.json()['id']
 def test_05_board_move(self):
  task=self.__class__.task;r=self.call('/api/v6/task/move',{'stage':'검토 중','orderedIds':[task]});self.assertEqual(r.status_code,200)
  got=[x for x in self.call('/api/v6/dashboard').json()['tasks'] if x['id']==task][0];self.assertEqual(got['stage'],'검토 중')
 def test_06_bad_task_stage(self):self.assertEqual(self.call('/api/v6/task/move',{'stage':'실계약 완료','orderedIds':[self.__class__.task]}).status_code,400)
 def test_07_docs_needs_reference(self):
  r=self.call('/api/v6/documents/review',{'shopId':'demo-fruit','code':'merchant_agreement','status':'내부 확인','evidenceRef':''});self.assertEqual(r.status_code,400)
 def test_08_docs_record(self):
  r=self.call('/api/v6/documents/review',{'shopId':'demo-fruit','code':'merchant_agreement','status':'검토 중','evidenceRef':'LOCAL-DEMO-001'});self.assertEqual(r.status_code,200)
  items=self.call('/api/v6/documents?shopId=demo-fruit').json()['items'];self.assertEqual(items[0]['evidence_ref'],'LOCAL-DEMO-001')
 def test_09_docs_internal_review(self):
  r=self.call('/api/v6/documents/review',{'shopId':'demo-fruit','code':'merchant_agreement','status':'내부 확인','evidenceRef':'TEST-ACK-001'});self.assertEqual(r.status_code,200)
  self.assertTrue(self.call('/api/v6/dashboard').json()['completeDocuments']>=1)
 def test_10_csv_bom_validate(self):
  r=self.call('/api/v6/products/validate',{'csv':'\ufeff'+self.sample()});self.assertEqual(r.status_code,200,r.text);self.assertEqual(r.json()['valid'],1)
 def test_11_csv_import(self):
  r=self.call('/api/v6/products/import',{'csv':self.sample()});self.assertEqual(r.status_code,200,r.text);self.assertFalse(r.json()['publiclyListed']);self.assertEqual(self.call('/api/v6/products').json()['items'][0]['published'],0)
 def test_12_bad_price_no_partial_import(self):
  bad=self.sample([['P6-GOOD-2','demo-fruit','[시연] 사과','1상자',12000,10000,10,'2026-10-29','2026-10-30'],['P6-BAD-2','demo-fruit','[시연] 오류','1상자',1000,5000,2,'2026-10-29','2026-10-30']]);self.assertEqual(self.call('/api/v6/products/import',{'csv':bad}).status_code,422);self.assertFalse(any(x['product_code']=='P6-GOOD-2' for x in self.call('/api/v6/products').json()['items']))
 def test_13_bad_shop(self):
  bad=self.sample([['P6-FAIL-3','unknown','[시연] 테스트','1개',3000,2000,2,'2026-10-29','2026-11-01']]);self.assertEqual(self.call('/api/v6/products/validate',{'csv':bad}).status_code,422)
 def test_14_duplicate_code(self):
  item=['DUP-3','demo-fruit','[시연] 배','1개',4000,3000,2,'2026-10-29','2026-10-30'];self.assertEqual(self.call('/api/v6/products/validate',{'csv':self.sample([item,item])}).status_code,422)
 def test_15_csv_excess_rows(self):
  item=['P','demo-fruit','[시연] 배','1개',4000,3000,2,'2026-10-29','2026-10-30'];lots=[['P6-'+str(i),*item[1:]] for i in range(351)];self.assertEqual(self.call('/api/v6/products/validate',{'csv':self.sample(lots)}).status_code,400)
 def test_16_settlement_no_real(self):
  j=self.call('/api/v6/settlement').json();self.assertEqual(j['actualRevenue'],0);self.assertEqual(j['currency'],'DEMO_CREDIT')
 def test_17_audit_log(self):self.assertTrue(len(self.call('/api/v6/audit').json()['items'])>=1)
 def test_18_static_file_guard(self):
  self.assertNotEqual(requests.get(BASE+'/ops/core.py',timeout=3).status_code,200)
  self.assertNotEqual(requests.get(BASE+'/data/garakland.sqlite',timeout=3).status_code,200)
 def test_19_ui_available(self):
  r=requests.get(BASE+'/ops.html',timeout=3);self.assertEqual(r.status_code,200);self.assertIn('출시 업무 관리 보드',r.text)
 def test_20_docx_file_available(self):
  r=requests.get(BASE+'/documents/templates/01_%EC%83%81%EC%9D%B8%EC%B0%B8%EC%97%AC_%EB%94%94%EC%A7%80%ED%84%B8%ED%99%8D%EB%B3%B4%ED%98%91%EC%95%BD%EC%84%9C_%EA%B2%80%ED%86%A0%EC%95%88.docx',timeout=4);self.assertEqual(r.status_code,200)
if __name__=='__main__':unittest.main(verbosity=2)
