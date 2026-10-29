"""GARAK LAND v5 market growth add-on.
No payment collection in this beta. Voucher amounts are simulation-only credits.
Only opted-in recipients can be queued for marketing; live sends off by default.
"""
from __future__ import annotations
import datetime as dt
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode
from registry_server import DB_LOCK, db_connect, ADMIN_TOKEN

KST=dt.timezone(dt.timedelta(hours=9))
CHANNELS={'email','sms','kakao'}
GIFT_TIERS={30000:28800,50000:47500,100000:94000} # simulated illustrative figures
DEMO_MODE=os.environ.get('GARAK_V5_DEMO','1')=='1'
LIVE_MODE=os.environ.get('GARAK_V5_LIVE_MARKETING','0')=='1'
MARKET_NAME='가락랜드 연합 시연권 (비공식)'
FALLBACK='서울특별시 송파구 양재대로 932 가락시장'
OPT_KEY=os.environ.get('GARAK_V5_OPT_OUT_SIGNING_KEY') or secrets.token_urlsafe(36)

def now():return dt.datetime.now(KST)
def iso(x=None):return (x or now()).isoformat(timespec='seconds')
def parse_iso(value):
    try:
        x=dt.datetime.fromisoformat(str(value));
        if x.tzinfo is None: x=x.replace(tzinfo=KST)
        return x.astimezone(KST)
    except (ValueError,TypeError):raise ValueError('시작/종료 일정은 ISO 날짜로 입력하세요')
def check_int(v, minimum, maximum, label):
    if type(v) is bool: raise ValueError(label+' 숫자 오류')
    try: n=int(v)
    except (ValueError,TypeError):raise ValueError(label+' 숫자 오류')
    if n<minimum or n>maximum:raise ValueError(f'{label}: {minimum}~{maximum} 범위만 허용')
    return n

def check_text(v,max_len=140,label='텍스트'):
    if not isinstance(v,str) or not v.strip() or len(v)>max_len:raise ValueError(f'{label} 길이 오류(1~{max_len})')
    return v.strip()

def keyid(prefix):return prefix+'-'+secrets.token_hex(9)
def secret_code():return secrets.token_hex(7).upper()
def auth_admin(h):
    token=h.headers.get('X-Garak-Admin-Token','')
    return bool(token and hmac.compare_digest(token,ADMIN_TOKEN))
def authenticated(h,shop):return h.merchant_allowed(shop)

def setup():
    with DB_LOCK, db_connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS v5_offers(
          id TEXT PRIMARY KEY,shop_id TEXT NOT NULL,item TEXT NOT NULL,description TEXT NOT NULL,
          original_price INTEGER NOT NULL,offer_price INTEGER NOT NULL,limit_count INTEGER NOT NULL,
          starts_at TEXT NOT NULL,ends_at TEXT NOT NULL,enabled INTEGER NOT NULL DEFAULT 1,
          image TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS ix_v5_offers_shop ON v5_offers(shop_id,starts_at,ends_at);
        CREATE TABLE IF NOT EXISTS v5_tickets(
          id TEXT PRIMARY KEY,offer_id TEXT NOT NULL,session_id TEXT NOT NULL,code TEXT NOT NULL UNIQUE,
          created_at TEXT NOT NULL,redeemed_at TEXT, UNIQUE(offer_id,session_id));
        CREATE TABLE IF NOT EXISTS v5_participants(
          shop_id TEXT PRIMARY KEY,approved INTEGER NOT NULL DEFAULT 0,approved_at TEXT,
          proof_note TEXT NOT NULL DEFAULT '',demo INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS v5_cards(
          id TEXT PRIMARY KEY,owner TEXT NOT NULL,face_value INTEGER NOT NULL,simulated_paid INTEGER NOT NULL,
          balance INTEGER NOT NULL,created_at TEXT NOT NULL,mode TEXT NOT NULL CHECK(mode='DEMO'),pin_hash TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS v5_ledger(
          id TEXT PRIMARY KEY,card_id TEXT NOT NULL,shop_id TEXT,kind TEXT NOT NULL,amount INTEGER NOT NULL,
          before_balance INTEGER NOT NULL,after_balance INTEGER NOT NULL,
          ref TEXT NOT NULL UNIQUE,original_id TEXT,created_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS ix_v5_ledger_card ON v5_ledger(card_id,created_at);
        CREATE TABLE IF NOT EXISTS v5_contacts(
          session_id TEXT PRIMARY KEY,email TEXT NOT NULL DEFAULT '',phone TEXT NOT NULL DEFAULT '',
          email_opt INTEGER NOT NULL DEFAULT 0,sms_opt INTEGER NOT NULL DEFAULT 0,
          kakao_opt INTEGER NOT NULL DEFAULT 0,kakao_friend INTEGER NOT NULL DEFAULT 0,
          updated_at TEXT NOT NULL,source TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS v5_consent_events(
          id TEXT PRIMARY KEY,session_id TEXT NOT NULL,channel TEXT NOT NULL,allowed INTEGER NOT NULL,
          happened_at TEXT NOT NULL,source TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS v5_broadcasts(
          id TEXT PRIMARY KEY,shop_id TEXT NOT NULL,offer_id TEXT,channel TEXT NOT NULL,
          title TEXT NOT NULL,message TEXT NOT NULL,send_at TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'SCHEDULED',created_at TEXT NOT NULL,
          CHECK(channel IN ('email','sms','kakao')));
        CREATE TABLE IF NOT EXISTS v5_outbox(
          id TEXT PRIMARY KEY,broadcast_id TEXT NOT NULL,recipient TEXT NOT NULL,
          channel TEXT NOT NULL,status TEXT NOT NULL,processed_at TEXT NOT NULL,
          UNIQUE(broadcast_id,recipient));
        ''')
        count=db.execute('SELECT count(*) FROM v5_offers').fetchone()[0]
        if not count:
            start=(now()-dt.timedelta(days=1)).isoformat(timespec='seconds')
            end=(now()+dt.timedelta(days=60)).isoformat(timespec='seconds')
            samples=[
            ('V5-DEMO-FRUIT','demo-fruit','제철 딸기 1팩','[가상 시연] 제철 과일 특가 체험',12500,9900,100,'/assets/v5/fruit.webp'),
            ('V5-DEMO-SEA','demo-sea','싱싱한 수산물 기획팩','[가상 시연] 오늘의 수산 식탁',28000,23800,60,'/assets/v5/seafood.webp'),
            ('V5-DEMO-MEAT','demo-meat','축산 특선 모둠','[가상 시연] 정육 기획전',39000,33900,40,'/assets/v5/meat.webp'),
            ('V5-DEMO-KITCHEN','demo-kitchen','가락한상 반찬 세트','[가상 시연] 식탁 한 끼 준비',17900,14900,70,'/assets/v5/market.webp')]
            for identifier,shop,item,detail,original,sale,stock,img in samples:
                db.execute('INSERT INTO v5_offers VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(identifier,shop,item,detail,original,sale,stock,start,end,1,img,iso()))
        for shop in ('demo-fruit','demo-sea','demo-meat','demo-kitchen'):
            db.execute('INSERT OR IGNORE INTO v5_participants VALUES(?,1,?,?,1)',(shop,iso(),'시연용 가상 가맹점'))
        db.commit()

def query_offers(db,all_offers=False):
    sql='''SELECT o.*,s.name AS shop_name,s.category AS category,s.building,s.floor,s.room,
              s.address,s.latitude,s.longitude,s.coordinateStatus,
              (SELECT COUNT(*) FROM v5_tickets t WHERE t.offer_id=o.id) AS claimed
            FROM v5_offers o JOIN stores s ON s.id=o.shop_id'''
    rows=[dict(r) for r in db.execute(sql+' ORDER BY o.created_at DESC')]
    stamp=now()
    for r in rows:
        r['is_demo']=r['shop_id'].startswith('demo-')
        r['is_active']=bool(r['enabled'] and parse_iso(r['starts_at'])<=stamp<=parse_iso(r['ends_at']) and r['claimed']<r['limit_count'])
        r['discount_percent']=round((r['original_price']-r['offer_price'])/r['original_price']*100) if r['original_price'] else 0
        r['directions_url']=directions(r)
        r['verified_location']=bool(r['coordinateStatus']=='verified' and r['latitude'] is not None and r['longitude'] is not None and not r['is_demo'])
    return rows if all_offers else [r for r in rows if r['is_active'] and (os.environ.get('GARAK_V7_MODE','demo')!='review' or not r['is_demo'])]

def directions(row):
    verified=(row.get('coordinateStatus')=='verified' and row.get('latitude') is not None and row.get('longitude') is not None and not row.get('is_demo'))
    dest=f"{row['latitude']},{row['longitude']}" if verified else FALLBACK
    return 'https://www.google.com/maps/dir/?'+urlencode({'api':'1','destination':dest,'travelmode':'walking','dir_action':'navigate'})

def unsubscribe_token(session_id):
    payload=base64.urlsafe_b64encode(session_id.encode()).decode().rstrip('=')
    signature=hmac.new(OPT_KEY.encode(),payload.encode(),hashlib.sha256).hexdigest()[:32]
    return payload+'.'+signature

def token_uid(token):
    if not isinstance(token,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{20,100}\.[a-f0-9]{32}',token):return None
    body,sig=token.rsplit('.',1)
    expect=hmac.new(OPT_KEY.encode(),body.encode(),hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(sig,expect):return None
    try:
        uid=base64.urlsafe_b64decode(body+'='*((-len(body))%4)).decode()
    except (ValueError,UnicodeError):return None
    return uid if re.fullmatch(r'[a-zA-Z0-9_-]{32,64}',uid) else None

def get(h,path,p):
    if path=='/api/v5/public':
        with DB_LOCK,db_connect() as db:
            offers=query_offers(db)
            registered=db.execute('SELECT COUNT(*) FROM v5_participants WHERE approved=1 AND demo=0').fetchone()[0]
            merchant_stores=[dict(r) for r in db.execute('SELECT id,name,category FROM stores WHERE status="published" ORDER BY name LIMIT 5000')]
        return h.send_json(200,{'offers':offers,'tiers':[{'face':f,'samplePrice':price} for f,price in GIFT_TIERS.items()],
           'memberShops':registered,'merchantStores':merchant_stores,'giftcardName':MARKET_NAME,'demo':True,'moneyEnabled':False,
           'marketingMode':'simulation' if not LIVE_MODE else 'configured-live','now':iso()})
    if path=='/api/v5/me':
        uid=h.uid()
        with DB_LOCK,db_connect() as db:
            tickets=[dict(r) for r in db.execute('''SELECT t.*,o.item,o.shop_id,o.offer_price,o.ends_at,s.name AS shop_name
               FROM v5_tickets t JOIN v5_offers o ON t.offer_id=o.id JOIN stores s ON o.shop_id=s.id
               WHERE t.session_id=? ORDER BY t.created_at DESC''',(uid,))]
            cards=[dict(r) for r in db.execute('SELECT id,face_value,simulated_paid,balance,created_at,mode FROM v5_cards WHERE owner=? ORDER BY created_at DESC',(uid,))]
            contact=db.execute('SELECT email,phone,email_opt,sms_opt,kakao_opt,kakao_friend,updated_at FROM v5_contacts WHERE session_id=?',(uid,)).fetchone()
            history=[dict(r) for r in db.execute('''SELECT l.* FROM v5_ledger l JOIN v5_cards c ON c.id=l.card_id
                WHERE c.owner=? ORDER BY l.created_at DESC LIMIT 100''',(uid,))]
        return h.send_json(200,{'tickets':tickets,'cards':cards,'contact':dict(contact) if contact else None,'ledger':history})
    if path=='/api/v5/merchant':
        shop=str(p.get('shopId',[''])[0])
        if not authenticated(h,shop):return h.send_json(403,{'error':'해당 매장 상인 인증이 필요합니다'})
        with DB_LOCK,db_connect() as db:
            offers=[r for r in query_offers(db,True) if r['shop_id']==shop]
            campaigns=[dict(r) for r in db.execute('SELECT * FROM v5_broadcasts WHERE shop_id=? ORDER BY send_at DESC',(shop,))]
            stats=db.execute('''SELECT COUNT(*) AS usages,COALESCE(SUM(-amount),0) AS simulated_sales FROM v5_ledger WHERE shop_id=? AND kind='REDEEM' ''',(shop,)).fetchone()
            redeemed=db.execute('''SELECT COUNT(*) FROM v5_tickets t JOIN v5_offers o ON o.id=t.offer_id
                             WHERE o.shop_id=? AND t.redeemed_at IS NOT NULL''',(shop,)).fetchone()[0]
            member=db.execute('SELECT approved,demo FROM v5_participants WHERE shop_id=?',(shop,)).fetchone()
        return h.send_json(200,{'offers':offers,'broadcasts':campaigns,'redeemedTickets':redeemed,
             'voucherUsage':dict(stats),'approved':bool(member and member['approved']),'demo':bool(member and member['demo'])})
    if path=='/api/v5/my-unsubscribe-link':
        uid=h.uid()
        return h.send_json(200,{'token':unsubscribe_token(uid),'note':'유효한 수신거부 확인코드는 서명되어 있습니다'})
    if path=='/api/v5/admin':
        if not auth_admin(h):return h.send_json(403,{'error':'관리자 권한이 필요합니다'})
        with DB_LOCK,db_connect() as db:
            counts={name:db.execute('SELECT COUNT(*) FROM '+name).fetchone()[0] for name in ('v5_offers','v5_tickets','v5_cards','v5_broadcasts','v5_outbox')}
            members=[dict(r) for r in db.execute('SELECT * FROM v5_participants')]
        return h.send_json(200,{'counts':counts,'members':members,'moneyEnabled':False,'liveMarketing':LIVE_MODE})
    return False

def post(h,path,b):
    uid=h.uid()
    if path=='/api/v5/offers/claim':
        oid=check_text(b.get('offerId'),90,'행사 ID')
        with DB_LOCK,db_connect() as db:
            db.execute('BEGIN IMMEDIATE')
            o=db.execute('SELECT * FROM v5_offers WHERE id=?',(oid,)).fetchone()
            if not o:return h.send_json(404,{'error':'행사를 찾을 수 없습니다'})
            if not (o['enabled'] and parse_iso(o['starts_at'])<=now()<=parse_iso(o['ends_at'])):
                return h.send_json(409,{'error':'아직 시작하지 않았거나 종료된 행사입니다'})
            if db.execute('SELECT 1 FROM v5_tickets WHERE offer_id=? AND session_id=?',(oid,uid)).fetchone():
                return h.send_json(409,{'error':'이번 상품 쿠폰은 이미 받았습니다'})
            count=db.execute('SELECT count(*) FROM v5_tickets WHERE offer_id=?',(oid,)).fetchone()[0]
            if count>=o['limit_count']:return h.send_json(409,{'error':'한정 수량이 종료되었습니다'})
            token=secret_code();db.execute('INSERT INTO v5_tickets VALUES(?,?,?,?,?,NULL)',(keyid('TK'),oid,uid,token,iso()));db.commit()
        return h.send_json(200,{'ok':True,'code':token,'offerId':oid,'notice':'가상 매장의 할인은 실제로 사용할 수 없는 시연입니다.' if o['shop_id'].startswith('demo-') else '상인에게 코드를 제시해 주세요'})
    if path=='/api/v5/merchant/offer':
        shop=check_text(b.get('shopId'),100,'매장')
        if not authenticated(h,shop):return h.send_json(403,{'error':'상인 키가 필요합니다'})
        item=check_text(b.get('item'),100,'상품명')
        detail=check_text(b.get('description','쿠폰 특가 안내'),300,'특가 설명')
        orig=check_int(b.get('originalPrice'),100,10000000,'정상가')
        sale=check_int(b.get('offerPrice'),100,orig-1,'특가')
        stock=check_int(b.get('limitCount'),1,100000,'발급 수량')
        start=parse_iso(b.get('startsAt'));end=parse_iso(b.get('endsAt'))
        if end<=start or end-start>dt.timedelta(days=366):raise ValueError('행사 기간은 1일 미만이거나 최대 366일 이내여야 합니다')
        with DB_LOCK,db_connect() as db:
            if not db.execute('SELECT id FROM stores WHERE id=?',(shop,)).fetchone():raise ValueError('없는 매장입니다')
            identifier=keyid('OF');db.execute('INSERT INTO v5_offers VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
               (identifier,shop,item,detail,orig,sale,stock,iso(start),iso(end),1,'',iso()));db.commit()
        return h.send_json(200,{'ok':True,'offerId':identifier,'message':'예약 발행 완료. 서버가 실행 중인 동안 정해진 시간에 자동 노출됩니다.'})
    if path=='/api/v5/merchant/offer/cancel':
        shop=check_text(b.get('shopId'),100,'매장')
        if not authenticated(h,shop):return h.send_json(403,{'error':'상인 인증 필요'})
        oid=check_text(b.get('offerId'),90,'행사 ID')
        with DB_LOCK,db_connect() as db:
            row=db.execute('UPDATE v5_offers SET enabled=0 WHERE id=? AND shop_id=? AND enabled=1',(oid,shop))
            db.commit()
        if row.rowcount==0:return h.send_json(404,{'error':'진행 중인 행사가 없습니다'})
        return h.send_json(200,{'ok':True,'note':'신규 쿠폰 발행을 중단했습니다. 기존 발급분 이용 조건은 별도로 공지하세요.'})
    if path=='/api/v5/merchant/broadcast/cancel':
        shop=check_text(b.get('shopId'),100,'매장')
        if not authenticated(h,shop):return h.send_json(403,{'error':'상인 인증 필요'})
        cid=check_text(b.get('broadcastId'),90,'광고 ID')
        with DB_LOCK,db_connect() as db:
            row=db.execute('UPDATE v5_broadcasts SET status="CANCELLED" WHERE id=? AND shop_id=? AND status="SCHEDULED"',(cid,shop))
            db.commit()
        if row.rowcount==0:return h.send_json(409,{'error':'예약 발송 상태가 아니거나 권한이 없습니다'})
        return h.send_json(200,{'ok':True,'note':'아직 발송되지 않은 캠페인을 취소했습니다'})
    if path=='/api/v5/merchant/offer/redeem':
        shop=check_text(b.get('shopId'),100,'매장')
        if not authenticated(h,shop):return h.send_json(403,{'error':'상인 키가 필요합니다'})
        code=check_text(b.get('code'),30,'쿠폰 번호')
        with DB_LOCK,db_connect() as db:
            db.execute('BEGIN IMMEDIATE')
            rec=db.execute('''SELECT t.*,o.shop_id,o.ends_at,o.starts_at FROM v5_tickets t
               JOIN v5_offers o ON o.id=t.offer_id WHERE t.code=?''',(code,)).fetchone()
            if not rec or rec['shop_id']!=shop:return h.send_json(404,{'error':'이 매장의 쿠폰이 아닙니다'})
            if rec['redeemed_at']:return h.send_json(409,{'error':'이미 사용 처리된 쿠폰입니다'})
            if not parse_iso(rec['starts_at'])<=now()<=parse_iso(rec['ends_at']):return h.send_json(409,{'error':'유효기간 외 쿠폰입니다'})
            db.execute('UPDATE v5_tickets SET redeemed_at=? WHERE id=?',(iso(),rec['id']));db.commit()
        return h.send_json(200,{'ok':True,'redeemed':True,'shopId':shop})
    if path=='/api/v5/gift/demo-purchase':
        if not DEMO_MODE:return h.send_json(403,{'error':'실제 결제는 이 베타에서 지원하지 않습니다'})
        face=check_int(b.get('face'),30000,100000,'권면 금액')
        if face not in GIFT_TIERS:raise ValueError('정해진 상품권 액면만 선택할 수 있습니다')
        card_id=keyid('GV')
        pin=secrets.token_hex(8).upper()
        pin_hash=hashlib.sha256((card_id+':'+pin).encode()).hexdigest()
        paid=GIFT_TIERS[face]
        with DB_LOCK,db_connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('INSERT INTO v5_cards VALUES(?,?,?,?,?,?,?,?)',(card_id,uid,face,paid,face,iso(),'DEMO',pin_hash))
            db.execute('INSERT INTO v5_ledger VALUES(?,?,?,?,?,?,?,?,?,?)',
                 (keyid('LG'),card_id,None,'DEMO_ISSUE',face,0,face,keyid('DEMO_ISSUE'),None,iso()))
            db.commit()
        return h.send_json(200,{'ok':True,'cardId':card_id,'face':face,'simulatedPrice':paid,'balance':face,'redeemPin':pin,
          'notice':'시연용 포인트입니다. 돈이 결제되거나 실제 상품권이 발행된 것이 아닙니다.'})
    if path=='/api/v5/merchant/gift/redeem':
        shop=check_text(b.get('shopId'),100,'매장')
        if not authenticated(h,shop):return h.send_json(403,{'error':'상인 키가 필요합니다'})
        card=check_text(b.get('cardId'),80,'상품권 번호')
        pin=check_text(b.get('pin'),32,'상품권 확인코드')
        amt=check_int(b.get('amount'),100,1000000,'사용액')
        idem=check_text(b.get('requestId'),120,'요청 고유번호')
        with DB_LOCK,db_connect() as db:
            db.execute('BEGIN IMMEDIATE')
            part=db.execute('SELECT approved,demo FROM v5_participants WHERE shop_id=?',(shop,)).fetchone()
            if not part or not part['approved']:return h.send_json(403,{'error':'상품권 가맹 승인 매장만 사용할 수 있습니다'})
            record=db.execute('SELECT * FROM v5_cards WHERE id=?',(card,)).fetchone()
            if not record:return h.send_json(404,{'error':'카드가 없습니다'})
            if not hmac.compare_digest(hashlib.sha256((card+':'+pin).encode()).hexdigest(),record['pin_hash']):
                return h.send_json(403,{'error':'상품권 확인코드가 올바르지 않습니다'})
            prior=db.execute('SELECT * FROM v5_ledger WHERE ref=?',(idem,)).fetchone()
            if prior:
                if prior['card_id']!=card or prior['shop_id']!=shop or prior['amount']!=-amt:
                    return h.send_json(409,{'error':'같은 요청 ID의 다른 거래가 있습니다'})
                return h.send_json(200,{'ok':True,'idempotent':True,'balance':prior['after_balance']})
            if amt>record['balance']:return h.send_json(409,{'error':'잔액이 부족합니다'})
            balance=record['balance']-amt
            db.execute('UPDATE v5_cards SET balance=? WHERE id=?',(balance,card))
            db.execute('INSERT INTO v5_ledger VALUES(?,?,?,?,?,?,?,?,?,?)',
                       (keyid('LG'),card,shop,'REDEEM',-amt,record['balance'],balance,idem,None,iso()))
            db.commit()
        return h.send_json(200,{'ok':True,'balance':balance,'notice':'모의 사용 승인입니다. 실제 정산·결제는 발생하지 않았습니다.'})
    if path=='/api/v5/admin/gift/refund':
        if not auth_admin(h):return h.send_json(403,{'error':'관리자 인증 필요'})
        target=check_text(b.get('ledgerId'),80,'거래')
        with DB_LOCK,db_connect() as db:
            db.execute('BEGIN IMMEDIATE')
            original=db.execute('SELECT * FROM v5_ledger WHERE id=? AND kind="REDEEM"',(target,)).fetchone()
            if not original: return h.send_json(404,{'error':'환불 대상 사용거래가 없습니다'})
            if db.execute('SELECT 1 FROM v5_ledger WHERE original_id=? AND kind="REVERSAL"',(target,)).fetchone():
                return h.send_json(409,{'error':'이미 취소된 사용거래입니다'})
            account=db.execute('SELECT balance FROM v5_cards WHERE id=?',(original['card_id'],)).fetchone()
            amount=-original['amount'];balance=account['balance']+amount
            db.execute('UPDATE v5_cards SET balance=? WHERE id=?',(balance,original['card_id']))
            db.execute('INSERT INTO v5_ledger VALUES(?,?,?,?,?,?,?,?,?,?)',
                  (keyid('LG'),original['card_id'],original['shop_id'],'REVERSAL',amount,account['balance'],balance,keyid('REV'),target,iso()))
            db.commit()
        return h.send_json(200,{'ok':True,'balance':balance,'notice':'시연 거래 취소 완료'})
    if path=='/api/v5/admin/member':
        if not auth_admin(h):return h.send_json(403,{'error':'관리자 인증 필요'})
        shop=check_text(b.get('shopId'),100,'매장')
        approved=1 if b.get('approved') is True else 0
        note=check_text(b.get('proofNote','현장 계약·검증 확인 필요'),240,'가맹 확인')
        with DB_LOCK,db_connect() as db:
            if not db.execute('SELECT 1 FROM stores WHERE id=?',(shop,)).fetchone():raise ValueError('없는 점포')
            db.execute('INSERT INTO v5_participants VALUES (?,?,?,?,?) ON CONFLICT(shop_id) DO UPDATE SET approved=excluded.approved,approved_at=excluded.approved_at,proof_note=excluded.proof_note',
              (shop,approved,iso(),note,int(shop.startswith('demo-'))));db.commit()
        return h.send_json(200,{'ok':True,'shopId':shop,'approved':bool(approved),'demo':shop.startswith('demo-')})
    if path=='/api/v5/optout':
        uid_token=token_uid(b.get('token'))
        if not uid_token:return h.send_json(403,{'error':'수신거부 코드가 올바르지 않습니다'})
        channel=str(b.get('channel','all'))
        if channel not in CHANNELS|{'all'}:raise ValueError('수신거부 채널 오류')
        chans=CHANNELS if channel=='all' else {channel}
        with DB_LOCK,db_connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if not db.execute('SELECT 1 FROM v5_contacts WHERE session_id=?',(uid_token,)).fetchone():return h.send_json(404,{'error':'등록된 수신 설정이 없습니다'})
            for ch in chans:
                db.execute(f'UPDATE v5_contacts SET {ch}_opt=0,updated_at=? WHERE session_id=?',(iso(),uid_token))
                db.execute('INSERT INTO v5_consent_events VALUES(?,?,?,?,?,?)',(keyid('CS'),uid_token,ch,0,iso(),'signed_optout'))
            db.commit()
        return h.send_json(200,{'ok':True,'withdrawn':sorted(chans),'message':'선택한 광고 수신이 철회되었습니다'})
    if path=='/api/v5/admin/dispatch-live':
        if not auth_admin(h):return h.send_json(403,{'error':'관리자 인증 필요'})
        if b.get('liveApproved') is not True:return h.send_json(403,{'error':'실발송 승인 확인이 필요합니다'})
        if not LIVE_MODE or os.environ.get('GARAK_V5_APPROVED_LIVE_SEND')!='YES':
            return h.send_json(403,{'error':'실발송 비활성화: 공급사 계약·법적 요건·안정성 점검 후에만 환경변수를 설정하세요'})
        if quiet_hours(now()):return h.send_json(409,{'error':'광고 야간 발송 제한 시간입니다'})
        cid=check_text(b.get('broadcastId'),90,'캠페인')
        limit=check_int(b.get('limit',5),1,20,'전송 최대 인원')
        return h.send_json(200,manual_live_dispatch(cid,limit))
    if path=='/api/v5/consent':
        email=str(b.get('email','')).strip();phone=re.sub(r'[ -]','',str(b.get('phone','')))
        choices={ch:b.get(ch+'Opt') is True for ch in CHANNELS}
        if email and not re.fullmatch(r'[^@\s]{1,64}@[^@\s]{1,128}\.[^@\s]{2,30}',email):raise ValueError('이메일 주소 오류')
        if phone and not re.fullmatch(r'01[0-9]{8,9}',phone):raise ValueError('휴대전화 번호 오류')
        if choices['email'] and not email:raise ValueError('메일 수신동의에는 이메일이 필요합니다')
        if (choices['sms'] or choices['kakao']) and not phone:raise ValueError('문자/카카오 수신동의에는 휴대전화가 필요합니다')
        # Provider must also establish Kakao channel friend/qualified marketing consent.
        friend=b.get('kakaoFriend') is True
        with DB_LOCK,db_connect() as db:
            before=db.execute('SELECT * FROM v5_contacts WHERE session_id=?',(uid,)).fetchone()
            db.execute('''INSERT INTO v5_contacts VALUES (?,?,?,?,?,?,?,?,?)
                 ON CONFLICT(session_id) DO UPDATE SET email=excluded.email,phone=excluded.phone,
                 email_opt=excluded.email_opt,sms_opt=excluded.sms_opt,kakao_opt=excluded.kakao_opt,
                 kakao_friend=excluded.kakao_friend,updated_at=excluded.updated_at,source=excluded.source''',
                 (uid,email,phone,int(choices['email']),int(choices['sms']),int(choices['kakao']),int(friend),iso(),'user_self_service'))
            for ch in CHANNELS:
                prev=bool(before[ch+'_opt']) if before else False
                if prev!=choices[ch]:db.execute('INSERT INTO v5_consent_events VALUES(?,?,?,?,?,?)',(keyid('CS'),uid,ch,int(choices[ch]),iso(),'user_self_service'))
            db.commit()
        return h.send_json(200,{'ok':True,'choices':choices,'notice':'광고 수신 동의는 언제든 변경할 수 있습니다.'})
    if path=='/api/v5/merchant/broadcast':
        shop=check_text(b.get('shopId'),100,'매장')
        if not authenticated(h,shop):return h.send_json(403,{'error':'상인 인증 필요'})
        ch=str(b.get('channel',''))
        if ch not in CHANNELS:raise ValueError('메일·문자·카카오 중 선택')
        title=check_text(b.get('title'),90,'캠페인 제목')
        message=check_text(b.get('message'),420,'메시지')
        when=parse_iso(b.get('sendAt'))
        if when < now()-dt.timedelta(minutes=5) or when>now()+dt.timedelta(days=366):raise ValueError('발송 일정이 유효하지 않습니다')
        offer=str(b.get('offerId','')).strip() or None
        with DB_LOCK,db_connect() as db:
            if offer and not db.execute('SELECT 1 FROM v5_offers WHERE id=? AND shop_id=?',(offer,shop)).fetchone():raise ValueError('해당 매장의 행사가 아닙니다')
            cid=keyid('BC');db.execute('INSERT INTO v5_broadcasts VALUES(?,?,?,?,?,?,?,?,?)',
              (cid,shop,offer,ch,title,message,iso(when),'SCHEDULED',iso()));db.commit()
        return h.send_json(200,{'ok':True,'broadcastId':cid,'mode':'simulation' if not LIVE_MODE else 'configured-live'})
    if path=='/api/v5/admin/dispatch':
        if not auth_admin(h):return h.send_json(403,{'error':'관리자 인증 필요'})
        report=dispatch_due(force_demo=bool(b.get('forceDemo')), now_override=None)
        return h.send_json(200,{'ok':True,**report})
    return False

def quiet_hours(t):return t.hour>=21 or t.hour<8

def dispatch_due(force_demo=False,now_override=None):
    """Runs under DB_LOCK; records recipient selection, not actual sending in demo.
    Live sending not supported without connector + compliance review; fail closed.
    """
    t=now_override or now()
    if quiet_hours(t) and not force_demo:return {'heldQuietHours':True,'processed':0,'queued':0,'mode':'simulation'}
    processed=0;queued=0
    with DB_LOCK, db_connect() as db:
        due=db.execute('SELECT * FROM v5_broadcasts WHERE status="SCHEDULED" AND send_at<=? ORDER BY send_at LIMIT 30',(iso(t),)).fetchall()
        for bc in due:
            ch=bc['channel']
            rows=db.execute(f'''SELECT session_id,email,phone FROM v5_contacts WHERE {ch}_opt=1''').fetchall()
            for r in rows:
                if ch=='kakao':
                    # Platform-side marketing targeting verification is still mandatory.
                    friend=db.execute('SELECT kakao_friend FROM v5_contacts WHERE session_id=?',(r['session_id'],)).fetchone()
                    if not friend or not friend['kakao_friend']: continue
                recipient=r['email'] if ch=='email' else r['phone']
                if not recipient:continue
                # Avoid sending in demo. Non-demo still disabled until compliant provider handoff.
                inserted=db.execute('INSERT OR IGNORE INTO v5_outbox VALUES (?,?,?,?,?,?)',
                      (keyid('OB'),bc['id'],hashlib.sha256(recipient.encode()).hexdigest()[:16],ch,'SIMULATED',iso(t)))
                queued+=inserted.rowcount
            db.execute('UPDATE v5_broadcasts SET status="SIMULATED" WHERE id=?',(bc['id'],));processed+=1
        db.commit()
    return {'processed':processed,'queued':queued,'mode':'simulation','liveSent':0,
            'note':'연락처 원문은 결과에 포함되지 않으며 네트워크 발송은 하지 않았습니다.'}


def manual_live_dispatch(cid,limit=5):
    """Optional administrator-initiated send. NEVER used by background worker.
    Recipient consent is checked immediately before each send. Provider acceptance
    is logged, not final phone/email delivery; no automated retry after unknown outcome.
    """
    if os.environ.get('GARAK_V5_APPROVED_LIVE_SEND')!='YES' or not LIVE_MODE:
        raise ValueError('실발송 승인 비활성화')
    from market import providers
    base=os.environ.get('GARAK_PUBLIC_BASE_URL','').rstrip('/')
    if not base.startswith('https://'):raise ValueError('공개 HTTPS 주소가 필요합니다')
    with DB_LOCK,db_connect() as db:
        bc=db.execute('SELECT * FROM v5_broadcasts WHERE id=? AND status="SCHEDULED"',(cid,)).fetchone()
        if not bc:raise ValueError('예약 상태의 캠페인이 없습니다')
        ch=bc['channel']
        rows=db.execute(f'SELECT session_id,email,phone,kakao_friend FROM v5_contacts WHERE {ch}_opt=1').fetchall()
    attempt=0;success=0;failed=0
    for row in rows:
        if attempt>=limit:break
        if ch=='kakao' and not row['kakao_friend']:continue
        recipient=row['email'] if ch=='email' else row['phone']
        if not recipient:continue
        with DB_LOCK,db_connect() as db:
            db.execute('BEGIN IMMEDIATE')
            # Recheck opt-out under lock to avoid stale batch opt-in.
            current=db.execute(f'SELECT {ch}_opt FROM v5_contacts WHERE session_id=?',(row['session_id'],)).fetchone()
            if not current or not current[0]:continue
            digest=hashlib.sha256(recipient.encode()).hexdigest()[:16]
            inserted=db.execute('INSERT OR IGNORE INTO v5_outbox VALUES(?,?,?,?,?,?)',
                    (keyid('OB'),cid,digest,ch,'SUBMITTING',iso()))
            db.commit()
        if not inserted.rowcount:continue
        attempt+=1
        optout_url=base+'/unsubscribe.html?token='+unsubscribe_token(row['session_id'])+'&channel='+ch
        msg=bc['message']+'\n오늘의 특가: '+base+'/market.html'
        try:
            if ch=='email':providers.smtp_email(recipient,bc['title'],msg,optout_url)
            elif ch=='sms':
                payload=providers.sms_payload(recipient,os.environ.get('SOLAPI_SENDER',''),msg,optout_url)
                providers.send_solapi(payload)
            elif ch=='kakao':
                payload=providers.kakao_brand_payload(recipient,os.environ.get('SOLAPI_KAKAO_PF_ID',''),msg,optout_url)
                providers.send_solapi(payload)
            status='ACCEPTED_BY_PROVIDER';success+=1
        except Exception:
            status='ERROR_REVIEW_REQUIRED';failed+=1
        with DB_LOCK,db_connect() as db:
            db.execute('UPDATE v5_outbox SET status=?,processed_at=? WHERE broadcast_id=? AND recipient=?',
                       (status,iso(),cid,digest));db.commit()
    return {'attempted':attempt,'acceptedByProvider':success,'errorsNeedReview':failed,
            'notConfirmedDelivered':True,'note':'추적 결과는 공급사 접수 여부이며 수신 완료가 아닙니다.'}
