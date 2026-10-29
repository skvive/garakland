"""Optional outbound marketing adapters (not called by default in v5 beta).
Policy: deliver only to explicit channel opt-ins after operator review and consent proof.
External gateway credentials must be supplied by the user; no external sending in tests.
"""
import datetime as dt
import hashlib
import hmac
import os
import re
import secrets
import smtplib
import ssl
import json
from email.message import EmailMessage
from urllib.request import Request,urlopen

SOLAPI_URL='https://api.solapi.com/messages/v4/send-many/detail'

def solapi_auth(key,secret,when=None,salt=None):
    if not key or not secret:raise ValueError('SOLAPI 인증 정보가 필요합니다')
    stamp=when or dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    salt=salt or secrets.token_hex(16)
    signature=hmac.new(secret.encode(),(stamp+salt).encode(),hashlib.sha256).hexdigest()
    return f'HMAC-SHA256 apiKey={key}, date={stamp}, salt={salt}, signature={signature}'

def sms_payload(recipient,sender,message,unsubscribe):
    if not re.fullmatch(r'01[0-9]{8,9}',recipient):raise ValueError('수신 휴대전화가 올바르지 않습니다')
    if not re.fullmatch(r'[0-9]{8,12}',sender):raise ValueError('사전 등록한 발신번호가 필요합니다')
    if not unsubscribe or not message:raise ValueError('수신거부 안내 및 메시지가 필요합니다')
    txt=f'(광고) 가락랜드\n{message}\n무료 수신거부: {unsubscribe}'
    if len(txt.encode('utf8'))>2000:raise ValueError('문자 최대 크기 초과')
    return {'messages':[{'to':recipient,'from':sender,'text':txt,'autoTypeDetect':True}]}

def kakao_brand_payload(recipient,pf_id,message,unsubscribe,target='M'):
    """Sample SOLAPI BMS text schema. Service/provider-side eligibility is mandatory."""
    if not re.fullmatch(r'01[0-9]{8,9}',recipient):raise ValueError('수신 휴대전화 오류')
    if not pf_id or not unsubscribe:raise ValueError('카카오 채널 ID 및 수신거부 경로 필수')
    if target not in ('M','I'):raise ValueError('채널 자격 심사 및 타깃 확인 필수')
    return {'messages':[{'to':recipient,'type':'BMS_TEXT','kakaoOptions':{
       'pfId':pf_id,'bms':{'targeting':target,'chatBubbleType':'TEXT'},'adFlag':True},
       'text':'(광고) 가락랜드\n'+message+'\n수신거부: '+unsubscribe}]}

def send_solapi(payload,api_key=None,api_secret=None,requester=None):
    key=api_key or os.environ.get('SOLAPI_API_KEY','')
    secret=api_secret or os.environ.get('SOLAPI_API_SECRET','')
    if not os.environ.get('GARAK_V5_APPROVED_LIVE_SEND')=='YES':raise RuntimeError('법적·사업자 승인 없이 실제 메시지 발송 차단됨')
    if not key or not secret:raise ValueError('SOLAPI API 키 및 비밀키가 없습니다')
    request=Request(SOLAPI_URL,data=json.dumps(payload,ensure_ascii=False).encode(),
      headers={'Authorization':solapi_auth(key,secret),'Content-Type':'application/json'},method='POST')
    sender=requester or urlopen
    with sender(request,timeout=15) as resp:
        if getattr(resp,'status',200)>=400:raise RuntimeError('문자 공급사 발송 실패')
        return json.loads(resp.read().decode())

def smtp_email(recipient,subject,text,unsubscribe):
    if os.environ.get('GARAK_V5_APPROVED_LIVE_SEND')!='YES':raise RuntimeError('실발송 비활성화')
    host=os.environ.get('GARAK_SMTP_HOST','')
    sender=os.environ.get('GARAK_SMTP_FROM','')
    user=os.environ.get('GARAK_SMTP_USER','')
    password=os.environ.get('GARAK_SMTP_PASSWORD','')
    if not all((host,sender,user,password,unsubscribe)):raise ValueError('SMTP 구성 및 수신거부 링크가 필요합니다')
    msg=EmailMessage();msg['From']=sender;msg['To']=recipient;msg['Subject']='[광고] '+subject
    msg['List-Unsubscribe']='<'+unsubscribe+'>'
    msg.set_content('(광고) 가락랜드\n'+text+'\n수신거부: '+unsubscribe)
    with smtplib.SMTP_SSL(host,int(os.environ.get('GARAK_SMTP_PORT','465')),context=ssl.create_default_context(),timeout=15) as s:
        s.login(user,password);s.send_message(msg)
    return {'accepted':True}
