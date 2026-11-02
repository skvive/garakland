import {validateCampus,routeCampus,makeCampusDraft} from './campus-graph.mjs';
const el=id=>document.getElementById(id),NS='http://www.w3.org/2000/svg';
const svgEl=(tag,attrs={},label='')=>{const n=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));if(label)n.textContent=label;return n;};
const nodeKey=(hall,floor,id)=>hall+':'+floor+':'+id;
let campus={schemaVersion:1,name:'도면 미등록',floors:[],transfers:[],publication:'disabled'};
let synthetic=false;
const example=()=>{
 const src=n=>({id:'demo-'+n,title:'TEST ONLY. NOT AN ACTUAL GARAK MALL DRAWING',kind:'on-site-survey',
   status:'approved',permissionRef:'TEST-MOCK-ONLY',reviewer:'TEST FIXTURE',reviewDate:'2026-11-02'});
 const floor=(hall,level,points,edges)=>({
   schemaVersion:1,hall,floor:level,source:src(hall+'-'+level),
   outline:[[12,20],[84,20],[89,74],[12,74]],entrances:[],
   shops:[{id:'test-shop-'+hall+'-'+level,name:'테스트 점포 (실제 아님)',category:'demo',
    polygon:[[40,42],[55,42],[55,52],[40,52]],verified:true}],
   nodes:points.map((p,i)=>({id:p[0],type:p[1],xy:[14+i*20,34],verified:true})),
   edges:edges.map((e,i)=>({id:'e'+i,from:e[0],to:e[1],mode:e[2],lengthMeters:e[3],verified:true}))
 });
 const f1=floor('5','1F',[['gate','entry'],['lift','elevator'],['stairs','stairs']],[
   ['gate','lift','walk',10],['gate','stairs','walk',4]
 ]);
 const f2=floor('5','2F',[['lift','elevator'],['stairs','stairs'],['hallway','passage']],[
   ['lift','hallway','walk',11],['stairs','hallway','walk',4]
 ]);
 const f3=floor('3','2F',[['hallway','passage'],['destination','passage']],[
   ['hallway','destination','walk',9]
 ]);
 return {schemaVersion:1,name:'TEST ONLY SYNTHETIC CAMPUS — NOT GARAK MALL',
   publication:'disabled',floors:[f1,f2,f3],transfers:[
    {id:'lift',from:{hall:'5',floor:'1F',node:'lift'},to:{hall:'5',floor:'2F',node:'lift'},
     mode:'elevator',lengthMeters:7,accessible:true,bidirectional:true,verified:true,evidenceId:'test-elevator',sourceKind:'survey'},
    {id:'stairs',from:{hall:'5',floor:'1F',node:'stairs'},to:{hall:'5',floor:'2F',node:'stairs'},
     mode:'stairs',lengthMeters:2,accessible:false,bidirectional:true,verified:true,evidenceId:'test-stairs',sourceKind:'survey'},
    {id:'hall-link',from:{hall:'5',floor:'2F',node:'hallway'},to:{hall:'3',floor:'2F',node:'hallway'},
     mode:'walk',lengthMeters:30,accessible:true,bidirectional:true,verified:true,evidenceId:'test-connection',sourceKind:'survey'}
   ]};
};
function clearAndOptions(select){
 select.replaceChildren();
 for(const f of campus.floors||[])for(const n of f.nodes||[]){
   const o=document.createElement('option');
   o.value=nodeKey(f.hall,f.floor,n.id);
   o.textContent=f.hall+'관 '+f.floor+' · '+n.id+' ('+n.type+')';select.append(o);
 }
 if(!select.options.length){const o=document.createElement('option');o.value='';o.textContent='도면 경로 노드 없음';select.append(o);select.disabled=true;}
 else select.disabled=false;
}
function render(){
 const v=validateCampus(campus);
 el('graphStatus').textContent=!v.ok?'검수 오류 · 게시 불가':v.routeReady?(synthetic?'테스트 예제 · 경로 시뮬레이션':'입력 데이터 형식상 경로 계산 가능'):'자료 미확인 · 게시 불가';
 el('graphNote').textContent=synthetic?'모든 위치와 승인이 임의의 테스트 값입니다. 실제 가락몰 길안내가 아닙니다.':
   '입력 문서에 적힌 승인·실측 주장은 독립 검증되지 않았습니다. 운영 게시는 별도 담당자 승인이 필요합니다.';
 el('previewTitle').textContent=campus.name||'관·층 연결 네트워크';
 el('counts').textContent='층 '+(v.stats?.floors||0)+'개 · 경로 노드 '+(v.stats?.nodes||0)+'개 · 관·층 연결 '+(v.stats?.transfers||0)+'개';
 const list=el('validationMessages');list.replaceChildren();
 for(const text of [...v.errors,...v.warnings].slice(0,12)){
   const li=document.createElement('li');li.textContent=text;list.append(li);
 }
 const a=el('startNode'),b=el('endNode');const beforeA=a.value,beforeB=b.value;
 clearAndOptions(a);clearAndOptions(b);
 if([...a.options].some(o=>o.value===beforeA))a.value=beforeA;
 if([...b.options].some(o=>o.value===beforeB))b.value=beforeB;
 else if(b.options.length>0)b.selectedIndex=b.options.length-1;
 renderSvg();
 el('routeResult').textContent='경로 검증 대기. 운영 지도 게시·실제 비상 경로 계산에는 사용되지 않습니다.';
}
function renderSvg(){
 const svg=el('campusSvg');svg.replaceChildren();
 svg.append(svgEl('rect',{x:5,y:5,width:990,height:590,rx:12,fill:'#e8f2f6',stroke:'#bbd5e2'}));
 svg.append(svgEl('text',{x:34,y:47,'font-size':20,'font-weight':'bold',fill:'#164b69'},'관·층 연결 토폴로지 · 정식 평면도 아님'));
 const layouts=campus.floors||[],positions=new Map();
 const columns=[170,460,750],rows=[115,255,395];
 for(let i=0;i<Math.min(layouts.length,9);i++){
   const f=layouts[i],x=columns[i%3],y=rows[Math.floor(i/3)];
   const label=f.hall+'관 '+f.floor;
   svg.append(svgEl('rect',{x:x-113,y:y-24,width:227,height:100,rx:11,fill:'#fff',stroke:'#8dafbd','stroke-width':2}));
   svg.append(svgEl('text',{x:x-96,y:y,'font-size':18,'font-weight':800,fill:'#204c64'},label));
   svg.append(svgEl('text',{x:x-96,y:y+24,'font-size':12,fill:'#6b8291'},(f.nodes||[]).length+'개 이동 노드'));
   for(let j=0;j<(f.nodes||[]).length;j++){
     const node=f.nodes[j],px=x-80+(j%5)*37,py=y+54+Math.floor(j/5)*12;
     positions.set(nodeKey(f.hall,f.floor,node.id),[px,py]);
     svg.append(svgEl('circle',{cx:px,cy:py,r:7,fill:node.type==='elevator'?'#158976':node.type==='stairs'?'#d18b37':'#2780bc'}));
   }
 }
 const shown=(campus.transfers||[]).slice(0,60);
 for(const t of shown){
   const a=positions.get(nodeKey(t.from?.hall,t.from?.floor,t.from?.node));
   const b=positions.get(nodeKey(t.to?.hall,t.to?.floor,t.to?.node));
   if(!a||!b)continue;
   svg.append(svgEl('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],
     stroke:t.mode==='elevator'?'#168c7b':t.mode==='stairs'?'#d18b37':'#2a7fb8',
     'stroke-width':3,'stroke-dasharray':t.verified?'none':'5 6'}));
 }
 if(!layouts.length)svg.append(svgEl('text',{x:500,y:285,'text-anchor':'middle','font-size':21,fill:'#5f7c8f'},'승인·실측 도면이 없습니다. 로컬 JSON을 불러오세요.'));
 svg.append(svgEl('text',{x:28,y:566,'font-size':15,fill:'#96612b'},
    synthetic?'TEST ONLY: 가상 건물·승인·동선 · 현장 길찾기 사용 금지':'도식 연결도 · 업로드 승인 증빙은 서버에서 검증되지 않음'));
 const target=el('transferRows');target.replaceChildren();
 for(const t of (campus.transfers||[]).slice(0,100)){
   const div=document.createElement('div');div.className='shop-record';
   const label=document.createElement('b');
   label.textContent=t.from?.hall+'관 '+t.from?.floor+' → '+t.to?.hall+'관 '+t.to?.floor+' · '+t.mode;
   const status=document.createElement('small');status.textContent=t.verified?'입력값상 검증 표기':'연결 미검증';
   div.append(label,status);target.append(div);
 }
}
function ref(value){
 const bits=value.split(':');
 return bits.length===3?{hall:bits[0],floor:bits[1],node:bits[2]}:null;
}
el('testExample').addEventListener('click',()=>{synthetic=true;campus=example();render();});
el('inputCampus').addEventListener('change',async e=>{
 const f=e.target.files?.[0];if(!f)return;
 if(f.size>1048576){el('routeResult').textContent='JSON은 1MB 이하만 허용됩니다.';e.target.value='';return;}
 try{
   const data=JSON.parse(await f.text());
   const v=validateCampus(data);
   if(!v.ok){el('routeResult').textContent='검수 오류: '+v.errors.slice(0,4).join(' / ');return;}
   campus=data;synthetic=false;render();
 }catch{el('routeResult').textContent='파일을 읽을 수 없습니다. JSON 형식인지 확인하세요.';}
 finally{e.target.value='';}
});
el('routeButton').addEventListener('click',()=>{
 const from=ref(el('startNode').value),to=ref(el('endNode').value);
 if(!from||!to){el('routeResult').textContent='유효한 경로 노드를 선택하세요.';return;}
 const result=routeCampus(campus,from,to,{wheelchair:el('wheelchairMode').checked});
 el('routeResult').textContent=result.status!=='verified-plan'?result.reason:
   (synthetic?'TEST ONLY · 실제 가락몰 거리가 아닙니다. ':'입력 데이터 기준 · 실측 진위 확인 필요. ')+
   result.path.map(p=>p.hall+'관 '+p.floor+' '+p.node).join(' → ')+' / 데이터 상 이동거리 '+result.distanceMeters+'m. '+result.warning;
});
el('exportDraft').addEventListener('click',()=>{
 const data=makeCampusDraft(campus);
 const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json;charset=utf-8'});
 const url=URL.createObjectURL(blob),a=document.createElement('a');
 a.href=url;a.download='garak-campus-review-draft.json';a.click();
 setTimeout(()=>URL.revokeObjectURL(url),1500);
});
render();
