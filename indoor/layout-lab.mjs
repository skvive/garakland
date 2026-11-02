import {template,validateLayout,makeDraft,safeFloorRoute} from './layout-schema.mjs';

const byId=id=>document.getElementById(id);
const NS='http://www.w3.org/2000/svg';
let current=structuredClone(template);
let adding=false, serial=0;
const elt=(tag,attrs={},text='')=>{
  const node=document.createElementNS(NS,tag);
  for(const [k,v] of Object.entries(attrs))node.setAttribute(k,String(v));
  if(text)node.textContent=String(text);
  return node;
};
function setState(){
  const verdict=validateLayout(current);
  const approved=verdict.canPublish;
  byId('status').textContent=approved?'자료상 승인 조건 충족 (사이트 미게시)':verdict.ok?'작성 중 · 미게시':'형식 오류 · 미게시';
  byId('statusDetail').textContent=approved
    ?'현재 검수 파일의 선언상 승인 조건을 충족합니다. 독립적인 사용권 확인과 담당자 배포 승인이 여전히 필요합니다.'
    :'입력·편집 파일은 자동으로 공개 지도에 반영되지 않습니다.';
  byId('status').style.color=approved?'#137866':'#865b1c';
  byId('previewTitle').textContent=current.hall+'관 · '+current.floor;
  byId('summary').textContent=verdict.ok
    ?'스키마 통과 · 매장 '+current.shops.length+'개 · 경로 노드 '+current.nodes.length+'개 · 검수 상태 '+current.source.status
    :'입력 데이터 오류 '+verdict.errors.length+'건';
  const ul=byId('messages');ul.replaceChildren();
  [...verdict.errors.map(x=>'오류: '+x),...verdict.warnings.slice(0,9)].forEach(msg=>{
    const li=document.createElement('li');li.textContent=msg;ul.append(li);
  });
  renderSvg(verdict.ok);
  renderShopRows();
  updateRouteControls(verdict);
}
function syncForm(){
  byId('hall').value=current.hall;
  byId('floor').value=current.floor;
  byId('sourceTitle').value=current.source.title;
  byId('sourceKind').value=current.source.kind;
  byId('permissionRef').value=current.source.permissionRef||'';
}
function forceDraft(){
  current=makeDraft(current);
}
function drawGrid(svg){
  for(let i=0;i<=10;i++){
    svg.append(elt('line',{x1:i*100,y1:0,x2:i*100,y2:650,stroke:'#bdd4e0','stroke-width':i===0||i===10?2:1,'stroke-dasharray':'4 8'}));
    svg.append(elt('line',{x1:0,y1:i*65,x2:1000,y2:i*65,stroke:'#bdd4e0','stroke-width':i===0||i===10?2:1,'stroke-dasharray':'4 8'}));
  }
}
function polygon(svg,points,fill,stroke,weight=3){
  svg.append(elt('polygon',{points:points.map(([x,y])=>(x*10)+','+(y*6.5)).join(' '),fill,stroke,'stroke-width':weight,'fill-opacity':.83}));
}
function renderSvg(valid){
  const svg=byId('preview');svg.replaceChildren();
  svg.append(elt('title',{},'가락몰 '+current.hall+'관 '+current.floor+' 도면 검수·시연'));
  svg.append(elt('desc',{},'실제 도면이 아닌 상대좌표 기반 미리보기. 검수 전 점포와 노드는 안전한 길안내에 사용하지 않습니다.'));
  drawGrid(svg);
  if(valid&&current.outline?.length)polygon(svg,current.outline,'#e4ebef','#6b90a5',5);
  if(valid){
    for(const s of current.shops){
      polygon(svg,s.polygon,s.verified?'#6abcab':'#83badd',s.verified?'#138677':'#2075aa');
      const [x,y]=s.polygon[0];
      svg.append(elt('text',{x:x*10,y:y*6.5-9,'font-size':14,'font-weight':850,fill:'#164262'},s.name));
    }
    for(const e of current.entrances){
      svg.append(elt('circle',{cx:e.xy[0]*10,cy:e.xy[1]*6.5,r:9,fill:'#e8ad43'}));
      svg.append(elt('text',{x:e.xy[0]*10+11,y:e.xy[1]*6.5,'font-size':13,fill:'#425e6d'},e.label));
    }
    for(const n of current.nodes)svg.append(elt('circle',{cx:n.xy[0]*10,cy:n.xy[1]*6.5,r:5,fill:'#3d8692'}));
  }
  svg.append(elt('text',{x:24,y:30,'font-size':22,'font-weight':850,fill:'#1d526f'},'가락몰 검수본 · '+current.hall+'관 '+current.floor));
  svg.append(elt('text',{x:25,y:625,'font-size':15,fill:'#865c21'},'NOT TO SCALE · DO NOT USE FOR EVACUATION · 발행 전 현장 확인'));
}
function updateRouteControls(verdict){
  const a=byId('routeFrom'),b=byId('routeTo');
  const from=a.value,to=b.value;
  for(const select of [a,b])select.replaceChildren();
  const nodes=verdict.ok?current.nodes:[];
  if(!nodes.length){
    for(const select of [a,b]){
      const opt=document.createElement('option');opt.value='';opt.textContent='검증된 경로 노드가 없습니다.';select.append(opt);select.disabled=true;
    }
  }else{
    for(const select of [a,b]){
      select.disabled=false;
      for(const n of nodes){
        const opt=document.createElement('option');opt.value=n.id;opt.textContent=n.id+' · '+n.type;select.append(opt);
      }
    }
    a.value=nodes.some(n=>n.id===from)?from:nodes[0].id;
    b.value=nodes.some(n=>n.id===to)?to:nodes[nodes.length-1].id;
  }
  byId('routeResult').textContent=verdict.canPublish
    ?'도면의 승인 메타데이터 조건은 충족했습니다. 그래프를 선택해 검증 결과를 확인하세요.'
    :'실측·권리 검증이 완료되지 않아 경로를 계산할 수 없습니다.';
}
function renderShopRows(){
  const parent=byId('shopRows');parent.replaceChildren();
  if(!current.shops.length){
    const p=document.createElement('p');p.textContent='등록된 점포 도형이 없습니다. 로컬 도면 파일을 불러오거나 초안 위치를 표시할 수 있습니다.';parent.append(p);return;
  }
  for(const s of current.shops.slice(0,200)){
    const r=document.createElement('div');r.className='shop-record';
    const name=document.createElement('b');name.textContent=s.name;
    const state=document.createElement('small');state.textContent=s.verified?'자료 내 승인 표기':'위치 확인 필요';
    r.append(name,state);parent.append(r);
  }
  if(current.shops.length>200){
    const p=document.createElement('p');p.textContent='목록 200개까지만 표시합니다. 전체는 JSON 내보내기로 확인하세요.';parent.append(p);
  }
}
function importLayout(parsed){
  const verdict=validateLayout(parsed);
  if(!verdict.ok){
    const message=verdict.errors.slice(0,5).join('\n');
    byId('summary').textContent='가져오기 거부 · '+message;
    return;
  }
  current=structuredClone(parsed);serial=current.shops.length;
  adding=false;byId('mapWrap').classList.remove('clicking');
  syncForm();setState();
}
function clickForPin(event){
  if(!adding)return;
  const svg=byId('preview'),ctm=svg.getScreenCTM();
  if(!ctm)return;
  const pointer=svg.createSVGPoint();pointer.x=event.clientX;pointer.y=event.clientY;
  const point=pointer.matrixTransform(ctm.inverse());
  const x=Math.round(point.x/10*10)/10,y=Math.round(point.y/6.5*10)/10;
  if(!Number.isFinite(x)||!Number.isFinite(y)||x<2||y<2||x>98||y>98)return;
  const name=byId('shopName').value.trim();
  if(!name||/[<>\x00-\x1f]/.test(name)||name.length>140){
    byId('summary').textContent='점포 이름을 먼저 정확히 입력해 주세요.';return;
  }
  const category=byId('shopCategory').value.trim();
  if(!category||/[<>\x00-\x1f]/.test(category)||category.length>140){
    byId('summary').textContent='업종 이름을 입력해 주세요.';return;
  }
  forceDraft();
  let id;
  do {serial++;id='draft-shop-'+serial;} while(current.shops.some(s=>s.id===id));
  current.shops.push({id,name,category,polygon:[
    [Math.max(0,x-2),Math.max(0,y-2)],[Math.min(100,x+2),Math.max(0,y-2)],
    [Math.min(100,x+2),Math.min(100,y+2)],[Math.max(0,x-2),Math.min(100,y+2)]
  ],verified:false});
  adding=false;byId('mapWrap').classList.remove('clicking');
  setState();
}
const fields=['hall','floor','sourceTitle','sourceKind','permissionRef'];
for(const id of fields)byId(id).addEventListener('change',()=>{
  forceDraft();
  if(id==='hall'||id==='floor'){
    // Coordinates of one floor must NEVER be silently reused on a different floor.
    current.shops=[];current.nodes=[];current.edges=[];current.entrances=[];
  }
  if(id==='hall')current.hall=byId('hall').value;
  if(id==='floor')current.floor=byId('floor').value;
  if(id==='sourceTitle')current.source.title=byId('sourceTitle').value.trim();
  if(id==='sourceKind')current.source.kind=byId('sourceKind').value;
  if(id==='permissionRef')current.source.permissionRef=byId('permissionRef').value.trim();
  adding=false;byId('mapWrap').classList.remove('clicking');setState();
});
byId('newDraft').addEventListener('click',()=>{
  current=structuredClone(template);serial=0;adding=false;
  byId('mapWrap').classList.remove('clicking');syncForm();setState();
});
byId('startPin').addEventListener('click',()=>{
  adding=true;byId('mapWrap').classList.add('clicking');
  byId('summary').textContent='도면의 상대 좌표를 눌러 초안 점포 구역을 등록하세요. 실제 호실 좌표가 아닙니다.';
});
byId('clearPins').addEventListener('click',()=>{
  forceDraft();current.shops=[];adding=false;byId('mapWrap').classList.remove('clicking');setState();
});
byId('preview').addEventListener('click',clickForPin);
byId('calculateRoute').addEventListener('click',()=>{
  const result=safeFloorRoute(current,byId('routeFrom').value,byId('routeTo').value,
                           {wheelchair:byId('wheelchairMode').checked});
  byId('routeResult').textContent=result.status==='verified-plan'
    ?'입력 도면 기준 경로: '+result.path.join(' → ')+' / 실측 간선 합 '+result.distanceMeters+'m. '+result.warning
    :result.reason;
});
byId('inputFile').addEventListener('change',async e=>{
  const file=e.target.files?.[0];if(!file)return;
  if(file.size>1048576){byId('summary').textContent='파일 크기는 1MB 이하만 허용합니다.';return;}
  try{importLayout(JSON.parse(await file.text()));}
  catch{byId('summary').textContent='JSON 구문을 읽을 수 없습니다. 원본 파일을 확인하세요.';}
  finally{e.target.value='';}
});
byId('download').addEventListener('click',()=>{
  const v=validateLayout(current);
  if(!v.ok){byId('summary').textContent='형식 오류를 수정한 뒤 내보내세요.';return;}
  // Export is a local review draft, never an auto-authorized publication.
  const bytes=JSON.stringify(makeDraft(current),null,2);
  const blob=new Blob([bytes],{type:'application/json;charset=utf-8'});
  const url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download='garak-mall-'+current.hall+'-'+current.floor+'-review-draft.json';a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
});
syncForm();setState();
