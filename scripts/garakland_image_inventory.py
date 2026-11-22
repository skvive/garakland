#!/usr/bin/env python3
"""Immutable full repository image audit. Read all assets/previews, record dimensions and usage."""
import csv,hashlib,json,re
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"qa-artifacts"/"brand-refresh"
OUT.mkdir(parents=True,exist_ok=True)
images=[]
for root in ["assets","previews","brand_strategy_docs/previews"]:
 for path in (ROOT/root).rglob("*"):
  if not path.is_file() or path.suffix.lower() not in {".webp",".png",".jpg",".jpeg",".svg",".gif"}:continue
  rel=path.relative_to(ROOT).as_posix()
  content=path.read_bytes()
  d={"path":rel,"bytes":len(content),"sha256":hashlib.sha256(content).hexdigest(),"width":None,"height":None,"format":path.suffix.lower(),"usage":[]}
  try:
   if path.suffix.lower()==".svg":
    txt=content.decode("utf-8")
    m=re.search(r'viewBox=["\']\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)',txt)
    if m:d["width"],d["height"]=int(float(m.group(3))),int(float(m.group(4)))
   else:
    with Image.open(path) as im:
     d["width"],d["height"]=im.size
  except Exception as exc:d["read_error"]=str(exc)[:150]
  images.append(d)
pages=[]
for ext in ("*.html","*.js","*.mjs","*.css"):
 pages.extend(ROOT.rglob(ext))
for p in pages:
 if ".git" in p.parts or "node_modules" in p.parts:continue
 if p.stat().st_size>1_000_000:continue
 try:src=p.read_text("utf-8")
 except Exception:continue
 for row in images:
  if row["path"] in src or "/"+row["path"] in src:
   row["usage"].append(p.relative_to(ROOT).as_posix())
for row in images:row["usage"]=sorted(set(row["usage"]))
dup={}
for row in images:dup.setdefault(row["sha256"],[]).append(row["path"])
duplicates=[v for v in dup.values() if len(v)>1]
result={"image_count":len(images),"image_read_errors":[r["path"] for r in images if "read_error" in r],"duplicate_groups":duplicates,"unused_assets":[r["path"] for r in images if not r["usage"]],"images":images}
(OUT/"asset-inventory.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
with (OUT/"asset-inventory.csv").open("w",encoding="utf-8-sig",newline="") as f:
 w=csv.writer(f);w.writerow(["path","width","height","bytes","sha256","used_by","issue"])
 for v in images:w.writerow([v["path"],v["width"],v["height"],v["bytes"],v["sha256"],"; ".join(v["usage"]),v.get("read_error","")])
print(json.dumps({"assets":len(images),"decode_errors":result["image_read_errors"],"duplicates":len(duplicates),"not_referenced":len(result["unused_assets"])},ensure_ascii=False))
if result["image_read_errors"]:raise SystemExit(1)
