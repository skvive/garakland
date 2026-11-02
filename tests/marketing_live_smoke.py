"""Read-only production rollout smoke for GARAKLAND after-Lotte visitor campaign.
Never uses logins, tokens, customer data, checkout, or backend writes.
"""
from __future__ import annotations
import os
import urllib.error
import urllib.request

BASE=os.environ.get('GARAKLAND_BASE_URL','https://garakland.lexid.site').rstrip('/')
CHECKS={
 '/':('text/html','가락랜드'),
 '/brand/app.js':('javascript','롯데월드 다음 코스'),
 '/lotteworld-next.html':('text/html','롯데월드 다음 코스'),
 '/indoor-map.html':('text/html','id="view3d"'),
 '/indoor/app.mjs':('javascript','function setMapMode('),
 '/design/after-lotte.css':('text/css','.gl-after-lotte'),
 '/indoor/indoor-3d.css':('text/css','.is-isometric'),
 '/assets/mascot/garak-hansang-wave.webp':('image/webp',None),
}
errors=[]
for path,(mime,marker) in CHECKS.items():
 request=urllib.request.Request(BASE+path,headers={
  'User-Agent':'Garakland-AfterLotte-Production-QA/1.0',
  'Accept':'*/*','Cache-Control':'no-cache'
 },method='GET')
 try:
  with urllib.request.urlopen(request,timeout=24) as response:
   status=response.status
   ct=response.headers.get('Content-Type','')
   body=response.read(1400000)
 except urllib.error.HTTPError as exc:
  errors.append(f'{path} HTTP {exc.code}')
  continue
 except (urllib.error.URLError,TimeoutError,OSError) as exc:
  errors.append(f'{path} network error {type(exc).__name__}')
  continue
 print(f'GET {path}: {status}, {ct.split(";")[0]}, {len(body)} bytes')
 if status!=200:
  errors.append(f'{path} unexpected HTTP {status}')
 if mime not in ct.lower():
  errors.append(f'{path} content-type mismatch')
 if marker and marker not in body.decode('utf-8','replace'):
  errors.append(f'{path} deployment marker missing')
print(f'GARAKLAND after-Lotte production smoke: {len(CHECKS)} GET routes, {len(errors)} failures')
for issue in errors:print('FAIL:',issue)
if errors:raise SystemExit(1)
