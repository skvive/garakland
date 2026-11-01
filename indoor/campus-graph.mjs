/**
 * Indoor campus graph (review-only). NOT a verified Garak Mall wayfinding dataset.
 * An independent signed operator process must validate the claimed approvals
 * before a layout is ever published to the customer-facing map.
 */
import {validateLayout} from './layout-schema.mjs';
export const CAMPUS_VERSION=1;
const idOk=s=>typeof s==='string'&&/^[a-z0-9_-]{1,64}$/i.test(s);
const hallOk=x=>['3','4','5'].includes(x);
const floorOk=x=>['B3','B2','B1','1F','2F','3F'].includes(x);
const nodeKey=r=>r.hall+':'+r.floor+':'+r.node;
const floorKey=x=>x.hall+':'+x.floor;
const transferKinds=new Set(['walk','stairs','escalator','elevator']);
const isAccess=e=>e.mode==='walk'||e.mode==='elevator';
export const sampleCampus={
 schemaVersion:1,name:'TEST ONLY hypothetical campus — not measured',
 floors:[],transfers:[],publication:'disabled'
};
export function validateCampus(bundle){
 const errors=[],warnings=[],nodes=new Map(),floors=new Map(),ids=new Set();
 if(!bundle||typeof bundle!=='object'||Array.isArray(bundle))return {ok:false,routeReady:false,errors:['구조화된 JSON 객체가 필요합니다.'],warnings};
 if(bundle.schemaVersion!==CAMPUS_VERSION)errors.push('schemaVersion은 1이어야 합니다.');
 if(!Array.isArray(bundle.floors)||!bundle.floors.length||bundle.floors.length>32)errors.push('floors: 1~32개의 층 데이터가 필요합니다.');
 if(!Array.isArray(bundle.transfers)||bundle.transfers.length>1000)errors.push('transfers 배열 크기가 잘못되었습니다.');
 const layouts=Array.isArray(bundle.floors)?bundle.floors.slice(0,32):[];
 for(const [i,f] of layouts.entries()){
   const k=floorKey(f);
   if(!hallOk(f?.hall)||!floorOk(f?.floor)){errors.push('floors['+i+'] 관·층 값 오류');continue;}
   if(floors.has(k)){errors.push('중복 관·층 '+k);continue;}
   floors.set(k,f);
   const result=validateLayout(f);
   if(!result.ok)errors.push('floors['+i+']: '+result.errors.slice(0,3).join(' / '));
   if(!result.canPublish)warnings.push(k+': 사용권·점포·노드 검증 승인 조건 미충족');
   for(const n of f.nodes||[]){
     if(!idOk(n.id))continue;
     const key=nodeKey({hall:f.hall,floor:f.floor,node:n.id});
     nodes.set(key,{...n,hall:f.hall,floor:f.floor,key});
   }
 }
 const transfers=Array.isArray(bundle.transfers)?bundle.transfers.slice(0,1000):[];
 const verifiedTransfers=[];
 for(const [i,t] of transfers.entries()){
   if(!idOk(t?.id)||ids.has(t.id)){errors.push('transfers['+i+'] id 중복 또는 오류');continue;}
   ids.add(t.id);
   if(!t.from||!t.to||!hallOk(t.from.hall)||!hallOk(t.to.hall)||
      !floorOk(t.from.floor)||!floorOk(t.to.floor)||!idOk(t.from.node)||!idOk(t.to.node)){
     errors.push('transfers['+i+'] 경유 지점 형식 오류');continue;
   }
   const a=nodeKey(t.from),b=nodeKey(t.to),start=nodes.get(a),end=nodes.get(b);
   if(!start||!end||a===b){errors.push('transfers['+i+'] 연결 노드가 존재하지 않음');continue;}
   if(!Number.isFinite(t.lengthMeters)||t.lengthMeters<=0||t.lengthMeters>1500||
       !transferKinds.has(t.mode)||typeof t.bidirectional!=='boolean'||
       typeof t.accessible!=='boolean'){
     errors.push('transfers['+i+'] 거리·수단·접근성 형식 오류');continue;
   }
   if(t.from.floor!==t.to.floor){
     if(t.from.hall!==t.to.hall||!['stairs','elevator','escalator'].includes(t.mode)||
       start.type!==t.mode||end.type!==t.mode){
       errors.push('transfers['+i+'] 층 이동 수단·연결 노드 불일치');continue;
     }
   }else if(t.from.hall===t.to.hall||t.mode!=='walk'){
     errors.push('transfers['+i+'] 동일 관·층 또는 잘못된 관 연결');continue;
   }
   if(!isAccess(t)&&t.accessible===true){
     errors.push('transfers['+i+'] 계단·에스컬레이터 무장애 표기 불가');continue;
   }
   if(t.verified!==true||!idOk(t.evidenceId)||!['survey','owner-approved-plan'].includes(t.sourceKind)){
     warnings.push('transfers['+i+']: 현장 확인·근거자료 미완료');
   }else verifiedTransfers.push(t);
 }
 const approved=layouts.length>0&&layouts.every(f=>{
   const verdict=validateLayout(f);
   return verdict.canPublish&&(f.nodes||[]).length>0&&(f.edges||[]).length>0;
 });
 const transfersApproved=transfers.every(t=>verifiedTransfers.includes(t));
 const routeReady=errors.length===0&&approved&&transfersApproved;
 if(!routeReady)warnings.push('실측·승인되지 않은 다층 동선은 계산 및 고객 공개 불가');
 return {ok:errors.length===0,routeReady,errors,warnings,stats:{
   floors:floors.size,nodes:nodes.size,transfers:transfers.length,
   approvedFloors:layouts.filter(f=>validateLayout(f).canPublish).length
 }};
}
export function routeCampus(bundle,from,to,{wheelchair=false}={}){
 const review=validateCampus(bundle);
 const unavailable=reason=>({status:'unavailable',reason,path:[],distanceMeters:null,accessible:wheelchair});
 if(!review.routeReady)return unavailable('실측·승인된 층별 도면과 층간 연결 증빙이 없습니다.');
 const index=new Map(),adj=new Map();
 for(const f of bundle.floors){
   for(const n of f.nodes){
     const key=nodeKey({...f,node:n.id});
     index.set(key,{key,hall:f.hall,floor:f.floor,node:n.id,type:n.type});
     adj.set(key,[]);
   }
 }
 const add=(a,b,d,mode)=>{adj.get(a).push({to:b,weight:d,mode});};
 for(const f of bundle.floors){
   for(const e of f.edges){
     if(wheelchair&&!isAccess(e))continue;
     const a=nodeKey({...f,node:e.from}),b=nodeKey({...f,node:e.to});
     add(a,b,e.lengthMeters,e.mode);add(b,a,e.lengthMeters,e.mode);
   }
 }
 for(const t of bundle.transfers){
   if(wheelchair&&(!isAccess(t)||t.accessible!==true))continue;
   const a=nodeKey(t.from),b=nodeKey(t.to);
   add(a,b,t.lengthMeters,t.mode);
   if(t.bidirectional)add(b,a,t.lengthMeters,t.mode);
 }
 if(!index.has(nodeKey(from))||!index.has(nodeKey(to)))return unavailable('선택한 노드가 승인 도면에 없습니다.');
 const start=nodeKey(from),goal=nodeKey(to),dist=new Map([[start,0]]),prev=new Map(),used=new Set();
 while(true){
   let cur=null,best=Infinity;
   for(const [k,d] of dist)if(!used.has(k)&&d<best){cur=k;best=d;}
   if(cur===null||cur===goal)break;
   used.add(cur);
   for(const e of adj.get(cur)||[]){
     const next=best+e.weight;
     if(next<(dist.get(e.to)??Infinity)){dist.set(e.to,next);prev.set(e.to,{from:cur,mode:e.mode});}
   }
 }
 if(!Number.isFinite(dist.get(goal)))return unavailable('선택한 이동 방식으로 검증된 연결 경로가 없습니다.');
 let cur=goal;const path=[{...index.get(cur),mode:'arrive'}];
 while(cur!==start){
   const p=prev.get(cur);if(!p)return unavailable('경로 복원 실패');
   cur=p.from;path.unshift({...index.get(cur),mode:p.mode});
 }
 return {status:'verified-plan',path,distanceMeters:dist.get(goal),accessible:wheelchair,
  warning:'등록된 도면 기준 거리입니다. 현장 출입 제한·공사·승강기 고장·피난 상황은 반영되지 않습니다.'};
}
export function makeCampusDraft(bundle){
 const cloned=JSON.parse(JSON.stringify(bundle));cloned.publication='disabled';
 for(const f of cloned.floors||[]){
   f.source={...f.source,status:'draft',reviewer:'',reviewDate:''};
   for(const kind of ['shops','nodes','edges','entrances'])for(const x of f[kind]||[])x.verified=false;
 }
 for(const t of cloned.transfers||[])t.verified=false;
 return cloned;
}
