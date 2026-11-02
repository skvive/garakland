"""Garakland campaign delivery gates — independent tourism, no pretend affiliation."""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
class AfterLotteCampaign(unittest.TestCase):
 def test_korean_brand_and_conversion(self):
  s=(R/'lotteworld-next.html').read_text()
  for phrase in ['롯데월드 다음 코스','가락랜드','가락한상','8호선','가락시장역','대중교통 길찾기','실내지도','3D 지도','공식 제휴','AI 생성 관광 콘셉트 이미지']:
   self.assertIn(phrase,s,phrase)
  self.assertGreaterEqual(s.count('indoor-map.html?floor='),5)
  self.assertIn('travelmode=transit',s)
  self.assertIn('rel="noopener noreferrer"',s)
 def test_licensed_brand_asset_and_generated_art(self):
  for p in ['assets/mascot/garak-hansang-wave.webp','assets/mascot/garak-hansang-hero.webp',
      'assets/campaign/garakland-after-lotte-hero.webp','assets/campaign/garakland-after-lotte-mobile.webp', 'assets/campaign/garak-hansang-official-guide.webp']:
   self.assertTrue((R/p).is_file(),p)
  self.assertLess((R/'assets/campaign/garakland-after-lotte-hero.webp').stat().st_size,350_000)
  self.assertLess((R/'assets/campaign/garakland-after-lotte-mobile.webp').stat().st_size,250_000)
 def test_no_false_organization_affiliation(self):
  s=(R/'lotteworld-next.html').read_text()
  self.assertIn('롯데월드 또는 가락몰 운영기관과 공식 제휴하거나 공동 운영하는 프로모션이 아니며',s)
  self.assertIn('실제 점포 영업',s)
  self.assertIn('이동 경로는 길찾기에서 확인',s)
  self.assertNotIn('공식 콜라보',s)
  self.assertNotIn('입장권 30% 할인',s)
 def test_home_and_seo(self):
  home=(R/'brand/app.js').read_text()
  self.assertIn('lotteworld-next.html',home)
  self.assertIn('gl-after-lotte',home)
  html=(R/'lotteworld-next.html').read_text()
  self.assertIn('property="og:image"',html)
  self.assertIn('rel="canonical"',html)
  self.assertIn('after-lotte-v2.css',html)
  self.assertIn('/assets/campaign/garak-hansang-official-guide.webp',html)
 def test_responsive_and_accessibility(self):
  css=(R/'design/after-lotte-v2.css').read_text()
  self.assertIn('max-width:640px',css)
  self.assertIn('max-width:820px',css)
  self.assertIn('prefers-reduced-motion',css)
  html=(R/'lotteworld-next.html').read_text()
  self.assertIn('href="#main"',html)
  self.assertIn('aria-labelledby="campaignTitle"',html)
  self.assertIn('loading="lazy"',html)
if __name__=='__main__':unittest.main()
