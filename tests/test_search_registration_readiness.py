from pathlib import Path
from html.parser import HTMLParser
import unittest,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
HOST='https://garakland.lexid.site'
URLS=['/','/map.html','/indoor-map.html','/lotteworld-next.html','/stores.html','/market-guide.html','/market.html','/ar-quest.html']
class Page(HTMLParser):
 def __init__(self):super().__init__();self.tags=[]
 def handle_starttag(self,name,attrs):self.tags.append((name,dict(attrs)))
def html(path):
 parser=Page();parser.feed((ROOT/path).read_text('utf-8'));return parser.tags
class SearchRegistrationReadiness(unittest.TestCase):
 def test_robots_and_sitemap(self):
  robots=(ROOT/'robots.txt').read_text()
  self.assertIn('Disallow: /api/',robots)
  self.assertIn('Sitemap: '+HOST+'/sitemap.xml',robots)
  root=ET.parse(ROOT/'sitemap.xml').getroot()
  urls=[x.text for x in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
  self.assertEqual(urls,[HOST+x for x in URLS])
 def test_public_pages_canonical(self):
  for route in URLS:
   path=route[1:] if route!='/' else 'index.html'
   with self.subTest(path=path):
    tags=html(path)
    self.assertEqual([d.get('href') for k,d in tags if k=='link' and d.get('rel')=='canonical'],[HOST+route])
    self.assertEqual(len([d for k,d in tags if k=='meta' and d.get('name')=='description']),1)
 def test_review_pages_noindex(self):
  for p in ['indoor-campus-lab.html','indoor-layout-lab.html','indoor-tenant-lab.html']:
   tags=html(p)
   self.assertIn('noindex',next(d.get('content','') for k,d in tags if k=='meta' and d.get('name')=='robots'))
 def test_visible_no_js_home_content(self):
  h=(ROOT/'index.html').read_text()
  self.assertIn('가락랜드에서 가락시장 탐험하기',h)
  self.assertIn('application/ld+json',h)
if __name__=='__main__':unittest.main()
