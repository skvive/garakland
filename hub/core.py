"""Garak Hansang Operations Hub v2: local, demo-only orchestration and analytics.
All mutations require the local administrator token. No real payments or marketing sending.
"""
from __future__ import annotations
import datetime as dt, hashlib, hmac, json, re, secrets, sqlite3
from registry_server import db_connect, DB_LOCK, ADMIN_TOKEN, ROOT

MODULES = [
 ('stores','매장·상인 마스터','점포 등록, 건물·층·호실, 검증 상태와 상인 정보','store','/stores.html',[]),
 ('map','지도·길찾기','2D·3D 테마맵 및 Google 지도 연결 검수','map','/market-map.html',['stores']),
 ('ar','AR 탐험·스탬프','카메라·QR 및 방문 보상 시연','scan','/ar-quest.html',['stores']),
 ('products','상품·가격 ERP','상품대장, 할인 가격, CSV 일괄등록','package','/ops.html',['stores']),
 ('coupons','쿠폰·특가','쿠폰 발행, 중복방지, 혜택별 길찾기','ticket','/coupons.html',['stores']),
 ('giftcards','연합 시연권','충전·차감·취소 가상 장부 — 실결제 비활성','wallet','/market.html',['stores']),
 ('orders','주문 시연','메뉴 선택, 주문 내역과 상태','shopping','/market.html',['stores']),
 ('marketing','홍보 캠페인','동의 확인, 발송 예약·모의 결과 확인','megaphone','/market.html',['stores']),
 ('merchants','상인센터','점포별 콘텐츠·계약·참여 준비','users','/merchant-center.html',['stores']),
 ('erp','운영·문서·정산','업무 칸반, 계약 증빙, 내부 검수·시연 정산','clipboard','/ops.html',['stores']),
 ('content','브랜드·행사 콘텐츠','마스코트·브랜드·이벤트 안내 및 글감','book','/events.html',[]),
 ('analytics','통계·리포트','운영 통계·추세·출시 준비 점검','chart','/hub.html',[]),
]
MODULE_BY_ID={x[0]:x for x in MODULES}
MODULE_VALID={x[0] for x in MODULES}
JOB_TYPES={'metrics_snapshot':'통계 스냅샷','coupon_audit':'쿠폰 정책 검수','readiness_check':'출시 준비 점검','marketing_preview':'홍보 대상 요약(발송 없음)'}
KST=dt.timezone(dt.timedelta(hours=9))
def now():return dt.datetime.now(KST)
def iso():return now().isoformat(timespec='seconds')
def check_auth(handler):
    token=handler.headers.get('X-Garak-Admin-Token','')
    return bool(token and hmac.compare_digest(token,ADMIN_TOKEN))
def bad_auth(h):return h.send_json(403,{'error':'운영 관리자 인증이 필요합니다. 실행 콘솔에서 발급된 토큰을 입력하세요.'})

def setup():
    with DB_LOCK,db_connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS v8_modules(id TEXT PRIMARY KEY, enabled INTEGER NOT NULL DEFAULT 1, note TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS v8_custom_modules(id TEXT PRIMARY KEY,name TEXT NOT NULL,description TEXT NOT NULL, url TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS v8_jobs(id TEXT PRIMARY KEY, kind TEXT NOT NULL, module_id TEXT NOT NULL, label TEXT NOT NULL,
          due_at TEXT NOT NULL, cadence TEXT NOT NULL, status TEXT NOT NULL, last_result TEXT NOT NULL DEFAULT '{}',
          run_count INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS v8_audit(id TEXT PRIMARY KEY, action TEXT NOT NULL, target TEXT NOT NULL, detail TEXT NOT NULL,
          created_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS v8_audit_time ON v8_audit(created_at);
        CREATE TABLE IF NOT EXISTS v8_snapshots(id TEXT PRIMARY KEY, captured_at TEXT NOT NULL, payload TEXT NOT NULL);
        ''')
        for m in MODULES:
            db.execute('INSERT OR IGNORE INTO v8_modules(id,enabled,note,updated_at) VALUES(?,?,?,?)',(m[0],1,'',iso()))

def log(db,action,target,detail):
    db.execute('INSERT INTO v8_audit VALUES (?,?,?,?,?)',(secrets.token_hex(12),action,target,json.dumps(detail,ensure_ascii=False,sort_keys=True),iso()))

def module_list(db):
    state={r['id']:dict(r) for r in db.execute('SELECT * FROM v8_modules')}
    result=[]
    for id_,title,description,icon,url,depends in MODULES:
        s=state.get(id_,{});enabled=bool(s.get('enabled',1))
        can_run=enabled and all(state.get(d,{}).get('enabled',1) for d in depends)
        result.append({'id':id_,'name':title,'description':description,'icon':icon,'url':url,
          'enabled':enabled,'ready':bool(can_run),'dependsOn':depends,'note':s.get('note',''),
          'status':'검토용 사용' if can_run else '일시중지','productionEnabled':False})
    for x in db.execute('SELECT * FROM v8_custom_modules ORDER BY created_at,id'):
        state_row=state.get(x['id'],{});enabled=bool(state_row.get('enabled',1))
        result.append({'id':x['id'],'name':x['name'],'description':x['description'],'icon':'custom',
          'url':x['url'],'enabled':enabled,'ready':enabled,'dependsOn':[],
          'note':state_row.get('note',''),'status':'연결형 시연 모듈' if enabled else '일시중지',
          'productionEnabled':False,'custom':True})
    return result

def count(db,table,where='',params=()):
    # All table / where strings are static from this module, never from user input.
    return db.execute('SELECT COUNT(*) FROM '+table+(' WHERE '+where if where else ''),params).fetchone()[0]

def metrics(db):
    counts={
      'stores':count(db,'stores'),'verifiedLocations':count(db,'stores',"coordinateStatus='verified' AND id NOT LIKE 'demo-%'"),
      'demoStores':count(db,'stores',"id LIKE 'demo-%'"), 'products':count(db,'v6_products'),
      'activeOffers':count(db,'v5_offers','enabled=1'), 'issuedCoupons':count(db,'v5_tickets'),
      'redeemedCoupons':count(db,'v5_tickets','redeemed_at IS NOT NULL'),
      'legacyCoupons':count(db,'wallet'), 'visits':count(db,'visits'), 'demoOrders':count(db,'orders'),
      'giftcardAccounts':count(db,'v5_cards'),'giftcardTransactions':count(db,'v5_ledger'),
      'campaigns':count(db,'v5_broadcasts'),'outboxPreview':count(db,'v5_outbox'),
      'merchantDocsReviewed':count(db,'v6_docs',"status='내부 확인'"),
      'pendingTasks':count(db,'v6_tasks',"stage NOT IN ('완료', '완료됨')"),
      'approvedNonDemoMerchants':count(db,'v5_participants','approved=1 AND demo=0'),
      'hubJobs':count(db,'v8_jobs'),'hubAuditEvents':count(db,'v8_audit'),
    }
    counts['couponRedeemRatePercent']=round(100*counts['redeemedCoupons']/counts['issuedCoupons'],1) if counts['issuedCoupons'] else 0
    return counts

def daily_stats(db,days):
    today=now().date();result=[]
    sources=[('coupons','v5_tickets','created_at'),('visits','visits','at'),('orders','orders','created_at')]
    by_type={}
    # Database timestamps use ISO strings, date part is safe to group by local date written by the app.
    for metric,table,col in sources:
        records=db.execute(f'SELECT substr({col},1,10) AS day,COUNT(*) n FROM {table} WHERE {col} >= ? GROUP BY substr({col},1,10)',((today-dt.timedelta(days=days-1)).isoformat(),)).fetchall()
        by_type[metric]={r['day']:r['n'] for r in records}
    for offset in range(days-1,-1,-1):
        date=(today-dt.timedelta(days=offset)).isoformat()
        result.append({'date':date,**{k:v.get(date,0) for k,v in by_type.items()}})
    return result

def readiness(db):
    m=metrics(db)
    rows=[
     ('verified_stores','실점포 위치 검증',m['verifiedLocations']>0,'공식 점포대장·GPS·실내 호실 현장 검증'),
     ('merchant_approval','비시연 상인 승인',m['approvedNonDemoMerchants']>0,'상인·연합회 참여 계약 및 권한 확인'),
     ('payment_review','선불·PG·정산 적법성',False,'금융 법률검토, PG 제휴, 환불·자금 보호 검증 필요'),
     ('marketing_review','광고 동의·발송 승인',False,'수신 동의, 수신거부, 발신 사업자 및 채널 승인 필요'),
     ('map_field_qa','Google 지도·AR 현장검증',False,'실기기·위치 정확도·실측 모델의 종단 간 검증 필요'),
     ('security_qa','실운영 인증·보안 심사',False,'SSO/RBAC, 2FA, 웹 보안·개인정보 보호 점검 필요'),
    ]
    return {'releaseApproved':False,'stage':'내부 베타 검수','checklist':[{'id':i,'label':a,'passed':v,'requirements':n} for i,a,v,n in rows],
     'message':'시연/현장 테스트용 운영허브입니다. 실거래·실발송·가락시장 공식 제휴를 의미하지 않습니다.'}

def gated_module(path):
    if path.startswith('/api/v6/products'):return 'products'
    if path.startswith('/api/v6/'):return 'erp'
    if path in ('/api/import','/api/stores'):return 'stores'
    if path in ('/api/merchant/campaign','/api/merchant/redeem'):return 'coupons'
    if path=='/api/merchant/order-status':return 'orders'
    if path.startswith('/api/merchant/'):return 'merchants'
    if path in ('/api/experience','/api/checkin','/api/demo/checkin','/api/recognize','/api/progress'):return 'ar'
    if path in ('/api/wallet','/api/coupons/claim'):return 'coupons'
    if path=='/api/orders':return 'orders'
    if path.startswith('/api/v5/'):
        if '/broadcast' in path or '/consent' in path or '/optout' in path or 'unsubscribe' in path:return 'marketing'
        if '/gift/' in path:return 'giftcards'
        if '/offer' in path:return 'coupons'
    return None

def is_disabled(path):
    id_=gated_module(path)
    if id_ is None:return False
    with DB_LOCK, db_connect() as db:
        states={r['id']:bool(r['enabled']) for r in db.execute('SELECT id,enabled FROM v8_modules')}
    return not states.get(id_,True) or any(not states.get(x,True) for x in MODULE_BY_ID[id_][5])

def short_text(v,name,maxlen=110):
    if not isinstance(v,str) or not v.strip() or len(v.strip())>maxlen:raise ValueError(f'{name}: 1~{maxlen}자 입력')
    return v.strip()
def parse_due(s):
    if not isinstance(s,str):raise ValueError('예약 시간이 필요합니다.')
    try: date=dt.datetime.fromisoformat(s)
    except ValueError:raise ValueError('ISO 8601 날짜·시간을 입력하세요.')
    if date.tzinfo is None:raise ValueError('시간대(+09:00)를 포함하세요.')
    if not now()-dt.timedelta(days=1)<=date<=now()+dt.timedelta(days=365):raise ValueError('예약은 1년 이내로 설정하세요.')
    return date.astimezone(KST).isoformat(timespec='seconds')
def make_result(db,kind):
    m=metrics(db)
    if kind=='metrics_snapshot':
        result={'metrics':m,'label':'통계 스냅샷','readOnly':True}
        db.execute('INSERT INTO v8_snapshots VALUES (?,?,?)',(secrets.token_hex(12),iso(),json.dumps(result,ensure_ascii=False)))
        return result
    if kind=='coupon_audit':
        return {'label':'중복·정책 점검','issued':m['issuedCoupons'],'redeemed':m['redeemedCoupons'],
        'duplicates':db.execute('''SELECT COUNT(*) FROM (SELECT session_id,offer_id,COUNT(*) n FROM v5_tickets GROUP BY session_id,offer_id HAVING n>1)''').fetchone()[0],
        'note':'쿠폰 데이터 중복 검사이며 실제 상점 현장 사용 검증은 아님'}
    if kind=='readiness_check':return readiness(db)
    if kind=='marketing_preview':
        rows=db.execute('SELECT SUM(email_opt) e,SUM(sms_opt) s,SUM(kakao_opt) k FROM v5_contacts').fetchone()
        return {'label':'광고 발송 전 수신동의 집계','consent':{'email':rows['e'] or 0,'sms':rows['s'] or 0,'kakao':rows['k'] or 0},
                'sent':0,'actualSendEnabled':False,'note':'예약 발송은 실행되지 않으며 개인정보를 내보내지 않습니다.'}
    raise ValueError('알 수 없는 작업 종류')

def dispatch_get(h,path,params):
    if not path.startswith('/api/v8/'):return False
    if not check_auth(h):return bad_auth(h)
    with DB_LOCK,db_connect() as db:
        if path=='/api/v8/dashboard':
            return h.send_json(200,{'version':'8.0 beta','asOf':iso(),'mode':'DEMO / INTERNAL ONLY',
             'modules':module_list(db),'metrics':metrics(db),'trend':daily_stats(db,14),'readiness':readiness(db),
             'recentJobs':[dict(x) for x in db.execute('SELECT * FROM v8_jobs ORDER BY updated_at DESC LIMIT 8')],
             'recentAudit':[dict(x) for x in db.execute('SELECT * FROM v8_audit ORDER BY created_at DESC LIMIT 8')]})
        if path=='/api/v8/modules':return h.send_json(200,{'items':module_list(db)})
        if path=='/api/v8/analytics':
            try:days=int(params.get('days',['30'])[0])
            except (ValueError,TypeError):raise ValueError('기간 오류')
            if days not in (7,14,30,90):raise ValueError('기간은 7·14·30·90일')
            return h.send_json(200,{'periodDays':days,'metrics':metrics(db),'daily':daily_stats(db,days),
                'currency':'DEMO_CREDIT','realRevenue':None,'note':'시연 세션 기반 이용량. 매출·실방문이 아닙니다.'})
        if path=='/api/v8/jobs':return h.send_json(200,{'items':[dict(x) for x in db.execute('SELECT * FROM v8_jobs ORDER BY due_at DESC LIMIT 200')],
                  'autoExecution':False,'note':'예약 작업은 수동 실행이며 실발송하지 않습니다.'})
        if path=='/api/v8/audit':return h.send_json(200,{'items':[dict(x) for x in db.execute('SELECT * FROM v8_audit ORDER BY created_at DESC LIMIT 150')]})
        if path=='/api/v8/snapshots':return h.send_json(200,{'items':[dict(x) for x in db.execute('SELECT * FROM v8_snapshots ORDER BY captured_at DESC LIMIT 50')]})
        if path=='/api/v8/readiness':return h.send_json(200,readiness(db))
    return h.send_json(404,{'error':'존재하지 않는 운영허브 API'})

def dispatch_post(h,path,body):
    if not path.startswith('/api/v8/'):return False
    if not check_auth(h):return bad_auth(h)
    if path=='/api/v8/module/config':
        id_=str(body.get('id',''));enabled=body.get('enabled')
        if type(enabled) is not bool:raise ValueError('boolean enabled가 필요합니다')
        note=body.get('note','')
        if not isinstance(note,str) or len(note)>200:raise ValueError('메모는 200자 이내')
        with DB_LOCK,db_connect() as db:
            state={r['id']:bool(r['enabled']) for r in db.execute('SELECT id,enabled FROM v8_modules')}
            if id_ not in state:raise ValueError('등록되지 않은 모듈 ID')
            if not enabled:
                active_dependents=[x[1] for x in MODULES if id_ in x[5] and state.get(x[0],True)]
                if active_dependents:return h.send_json(409,{'error':'하위 모듈부터 중지해야 합니다','dependents':active_dependents})
            else:
                missing=[d for d in MODULE_BY_ID[id_][5] if not state.get(d,True)] if id_ in MODULE_BY_ID else []
                if missing:return h.send_json(409,{'error':'선행 모듈 활성화 필요','dependencies':missing})
            db.execute('UPDATE v8_modules SET enabled=?,note=?,updated_at=? WHERE id=?',(int(enabled),note,iso(),id_))
            log(db,'module.enabled' if enabled else 'module.disabled',id_,{'note':note});db.commit()
            result=next(x for x in module_list(db) if x['id']==id_)
        return h.send_json(200,{'ok':True,'module':result,'warning':'레거시 외부 연동은 이 로컬 허브만으로 통제되지 않습니다.'})
    if path=='/api/v8/modules/register':
        id_=str(body.get('id','')).strip()
        name=short_text(body.get('name',''),'모듈명',60)
        description=short_text(body.get('description',''),'설명',240)
        url=str(body.get('url','')).strip()
        if not re.fullmatch(r'[a-z][a-z0-9-]{2,30}',id_):raise ValueError('모듈 코드는 영문 소문자·숫자·-로 3~31자')
        if not re.fullmatch(r'/[a-z][a-z0-9-]{0,60}\.html',url):raise ValueError('내부 HTML 페이지 경로만 등록할 수 있습니다.')
        if not (ROOT/url[1:]).is_file():raise ValueError('존재하는 HTML 페이지를 연결해야 합니다. 기능 코드는 별도 구현이 필요합니다.')
        with DB_LOCK,db_connect() as db:
            if id_ in MODULE_VALID or db.execute('SELECT 1 FROM v8_modules WHERE id=?',(id_,)).fetchone():
                return h.send_json(409,{'error':'이미 등록된 모듈 코드입니다.'})
            db.execute('INSERT INTO v8_custom_modules VALUES (?,?,?,?,?)',(id_,name,description,url,iso()))
            db.execute('INSERT INTO v8_modules VALUES (?,?,?,?)',(id_,1,'',iso()))
            log(db,'module.registered',id_,{'name':name,'url':url,'type':'linked_page_only'});db.commit()
        return h.send_json(201,{'ok':True,'moduleId':id_,'note':'운영 허브에 링크 모듈이 등록되었습니다. 별도 백엔드 코드를 자동 생성하거나 실행하지 않습니다.'})
    if path=='/api/v8/jobs/create':
        kind=body.get('kind');mod=body.get('moduleId','analytics')
        if kind not in JOB_TYPES or not isinstance(mod,str):raise ValueError('작업 유형 또는 모듈 ID가 잘못되었습니다.')
        label=short_text(body.get('label',JOB_TYPES[kind]),'작업명',100)
        due=parse_due(body.get('dueAt',iso()))
        cadence=body.get('cadence','once')
        if cadence not in ('once','daily','weekly'):raise ValueError('반복은 once/daily/weekly만 지원합니다.')
        job_id='JB-'+secrets.token_hex(8)
        with DB_LOCK,db_connect() as db:
            state={r['id']:bool(r['enabled']) for r in db.execute('SELECT id,enabled FROM v8_modules')}
            if mod not in state or not state.get(mod):return h.send_json(409,{'error':'등록되지 않았거나 중지된 모듈에는 작업을 예약할 수 없습니다.'})
            db.execute('INSERT INTO v8_jobs VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                       (job_id,kind,mod,label,due,cadence,'scheduled','{}',0,iso(),iso()))
            log(db,'job.created',job_id,{'kind':kind,'module':mod,'dueAt':due});db.commit()
        return h.send_json(201,{'ok':True,'id':job_id,'status':'scheduled','autoExecution':False})
    if path=='/api/v8/jobs/run':
        job_id=body.get('id')
        if not isinstance(job_id,str) or not re.fullmatch(r'JB-[a-f0-9]{16}',job_id):raise ValueError('작업 ID 오류')
        with DB_LOCK,db_connect() as db:
            db.execute('BEGIN IMMEDIATE')
            job=db.execute('SELECT * FROM v8_jobs WHERE id=?',(job_id,)).fetchone()
            if not job:return h.send_json(404,{'error':'작업을 찾을 수 없습니다'})
            if job['status'] not in ('scheduled','completed'):return h.send_json(409,{'error':'실행할 수 없는 작업 상태'})
            if job['status']=='completed' and job['cadence']=='once':return h.send_json(409,{'error':'이미 완료된 단발 작업'})
            if not db.execute('SELECT enabled FROM v8_modules WHERE id=?',(job['module_id'],)).fetchone()[0]:return h.send_json(409,{'error':'중지된 모듈'})
            result=make_result(db,job['kind'])
            next_due=dt.datetime.fromisoformat(job['due_at'])
            if job['cadence']=='daily':next_due+=dt.timedelta(days=1)
            if job['cadence']=='weekly':next_due+=dt.timedelta(days=7)
            new_state='completed' if job['cadence']=='once' else 'scheduled'
            db.execute('UPDATE v8_jobs SET status=?,due_at=?,run_count=run_count+1,last_result=?,updated_at=? WHERE id=?',
               (new_state,next_due.isoformat(timespec='seconds'),json.dumps(result,ensure_ascii=False),iso(),job_id))
            log(db,'job.executed',job_id,{'kind':job['kind'],'runCount':job['run_count']+1,'sent':0});db.commit()
        return h.send_json(200,{'ok':True,'id':job_id,'status':new_state,'result':result,'automaticSend':False})
    if path=='/api/v8/jobs/cancel':
        job_id=body.get('id')
        if not isinstance(job_id,str) or not re.fullmatch(r'JB-[a-f0-9]{16}',job_id):raise ValueError('작업 ID 오류')
        with DB_LOCK,db_connect() as db:
            current=db.execute('SELECT status FROM v8_jobs WHERE id=?',(job_id,)).fetchone()
            if not current:return h.send_json(404,{'error':'작업을 찾을 수 없습니다'})
            db.execute('UPDATE v8_jobs SET status="cancelled",updated_at=? WHERE id=?',(iso(),job_id))
            log(db,'job.cancelled',job_id,{});db.commit()
        return h.send_json(200,{'ok':True,'id':job_id,'status':'cancelled'})
    return h.send_json(404,{'error':'존재하지 않는 운영허브 API'})
