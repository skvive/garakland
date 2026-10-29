import unittest, os
from types import SimpleNamespace
from unittest.mock import patch
import bridge_v7

class FakeHandler:
    def __init__(self,token=''):self.headers={'X-Garak-Admin-Token':token};self.result=None
    def send_json(self,status,value):self.result=(status,value);return self.result

class V7BridgeTests(unittest.TestCase):
    def test_01_only_demo_or_review(self):self.assertIn(bridge_v7.MODE,('demo','review'))
    def test_02_public_base_missing(self):
        with patch.dict(os.environ,{'GARAK_PUBLIC_BASE_URL':'http://localhost:8769'}):self.assertEqual(bridge_v7.clean_base(),'')
    def test_03_bad_host_suppressed(self):
        with patch.dict(os.environ,{'GARAK_PUBLIC_BASE_URL':'https://127.0.0.1'}):self.assertEqual(bridge_v7.clean_base(),'')
    def test_04_https_public_host(self):
        with patch.dict(os.environ,{'GARAK_PUBLIC_BASE_URL':'https://garak.example.org'}):self.assertEqual(bridge_v7.clean_base(),'https://garak.example.org')
    def test_05_demo_disclaimer(self):
        x={'id':'T1','shop_id':'demo-fruit','item':'제철과일','original_price':15000,'offer_price':12000,'shop_name':'[시연] 과일','building':'청과','floor':'1F','room':'A-1','directions_url':'https://www.google.com/maps/dir/?api=1','verified_location':False}
        y=bridge_v7.share_text(x);self.assertIn('시연용/실제 사용 불가',y['text']);self.assertFalse(y['automaticSendEnabled']);self.assertTrue(y['requiresPublicUrl'])
    def test_06_real_no_unverified_claims(self):
        x={'id':'T2','shop_id':'abc','item':'제철과일','original_price':15000,'offer_price':12000,'shop_name':'상인','building':'청과','floor':'1F','room':'A-1','directions_url':'https://maps.example','verified_location':False}
        y=bridge_v7.share_text(x,'https://garak.example.org');self.assertNotIn('검증된 GPS',y['text']);self.assertIn('(광고)',y['text']);self.assertTrue(y['landingUrl'].startswith('https://'))
    def test_07_anonymous_readiness_forbidden(self):
        h=FakeHandler();r=bridge_v7.get(h,'/api/v7/readiness',{});self.assertEqual(r[0],403)
    def test_08_reject_bad_id(self):
        h=FakeHandler();r=bridge_v7.get(h,'/api/v7/share-kit',{'offerId':['../../bad']});self.assertEqual(r[0],400)
    def test_09_meta_safe(self):
        h=FakeHandler();r=bridge_v7.get(h,'/api/v7/meta',{});self.assertEqual(r[0],200);self.assertFalse(r[1]['realPaymentsEnabled'])
if __name__=='__main__':unittest.main()
