'use strict';
const $=id=>document.getElementById(id);
let adminToken='',modules=[],viewFilter='all',activity=[],currentMetrics={};
let toastTimeout;
function toast(message){const t=$('toast');t.textContent=message;t.classList.add('show');clearTimeout(toastTimeout);toastTimeout=setTimeout(()=>t.classList.remove('show'),4400)}
const fmt=v=>Number(v||0).toLocaleString('ko-KR');
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&gt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
async function api(path,{method='GET',data}={}){
 const opt={method,headers:{'X-Garak-Admin-Token':adminToken,'X-Garak-Client':'1'}};
 if(data!==undefined){opt.headers['Content-Type']='application/json';opt.body=JSON.stringify(data)}
 const res=await fetch(path,opt);let body;try{body=await res.json()}catch{throw Error(`서버에서 올바른 응답이 없습니다 (${res.status})`)}
 if(!res.ok)throw Error(body.error||`HTTP ${res.status}`);return body;
}
const icons={stores:'▣',map:'⌖',ar:'◎',products:'▤',coupons:'◇',giftcards:'◈',orders:'▥',marketing:'◉',merchants:'♟',erp:'▦',content:'▤',analytics:'▥',custom:'✣'};
function renderMetrics(m){currentMetrics=m;const val=(id,x)=>$(id).textContent=fmt(x);
 val('kpiStores',m.stores);val('kpiCoupons',m.issuedCoupons+m.legacyCoupons);val('kpiVisits',m.visits);val('kpiProducts',m.products);
 $('kpiStoresNote').textContent=`실점포 GPS 검증 ${fmt(m.verifiedLocations)}건 · 시연 ${fmt(m.demoStores)}건`;
 $('kpiCouponNote').textContent=`v5 쿠폰 사용률 ${fmt(m.couponRedeemRatePercent)}%`;
 const s=[['진행 특가',m.activeOffers],['마케팅 예약(시연)',m.campaigns],['주문 접수(시연)',m.demoOrders],['연합 시연권',m.giftcardAccounts],['시연권 거래',m.giftcardTransactions],['검토된 계약 서류',m.merchantDocsReviewed],['수신 대상 미리보기',m.outboxPreview],['운영 작업',m.pendingTasks]];
 $('otherStats').innerHTML=s.map(([k,v])=>`<div class="stat-line"><span>${esc(k)}</span><b>${fmt(v)}</b></div>`).join('');
}
function filtered(){const q=$('moduleSearch').value.trim().toLowerCase();return modules.filter(m=>(viewFilter==='all'||(viewFilter==='on'&&m.enabled)||(viewFilter==='off'&&!m.enabled))&&(!q||[m.name,m.description,m.id].some(v=>v.toLowerCase().includes(q))))}
function renderModules(){const active=modules.filter(m=>m.ready).length;$('activeCount').textContent=`${active} / ${modules.length} 사용 중`;
 $('moduleGrid').innerHTML=filtered().map(m=>`<article class="module ${m.ready?'':'off'}" data-id="${esc(m.id)}"><div class="module-heading"><div class="module-icon" aria-hidden="true">${icons[m.id]||icons.custom}</div><div><h3>${esc(m.name)}</h3><span class="module-status"><i></i>${m.ready?'시연 모드 운영':'운영 중지'}</span></div></div><p>${esc(m.description)}</p><div class="module-foot"><a href="${esc(m.url)}">관련 페이지 바로가기 ↗</a><button type="button" class="toggle ${m.enabled?'on':''}" data-action="toggle" data-id="${esc(m.id)}" aria-label="${esc(m.name)} ${m.enabled?'중지':'사용'}" aria-pressed="${m.enabled}">${m.enabled?'사용 중':'중지됨'}</button></div></article>`).join('')||'<p class="muted">검색 결과가 없습니다.</p>';
}
function chart(rows){activity=rows;
 const root=$('activityChart');const max=Math.max(1,...rows.flatMap(r=>[r.coupons,r.visits,r.orders]));
 root.innerHTML=rows.map(r=>`<div class="bar-group" title="${esc(r.date)} / 쿠폰 ${fmt(r.coupons)}, 방문 ${fmt(r.visits)}, 주문 ${fmt(r.orders)}"><div class="bar bar-a ${r.coupons===0?'bar-zero':''}" style="height:${Math.max(1,r.coupons/max*100)}%"></div><div class="bar bar-b ${r.visits===0?'bar-zero':''}" style="height:${Math.max(1,r.visits/max*100)}%"></div><div class="bar bar-c ${r.orders===0?'bar-zero':''}" style="height:${Math.max(1,r.orders/max*100)}%"></div></div>`).join('');
 $('chartAxis').innerHTML=`<span>${esc(rows[0]?.date||'')}</span><span>최대 ${fmt(max)}건 / 일</span><span>${esc(rows[rows.length-1]?.date||'')}</span>`;
 root.setAttribute('aria-label',`최근 ${rows.length}일 일별 쿠폰·방문·주문 현황. 데이터 최대 ${max}건`);
}
function renderReadiness(d){$('readinessList').innerHTML=d.checklist.map(r=>`<div class="check-row"><div class="check-icon ${r.passed?'ok':''}">${r.passed?'✓':'!'}</div><div><b>${esc(r.label)} · ${r.passed?'내부 기준 확인':'별도 확인 필요'}</b><p>${esc(r.requirements)}</p></div></div>`).join('')}
function renderJobs(items){$('jobList').innerHTML=items.length?items.map(j=>`<div class="job-item"><div><strong>${esc(j.label)}</strong><small>${esc(j.kind)} · ${esc(j.cadence)} · ${esc(j.due_at.slice(0,16).replace('T',' '))}</small><small>상태: ${esc(j.status)} · 실행 ${fmt(j.run_count)}회</small></div><div class="job-buttons"><button class="tiny-btn" data-job="run" data-id="${esc(j.id)}" ${j.status==='cancelled'||(j.status==='completed'&&j.cadence==='once')?'disabled':''}>실행</button><button class="tiny-btn danger" data-job="cancel" data-id="${esc(j.id)}" ${j.status==='cancelled'?'disabled':''}>취소</button></div></div>`).join(''):'<p class="muted">등록된 작업이 없습니다. 왼쪽에서 예약을 추가하세요.</p>'}
function renderAudit(items){$('auditRows').innerHTML=items.length?items.map(e=>`<tr><td>${esc(e.created_at.replace('T',' ').slice(0,19))}</td><td><b>${esc(e.action)}</b></td><td>${esc(e.target)}</td><td>${esc(e.detail.slice(0,180))}</td></tr>`).join(''):'<tr><td colspan="4" class="muted">아직 변경 기록이 없습니다.</td></tr>'}
async function load(){const d=await api('/api/v8/dashboard');modules=d.modules;renderMetrics(d.metrics);renderModules();chart(d.trend);renderReadiness(d.readiness);renderJobs(d.recentJobs);renderAudit(d.recentAudit)}
async function jobs(){renderJobs((await api('/api/v8/jobs')).items)}
async function audit(){renderAudit((await api('/api/v8/audit')).items)}
function localDue(){const d=new Date(Date.now()+60000);const two=n=>String(n).padStart(2,'0');return `${d.getFullYear()}-${two(d.getMonth()+1)}-${two(d.getDate())}T${two(d.getHours())}:${two(d.getMinutes())}`}
$('jobDue').value=localDue();
$('authForm').addEventListener('submit',async e=>{e.preventDefault();const key=$('adminToken').value.trim();if(!key)return toast('관리자 토큰을 입력하세요.');adminToken=key;try{await load();$('secured').hidden=false;$('locked').hidden=true;$('authPanel').style.display='none';$('adminToken').value='';toast('관리자 운영 허브에 안전하게 연결되었습니다.')}catch(err){adminToken='';toast(err.message)}});
$('refreshBtn').addEventListener('click',async()=>{if(!adminToken)return toast('관리자 인증 후 이용해 주세요.');try{await load();toast('현황을 새로고침했습니다.')}catch(e){toast(e.message)}});
$('moduleSearch').addEventListener('input',renderModules);
document.querySelectorAll('.filter').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.filter').forEach(x=>x.classList.remove('active'));b.classList.add('active');viewFilter=b.dataset.filter;renderModules()}));
$('moduleGrid').addEventListener('click',async e=>{const b=e.target.closest('[data-action="toggle"]');if(!b)return;const item=modules.find(x=>x.id===b.dataset.id);if(!item)return;
 if(!confirm(`"${item.name}" 모듈을 ${item.enabled?'중지':'사용'}하시겠습니까?\n하위 모듈과 관련 API에 영향을 줄 수 있습니다.`))return;
 b.disabled=true;try{const d=await api('/api/v8/module/config',{method:'POST',data:{id:item.id,enabled:!item.enabled,note:'허브 화면에서 변경'}});modules=modules.map(m=>m.id===item.id?d.module:m);renderModules();await audit();toast(`${item.name}: ${d.module.enabled?'사용':'중지'} 설정 저장`)}catch(error){toast(error.message);b.disabled=false}});
$('period').addEventListener('change',async e=>{if(!adminToken)return;try{const x=await api('/api/v8/analytics?days='+encodeURIComponent(e.target.value));chart(x.daily);renderMetrics(x.metrics)}catch(err){toast(err.message)}});
$('jobForm').addEventListener('submit',async e=>{e.preventDefault();if(!adminToken)return toast('관리자 인증 후 이용하세요.');const date=$('jobDue').value;if(!date)return toast('예약 날짜와 시간을 선택하세요.');const dueAt=date+':00+09:00';
 const body={kind:$('jobKind').value,moduleId:'analytics',label:$('jobLabel').value,dueAt,cadence:$('jobCadence').value};try{await api('/api/v8/jobs/create',{method:'POST',data:body});await jobs();$('jobLabel').value='';toast('검수 작업을 등록했습니다. 자동 실행은 하지 않습니다.')}catch(err){toast(err.message)}});
$('jobList').addEventListener('click',async e=>{const b=e.target.closest('[data-job]');if(!b)return;const mode=b.dataset.job;if(!confirm(`${mode==='run'?'검수 작업을 지금 수동으로 실행':'해당 작업을 취소'}하시겠습니까?`))return;
 b.disabled=true;try{const r=await api(mode==='run'?'/api/v8/jobs/run':'/api/v8/jobs/cancel',{method:'POST',data:{id:b.dataset.id}});await Promise.all([jobs(),audit()]);if(mode==='run'){await load();await jobs();}toast(mode==='run'?`실행 완료 · ${r.result?.label||'점검'}`:'작업을 취소했습니다.')}catch(err){toast(err.message);b.disabled=false}});
$('reloadJobs').addEventListener('click',()=>jobs().catch(e=>toast(e.message)));
$('reloadAudit').addEventListener('click',()=>audit().catch(e=>toast(e.message)));
$('mobileMenu').addEventListener('click',()=>{$('side').classList.toggle('open')});
document.querySelectorAll('.sidebar nav a').forEach(a=>a.addEventListener('click',()=>$('side').classList.remove('open')));

$('registerForm').addEventListener('submit',async e=>{e.preventDefault();if(!adminToken)return toast('관리자 인증 후 이용해 주세요.');const data=Object.fromEntries(new FormData(e.target).entries());try{const r=await api('/api/v8/modules/register',{method:'POST',data});await load();e.target.reset();$('registerBox').open=false;toast(`${r.moduleId} 연결형 모듈을 등록했습니다. 별도 기능 코드는 자동 생성되지 않습니다.`)}catch(error){toast(error.message)}});
