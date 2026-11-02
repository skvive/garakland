import {template,validateLayout,makeDraft} from './layout-schema.mjs';
import {seedFromSignboard,validateCandidates,parseCsv,csvExport,placeCandidateDraft,prepareRegistryDraft,columns,MAX_BYTES} from './tenant-onboarding.mjs';

const el=id=>document.getElementById(id),NS='http://www.w3.org/2000/svg';
const safeText=(node,s)=>{node.textContent=String(s??'');return node;};
const svg=(tag,attrs={},label='')=>{
 const n=document.createElementNS(NS,tag);
 for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));
 if(label)n.textContent=String(label);
 return n;
};
const stage={validation:validateCandidates([]),selectedId:null,layouts:new Map()};
const key=(h,f)=>h+':'+f;
const rawDraft=(hall,floor)=>{
 const d=structuredClone(template);
 d.hall=hall;d.floor=floor;
 d.source={id:'tenant-phase4-draft',title:'미확인 매장 위치 등록 초안',kind:'illustrative',status:'draft',permissionRef:'',reviewer:'',reviewDate:''};
 return d;
};
const getDraft=()=>{
 const hall=el('editHall').value,floor=el('editFloor').value;
 return stage.layouts.get(key(hall,floor))??rawDraft(hall,floor);
};
const download=(filename,body,type)=>{
 const blob=new Blob([body],{type}),url=URL.createObjectURL(blob),a=document.createElement('a');
 a.href=url;a.download=filename;a.click();
 setTimeout(()=>URL.revokeObjectURL(url),1000);
};
function apply(raw){
 stage.validation=validateCandidates(raw);
 stage.selectedId=null;
 stage.layouts.clear();
 renderAll();
}
function currentSelected(){
 return stage.validation.rows.find(r=>r.shop_id===stage.selectedId)||null;
}
function renderAll(){
 const v=stage.validation;
 el('summary').textContent='전체 '+(v.stats?.count??0)+'개 · 안내판 이름 일치 '+(v.stats?.signboardMatches??0)+'개 · 호실 미확인 '+(v.stats?.noRoom??0)+'개';
 el('warning').textContent=v.ok?'CSV 서식 검사 통과 · 실제 영업·호실·좌표 미검증 · 운영 게시 불가':'매장 명부 검수 오류 또는 중복이 있습니다. 수정 전 위치 등록·내보내기 불가.';
 const ul=el('errorList');ul.replaceChildren();
 const messages=[...(v.errors||[]),...(v.duplicates||[]),...(v.warnings||[])];
 for(const msg of messages.slice(0,15)){const li=document.createElement('li');li.textContent=msg;ul.append(li);}
 if(messages.length>15){const li=document.createElement('li');li.textContent='나머지 '+(messages.length-15)+'개 경고는 표시하지 않았습니다.';ul.append(li);}
 if(!messages.length){const li=document.createElement('li');li.textContent='CSV 구문·중복 검사에서 발견된 문제가 없습니다. 현장 대조는 별도입니다.';ul.append(li);}
 renderRows();renderMap();
}
function renderRows(){
 const v=stage.validation,search=el('search').value.trim().toLocaleLowerCase('ko');
 const hall=el('hallFilter').value,floor=el('floorFilter').value;
 const parent=el('tenantRows');parent.replaceChildren();
 const records=v.rows.filter(r=>
   (hall==='all'||r.hall===hall)&&(floor==='all'||r.floor===floor)&&
   (!search||[r.name,r.room,r.shop_id].some(s=>String(s).toLocaleLowerCase('ko').includes(search)))
 ).slice(0,500);
 for(const row of records){
   const tr=document.createElement('tr');
   if(row.shop_id===stage.selectedId)tr.className='selected';
   const action=document.createElement('button');action.type='button';action.dataset.id=row.shop_id;
   action.textContent=row.shop_id===stage.selectedId?'선택 중':'선택';
   action.setAttribute('aria-label',row.name+' · 임시 위치 선택');
   const tdAction=document.createElement('td');tdAction.append(action);tr.append(tdAction);
   const cells=[row.name,row.hall+'관 '+row.floor,row.room||'확인 필요',
     row.signboard_match?'이름 표기 확인':'사진 미확인'];
   for(const [i,val] of cells.entries()){
     const td=document.createElement('td');safeText(td,val);
     if(i===3)td.className=row.signboard_match?'matched':'pending';
     tr.append(td);
   }
   const td=document.createElement('td');td.className='unverified';
   const d=stage.layouts.get(key(row.hall,row.floor));
   const linked=d?.shops.some(s=>s.registryId===row.shop_id)||false;
   td.textContent=linked?'초안 위치 지정':'위치 미확인';tr.append(td);
   parent.append(tr);
 }
 if(!records.length){
   const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=6;td.textContent='해당 매장 정보가 없습니다.';tr.append(td);parent.append(tr);
 }
}
function renderMap(){
 const d=getDraft(),v=validateLayout(d),map=el('stageMap');map.replaceChildren();
 const title=svg('title',{},d.hall+'관 '+d.floor+' 매장 미확인 위치 초안');map.append(title);
 map.append(svg('rect',{x:0,y:0,width:1000,height:650,fill:'#edf4f8'}));
 for(let x=0;x<=1000;x+=100)map.append(svg('line',{x1:x,x2:x,y1:0,y2:650,stroke:'#d3e3ec','stroke-width':1,'stroke-dasharray':'6 6'}));
 for(let y=0;y<=650;y+=65)map.append(svg('line',{x1:0,x2:1000,y1:y,stroke:'#d3e3ec','stroke-width':1,'stroke-dasharray':'6 6'}));
 const base=d.outline.map(([x,y])=>(x*10)+','+(y*6.5)).join(' ');
 map.append(svg('polygon',{points:base,fill:'#e1ebf1',stroke:'#7698a9','stroke-width':5}));
 for(const p of d.shops||[]){
   const poly=p.polygon.map(([x,y])=>(x*10)+','+(y*6.5)).join(' ');
   map.append(svg('polygon',{points:poly,fill:'#62aadb',stroke:'#236c9b','stroke-width':2}));
   const [x,y]=p.polygon[0];
   map.append(svg('text',{x:x*10+5,y:y*6.5-7,'font-size':15,'font-weight':'bold',fill:'#205b78'},p.name));
 }
 map.append(svg('text',{x:30,y:40,'font-size':24,'font-weight':'bold',fill:'#22536c'},d.hall+'관 '+d.floor+' · 검수 전 매장 배치'));
 map.append(svg('text',{x:30,y:622,'font-size':16,'font-weight':750,fill:'#94631e'},'SCHEMATIC ONLY / NOT REAL STORE LOCATIONS / DO NOT PUBLISH'));
 const candidate=currentSelected();
 el('selectedInfo').textContent=candidate
   ?candidate.name+' · '+candidate.hall+'관 '+candidate.floor+' · '+(candidate.room||'호실 미확인')+' — 오른쪽 도면을 눌러 임시 좌표를 정하세요.'
   :'명부에서 매장을 선택한 뒤 상대좌표 지도를 클릭하세요.';
 el('stageStatus').textContent='검수 전 폴리곤 '+(d.shops||[]).length+'개 · '+(v.canPublish?'입력값상 승인 표기 포함, 실제 사용권은 확인되지 않음':'공개 승인 조건 미충족')+' · 고객 지도 미반영';
}
el('tenantRows').addEventListener('click',e=>{
 const target=e.target.closest('button[data-id]');if(!target)return;
 if(!stage.validation.ok){el('selectedInfo').textContent='명부의 중복·형식 문제를 먼저 해결하세요.';return;}
 const row=stage.validation.rows.find(r=>r.shop_id===target.dataset.id);if(!row)return;
 stage.selectedId=row.shop_id;
 el('editHall').value=row.hall;
 el('editFloor').value=row.floor;
 renderRows();renderMap();
});
el('stageMap').addEventListener('click',e=>{
 if(!stage.validation.ok){el('stageStatus').textContent='중복 또는 서식 오류가 있어 배치할 수 없습니다.';return;}
 const candidate=currentSelected();
 if(!candidate){el('stageStatus').textContent='명부의 매장을 먼저 선택하세요.';return;}
 const map=el('stageMap'),matrix=map.getScreenCTM();if(!matrix)return;
 const point=map.createSVGPoint();point.x=e.clientX;point.y=e.clientY;
 const q=point.matrixTransform(matrix.inverse()),xy=[q.x/10,q.y/6.5];
 try{
  const d=placeCandidateDraft(getDraft(),candidate,xy);
  stage.layouts.set(key(candidate.hall,candidate.floor),d);
  el('stageStatus').textContent=candidate.name+' 위치 임시 등록. 실제 호실·도면 경계 확인 전에는 게시하지 마세요.';
  renderRows();renderMap();
 }catch(err){el('stageStatus').textContent='등록하지 못했습니다: '+err.message;}
});
for(const name of ['search','hallFilter','floorFilter'])el(name).addEventListener(name==='search'?'input':'change',renderRows);
for(const name of ['editHall','editFloor'])el(name).addEventListener('change',renderMap);
el('seedButton').addEventListener('click',()=>apply(seedFromSignboard()));
el('templateButton').addEventListener('click',()=>{
 const sample={shop_id:'your-unique-id',name:'검수 전 매장 예시',hall:'5',floor:'1F',room:'',category:'food',source_ref:'현장 확인 자료 ID'};
 download('garakmall-tenant-csv-template.csv',csvExport([sample]),'text/csv;charset=utf-8');
});
el('exportCsv').addEventListener('click',()=>{
 if(!stage.validation.ok){el('warning').textContent='중복 및 필수 열 오류를 먼저 해결하세요.';return;}
 download('garakmall-tenant-review.csv',csvExport(stage.validation.rows),'text/csv;charset=utf-8');
});
el('exportJson').addEventListener('click',()=>{
 try{
  const draft=prepareRegistryDraft(stage.validation);
  download('garakmall-tenant-review-draft.json',JSON.stringify(draft,null,2),'application/json;charset=utf-8');
 }catch(err){el('warning').textContent=err.message;}
});
function inputCsv(s){try{apply(parseCsv(s));}catch(err){el('warning').textContent='CSV 가져오기 오류: '+err.message;}}
el('loadPaste').addEventListener('click',()=>inputCsv(el('csvPaste').value));
el('csvFile').addEventListener('change',async e=>{
 const file=e.target.files?.[0];if(!file)return;
 if(file.size>MAX_BYTES){el('warning').textContent='최대 1MB까지 가져올 수 있습니다.';e.target.value='';return;}
 try{inputCsv(await file.text());}catch{el('warning').textContent='CSV 파일을 읽을 수 없습니다.';}
 finally{e.target.value='';}
});
el('layoutFile').addEventListener('change',async e=>{
 const file=e.target.files?.[0];if(!file)return;
 if(file.size>MAX_BYTES){el('stageStatus').textContent='도면 파일은 1MB 이하만 허용됩니다.';e.target.value='';return;}
 try{
   const obj=JSON.parse(await file.text()),verdict=validateLayout(obj);
   if(!verdict.ok){el('stageStatus').textContent='도면 형식 오류: '+verdict.errors.slice(0,3).join(' / ');return;}
   const d=makeDraft(obj);
   stage.layouts.set(key(d.hall,d.floor),d);
   el('editHall').value=d.hall;el('editFloor').value=d.floor;
   renderRows();renderMap();
   el('stageStatus').textContent='도면을 검수 초안으로 불러왔습니다. 입력된 승인·실측 플래그는 모두 초기화했습니다.';
 }catch{el('stageStatus').textContent='도면 JSON을 가져올 수 없습니다.';}
 finally{e.target.value='';}
});
el('downloadLayout').addEventListener('click',()=>{
 const d=makeDraft(getDraft());
 download('garakmall-'+d.hall+'-'+d.floor+'-unverified-layout.json',JSON.stringify(d,null,2),'application/json;charset=utf-8');
});
apply(seedFromSignboard());
