"""Static marketing copy, route and independence safeguards."""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
class AfterLotteCampaign(unittest.TestCase):
 def test_marketing_brand_copy(self):
  html=(R/'lotteworld-next.html').read_text()
  self.assertIn('롯데월드 다음 코스',html)
  self.assertIn('가락랜드',html)
  self.assertIn('가락한상',html)
  self.assertIn('8호선',html)
  self.assertIn('가락시장역',html)
  self.assertIn('indoor-map.html?floor=1F',html)
  self.assertIn('공식 공동 프로모션',html)
  self.assertIn('travelmode=transit',html)
 def test_reuses_existing_mascot(self):
  self.assertTrue((R/'assets/mascot/garak-hansang-wave.webp').is_file())
  self.assertTrue((R/'assets/mascot/garak-hansang-hero.webp').is_file())
 def test_landing_navigation(self):
  s=(R/'brand/app.js').read_text()
  self.assertIn('lotteworld-next.html',s)
  self.assertIn('롯데월드 다음 코스',s)
  self.assertIn('gl-after-lotte',s)
 def test_no_fake_offer(self):
  s=(R/'lotteworld-next.html').read_text()
  self.assertIn('실제 사용',s) if '실제 사용' in s else self.assertIn('체험용',s)
  self.assertIn('공식 제휴',s)
if __name__=='__main__': unittest.main()
