import {floorOrder,stores,floorZones,displayZones,floorDescriptions,halls,categories,defaultOrigin} from './data.mjs';

export const knownFloor = floor => floorOrder.includes(floor);
export const knownHall = hall => halls.some(h=>h.id===String(hall));
export function readSelection(params){
  const requestedFloor=params.get('floor'),requestedHall=params.get('hall');
  return {
    floor:knownFloor(requestedFloor)?requestedFloor:'1F',
    hall:knownHall(requestedHall)?requestedHall:'all',
    search:(params.get('q')||'').slice(0,120)
  };
}
export function lookupStores({floor='1F',hall='all',query='',allFloors=false,category='all'}={}){
  const q=String(query).trim().toLocaleLowerCase('ko-KR');
  return stores.filter(s=>
    (allFloors||s.floor===floor)&&
    (hall==='all'||s.hall===hall)&&
    (category==='all'||s.category===category)&&
    (!q || [s.name,s.note,s.floor,s.hall+'관',categories[s.category]?.label||''].some(v=>String(v).toLocaleLowerCase('ko-KR').includes(q)))
  );
}
export function findShop(id){return stores.find(s=>s.id===id)||null;}
export function findZone(floor,id,hall='all'){return displayZones(hall,floor).find(z=>z.id===id)||null;}
export function areaSummary(floor){return floorDescriptions[floor]||'층별 자료 확인 필요';}
export function buildSchematicRoute(origin=defaultOrigin,destination){
  if(!destination||!knownFloor(destination.floor)||!knownHall(destination.hall)){
    return {supported:false,steps:[],title:'목적지를 선택하세요.',warning:'위치 정보가 없는 매장은 정확한 실내 경로를 제공할 수 없습니다.'};
  }
  const hallTo=destination.hall==='all'?'선택 구역':destination.hall+'관';
  const steps=[{type:'start',label:'출발',detail:origin.hall+'관 '+origin.floor+' 출입구 기준 (수동 지정)'}];
  if(origin.hall!==destination.hall&&destination.hall!=='all'){
    steps.push({type:'hall',label:'관 이동',detail:destination.hall+'관 방향 통로를 현장 안내판에서 확인하세요.'});
  }
  if(origin.floor!==destination.floor){
    steps.push({type:'floor',label:'층 이동',detail:destination.floor+' 층 이동. 엘리베이터/에스컬레이터의 실제 연결 지점은 확인 필요.'});
  }
  steps.push({type:'arrive',label:'목적 구역',detail:hallTo+' '+destination.floor+' · '+(destination.name||'선택 구역')+' (정확한 호실 미확인)'});
  return {
    supported:true,steps,
    title:(destination.name||'선택 구역')+' 안내',
    warning:'개략적인 관·층 안내입니다. 실제 보행 경로·거리·소요시간·무장애 동선은 검증되지 않았습니다.',
    distanceMeters:null,etaMinutes:null,indoorLocationVerified:false
  };
}
export function qualityStats(){
  return {floors:floorOrder.length,storeNames:stores.length,locatedStores:stores.filter(s=>Number.isFinite(s.x)&&Number.isFinite(s.y)&&s.status==='verified').length,routeSurveyed:false};
}
