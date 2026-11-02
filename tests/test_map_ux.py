"""Map UX: floor zoom, store-to-floor navigation and mobile details sheet."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class MapUX(unittest.TestCase):
 def test_floor_zoom_controller_connected(self):
  e=(ROOT/'src/map-engine.js').read_text()
  self.assertIn("import {FloorViewport}",e)
  self.assertIn("new FloorViewport(this.el)",e)
  for v in ('data-floor-zoom="in"','data-floor-zoom="out"','data-floor-zoom="reset"','floor-map-viewport'):
   self.assertIn(v,e)
 def test_store_navigation_does_not_fake_room_markers(self):
  app=(ROOT/'src/app.js').read_text()
  self.assertIn("const knownFloor=building.floors.includes(shop.floor)",app)
  self.assertIn("changeMapMode('floor')",app)
  self.assertIn("storeName:ctx.store?.name",app)
  self.assertIn('개별 호실의 정확한 위치는 검증되지 않았습니다',app)
  floor=(ROOT/'src/floorplans.js').read_text()
  self.assertIn("plan.geometryApproved===true",floor)
  self.assertIn("s.indoorCoordinateStatus==='verified'",floor)
  eng=(ROOT/'src/map-engine.js').read_text()
  self.assertIn("개별 매장 호실의 지도 위치는 미확인",eng)
 def test_bottom_sheet_accessibility(self):
  html=(ROOT/'map.html').read_text()
  self.assertIn('id="detailSheetToggle"',html)
  self.assertIn('aria-controls="detailBody"',html)
  style=(ROOT/'src/studio-map.css').read_text()
  self.assertIn('.details.is-open{transform:translateY(0)}',style)
  self.assertIn('prefers-reduced-motion',style)
if __name__=='__main__':unittest.main()
