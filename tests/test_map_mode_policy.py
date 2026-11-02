"""Satellite mode removal policy: no tab and no fallback to broken imagery."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class MapModePolicy(unittest.TestCase):
 def test_no_satellite_tab(self):
  html=(ROOT/'map.html').read_text('utf-8')
  self.assertNotIn('data-mode="satellite"',html)
  self.assertNotIn('>위성</button>',html)
  self.assertEqual(html.count('data-mode="concept"'),1)
  self.assertEqual(html.count('data-mode="3d"'),1)
  self.assertEqual(html.count('data-mode="terrain"'),1)
  self.assertEqual(html.count('data-mode="floor"'),1)
 def test_no_satellite_fallback(self):
  app=(ROOT/'src/app.js').read_text('utf-8')
  engine=(ROOT/'src/map-engine.js').read_text('utf-8')
  self.assertNotIn("setMode('satellite')",app)
  self.assertNotIn("applyModeChrome('satellite')",app)
  self.assertNotIn("MapTypeId?.SATELLITE",engine)
  self.assertNotIn("VIEW.satellite",engine)
  self.assertIn("SUPPORTED_PUBLIC_MAP_MODES.has(mode)",app)
  self.assertIn("map.setMode('concept');applyModeChrome('concept')",app)
  self.assertIn("['concept','floor','terrain','roadmap','3d']",engine)
 def test_help_text_does_not_promote_satellite(self):
  html=(ROOT/'map.html').read_text('utf-8')
  self.assertNotIn('실제 위성·지형 지도',html)
  self.assertNotIn('위성 지도와 3D 지도',html)
if __name__=='__main__':unittest.main()
