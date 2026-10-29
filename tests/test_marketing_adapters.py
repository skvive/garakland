import unittest,os,re,hmac,hashlib
from market.providers import solapi_auth,sms_payload,kakao_brand_payload,send_solapi
class ProviderShapeTests(unittest.TestCase):
 def test_hmac(self):
  stamp='2026-10-29T00:00:00Z';salt='a'*32;auth=solapi_auth('key','secret',stamp,salt)
  digest=hmac.new(b'secret',(stamp+salt).encode(),hashlib.sha256).hexdigest()
  self.assertIn('signature='+digest,auth)
 def test_sms(self):
  msg=sms_payload('01012345678','0212345678','제철 과일 쿠폰','https://example.org/unsubscribe')
  self.assertIn('(광고)',msg['messages'][0]['text']);self.assertIn('수신거부',msg['messages'][0]['text'])
  self.assertEqual(msg['messages'][0]['to'],'01012345678')
 def test_sms_fail(self):
  with self.assertRaises(ValueError):sms_payload('abc','0212345678','메시지','https://example.org')
 def test_kakao_bms(self):
  p=kakao_brand_payload('01012345678','pf-demo','세일 안내','https://example.org/unsubscribe')
  self.assertEqual(p['messages'][0]['type'],'BMS_TEXT')
  self.assertEqual(p['messages'][0]['kakaoOptions']['bms']['targeting'],'M')
 def test_kakao_reject_invalid_target(self):
  with self.assertRaises(ValueError):kakao_brand_payload('01012345678','pf-demo','안내','https://example.org',target='N')
 def test_live_disabled(self):
  old=os.environ.get('GARAK_V5_APPROVED_LIVE_SEND')
  os.environ.pop('GARAK_V5_APPROVED_LIVE_SEND',None)
  try:
   with self.assertRaises(RuntimeError):send_solapi({'messages':[]},api_key='key',api_secret='secret')
  finally:
   if old:os.environ['GARAK_V5_APPROVED_LIVE_SEND']=old
if __name__=='__main__':unittest.main()
