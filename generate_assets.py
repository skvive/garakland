"""Generate original fictional beta merchant graphics; not real shop images."""
from PIL import Image, ImageDraw, ImageFont
import random, math, os, qrcode
from pathlib import Path
ROOT=Path(__file__).resolve().parent/'assets'/'demo'; ROOT.mkdir(parents=True,exist_ok=True)
FONT='/usr/share/fonts/truetype/nanum/NanumSquareRoundB.ttf'
if not Path(FONT).exists(): FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def f(sz):return ImageFont.truetype(FONT,sz)
CASES=[('sea','바다마루','수산 탐험단','신선함을 발견하세요',['참돔 모둠     22,000원','광어회 한 접시   26,000원','해물탕 밀키트   19,000원'],(29,106,127),(26,202,176),'🐟','demo-sea'),('fruit','색동과일','과일 탐험단','제철의 맛을 발견하세요',['제철과일 컵      7,500원','샤인머스캣 박스  18,000원','오늘의 과일세트  15,000원'],(149,79,105),(255,193,100),'🍓','demo-fruit'),('meat','고기공방','정육 탐험단','기분 좋은 한 끼',['불고기 도시락    12,900원','한우 국거리      21,000원','양념갈비 팩     24,900원'],(121,64,65),(248,188,151),'🥩','demo-meat'),('kitchen','가락한상 키친','요리 탐험단','시장 속 한상차림',['든든 한상       13,900원','수산 한 그릇     11,900원','가락 시장국밥      9,900원'],(63,101,78),(221,201,125),'🍱','demo-kitchen')]
for slug,name,cat,copy,menu,bg,accent,em,sid in CASES:
 random.seed(sid)
 poster=Image.new('RGB',(900,1080),(248,248,239)); d=ImageDraw.Draw(poster)
 d.rectangle([24,24,876,1056],fill=(255,255,255),outline=bg,width=8)
 d.rounded_rectangle([65,66,835,790],radius=40,fill=bg)
 for k in range(160):
  x=random.randrange(80,815); y=random.randrange(100,755); r=random.randrange(3,15)
  d.ellipse((x-r,y-r,x+r,y+r),outline=(*accent,),width=3)
 d.rounded_rectangle([105,126,795,242],22,fill=accent)
 d.text((143,157),'GARAKLAND • AR QUEST',fill=bg,font=f(47))
 d.text((124,330),name,fill=(255,255,255),font=f(106),stroke_width=1)
 d.text((130,490),cat,fill=accent,font=f(63))
 d.line((133,583,740,583),fill=accent,width=5)
 d.text((130,624),copy,fill=(255,255,255),font=f(49))
 d.text((102,834),'[ 베타 시연 · 가상 매장 ]',fill=bg,font=f(41))
 q=qrcode.QRCode(box_size=7,border=1);q.add_data('GARAKLAND:'+sid);q.make(fit=True)
 qr=q.make_image(fill_color=bg,back_color='white').convert('RGB');qr.thumbnail((177,177))
 poster.paste(qr,(650,816))
 d.text((105,975),'시연 카드 · 실재 매장이 아닙니다',fill=(85,89,91),font=f(25))
 poster.save(ROOT/f'{slug}-poster.png',optimize=True)
 menu_img=Image.new('RGB',(920,1200),(250,248,240));d=ImageDraw.Draw(menu_img)
 d.rounded_rectangle((30,30,890,1170),radius=38,fill=(255,255,255),outline=accent,width=6)
 d.rounded_rectangle((61,60,860,350),radius=28,fill=bg)
 d.text((95,113),'GARAKLAND   MENU',fill=accent,font=f(42))
 d.text((93,195),name,fill='white',font=f(85))
 d.text((100,404),'오늘의 인기메뉴',fill=bg,font=f(56))
 for j,x in enumerate(menu):
  y=535+j*163
  d.rounded_rectangle((90,y,830,y+122),20,fill=(241,246,238) if j%2==0 else (251,244,232))
  d.text((120,y+35),x,fill=(41,66,58),font=f(38))
 d.text((99,1088),'※ 샘플 메뉴·가격 · 실제 구매 불가',fill=(130,130,130),font=f(28))
 menu_img.save(ROOT/f'{slug}-menu.png',optimize=True)
 hero=Image.new('RGB',(1000,650),bg); d=ImageDraw.Draw(hero)
 for j in range(60):
  x=random.randrange(0,1000);y=random.randrange(0,650);r=random.randrange(8,90); d.ellipse((x-r,y-r,x+r,y+r),outline=accent,width=3)
 d.rounded_rectangle((65,80,600,160),radius=28,fill=accent)
 d.text((93,99),cat+'   •   DISCOVERY',fill=bg,font=f(33))
 d.text((74,240),name,fill='white',font=f(104))
 d.text((79,405),copy,fill=accent,font=f(45))
 d.text((80,569),'VIRTUAL STORE · BETA DEMO',fill='white',font=f(30))
 hero.save(ROOT/f'{slug}-hero.png',optimize=True)
print('Generated',len(list(ROOT.glob('*.png'))),'image assets')
