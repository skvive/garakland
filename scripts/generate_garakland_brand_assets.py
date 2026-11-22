#!/usr/bin/env python3
"""Build deterministic GARAKLAND OG + app icons. Preserve original brand assets."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"assets"/"brand"
OUT.mkdir(parents=True,exist_ok=True)
FONTS=[
 "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
 "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
 "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
 "/usr/share/fonts/truetype/noto/NotoSansKR-Bold.ttf",
]
fontfile=next((f for f in FONTS if Path(f).exists()),None)
if not fontfile: raise SystemExit("Noto Korean font unavailable; do not generate corrupt Korean typography.")
def font(n):return ImageFont.truetype(fontfile,n,index=0)
G=(15,93,59);D=(18,59,42);C=(249,245,233);A=(242,122,80);Y=(245,209,121)
def symbol(draw,box,scale=1):
 x,y,w,h=box
 r=int(w*.20)
 draw.rounded_rectangle([x,y,x+w,y+h],radius=r,fill=G)
 cx,cy=x+w*.50,y+h*.36
 rr=w*.22
 draw.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),outline=Y,width=max(2,int(w*.045)))
 for dx,dy in [(1,0),(0,1),(.7,.7),(-.7,.7)]:
  draw.line([(cx-dx*rr,cy-dy*rr),(cx+dx*rr,cy+dy*rr)],fill=Y,width=max(1,int(w*.024)))
 draw.ellipse((cx-w*.035,cy-w*.035,cx+w*.035,cy+w*.035),fill=C)
 roof_y=y+h*.71
 draw.polygon([(x+w*.16,roof_y),(x+w*.31,y+h*.57),(x+w*.69,y+h*.57),(x+w*.84,roof_y)],fill=C)
 for x0,x1 in [(0.16,.33),(.34,.5),(.51,.67),(.68,.84)]:
  draw.polygon([(x+w*x0,roof_y),(x+w*(x0+.07),y+h*.57),(x+w*x1,y+h*.57),(x+w*x1,roof_y)],fill=A)
 draw.rounded_rectangle((x+w*.23,y+h*.77,x+w*.77,y+h*.83),radius=max(2,int(w*.025)),fill=Y)
# OG card
W,H=1200,630
im=Image.new("RGB",(W,H),C);d=ImageDraw.Draw(im)
for y in range(H):
 t=y/(H-1);d.line([(0,y),(W,y)],fill=(int(249-8*t),int(245-8*t),int(233-6*t)))
d.ellipse((-210,-260,400,340),fill=(218,234,217))
d.ellipse((915,440,1380,850),fill=(225,234,216))
d.rounded_rectangle((60,65,1140,565),radius=42,fill=(255,254,250),outline=(218,231,217),width=2)
symbol(d,(110,145,230,230))
d.text((401,157),"가락랜드",font=font(94),fill=D)
d.text((407,283),"GARAKLAND",font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",34),fill=G,stroke_width=0)
d.text((406,358),"시장·문화·관광을",font=font(34),fill=(69,93,77))
d.text((406,407),"온라인 유통과 연결합니다",font=font(34),fill=(69,93,77))
d.rounded_rectangle((405,487,853,535),radius=24,fill=(235,244,234))
d.text((430,498),"MARKET  ·  CULTURE  ·  COMMERCE",font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",18),fill=G)
og=OUT/"garakland-og-v2.jpg";im.save(og,"JPEG",quality=86,optimize=True,progressive=True,subsampling=0)
# derived mobile icons (never overwrite the user-provided old mascot icons)
for size in (32,192,512,180):
 q=4;high=Image.new("RGBA",(size*q,size*q),(0,0,0,0));di=ImageDraw.Draw(high)
 symbol(di,(0,0,size*q-1,size*q-1))
 fn=("garakland-apple-v2.png" if size==180 else f"garakland-favicon-v2-{size}.png")
 high.resize((size,size),Image.Resampling.LANCZOS).save(OUT/fn,optimize=True)
print("GENERATED",[(x.name,x.stat().st_size) for x in [og,*sorted(OUT.glob("*v2*.png"))]])
