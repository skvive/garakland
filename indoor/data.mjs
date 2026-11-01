/**
 * GARAK MALL indoor guide pilot – 2026-11-02.
 * Source class: on-site sign photos uploaded by project owner + public category guides.
 * All x/y and polygons are SCHEMATIC, not surveyed positions.
 * Store names are photo-transcribed and never claim verified tenant occupancy.
 * This dataset must NOT be used for evacuation or accessibility routing.
 */
export const floorOrder = ['B3','B2','B1','1F','2F','3F'];
export const halls = [
 {id:'all',label:'전체 구역',description:'가락몰 전체 영역'},
 {id:'3',label:'3관',description:'3관 안내판 기반'},
 {id:'4',label:'4관',description:'공용 연결 구역 · 자료 보강 필요'},
 {id:'5',label:'5관',description:'5관 안내판 기반'}
];
export const categories = {
 parking:{label:'주차',color:'#8392a8'}, produce:{label:'채소·과일',color:'#80bf70'},
 seafood:{label:'수산',color:'#5ba6df'}, meat:{label:'축산',color:'#e59a95'},
 dried:{label:'건어·식재료',color:'#b3a3da'}, food:{label:'식당·외식',color:'#f5b46b'},
 grocery:{label:'종합식품',color:'#80bcbb'}, kitchen:{label:'주방용품',color:'#e5c782'},
 services:{label:'회센터·편의',color:'#83a7df'}, processing:{label:'가공·창고',color:'#a3a3c9'}
};
const z=(id,label,category,x,y,w,h,notes='')=>({id,label,category,x,y,w,h,notes,accuracy:'concept'});
/** Normalized layout units x:0..100, y:0..100. Each zone is a category, NOT a verified shop unit. */
export const floorZones={
 B3:[z('b3-parking','고객전용 주차장','parking',12,25,76,48,'정확한 주차구획과 진입로 확인 필요')],
 B2:[
  z('b2-byproduct','축산부산물','meat',11,26,36,43),
  z('b2-processing','가공처리장','processing',48,26,23,43),
  z('b2-parking','주차·창고','parking',72,26,16,43)],
 B1:[
  z('b1-produce','과일·채소','produce',11,23,40,42),
  z('b1-food','먹거리광장','food',53,23,20,42),
  z('b1-parking','주차·편의','parking',75,23,13,42)],
 '1F':[
  z('f1-seafood','수산시장','seafood',10,19,34,48),
  z('f1-dried','건어물','dried',45,19,16,48),
  z('f1-meat','축산시장','meat',62,19,16,48),
  z('f1-center','회센터·판매시설','services',79,19,10,48)],
 '2F':[
  z('f2-grocery','종합식품·식자재','grocery',11,22,35,44),
  z('f2-kitchen','주방용품','kitchen',48,22,25,44),
  z('f2-food','식당·식자재','food',75,22,13,44)],
 '3F':[
  z('f3-restaurants','전문식당가','food',11,22,46,44),
  z('f3-dried','건어물·도소매','dried',59,22,29,44)]
};
export const floorDescriptions={
 B3:'고객용 주차장',
 B2:'축산부산물 · 가공처리 · 주차',
 B1:'채소·과일 · 먹거리광장 · 주차',
 '1F':'수산 · 건어 · 축산 · 회센터',
 '2F':'종합식품 · 주방용품 · 식자재',
 '3F':'전문식당가 · 건어물 관련 상가'
};
/** Building names only; no claimed storefront geometry or official unit number. */
export const stores = [
 {id:'h3-damijeong',name:'다미정',hall:'3',floor:'3F',category:'food',note:'3관 3층 안내판에 표기'},
 {id:'h3-sojeong',name:'소정',hall:'3',floor:'3F',category:'food',note:'3관 3층 안내판에 표기'},
 {id:'h3-ediya',name:'이디야 가락몰점',hall:'3',floor:'3F',category:'food',note:'3관 3층 안내판에 표기'},
 {id:'h3-saenong',name:'새농 푸드마켓',hall:'3',floor:'2F',category:'grocery',note:'3관 2층 안내판에 표기'},
 {id:'h3-daose',name:'다오세 사람들',hall:'3',floor:'1F',category:'food',note:'3관 1층 안내판에 표기'},
 {id:'h3-realpub',name:'리얼펍',hall:'3',floor:'1F',category:'food',note:'3관 1층 안내판에 표기'},
 {id:'h3-jeongjin',name:'정진농산',hall:'3',floor:'1F',category:'produce',note:'3관 1층 안내판에 표기'},
 {id:'h5-dolgorae',name:'돌고래',hall:'5',floor:'3F',category:'food',note:'5관 3층 안내판에 표기'},
 {id:'h5-manchan',name:'만찬',hall:'5',floor:'3F',category:'food',note:'5관 3층 안내판에 표기'},
 {id:'h5-seoul',name:'서울식당',hall:'5',floor:'3F',category:'food',note:'5관 3층 안내판에 표기'},
 {id:'h5-haegeum',name:'해금강',hall:'5',floor:'3F',category:'food',note:'5관 3층 안내판에 표기'},
 {id:'h5-geobuk',name:'거북선',hall:'5',floor:'2F',category:'food',note:'5관 2층 안내판에 표기'},
 {id:'h5-guryong',name:'구룡각',hall:'5',floor:'2F',category:'food',note:'5관 2층 안내판에 표기'},
 {id:'h5-ilpum',name:'일품',hall:'5',floor:'2F',category:'food',note:'5관 2층 안내판에 표기'}
].map(s=>({...s,source:'현장 안내판 사진',status:'명칭·관·층 표기 확인 / 영업·호실·정확 위치 미확인',unit:null,x:null,y:null}));

export const evidence = [
 {id:'sign-hall3',label:'3관 층별 안내판',coverage:'3관 1F·2F·3F 매장명',type:'uploaded_photo',quality:'listed_only'},
 {id:'sign-hall5',label:'5관 층별 안내판',coverage:'5관 1F·2F·3F 매장명',type:'uploaded_photo',quality:'listed_only'},
 {id:'sign-b1',label:'B1F 안내도',coverage:'B1 내부 통로와 범례',type:'uploaded_photo',quality:'approximate_structure'},
 {id:'sign-1f',label:'1F 안내도·피난 안내도',coverage:'판매동의 길게 굽은 외곽·통로 형태',type:'uploaded_photo',quality:'approximate_structure'},
 {id:'online-2026',label:'2026년 카카오맵 가락몰 실내지도 보도자료',coverage:'상세 도면이 공개 서비스에 존재한다는 사실',type:'web',url:'https://www.kakaocorp.com/page/detail/11930',quality:'reference_only'}
];
export const defaultOrigin={hall:'5',floor:'1F',label:'5관 1층 출입구(수동 선택)'};
export const demoPois=[
 {id:'po-restroom',type:'restroom',label:'화장실(위치 시연)',x:19,y:72},
 {id:'po-elevator',type:'elevator',label:'엘리베이터(위치 시연)',x:56,y:72},
 {id:'po-escalator',type:'escalator',label:'에스컬레이터(위치 시연)',x:78,y:72}
];
