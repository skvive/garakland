import {floorOrder,halls,categories,displayZones,floorDescriptions,stores,defaultOrigin} from './data.mjs';
import {readSelection,lookupStores,findShop,findZone,buildSchematicRoute,areaSummary,qualityStats} from './nav-model.mjs';
const el=id=>document.getElementById(id);
const escapeText=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state={...readSelection(new URLSearchParams(location.search)),category:'all',destination:null,selectedZone:null,zoom:1,origin:{...defaultOrigin}};
const quality=qualityStats();
function init(){
  halls.forEach(h=>{const b=document.createElement('button');b.type='button';b.dataset.hall=h.id;b.textContent=h.label;el('hallTabs').append(b);});
  floorOrder.forEach(f=>{
    const b=document.createElement('button');b.type='button';b.dataset.floor=f;b.textContent=f;el('floorTabs').append(b);
    const option=document.createElement('option');option.value=f;option.textContent=f;el('originFloor').append(option);
  });
  Object.entries(categories).forEach(([id,cat])=>{
    const opt=document.createElement('option');opt.value=id;opt.textContent=cat.label;el('categoryFilter').append(opt);
  });
  el('searchInput').value=state.search;
  el('originHall').value=state.origin.hall;el('originFloor').value=state.origin.floor;
  el('hallTabs').addEventListener('click',e=>{
    const target=e.target.closest('[data-hall]');
    if(!target)return;
    state.hall=target.dataset.hall;state.destination=null;state.selectedZone=null;render();
  });
  el('floorTabs').addEventListener('click',e=>{
    const target=e.target.closest('[data-floor]');
    if(!target)return;
    state.floor=target.dataset.floor;state.destination=null;state.selectedZone=null;render();
  });
  el('categoryFilter').addEventListener('change',e=>{state.category=e.target.value;state.destination=null;state.selectedZone=null;render();});
  el('searchInput').addEventListener('input',e=>{state.search=e.target.value.slice(0,120);state.destination=null;state.selectedZone=null;render();});
  el('storeList').addEventListener('click',e=>{
    const b=e.target.closest('[data-store]');
    if(!b)return;
    const shop=findShop(b.dataset.store);
    if(!shop)return;
    state.floor=shop.floor;state.hall=shop.hall;state.category='all';state.destination={name:shop.name,hall:shop.hall,floor:shop.floor};
    state.selectedZone=null;render();
  });
  el('floorSvg').addEventListener('click',e=>{
    const z=e.target.closest('[data-zone]');
    if(z)selectZone(z.dataset.zone);
  });
  el('floorSvg').addEventListener('keydown',e=>{
    if(e.key!=='Enter'&&e.key!==' ')return;
    const z=e.target.closest('[data-zone]');if(z){e.preventDefault();selectZone(z.dataset.zone);}
  });
  document.querySelectorAll('[data-hall-link]').forEach(b=>b.addEventListener('click',()=>{
    state.hall=b.dataset.hallLink;state.selectedZone=null;state.destination=null;render();
    el('hallTabs').scrollIntoView({behavior:'smooth',block:'nearest'});
  }));
  el('originHall').addEventListener('change',e=>{state.origin.hall=e.target.value;drawRoute();});
  el('originFloor').addEventListener('change',e=>{state.origin.floor=e.target.value;drawRoute();});
  el('zoomIn').addEventListener('click',()=>setZoom(state.zoom+.2));
  el('zoomOut').addEventListener('click',()=>setZoom(state.zoom-.2));
  el('zoomReset').addEventListener('click',()=>setZoom(1));
  render();
}
function setZoom(value){
  state.zoom=Math.round(Math.max(1,Math.min(2,value))*10)/10;
  el('zoomValue').value=Math.round(state.zoom*100)+'%';
  el('zoomValue').textContent=Math.round(state.zoom*100)+'%';
  el('floorSvg').style.width=state.zoom===1?'100%':Math.round(100*state.zoom)+'%';
}
function selectZone(id){
  const z=findZone(state.floor,id,state.hall);
  if(!z)return;
  state.selectedZone=z.id;
  state.destination={name:z.label,hall:state.hall==='all'?'all':state.hall,floor:state.floor};
  render();
}
function render(){
  document.querySelectorAll('[data-hall]').forEach(b=>{
    const selected=b.dataset.hall===state.hall;b.setAttribute('aria-pressed',String(selected));
  });
  document.querySelectorAll('[data-floor]').forEach(b=>{
    const selected=b.dataset.floor===state.floor;b.setAttribute('aria-pressed',String(selected));
  });
  el('categoryFilter').value=state.category;
  el('mapHeading').textContent=state.floor+' · '+areaSummary(state.floor);
  el('mapSub').textContent=(state.hall==='all'?'전체 관':state.hall+'관 선택')+' · 구역 구분은 범주 기반 시연입니다.';
  renderStores();
  renderMap();
  drawRoute();
  const params=new URLSearchParams();
  params.set('floor',state.floor);params.set('hall',state.hall);
  if(state.search.trim())params.set('q',state.search.trim());
  history.replaceState(null,'',location.pathname+'?'+params.toString());
}
function renderStores(){
  const searchActive=state.search.trim().length>0;
  const items=lookupStores({
    hall:state.hall,floor:state.floor,query:state.search,
    allFloors:searchActive,category:state.category
  });
  el('searchMeta').textContent=(searchActive?'전체 층 검색 · ':'')+'안내판 수록 매장 '+items.length+'곳 · 정확 좌표 확인 '+quality.locatedStores+'곳';
  const list=el('storeList');list.replaceChildren();
  if(!items.length){
    const p=document.createElement('p');p.className='empty-results';
    p.textContent=searchActive?'해당 검색어의 안내판 매장 정보가 없습니다. 다른 검색어를 사용하세요.':'선택한 관·층의 개별 매장 목록은 확보 중입니다. 구역 안내도를 참고하세요.';
    list.append(p);return;
  }
  items.forEach(s=>{
    const b=document.createElement('button');b.type='button';b.className='store-item';
    if(state.destination?.name===s.name&&state.destination?.floor===s.floor)b.classList.add('active');
    b.dataset.store=s.id;
    b.innerHTML='<span><b>'+escapeText(s.name)+'</b><small>'+escapeText(s.hall)+'관 · '+escapeText(s.floor)+' · '+escapeText(categories[s.category]?.label||'업종 확인 필요')+'</small></span><span class="marker">위치 확인 필요</span>';
    b.title=s.note;b.setAttribute('aria-label',s.name+' · '+s.hall+'관 '+s.floor+' 관·층 안내');
    list.append(b);
  });
}
function floorSvgMarkup(){
  const zones=displayZones(state.hall,state.floor);
  const zoneShapes=zones.map(z=>{
    const x=z.x*10,y=115+z.y*2.1,w=z.w*10,h=z.h*2.1;
    const dimmed=state.category!=='all'&&state.category!==z.category?' dimmed':'';
    const selected=state.selectedZone===z.id?' selected':'';
    const shade=categories[z.category]?.color||'#adc5d8';
    const label=escapeText(z.label);
    const textX=x+w/2,textY=y+h/2;
    const fontSize=z.w<17?12:16;
    return '<g data-zone="'+z.id+'" role="button" tabindex="0" aria-label="'+label+' 개략 구역 선택">'+
    '<rect class="zone'+dimmed+selected+'" x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="10" fill="'+shade+'"></rect>'+
    '<text class="zone-label" font-size="'+fontSize+'" x="'+textX+'" y="'+textY+'">'+label+'</text></g>';
  }).join('');
  const hallLabels=['3관','4관','5관'].map((h,i)=>
    '<g><rect x="'+(130+i*270)+'" y="425" width="195" height="39" rx="18" fill="#fff" stroke="#a9c8d7"/>'+
    '<text x="'+(227+i*270)+'" y="450" class="hall-tag" text-anchor="middle">'+h+' · 관 위치 대조 필요</text></g>'
  ).join('');
  const footprint=state.hall==='3'?'M175 158 Q205 112 300 113 L660 118 Q790 124 840 190 Q862 225 834 269 Q777 342 670 349 L274 343 Q167 322 165 258 Z':state.hall==='5'?'M122 148 L739 136 Q790 132 842 167 L922 226 Q937 239 908 270 L821 338 L121 342 Z':'M73 165 Q88 134 137 132 L814 125 Q907 114 943 156 Q965 193 931 229 L825 331 Q774 354 708 355 L160 361 Q82 352 73 301 Z';
  return '<title>'+escapeText(state.floor)+' 층 구역 안내 모식도</title>'+
   '<desc>현장 사진을 참고한 비축척 도면. 색상 구역과 편의시설 기호는 정확한 위치가 아닌 예시입니다.</desc>'+
   '<defs><clipPath id="mallFootprint"><path d="'+footprint+'"/></clipPath></defs>'+
   '<text x="75" y="64" class="floor-caption">'+escapeText(state.floor)+' FLOOR · CATEGORY ZONES</text>'+
   '<text x="75" y="94" class="external">입구 및 관 연결 통로 위치 확인 필요</text>'+
   '<path d="'+footprint+'" fill="#fdfefe" stroke="#769ab0" stroke-width="6"/>'+
   '<g clip-path="url(#mallFootprint)">'+zoneShapes+(!zones.length?'<text x="500" y="230" text-anchor="middle" class="external">이 관·층의 공식 구획자료 확인 필요</text>':'')+
   '<path d="M80 322 C300 309 610 315 916 283" fill="none" stroke="#fff" stroke-width="30" opacity=".83"/>'+
   '<path d="M80 322 C300 309 610 315 916 283" fill="none" stroke="#8db2c4" stroke-width="4" stroke-dasharray="14 10"/></g>'+
   '<text x="270" y="301" class="floor-caption">통로(시연)</text>'+
   '<g fill="#fff" stroke="#779cb1" stroke-width="2">'+
   '<circle cx="188" cy="342" r="23"/><circle cx="520" cy="343" r="23"/><circle cx="814" cy="306" r="23"/></g>'+
   '<text class="poi" x="188" y="348" text-anchor="middle">WC</text>'+
   '<text class="poi" x="520" y="349" text-anchor="middle">EV</text>'+
   '<text class="poi" x="814" y="312" text-anchor="middle">ES</text>'+
   '<text x="73" y="401" class="external">WC 화장실 · EV 승강기 · ES 에스컬레이터 (표시 위치는 예시)</text>'+
   (state.hall==='all'?hallLabels:'<text x="510" y="452" class="floor-caption" text-anchor="middle">'+state.hall+'관 구역 간략도 · 매장별 정확 좌표 미확인</text>');
}
function renderMap(){
  el('floorSvg').innerHTML=floorSvgMarkup();
  el('floorSvg').setAttribute('aria-label',state.floor+' '+floorDescriptions[state.floor]+' 구조 모식도');
  const mapLegend=el('mapLegend');mapLegend.replaceChildren();
  const used=[...new Set(displayZones(state.hall,state.floor).map(z=>z.category))];
  if(!used.length){const p=document.createElement('span');p.textContent='선택한 관·층은 도면자료 확보 중입니다.';mapLegend.append(p);}
  used.forEach(k=>{
    const span=document.createElement('span'),swatch=document.createElement('i');
    swatch.style.background=categories[k].color;
    span.append(swatch,document.createTextNode(categories[k].label));
    mapLegend.append(span);
  });
}
function drawRoute(){
  const route=buildSchematicRoute(state.origin,state.destination);
  const target=el('routeSteps');
  target.replaceChildren();
  if(!route.supported){
    const p=document.createElement('p');p.className='notice';p.textContent='매장 또는 지도 내 구역을 선택하면 관·층 이동 순서를 보여드립니다. '+route.warning;target.append(p);return;
  }
  const h=document.createElement('h3');h.textContent=route.title;target.append(h);
  const list=document.createElement('ol');
  route.steps.forEach(s=>{
    const li=document.createElement('li'),b=document.createElement('b'),span=document.createElement('span');
    b.textContent=s.label;span.textContent=s.detail;li.append(b,span);list.append(li);
  });
  const warning=document.createElement('p');warning.className='notice';warning.textContent=route.warning;
  target.append(list,warning);
}
init();
