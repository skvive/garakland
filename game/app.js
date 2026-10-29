import {buildDirections,hasVerifiedGps} from './navigation.mjs';
/* GARAKLAND AR QUEST — original beta client. No location history or camera stream persisted. */
const $=id=>document.getElementById(id);
const state={shops:[],campaigns:[],wallet:[],progress:{visits:[],badges:[],xp:0,level:1,streak:0,uniqueShops:0},orders:[],selected:null,filter:'all',geo:null,demo:false,stream:null,detector:null,scanTimer:null,scanBusy:false,detectedCode:'',orderShop:null};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const won=n=>new Intl.NumberFormat('ko-KR').format(Number(n)||0)+'원';
const link=u=>{try{const v=new URL(u);return ['https:','http:'].includes(v.protocol)&&!v.username&&!v.password?v.href:'';}catch{return ''}};
const stamp=()=>new Date().toLocaleString('ko-KR');
let toastTimeout;
function toast(s){const n=$('toast');n.textContent=String(s);n.classList.add('show');clearTimeout(toastTimeout);toastTimeout=setTimeout(()=>n.classList.remove('show'),4600);}
async function get(url,headers={}){const r=await fetch(url,{headers,credentials:'same-origin'});const p=await r.json();if(!r.ok)throw Error(p.error||r.statusText);return p;}
async function post(url,obj,headers={}){const r=await fetch(url,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Garak-Client':'1',...headers},body:JSON.stringify(obj)});const p=await r.json().catch(()=>({error:'서버 응답 오류'}));if(!r.ok)throw Error(p.error||r.statusText);return p;}
function go(page){document.querySelectorAll('[data-page]').forEach(n=>{n.classList.toggle('active',n.dataset.page===page);n.setAttribute('aria-current',n.dataset.page===page?'page':'false')});document.querySelectorAll('.page').forEach(n=>n.classList.toggle('active',n.id==='page-'+page));window.scrollTo({top:0,behavior:'instant'});}
function shop(id){return state.shops.find(s=>s.id===id)}
function image(src,alt){return `<img alt="${esc(alt)}" src="${esc(src||'/assets/icon.svg')}" loading="lazy" onerror="this.onerror=null;this.src='/assets/icon.svg'">`}

/* v4 editorial assets are explicitly demo imagery; never override authentic merchant uploads. */
const photoByCategory={"수산":"seafood","청과":"fruit","축산":"meat","음식":"kitchen","식자재":"market"};
function editorialPhoto(s){
  if(!s)return './assets/editorial/market.webp';
  if(!s.isDemo)return s.hero||'/assets/icon.svg';
  const k=photoByCategory[s.category]||'merchant';
  return './assets/editorial/'+k+'.webp';
}
let favoriteIds=new Set();
try{const a=JSON.parse(localStorage.getItem('garakland_favorites_v4')||'[]');if(Array.isArray(a))favoriteIds=new Set(a.filter(x=>typeof x==='string'))}catch{}
function saveFavorite(id){if(favoriteIds.has(id))favoriteIds.delete(id);else favoriteIds.add(id);try{localStorage.setItem('garakland_favorites_v4',JSON.stringify([...favoriteIds]))}catch{};
 toast(favoriteIds.has(id)?'관심 매장에 저장했습니다.':'관심 매장에서 해제했습니다.');
 if(state.selected?.id===id){const b=document.getElementById('modalFavorite');if(b)b.textContent=favoriteIds.has(id)?'♥ 관심 매장 저장됨':'♡ 관심 매장 저장';}
 renderDirectory();
}
async function shareShop(id){const url=new URL(window.location.href);url.searchParams.set('shop',id);url.hash='';try{if(navigator.share){await navigator.share({title:'가락랜드 매장 안내',url:url.href});return}await navigator.clipboard.writeText(url.href);toast('매장 링크를 복사했습니다.')}catch(e){if(e?.name!=='AbortError')toast('링크 복사 기능을 사용할 수 없습니다.')}}
function renderFilterPills(){const host=$('shopFilterPills');if(!host)return;const cats=[...new Set(state.shops.map(x=>x.category).filter(Boolean))];
 host.innerHTML=[['all','전체 매장'],['favorites','♡ 저장한 매장'],...cats.map(x=>[x,x])].map(([id,label])=>`<button type="button" data-filter-pill="${esc(id)}" class="${state.filter===id?'active':''}" aria-pressed="${state.filter===id}">${esc(label)}</button>`).join('');
}
function updateMerchantChecklist(){const host=$('merchantCompletion');if(!host)return;const s=shop($('merchantShop').value);if(!s){host.textContent='매장 선택 후 확인하세요.';return}
 const checks=[['메뉴 등록',!!s.menu?.length],['대표 사진',!!s.hero&&!s.isDemo],['메뉴판 이미지',!!s.menu_image&&!s.isDemo],['블로그 연결',!!link(s.blogUrl)],['GPS 확인',s.coordinateStatus==='verified'&&!s.isDemo]];
 host.innerHTML=checks.map(([name,yes])=>`<span class="${yes?'':'pending'}">${yes?'✓':'○'} ${esc(name)}</span>`).join('');
}
function symbol(s){return s.category==='수산'?'🐟':s.category==='청과'?'🍎':s.category==='축산'?'🥩':s.category==='음식'?'🍱':'🏪'}
function openShop(id){const s=shop(id);if(!s){toast('등록된 매장 정보가 없습니다.');return}state.selected=s;let gps=s.coordinateStatus==='verified'&&Number.isFinite(+s.latitude)&&Number.isFinite(+s.longitude);const campaigns=state.campaigns.filter(c=>c.shop_id===s.id);
let url=link(s.blogUrl),dl=link(s.delivery_url),nav=buildDirections(s);
$('shopModalBody').innerHTML=`${image(editorialPhoto(s),s.isDemo?'AI 생성 시연 이미지':'등록 매장 이미지') .replace('<img','<img class="shop-hero-img"')}<div class="shop-modal-content"><span class="shop-kicker">${s.isDemo?'BETA · FICTIONAL STORE':'MERCHANT DIRECTORY'}</span><h2>${esc(s.name)}</h2><span class="location">${esc(s.building)} · ${esc(s.floor||'층 정보 미확인')} · ${esc(s.room||'호실 미확인')} ${gps?'· GPS 등록됨':'· GPS 미검증'}</span><div class="shop-info-grid"><div>${s.menu_image?image(s.menu_image,'등록 메뉴판 이미지'):'<div class="empty">메뉴판 이미지 미등록</div>'}</div><div><b>📋 메뉴와 가격</b><div class="shop-menu-list">${(s.menu||[]).map(m=>`<div><span>${esc(m.name)}</span><strong>${won(m.price)}</strong></div>`).join('')||'<p class="empty">등록된 메뉴가 없습니다.</p>'}</div><p class="description">${s.isDemo?'이 매장은 실제 상점이 아닌 기능 시연을 위한 가상 매장입니다. 메뉴·가격·호실·사진은 모두 시연용입니다.':'상인이 직접 등록한 매장 정보입니다. 방문 전 실매장 영업·주소·가격을 확인하세요.'}</p><b>🎟️ 진행 중인 캠페인</b><div class="shop-menu-list">${campaigns.map(c=>`<div><span>${esc(c.title)}</span><strong>${esc(c.discount_label)}</strong></div>`).join('')||'<p class="empty">현재 등록된 쿠폰이 없습니다.</p>'}</div></div></div><div class="shop-buttons"><a target="_blank" rel="noopener noreferrer" href="${esc(nav.url)}">📍 ${esc(nav.buttonLabel)} ↗</a>${url?`<a target="_blank" rel="noopener noreferrer" href="${esc(url)}">📝 매장 블로그 ↗</a>`:'<button disabled>📝 블로그 미등록</button>'}${dl?`<a target="_blank" rel="noopener noreferrer" href="${esc(dl)}">🛵 제휴 주문 열기 ↗</a>`:''}<button class="strong" id="modalOrder" ${!(s.menu||[]).length?'disabled':''}>🛍️ 메뉴·주문 시연</button><button id="modalFavorite" type="button">${favoriteIds.has(s.id)?'♥ 관심 매장 저장됨':'♡ 관심 매장 저장'}</button><button id="modalShare" type="button">↗ 매장 링크 공유</button>${state.demo&&s.isDemo?`<button id="demoVisit">✨ 시연 스탬프 획득</button>`:''}${campaigns.length?'<button id="modalCoupon">🎟️ 쿠폰 보러 가기</button>':''}</div><p class="description route-note">${esc(nav.notice)}</p>${s.isDemo?'<p class="description">※ 가상 시연점 쿠폰은 실매장에서 사용 불가합니다.</p>':''}</div>`;
$('shopDialog').showModal();$('modalFavorite')?.addEventListener('click',()=>saveFavorite(s.id));$('modalShare')?.addEventListener('click',()=>shareShop(s.id));$('modalOrder')?.addEventListener('click',()=>startOrder(s.id));$('demoVisit')?.addEventListener('click',()=>demoVisit(s.id));$('modalCoupon')?.addEventListener('click',()=>{$('shopDialog').close();go('coupons')});}
function showCouponRoute(id, couponCode='') {
 const s=shop(id); if(!s){toast('연결된 매장을 찾을 수 없습니다.');return}
 const walking=buildDirections(s,'walking');const driving=buildDirections(s,'driving');
 $('routeTitle').textContent=s.name;
 $('routeDetails').textContent=[s.building,s.floor,s.room].filter(Boolean).join(' · ')||'층·호실 미등록';
 $('routeAccuracy').textContent=walking.verified?'✅ 확인된 매장 GPS로 안내':'⚠️ 개별 매장 좌표 미확인 · 가락시장 공통 위치로 안내';
 $('routeAccuracy').className=walking.verified?'route-accuracy verified':'route-accuracy caution';
 $('routeNotice').textContent=walking.notice;
 $('routeCoupon').textContent=couponCode?`발급된 쿠폰 번호: ${couponCode}`:'쿠폰 지갑의 쿠폰 번호를 상인에게 제시하고 사용 확인을 요청하세요.';
 for(const [id,nav] of [['routeWalk',walking],['routeDrive',driving]]){
   const el=$(id);el.href=nav.url;el.textContent=(id==='routeWalk'?'🚶 도보 ':'🚘 자동차 ')+ (nav.verified?'매장 GPS 길안내 열기':'가락시장 길안내 열기');
 }
 $('routeDialog').showModal();
}
async function demoVisit(id){try{const p=await post('/api/demo/checkin',{shopId:id});toast(p.message+(p.earnedXp?' +40 XP':''));await refreshProgress()}catch(e){toast(e.message)}}
function renderShops(){const demoFirst=state.shops.filter(s=>s.isDemo),real=state.shops.filter(s=>!s.isDemo);$('featuredShops').innerHTML=(demoFirst.length?demoFirst:real).slice(0,4).map(s=>`<button class="shop-card" data-shop="${esc(s.id)}">${image(editorialPhoto(s),s.isDemo?'AI 생성 시연용 매장 사진':s.name)}<div class="shop-card-body"><b>${esc(s.name)}</b><small>${esc(s.category)} · ${esc(s.floor)} ${esc(s.room)}</small><div class="shop-card-bottom"><span>${s.isDemo?'✳ 가상 시연 매장':'🏪 등록 매장'}</span><span>VIEW ↗</span></div></div></button>`).join('')||'<div class="empty">매장이 아직 등록되지 않았습니다.</div>';
const categories=[...new Set(state.shops.map(s=>s.category).filter(Boolean))];$('categoryFilter').innerHTML='<option value="all">전체 업종</option>'+categories.map(a=>`<option value="${esc(a)}">${esc(a)}</option>`).join('');renderDirectory();renderFilterPills();renderOrdersCatalog();const m=$('merchantShop');const old=m.value;m.innerHTML=state.shops.map(s=>`<option value="${esc(s.id)}">${esc(s.name)}</option>`).join('');if(state.shops.some(s=>s.id===old))m.value=old;fillMerchantFields();}
function fillMerchantFields(){const s=shop($('merchantShop').value);if(!s)return;updateMerchantChecklist();$('merchantBlog').value=s.blogUrl||'';$('merchantDelivery').value=s.delivery_url||'';$('merchantMenus').value=(s.menu||[]).map(m=>`${m.name}|${m.price}`).join('\n')}
function renderDirectory(){const q=$('shopSearch').value.trim().toLowerCase();const list=state.shops.filter(s=>{if(state.filter==='favorites'&&!favoriteIds.has(s.id))return false;if(state.filter!=='favorites'&&state.filter!=='all'&&s.category!==state.filter&&s.building!==state.filter)return false;return (s.name+' '+s.category+' '+s.floor+' '+s.room+' '+(s.menu||[]).map(a=>a.name).join(' ')).toLowerCase().includes(q)});$('shopCount').textContent=list.length+' STORES';$('directoryItems').innerHTML=list.map(s=>`<button class="directory-row" data-shop="${esc(s.id)}"><span class="directory-emoji">${image(editorialPhoto(s),s.isDemo?'AI 생성 시연 이미지':s.name)}</span><span><b>${esc(s.name)}</b><small>${esc(s.category)} · ${esc(s.floor||'-')} / ${esc(s.room||'-')} · ${s.coordinateStatus==='verified'?'GPS 등록':'좌표 미검증'}</small></span><i>${favoriteIds.has(s.id)?'♥':'↗'}</i></button>`).join('')||'<div class="empty">검색 결과가 없습니다. 점포대장에 새 매장을 등록하면 여기에 나타납니다.</div>'}
function renderProgress(){const p=state.progress;$('xpText').textContent=p.xp+' XP';$('levelText').textContent='LV '+String(p.level).padStart(2,'0');$('levelBar').style.width=((p.xp%120)/120*100)+'%';$('statVisited').innerHTML=p.uniqueShops+' <small>SPOTS</small>';$('statXp').innerHTML=p.xp+' <small>XP</small>';$('statStreak').innerHTML=p.streak+' <small>DAYS</small>';$('missionLevel').textContent=String(p.level).padStart(2,'0');$('missionXp').textContent=p.xp+' XP';$('missionSubtitle').textContent=`현재 ${p.totalVisits||0}번 발견 · ${p.uniqueShops}개 매장 · ${p.streak}일 연속`;
$('badgesList').innerHTML=(p.badges||[]).map(b=>`<div class="badge-card ${b.earned?'earned':''}"><span class="medal">${esc(b.emoji)}</span><b>${esc(b.label)}</b><small>${b.earned?'✓ 획득 완료':'🔒 아직 미획득'}</small></div>`).join('');$('visitsList').innerHTML=(p.visits||[]).map(v=>`<div class="history-row"><span class="history-icon">✳</span><b>${esc(shop(v.shop_id)?.name||v.shop_id)}</b><small>${esc(v.day)} · ${v.method==='DEMO'?'시연 스탬프':'GPS+QR 인증'}</small></div>`).join('')||'<div class="empty">아직 발견 기록이 없습니다. 매장을 탐험해 첫 번째 배지를 모아보세요.</div>'}
function renderCoupons(){
 const claimed=new Set(state.wallet.map(w=>w.campaign_id+'|'+w.period));
 const today=new Date();const utcKst=new Date(today.toLocaleString('en-US',{timeZone:'Asia/Seoul'}));
 const day=utcKst.getFullYear()+'-'+String(utcKst.getMonth()+1).padStart(2,'0')+'-'+String(utcKst.getDate()).padStart(2,'0');
 function wk(d){const n=new Date(Date.UTC(d.getFullYear(),d.getMonth(),d.getDate()));n.setUTCDate(n.getUTCDate()+4-(n.getUTCDay()||7));const yearStart=new Date(Date.UTC(n.getUTCFullYear(),0,1));return n.getUTCFullYear()+'-W'+String(Math.ceil((((n-yearStart)/86400000)+1)/7)).padStart(2,'0')}
 $('couponCampaigns').innerHTML=state.campaigns.map(c=>{
  const s=shop(c.shop_id);const p=c.recurrence==='DAILY'?day:c.recurrence==='WEEKLY'?wk(utcKst):'ONCE';
  const has=claimed.has(c.id+'|'+p);const nav=buildDirections(s);
  return `<article class="coupon-card"><div class="copy"><small>${esc(s?.name||c.shop_id)} · ${c.recurrence==='DAILY'?'매일 새로 발행':c.recurrence==='WEEKLY'?'매주 새로 발행':'1회 한정'}</small><strong>${esc(c.discount_label)}</strong><b>${esc(c.title)}</b><p>${esc(c.details)} · 발행 회차당 ${esc(c.stock)}장</p><button class="coupon-see-route" data-route-shop="${esc(c.shop_id)}">📍 ${nav.verified?'매장 위치 안내':'가락시장 위치 안내'} · ${esc(s?.floor||'층 미확인')} ${esc(s?.room||'')}</button></div><div class="ribbon"><span>🎁</span><button data-claim="${esc(c.id)}" ${has?'disabled':''}>${has?'받음 ✓':'쿠폰 받기'}</button></div></article>`
 }).join('')||'<div class="empty">현재 발행 중인 쿠폰이 없습니다.</div>';
 $('statCoupon').innerHTML=state.wallet.length+' <small>COUPONS</small>';
 $('walletDot').classList.toggle('on',!!state.wallet.length);
 $('walletItems').innerHTML=state.wallet.map(w=>{
   const used=!!w.redeemed_at||w.expired;const s=shop(w.shop_id);const nav=buildDirections(s);
   return `<article class="wallet-item ${used?'inactive':''}"><button class="ticket wallet-click" type="button" data-route-shop="${esc(w.shop_id)}" aria-label="${esc(w.shop_name)} 쿠폰 매장 길안내 보기"><span>🎟️ 쿠폰 누르면 길안내</span><strong>${esc(w.code)}</strong></button><div class="wallet-copy"><b>${esc(w.shop_name)} · ${esc(w.discount_label)}</b><small>${esc(w.title)} · ${esc(w.expires_at)} 까지</small><small>${esc(s?.building||'')} ${esc(s?.floor||'')} ${esc(s?.room||'')} ${nav.verified?'· GPS 확인됨':'· 매장 GPS 미확인'}</small></div><span class="${used?'used':''}">${w.redeemed_at?'사용 완료':w.expired?'기간 만료':'사용 가능'}</span><div class="wallet-actions"><a class="wallet-nav" target="_blank" rel="noopener noreferrer" href="${esc(nav.url)}">${esc(nav.buttonLabel)} ↗</a><button class="wallet-copy-code" data-copy-code="${esc(w.code)}">번호 복사</button></div></article>`
 }).join('')||'<div class="empty">내 지갑이 비어 있습니다. 위에서 원하는 쿠폰을 받아보세요.</div>';
}

function renderOrdersCatalog(){$('orderCatalog').innerHTML=state.shops.filter(s=>(s.menu||[]).length).map(s=>`<article class="order-shop">${image(editorialPhoto(s),s.isDemo?'AI 생성 시연용 메뉴 사진':s.name)}<div><h3>${esc(s.name)}</h3><p>${s.isDemo?'가상 시연 메뉴 · 결제 불가':'상인 등록 메뉴 · 미연동'}</p><select id="list-${esc(s.id)}">${s.menu.map((m,i)=>`<option value="${i}">${esc(m.name)} · ${won(m.price)}</option>`).join('')}</select><button data-order-shop="${esc(s.id)}">메뉴 선택하고 요청하기 ↗</button></div></article>`).join('')||'<div class="empty">메뉴가 등록되지 않았습니다.</div>'}
function renderOrders(){$('ordersList').innerHTML=state.orders.map(o=>`<div class="history-row"><span class="history-icon">🛵</span><b>${esc(o.shop_id)} · ${esc(o.menu_name)} × ${o.quantity} <small>${won(o.total)} · ${o.mode==='pickup'?'포장 시연':'배달 문의 시연'}</small></b><small>${esc(o.status)}<br>${esc(o.id)}</small></div>`).join('')||'<div class="empty">시연 요청 내역이 없습니다.</div>'}
async function refreshProgress(){try{state.progress=await get('/api/progress');renderProgress()}catch(e){toast(e.message)}}

async function refreshWallet(){try{state.wallet=(await get('/api/wallet')).items;renderCoupons()}catch(e){toast(e.message)}}
async function refreshOrders(){try{state.orders=(await get('/api/orders')).items;renderOrders()}catch(e){toast(e.message)}}
async function load(){try{const a=await get('/api/experience');state.shops=a.shops;state.campaigns=a.campaigns;state.demo=a.demoMode;$('serverStatus').textContent='● 베타 서버 연결됨';renderShops();await Promise.all([refreshProgress(),refreshWallet(),refreshOrders()]);const url=new URL(location.href);const sid=url.searchParams.get('shop');const qr=url.searchParams.get('qr');if(sid){history.replaceState(null,'','/');openShop(sid);if(qr){setTimeout(()=>{if(confirm('이 점포의 현장 QR이 확인되었습니다. GPS를 받아 방문 인증할까요?'))checkin(sid,qr)},150)}}}catch(e){$('serverStatus').textContent='● 서버 연결 필요';$('featuredShops').innerHTML='<div class="empty">로컬 Python 서버 실행 후 접속하세요. '+esc(e.message)+'</div>';toast('서버 연결을 확인하세요: '+e.message)}}
function position(){return new Promise((resolve,reject)=>{if(!navigator.geolocation){reject(Error('이 기기는 위치 기능을 지원하지 않습니다.'));return;}if(!window.isSecureContext){reject(Error('GPS는 HTTPS 또는 localhost에서만 가능합니다.'));return}navigator.geolocation.getCurrentPosition(p=>{state.geo={latitude:p.coords.latitude,longitude:p.coords.longitude,accuracy:p.coords.accuracy};resolve(state.geo)},e=>reject(Error(e.message)),{enableHighAccuracy:true,maximumAge:0,timeout:12500})})}
function meters(a,b,c,d){const p=Math.PI/180;const x=(c-a)*p,y=(d-b)*p;const z=Math.sin(x/2)**2+Math.cos(a*p)*Math.cos(c*p)*Math.sin(y/2)**2;return 6371000*2*Math.atan2(Math.sqrt(z),Math.sqrt(1-z))}
async function showPosition(){try{const x=await position();const found=state.shops.filter(s=>s.coordinateStatus==='verified'&&!s.isDemo&&s.latitude!=null&&s.longitude!=null).map(s=>({...s,meters:meters(x.latitude,x.longitude,+s.latitude,+s.longitude)})).sort((a,b)=>a.meters-b.meters).slice(0,6);
$('gpsInfo').innerHTML=`<b>GPS 확인 · 정확도 약 ${Math.round(x.accuracy)}m</b><p>원시 GPS는 위치 판단에만 이용합니다. ${found.length?'검증된 좌표를 가진 가까운 등록 매장:':'현재 정확 좌표가 검증된 매장이 없습니다.'}</p>${found.map(s=>`<button class="gps-nearby" data-shop="${esc(s.id)}">📍 ${esc(s.name)} · 약 ${Math.round(s.meters)}m ↗</button>`).join('')}`;toast('내 GPS 위치 확인 완료. 원시 좌표는 서버에 저장하지 않습니다.')}catch(e){toast('GPS: '+e.message)}}
async function checkin(id,qrToken){try{const x=await position();const y=await post('/api/checkin',{shopId:id,qrToken,...x});toast(y.message);await refreshProgress()}catch(e){toast('방문 인증: '+e.message)}}
function stopCamera(){if(state.scanTimer){clearInterval(state.scanTimer);state.scanTimer=null}if(state.stream){state.stream.getTracks().forEach(t=>t.stop());state.stream=null}$('cameraVideo').srcObject=null;state.scanBusy=false;$('cameraState').textContent='카메라를 껐습니다.';$('arDiscovery').hidden=true;$('arDiscovery').innerHTML=''}
function openCamera(){ $('scannerDialog').showModal(); }
async function activateCamera(){try{if(!window.isSecureContext)throw Error('카메라는 HTTPS 또는 localhost 주소에서만 작동합니다.');if(!navigator.mediaDevices?.getUserMedia)throw Error('이 기기의 카메라 API를 사용할 수 없습니다.');stopCamera();state.stream=await navigator.mediaDevices.getUserMedia({audio:false,video:{facingMode:{ideal:'environment'},width:{ideal:1280},height:{ideal:720}}});const video=$('cameraVideo');video.srcObject=state.stream;await video.play();$('cameraState').textContent='카메라 작동 중 · QR 표식을 화면 중앙에 맞추세요.';
if('BarcodeDetector' in window){const supported=await BarcodeDetector.getSupportedFormats?.().catch(()=>[])||[];if(!supported.length||supported.includes('qr_code')){state.detector=new BarcodeDetector({formats:['qr_code']});state.scanTimer=setInterval(scanFrame,450)}else{$('cameraState').textContent='브라우저 QR 디코더를 지원하지 않습니다. 사진 업로드 또는 수동 검색을 사용하세요.'}}else{$('cameraState').textContent='이 브라우저는 자동 QR 인식을 지원하지 않습니다. 사진 업로드/직접 입력으로 찾으세요.'}
}catch(e){toast('카메라: '+e.message);$('cameraState').textContent=e.message}}
async function scanFrame(){if(state.scanBusy||!state.detector||!state.stream)return;state.scanBusy=true;try{const hits=await state.detector.detect($('cameraVideo'));if(hits.length){handleCode(hits[0].rawValue)}}catch(e){if(e.name!=='NotSupportedError')console.warn('QR scan',e)}finally{state.scanBusy=false}}
function showARDiscovery(id,token='',method='QR'){
 const s=shop(id);if(!s){toast('매장 정보가 없습니다.');return}
 if(state.scanTimer){clearInterval(state.scanTimer);state.scanTimer=null}
 const best=s.menu?.[0];const promo=state.campaigns.find(c=>c.shop_id===id);
 const overlay=$('arDiscovery');overlay.hidden=false;
 overlay.innerHTML=`<div class="ar-title">✳ ${esc(s.name)} 발견!</div><div class="ar-source">${esc(method)} 매칭 · ${s.isDemo?'가상 시연 매장':'등록 매장'} · 방문 인증과 별개</div><div class="ar-menu">${s.menu_image?image(s.menu_image,'메뉴 이미지'):''}<p><b>${esc(best?.name||'등록 메뉴 확인')}</b><br>${best?won(best.price):'가격 미등록'}<br>${promo?'🎟️ '+esc(promo.discount_label):'현재 쿠폰 없음'}</p></div><button id="arOpenShop">매장 메뉴·블로그·쿠폰 보기 ↗</button> <button id="arRouteShop">📍 Google 지도 길안내</button> ${token?'<button id="arCheckin">📍 GPS 방문 인증</button>':''}`;
 $('arOpenShop').onclick=()=>{stopCamera();$('scannerDialog').close();openShop(id)};
 $('arCheckin')?.addEventListener('click',()=>checkin(id,token));$('arRouteShop')?.addEventListener('click',()=>{stopCamera();$('scannerDialog').close();showCouponRoute(id)});
 $('cameraState').textContent='매장을 발견했습니다! 메뉴판과 혜택을 보려면 선택하세요.';
}
function handleCode(raw){if(!raw)return;let id='',token='';raw=String(raw).trim();if(raw.startsWith('GARAKLAND:'))id=raw.slice('GARAKLAND:'.length);else if(/^[a-zA-Z0-9_-]{1,80}$/.test(raw))id=raw;else{try{const u=new URL(raw);id=u.searchParams.get('shop')||u.searchParams.get('shopId')||'';token=u.searchParams.get('token')||u.searchParams.get('qr')||'';}catch{}}
 if(!shop(id)){toast('등록되지 않은 점포 표식입니다.');return}showARDiscovery(id,token,'QR');toast('매장 발견! 카메라 위에 메뉴와 쿠폰이 나타났습니다.');}
async function photoRecognize(canvas){const img=canvas.toDataURL('image/jpeg',.82).split(',')[1];$('cameraState').textContent='기준 이미지와 간판 특징점을 비교하는 중…';try{const r=await post('/api/recognize',{image:img});if(!r.supported)throw Error(r.message);if(!r.matched)throw Error(r.reason);showARDiscovery(r.shopId,'','PHOTO ORB');toast(`등록 사진과 일치하는 매장 발견 · 특징점 ${r.inliers}개 (위치 인증과는 별개)`)}catch(e){toast('사진 인식: '+e.message);$('cameraState').textContent=e.message}}
function capture(){const video=$('cameraVideo');if(!state.stream||!video.videoWidth){toast('먼저 카메라를 켜세요.');return}const canvas=document.createElement('canvas');const scale=Math.min(1,1150/video.videoWidth);canvas.width=Math.round(video.videoWidth*scale);canvas.height=Math.round(video.videoHeight*scale);canvas.getContext('2d').drawImage(video,0,0,canvas.width,canvas.height);photoRecognize(canvas)}
async function uploadPhoto(file){if(!file)return;const img=new Image();const src=URL.createObjectURL(file);img.onload=()=>{URL.revokeObjectURL(src);const k=Math.min(1,1150/Math.max(img.width,img.height));const canvas=document.createElement('canvas');canvas.width=Math.round(img.width*k);canvas.height=Math.round(img.height*k);canvas.getContext('2d').drawImage(img,0,0,canvas.width,canvas.height);photoRecognize(canvas)};img.onerror=()=>{URL.revokeObjectURL(src);toast('이미지 읽기 오류')};img.src=src}
function startOrder(id,index=0){const s=shop(id);if(!s)return;state.orderShop=s;$('shopDialog').close();$('orderShopName').value=s.name;$('orderMenu').innerHTML=(s.menu||[]).map((m,i)=>`<option value="${i}">${esc(m.name)} · ${won(m.price)}</option>`).join('');$('orderMenu').value=String(index);$('orderQty').value='1';$('orderNote').value='';updateOrderTotal();$('orderDialog').showModal();}
function updateOrderTotal(){const m=state.orderShop?.menu?.[Number($('orderMenu').value)];$('orderTotal').textContent='총 '+won((m?.price||0)*Number($('orderQty').value||1))}
async function requestOrder(){try{const s=state.orderShop;const m=s?.menu?.[Number($('orderMenu').value)];if(!m)throw Error('메뉴 선택이 필요합니다');const r=await post('/api/orders',{shopId:s.id,menuName:m.name,quantity:Number($('orderQty').value),mode:$('orderMode').value,note:$('orderNote').value});$('orderDialog').close();toast('시연 주문 '+r.orderId+' 저장 · 실제 배달·결제 없음');await refreshOrders();go('delivery')}catch(e){toast(e.message)}}
function merchantHeaders(){const result={};if($('merchantKey').value.trim())result['X-Garak-Merchant-Key']=$('merchantKey').value.trim();if($('adminKey').value.trim())result['X-Garak-Admin-Token']=$('adminKey').value.trim();return result}
async function merchantRun(fn){try{await fn();}catch(e){$('merchantResult').textContent='오류: '+e.message;toast(e.message)}}
function merchantShop(){return $('merchantShop').value}
function attach(){$('merchantShop').addEventListener('change',fillMerchantFields);document.querySelectorAll('[data-page]').forEach(b=>b.addEventListener('click',()=>go(b.dataset.page)));document.querySelectorAll('[data-gopage]').forEach(b=>b.addEventListener('click',()=>go(b.dataset.gopage)));$('walletShortcut').onclick=()=>go('coupons');$('railCamera').onclick=openCamera;$('startCamera').onclick=$('howScan').onclick=openCamera;$('cameraActivate').onclick=activateCamera;$('capturePhoto').onclick=capture;$('photoFile').onchange=e=>uploadPhoto(e.target.files?.[0]);$('manualSearch').onclick=()=>handleCode($('manualCode').value);
document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>$(b.dataset.close).close());$('scannerDialog').addEventListener('close',stopCamera);
document.body.addEventListener('click',async e=>{let s=e.target.closest('[data-shop]');if(s){openShop(s.dataset.shop);return}let v=e.target.closest('[data-zone]');if(v){state.filter=v.dataset.zone;$('categoryFilter').value='all';renderDirectory();return}let route=e.target.closest('[data-route-shop]');if(route){showCouponRoute(route.dataset.routeShop);return}
let copy=e.target.closest('[data-copy-code]');if(copy){try{await navigator.clipboard.writeText(copy.dataset.copyCode);toast('쿠폰 번호를 복사했습니다.')}catch{toast('쿠폰 번호를 길게 눌러 복사해 주세요.')}return}
let c=e.target.closest('[data-claim]');if(c){try{const result=await post('/api/coupons/claim',{campaignId:c.dataset.claim});toast('쿠폰 '+result.code+' 발급 · '+result.notice);await refreshWallet();const campaign=state.campaigns.find(x=>x.id===c.dataset.claim);if(campaign)showCouponRoute(campaign.shop_id,result.code)}catch(err){toast(err.message)}return}let o=e.target.closest('[data-order-shop]');if(o){const selector=o.closest('.order-shop')?.querySelector('select');startOrder(o.dataset.orderShop,Number(selector?.value||0))}});
$('shopSearch').addEventListener('input',renderDirectory);$('categoryFilter').onchange=e=>{state.filter=e.target.value;renderDirectory();renderFilterPills()};$('locateMe').onclick=showPosition;$('orderMenu').onchange=updateOrderTotal;$('orderQty').oninput=updateOrderTotal;$('orderForm').onsubmit=e=>e.preventDefault();$('sendOrder').onclick=e=>{e.preventDefault();requestOrder()};
$('saveMerchantProfile').onclick=()=>merchantRun(async()=>{
  const lines=$('merchantMenus').value.split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
  const menu=lines.map(line=>{const i=line.lastIndexOf('|');if(i<1)throw Error('메뉴명|가격 형태로 입력하세요');return {name:line.slice(0,i).trim(),price:Number(line.slice(i+1).trim())}});
  const result=await post('/api/merchant/profile',{shopId:merchantShop(),blogUrl:$('merchantBlog').value.trim(),deliveryUrl:$('merchantDelivery').value.trim(),menu},merchantHeaders());
  $('merchantResult').textContent='매장 홍보·메뉴 정보 저장 완료';toast('등록 완료');const a=await get('/api/experience');state.shops=a.shops;renderShops();
});
$('uploadMerchantPhoto').onclick=()=>merchantRun(async()=>{
  const file=$('merchantPhoto').files?.[0];if(!file)throw Error('사진 파일을 선택해 주세요');
  if(file.size>3_000_000)throw Error('파일 크기는 3MB 이내여야 합니다');
  const img=new Image(),u=URL.createObjectURL(file);
  const photo=await new Promise((resolve,reject)=>{img.onload=()=>{URL.revokeObjectURL(u);const k=Math.min(1,1200/Math.max(img.width,img.height));const canvas=document.createElement('canvas');canvas.width=Math.round(img.width*k);canvas.height=Math.round(img.height*k);canvas.getContext('2d').drawImage(img,0,0,canvas.width,canvas.height);resolve(canvas.toDataURL('image/jpeg',.8).split(',')[1])};img.onerror=()=>{URL.revokeObjectURL(u);reject(Error('사진 로딩 오류'))};img.src=u});
  const r=await post('/api/merchant/upload-photo',{shopId:merchantShop(),kind:$('merchantPhotoKind').value,image:photo},merchantHeaders());
  $('photoResult').textContent='등록된 사진 경로: '+r.path;toast('사진 등록 완료');const a=await get('/api/experience');state.shops=a.shops;renderShops();
});
$('issueMerchantKey').onclick=()=>merchantRun(async()=>{const r=await post('/api/admin/merchant-key',{shopId:merchantShop()},{'X-Garak-Admin-Token':$('adminKey').value.trim()});$('merchantKey').value=r.merchantKey;$('keyResult').textContent='새 상인 비밀키를 발급해 입력했습니다. 이 창을 나가면 다시 볼 수 없습니다. 이전 키는 취소됐습니다.';toast('상인 키 발급 완료')});
$('issueQr').onclick=()=>merchantRun(async()=>{const r=await get('/api/merchant/qr?shopId='+encodeURIComponent(merchantShop()),merchantHeaders());$('qrPreview').innerHTML=(r.image?`<img alt="현재 매장 방문 QR" src="${r.image}">`:'<p>qrcode 의존성 설치 후 QR 이미지를 생성합니다.</p>')+`<p>만료 3분 · 매장 현장에서 새로고침 필요</p><p>QR 링크: ${esc(r.url)}</p>`;toast('현장용 QR 발급 (3분 후 만료)')});
$('createCampaign').onclick=()=>merchantRun(async()=>{const r=await post('/api/merchant/campaign',{shopId:merchantShop(),title:$('campaignTitle').value,discountLabel:$('campaignDiscount').value,details:$('campaignDetails').value,stock:Number($('campaignStock').value),recurrence:$('campaignPeriod').value},merchantHeaders());$('merchantResult').textContent='쿠폰 캠페인 발행 완료: '+r.campaignId;toast('정기 쿠폰 발행 완료');const experience=await get('/api/experience');state.campaigns=experience.campaigns;renderCoupons()});
$('redeemCoupon').onclick=()=>merchantRun(async()=>{const r=await post('/api/merchant/redeem',{shopId:merchantShop(),code:$('redeemCode').value},merchantHeaders());$('merchantResult').textContent='쿠폰 사용 처리 완료 · '+r.status;await refreshWallet()});
for(const [id,status] of [['ackOrder','DEMO_ACKNOWLEDGED'],['cancelOrder','DEMO_CANCELLED']])$(id).onclick=()=>merchantRun(async()=>{const r=await post('/api/merchant/order-status',{shopId:merchantShop(),orderId:$('merchantOrderId').value,status},merchantHeaders());$('merchantResult').textContent='시연 주문 상태 처리 완료 · '+status;await refreshOrders()});
}
// v4 guided discovery + favorites + keyboard search; all mutations are client-only.
document.body.addEventListener('click',e=>{
 const quick=e.target.closest('[data-quick-category]');
 if(quick){const category=quick.dataset.quickCategory;state.filter=category;$('shopSearch').value='';$('categoryFilter').value=category;go('directory');renderDirectory();renderFilterPills();return}
 const pill=e.target.closest('[data-filter-pill]');
 if(pill){state.filter=pill.dataset.filterPill;$('categoryFilter').value=state.filter==='favorites'?'all':state.filter;renderDirectory();renderFilterPills();return}
 const jump=e.target.closest('[data-jump-search]');if(jump){go('directory');$('shopSearch').focus();return}
});
document.addEventListener('keydown',e=>{const tag=e.target?.tagName||'';if(e.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(tag)&&!e.ctrlKey&&!e.metaKey){e.preventDefault();go('directory');$('shopSearch').focus()}});
attach();load();
export {esc,won,link};
