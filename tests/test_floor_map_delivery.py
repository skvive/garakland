"""Verify delivery-sized Garakland sales-hall floor map preserves source and uncertainty."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class FloorMapDelivery(unittest.TestCase):
 def test_original_sales_plan_retained(self):
  original=(ROOT/'assets/floorplans/sales-2f.svg').read_text('utf-8')
  self.assertIn('판매동 2F',original)
  self.assertIn('수협/신협',original)
 def test_mobile_map_uses_full_width(self):
  style=(ROOT/'src/studio-map.css').read_text('utf-8')
  self.assertIn('.floor-map-stage .floor-plan-figure img',style)
  self.assertIn('width:100%;max-width:100%;height:auto',style)
  self.assertIn('display:block;flex:1 1 auto;min-width:0',style)
 def test_source_and_disclaimer(self):
  src=(ROOT/'src/map-engine.js').read_text('utf-8')
  self.assertIn('floor-map-original',src)
  self.assertIn('실측 경로가 검증된 도면은 아닙니다',src)
  self.assertIn('aria-label="층별 도면 선택"',src)
if __name__=='__main__':unittest.main()
