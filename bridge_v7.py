"""v7 GitHub-pattern adaptation: SAFE promo share-kit and production-readiness report.
Inspired by architecture patterns from connected repositories; code newly authored.
No real payments, Kakao messaging or mass SMS are enabled here.
"""
from __future__ import annotations
import os, re, hmac
from urllib.parse import urlencode, urlsplit
from registry_server import DB_LOCK, db_connect, ADMIN_TOKEN
from market import core as growth

MODE=os.environ.get('GARAK_V7_MODE','demo').strip().lower()
if MODE not in {'demo','review'}:
    raise RuntimeError('GARAK_V7_MODE supports demo/review only. Real payment or marketing launch requires separate reviewed deployment.')

REPOS=[
 {'name':'shinkangteam/skvive','visibility':'private','pattern':'dummy/real origins and admin-managed mode isolation','used':'review mode and explicit demo labeling'},
 {'name':'shinkangteam/gbsales','visibility':'private','pattern':'market price cards and wallet balances','used':'existing KRW amounts retained; no imported payment handlers'},
 {'name':'shinkangteam/helloapp','visibility':'private','pattern':'Kakao OAuth scope, refresh and delivery audit','used':'consent/approval checks and provider-stub boundary only'},
 {'name':'shinkangteam/marketingsodong','visibility':'public','pattern':'store registration and one-touch share UX','used':'coupon share text/URL generation'},
 {'name':'shinkangteam/greenbean-ledger','visibility':'private','pattern':'separate authenticated ledger and audit','used':'read-only audit summary; no financial code copied'}
]

def clean_base():
    base=os.environ.get('GARAK_PUBLIC_BASE_URL','').strip().rstrip('/')
    if not base: return ''
    p=urlsplit(base)
    if p.scheme!='https' or not p.hostname or p.username or p.password or p.query or p.fragment:
        return ''
    if p.hostname in {'localhost','127.0.0.1','0.0.0.0'}: return ''
    return base

def share_text(offer,public_base=''):
    is_demo=bool(offer['shop_id'].startswith('demo-'))
    pre='[시연용/실제 사용 불가] ' if is_demo else ''
    # Wording never asserts stock, verified GPS or actual business participation without proof.
    title=pre+str(offer['item'])
    sale=int(offer['offer_price']);original=int(offer['original_price'])
    lines=[f'(광고) {title}', f'판매가 {original:,}원 → 쿠폰가 {sale:,}원',
        f"매장: {offer['shop_name']} · {offer['building']} {offer['floor']} {offer['room']}",
        '쿠폰 조건·잔여수량·행사기간은 방문 전에 꼭 확인하세요.']
    landing=public_base+'/market.html#explore' if public_base else ''
    if landing:lines.append('행사 보기: '+landing)
    lines.append('길찾기: '+offer['directions_url'])
    lines.append('수신거부는 앱의 ‘소식 받기’ 메뉴에서 설정할 수 있습니다.')
    return {'offerId':offer['id'],'shopId':offer['shop_id'],'title':title,
      'text':'\n'.join(lines),'emailSubject':'[광고] 가락랜드 특가: '+str(offer['item']),
      'directionsUrl':offer['directions_url'], 'landingUrl':landing,
      'requiresPublicUrl':not bool(public_base),'demo':is_demo,
      'locationVerified':bool(offer['verified_location']),
      'automaticSendEnabled':False,
      'providerNote':'문구 복사용 시연. 실제 대량발송에는 수신동의, 광고 표시, 발신자 및 업체 승인 필요.'}

def get(h,path,p):
    if path=='/api/v7/meta':
        return h.send_json(200,{'version':'7.0-github-integrated-beta','mode':MODE,
          'realPaymentsEnabled':False,'bulkMessagingEnabled':False,
          'publicLinkConfigured':bool(clean_base()),'githubComparedRepositories':len(REPOS)})
    if path=='/api/v7/share-kit':
        offer_id=p.get('offerId',[''])[0]
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',offer_id):
            return h.send_json(400,{'error':'올바른 행사 ID가 필요합니다'})
        with DB_LOCK, db_connect() as db:
            found=next((x for x in growth.query_offers(db) if x['id']==offer_id),None)
        if not found or (MODE=='review' and found['is_demo']):
            return h.send_json(404,{'error':'공개할 수 없는 행사입니다'})
        return h.send_json(200,share_text(found,clean_base()))
    if path=='/api/v7/readiness':
        token=h.headers.get('X-Garak-Admin-Token','')
        if not token or not hmac.compare_digest(token,ADMIN_TOKEN):return h.send_json(403,{'error':'관리자 인증 필요'})
        with DB_LOCK, db_connect() as db:
            query=lambda q:db.execute(q).fetchone()[0]
            metrics={
              'storeCount':query('SELECT count(*) FROM stores'),
              'demoStoreCount':query("SELECT count(*) FROM stores WHERE id LIKE 'demo-%'"),
              'verifiedActualStores':query("SELECT count(*) FROM stores WHERE coordinateStatus='verified' AND id NOT LIKE 'demo-%' AND status='published'"),
              'approvedActualMerchants':query('SELECT count(*) FROM v5_participants WHERE approved=1 AND demo=0'),
              'activeOffers':query('SELECT count(*) FROM v5_offers WHERE enabled=1'),
              'simulatedGiftCardCount':query('SELECT count(*) FROM v5_cards')}
        blockers=['상인연합 참여계약과 실점포 등록 서류 승인','공식 점포 배치도와 현장 GPS 검증',
          '전자금융업·PG·정산·환불 법률 심사','광고 발송 사업자·마케팅 동의 적법성 감사',
          '실사용자 인증/개인정보 보호 영향평가/보안 침투검사','Google 지도/카메라/GPS 실기기 테스트']
        return h.send_json(200,{'version':'7.0-beta','mode':MODE,'releaseApproved':False,
          'financialOperationEnabled':False,'realMassMessagingEnabled':False,
          'metrics':metrics,'blockers':blockers,'repositoryComparison':REPOS,
          'decision':'NO_GO: 상용 실거래 전면 차단, 검토용 베타만 허용'})
    return False
