"""GARAKLAND v6 ERP readiness staging center.
Internal document checklists, product draft import, drag/drop roadmap, demo ledger report.
Never grants a legal permit, sends live messages, or moves real funds.
"""
from __future__ import annotations
import csv, io, json, re, secrets, sqlite3, hmac, datetime as dt
from market.core import auth_admin, iso
from registry_server import DB_LOCK, db_connect

STAGES = ('자료 접수', '검토 중', '보완 요청', '내부 확인')
DOCS = (
 ('merchant_agreement','상인 참여 협약서'),
 ('business_identity','사업자·점포 운영권 확인'),
 ('store_location','점포대장·층별 도면·GPS 근거'),
 ('settlement_agreement','정산 계약·PG·세무 협의'),
 ('privacy_consent','개인정보·광고 동의·처리위탁 검토'),
 ('voucher_legal','선불형 상품권 법률검토·승인 판단'),
 ('field_qa','매장 현장 검수 및 QR·지도 테스트'),
 ('launch_signoff','운영·보안·고객지원 출시 승인'),
)
DEFAULT_TASKS = (
 ('상인 연합회 참여 및 담당자 확인','실제 상인회·협회 승인 및 운영 주체 확인','자료 접수'),
 ('점포별 서명·사업자 증빙 수집','사업자증명·점포코드·권한 위임·정보 고지','자료 접수'),
 ('가락시장 층별 배치도 사용허락','공식 도면·실측 GPS·사진 저작권 범위 확인','자료 접수'),
 ('정산대행·PG 계약 검토','대금 수취 주체, 정산 주기, 수수료, 환불 구조 확정','검토 중'),
 ('상품권 등록/면제 및 자금 보호 판단','선불업 적용 여부와 고객 충전금 보호 구조 법무 검토','검토 중'),
 ('광고 발송 계약 및 수신동의 검증','발신번호·채널·광고 표시·철회·로그 보존','검토 중'),
 ('개인정보 보호 영향 및 위탁 점검','최소 수집, 접근통제, 보존/파기, 침해대응','보완 요청'),
 ('현장 인수·최종 출시 승인','모바일 GPS, 내비게이션, 쿠폰, 환불, 복구 테스트','자료 접수'),
)
MAX_CSV=500_000
MAX_ROWS=350
FIELDS=('product_code','shop_id','product_name','unit','regular_price','special_price','stock','starts_at','ends_at')

def setup():
  with DB_LOCK,db_connect() as db:
    db.executescript('''
    CREATE TABLE IF NOT EXISTS v6_tasks(id TEXT PRIMARY KEY,title TEXT NOT NULL,detail TEXT NOT NULL,
      stage TEXT NOT NULL,sort_index INTEGER NOT NULL,updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS v6_docs(shop_id TEXT NOT NULL,code TEXT NOT NULL,status TEXT NOT NULL,
      evidence_ref TEXT NOT NULL,reviewed_at TEXT NOT NULL,PRIMARY KEY(shop_id,code));
    CREATE TABLE IF NOT EXISTS v6_products(product_code TEXT PRIMARY KEY,shop_id TEXT NOT NULL,product_name TEXT NOT NULL,
      unit TEXT NOT NULL,regular_price INTEGER NOT NULL,special_price INTEGER NOT NULL,stock INTEGER NOT NULL,
      starts_at TEXT NOT NULL,ends_at TEXT NOT NULL,published INTEGER NOT NULL DEFAULT 0,updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS v6_audit(id TEXT PRIMARY KEY,kind TEXT NOT NULL,target TEXT NOT NULL,
      detail TEXT NOT NULL,created_at TEXT NOT NULL);
    ''')
    count=db.execute('SELECT COUNT(*) FROM v6_tasks').fetchone()[0]
    if not count:
      for i,(title,detail,stage) in enumerate(DEFAULT_TASKS):
        db.execute('INSERT INTO v6_tasks VALUES(?,?,?,?,?,?)',(secrets.token_hex(9),title,detail,stage,i,iso()))
    db.commit()

def auth(h):
  if not auth_admin(h):
    h.send_json(403,{'error':'관리자 토큰 인증이 필요합니다.'})
    return False
  return True

def tasks(db):
  return [dict(r) for r in db.execute('SELECT * FROM v6_tasks ORDER BY sort_index,updated_at,id')]

def shop_rows(db):
  sql='''SELECT s.id,s.name,s.category,s.building,s.floor,s.room,s.coordinateStatus,s.status,
    COALESCE(p.approved,0) AS demo_member_approved, COALESCE(p.demo,0) AS is_demo,
    (SELECT COUNT(*) FROM v6_docs d WHERE d.shop_id=s.id AND d.status='내부 확인') AS reviewed
    FROM stores s LEFT JOIN v5_participants p ON p.shop_id=s.id ORDER BY s.name LIMIT 1500'''
  return [dict(r) for r in db.execute(sql)]

def get(h,path,p):
  if not path.startswith('/api/v6/'): return False
  if not auth(h): return True
  with DB_LOCK,db_connect() as db:
    if path=='/api/v6/dashboard':
      sh=shop_rows(db)
      demo_debits=db.execute("SELECT count(*),COALESCE(SUM(-amount),0) FROM v5_ledger WHERE kind='REDEEM'").fetchone()
      qty=db.execute('SELECT count(*) FROM v6_products').fetchone()[0]
      return h.send_json(200,{'version':'v6.0-staging','realPayment':False,'bulkLiveMessaging':False,
        'shops':sh,'tasks':tasks(db),'totalShops':len(sh),'completeDocuments':sum(s['reviewed'] for s in sh),
        'requiredDocs':len(DOCS),'documents':[{'code':c,'label':t} for c,t in DOCS],
        'stagedProducts':qty,'simulatedVoucherUses':demo_debits[0],
        'simulatedVoucherSpend':demo_debits[1], 'officialApproval':False,
        'disclaimer':'내부 상태 표시는 법률상 허가·계약 체결 또는 실제 결제를 의미하지 않습니다.'})
    if path=='/api/v6/documents':
      sid=(p.get('shopId') or [''])[0]
      if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',sid): raise ValueError('매장 ID 오류')
      rows=[dict(r) for r in db.execute('SELECT * FROM v6_docs WHERE shop_id=?',(sid,))]
      return h.send_json(200,{'shopId':sid,'items':rows,'required':[{'code':c,'label':t} for c,t in DOCS]})
    if path=='/api/v6/products':
      sid=(p.get('shopId') or [''])[0]
      if sid:
        rows=[dict(r) for r in db.execute('SELECT * FROM v6_products WHERE shop_id=? ORDER BY updated_at DESC LIMIT 500',(sid,))]
      else:rows=[dict(r) for r in db.execute('SELECT * FROM v6_products ORDER BY updated_at DESC LIMIT 500')]
      return h.send_json(200,{'items':rows,'publishedToPublic':False})
    if path=='/api/v6/audit':
      rows=[dict(r) for r in db.execute('SELECT * FROM v6_audit ORDER BY created_at DESC LIMIT 100')]
      return h.send_json(200,{'items':rows})
    if path=='/api/v6/settlement':
      rows=[dict(r) for r in db.execute('''SELECT l.id,l.card_id,l.shop_id,l.kind,l.amount,l.before_balance,l.after_balance,l.created_at,s.name AS shop_name
       FROM v5_ledger l LEFT JOIN stores s ON s.id=l.shop_id ORDER BY l.created_at DESC LIMIT 500''')]
      return h.send_json(200,{'items':rows,'currency':'DEMO_CREDIT','actualRevenue':0,
         'warning':'가상 거래 장부입니다. 실제 정산·부가가치세 신고 자료로 사용할 수 없습니다.'})
  return h.send_json(404,{'error':'지원하지 않는 ERP 주소입니다.'})

def _text(value,label,max_len=120):
  if not isinstance(value,str) or not value.strip() or len(value.strip())>max_len:
    raise ValueError(f'{label}을(를) 1~{max_len}자로 입력하세요.')
  return value.strip()

def _validate_products(text,db):
  if not isinstance(text,str) or len(text.encode('utf-8'))>MAX_CSV:raise ValueError('CSV 본문은 최대 500KB입니다.')
  reader=csv.DictReader(io.StringIO(text.lstrip('\ufeff'), newline=''))
  if reader.fieldnames is None or tuple(reader.fieldnames)!=FIELDS:
    raise ValueError('CSV 헤더가 양식과 다릅니다: '+','.join(FIELDS))
  rows=[];seen=set();issues=[]
  for rownum,r in enumerate(reader,start=2):
    if rownum>MAX_ROWS+1:raise ValueError('최대 350개 품목만 일괄 등록할 수 있습니다.')
    try:
      if None in r or any(r[k] is None for k in FIELDS):raise ValueError('열 개수가 일치하지 않습니다.')
      code=_text(r['product_code'],'상품코드',60)
      sid=_text(r['shop_id'],'점포 ID',80)
      if not re.fullmatch(r'[A-Za-z0-9_-]+',code):raise ValueError('상품코드는 영문·숫자·-·_만 가능합니다.')
      if code in seen:raise ValueError('파일 안에 중복 상품코드가 있습니다.')
      if not re.fullmatch(r'[A-Za-z0-9_-]+',sid):raise ValueError('점포 ID 형식 오류')
      if not db.execute('SELECT 1 FROM stores WHERE id=?',(sid,)).fetchone():raise ValueError('등록되지 않은 점포 ID')
      name=_text(r['product_name'],'상품명',100)
      unit=_text(r['unit'],'단위',30)
      for label,value in [('상품명',name),('단위',unit)]:
        if value[0] in '=+@\t\r\n':raise ValueError(label+'에 허용되지 않는 첫 글자')
      regular=int(r['regular_price']); special=int(r['special_price']);stock=int(r['stock'])
      if not (100<=special<=regular<=100_000_000):raise ValueError('정상가·특가 범위 오류(100~1억원 / 특가 ≤ 정상가)')
      if not 0<=stock<=1_000_000:raise ValueError('재고는 0~100만개 범위입니다.')
      start=dt.datetime.fromisoformat(r['starts_at']);end=dt.datetime.fromisoformat(r['ends_at'])
      if start>=end:raise ValueError('종료 시각은 시작 시각보다 늦어야 합니다.')
      if (end-start).days>365:raise ValueError('행사 기간 최대 1년')
      seen.add(code)
      rows.append({'product_code':code,'shop_id':sid,'product_name':name,'unit':unit,
       'regular_price':regular,'special_price':special,'stock':stock,'starts_at':start.isoformat(),
       'ends_at':end.isoformat()})
    except (ValueError,TypeError,KeyError,OverflowError) as exc:
      issues.append({'line':rownum,'error':str(exc)})
  if not rows and not issues:issues.append({'line':1,'error':'등록할 상품 행이 없습니다.'})
  return rows,issues

def post(h,path,b):
  if not path.startswith('/api/v6/'): return False
  if not auth(h):return True
  with DB_LOCK,db_connect() as db:
    if path=='/api/v6/task/add':
      title=_text(b.get('title'),'업무명',90)
      detail=_text(b.get('detail','직접 등록한 업무'),'업무 설명',350)
      stage=b.get('stage','자료 접수')
      if stage not in STAGES:raise ValueError('단계 값 오류')
      token=secrets.token_hex(9)
      idx=db.execute('SELECT COALESCE(MAX(sort_index)+1,0) FROM v6_tasks').fetchone()[0]
      db.execute('INSERT INTO v6_tasks VALUES(?,?,?,?,?,?)',(token,title,detail,stage,idx,iso()))
      db.execute('INSERT INTO v6_audit VALUES(?,?,?,?,?)',(secrets.token_hex(9),'task-create',token,title,iso()))
      db.commit();return h.send_json(200,{'ok':True,'id':token})
    if path=='/api/v6/task/move':
      ids=b.get('orderedIds');stage=b.get('stage')
      if stage not in STAGES or not isinstance(ids,list) or not ids or len(ids)>200 or len(ids)!=len(set(ids)):
        raise ValueError('드래그 순서 또는 열 정보 오류')
      current={r[0] for r in db.execute('SELECT id FROM v6_tasks')}
      if not set(ids).issubset(current):raise ValueError('없는 업무 카드가 포함되어 있습니다.')
      for i,item in enumerate(ids):db.execute('UPDATE v6_tasks SET stage=?,sort_index=?,updated_at=? WHERE id=?',(stage,i,iso(),item))
      db.execute('INSERT INTO v6_audit VALUES(?,?,?,?,?)',(secrets.token_hex(9),'task-move',stage,','.join(ids),iso()))
      db.commit();return h.send_json(200,{'ok':True,'count':len(ids)})
    if path=='/api/v6/documents/review':
      sid=_text(b.get('shopId'),'매장 ID',80);code=b.get('code');status=b.get('status')
      if code not in dict(DOCS):raise ValueError('문서 종류 오류')
      if status not in ('미접수','접수','검토 중','내부 확인','보완 요청'):raise ValueError('문서 상태 오류')
      if not db.execute('SELECT 1 FROM stores WHERE id=?',(sid,)).fetchone():raise ValueError('없는 점포입니다.')
      ref=str(b.get('evidenceRef','')).strip()
      if len(ref)>160 or any(c in ref for c in ('\r','\n','<','>')):raise ValueError('증빙 참조번호는 160자 이내의 일반 문자입니다.')
      if status=='내부 확인' and not ref:raise ValueError('내부 확인에는 계약/검수 증빙 참조번호가 필요합니다.')
      db.execute('INSERT INTO v6_docs VALUES(?,?,?,?,?) ON CONFLICT(shop_id,code) DO UPDATE SET status=excluded.status,evidence_ref=excluded.evidence_ref,reviewed_at=excluded.reviewed_at',(sid,code,status,ref,iso()))
      db.execute('INSERT INTO v6_audit VALUES(?,?,?,?,?)',(secrets.token_hex(9),'doc-review',sid,code+':'+status+':'+ref,iso()))
      db.commit();return h.send_json(200,{'ok':True,'status':status,'notice':'시스템 내부 검토 상태입니다. 실제 계약·기관 승인을 의미하지 않습니다.'})
    if path in ('/api/v6/products/validate','/api/v6/products/import'):
      rows,issues=_validate_products(b.get('csv',''),db)
      if issues:return h.send_json(422,{'ok':False,'valid':len(rows),'issues':issues[:50]})
      if path.endswith('validate'):return h.send_json(200,{'ok':True,'valid':len(rows),'sample':rows[:3],'writes':False})
      for r in rows:
        db.execute('''INSERT INTO v6_products(product_code,shop_id,product_name,unit,regular_price,special_price,stock,starts_at,ends_at,published,updated_at)
         VALUES (?,?,?,?,?,?,?,?,?,0,?)
         ON CONFLICT(product_code) DO UPDATE SET shop_id=excluded.shop_id,product_name=excluded.product_name,
         unit=excluded.unit,regular_price=excluded.regular_price,special_price=excluded.special_price,
         stock=excluded.stock,starts_at=excluded.starts_at,ends_at=excluded.ends_at,published=0,updated_at=excluded.updated_at''',
         tuple(r[k] for k in FIELDS)+(iso(),))
      db.execute('INSERT INTO v6_audit VALUES(?,?,?,?,?)',(secrets.token_hex(9),'product-import','catalog',f'{len(rows)}개 상품 / 모두 비공개 초안',iso()))
      db.commit();return h.send_json(200,{'ok':True,'imported':len(rows),'status':'비공개 초안','publiclyListed':False})
  return h.send_json(404,{'error':'지원하지 않는 ERP 명령입니다.'})
