/**
 * Approved indoor floor-plan ingestion contract.
 * A Google/Kakao map capture or informal shop-sign photo is NOT an approved survey.
 * Importing a file never marks it verified or publishes it to the public site.
 */
export const SCHEMA_VERSION=1;
const ID=/^[a-z0-9][a-z0-9_-]{0,63}$/i;
const FLOOR=new Set(['B3','B2','B1','1F','2F','3F']);
const HALL=new Set(['3','4','5']);
const STATUS=new Set(['draft','reviewed','approved']);
const PROVENANCE=new Set(['owner-authorized-drawing','on-site-survey','signboard-photo','illustrative']);
const SAFE_RE=/^[^<>\x00-\x1f]{1,140}$/u;
export const template={
  schemaVersion:1,
  hall:'5',floor:'3F',
  source:{id:'replace-source-id',title:'승인된 도면 자료명 입력',kind:'illustrative',
          status:'draft',permissionRef:'',reviewer:'',reviewDate:''},
  outline:[[8,20],[72,18],[90,45],[78,70],[10,72]],
  entrances:[],
  shops:[],
  nodes:[],
  edges:[]
};
const error=(errs,msg)=>errs.push(msg);
const str=(x,limit=140)=>typeof x==='string'&&x.length>0&&x.length<=limit&&SAFE_RE.test(x);
const coord=x=>Number.isFinite(x)&&x>=0&&x<=100;
function point(v){return Array.isArray(v)&&v.length===2&&v.every(coord)}
function list(x){return Array.isArray(x)?x:null}
function poly(x){return list(x)&&x.length>=3&&x.length<=150&&x.every(point)}
export function validateLayout(input){
  const errors=[],warnings=[];
  if(!input||typeof input!=='object'||Array.isArray(input))return {ok:false,errors:['JSON 객체가 필요합니다.'],warnings,canPublish:false,summary:null};
  if(input.schemaVersion!==SCHEMA_VERSION)error(errors,'schemaVersion은 1이어야 합니다.');
  if(!HALL.has(input.hall))error(errors,'hall은 3, 4, 5 중 하나여야 합니다.');
  if(!FLOOR.has(input.floor))error(errors,'floor는 B3~3F 중 지정된 층이어야 합니다.');
  const src=input.source;
  if(!src||typeof src!=='object'){error(errors,'source: 도면 출처와 사용 허가 기록이 필요합니다.');}
  else {
    if(!str(src.id,64)||!ID.test(src.id))error(errors,'source.id가 유효하지 않습니다.');
    if(!str(src.title))error(errors,'source.title이 유효하지 않습니다.');
    if(!PROVENANCE.has(src.kind))error(errors,'source.kind 유형이 유효하지 않습니다.');
    if(!STATUS.has(src.status))error(errors,'source.status가 유효하지 않습니다.');
    if(src.status==='approved'&&
      (!str(src.permissionRef)||!str(src.reviewer)||! /^\d{4}-\d{2}-\d{2}$/.test(src.reviewDate??''))){
      error(errors,'approved 도면에는 permissionRef, reviewer, reviewDate가 필요합니다.');
    }
    if(src.kind==='signboard-photo'||src.kind==='illustrative'){
      warnings.push('안내판 사진·시연도는 공식 실측 도면으로 승인할 수 없습니다.');
    }
  }
  if(!poly(input.outline))error(errors,'outline은 [x,y] 3~150개 점으로 이루어진 폴리곤이어야 합니다.');
  for(const key of ['entrances','shops','nodes','edges'])if(!list(input[key]))error(errors,key+'는 배열이어야 합니다.');
  const ent=list(input.entrances)||[],shops=list(input.shops)||[],nodes=list(input.nodes)||[],edges=list(input.edges)||[];
  if(ent.length>100||shops.length>5000||nodes.length>5000||edges.length>10000)error(errors,'도면 항목 수가 상한을 초과했습니다.');
  const allIds=new Set(),nodeIds=new Set(),nodeMap=new Map();
  const addId=(item,key)=>{
    if(!item||!str(item.id,64)||!ID.test(item.id)){error(errors,key+': 유효한 id가 필요합니다.');return false;}
    if(allIds.has(item.id)){error(errors,key+': 중복 id '+item.id);return false;}
    allIds.add(item.id);return true;
  };
  ent.forEach((e,i)=>{
    if(addId(e,'entrances['+i+']')){
      if(!str(e.label)||!point(e.xy))error(errors,'entrances['+i+']: label/xy 필요');
      if(e.verified!==true)warnings.push('출입구 '+e.id+' 위치는 미검증입니다.');
    }
  });
  shops.forEach((s,i)=>{
    if(addId(s,'shops['+i+']')){
      if(!str(s.name)||!str(s.category)||!poly(s.polygon))error(errors,'shops['+i+']: name/category/polygon 필요');
      if(s.verified!==true)warnings.push(s.name+' 위치는 미검증입니다.');
    }
  });
  nodes.forEach((n,i)=>{
    if(addId(n,'nodes['+i+']')){
      nodeIds.add(n.id);nodeMap.set(n.id,n);
      if(!point(n.xy)||!['passage','entry','stairs','elevator','escalator'].includes(n.type))
        error(errors,'nodes['+i+']: xy/type 필요');
      if(n.verified!==true)warnings.push('경로 노드 '+n.id+' 미검증');
    }
  });
  edges.forEach((e,i)=>{
    if(addId(e,'edges['+i+']')){
      if(!nodeIds.has(e.from)||!nodeIds.has(e.to)||e.from===e.to)error(errors,'edges['+i+']: 연결 노드 불일치');
      if(typeof e.lengthMeters!=='number'||!Number.isFinite(e.lengthMeters)||e.lengthMeters<=0||e.lengthMeters>1000)error(errors,'edges['+i+']: 실측 거리 필요');
      if(!['walk','stairs','elevator','escalator'].includes(e.mode))error(errors,'edges['+i+']: mode 불일치');
      if(e.verified!==true)warnings.push('경로 간선 '+e.id+' 미검증');
    }
  });
  if(shops.length===0)warnings.push('매장 폴리곤이 아직 없습니다.');
  if(nodes.length===0||edges.length===0)warnings.push('검증된 보행 그래프가 없어 길안내가 비활성화됩니다.');
  const verifiedSource=src?.status==='approved'&&
    ['owner-authorized-drawing','on-site-survey'].includes(src?.kind)&&
    !!src.permissionRef&&!!src.reviewer&&!!src.reviewDate;
  const geometriesVerified=[...ent,...shops,...nodes,...edges].every(x=>x.verified===true);
  const canPublish=errors.length===0&&verifiedSource&&geometriesVerified&&shops.length>0;
  if(!canPublish)warnings.push('공개 지도 자동 반영 금지: 승인된 원본·검수 완료 지오메트리·점포 데이터가 필요합니다.');
  return {ok:errors.length===0,errors,warnings,canPublish,
    summary:{hall:input.hall,floor:input.floor,shopCount:shops.length,nodeCount:nodes.length,edgeCount:edges.length,sourceStatus:src?.status||'unknown'}};
}
/** Returns a copy that is always draft; UI edits cannot fake an approval. */
export function makeDraft(layout){
  return JSON.parse(JSON.stringify({...layout,
    source:{...layout.source,status:'draft',reviewer:'',reviewDate:''},
    shops:(layout.shops||[]).map(s=>({...s,verified:false})),
    entrances:(layout.entrances||[]).map(e=>({...e,verified:false})),
    nodes:(layout.nodes||[]).map(n=>({...n,verified:false})),
    edges:(layout.edges||[]).map(e=>({...e,verified:false}))}));
}
/** Dijkstra only traverses verified, surveyed edges on an approved source. No emergency routing. */
export function safeFloorRoute(layout,from,to,{wheelchair=false}={}){
  const validity=validateLayout(layout);
  if(!validity.ok||!validity.canPublish)return {status:'unavailable',reason:'승인된 실측도면·출입구·보행 경로가 필요합니다.',path:[],distanceMeters:null};
  const nodes=new Map(layout.nodes.map(n=>[n.id,n]));
  if(!nodes.has(from)||!nodes.has(to))return {status:'unavailable',reason:'경로 지점이 존재하지 않습니다.',path:[],distanceMeters:null};
  const dist=new Map([...nodes.keys()].map(x=>[x,Infinity])),prev=new Map();
  dist.set(from,0);
  const remaining=new Set(nodes.keys());
  while(remaining.size){
    let cur=null,best=Infinity;
    for(const n of remaining)if(dist.get(n)<best){cur=n;best=dist.get(n);}
    if(cur===null||cur===to)break;
    remaining.delete(cur);
    for(const e of layout.edges){
      if(e.verified!==true||(wheelchair&&e.mode!=='walk'&&e.mode!=='elevator'))continue;
      const adj=e.from===cur?e.to:e.to===cur?e.from:null;
      if(adj===null||!remaining.has(adj))continue;
      const value=best+e.lengthMeters;
      if(value<dist.get(adj)){dist.set(adj,value);prev.set(adj,cur);}
    }
  }
  if(!Number.isFinite(dist.get(to)))return {status:'unavailable',reason:'검증된 연결 동선이 없습니다.',path:[],distanceMeters:null};
  const path=[to];while(path[0]!==from){const next=prev.get(path[0]);if(!next)return {status:'unavailable',reason:'경로 복원 실패',path:[],distanceMeters:null};path.unshift(next);}
  return {status:'verified-plan',path,distanceMeters:dist.get(to),warning:'이 경로는 등록된 승인 도면 그래프 기준입니다. 실제 출입 제한·공사·장애물은 반영되지 않을 수 있습니다.'};
}
