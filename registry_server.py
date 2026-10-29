#!/usr/bin/env python3
"""GARAKLAND local server + SQLite store registry. Python standard library only.
Run: GARAK_ADMIN_TOKEN=<strong-random-token> python server.py
Without env token a random token is printed to the LOCAL console (development only).
"""
from __future__ import annotations
import json, os, sqlite3, secrets, hmac, re
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlsplit, parse_qs, urlparse, unquote
from db_adapter import DB_LOCK, backend_name, db_connect, table_columns

ROOT = Path(__file__).resolve().parent
DB = Path(os.environ.get('GARAK_DB_PATH', str(ROOT/'data'/'garakland.sqlite')))
PORT = int(os.environ.get('PORT', '8769'))
HOST = os.environ.get('GARAK_HOST', '127.0.0.1')
ADMIN_TOKEN = os.environ.get('GARAK_ADMIN_TOKEN') or secrets.token_urlsafe(24)
FIELDS = ('id','name','category','building','floor','room','description','address','latitude','longitude','coordinateStatus','blogUrl','websiteUrl','phone','sourceUrl','verifiedAt','status','featured','indoorX','indoorY')
BUILDINGS = {'sales','theme1','theme2','theme3','theme4','theme5','office','produce','seafood'}

def normalize(record):
    if not isinstance(record,dict): raise ValueError('매장 레코드는 JSON 객체여야 합니다.')
    s={key:record.get(key) for key in FIELDS}
    for k in FIELDS:
        if k not in ('latitude','longitude','indoorX','indoorY','featured'):
            s[k]=str(s[k] if s[k] is not None else '').strip()
    s['featured']=int(s['featured'] is True or str(s['featured']).lower() in ('true','1','yes'))
    for k in ('latitude','longitude','indoorX','indoorY'):
        if s[k] is None or s[k]=='':s[k]=None
        else:
            try: s[k]=float(s[k])
            except (ValueError,TypeError):raise ValueError(k+'이 숫자가 아닙니다.')
    if not re.fullmatch('[a-zA-Z0-9_-]{1,80}',s['id']):raise ValueError('id는 영문·숫자·-·_ 1~80자로 입력하세요.')
    if not s['name'] or len(s['name'])>130:raise ValueError('상호명은 1~130자 이내여야 합니다.')
    if s['building'] not in BUILDINGS:raise ValueError('올바른 building 코드가 아닙니다.')
    if (s['latitude'] is None)!=(s['longitude'] is None):raise ValueError('위도·경도는 동시에 입력하세요.')
    if s['latitude'] is not None and not (37.47<=s['latitude']<=37.52 and 127.08<=s['longitude']<=127.15):raise ValueError('가락시장 주변이 아닌 좌표입니다.')
    if s['coordinateStatus'] not in ('verified','approximate','unverified'):raise ValueError('coordinateStatus 값이 잘못되었습니다.')
    if any(s[k] is not None and not (0<=s[k]<=100) for k in ('indoorX','indoorY')):raise ValueError('도면의 실내 좌표는 0~100 사이여야 합니다.')
    if s['coordinateStatus']=='verified' and s['latitude'] is None:raise ValueError('검증된 좌표는 GPS 수치가 필요합니다.')
    if s['status'] not in ('published','needs_review','closed'):raise ValueError('status 값이 잘못되었습니다.')
    for k in ('blogUrl','websiteUrl','sourceUrl'):
        if s[k]:
            u=urlparse(s[k]);
            if u.scheme not in ('http','https') or not u.netloc:raise ValueError(k+'은 유효한 http/https URL이어야 합니다.')
    for k in ('category','floor','room','phone','verifiedAt'):s[k]=s[k][:120]
    s['description']=s['description'][:3000]
    s['address']=s['address'][:250]
    for k in ('blogUrl','websiteUrl','sourceUrl'):s[k]=s[k][:1200]
    return s

def init_db():
    with DB_LOCK, db_connect() as db:
        cols=','.join(f'"{x}" '+ ('REAL' if x in ('latitude','longitude','indoorX','indoorY') else 'INTEGER' if x=='featured' else 'TEXT') for x in FIELDS)
        db.execute('CREATE TABLE IF NOT EXISTS stores ('+cols+', PRIMARY KEY ("id"))')
        existing=table_columns(db,'stores')
        for extra in ('indoorX','indoorY'):
            if extra not in existing:db.execute('ALTER TABLE stores ADD COLUMN '+extra+' REAL')
        db.execute('CREATE INDEX IF NOT EXISTS idx_store_building ON stores(building,floor)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_store_category ON stores(category)')
        cnt=db.execute('SELECT COUNT(*) FROM stores').fetchone()[0]
        if cnt==0:
            seed=json.loads((ROOT/'data'/'shops.seed.json').read_text(encoding='utf-8'))
            for raw in seed:upsert(db, normalize(raw))
        db.commit()

def upsert(db,s):
    columns=','.join('"'+k+'"' for k in FIELDS)
    bind=','.join('?' for _ in FIELDS)
    assignments=','.join(f'"{k}"=excluded."{k}"' for k in FIELDS if k!='id')
    db.execute(f'INSERT INTO stores ({columns}) VALUES ({bind}) ON CONFLICT(id) DO UPDATE SET {assignments}', tuple(s[x] for x in FIELDS))

def all_stores(limit,offset=0):
    with DB_LOCK, db_connect() as db:
        rows=db.execute('SELECT * FROM stores ORDER BY name LIMIT ? OFFSET ?', (limit,offset)).fetchall()
        count=db.execute('SELECT COUNT(*) FROM stores').fetchone()[0]
    return [dict(r) | {'featured':bool(r['featured'])} for r in rows],count

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def do_GET(self):
        u=urlsplit(self.path)
        if u.path=='/api/health':return self.send_json(200,{'ok':True,'version':'7.0','mode':backend_name()})
        if u.path=='/api/stores':
            params=parse_qs(u.query)
            try: limit=min(10000,max(1,int(params.get('limit',['1000'])[0])));offset=max(0,int(params.get('offset',['0'])[0]))
            except ValueError:return self.send_json(400,{'error':'잘못된 페이지 설정'})
            items,count=all_stores(limit,offset);return self.send_json(200,{'items':items,'total':count,'limit':limit,'offset':offset})
        if u.path=='/':self.path='/index.html'
        decoded=unquote(u.path)
        if (decoded.replace('//','/').startswith('/data/garakland.sqlite') or '/.' in decoded or decoded.endswith(('.py','.bat','.sh','.sqlite','.sqlite-wal','.sqlite-shm')) or decoded.startswith(('/tests/','/docs/'))):
            return self.send_error(404)
        return super().do_GET()
    def do_POST(self):
        if urlsplit(self.path).path!='/api/import':return self.send_json(404,{'error':'API 없음'})
        supplied=self.headers.get('X-Garak-Admin-Token','')
        if not supplied or not hmac.compare_digest(supplied,ADMIN_TOKEN):return self.send_json(403,{'error':'관리자 토큰이 올바르지 않습니다.'})
        try: length=int(self.headers.get('Content-Length','0'))
        except ValueError:return self.send_json(400,{'error':'Content-Length 오류'})
        if length<=0 or length>12_000_000:return self.send_json(413,{'error':'본문 최대 12MB'})
        try:
            body=json.loads(self.rfile.read(length))
            items=body.get('items')
            if not isinstance(items,list) or not 1<=len(items)<=5000:raise ValueError('1~5000개 매장 배열이 필요합니다.')
            validated=[];seen=set()
            for i,row in enumerate(items):
                try: norm=normalize(row)
                except ValueError as err:raise ValueError(f'{i+1}번째 매장: {err}')
                if norm['id'] in seen:raise ValueError(f'CSV 내 중복 ID: {norm["id"]}')
                seen.add(norm['id']);validated.append(norm)
            with DB_LOCK, db_connect() as db:
                for s in validated:upsert(db,s)
                db.commit()
            all_items,total=all_stores(10000)
            return self.send_json(200,{'ok':True,'updated':len(validated),'items':all_items,'total':total})
        except (ValueError,TypeError,json.JSONDecodeError) as err:return self.send_json(400,{'error':str(err)})
        except sqlite3.Error:return self.send_json(500,{'error':'DB 쓰기 오류'})
    def send_json(self,status,obj):
        raw=json.dumps(obj,ensure_ascii=False).encode('utf-8');self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
    def end_headers(self):
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','strict-origin-when-cross-origin')
        super().end_headers()

if __name__=='__main__':
    init_db()
    print('\nGARAKLAND Google Maps + Store Registry',flush=True)
    print('URL: http://localhost:'+str(PORT),flush=True)
    print('LOCAL ADMIN TOKEN (keep private): '+ADMIN_TOKEN,flush=True)
    print('For production: set GARAK_ADMIN_TOKEN, HTTPS/reverse proxy, and restrict Google Maps API key referrers.\n',flush=True)
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
