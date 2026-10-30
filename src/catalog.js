export const MARKET = {address:'서울특별시 송파구 양재대로 932',lat:37.4943,lng:127.1116, name:'가락시장·가락몰', disclaimer:'지도 시작점은 안내용 근사 좌표입니다. 실제 지형·지물은 Google 지도에서 확인하세요.'};
export const ZONE_IMAGES = {
 campus:'/assets/zones/campus-3d.jpg',
 seafood:'/assets/zones/seafood-3d.jpg',
 produce:'/assets/zones/produce-3d.jpg',
 sales:'/assets/zones/sales-3d.jpg',
 food:'/assets/zones/food-3d.jpg'
};
export const BUILDINGS = [
 {id:'sales',name:'가락몰 판매동',en:'THE MARKET HALL',theme:'식재료광장',category:'소매',icon:'🛒',accent:'#ee9b5c',description:'수산·축산·청과·식자재 매장을 층별로 탐색하는 중심 쇼핑 건물',floors:['B2','B1','1F','2F','3F'],floorInfo:{B2:'축산부산물',B1:'청과', '1F':'수산 · 축산 · 건해', '2F':'식자재 · 주방', '3F':'식품 관련 상가'},illustrative:[50,42],lat:37.4943,lng:127.1116,image:ZONE_IMAGES.sales,externalLink:'https://www.garak.co.kr/homepage/M0000273/garak/list.do'},
 {id:'theme1',name:'가락몰 테마 1관',en:'THEME PAVILION 01',theme:'푸드테마관',category:'테마관',icon:'🥬',accent:'#84c2a4',description:'가락몰 테마관 — 실제 매장·시설 배치는 공식 안내에서 확인하세요.',floors:['1F','2F','3F'],illustrative:[70,48],lat:37.4952,lng:127.1102,image:ZONE_IMAGES.food},
 {id:'theme2',name:'가락몰 테마 2관',en:'THEME PAVILION 02',theme:'푸드테마관',category:'테마관',icon:'🍲',accent:'#d7bd80',description:'식자재와 먹거리 중심 테마 구역',floors:['1F','2F','3F'],illustrative:[42,22],lat:37.4954,lng:127.1110,image:ZONE_IMAGES.food},
 {id:'theme3',name:'가락몰 테마 3관',en:'THEME PAVILION 03',theme:'과일정원',category:'테마관',icon:'🌿',accent:'#88bbc5',description:'식문화·상업시설이 연결되는 테마 구역',floors:['1F','2F','3F'],illustrative:[58,22],lat:37.4954,lng:127.1120,image:ZONE_IMAGES.produce},
 {id:'theme4',name:'가락몰 테마 4관',en:'THEME PAVILION 04',theme:'푸드테마관',category:'테마관',icon:'🍜',accent:'#dcaa8f',description:'식문화 관련 테마 구역',floors:['B1','1F','2F','3F'],illustrative:[78,30],lat:37.4952,lng:127.1128,image:ZONE_IMAGES.food},
 {id:'theme5',name:'가락몰 테마 5관',en:'THEME PAVILION 05',theme:'수산랜드',category:'테마관',icon:'🐟',accent:'#7eb4d4',description:'회센터 등 방문객을 위한 식음 관련 시설',floors:['1F','2F','3F'],illustrative:[86,46],lat:37.4946,lng:127.1134,image:ZONE_IMAGES.seafood},
 {id:'office',name:'가락몰 업무동',en:'CULTURE & SERVICES',theme:'가락랜드',category:'문화',icon:'📚',accent:'#baabdb',description:'도서관·컨벤션·금융과 시민 편의 시설',floors:['1F','2F','3F','4F','5F'],illustrative:[86,78],lat:37.4936,lng:127.1132,image:ZONE_IMAGES.campus},
 {id:'produce',name:'청과 도매구역',en:'FRESH PRODUCE ZONE',theme:'과일정원',category:'도매',icon:'🍎',accent:'#e6bb66',description:'청과 도매 기능을 안내하는 구역. 지도상의 정확한 동 경계는 도면 확보 전입니다.',floors:['1F'],illustrative:[26,50],lat:37.4938,lng:127.1095,image:ZONE_IMAGES.produce},
 {id:'seafood',name:'수산 도매구역',en:'SEAFOOD ZONE',theme:'수산랜드',category:'도매',icon:'🦀',accent:'#76b3c8',description:'수산 도매 기능을 안내하는 구역. 지도상의 정확한 동 경계는 도면 확보 전입니다.',floors:['1F'],illustrative:[82,70],lat:37.4934,lng:127.1104,image:ZONE_IMAGES.seafood}
];
export const GUIDES=[
 {eyebrow:'DISCOVER · 01',title:'처음 만나는 가락랜드',description:'가락시장과 가락몰은 도매 유통과 소비자 판매 공간이 공존합니다. 목적에 맞는 시설을 먼저 찾는 것이 가장 좋습니다.',icon:'✳'},
 {eyebrow:'DISCOVER · 02',title:'판매동 층별 가이드',description:'지하 1층은 청과, 1층은 수산·축산·건어 등, 2층은 식자재 중심입니다. 방문 전 개별 매장의 위치와 운영 여부를 확인하세요.',icon:'◈'},
 {eyebrow:'DISCOVER · 03',title:'맛있는 시장 산책',description:'장보기와 식사, 문화시설을 함께 둘러볼 수 있습니다. 실내 도보 내비게이션은 정식 층별 연결도면이 있어야 구축 가능합니다.',icon:'✦'},
 {eyebrow:'DISCOVER · 04',title:'매장을 찾는 가장 빠른 길',description:'매장 이름 또는 업종을 검색해 건물·층·호실을 확인한 다음, 외부 이동은 Google 길찾기를 이용하세요.',icon:'↗'}
];
export const MAP_SOURCES={ official:'https://www.garak.co.kr/homepage/M0000212/market/findStore.do', directory:'https://www.garak.co.kr/homepage/M0000273/garak/list.do',overview:'https://www.garak.co.kr/main/main.do', google3d:'https://developers.google.com/maps/documentation/javascript/3d/overview', googletypes:'https://developers.google.com/maps/documentation/javascript/maptypes',googleurls:'https://developers.google.com/maps/documentation/urls/get-started'};
export const getBuilding=id=>BUILDINGS.find(z=>z.id===id)||BUILDINGS[0];
export function safeUrl(raw){try{const x=new URL(String(raw||''));return ['http:','https:'].includes(x.protocol)?x.href:'';}catch{return '';}}
export function mapsSearchURL(q){const u=new URL('https://www.google.com/maps/search/');u.searchParams.set('api','1');u.searchParams.set('query',q);return u.toString();}
export function mapDirectionsURL(shop,mode='walking',origin=null){const u=new URL('https://www.google.com/maps/dir/');u.searchParams.set('api','1');const verified=shop&&shop.coordinateStatus==='verified'&&Number.isFinite(Number(shop.latitude))&&Number.isFinite(Number(shop.longitude));u.searchParams.set('destination',verified?`${shop.latitude},${shop.longitude}`:((shop?.name||MARKET.name)+' '+MARKET.address));if(origin&&Number.isFinite(origin.lat)&&Number.isFinite(origin.lng))u.searchParams.set('origin',`${origin.lat},${origin.lng}`);u.searchParams.set('travelmode',mode);u.searchParams.set('dir_action','navigate');return u.toString();}
export function verifiedCoords(s){return s.coordinateStatus==='verified'&&Number.isFinite(Number(s.latitude))&&Number.isFinite(Number(s.longitude))&&s.latitude!==null&&s.longitude!==null;}
export function escapeHTML(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
export function cleanShop(s){return {...s,id:String(s.id||'').trim(), name:String(s.name||'').trim(),latitude: s.latitude===''||s.latitude==null?null:Number(s.latitude),longitude:s.longitude===''||s.longitude==null?null:Number(s.longitude),indoorX:s.indoorX===''||s.indoorX==null?null:Number(s.indoorX),indoorY:s.indoorY===''||s.indoorY==null?null:Number(s.indoorY),featured: s.featured===true||s.featured==='true'||s.featured==='1',verifiedAt:String(s.verifiedAt||''),status:String(s.status||'needs_review'),coordinateStatus:String(s.coordinateStatus||'unverified')};}
export function categoryEditorialWebp(category){
  const t=String(category||'').toLowerCase();
  if(t.includes('수산'))return '/assets/v5/seafood.webp';
  if(t.includes('축'))return '/assets/v5/meat.webp';
  if(t.includes('청과'))return '/assets/v5/fruit.webp';
  if(t.includes('식'))return '/assets/v5/market.webp';
  return '/assets/editorial/market.webp';
}
