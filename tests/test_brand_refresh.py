#!/usr/bin/env python3
"""GARAKLAND brand v3: user-approved wordmark + G emblem, image and reference contract."""
from pathlib import Path
from PIL import Image
import json,re,sys
ROOT=Path(__file__).resolve().parents[1];ASSETS=ROOT/"assets"/"brand"
errors=[]
assets={"garakland-og-v3.jpg":(1200,630),"garakland-wordmark-header-v3.webp":(1200,332),"garakland-wordmark-full-v3.webp":(1300,559),"garakland-g-symbol-v3.webp":(750,750),"garakland-g-favicon-v3-16.png":(16,16),"garakland-g-favicon-v3-32.png":(32,32),"garakland-g-favicon-v3-48.png":(48,48),"garakland-g-favicon-v3-192.png":(192,192),"garakland-g-favicon-v3-512.png":(512,512),"garakland-g-apple-touch-v3.png":(180,180)}
for name,size in assets.items():
 p=ASSETS/name
 if not p.is_file():errors.append("missing image: "+name);continue
 try:
  with Image.open(p) as im:
   if im.size!=size:errors.append(f"dimension mismatch {name}: {im.size}, expected {size}")
   im.verify()
 except Exception as exc: errors.append(f"decode error {name}: {exc}")
if not (ROOT/"favicon.ico").is_file(): errors.append("missing root favicon.ico")
manifest=json.loads((ROOT/"manifest.webmanifest").read_text(encoding="utf-8"))
for entry in manifest.get("icons",[]):
 path=ROOT/entry["src"].lstrip("/")
 if not path.is_file():errors.append("PWA missing "+str(path))
 if "garakland-g-favicon-v3" not in entry["src"]:errors.append("wrong PWA icon "+entry["src"])
for p in ROOT.glob("*.html"):
 s=p.read_text(encoding="utf-8")
 if "garakland-themepark-logo.svg" in s or "garakland-themepark-mark.svg" in s or "garakland-og-v2.jpg" in s:errors.append("old brand reference: "+p.name)
 if 'og:image' in s and "garakland-og-v3.jpg" not in s:errors.append("OG mismatch: "+p.name)
 if 'garakland-g-favicon-v3-' in s and not ("garakland-g-favicon-v3-32.png" in s or "garakland-g-favicon-v3-48.png" in s):errors.append("favicon reference mismatch: "+p.name)
 if p.name in ("index.html","home.html","project.html","culture.html","commerce.html","map.html","login.html","hub.html"):
  if p.name=="index.html":continue # Index header is generated from brand/app.js
  if "garakland-wordmark-header-v3.webp" not in s:errors.append("wordmark not installed: "+p.name)
s=(ROOT/"brand/app.js").read_text(encoding="utf-8")
if 'garakland-wordmark-header-v3.webp' not in s or 'garakland-g-symbol-v3.webp' not in s:errors.append("dynamic brand renderer still stale")
if 'class="gl-floating-hub"' in (ROOT/"index.html").read_text(encoding="utf-8"):errors.append("public operations entry reintroduced")
for name in ("project.html","culture.html","commerce.html"):
 body=(ROOT/name).read_text(encoding="utf-8")
 if "실증" not in body or "공식 운영 서비스" not in body:errors.append("project disclaimer absent "+name)
for p in ROOT.rglob("*.html"):
 if "node_modules" in p.parts:continue
 txt=p.read_text(encoding="utf-8")
 for src in re.findall(r"""(?:src|href)=['"](/(?:assets|design)/[^'"]+)['"]""",txt):
  if not (ROOT/src.lstrip("/")).exists(): errors.append(f"{p.name}: missing {src}")
print(json.dumps({"test":"brand-v3","assets_verified":len(assets),"pages_scanned":len(list(ROOT.glob('*.html'))),"errors":errors},ensure_ascii=False))
if errors:sys.exit(1)
