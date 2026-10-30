#!/usr/bin/env python3
"""GARAKLAND AR QUEST beta / local stdlib backend; core Google map inherited.
Production requires verified merchant data, user auth, HTTPS and regulatory review.
"""
from __future__ import annotations
import os, re, io, json, math, time, hmac, base64, hashlib, secrets, sqlite3, threading
from http.cookies import SimpleCookie
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, parse_qs, quote
from market import core as growth_v5
import bridge_v7
from ops import core as operations_v6
from hub import core as hub_v8
from registry_server import (ROOT, DB, db_connect, DB_LOCK, init_db as init_registry,
                             Handler as RegistryHandler, ADMIN_TOKEN, HOST, PORT, normalize, upsert)

KST = timezone(timedelta(hours=9))
SIGN_SECRET = os.environ.get('GARAK_QR_SECRET') or secrets.token_urlsafe(40)
LOCAL_DEMO = os.environ.get('GARAK_ENABLE_DEMO', '1' if HOST in ('127.0.0.1','localhost') else '0') == '1'
MAX_BODY = 4_500_000
METERS_LIMIT = 110
SAMPLE = [
 ('demo-sea','[시연] 바다마루','수산','seafood','1F','체험 S-01','🐟','참돔 모둠','22000','sea'),
 ('demo-fruit','[시연] 색동과일','청과','produce','1F','체험 P-02','🍓','제철과일 컵','7500','fruit'),
 ('demo-meat','[시연] 고기공방','축산','sales','1F','체험 M-03','🥩','불고기 도시락','12900','meat'),
 ('demo-kitchen','[시연] 가락한상 키친','음식','theme1','2F','체험 K-04','🍱','든든 한상','13900','kitchen'),
]
SAMPLE_MENU = {
 'demo-sea':[('참돔 모둠',22000),('광어회 한 접시',26000),('해물탕 밀키트',19000)],
 'demo-fruit':[('제철과일 컵',7500),('샤인머스캣 박스',18000),('오늘의 과일세트',15000)],
 'demo-meat':[('불고기 도시락',12900),('한우 국거리',21000),('양념갈비 팩',24900)],
 'demo-kitchen':[('든든 한상',13900),('수산 한 그릇',11900),('가락 시장국밥',9900)]
}

def now(): return datetime.now(KST)
def iso(dt=None): return (dt or now()).isoformat(timespec='seconds')
def epoch(): return int(time.time())
def period_key(kind, dt=None):
    dt=dt or now()
    if kind=='DAILY':return dt.strftime('%Y-%m-%d')
    if kind=='WEEKLY':return f'{dt.isocalendar().year}-W{dt.isocalendar().week:02d}'
    return 'ONCE'
def period_end(kind,dt=None):
    dt=dt or now()
    if kind=='DAILY': return dt.replace(hour=23,minute=59,second=59,microsecond=0)
    if kind=='WEEKLY': return (dt+timedelta(days=6-dt.weekday())).replace(hour=23,minute=59,second=59,microsecond=0)
    return dt+timedelta(days=30)
def fmt_shop(s): return {'id':s['id'],'name':s['name'],'category':s['category'],'building':s['building'],'floor':s['floor'],'room':s['room'],'latitude':s['latitude'],'longitude':s['longitude'],'coordinateStatus':s['coordinateStatus'],'blogUrl':s['blogUrl'],'isDemo':s['id'].startswith('demo-')}

def setup():
    init_registry()
    with DB_LOCK, db_connect() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS game_sessions (id TEXT PRIMARY KEY, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS merchant_meta (shop_id TEXT PRIMARY KEY, hero TEXT NOT NULL, menu_image TEXT NOT NULL, reference_image TEXT NOT NULL, delivery_url TEXT NOT NULL DEFAULT '', menu_json TEXT NOT NULL DEFAULT '[]', is_demo INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS merchant_keys (shop_id TEXT PRIMARY KEY, key_hash TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS campaigns (id TEXT PRIMARY KEY, shop_id TEXT NOT NULL, title TEXT NOT NULL, details TEXT NOT NULL, discount_label TEXT NOT NULL, recurrence TEXT NOT NULL, stock INTEGER NOT NULL, active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS wallet (id TEXT PRIMARY KEY, session_id TEXT NOT NULL, campaign_id TEXT NOT NULL, period TEXT NOT NULL, code TEXT UNIQUE NOT NULL, issued_at TEXT NOT NULL, expires_at TEXT NOT NULL, redeemed_at TEXT, UNIQUE(session_id,campaign_id,period));
        CREATE INDEX IF NOT EXISTS idx_wallet_user ON wallet(session_id);
        CREATE TABLE IF NOT EXISTS visits (session_id TEXT NOT NULL, shop_id TEXT NOT NULL, day TEXT NOT NULL, method TEXT NOT NULL, at TEXT NOT NULL, PRIMARY KEY(session_id,shop_id,day));
        CREATE INDEX IF NOT EXISTS idx_visits_user ON visits(session_id);
        CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY, session_id TEXT NOT NULL, shop_id TEXT NOT NULL, menu_name TEXT NOT NULL, quantity INTEGER NOT NULL, total INTEGER NOT NULL, mode TEXT NOT NULL, status TEXT NOT NULL, note TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(session_id);
        ''')
        for sid,name,cat,building,floor,room,icon,product,price,slug in SAMPLE:
            rec={'id':sid,'name':name,'category':cat,'building':building,'floor':floor,'room':room,'description':'[베타 시연용 가상 매장] 실재 상호·점포가 아닙니다. 실제 가락시장 위치·메뉴·가격과 무관합니다.','address':'서울 송파구 양재대로 932','latitude':None,'longitude':None,'coordinateStatus':'unverified','blogUrl':'','websiteUrl':'','phone':'','sourceUrl':'','verifiedAt':'','status':'published','featured':False}
            # Preserve official/merchant edits. Never overwrite an existing shop.
            con.execute('INSERT OR IGNORE INTO stores ("id","name","category","building","floor","room","description","address","latitude","longitude","coordinateStatus","blogUrl","websiteUrl","phone","sourceUrl","verifiedAt","status","featured","indoorX","indoorY") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', tuple(normalize(rec).get(k) for k in ('id','name','category','building','floor','room','description','address','latitude','longitude','coordinateStatus','blogUrl','websiteUrl','phone','sourceUrl','verifiedAt','status','featured','indoorX','indoorY')))
            base=f'/assets/demo/{slug}'
            con.execute('INSERT OR IGNORE INTO merchant_meta VALUES (?,?,?,?,?,?,?)',(sid,base+'-hero.png',base+'-menu.png',base+'-poster.png','',json.dumps([{'name':n,'price':p} for n,p in SAMPLE_MENU[sid]],ensure_ascii=False),1))
        seeds=[('c-sea','demo-sea','오늘의 수산 탐험','실내 확인 시 적용 조건 별도 문의','2,000원 할인','DAILY',50),('c-fruit','demo-fruit','제철 과일 보너스','1인 1회 사용, 시연 데이터','10% 할인','WEEKLY',100),('c-meat','demo-meat','정육 탐험 쿠폰','시연 데이터, 실제 결제 불가','3,000원 할인','DAILY',30),('c-kitchen','demo-kitchen','한상 시식권','시연 데이터, 실제 사용 불가','무료 시식 체험','WEEKLY',20)]
        for c in seeds:con.execute('INSERT OR IGNORE INTO campaigns VALUES (?,?,?,?,?,?,?,?,?)',(*c,1,iso()))
        con.commit()
    growth_v5.setup()
    operations_v6.setup()
    hub_v8.setup()

def read_json(handler):
    if handler.headers.get('X-Garak-Client') != '1': raise ValueError('보안 헤더 누락')
    try: l=int(handler.headers.get('Content-Length','0'))
    except Exception:raise ValueError('Content-Length 오류')
    if l<1 or l>MAX_BODY:raise ValueError('본문 크기 제한')
    val=json.loads(handler.rfile.read(l))
    if not isinstance(val,dict):raise ValueError('JSON 객체가 필요합니다')
    return val

def safe_http(url):
    if not isinstance(url,str) or not url:return ''
    u=urlsplit(url)
    return url[:1000] if u.scheme in ('https','http') and u.hostname and not u.username and not u.password else ''

def haversine(a,b,c,d):
    radius=6371000
    p=math.radians(c-a);q=math.radians(d-b)
    z=math.sin(p/2)**2+math.cos(math.radians(a))*math.cos(math.radians(c))*math.sin(q/2)**2
    return radius*2*math.atan2(math.sqrt(z),math.sqrt(1-z))

def sign_qr(shop_id, secs=180):
    expiry=epoch()+secs
    raw=f'{shop_id}.{expiry}'
    mac=hmac.new(SIGN_SECRET.encode(),raw.encode(),hashlib.sha256).hexdigest()[:24]
    return raw+'.'+mac

def verify_qr(token, shop):
    if not isinstance(token,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}\.[0-9]{10,11}\.[a-f0-9]{24}',token):return False
    a,t,mac=token.rsplit('.',2)
    if a!=shop or abs(int(t)-epoch())>480 or int(t)<epoch():return False
    want=hmac.new(SIGN_SECRET.encode(),f'{a}.{t}'.encode(),hashlib.sha256).hexdigest()[:24]
    return hmac.compare_digest(mac,want)

def recognize(image_b64):
    """Real optional OpenCV ORB reference-image matching; never claim vision success without references."""
    try: import cv2, numpy as np
    except ImportError:return {'supported':False,'message':'사진 매칭용 OpenCV/NumPy를 설치하세요. QR 인식·매장 검색은 계속 사용할 수 있습니다.'}
    if not isinstance(image_b64,str) or len(image_b64)>4_200_000:raise ValueError('이미지 최대 3MB')
    try: data=base64.b64decode(image_b64.split(',',1)[-1],validate=True)
    except Exception:raise ValueError('이미지 인코딩 오류')
    if len(data)>3_100_000:raise ValueError('이미지 최대 3MB')
    camera=cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_GRAYSCALE)
    if camera is None:raise ValueError('사진을 판독할 수 없습니다')
    h,w=camera.shape[:2]
    if h*w>16_000_000:raise ValueError('이미지 해상도 초과')
    scale=min(1,1050/max(h,w));camera=cv2.resize(camera,None,fx=scale,fy=scale) if scale<1 else camera
    orb=cv2.ORB_create(nfeatures=1500)
    kp1,des1=orb.detectAndCompute(camera,None)
    if des1 is None or len(kp1)<15:return {'supported':True,'matched':False,'reason':'특징점이 부족합니다. 간판을 더 가까이 또렷하게 촬영하세요.'}
    with DB_LOCK,db_connect() as c:
        rows=c.execute('SELECT shop_id,reference_image FROM merchant_meta WHERE reference_image!=""').fetchall()
    matcher=cv2.BFMatcher(cv2.NORM_HAMMING)
    scores=[]
    for x in rows:
        rel=x['reference_image'].lstrip('/')
        path=(ROOT/rel).resolve()
        if not path.is_relative_to(ROOT/'assets') or not path.is_file():continue
        ref=cv2.imread(str(path),cv2.IMREAD_GRAYSCALE)
        if ref is None:continue
        k2,d2=orb.detectAndCompute(ref,None)
        if d2 is None or len(k2)<15:continue
        pairs=matcher.knnMatch(des1,d2,k=2)
        good=[m for pair in pairs if len(pair)==2 for m,n in [pair] if m.distance<0.72*n.distance]
        if len(good)<18:continue
        src=np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1,1,2)
        dst=np.float32([k2[m.trainIdx].pt for m in good]).reshape(-1,1,2)
        H,mask=cv2.findHomography(src,dst,cv2.RANSAC,5.0)
        inliers=int(mask.sum()) if mask is not None else 0
        if H is not None and inliers>=12 and inliers/len(good)>=0.35:scores.append((inliers,x['shop_id'],len(good)))
    scores.sort(reverse=True)
    if not scores:return {'supported':True,'matched':False,'reason':'등록된 매장 간판과 충분히 일치하지 않습니다.'}
    if len(scores)>1 and scores[0][0] < scores[1][0]*1.35:return {'supported':True,'matched':False,'reason':'복수 매장이 비슷하게 인식되어 확인이 필요합니다.'}
    count,shop,good=scores[0]
    return {'supported':True,'matched':True,'shopId':shop,'method':'ORB_REFERENCE','inliers':count,'goodMatches':good,'note':'등록된 기준 이미지와의 시각적 일치이며 실제 방문·위치 확인은 아닙니다.'}

class Handler(RegistryHandler):
    def session(self):
        c=SimpleCookie()
        try:c.load(self.headers.get('Cookie',''))
        except Exception:pass
        value=c.get('garak_quest_session')
        candidate=value.value if value else ''
        if not re.fullmatch(r'[A-Za-z0-9_-]{32,64}',candidate):candidate=''
        if candidate:
            with DB_LOCK,db_connect() as db:
                if db.execute('SELECT id FROM game_sessions WHERE id=?',(candidate,)).fetchone():return candidate
        self._new_session=secrets.token_urlsafe(32)
        with DB_LOCK,db_connect() as db:
            db.execute('INSERT INTO game_sessions VALUES (?,?)',(self._new_session,iso()));db.commit()
        return self._new_session
    def uid(self):
        if not hasattr(self,'_uid'):self._uid=self.session()
        return self._uid
    def send_json(self,code,obj):
        raw=json.dumps(obj,ensure_ascii=False,default=str).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        if getattr(self,'_new_session',''):
            secure='; Secure' if self.headers.get('X-Forwarded-Proto')=='https' else ''
            self.send_header('Set-Cookie',f'garak_quest_session={self._new_session}; HttpOnly; SameSite=Lax; Path=/{secure}')
        self.end_headers();self.wfile.write(raw)
    def guess_type(self,path):
        # Make Korean characters unambiguous for clients that ignore HTML meta charset.
        mime=super().guess_type(path)
        if mime.startswith('text/') and 'charset=' not in mime:
            return mime+'; charset=utf-8'
        return mime
    def do_GET(self):
        u=urlsplit(self.path); p=u.path
        try:
            if p.startswith('/api/v8/'):
                found=hub_v8.dispatch_get(self,p,parse_qs(u.query))
                if found is not False:return found
            if hub_v8.is_disabled(p):return self.send_json(503,{'error':'운영 허브에서 해당 모듈이 일시중지되었습니다.'})
            if p.startswith('/api/v7/'):
                found=bridge_v7.get(self,p,parse_qs(u.query))
                if found is not False:return found
            if p.startswith('/api/v8/'):
                found=hub_v8.dispatch_post(self,p,body)
                if found is not False:return found
            if hub_v8.is_disabled(p):return self.send_json(503,{'error':'운영 허브에서 해당 모듈이 일시중지되었습니다.'})
            if p.startswith('/api/v6/'):
                found=operations_v6.get(self,p,parse_qs(u.query))
                if found is not False:return found
            if p.startswith('/api/v5/'):
                found=growth_v5.get(self,p,parse_qs(u.query))
                if found is not False:return found
            if p=='/api/experience':return self.send_json(200,self.experience())
            if p=='/api/wallet':return self.send_json(200,self.wallet())
            if p=='/api/progress':return self.send_json(200,self.progress())
            if p=='/api/orders':return self.send_json(200,self.orders())
            if p=='/api/merchant/qr':return self.merchant_qr(parse_qs(u.query))
            if p=='/api/health':return self.send_json(200,{'ok':True,'version':'3.0-beta','demo':LOCAL_DEMO,'cameraScan':'BarcodeDetector','photoMatcher':'OpenCV optional'})
            if p=='/api/public/config':
                key=(os.environ.get('GOOGLE_MAPS_API_KEY') or '').strip()
                if not key.startswith('AIza'):key=''
                return self.send_json(200,{'googleMapsApiKey':key,'mapsConfigured':bool(key)})
            if p=='/scan':
                # Shareable shop QR (only discovery). Time-bound signed QR is used for check-in.
                query=parse_qs(u.query);s=query.get('shop',[''])[0]
                self.send_response(302);self.send_header('Location','/?shop='+quote(s,safe='')+('&qr='+quote(query.get('token',[''])[0],safe='') if query.get('token',[''])[0] else ''));self.end_headers();return
            if p in ('/','/index.html'):
                self.path='/index.html';return super().do_GET()
            return super().do_GET()
        except (ValueError,sqlite3.Error) as exc:return self.send_json(400,{'error':str(exc)})
    def do_POST(self):
        p=urlsplit(self.path).path
        if p=='/api/import':
            if hub_v8.is_disabled(p):return self.send_json(503,{'error':'매장 모듈이 일시중지되었습니다.'})
            return super().do_POST()
        try:
            body=read_json(self)
            if p.startswith('/api/v8/'):
                found=hub_v8.dispatch_post(self,p,body)
                if found is not False:return found
            if hub_v8.is_disabled(p):return self.send_json(503,{'error':'운영 허브에서 해당 모듈이 일시중지되었습니다.'})
            if p.startswith('/api/v6/'):
                found=operations_v6.post(self,p,body)
                if found is not False:return found
            if p.startswith('/api/v5/'):
                found=growth_v5.post(self,p,body)
                if found is not False:return found
            if p=='/api/recognize':return self.send_json(200,recognize(body.get('image','')))
            if p=='/api/demo/checkin':return self.demo_checkin(body)
            if p=='/api/checkin':return self.checkin(body)
            if p=='/api/coupons/claim':return self.claim(body)
            if p=='/api/orders':return self.create_order(body)
            if p=='/api/merchant/campaign':return self.campaign(body)
            if p=='/api/merchant/redeem':return self.redeem(body)
            if p=='/api/merchant/order-status':return self.order_status(body)
            if p=='/api/admin/merchant-key':return self.merchant_create(body)
            if p=='/api/admin/metadata':return self.metadata(body)
            if p=='/api/merchant/profile':return self.merchant_profile(body)
            if p=='/api/merchant/upload-photo':return self.merchant_upload_photo(body)
            return self.send_json(404,{'error':'API 없음'})
        except (ValueError,TypeError,KeyError) as exc:return self.send_json(400,{'error':str(exc)})
        except sqlite3.Error:return self.send_json(500,{'error':'데이터베이스 오류'})
    def experience(self):
        with DB_LOCK,db_connect() as db:
            stores=db.execute("SELECT * FROM stores WHERE status='published' ORDER BY name").fetchall()
            meta={r['shop_id']:dict(r) for r in db.execute('SELECT * FROM merchant_meta')}
            coupons=[dict(r) for r in db.execute('SELECT * FROM campaigns WHERE active=1')]
        out=[]
        for s in stores:
            a=fmt_shop(s);m=meta.get(s['id'],{})
            a.update({k:m.get(k,'') for k in ('hero','menu_image','delivery_url','reference_image')})
            a['menu']=json.loads(m.get('menu_json','[]'))
            a['isDemo']=bool(m.get('is_demo',s['id'].startswith('demo-')))
            a['delivery_url']=safe_http(a['delivery_url'])
            out.append(a)
        return {'shops':out,'campaigns':coupons,'demoMode':LOCAL_DEMO,'serverTime':iso(),'policy':'GPS 위치는 방문 시 판정에만 사용하며 원시 좌표를 보관하지 않습니다.'}
    def wallet(self):
        uid=self.uid()
        with DB_LOCK,db_connect() as db:
            rows=[dict(r) for r in db.execute('''SELECT w.*, c.shop_id,c.title,c.discount_label,s.name AS shop_name FROM wallet w JOIN campaigns c ON c.id=w.campaign_id JOIN stores s ON s.id=c.shop_id WHERE session_id=? ORDER BY issued_at DESC''',(uid,))]
        for a in rows:a['expired']=a['expires_at']<iso()
        return {'items':rows}
    def progress(self):
        uid=self.uid()
        with DB_LOCK,db_connect() as db:
            rows=[dict(r) for r in db.execute('SELECT * FROM visits WHERE session_id=? ORDER BY at DESC',(uid,))]
        dates=set(r['day'] for r in rows);n=len(rows);distinct=len(set(r['shop_id'] for r in rows))
        streak=0;d=now().date()
        if d.isoformat() not in dates:d-=timedelta(days=1)
        while d.isoformat() in dates:streak+=1;d-=timedelta(days=1)
        badges=[{'id':'first','label':'첫 발견','emoji':'🧭','earned':n>=1},{'id':'trio','label':'시장 탐험가','emoji':'🏅','earned':distinct>=3},{'id':'five','label':'가락랜드 수집가','emoji':'🌟','earned':n>=5},{'id':'streak','label':'3일 연속','emoji':'🔥','earned':streak>=3}]
        return {'visits':rows,'totalVisits':n,'uniqueShops':distinct,'xp':n*40,'level':1+(n*40)//120,'streak':streak,'badges':badges}
    def orders(self):
        uid=self.uid()
        with DB_LOCK,db_connect() as db:rows=[dict(r) for r in db.execute('SELECT * FROM orders WHERE session_id=? ORDER BY created_at DESC',(uid,))]
        return {'items':rows}
    def demo_checkin(self,b):
        if not LOCAL_DEMO:return self.send_json(403,{'error':'시연모드가 비활성화되어 있습니다.'})
        shop=str(b.get('shopId',''))
        with DB_LOCK,db_connect() as db: valid=db.execute('SELECT 1 FROM merchant_meta WHERE shop_id=? AND is_demo=1',(shop,)).fetchone()
        if not valid:return self.send_json(403,{'error':'시연 매장만 사용할 수 있습니다.'})
        return self.save_visit(shop,'DEMO')
    def checkin(self,b):
        shop=str(b.get('shopId',''))
        if not verify_qr(b.get('qrToken',''),shop):return self.send_json(403,{'error':'현장 QR 코드가 만료되었거나 유효하지 않습니다.'})
        with DB_LOCK,db_connect() as db:s=db.execute('SELECT * FROM stores WHERE id=? AND status="published"',(shop,)).fetchone()
        if not s or s['coordinateStatus']!='verified' or s['latitude'] is None: return self.send_json(403,{'error':'검증된 매장 좌표가 없어 실방문 인증이 불가능합니다.'})
        try:lat=float(b['latitude']);lng=float(b['longitude']);accuracy=float(b['accuracy'])
        except (ValueError,TypeError,KeyError):raise ValueError('위치정보와 정확도가 필요합니다.')
        if not (-90<=lat<=90 and -180<=lng<=180 and 0<=accuracy<=75):raise ValueError('위치 정확도가 부족합니다. 개방된 장소에서 GPS를 다시 시도하세요.')
        dist=haversine(lat,lng,s['latitude'],s['longitude'])
        if dist>METERS_LIMIT:return self.send_json(403,{'error':'매장 주변에서만 인증할 수 있습니다.','distanceMeters':round(dist)})
        # NOTE: client GPS can be spoofed; beta is not fraud-proof.
        return self.save_visit(shop,'QR_GPS')
    def save_visit(self,shop,method):
        uid=self.uid();day=now().strftime('%Y-%m-%d')
        with DB_LOCK,db_connect() as db:
            cur=db.execute('INSERT OR IGNORE INTO visits VALUES (?,?,?,?,?)',(uid,shop,day,method,iso()))
            created=cur.rowcount==1;db.commit()
        return self.send_json(200,{'ok':True,'newVisit':created,'earnedXp':40 if created else 0,'message':'오늘의 방문 스탬프 획득!' if created else '오늘은 이미 스탬프를 받았습니다.'})
    def claim(self,b):
        uid=self.uid();cid=str(b.get('campaignId',''));dt=now()
        with DB_LOCK,db_connect() as db:
            db.execute('BEGIN IMMEDIATE')
            c=db.execute('SELECT * FROM campaigns WHERE id=? AND active=1',(cid,)).fetchone()
            if not c:return self.send_json(404,{'error':'쿠폰 행사가 없습니다.'})
            k=period_key(c['recurrence'],dt)
            prior=db.execute('SELECT id FROM wallet WHERE session_id=? AND campaign_id=? AND period=?',(uid,cid,k)).fetchone()
            if prior:return self.send_json(409,{'error':'이번 발행 주기에 이미 받았습니다.'})
            used=db.execute('SELECT COUNT(*) FROM wallet WHERE campaign_id=? AND period=?',(cid,k)).fetchone()[0]
            if used>=c['stock']:return self.send_json(409,{'error':'이번 발행 주기의 쿠폰이 소진되었습니다.'})
            code=secrets.token_hex(5).upper()
            coupon_id=secrets.token_urlsafe(12)
            db.execute('INSERT INTO wallet VALUES (?,?,?,?,?,?,?,?)',(coupon_id,uid,cid,k,code,iso(dt),iso(period_end(c['recurrence'],dt)),None));db.commit()
        return self.send_json(200,{'ok':True,'code':code,'period':k,'expiresAt':iso(period_end(c['recurrence'],dt)),'notice':'시연점 쿠폰은 실제 상점에서 사용할 수 없습니다.' if c['shop_id'].startswith('demo-') else '사용 조건을 매장에 확인해 주세요.'})
    def create_order(self,b):
        shop=str(b.get('shopId',''));name=str(b.get('menuName',''));mode=str(b.get('mode',''))
        if mode not in ('pickup','delivery_request'):raise ValueError('주문 유형이 올바르지 않습니다')
        try:qty=int(b.get('quantity',1))
        except (ValueError,TypeError):raise ValueError('수량이 올바르지 않습니다')
        if qty<1 or qty>10:raise ValueError('주문 수량은 1~10개입니다')
        uid=self.uid()
        with DB_LOCK,db_connect() as db:
            row=db.execute('SELECT menu_json,is_demo FROM merchant_meta WHERE shop_id=?',(shop,)).fetchone()
            if not row:raise ValueError('메뉴가 등록되지 않은 매장입니다')
            menu=next((x for x in json.loads(row['menu_json']) if x['name']==name),None)
            if not menu:raise ValueError('메뉴가 등록되어 있지 않습니다')
            amount=int(menu['price'])*qty
            if amount<0 or amount>1_000_000:raise ValueError('금액 오류')
            # Always demo-only until payment/merchant/fulfillment integration is configured.
            order_id='GQ-'+secrets.token_hex(4).upper()
            db.execute('INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?)',(order_id,uid,shop,name,qty,amount,mode,'DEMO_REQUESTED',str(b.get('note',''))[:240],iso(),iso()));db.commit()
        return self.send_json(200,{'ok':True,'orderId':order_id,'total':amount,'status':'DEMO_REQUESTED','notice':'실제 결제·배달이 접수된 주문이 아닌 베타 시연 기록입니다.'})
    def merchant_allowed(self,shop):
        token=self.headers.get('X-Garak-Merchant-Key','')
        if token and len(token)<=180:
            with DB_LOCK,db_connect() as db:r=db.execute('SELECT key_hash FROM merchant_keys WHERE shop_id=?',(shop,)).fetchone()
            if r and hmac.compare_digest(hashlib.sha256(token.encode()).hexdigest(),r['key_hash']):return True
        a=self.headers.get('X-Garak-Admin-Token','')
        return bool(a and hmac.compare_digest(a,ADMIN_TOKEN))
    def merchant_create(self,b):
        a=self.headers.get('X-Garak-Admin-Token','')
        if not a or not hmac.compare_digest(a,ADMIN_TOKEN):return self.send_json(403,{'error':'관리자 인증이 필요합니다'})
        shop=str(b.get('shopId',''))
        with DB_LOCK,db_connect() as db:
            if not db.execute('SELECT id FROM stores WHERE id=?',(shop,)).fetchone():raise ValueError('없는 매장입니다')
            key=secrets.token_urlsafe(30)
            db.execute('INSERT OR REPLACE INTO merchant_keys VALUES (?,?)',(shop,hashlib.sha256(key.encode()).hexdigest()));db.commit()
        return self.send_json(200,{'ok':True,'shopId':shop,'merchantKey':key,'warning':'비밀키는 이번에만 반환됩니다. 재발급하면 이전 키는 폐기됩니다.'})
    def merchant_qr(self,p):
        shop=p.get('shopId',[''])[0]
        if not self.merchant_allowed(shop):return self.send_json(403,{'error':'상인 인증이 필요합니다'})
        token=sign_qr(shop)
        # Query not logged by server custom log; HTTPS and privacy control necessary.
        scheme='https' if self.headers.get('X-Forwarded-Proto')=='https' else 'http'
        host=self.headers.get('Host','localhost')
        if not re.fullmatch(r'[A-Za-z0-9.:-]{1,150}',host):host='localhost'
        url=f'{scheme}://{host}/scan?shop={quote(shop)}&token={quote(token)}'
        try:
            import qrcode
            buf=io.BytesIO();qrcode.make(url).save(buf,format='PNG');data=base64.b64encode(buf.getvalue()).decode('ascii')
            image='data:image/png;base64,'+data
        except ImportError:image=None
        return self.send_json(200,{'ok':True,'shopId':shop,'token':token,'url':url,'image':image,'expiresSeconds':180})
    def campaign(self,b):
        shop=str(b.get('shopId',''))
        if not self.merchant_allowed(shop):return self.send_json(403,{'error':'상인 인증이 필요합니다'})
        rec=str(b.get('recurrence',''))
        if rec not in ('DAILY','WEEKLY','ONCE'):raise ValueError('발행 주기는 DAILY/WEEKLY/ONCE')
        title=str(b.get('title','')).strip()[:75];detail=str(b.get('details','')).strip()[:250];discount=str(b.get('discountLabel','')).strip()[:70]
        stock=int(b.get('stock',50))
        if not title or not discount or not (1<=stock<=100000):raise ValueError('제목·혜택·발행량을 확인하세요')
        cid='campaign-'+secrets.token_hex(6)
        with DB_LOCK,db_connect() as db:db.execute('INSERT INTO campaigns VALUES (?,?,?,?,?,?,?,?,?)',(cid,shop,title,detail,discount,rec,stock,1,iso()));db.commit()
        return self.send_json(200,{'ok':True,'campaignId':cid})
    def redeem(self,b):
        shop=str(b.get('shopId',''))
        if not self.merchant_allowed(shop):return self.send_json(403,{'error':'상인 인증이 필요합니다'})
        code=str(b.get('code','')).upper().strip()
        if not re.fullmatch('[0-9A-F]{10}',code):raise ValueError('쿠폰 코드 형식이 다릅니다')
        with DB_LOCK,db_connect() as db:
            db.execute('BEGIN IMMEDIATE')
            r=db.execute('SELECT w.id,w.expires_at,w.redeemed_at FROM wallet w JOIN campaigns c ON c.id=w.campaign_id WHERE w.code=? AND c.shop_id=?',(code,shop)).fetchone()
            if not r:return self.send_json(404,{'error':'이 점포에서 사용할 수 없는 코드입니다'})
            if r['redeemed_at']:return self.send_json(409,{'error':'이미 사용한 쿠폰입니다'})
            if r['expires_at']<iso():return self.send_json(409,{'error':'기간 만료된 쿠폰입니다'})
            db.execute('UPDATE wallet SET redeemed_at=? WHERE id=? AND redeemed_at IS NULL',(iso(),r['id']));db.commit()
        return self.send_json(200,{'ok':True,'status':'REDEEMED'})
    def order_status(self,b):
        shop=str(b.get('shopId',''))
        if not self.merchant_allowed(shop):return self.send_json(403,{'error':'상인 인증이 필요합니다'})
        status=str(b.get('status',''))
        if status not in ('DEMO_ACKNOWLEDGED','DEMO_CANCELLED'):raise ValueError('시연 승인 또는 취소만 지원합니다')
        with DB_LOCK,db_connect() as db:
            cur=db.execute('UPDATE orders SET status=?,updated_at=? WHERE id=? AND shop_id=?',(status,iso(),str(b.get('orderId','')),shop));db.commit()
        return self.send_json(200 if cur.rowcount else 404,{'ok':bool(cur.rowcount)})
    def metadata(self,b):
        a=self.headers.get('X-Garak-Admin-Token','')
        if not a or not hmac.compare_digest(a,ADMIN_TOKEN):return self.send_json(403,{'error':'관리자 인증 필요'})
        shop=str(b.get('shopId',''))
        menu=b.get('menu',[])
        if not isinstance(menu,list) or len(menu)>80:raise ValueError('최대 메뉴 80개')
        valid=[]
        for m in menu:
            if not isinstance(m,dict) or not str(m.get('name','')).strip() or len(str(m['name']))>65:raise ValueError('메뉴명 오류')
            price=int(m.get('price',-1))
            if not (0<=price<=1000000):raise ValueError('가격 오류')
            valid.append({'name':str(m['name']).strip(),'price':price})
        # Image paths must be uploaded through approved local deployment process, not arbitrary external URLs.
        with DB_LOCK,db_connect() as db:
            if not db.execute('SELECT 1 FROM stores WHERE id=?',(shop,)).fetchone():raise ValueError('등록되지 않은 매장')
            link=safe_http(b.get('deliveryUrl',''))
            db.execute('INSERT INTO merchant_meta (shop_id,hero,menu_image,reference_image,delivery_url,menu_json,is_demo) VALUES (?,?,?,?,?,?,?) ON CONFLICT(shop_id) DO UPDATE SET delivery_url=excluded.delivery_url, menu_json=excluded.menu_json',(shop,'','','',link,json.dumps(valid,ensure_ascii=False),0));db.commit()
        return self.send_json(200,{'ok':True})
    def merchant_profile(self,b):
        shop=str(b.get('shopId',''))
        if not self.merchant_allowed(shop):return self.send_json(403,{'error':'상인 인증이 필요합니다'})
        blog=safe_http(b.get('blogUrl',''))
        delivery=safe_http(b.get('deliveryUrl',''))
        if (b.get('blogUrl') and not blog) or (b.get('deliveryUrl') and not delivery):raise ValueError('HTTPS/HTTP 웹 주소만 입력하세요')
        menu=b.get('menu',[])
        if not isinstance(menu,list) or len(menu)>80:raise ValueError('메뉴는 80개 이내로 입력하세요')
        checked=[]
        for m in menu:
            if not isinstance(m,dict) or not (1<=len(str(m.get('name','')).strip())<=65):raise ValueError('메뉴 이름 오류')
            try:price=int(m['price'])
            except Exception:raise ValueError('메뉴 가격 오류')
            if not 0<=price<=1000000:raise ValueError('메뉴 가격 범위 오류')
            checked.append({'name':str(m['name']).strip(),'price':price})
        with DB_LOCK,db_connect() as db:
            if not db.execute('SELECT 1 FROM stores WHERE id=?',(shop,)).fetchone():raise ValueError('매장 등록 후 이용 가능합니다')
            db.execute('UPDATE stores SET "blogUrl"=? WHERE id=?',(blog,shop))
            db.execute('INSERT INTO merchant_meta (shop_id,hero,menu_image,reference_image,delivery_url,menu_json,is_demo) VALUES (?,?,?,?,?,?,?) ON CONFLICT(shop_id) DO UPDATE SET delivery_url=excluded.delivery_url,menu_json=excluded.menu_json',(shop,'','','',delivery,json.dumps(checked,ensure_ascii=False),int(shop.startswith('demo-'))));db.commit()
        return self.send_json(200,{'ok':True,'notice':'실제 사업자·계정 권한은 상용화 단계에서 추가 검증해야 합니다.'})
    def merchant_upload_photo(self,b):
        shop=str(b.get('shopId',''))
        if not self.merchant_allowed(shop):return self.send_json(403,{'error':'상인 인증이 필요합니다'})
        kind=str(b.get('kind',''))
        if kind not in ('reference','menu','hero'):raise ValueError('사진 종류는 reference/menu/hero')
        value=b.get('image','')
        if not isinstance(value,str) or len(value)>4_100_000:raise ValueError('사진 크기 제한(3MB)')
        try:
            from PIL import Image, ImageOps, UnidentifiedImageError
        except ImportError:raise ValueError('사진 등록에는 Pillow가 필요합니다. install_vision_windows.bat을 실행하세요.')
        try:
            raw=base64.b64decode(value.split(',',1)[-1],validate=True)
            if len(raw)>3_000_000:raise ValueError('사진 최대 3MB')
            im=Image.open(io.BytesIO(raw))
            if im.width*im.height>12_000_000:raise ValueError('사진 해상도는 1200만 픽셀 이하')
            if im.format not in ('JPEG','PNG','WEBP'):raise ValueError('JPG/PNG/WebP 사진만 가능')
            im=ImageOps.exif_transpose(im).convert('RGB');im.thumbnail((1400,1400))
        except ValueError:raise
        except Exception:raise ValueError('정상적인 이미지인지 확인해 주세요')
        folder=ROOT/'assets'/'store_photos';folder.mkdir(parents=True,exist_ok=True)
        # Avoid directory traversal and overwrite with a generated identifier.
        path=folder/(secrets.token_hex(12)+'.jpg')
        im.save(path,format='JPEG',quality=86,optimize=True)
        field={'reference':'reference_image','menu':'menu_image','hero':'hero'}[kind]
        rel='/assets/store_photos/'+path.name
        with DB_LOCK,db_connect() as db:
            if not db.execute('SELECT 1 FROM stores WHERE id=?',(shop,)).fetchone():
                path.unlink(missing_ok=True);raise ValueError('등록된 매장이 아닙니다')
            db.execute('INSERT OR IGNORE INTO merchant_meta (shop_id,hero,menu_image,reference_image,delivery_url,menu_json,is_demo) VALUES (?,?,?,?,?,?,?)',(shop,'','','','','[]',int(shop.startswith('demo-'))))
            db.execute(f'UPDATE merchant_meta SET {field}=? WHERE shop_id=?',(rel,shop));db.commit()
        return self.send_json(200,{'ok':True,'path':rel,'kind':kind,'note':'이 사진은 운영자가 권한을 확보한 자료여야 하며, 게시 승인이 별도로 필요합니다.'})
    def log_message(self,fmt,*args):
        # Avoid full scan?token=... access log; client coordinates are POST body only.
        p=urlsplit(self.path).path
        print('[access]', self.client_address[0], self.command, p, fmt%args if '%s' not in fmt else '',flush=True)

if __name__=='__main__':
    from http.server import ThreadingHTTPServer
    setup()
    def v5_campaign_scheduler():
        while True:
            try:
                if not hub_v8.is_disabled("/api/v5/merchant/broadcast"):
                    growth_v5.dispatch_due()
            except Exception as e:
                print('[market/v5] scheduled campaign simulation error:',str(e)[:150],flush=True)
            time.sleep(60)
    threading.Thread(target=v5_campaign_scheduler,daemon=True,name='v5-campaign-scheduler').start()
    print(f'GARAKLAND MARKET GROWTH v5 + AR QUEST: http://localhost:{PORT}  |  DEMO={LOCAL_DEMO}',flush=True)
    print('LOCAL ADMIN TOKEN:',ADMIN_TOKEN,flush=True)
    print('NOTE: LAN/mobile requires HTTPS (camera+GPS), verified locations and production security.',flush=True)
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
