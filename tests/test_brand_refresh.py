#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import re,sys
ROOT=Path(__file__).resolve().parents[1];ASSETS=ROOT/"assets"/"brand"
pages=[ROOT/p for p in ("index.html","home.html","hub.html","login.html","project.html","culture.html","commerce.html","events.html","market-guide.html")]
errors=[]
for p in pages:
 s=p.read_text(encoding="utf-8")
 if "garakland-logo-header.png" in s: errors.append(f"legacy wrong-size OG in {p.name}")
 if p.name in ("index.html","home.html","project.html","culture.html","commerce.html"):
  if "garakland-og-v2.jpg" not in s: errors.append(f"missing new OG {p.name}")
 if p.name=="index.html" and 'class="gl-floating-hub"' in s:errors.append("admin shortcut is public on homepage")
 if p.name=="hub.html" and 'garakland-themepark-logo.svg" alt="가락한상"' in s: errors.append("incorrect logo alt")
 for link in re.findall(r'(?:src|href)=["\'](/(?:assets|design)/[^"\']+)["\']',s):
  if not (ROOT/link.lstrip("/")).exists(): errors.append(f"{p.name}:missing {link}")
og=ASSETS/"garakland-og-v2.jpg"
if not og.exists():errors.append("new OG has not been generated")
else:
 with Image.open(og) as im:
  if im.size!=(1200,630):errors.append(f"wrong OG dimensions {im.size}")
for n,s in [("garakland-favicon-v2-32.png",32),("garakland-favicon-v2-192.png",192),("garakland-favicon-v2-512.png",512),("garakland-apple-v2.png",180)]:
 f=ASSETS/n
 if not f.exists():errors.append(f"missing icon {n}")
 else:
  with Image.open(f) as im:
   if im.size!=(s,s):errors.append(f"{n}: wrong size {im.size}")
for name in ["project.html","culture.html","commerce.html"]:
 page=(ROOT/name).read_text(encoding="utf-8")
 if "실증" not in page or "공식 운영 서비스" not in page:errors.append(f"{name}:missing independent demo disclaimer")
print("brand-static-audit",{"files":len(pages),"og":og.exists(),"errors":errors})
if errors:sys.exit(1)
