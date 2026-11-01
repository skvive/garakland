"""Theme park identity and legacy 3D map routing regression.
This static test is independent of live Google Maps, browser permissions and payments.
"""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
def read(path): return (ROOT/path).read_text(encoding="utf-8")
class ThemeParkBrand(unittest.TestCase):
    def test_logo_valid_svg(self):
        for path in ("assets/brand/garakland-themepark-logo.svg",
                     "assets/brand/garakland-themepark-mark.svg"):
            root=ET.parse(ROOT/path).getroot()
            self.assertTrue(root.tag.endswith("svg"))
    def test_brand_is_garakland_first(self):
        s=read("brand/app.js")
        self.assertIn("GARAKLAND · MARKET THEME PARK",s)
        self.assertIn('map:\'map.html\'',s)
        self.assertIn('gl-theme-brand-logo',s)
        self.assertIn('gl-sponsor-inline',s)
        self.assertNotIn('map:\'market-map.html\'',s)
        self.assertIn('실제 협찬·입점 업체는 계약 확인 후 표시합니다',s)
    def test_old_map_is_3d_redirect(self):
        s=read("market-map.html")
        self.assertIn("location.replace('/map.html'",s)
        self.assertNotIn('src="brand/app.js"',s)
    def test_current_3d_atlas_still_exists(self):
        s=read("map.html")
        for expected in ("src/app.js","src/styles.css","id=\"map\""):
            self.assertIn(expected,s)
    def test_entrypoints_include_themepark_styles(self):
        pages=("index.html","home.html","stores.html","store.html","coupons.html",
               "events.html","market-guide.html","merchant-center.html","market.html",
               "map.html","ar-quest.html","ops.html","hub.html","login.html",
               "documents.html","design_gallery.html","unsubscribe.html")
        for p in pages:
            with self.subTest(page=p):
                self.assertIn("/design/garakland-themepark.css",read(p))
    def test_manifest_brand(self):
        import json
        m=json.loads(read("manifest.webmanifest"))
        self.assertTrue(m["name"].startswith("가락랜드"))
        self.assertIn("garakland-themepark-mark.svg",m["icons"][0]["src"])
if __name__=="__main__": unittest.main()
